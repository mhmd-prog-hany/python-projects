#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║           T I C  T A C  T O E  —  A D V A N C E D  E D I T I O N   ║
║                    Built with Professional OOP Design                ║
║                        By: Mohammed Hany                             ║
╚══════════════════════════════════════════════════════════════════════╝

Design Patterns Used:
  ✦ Abstract Base Class (ABC)         — Player, Renderer, GameStrategy
  ✦ Observer / Event System           — EventEmitter, GameEvent, Listener
  ✦ Strategy Pattern                  — AI difficulty strategies
  ✦ State Machine                     — GameStateMachine
  ✦ Factory Pattern                   — PlayerFactory, RendererFactory
  ✦ Singleton Pattern                 — GameConfig, ScoreManager
  ✦ Command Pattern                   — MoveCommand with undo/redo
  ✦ Decorator Pattern                 — LoggedBoard, TimedBoard
  ✦ Repository Pattern                — GameRepository (save/load)
  ✦ Builder Pattern                   — GameBuilder
"""

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTS
# ─────────────────────────────────────────────────────────────────────────────

import os
import sys
import math
import time
import json
import random
import threading
import platform
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional, List, Dict, Callable, Any, Tuple
from dataclasses import dataclass, field
from copy import deepcopy
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — TERMINAL COLORS & STYLES
# ─────────────────────────────────────────────────────────────────────────────

class Color:
    """ANSI color codes for terminal styling."""

    # Reset
    RESET       = "\033[0m"

    # Text Styles
    BOLD        = "\033[1m"
    DIM         = "\033[2m"
    ITALIC      = "\033[3m"
    UNDERLINE   = "\033[4m"
    BLINK       = "\033[5m"
    REVERSE     = "\033[7m"

    # Foreground Colors (Standard)
    BLACK       = "\033[30m"
    RED         = "\033[31m"
    GREEN       = "\033[32m"
    YELLOW      = "\033[33m"
    BLUE        = "\033[34m"
    MAGENTA     = "\033[35m"
    CYAN        = "\033[36m"
    WHITE       = "\033[37m"

    # Foreground Colors (Bright / Neon)
    BR_BLACK    = "\033[90m"
    BR_RED      = "\033[91m"
    BR_GREEN    = "\033[92m"
    BR_YELLOW   = "\033[93m"
    BR_BLUE     = "\033[94m"
    BR_MAGENTA  = "\033[95m"
    BR_CYAN     = "\033[96m"
    BR_WHITE    = "\033[97m"

    # Background Colors
    BG_BLACK    = "\033[40m"
    BG_RED      = "\033[41m"
    BG_GREEN    = "\033[42m"
    BG_YELLOW   = "\033[43m"
    BG_BLUE     = "\033[44m"
    BG_MAGENTA  = "\033[45m"
    BG_CYAN     = "\033[46m"
    BG_WHITE    = "\033[47m"

    # Theme Aliases (Neon Cyberpunk)
    NEON_PINK   = "\033[38;5;213m"
    NEON_CYAN   = "\033[38;5;51m"
    NEON_GREEN  = "\033[38;5;118m"
    NEON_ORANGE = "\033[38;5;214m"
    NEON_PURPLE = "\033[38;5;141m"
    NEON_GOLD   = "\033[38;5;220m"
    DARK_GRAY   = "\033[38;5;240m"
    MID_GRAY    = "\033[38;5;245m"

    @staticmethod
    def rgb(r: int, g: int, b: int) -> str:
        """Return true-color ANSI escape for foreground."""
        return f"\033[38;2;{r};{g};{b}m"

    @staticmethod
    def bg_rgb(r: int, g: int, b: int) -> str:
        """Return true-color ANSI escape for background."""
        return f"\033[48;2;{r};{g};{b}m"

    @staticmethod
    def style(text: str, *codes: str) -> str:
        """Wrap text with multiple color/style codes."""
        prefix = "".join(codes)
        return f"{prefix}{text}{Color.RESET}"


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — ENUMERATIONS
# ─────────────────────────────────────────────────────────────────────────────

class Symbol(Enum):
    """Board symbols."""
    X       = "X"
    O       = "O"
    EMPTY   = " "

    def opponent(self) -> "Symbol":
        if self == Symbol.X:
            return Symbol.O
        if self == Symbol.O:
            return Symbol.X
        return Symbol.EMPTY

    def colored(self) -> str:
        if self == Symbol.X:
            return Color.style(" X ", Color.BOLD, Color.NEON_CYAN)
        if self == Symbol.O:
            return Color.style(" O ", Color.BOLD, Color.NEON_PINK)
        return Color.style("   ", Color.DIM)


class GameState(Enum):
    """Finite states of the game state machine."""
    IDLE        = auto()
    MENU        = auto()
    STARTING    = auto()
    PLAYING     = auto()
    PAUSED      = auto()
    GAME_OVER   = auto()
    REPLAY      = auto()
    SETTINGS    = auto()
    SCORES      = auto()
    EXITING     = auto()


class GameResult(Enum):
    """Possible outcomes of a finished game."""
    X_WINS  = auto()
    O_WINS  = auto()
    DRAW    = auto()
    ONGOING = auto()


class Difficulty(Enum):
    """AI difficulty levels."""
    EASY    = "Easy"
    MEDIUM  = "Medium"
    HARD    = "Hard"
    INSANE  = "Insane"


class EventType(Enum):
    """All possible game events for the observer system."""
    GAME_STARTED    = auto()
    GAME_ENDED      = auto()
    MOVE_MADE       = auto()
    MOVE_UNDONE     = auto()
    TURN_CHANGED    = auto()
    BOARD_RESET     = auto()
    SCORE_UPDATED   = auto()
    STATE_CHANGED   = auto()
    ERROR_OCCURRED  = auto()
    AI_THINKING     = auto()
    AI_DONE         = auto()


class PlayerType(Enum):
    """Types of players."""
    HUMAN       = "Human"
    AI_EASY     = "AI (Easy)"
    AI_MEDIUM   = "AI (Medium)"
    AI_HARD     = "AI (Hard)"
    AI_INSANE   = "AI (Insane)"


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — DATA CLASSES (Value Objects)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Position:
    """Immutable board position (row, col)."""
    row: int
    col: int

    def to_index(self) -> int:
        return self.row * 3 + self.col

    @staticmethod
    def from_index(idx: int) -> "Position":
        return Position(idx // 3, idx % 3)

    def is_valid(self) -> bool:
        return 0 <= self.row < 3 and 0 <= self.col < 3

    def __str__(self) -> str:
        return f"({self.row}, {self.col})"


@dataclass
class GameEvent:
    """Event object passed through the observer system."""
    event_type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def __str__(self) -> str:
        return f"[{self.event_type.name}] at {self.timestamp:.2f} | data={self.data}"


@dataclass
class ScoreRecord:
    """Score record for one player."""
    name: str
    wins: int = 0
    losses: int = 0
    draws: int = 0
    total_games: int = 0
    total_moves: int = 0

    @property
    def win_rate(self) -> float:
        if self.total_games == 0:
            return 0.0
        return round(self.wins / self.total_games * 100, 1)

    def update(self, result: GameResult, symbol: Symbol, winner_symbol: Optional[Symbol]) -> None:
        self.total_games += 1
        if result == GameResult.DRAW:
            self.draws += 1
        elif winner_symbol == symbol:
            self.wins += 1
        else:
            self.losses += 1

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "total_games": self.total_games,
            "total_moves": self.total_moves,
            "win_rate": self.win_rate,
        }


@dataclass
class GameSnapshot:
    """Snapshot of a game at a given moment (for save/load)."""
    cells: List[str]
    current_symbol: str
    move_count: int
    timestamp: str
    player_x_name: str
    player_o_name: str
    player_x_type: str
    player_o_type: str


@dataclass
class MoveRecord:
    """History record for a single move."""
    position: Position
    symbol: Symbol
    move_number: int
    timestamp: float = field(default_factory=time.time)

    def __str__(self) -> str:
        return (
            f"Move #{self.move_number}: "
            f"{self.symbol.value} → {self.position}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — OBSERVER PATTERN (Event System)
# ─────────────────────────────────────────────────────────────────────────────

class EventListener(ABC):
    """Abstract base for anything that listens to game events."""

    @abstractmethod
    def on_event(self, event: GameEvent) -> None:
        """Handle an incoming event."""
        ...


class EventEmitter:
    """
    Core event bus — implements the Observer pattern.
    Any object can subscribe to specific EventTypes and receive GameEvents.
    """

    def __init__(self) -> None:
        self._listeners: Dict[EventType, List[EventListener]] = {
            et: [] for et in EventType
        }
        self._global_listeners: List[EventListener] = []
        self._event_log: List[GameEvent] = []

    def subscribe(self, event_type: EventType, listener: EventListener) -> None:
        """Subscribe a listener to a specific event type."""
        if listener not in self._listeners[event_type]:
            self._listeners[event_type].append(listener)

    def subscribe_all(self, listener: EventListener) -> None:
        """Subscribe a listener to ALL event types."""
        if listener not in self._global_listeners:
            self._global_listeners.append(listener)

    def unsubscribe(self, event_type: EventType, listener: EventListener) -> None:
        """Remove a listener from a specific event type."""
        if listener in self._listeners[event_type]:
            self._listeners[event_type].remove(listener)

    def emit(self, event: GameEvent) -> None:
        """Dispatch event to all relevant listeners."""
        self._event_log.append(event)
        for listener in self._listeners[event.event_type]:
            listener.on_event(event)
        for listener in self._global_listeners:
            listener.on_event(event)

    def emit_simple(self, event_type: EventType, **data) -> None:
        """Shortcut: emit with keyword data."""
        self.emit(GameEvent(event_type=event_type, data=data))

    @property
    def event_log(self) -> List[GameEvent]:
        return list(self._event_log)

    def clear_log(self) -> None:
        self._event_log.clear()


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — BOARD (Core Domain Object)
# ─────────────────────────────────────────────────────────────────────────────

class Board:
    """
    The game board — a 3×3 grid.
    Supports full state inspection, move validation, and winner detection.
    """

    WIN_PATTERNS: List[List[int]] = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],   # rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],   # cols
        [0, 4, 8], [2, 4, 6],               # diagonals
    ]

    def __init__(self) -> None:
        self._cells: List[Symbol] = [Symbol.EMPTY] * 9
        self._move_count: int = 0
        self._last_move: Optional[Position] = None
        self._winning_pattern: Optional[List[int]] = None

    # ── State Access ────────────────────────────────────────────────────────

    def get(self, pos: Position) -> Symbol:
        return self._cells[pos.to_index()]

    def get_by_index(self, idx: int) -> Symbol:
        return self._cells[idx]

    @property
    def cells(self) -> List[Symbol]:
        return list(self._cells)

    @property
    def move_count(self) -> int:
        return self._move_count

    @property
    def last_move(self) -> Optional[Position]:
        return self._last_move

    @property
    def winning_pattern(self) -> Optional[List[int]]:
        return self._winning_pattern

    # ── Move Operations ─────────────────────────────────────────────────────

    def place(self, pos: Position, symbol: Symbol) -> bool:
        """Place a symbol. Returns True on success."""
        if not pos.is_valid():
            return False
        if self._cells[pos.to_index()] != Symbol.EMPTY:
            return False
        self._cells[pos.to_index()] = symbol
        self._move_count += 1
        self._last_move = pos
        self._winning_pattern = None
        return True

    def remove(self, pos: Position) -> Symbol:
        """Remove symbol (for AI backtracking). Returns removed symbol."""
        removed = self._cells[pos.to_index()]
        self._cells[pos.to_index()] = Symbol.EMPTY
        self._move_count -= 1
        self._winning_pattern = None
        return removed

    def reset(self) -> None:
        self._cells = [Symbol.EMPTY] * 9
        self._move_count = 0
        self._last_move = None
        self._winning_pattern = None

    # ── Queries ─────────────────────────────────────────────────────────────

    def available_positions(self) -> List[Position]:
        return [
            Position.from_index(i)
            for i, s in enumerate(self._cells)
            if s == Symbol.EMPTY
        ]

    def available_indices(self) -> List[int]:
        return [i for i, s in enumerate(self._cells) if s == Symbol.EMPTY]

    def is_full(self) -> bool:
        return Symbol.EMPTY not in self._cells

    def check_winner(self, symbol: Symbol) -> bool:
        """Check if a symbol has won, and cache the winning pattern."""
        for pattern in self.WIN_PATTERNS:
            if all(self._cells[i] == symbol for i in pattern):
                self._winning_pattern = pattern
                return True
        return False

    def get_result(self) -> GameResult:
        if self.check_winner(Symbol.X):
            return GameResult.X_WINS
        if self.check_winner(Symbol.O):
            return GameResult.O_WINS
        if self.is_full():
            return GameResult.DRAW
        return GameResult.ONGOING

    def clone(self) -> "Board":
        b = Board()
        b._cells = list(self._cells)
        b._move_count = self._move_count
        b._last_move = self._last_move
        return b

    def to_list(self) -> List[str]:
        return [s.value for s in self._cells]

    @staticmethod
    def from_list(data: List[str]) -> "Board":
        b = Board()
        for i, v in enumerate(data):
            if v == "X":
                b._cells[i] = Symbol.X
            elif v == "O":
                b._cells[i] = Symbol.O
        b._move_count = sum(1 for s in b._cells if s != Symbol.EMPTY)
        return b

    def __str__(self) -> str:
        rows = []
        for r in range(3):
            row = [self._cells[r * 3 + c].value for c in range(3)]
            rows.append(" | ".join(row))
        return "\n---------\n".join(rows)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 — DECORATOR PATTERN (Board Decorators)
# ─────────────────────────────────────────────────────────────────────────────

class BoardDecorator(ABC):
    """Abstract decorator wrapping a Board with additional behavior."""

    def __init__(self, board: Board) -> None:
        self._board = board

    def __getattr__(self, name: str):
        return getattr(self._board, name)


class LoggedBoard(BoardDecorator):
    """Logs every move placed on the board."""

    def __init__(self, board: Board) -> None:
        super().__init__(board)
        self._log: List[str] = []

    def place(self, pos: Position, symbol: Symbol) -> bool:
        result = self._board.place(pos, symbol)
        if result:
            entry = f"[LOG] Move #{self._board.move_count}: {symbol.value} → {pos}"
            self._log.append(entry)
        return result

    @property
    def move_log(self) -> List[str]:
        return list(self._log)


class TimedBoard(BoardDecorator):
    """Tracks how long each move takes."""

    def __init__(self, board: Board) -> None:
        super().__init__(board)
        self._move_times: List[float] = []
        self._last_tick: float = time.time()

    def place(self, pos: Position, symbol: Symbol) -> bool:
        elapsed = time.time() - self._last_tick
        result = self._board.place(pos, symbol)
        if result:
            self._move_times.append(elapsed)
            self._last_tick = time.time()
        return result

    @property
    def average_move_time(self) -> float:
        if not self._move_times:
            return 0.0
        return round(sum(self._move_times) / len(self._move_times), 2)

    @property
    def move_times(self) -> List[float]:
        return list(self._move_times)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7 — COMMAND PATTERN (Move History & Undo)
# ─────────────────────────────────────────────────────────────────────────────

class Command(ABC):
    """Abstract command — supports execute and undo."""

    @abstractmethod
    def execute(self) -> bool:
        ...

    @abstractmethod
    def undo(self) -> bool:
        ...

    @abstractmethod
    def describe(self) -> str:
        ...


class MoveCommand(Command):
    """
    Command wrapping a single board move.
    Stores the position and symbol so it can be fully undone.
    """

    def __init__(self, board: Board, position: Position, symbol: Symbol) -> None:
        self._board = board
        self._position = position
        self._symbol = symbol
        self._executed = False

    def execute(self) -> bool:
        if self._executed:
            return False
        success = self._board.place(self._position, self._symbol)
        if success:
            self._executed = True
        return success

    def undo(self) -> bool:
        if not self._executed:
            return False
        self._board.remove(self._position)
        self._executed = False
        return True

    def describe(self) -> str:
        return (
            f"MoveCommand: {self._symbol.value} → "
            f"pos={self._position} | executed={self._executed}"
        )

    @property
    def position(self) -> Position:
        return self._position

    @property
    def symbol(self) -> Symbol:
        return self._symbol


class MoveHistory:
    """
    Maintains a stack of MoveCommands for undo/redo support.
    """

    def __init__(self) -> None:
        self._done: List[MoveCommand] = []
        self._undone: List[MoveCommand] = []

    def push(self, cmd: MoveCommand) -> bool:
        success = cmd.execute()
        if success:
            self._done.append(cmd)
            self._undone.clear()
        return success

    def undo(self) -> Optional[MoveCommand]:
        if not self._done:
            return None
        cmd = self._done.pop()
        cmd.undo()
        self._undone.append(cmd)
        return cmd

    def redo(self) -> Optional[MoveCommand]:
        if not self._undone:
            return None
        cmd = self._undone.pop()
        cmd.execute()
        self._done.append(cmd)
        return cmd

    def can_undo(self) -> bool:
        return len(self._done) > 0

    def can_redo(self) -> bool:
        return len(self._undone) > 0

    def history(self) -> List[MoveCommand]:
        return list(self._done)

    def clear(self) -> None:
        self._done.clear()
        self._undone.clear()

    def __len__(self) -> int:
        return len(self._done)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8 — STRATEGY PATTERN (AI Difficulty Strategies)
# ─────────────────────────────────────────────────────────────────────────────

class AIStrategy(ABC):
    """Abstract AI strategy — each difficulty implements this."""

    @abstractmethod
    def choose_move(self, board: Board, ai_symbol: Symbol) -> Position:
        """Return the best position for the AI to play."""
        ...

    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def description(self) -> str:
        ...


class EasyStrategy(AIStrategy):
    """
    Easy AI — plays completely random moves.
    Great for beginners or players who just want to have fun.
    """

    def choose_move(self, board: Board, ai_symbol: Symbol) -> Position:
        time.sleep(random.uniform(0.3, 0.7))
        moves = board.available_positions()
        return random.choice(moves)

    def name(self) -> str:
        return "Easy"

    def description(self) -> str:
        return "Random moves — even your grandma can beat this."


class MediumStrategy(AIStrategy):
    """
    Medium AI — wins if it can, blocks if needed, otherwise random.
    Uses single-step lookahead, no minimax.
    """

    def choose_move(self, board: Board, ai_symbol: Symbol) -> Position:
        time.sleep(random.uniform(0.4, 0.9))
        human_symbol = ai_symbol.opponent()

        # 1) Win if possible
        win_move = self._find_winning_move(board, ai_symbol)
        if win_move is not None:
            return win_move

        # 2) Block human win
        block_move = self._find_winning_move(board, human_symbol)
        if block_move is not None:
            return block_move

        # 3) Take center
        center = Position(1, 1)
        if board.get(center) == Symbol.EMPTY:
            return center

        # 4) Take a corner
        for idx in [0, 2, 6, 8]:
            pos = Position.from_index(idx)
            if board.get(pos) == Symbol.EMPTY:
                return pos

        # 5) Random
        return random.choice(board.available_positions())

    def _find_winning_move(self, board: Board, symbol: Symbol) -> Optional[Position]:
        for pos in board.available_positions():
            board.place(pos, symbol)
            wins = board.check_winner(symbol)
            board.remove(pos)
            if wins:
                return pos
        return None

    def name(self) -> str:
        return "Medium"

    def description(self) -> str:
        return "Blocks and attacks — puts up a decent fight."


class HardStrategy(AIStrategy):
    """
    Hard AI — uses Minimax with Alpha-Beta pruning.
    Plays near-optimally but with a tiny bit of randomness for variety.
    """

    def choose_move(self, board: Board, ai_symbol: Symbol) -> Position:
        time.sleep(random.uniform(0.5, 1.2))
        if len(board.available_positions()) == 9:
            # First move: pick random corner for variety
            corners = [Position.from_index(i) for i in [0, 2, 6, 8]]
            return random.choice(corners)

        result = self._minimax(board, ai_symbol, ai_symbol, -math.inf, math.inf, 0)
        return result["pos"]

    def _minimax(
        self,
        board: Board,
        ai_symbol: Symbol,
        current: Symbol,
        alpha: float,
        beta: float,
        depth: int,
    ) -> Dict:
        human_symbol = ai_symbol.opponent()

        if board.check_winner(ai_symbol):
            return {"score": 10 - depth}
        if board.check_winner(human_symbol):
            return {"score": depth - 10}
        if board.is_full():
            return {"score": 0}

        is_maximizing = current == ai_symbol
        best: Dict = {
            "score": -math.inf if is_maximizing else math.inf,
            "pos": None,
        }

        for pos in board.available_positions():
            board.place(pos, current)
            result = self._minimax(
                board, ai_symbol, current.opponent(), alpha, beta, depth + 1
            )
            board.remove(pos)
            result["pos"] = pos

            if is_maximizing:
                if result["score"] > best["score"]:
                    best = result
                alpha = max(alpha, best["score"])
            else:
                if result["score"] < best["score"]:
                    best = result
                beta = min(beta, best["score"])

            if beta <= alpha:
                break

        return best

    def name(self) -> str:
        return "Hard"

    def description(self) -> str:
        return "Alpha-Beta Minimax — very tough to beat."


class InsaneStrategy(HardStrategy):
    """
    Insane AI — pure perfect Minimax, no randomness at all.
    Will NEVER lose. Best possible play every single move.
    """

    def choose_move(self, board: Board, ai_symbol: Symbol) -> Position:
        time.sleep(random.uniform(0.8, 1.5))  # Dramatic pause
        if len(board.available_positions()) == 9:
            return Position(1, 1)  # Always take center
        result = self._minimax(board, ai_symbol, ai_symbol, -math.inf, math.inf, 0)
        return result["pos"]

    def name(self) -> str:
        return "Insane"

    def description(self) -> str:
        return "Perfect Minimax — impossible to beat. You have been warned."


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 9 — ABSTRACT PLAYER & CONCRETE IMPLEMENTATIONS
# ─────────────────────────────────────────────────────────────────────────────

class Player(ABC):
    """
    Abstract base class for all players.
    Both human and AI players implement this interface.
    """

    def __init__(self, name: str, symbol: Symbol, player_type: PlayerType) -> None:
        self._name = name
        self._symbol = symbol
        self._player_type = player_type
        self._move_history: List[MoveRecord] = []
        self._score: ScoreRecord = ScoreRecord(name=name)

    @property
    def name(self) -> str:
        return self._name

    @property
    def symbol(self) -> Symbol:
        return self._symbol

    @property
    def player_type(self) -> PlayerType:
        return self._player_type

    @property
    def score(self) -> ScoreRecord:
        return self._score

    @property
    def is_human(self) -> bool:
        return self._player_type == PlayerType.HUMAN

    @property
    def is_ai(self) -> bool:
        return not self.is_human

    @abstractmethod
    def request_move(self, board: Board) -> Position:
        """Ask the player for their next move."""
        ...

    def record_move(self, pos: Position, move_number: int) -> None:
        record = MoveRecord(
            position=pos,
            symbol=self._symbol,
            move_number=move_number,
        )
        self._move_history.append(record)
        self._score.total_moves += 1

    def move_history(self) -> List[MoveRecord]:
        return list(self._move_history)

    def reset_session(self) -> None:
        self._move_history.clear()

    def update_score(self, result: GameResult, winner_symbol: Optional[Symbol]) -> None:
        self._score.update(result, self._symbol, winner_symbol)

    def colored_name(self) -> str:
        if self._symbol == Symbol.X:
            return Color.style(self._name, Color.BOLD, Color.NEON_CYAN)
        return Color.style(self._name, Color.BOLD, Color.NEON_PINK)

    def __str__(self) -> str:
        return f"{self._name} [{self._symbol.value}] ({self._player_type.value})"


class HumanPlayer(Player):
    """
    Human player — reads moves from stdin with full validation and UX.
    """

    def __init__(self, name: str, symbol: Symbol) -> None:
        super().__init__(name, symbol, PlayerType.HUMAN)

    def request_move(self, board: Board) -> Position:
        available = board.available_indices()
        while True:
            try:
                raw = input(
                    f"  {self.colored_name()} "
                    f"{Color.style('→', Color.DARK_GRAY)} "
                    f"Enter position {Color.style('[1-9]', Color.NEON_GOLD)}: "
                ).strip()

                if raw.lower() in ("u", "undo"):
                    return Position(-1, -1)  # Sentinel for undo request

                if raw.lower() in ("q", "quit", "exit"):
                    return Position(-2, -2)  # Sentinel for quit

                if raw.lower() in ("h", "help"):
                    self._show_help()
                    continue

                num = int(raw)
                if not 1 <= num <= 9:
                    print(
                        f"  {Color.style('⚠', Color.NEON_ORANGE)} "
                        f"Please enter a number between 1 and 9."
                    )
                    continue

                idx = num - 1
                pos = Position.from_index(idx)

                if idx not in available:
                    print(
                        f"  {Color.style('✗', Color.BR_RED)} "
                        f"That cell is already taken! Pick another."
                    )
                    continue

                return pos

            except ValueError:
                print(
                    f"  {Color.style('⚠', Color.NEON_ORANGE)} "
                    f"Invalid input. Enter a number 1–9 (or 'u' to undo, 'q' to quit)."
                )

    def _show_help(self) -> None:
        print()
        print(Color.style("  ╔═══ HELP ═══════════════════════════╗", Color.DARK_GRAY))
        print(Color.style("  ║", Color.DARK_GRAY) + "  1-9 : Place your symbol           " + Color.style("║", Color.DARK_GRAY))
        print(Color.style("  ║", Color.DARK_GRAY) + "  u   : Undo last move              " + Color.style("║", Color.DARK_GRAY))
        print(Color.style("  ║", Color.DARK_GRAY) + "  q   : Quit game                   " + Color.style("║", Color.DARK_GRAY))
        print(Color.style("  ╚════════════════════════════════════╝", Color.DARK_GRAY))
        print()


class AIPlayer(Player):
    """
    AI player — delegates move selection to a pluggable AIStrategy.
    Supports hot-swapping strategies at runtime.
    """

    def __init__(
        self,
        symbol: Symbol,
        strategy: AIStrategy,
        name: Optional[str] = None,
    ) -> None:
        player_type = self._strategy_to_type(strategy)
        resolved_name = name or f"AI [{strategy.name()}]"
        super().__init__(resolved_name, symbol, player_type)
        self._strategy = strategy
        self._thinking = False

    @staticmethod
    def _strategy_to_type(strategy: AIStrategy) -> PlayerType:
        mapping = {
            "Easy": PlayerType.AI_EASY,
            "Medium": PlayerType.AI_MEDIUM,
            "Hard": PlayerType.AI_HARD,
            "Insane": PlayerType.AI_INSANE,
        }
        return mapping.get(strategy.name(), PlayerType.AI_HARD)

    def request_move(self, board: Board) -> Position:
        self._thinking = True
        pos = self._strategy.choose_move(board, self._symbol)
        self._thinking = False
        return pos

    def swap_strategy(self, strategy: AIStrategy) -> None:
        """Swap AI strategy at runtime (Open/Closed principle)."""
        self._strategy = strategy
        self._player_type = self._strategy_to_type(strategy)

    @property
    def strategy(self) -> AIStrategy:
        return self._strategy

    @property
    def is_thinking(self) -> bool:
        return self._thinking


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 10 — FACTORY PATTERN (Player & Strategy factories)
# ─────────────────────────────────────────────────────────────────────────────

class StrategyFactory:
    """Creates AI strategy objects by difficulty enum."""

    _registry: Dict[Difficulty, type] = {
        Difficulty.EASY:   EasyStrategy,
        Difficulty.MEDIUM: MediumStrategy,
        Difficulty.HARD:   HardStrategy,
        Difficulty.INSANE: InsaneStrategy,
    }

    @classmethod
    def create(cls, difficulty: Difficulty) -> AIStrategy:
        strategy_class = cls._registry.get(difficulty)
        if strategy_class is None:
            raise ValueError(f"Unknown difficulty: {difficulty}")
        return strategy_class()

    @classmethod
    def register(cls, difficulty: Difficulty, strategy_class: type) -> None:
        """Register a custom strategy (extensibility)."""
        cls._registry[difficulty] = strategy_class

    @classmethod
    def available_difficulties(cls) -> List[Difficulty]:
        return list(cls._registry.keys())


class PlayerFactory:
    """Creates Player instances from high-level configuration."""

    @staticmethod
    def create_human(name: str, symbol: Symbol) -> HumanPlayer:
        return HumanPlayer(name=name, symbol=symbol)

    @staticmethod
    def create_ai(symbol: Symbol, difficulty: Difficulty, name: Optional[str] = None) -> AIPlayer:
        strategy = StrategyFactory.create(difficulty)
        return AIPlayer(symbol=symbol, strategy=strategy, name=name)

    @classmethod
    def from_type(
        cls,
        player_type: PlayerType,
        symbol: Symbol,
        name: str = "",
    ) -> Player:
        if player_type == PlayerType.HUMAN:
            return cls.create_human(name or "Player", symbol)
        difficulty_map = {
            PlayerType.AI_EASY:   Difficulty.EASY,
            PlayerType.AI_MEDIUM: Difficulty.MEDIUM,
            PlayerType.AI_HARD:   Difficulty.HARD,
            PlayerType.AI_INSANE: Difficulty.INSANE,
        }
        diff = difficulty_map.get(player_type, Difficulty.HARD)
        return cls.create_ai(symbol, diff, name)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 11 — SINGLETON PATTERN (Config & Score Manager)
# ─────────────────────────────────────────────────────────────────────────────

class GameConfig:
    """
    Singleton: Holds all user-configurable settings.
    """
    _instance: Optional["GameConfig"] = None

    def __new__(cls) -> "GameConfig":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_defaults()
        return cls._instance

    def _init_defaults(self) -> None:
        self.show_animations: bool = True
        self.show_move_numbers: bool = True
        self.ai_delay_enabled: bool = True
        self.sound_enabled: bool = False
        self.theme: str = "cyberpunk"
        self.default_difficulty: Difficulty = Difficulty.HARD
        self.player_x_name: str = "Player X"
        self.player_o_name: str = "Player O"
        self.save_file: str = "ttt_save.json"
        self.max_history: int = 100

    def to_dict(self) -> Dict:
        return {
            "show_animations": self.show_animations,
            "show_move_numbers": self.show_move_numbers,
            "ai_delay_enabled": self.ai_delay_enabled,
            "theme": self.theme,
            "default_difficulty": self.default_difficulty.value,
            "player_x_name": self.player_x_name,
            "player_o_name": self.player_o_name,
        }


class ScoreManager:
    """
    Singleton: Tracks scores across multiple games in a session.
    """
    _instance: Optional["ScoreManager"] = None

    def __new__(cls) -> "ScoreManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._records: Dict[str, ScoreRecord] = {}
            cls._instance._game_count: int = 0
        return cls._instance

    def get_or_create(self, name: str) -> ScoreRecord:
        if name not in self._records:
            self._records[name] = ScoreRecord(name=name)
        return self._records[name]

    def record_game(
        self,
        player_x: Player,
        player_o: Player,
        result: GameResult,
    ) -> None:
        self._game_count += 1
        winner_symbol: Optional[Symbol] = None
        if result == GameResult.X_WINS:
            winner_symbol = Symbol.X
        elif result == GameResult.O_WINS:
            winner_symbol = Symbol.O

        for player in [player_x, player_o]:
            rec = self.get_or_create(player.name)
            rec.update(result, player.symbol, winner_symbol)

    def all_records(self) -> List[ScoreRecord]:
        return sorted(self._records.values(), key=lambda r: r.wins, reverse=True)

    @property
    def game_count(self) -> int:
        return self._game_count

    def reset(self) -> None:
        self._records.clear()
        self._game_count = 0


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 12 — REPOSITORY PATTERN (Save / Load)
# ─────────────────────────────────────────────────────────────────────────────

class GameRepository:
    """
    Handles persistence: saving and loading game state to/from JSON.
    Implements the Repository pattern.
    """

    def __init__(self, filepath: str = "ttt_save.json") -> None:
        self._filepath = filepath

    def save(self, snapshot: GameSnapshot) -> bool:
        try:
            data = {
                "cells": snapshot.cells,
                "current_symbol": snapshot.current_symbol,
                "move_count": snapshot.move_count,
                "timestamp": snapshot.timestamp,
                "player_x_name": snapshot.player_x_name,
                "player_o_name": snapshot.player_o_name,
                "player_x_type": snapshot.player_x_type,
                "player_o_type": snapshot.player_o_type,
            }
            with open(self._filepath, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except (OSError, IOError):
            return False

    def load(self) -> Optional[GameSnapshot]:
        try:
            with open(self._filepath, "r") as f:
                data = json.load(f)
            return GameSnapshot(
                cells=data["cells"],
                current_symbol=data["current_symbol"],
                move_count=data["move_count"],
                timestamp=data["timestamp"],
                player_x_name=data["player_x_name"],
                player_o_name=data["player_o_name"],
                player_x_type=data["player_x_type"],
                player_o_type=data["player_o_type"],
            )
        except (OSError, IOError, KeyError, json.JSONDecodeError):
            return None

    def has_saved_game(self) -> bool:
        return os.path.exists(self._filepath)

    def delete_save(self) -> None:
        if os.path.exists(self._filepath):
            os.remove(self._filepath)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 13 — ABSTRACT RENDERER & IMPLEMENTATIONS
# ─────────────────────────────────────────────────────────────────────────────

class Renderer(ABC):
    """Abstract base class for all renderers."""

    @abstractmethod
    def render_board(self, board: Board) -> None:
        ...

    @abstractmethod
    def render_header(self, player_x: Player, player_o: Player, current: Player) -> None:
        ...

    @abstractmethod
    def render_result(self, result: GameResult, winner: Optional[Player]) -> None:
        ...

    @abstractmethod
    def render_scores(self, score_manager: ScoreManager) -> None:
        ...

    @abstractmethod
    def clear(self) -> None:
        ...


class CyberpunkRenderer(Renderer):
    """
    Stunning cyberpunk-themed terminal renderer.
    Neon colors, box-drawing chars, animated elements.
    """

    BORDER_TOP    = "╔" + "═" * 45 + "╗"
    BORDER_BOT    = "╚" + "═" * 45 + "╝"
    BORDER_MID    = "╠" + "═" * 45 + "╣"
    BORDER_SIDE   = "║"

    CELL_SEP      = Color.style(" ┃ ", Color.DARK_GRAY)
    ROW_SEP       = Color.style("  ───┼───┼───", Color.DARK_GRAY)

    LOGO = [
        "  ████████╗██╗ ██████╗    ████████╗ █████╗  ██████╗",
        "     ██╔══╝██║██╔════╝       ██╔══╝██╔══██╗██╔════╝",
        "     ██║   ██║██║            ██║   ███████║██║     ",
        "     ██║   ██║██║            ██║   ██╔══██║██║     ",
        "     ██║   ██║╚██████╗       ██║   ██║  ██║╚██████╗",
        "     ╚═╝   ╚═╝ ╚═════╝       ╚═╝   ╚═╝  ╚═╝ ╚═════╝",
        "              ─── T O E  •  A D V A N C E D ───",
    ]

    def clear(self) -> None:
        os.system("cls" if platform.system() == "Windows" else "clear")

    def render_logo(self) -> None:
        colors = [
            Color.NEON_CYAN, Color.NEON_CYAN,
            Color.NEON_PURPLE, Color.NEON_PURPLE,
            Color.NEON_PINK, Color.NEON_PINK,
            Color.MID_GRAY,
        ]
        print()
        for i, line in enumerate(self.LOGO):
            c = colors[i % len(colors)]
            print(Color.style(line, c, Color.BOLD))
        print()

    def render_header(self, player_x: Player, player_o: Player, current: Player) -> None:
        print(Color.style("  " + "─" * 46, Color.DARK_GRAY))
        xn = Color.style(f" {player_x.name} ", Color.BOLD, Color.NEON_CYAN)
        on = Color.style(f" {player_o.name} ", Color.BOLD, Color.NEON_PINK)
        xsym = Color.style("[X]", Color.NEON_CYAN)
        osym = Color.style("[O]", Color.NEON_PINK)
        print(f"  {xsym} {xn}  {Color.style('vs', Color.DARK_GRAY)}  {osym} {on}")
        print(Color.style("  " + "─" * 46, Color.DARK_GRAY))

        arrow = Color.style("▶", Color.NEON_GOLD, Color.BOLD)
        turn_name = current.colored_name()
        sym = current.symbol.colored()
        print(f"  {arrow} Turn: {turn_name}  {sym}")
        print()

    def render_board(self, board: Board) -> None:
        winning = board.winning_pattern or []

        # Position guide (small, dim)
        guide_cells = [Color.style(str(i + 1), Color.DARK_GRAY) for i in range(9)]

        print(Color.style("  ┌─────────────────┐", Color.DARK_GRAY))

        for row in range(3):
            cells_str = []
            for col in range(3):
                idx = row * 3 + col
                sym = board.get_by_index(idx)
                is_winning = idx in winning

                if sym == Symbol.EMPTY:
                    cell = Color.style(f" {idx+1} ", Color.DARK_GRAY)
                elif sym == Symbol.X:
                    style = (Color.BOLD, Color.NEON_CYAN, Color.BG_BLACK)
                    if is_winning:
                        style = (Color.BOLD, Color.NEON_GOLD)
                    cell = Color.style(" X ", *style)
                else:
                    style = (Color.BOLD, Color.NEON_PINK, Color.BG_BLACK)
                    if is_winning:
                        style = (Color.BOLD, Color.NEON_GOLD)
                    cell = Color.style(" O ", *style)

                cells_str.append(cell)

            sep = Color.style("│", Color.DARK_GRAY)
            row_str = f"  {sep} " + f" {sep} ".join(cells_str) + f" {sep}"
            print(row_str)

            if row < 2:
                print(Color.style("  ├─────┼─────┼─────┤", Color.DARK_GRAY))

        print(Color.style("  └─────────────────┘", Color.DARK_GRAY))
        print()

    def render_move_history(self, history: List[MoveCommand]) -> None:
        if not history:
            return
        print(Color.style("  ── Move History ────────────────────", Color.DARK_GRAY))
        recent = history[-6:]
        for i, cmd in enumerate(recent):
            num = len(history) - len(recent) + i + 1
            sym_str = cmd.symbol.colored()
            pos_str = Color.style(f"pos {cmd.position.to_index()+1}", Color.MID_GRAY)
            print(f"    {Color.style(str(num).rjust(2), Color.DARK_GRAY)}. {sym_str}  {pos_str}")
        print()

    def render_result(self, result: GameResult, winner: Optional[Player]) -> None:
        print()
        if result == GameResult.DRAW:
            msg = Color.style("  ══  DRAW!  ══  It's a tie!  ══", Color.NEON_ORANGE, Color.BOLD)
            print(msg)
        elif winner is not None:
            wname = winner.colored_name()
            wsym = winner.symbol.colored()
            print(Color.style("  ╔══════════════════════════════╗", Color.NEON_GOLD))
            print(Color.style("  ║", Color.NEON_GOLD) + f"   🏆  {wname} {wsym} WINS!  " + Color.style("   ║", Color.NEON_GOLD))
            print(Color.style("  ╚══════════════════════════════╝", Color.NEON_GOLD))
        print()

    def render_scores(self, score_manager: ScoreManager) -> None:
        records = score_manager.all_records()
        print()
        print(Color.style("  ══════════════════════════════════════", Color.NEON_PURPLE))
        print(Color.style("          S C O R E B O A R D          ", Color.NEON_GOLD, Color.BOLD))
        print(Color.style("  ══════════════════════════════════════", Color.NEON_PURPLE))
        print()
        header = (
            f"  {'NAME':<20}"
            f"{'W':>5}{'L':>5}{'D':>5}"
            f"{'WIN%':>8}"
        )
        print(Color.style(header, Color.MID_GRAY, Color.BOLD))
        print(Color.style("  " + "─" * 44, Color.DARK_GRAY))

        for rec in records:
            pct = Color.style(f"{rec.win_rate:>7.1f}%", Color.NEON_GREEN)
            wins = Color.style(f"{rec.wins:>5}", Color.NEON_CYAN)
            losses = Color.style(f"{rec.losses:>5}", Color.NEON_PINK)
            draws = Color.style(f"{rec.draws:>5}", Color.NEON_ORANGE)
            name = Color.style(f"  {rec.name:<20}", Color.BR_WHITE)
            print(f"{name}{wins}{losses}{draws}{pct}")

        print()
        total = Color.style(f"Total games played: {score_manager.game_count}", Color.DARK_GRAY)
        print(f"  {total}")
        print(Color.style("  ══════════════════════════════════════", Color.NEON_PURPLE))
        print()

    def render_settings(self, config: GameConfig) -> None:
        print()
        print(Color.style("  ══════════════════════════════════════", Color.NEON_CYAN))
        print(Color.style("            S E T T I N G S            ", Color.NEON_GOLD, Color.BOLD))
        print(Color.style("  ══════════════════════════════════════", Color.NEON_CYAN))
        print()
        settings = [
            ("1", "Animations", config.show_animations),
            ("2", "Move Numbers on Board", config.show_move_numbers),
            ("3", "AI Delay", config.ai_delay_enabled),
            ("4", "Default Difficulty", config.default_difficulty.value),
        ]
        for key, label, value in settings:
            k = Color.style(f"[{key}]", Color.NEON_GOLD)
            l_str = Color.style(f"  {label:<30}", Color.BR_WHITE)
            if isinstance(value, bool):
                v_str = Color.style("ON", Color.NEON_GREEN) if value else Color.style("OFF", Color.NEON_PINK)
            else:
                v_str = Color.style(str(value), Color.NEON_ORANGE)
            print(f"  {k} {l_str} {v_str}")
        print()
        print(Color.style("  [0] Back to Menu", Color.MID_GRAY))
        print()

    def render_ai_thinking(self, player: AIPlayer) -> None:
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        name = player.colored_name()
        for frame in frames:
            spinner = Color.style(frame, Color.NEON_CYAN)
            print(f"\r  {spinner}  {name} is thinking...", end="", flush=True)
            time.sleep(0.08)
        print()

    def print_separator(self, char: str = "─", width: int = 46) -> None:
        print(Color.style("  " + char * width, Color.DARK_GRAY))

    def print_title(self, text: str) -> None:
        print()
        print(Color.style(f"  ══  {text}  ══", Color.NEON_GOLD, Color.BOLD))
        print()

    def prompt(self, text: str) -> str:
        arrow = Color.style("▶", Color.NEON_GOLD)
        return input(f"  {arrow} {text}: ").strip()


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 14 — STATE MACHINE (Game Flow)
# ─────────────────────────────────────────────────────────────────────────────

class StateMachine:
    """
    Finite State Machine for controlling game flow.
    Enforces valid state transitions.
    """

    TRANSITIONS: Dict[GameState, List[GameState]] = {
        GameState.IDLE:      [GameState.MENU, GameState.EXITING],
        GameState.MENU:      [GameState.STARTING, GameState.SETTINGS, GameState.SCORES, GameState.EXITING],
        GameState.STARTING:  [GameState.PLAYING],
        GameState.PLAYING:   [GameState.GAME_OVER, GameState.PAUSED, GameState.EXITING],
        GameState.PAUSED:    [GameState.PLAYING, GameState.MENU, GameState.EXITING],
        GameState.GAME_OVER: [GameState.REPLAY, GameState.MENU, GameState.SCORES, GameState.EXITING],
        GameState.REPLAY:    [GameState.PLAYING, GameState.MENU],
        GameState.SETTINGS:  [GameState.MENU],
        GameState.SCORES:    [GameState.MENU],
        GameState.EXITING:   [],
    }

    def __init__(self, initial: GameState = GameState.IDLE) -> None:
        self._state = initial
        self._history: List[GameState] = [initial]

    @property
    def state(self) -> GameState:
        return self._state

    def can_transition(self, target: GameState) -> bool:
        return target in self.TRANSITIONS.get(self._state, [])

    def transition(self, target: GameState) -> bool:
        if self.can_transition(target):
            self._history.append(target)
            self._state = target
            return True
        return False

    def force(self, target: GameState) -> None:
        """Force a transition (bypass validation — use sparingly)."""
        self._history.append(target)
        self._state = target

    @property
    def history(self) -> List[GameState]:
        return list(self._history)

    def __str__(self) -> str:
        return f"StateMachine[{self._state.name}]"


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 15 — BUILDER PATTERN (Game Setup)
# ─────────────────────────────────────────────────────────────────────────────

class GameBuilder:
    """
    Fluent builder for constructing a Game instance with full configuration.
    """

    def __init__(self) -> None:
        self._player_x: Optional[Player] = None
        self._player_o: Optional[Player] = None
        self._renderer: Optional[Renderer] = None
        self._config: GameConfig = GameConfig()

    def with_player_x(self, player: Player) -> "GameBuilder":
        self._player_x = player
        return self

    def with_player_o(self, player: Player) -> "GameBuilder":
        self._player_o = player
        return self

    def with_renderer(self, renderer: Renderer) -> "GameBuilder":
        self._renderer = renderer
        return self

    def human_vs_ai(
        self,
        human_name: str = "Player",
        difficulty: Difficulty = Difficulty.HARD,
    ) -> "GameBuilder":
        self._player_x = PlayerFactory.create_human(human_name, Symbol.X)
        self._player_o = PlayerFactory.create_ai(Symbol.O, difficulty)
        return self

    def ai_vs_ai(
        self,
        diff_x: Difficulty = Difficulty.HARD,
        diff_o: Difficulty = Difficulty.MEDIUM,
    ) -> "GameBuilder":
        self._player_x = PlayerFactory.create_ai(Symbol.X, diff_x, "AI-X")
        self._player_o = PlayerFactory.create_ai(Symbol.O, diff_o, "AI-O")
        return self

    def human_vs_human(self, name_x: str = "Player 1", name_o: str = "Player 2") -> "GameBuilder":
        self._player_x = PlayerFactory.create_human(name_x, Symbol.X)
        self._player_o = PlayerFactory.create_human(name_o, Symbol.O)
        return self

    def build(self) -> "Game":
        if self._player_x is None or self._player_o is None:
            raise RuntimeError("GameBuilder: both players must be set before building.")
        renderer = self._renderer or CyberpunkRenderer()
        return Game(
            player_x=self._player_x,
            player_o=self._player_o,
            renderer=renderer,
        )


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 16 — CORE GAME CLASS
# ─────────────────────────────────────────────────────────────────────────────

class Game(EventListener):
    """
    Main Game class — orchestrates board, players, state, events, and rendering.
    Listens to its own events for logging.
    """

    def __init__(
        self,
        player_x: Player,
        player_o: Player,
        renderer: Renderer,
    ) -> None:
        self._board = Board()
        self._player_x = player_x
        self._player_o = player_o
        self._renderer = renderer
        self._current: Player = player_x
        self._history = MoveHistory()
        self._state_machine = StateMachine(GameState.IDLE)
        self._emitter = EventEmitter()
        self._score_manager = ScoreManager()
        self._config = GameConfig()
        self._result: GameResult = GameResult.ONGOING
        self._winner: Optional[Player] = None
        self._timed_board = TimedBoard(self._board)
        self._logged_board = LoggedBoard(self._board)
        self._move_records: List[MoveRecord] = []

        # Self-subscribe for logging
        self._emitter.subscribe_all(self)

    # ── EventListener Interface ─────────────────────────────────────────────

    def on_event(self, event: GameEvent) -> None:
        """Internal event handler for logging."""
        pass  # Could write to file, etc.

    # ── Properties ──────────────────────────────────────────────────────────

    @property
    def board(self) -> Board:
        return self._board

    @property
    def current_player(self) -> Player:
        return self._current

    @property
    def result(self) -> GameResult:
        return self._result

    @property
    def winner(self) -> Optional[Player]:
        return self._winner

    @property
    def state(self) -> GameState:
        return self._state_machine.state

    # ── Game Flow ────────────────────────────────────────────────────────────

    def _switch_player(self) -> None:
        self._current = (
            self._player_o
            if self._current == self._player_x
            else self._player_x
        )
        self._emitter.emit_simple(EventType.TURN_CHANGED, player=self._current.name)

    def _check_game_over(self) -> bool:
        result = self._board.get_result()
        if result == GameResult.ONGOING:
            return False

        self._result = result
        if result == GameResult.X_WINS:
            self._winner = self._player_x
        elif result == GameResult.O_WINS:
            self._winner = self._player_o

        self._score_manager.record_game(self._player_x, self._player_o, result)
        self._emitter.emit_simple(
            EventType.GAME_ENDED,
            result=result.name,
            winner=self._winner.name if self._winner else None,
        )
        return True

    def _handle_undo(self) -> None:
        """Undo last two moves (current player + previous)."""
        undone = 0
        for _ in range(2):
            cmd = self._history.undo()
            if cmd is not None:
                undone += 1
                self._emitter.emit_simple(
                    EventType.MOVE_UNDONE,
                    position=str(cmd.position),
                    symbol=cmd.symbol.value,
                )
        if undone == 0:
            print(Color.style("  ✗ Nothing to undo!", Color.NEON_ORANGE))
            time.sleep(1)
        elif undone == 1:
            self._switch_player()  # Undo one means it's still our turn

    def _do_move(self, pos: Position) -> bool:
        cmd = MoveCommand(self._board, pos, self._current.symbol)
        success = self._history.push(cmd)
        if success:
            record = MoveRecord(
                position=pos,
                symbol=self._current.symbol,
                move_number=len(self._history),
            )
            self._move_records.append(record)
            self._current.record_move(pos, len(self._history))
            self._emitter.emit_simple(
                EventType.MOVE_MADE,
                position=str(pos),
                symbol=self._current.symbol.value,
                move_number=len(self._history),
            )
        return success

    def play_turn(self) -> bool:
        """
        Execute one turn. Returns True if game continues, False if over.
        """
        self._renderer.clear()
        self._renderer.render_logo()
        self._renderer.render_header(self._player_x, self._player_o, self._current)
        self._renderer.render_board(self._board)
        self._renderer.render_move_history(self._history.history())

        if self._current.is_ai:
            ai_player = self._current  # type: ignore[assignment]
            if isinstance(ai_player, AIPlayer):
                self._emitter.emit_simple(EventType.AI_THINKING, player=ai_player.name)
                print(
                    f"  {Color.style('⠿', Color.NEON_CYAN)} "
                    f"{ai_player.colored_name()} is computing best move..."
                )
                time.sleep(0.3)

        pos = self._current.request_move(self._board)

        # Sentinel: undo request
        if pos == Position(-1, -1):
            self._handle_undo()
            return True

        # Sentinel: quit request
        if pos == Position(-2, -2):
            self._state_machine.force(GameState.EXITING)
            return False

        success = self._do_move(pos)
        if not success:
            print(Color.style("  ✗ Move failed. Try again.", Color.BR_RED))
            time.sleep(0.8)
            return True

        if self._check_game_over():
            return False

        self._switch_player()
        return True

    def run(self) -> GameResult:
        """Main game loop. Returns the final GameResult."""
        self._state_machine.transition(GameState.PLAYING)
        self._emitter.emit_simple(
            EventType.GAME_STARTED,
            player_x=self._player_x.name,
            player_o=self._player_o.name,
        )

        while self.state == GameState.PLAYING:
            continues = self.play_turn()
            if not continues:
                break

        # Show final board + result
        if self.state != GameState.EXITING:
            self._renderer.clear()
            self._renderer.render_logo()
            self._renderer.render_board(self._board)
            self._renderer.render_result(self._result, self._winner)
            self._renderer.render_move_history(self._history.history())
            self._state_machine.force(GameState.GAME_OVER)

        return self._result

    def reset(self) -> None:
        """Reset board and state for a new game."""
        self._board.reset()
        self._history.clear()
        self._move_records.clear()
        self._current = self._player_x
        self._result = GameResult.ONGOING
        self._winner = None
        self._player_x.reset_session()
        self._player_o.reset_session()
        self._emitter.emit_simple(EventType.BOARD_RESET)
        self._state_machine.force(GameState.IDLE)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 17 — GAME LOBBY (Main Menu & Navigation)
# ─────────────────────────────────────────────────────────────────────────────

class GameLobby:
    """
    Top-level application controller.
    Manages the main menu, game setup, and session loop.
    """

    def __init__(self) -> None:
        self._renderer = CyberpunkRenderer()
        self._config = GameConfig()
        self._score_manager = ScoreManager()
        self._repository = GameRepository(self._config.save_file)
        self._running = True

    # ── Menu Rendering ───────────────────────────────────────────────────────

    def _show_main_menu(self) -> str:
        self._renderer.clear()
        self._renderer.render_logo()

        options = [
            ("1", "Human vs AI",       Color.NEON_CYAN),
            ("2", "Human vs Human",    Color.NEON_GREEN),
            ("3", "AI vs AI",          Color.NEON_PURPLE),
            ("4", "Scoreboard",        Color.NEON_GOLD),
            ("5", "Settings",          Color.NEON_ORANGE),
            ("0", "Exit",              Color.DARK_GRAY),
        ]

        print(Color.style("  ╔══════════════════════════════════╗", Color.NEON_PURPLE))
        print(Color.style("  ║", Color.NEON_PURPLE) + Color.style("         MAIN MENU              ", Color.NEON_GOLD, Color.BOLD) + Color.style("  ║", Color.NEON_PURPLE))
        print(Color.style("  ╠══════════════════════════════════╣", Color.NEON_PURPLE))
        for key, label, color in options:
            k = Color.style(f" [{key}]", Color.NEON_GOLD)
            l_str = Color.style(f" {label:<28}", color)
            print(Color.style("  ║", Color.NEON_PURPLE) + f"{k}{l_str}" + Color.style("║", Color.NEON_PURPLE))
        print(Color.style("  ╚══════════════════════════════════╝", Color.NEON_PURPLE))
        print()

        choice = self._renderer.prompt("Select option")
        return choice

    def _choose_difficulty(self) -> Difficulty:
        print()
        opts = [
            ("1", Difficulty.EASY,   "Random moves"),
            ("2", Difficulty.MEDIUM, "Win/Block"),
            ("3", Difficulty.HARD,   "Alpha-Beta Minimax"),
            ("4", Difficulty.INSANE, "Perfect Minimax — unbeatable"),
        ]
        print(Color.style("  ── Select AI Difficulty ─────────────────", Color.NEON_CYAN))
        for key, diff, desc in opts:
            k = Color.style(f"  [{key}]", Color.NEON_GOLD)
            d = Color.style(f" {diff.value:<10}", Color.BR_WHITE, Color.BOLD)
            desc_str = Color.style(f" {desc}", Color.MID_GRAY)
            print(f"{k}{d}{desc_str}")
        print()
        choice = self._renderer.prompt("Difficulty [1-4]")
        mapping = {"1": Difficulty.EASY, "2": Difficulty.MEDIUM, "3": Difficulty.HARD, "4": Difficulty.INSANE}
        return mapping.get(choice, Difficulty.HARD)

    def _after_game_menu(self) -> str:
        print()
        after_opts = [
            ("r", "Play Again",     Color.NEON_GREEN),
            ("s", "Scoreboard",     Color.NEON_GOLD),
            ("m", "Main Menu",      Color.NEON_CYAN),
            ("q", "Quit",           Color.DARK_GRAY),
        ]
        for key, label, color in after_opts:
            k = Color.style(f"  [{key}]", Color.NEON_GOLD)
            l_str = Color.style(f" {label}", color)
            print(f"{k}{l_str}")
        print()
        return self._renderer.prompt("Choice").lower()

    # ── Game Mode Handlers ────────────────────────────────────────────────────

    def _run_human_vs_ai(self) -> None:
        self._renderer.clear()
        self._renderer.render_logo()
        name = self._renderer.prompt(f"Your name [{self._config.player_x_name}]")
        if not name:
            name = self._config.player_x_name
        difficulty = self._choose_difficulty()

        while True:
            game = (
                GameBuilder()
                .human_vs_ai(human_name=name, difficulty=difficulty)
                .with_renderer(self._renderer)
                .build()
            )
            result = game.run()
            choice = self._after_game_menu()
            if choice == "r":
                game.reset()
                continue
            elif choice == "s":
                self._show_scoreboard()
            break

    def _run_human_vs_human(self) -> None:
        self._renderer.clear()
        self._renderer.render_logo()
        name_x = self._renderer.prompt(f"Player X name [{self._config.player_x_name}]")
        if not name_x:
            name_x = self._config.player_x_name
        name_o = self._renderer.prompt(f"Player O name [{self._config.player_o_name}]")
        if not name_o:
            name_o = self._config.player_o_name

        while True:
            game = (
                GameBuilder()
                .human_vs_human(name_x=name_x, name_o=name_o)
                .with_renderer(self._renderer)
                .build()
            )
            result = game.run()
            choice = self._after_game_menu()
            if choice == "r":
                game.reset()
                continue
            elif choice == "s":
                self._show_scoreboard()
            break

    def _run_ai_vs_ai(self) -> None:
        self._renderer.clear()
        self._renderer.render_logo()
        print(Color.style("  ── AI vs AI Setup ──────────────────────", Color.NEON_PURPLE))
        print()
        print(Color.style("  Configure AI-X:", Color.NEON_CYAN))
        diff_x = self._choose_difficulty()
        print(Color.style("  Configure AI-O:", Color.NEON_PINK))
        diff_o = self._choose_difficulty()

        while True:
            game = (
                GameBuilder()
                .ai_vs_ai(diff_x=diff_x, diff_o=diff_o)
                .with_renderer(self._renderer)
                .build()
            )
            result = game.run()
            choice = self._after_game_menu()
            if choice == "r":
                game.reset()
                continue
            elif choice == "s":
                self._show_scoreboard()
            break

    def _show_scoreboard(self) -> None:
        self._renderer.clear()
        self._renderer.render_logo()
        self._renderer.render_scores(self._score_manager)
        input(Color.style("  Press Enter to continue...", Color.DARK_GRAY))

    def _show_settings(self) -> None:
        while True:
            self._renderer.clear()
            self._renderer.render_logo()
            self._renderer.render_settings(self._config)
            choice = self._renderer.prompt("Option [1-4, 0=back]")

            if choice == "0":
                break
            elif choice == "1":
                self._config.show_animations = not self._config.show_animations
            elif choice == "2":
                self._config.show_move_numbers = not self._config.show_move_numbers
            elif choice == "3":
                self._config.ai_delay_enabled = not self._config.ai_delay_enabled
            elif choice == "4":
                diff = self._choose_difficulty()
                self._config.default_difficulty = diff

    # ── Main Loop ────────────────────────────────────────────────────────────

    def run(self) -> None:
        """Main application loop."""
        while self._running:
            choice = self._show_main_menu()

            if choice == "1":
                self._run_human_vs_ai()
            elif choice == "2":
                self._run_human_vs_human()
            elif choice == "3":
                self._run_ai_vs_ai()
            elif choice == "4":
                self._show_scoreboard()
            elif choice == "5":
                self._show_settings()
            elif choice == "0":
                self._exit()
                break
            else:
                print(Color.style("  ✗ Invalid option.", Color.BR_RED))
                time.sleep(0.8)

    def _exit(self) -> None:
        self._renderer.clear()
        self._renderer.render_logo()
        farewell = [
            Color.style("  Thanks for playing!", Color.NEON_GOLD, Color.BOLD),
            Color.style("  Built with ♥ and Python OOP", Color.NEON_CYAN),
            Color.style("  by Mohammed Hany", Color.NEON_PURPLE),
        ]
        for line in farewell:
            print(line)
            time.sleep(0.15)
        print()
        time.sleep(0.5)
        self._running = False


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 18 — ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def check_terminal_support() -> None:
    """Check that the terminal supports ANSI colors."""
    if platform.system() == "Windows":
        os.system("color")  # Enable ANSI on Windows
    term = os.environ.get("TERM", "")
    if not term and platform.system() != "Windows":
        print("Warning: Terminal may not support ANSI colors.")


def print_startup_banner() -> None:
    """Animated startup splash."""
    lines = [
        "",
        Color.style("  ┌─────────────────────────────────────────────────┐", Color.NEON_PURPLE),
        Color.style("  │", Color.NEON_PURPLE) + Color.style("   TIC TAC TOE — Professional OOP Edition      ", Color.NEON_GOLD, Color.BOLD) + Color.style("│", Color.NEON_PURPLE),
        Color.style("  │", Color.NEON_PURPLE) + Color.style("   Patterns: ABC · Observer · Strategy ·       ", Color.MID_GRAY) + Color.style("│", Color.NEON_PURPLE),
        Color.style("  │", Color.NEON_PURPLE) + Color.style("   Command · Factory · Singleton · Builder ·   ", Color.MID_GRAY) + Color.style("│", Color.NEON_PURPLE),
        Color.style("  │", Color.NEON_PURPLE) + Color.style("   State Machine · Decorator · Repository      ", Color.MID_GRAY) + Color.style("│", Color.NEON_PURPLE),
        Color.style("  └─────────────────────────────────────────────────┘", Color.NEON_PURPLE),
        "",
    ]
    for line in lines:
        print(line)
        time.sleep(0.07)


def main() -> None:
    """Application entry point."""
    check_terminal_support()
    print_startup_banner()
    time.sleep(0.5)

    try:
        lobby = GameLobby()
        lobby.run()
    except KeyboardInterrupt:
        print()
        print(Color.style("\n  Game interrupted. Goodbye!", Color.MID_GRAY))
        sys.exit(0)


if __name__ == "__main__":
    main()