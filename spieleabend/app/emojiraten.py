"""Emoji-Rätsel: a row of emojis stands for a film, a fairy tale, a saying, a word … – everyone types
what it means. Answers are matched tolerantly; the faster a correct answer, the more points."""

import random
import re
import time
import unicodedata

from common import RuleError
from emojiraten_daten import GROUPS
from party import PartyGame, clean

MAX_TRIES = 3            # wrong answers before a player is out for the round
BASE, SPEED, FIRST = 5, 5, 2   # correct answer: BASE + up to SPEED for being quick + FIRST for the fastest

# Category id (the settings send numbers) → (name, puzzles as (emojis, answer, alternatives, group name)).
CATEGORIES = {0: ("Alles gemischt", [(e, a, alts, name) for name, items in GROUPS for e, a, alts in items])}
for i, (name, items) in enumerate(GROUPS, 1):
    CATEGORIES[i] = (name, [(e, a, alts, name) for e, a, alts in items])
PUZZLES = CATEGORIES[0][1]

ARTICLES = {"der", "die", "das", "den", "dem", "des", "ein", "eine", "einen", "einem", "einer", "the", "a", "an"}
FILLERS = ARTICLES | {"und", "in", "im", "zu", "von", "vom", "mit", "auf", "of", "to", "and", "nicht", "man", "ist", "hat"}


def words(text: str, plain: bool = False) -> list[str]:
    """Lower case ASCII words: umlauts become ae/oe/ue (or a/o/u with plain), ß becomes ss,
    punctuation is dropped."""
    text = str(text).lower().replace("&", " und ").replace("?", " fragezeichen ")
    if not plain:
        text = text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    text = text.replace("ß", "ss")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", text).split()


