"""Spieleabend add-on: multiplayer card games with a shared lobby, rooms and computer players."""

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

import kritzelpost
import stapeljagd
import tiefpunkt
from common import RuleError

OPTIONS_FILE = Path("/data/options.json")
STATIC_DIR = Path(__file__).parent / "static"
PORT = int(os.environ.get("SPIELE_PORT", "8098"))
BOT_DELAY = float(os.environ.get("SPIELE_BOT_DELAY", "0.9"))
BOT_NAMES = ["Robo", "Karla", "Bitty", "Otto", "Zora", "Pixel", "Toni", "Mops"]
GAME_TTL = 6 * 3600  # remove games nobody has touched for this long

GAMES = {"stapeljagd": stapeljagd, "tiefpunkt": tiefpunkt, "kritzelpost": kritzelpost}

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("spieleabend")


def load_options() -> dict:
    try:
        return json.loads(OPTIONS_FILE.read_text())
    except (OSError, ValueError):
        return {}


THEME = os.environ.get("SPIELE_THEME") or load_options().get("theme") or "dark"
if THEME not in ("dark", "light"):
    THEME = "dark"


class Hub:
    """All rooms of one game kind, the browsers connected to them and their bots."""

    def __init__(self, module) -> None:
        self.module = module
        self.games: dict = {}
        self.touched: dict[str, float] = {}
        # Each browser keeps a token; it maps to (room code, player id) so a reload rejoins.
        self.seats: dict[str, tuple[str, str]] = {}
        self.sockets: dict[web.WebSocketResponse, str] = {}
        self.bot_tasks: dict[str, asyncio.Task] = {}
        self.timers: dict[str, float] = {}  # room code -> deadline a timer task waits for
        self.timer_tasks: set[asyncio.Task] = set()  # keep references so tasks aren't collected

    # -- sending -------------------------------------------------------------
    @staticmethod
    async def send(ws: web.WebSocketResponse, message: dict) -> None:
        if not ws.closed:
            try:
                await ws.send_json(message)
            except (ConnectionError, RuntimeError):
                pass

    def open_games(self) -> list[dict]:
        return [
            {"code": g.code, "state": g.state, "players": [p.name for p in g.players],
             "full": len(g.players) >= self.module.MAX_PLAYERS}
            for g in self.games.values() if g.players
        ]

    async def send_view(self, ws: web.WebSocketResponse) -> None:
        token = self.sockets.get(ws)
        seat = self.seats.get(token)
        game = self.games.get(seat[0]) if seat else None
        if game and game.player(seat[1]):
            await self.send(ws, {"t": "game", "me": seat[1], "game": game.view_for(seat[1])})
        else:
            self.seats.pop(token, None)
            await self.send(ws, {"t": "lobby", "games": self.open_games()})

    async def broadcast(self, code: str | None = None) -> None:
        """Update every browser in room `code` and everyone in the lobby."""
        if code:
            self.touched[code] = time.time()
        for ws, token in list(self.sockets.items()):
            seat = self.seats.get(token)
            if seat is None or seat[0] == code:
                await self.send_view(ws)
        if code:
            self.schedule_bots(code)
            self.schedule_timer(code)

    # -- bots ----------------------------------------------------------------
    def schedule_bots(self, code: str) -> None:
        game = self.games.get(code)
        task = self.bot_tasks.get(code)
        if game and game.pending_bots() and (task is None or task.done()):
            self.bot_tasks[code] = asyncio.create_task(self.run_bots(code))

    async def run_bots(self, code: str) -> None:
        while True:
            await asyncio.sleep(BOT_DELAY)
            game = self.games.get(code)
            bots = game.pending_bots() if game else []
            if not bots:
                return
            try:
                game.bot_step(bots[0])
            except RuleError as err:  # should not happen; never let a bot freeze a room
                log.warning("Bot %s in %s: %s", bots[0].name, code, err)
                return
            await self.broadcast(code)

    # -- timers (games with a `deadline`) -------------------------------------
    def schedule_timer(self, code: str) -> None:
        game = self.games.get(code)
        deadline = getattr(game, "deadline", None) if game else None
        if deadline is None or self.timers.get(code) == deadline:
            return
        self.timers[code] = deadline
        task = asyncio.create_task(self.run_timer(code, deadline))
        self.timer_tasks.add(task)
        task.add_done_callback(self.timer_tasks.discard)

    async def run_timer(self, code: str, deadline: float) -> None:
        await asyncio.sleep(max(0.0, deadline - time.time()))
        game = self.games.get(code)
        # A newer deadline (next step) replaced this one: nothing to do.
        if game and getattr(game, "deadline", None) == deadline:
            game.on_deadline()
            await self.broadcast(code)

    # -- actions -------------------------------------------------------------
    def new_code(self) -> str:
        letters = string.ascii_uppercase.replace("O", "").replace("I", "")
        while True:
            code = "".join(random.choices(letters, k=4))
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
                game = self.module.Game(self.new_code())
                game.configure(msg.get("settings") or {})
                self.games[game.code] = game
            else:
                game = self.games.get(str(msg.get("code", "")).strip().upper())
                if not game:
                    raise RuleError("Dieses Spiel gibt es nicht")
            player = game.new_player(name)
            game.add_player(player)
            self.seats[token] = (game.code, player.id)
            await self.broadcast(game.code)
            return

        if not game:
            if kind == "lobby":
                await self.send(ws, {"t": "lobby", "games": self.open_games()})
                return
            raise RuleError("Du bist in keinem Spiel")

        is_host = game.host_id == me
        if kind == "leave":
            code = self.leave(token)
            await self.broadcast(code)
            await self.send(ws, {"t": "lobby", "games": self.open_games()})
            return
        if kind == "add_bot":
            if not is_host:
                raise RuleError("Nur der Gastgeber kann Computer-Spieler hinzufügen")
            used = {p.name for p in game.players}
            bot_name = next((n for n in BOT_NAMES if n not in used), f"Bot {len(game.players) + 1}")
            game.add_player(game.new_player(bot_name, is_bot=True))
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
            game.configure(msg.get("settings") or {})
        elif kind == "start":
            if not is_host:
                raise RuleError("Nur der Gastgeber kann das Spiel starten")
            game.start()
        elif kind == "rematch":
            if not is_host or game.state != "finished":
                raise RuleError("Nur der Gastgeber kann eine neue Runde starten")
            game.start()
        else:
            game.act(me, msg, is_host)
        await self.broadcast(game.code)

    async def cleanup(self) -> None:
        now = time.time()
        for code in [c for c, t in self.touched.items() if now - t > GAME_TTL]:
            self.games.pop(code, None)
            self.touched.pop(code, None)
            self.timers.pop(code, None)
            for token in [t for t, s in self.seats.items() if s[0] == code]:
                self.seats.pop(token)
        await self.broadcast()


