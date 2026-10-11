"""Stapeljagd add-on: multiplayer game server with lobby, rooms and computer players."""

import asyncio
import json
import logging
import os
import random
import secrets
import string
import time
from pathlib import Path

from aiohttp import WSMsgType, web

from game import MAX_PLAYERS, Game, Player, RuleError, bot_moves

OPTIONS_FILE = Path("/data/options.json")
STATIC_DIR = Path(__file__).parent / "static"
PORT = int(os.environ.get("STAPELJAGD_PORT", "8098"))
BOT_DELAY = float(os.environ.get("STAPELJAGD_BOT_DELAY", "0.9"))
BOT_NAMES = ["Robo", "Karla", "Bitty", "Otto", "Zora", "Pixel", "Toni", "Mops"]
GAME_TTL = 6 * 3600  # remove games nobody has touched for this long

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stapeljagd")


def load_options() -> dict:
    try:
        return json.loads(OPTIONS_FILE.read_text())
    except (OSError, ValueError):
        return {}


THEME = os.environ.get("STAPELJAGD_THEME") or load_options().get("theme") or "dark"
if THEME not in ("dark", "light"):
    THEME = "dark"


class Hub:
    """All games, the browsers connected to them and the bots that play in them."""

    def __init__(self) -> None:
        self.games: dict[str, Game] = {}
        self.touched: dict[str, float] = {}
        # Each browser keeps a token; it maps to (game code, player id) so a reload rejoins.
        self.seats: dict[str, tuple[str, str]] = {}
        self.sockets: dict[web.WebSocketResponse, str] = {}  # socket -> token
        self.bot_tasks: dict[str, asyncio.Task] = {}

    # -- sending -----------------------------------------------------------
    @staticmethod
    async def send(ws: web.WebSocketResponse, message: dict) -> None:
        if not ws.closed:
            try:
                await ws.send_json(message)
            except (ConnectionError, RuntimeError):
                pass

    def lobby_view(self) -> dict:
        games = [
            {
                "code": g.code, "state": g.state,
                "players": [p.name for p in g.players],
                "full": len(g.players) >= MAX_PLAYERS,
            }
            for g in self.games.values() if g.players
        ]
        return {"t": "lobby", "games": games}

    async def send_view(self, ws: web.WebSocketResponse) -> None:
        token = self.sockets.get(ws)
        seat = self.seats.get(token)
        game = self.games.get(seat[0]) if seat else None
        if game and game.player(seat[1]):
            await self.send(ws, {"t": "game", "me": seat[1], "game": game.view_for(seat[1])})
        else:
            self.seats.pop(token, None)
            await self.send(ws, self.lobby_view())

    async def broadcast(self, code: str | None = None) -> None:
        """Update every browser in game `code` and everyone in the lobby."""
        if code:
            self.touched[code] = time.time()
        for ws, token in list(self.sockets.items()):
            seat = self.seats.get(token)
            if seat is None or seat[0] == code:
                await self.send_view(ws)
        if code:
            self.schedule_bot(code)

    # -- bots --------------------------------------------------------------
    def schedule_bot(self, code: str) -> None:
        game = self.games.get(code)
        player = game.current if game else None
        task = self.bot_tasks.get(code)
        if player and player.is_bot and (task is None or task.done()):
            self.bot_tasks[code] = asyncio.create_task(self.run_bot(code))

    async def run_bot(self, code: str) -> None:
        while True:
            await asyncio.sleep(BOT_DELAY)
            game = self.games.get(code)
            player = game.current if game else None
            if not player or not player.is_bot:
                return
            move = bot_moves(game, player)[0]
            try:
                if move[0] == "play":
                    game.play(player.id, *move[1:])
                elif move[0] == "discard":
                    game.discard(player.id, *move[1:])
                else:
                    game.pass_turn(player.id)
            except RuleError as err:  # should not happen; don't let a bot hang the game
                log.warning("Bot %s: %s", player.name, err)
                game.pass_turn(player.id) if not player.hand else game.discard(player.id, 0, 0)
            await self.broadcast(code)

    # -- actions -----------------------------------------------------------
    def new_code(self) -> str:
        while True:
            code = "".join(random.choices(string.ascii_uppercase.replace("O", "").replace("I", ""), k=4))
            if code not in self.games:
                return code

    def leave(self, token: str) -> str | None:
        seat = self.seats.pop(token, None)
        if not seat:
            return None
        code, player_id = seat
        game = self.games.get(code)
        if not game:
            return None
        player = game.player(player_id)
        if game.state == "playing" and player:
            # Keep the game going: a computer player takes over the seat.
            player.is_bot = True
            player.name += " (Bot)"
            game.note(f"{player.name} spielt jetzt für den Spieler weiter")
            if game.host_id == player_id:
                game.host_id = next((p.id for p in game.players if not p.is_bot), None)
        else:
            game.remove_player(player_id)
        if not any(not p.is_bot for p in game.players):
            self.games.pop(code, None)
            return None
        return code

    async def handle(self, ws: web.WebSocketResponse, token: str, msg: dict) -> None:
        kind = msg.get("t")
        seat = self.seats.get(token)
        game = self.games.get(seat[0]) if seat else None
        me = seat[1] if seat else None
        name = str(msg.get("name", "")).strip()[:20]

        if kind in ("create", "join"):
            if not name:
                raise RuleError("Bitte gib deinen Namen ein")
            if seat:
                self.leave(token)
            if kind == "create":
                stock = int(msg.get("stock") or 0)
                game = Game(self.new_code(), stock if stock in (0, 5, 10, 15, 20, 25, 30) else 0)
                self.games[game.code] = game
            else:
                game = self.games.get(str(msg.get("code", "")).strip().upper())
                if not game:
                    raise RuleError("Dieses Spiel gibt es nicht")
            player = Player(name)
            game.add_player(player)
            self.seats[token] = (game.code, player.id)
            await self.broadcast(game.code)
            return

        if not game:
            if kind == "lobby":
                await self.send(ws, self.lobby_view())
                return
            raise RuleError("Du bist in keinem Spiel")

        is_host = game.host_id == me
        if kind == "leave":
            code = self.leave(token)
            await self.broadcast(code)
            await self.send(ws, self.lobby_view())
            return
        if kind == "add_bot":
            if not is_host:
                raise RuleError("Nur der Gastgeber kann Computer-Spieler hinzufügen")
            used = {p.name for p in game.players}
            bot_name = next((n for n in BOT_NAMES if n not in used), f"Bot {len(game.players) + 1}")
            game.add_player(Player(bot_name, is_bot=True))
        elif kind == "kick":
            if not is_host or game.state != "lobby":
                raise RuleError("Nur der Gastgeber kann vor dem Start Spieler entfernen")
            target = game.player(str(msg.get("id")))
            if target and target.id != me:
                for other, (code, pid) in list(self.seats.items()):
                    if code == game.code and pid == target.id:
                        self.seats.pop(other)
                game.remove_player(target.id)
        elif kind == "settings":
            if not is_host or game.state != "lobby":
                raise RuleError("Nur der Gastgeber kann das ändern")
            stock = int(msg.get("stock") or 0)
            game.stock_size = stock if stock in (0, 5, 10, 15, 20, 25, 30) else 0
        elif kind == "start":
            if not is_host:
                raise RuleError("Nur der Gastgeber kann das Spiel starten")
            game.start()
        elif kind == "rematch":
            if not is_host or game.state != "finished":
                raise RuleError("Nur der Gastgeber kann eine neue Runde starten")
            game.start()
        elif kind == "play":
            game.play(me, str(msg.get("src")), int(msg.get("index", 0)), int(msg.get("pile", -1)))
        elif kind == "discard":
            game.discard(me, int(msg.get("index", -1)), int(msg.get("pile", -1)))
        elif kind == "pass":
            game.pass_turn(me)
        else:
            raise RuleError("Unbekannte Aktion")
        await self.broadcast(game.code)

    async def cleanup(self) -> None:
        while True:
            await asyncio.sleep(600)
            now = time.time()
            for code in [c for c, t in self.touched.items() if now - t > GAME_TTL]:
                self.games.pop(code, None)
                self.touched.pop(code, None)
                for token in [t for t, s in self.seats.items() if s[0] == code]:
                    self.seats.pop(token)
            await self.broadcast()