def distance(a: str, b: str) -> int:
    """Levenshtein distance."""
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def tolerance(length: int) -> int:
    """How many typos are forgiven for an answer of this length."""
    if length <= 4:
        return 0
    if length <= 7:
        return 1
    if length <= 12:
        return 2
    return max(3, length // 6)


def _keys(text: str) -> set[str]:
    """Ways to write the answer that count as the same: without a leading article, without all
    articles and small words, and with umlauts written without the 'e' (König → konig)."""
    keys = set()
    for plain in (False, True):
        ws = words(text, plain)
        while len(ws) > 1 and ws[0] in ARTICLES:
            ws = ws[1:]
        keys |= {"".join(ws), "".join(w for w in ws if w not in FILLERS) or "".join(ws)}
    return {k for k in keys if k}


def _close(a: str, b: str) -> bool:
    return distance(a, b) <= tolerance(len(b))


def _covers(guess: str, answer: str) -> bool:
    """Long answers (sayings): enough of the important words are there, each with a typo at most."""
    need = [w for w in words(answer) if w not in FILLERS]
    have = [w for w in words(guess) if w not in FILLERS]
    if len(need) < 3 or not have:
        return False
    found = sum(1 for w in need if any(distance(w, h) <= (1 if len(w) >= 5 else 0) for h in have))
    return found >= max(3, round(len(need) * .75))


def matches(guess: str, answer: str, alternatives=()) -> bool:
    guess_keys = _keys(guess)
    if not guess_keys:
        return False
    options = {k for option in (answer, *alternatives) for k in _keys(option)}
    if guess_keys & OTHER_ANSWERS and not guess_keys & options:
        return False     # exactly another puzzle's answer (Island ≠ Irland) is no typo
    numbers = re.findall(r"\d+", guess)
    for option in (answer, *alternatives):
        if re.findall(r"\d+", option) not in ([], numbers):
            continue     # numbers have to be right (101 Dalmatiner, not 100)
        for want in _keys(option):
            if any(_close(g, want) for g in guess_keys):
                return True
        if _covers(guess, option):
            return True
    return False


OTHER_ANSWERS = {k for _, answer, alts, _ in PUZZLES for option in (answer, *alts) for k in _keys(option)}


class Game(PartyGame):
    KIND = "emojiraten"
    MIN_PLAYERS, MAX_PLAYERS = 2, 16
    ROUNDS = (10, 5, 15, 20)
    TIMES = (45, 30, 60, 0)
    INPUT_PHASES = ("guess",)

    def __init__(self, code: str):
        super().__init__(code)
        self.category = 0
        self.puzzle = None
        self.started = 0.0
        self.solvers: list[str] = []   # player ids in the order they solved the puzzle

    def configure_more(self, settings: dict) -> None:
        category = settings.get("category")
        self.category = int(category) if category is not None and int(category) in CATEGORIES else 0

    def settings_view(self) -> dict:
        return {**super().settings_view(), "category": self.category}

    def setup_round(self) -> None:
        puzzles = CATEGORIES[self.category][1]
        pool = [p for p in puzzles if p[0] not in self.used] or puzzles
        self.puzzle = random.choice(pool)
        self.used.add(self.puzzle[0])
        self.solvers = []
        self.started = time.time()
        for p in self.players:
            p.tries = []          # wrong answers in this round
            p.solved_in = None    # seconds it took
        self.begin("guess")

    def play(self, player, msg: dict) -> None:
        kind = msg.get("t")
        if kind == "pass":
            if player.answer is None:
                player.answer = False
        elif kind == "guess":
            if player.answer is not None:
                raise RuleError("Du bist in dieser Runde schon fertig")
            text = clean(msg.get("value"), 80)
            if not text:
                raise RuleError("Bitte etwas eintippen")
            _, answer, alternatives, _ = self.puzzle
            if matches(text, answer, alternatives):
                player.answer = text
                player.solved_in = round(time.time() - self.started, 1)
                self.solvers.append(player.id)
            else:
                player.tries.append(text)
                if len(player.tries) >= MAX_TRIES:
                    player.answer = False
        else:
            raise RuleError("Unbekannte Aktion")
        if self.done("answer"):
            self.advance()

    def points_for(self, player) -> int:
        place = self.solvers.index(player.id)
        bonus = FIRST if place == 0 else 0
        if self.seconds:
            left = max(0.0, self.seconds - (player.solved_in or 0)) / self.seconds
            return BASE + round(SPEED * left) + bonus
        return BASE + max(0, SPEED - place) + bonus

    def advance(self) -> None:
        for p in self.gamers:
            if p.id in self.solvers:
                p.gained = self.points_for(p)
                p.score += p.gained
        self.begin("reveal", timed=False)
        if self.solvers:
            first = self.player(self.solvers[0])
            self.note(f"{first.name} war am schnellsten" if first else "Gelöst!")
        else:
            self.note("Niemand hat es erraten")

    # -- view ----------------------------------------------------------------
    def extra_view(self, me) -> dict:
        emojis, answer, alternatives, group = self.puzzle or ("", "", (), "")
        reveal = self.phase == "reveal"
        view = {
            "emojis": emojis, "group": group, "category": CATEGORIES[self.category][0],
            "max_tries": MAX_TRIES,
            "answer": answer if reveal else None,
            "solved": len(self.solvers),
            "my_tries": list(getattr(me, "tries", [])) if me else [],
            "my_solved": bool(me and me.id in self.solvers),
            "my_answer": me.answer if me and isinstance(me.answer, str) else None,
            "my_out": bool(me and me.answer is False),
        }
        if reveal:
            results = []
            for p in self.gamers:
                solved = p.id in self.solvers
                results.append({"id": p.id, "solved": solved, "text": p.answer if solved else (p.tries[-1] if getattr(p, "tries", None) else ""),
                                "time": p.solved_in, "points": p.gained,
                                "place": self.solvers.index(p.id) + 1 if solved else None})
            results.sort(key=lambda r: (r["place"] is None, r["place"] or 0))
            view["results"] = results
        return view


MIN_PLAYERS, MAX_PLAYERS = Game.MIN_PLAYERS, Game.MAX_PLAYERS