hubs = {kind: Hub(module) for kind, module in GAMES.items()}
routes = web.RouteTableDef()


def page(path: Path) -> web.Response:
    html = path.read_text(encoding="utf-8").replace("<html ", f'<html data-theme="{THEME}" ', 1)
    return web.Response(text=html, content_type="text/html", headers={"Cache-Control": "no-cache"})


@routes.get("/")
async def index(_: web.Request) -> web.Response:
    return page(STATIC_DIR / "index.html")


@routes.get("/api/summary")
async def summary(_: web.Request) -> web.Response:
    data = {}
    for kind, hub in hubs.items():
        games = hub.open_games()
        data[kind] = {
            "open": sum(1 for g in games if g["state"] == "lobby" and not g["full"]),
            "playing": sum(1 for g in games if g["state"] == "playing"),
        }
    return web.json_response(data)


@routes.get("/{kind}")
async def no_slash(request: web.Request) -> web.Response:
    kind = request.match_info["kind"]
    if kind not in hubs:
        raise web.HTTPNotFound()
    raise web.HTTPFound(f"{kind}/")  # relative, so it also works behind Ingress


@routes.get("/{kind}/")
async def game_page(request: web.Request) -> web.Response:
    kind = request.match_info["kind"]
    if kind not in hubs:
        raise web.HTTPNotFound()
    return page(STATIC_DIR / kind / "index.html")


@routes.get("/{kind}/ws")
async def websocket(request: web.Request) -> web.WebSocketResponse:
    hub = hubs.get(request.match_info["kind"])
    if not hub:
        raise web.HTTPNotFound()
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


async def cleanup_loop() -> None:
    while True:
        await asyncio.sleep(600)
        for hub in hubs.values():
            await hub.cleanup()


async def on_startup(app: web.Application) -> None:
    app["cleanup"] = asyncio.create_task(cleanup_loop())
    log.info("Spieleabend läuft auf Port %s", PORT)


def main() -> None:
    app = web.Application()
    app.router.add_static("/static/", STATIC_DIR / "shared")
    app.add_routes(routes)
    app.on_startup.append(on_startup)
    web.run_app(app, host=None, port=PORT, print=None, access_log=None)


if __name__ == "__main__":
    main()