hub = Hub()
routes = web.RouteTableDef()


@routes.get("/")
async def index(_: web.Request) -> web.Response:
    html = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    html = html.replace("<html ", f'<html data-theme="{THEME}" ', 1)
    return web.Response(text=html, content_type="text/html", headers={"Cache-Control": "no-cache"})


@routes.get("/ws")
async def websocket(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse(heartbeat=25)
    await ws.prepare(request)
    token = None
    try:
        async for message in ws:
            if message.type != WSMsgType.TEXT:
                continue
            try:
                data = json.loads(message.data)
            except ValueError:
                continue
            if token is None:
                # First message identifies the browser; an unknown token gets a fresh one.
                token = str(data.get("token") or "")
                if len(token) < 16:
                    token = secrets.token_urlsafe(16)
                hub.sockets[ws] = token
                await hub.send(ws, {"t": "hello", "token": token})
                await hub.send_view(ws)
                continue
            try:
                await hub.handle(ws, token, data)
            except RuleError as err:
                await hub.send(ws, {"t": "error", "msg": str(err)})
            except (TypeError, ValueError):
                await hub.send(ws, {"t": "error", "msg": "Ungültige Eingabe"})
    finally:
        hub.sockets.pop(ws, None)
    return ws


async def on_startup(app: web.Application) -> None:
    app["cleanup"] = asyncio.create_task(hub.cleanup())
    log.info("Stapeljagd läuft auf Port %s", PORT)


def main() -> None:
    app = web.Application()
    app.add_routes(routes)
    app.on_startup.append(on_startup)
    web.run_app(app, host=None, port=PORT, print=None, access_log=None)


if __name__ == "__main__":
    main()
