#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║          ULTRA CALC — Advanced OOP Scientific Calculator         ║
║                   Built by Mohammed Hany                         ║
║              Architecture: Full OOP + Design Patterns            ║
╚══════════════════════════════════════════════════════════════════╝

OOP Concepts Used:
  - Abstract Base Classes (ABC)
  - Inheritance & Polymorphism
  - Encapsulation
  - Singleton Pattern (History Manager)
  - Strategy Pattern (Operations)
  - Observer Pattern (Event system)
  - Factory Pattern (Operation creation)
  - Decorator Pattern (logging & validation)
  - Command Pattern (undo/redo)
"""

import math
import os
import sys
import time
import datetime
import json
import random
from abc import ABC, abstractmethod
from typing import Optional, List, Callable, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import wraps


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 1: COLOR & STYLE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class Color:
    """
    ANSI color codes for terminal styling.
    Full color engine with foreground, background, and effects.
    """
    # Reset
    RESET        = "\033[0m"

    # Effects
    BOLD         = "\033[1m"
    DIM          = "\033[2m"
    ITALIC       = "\033[3m"
    UNDERLINE    = "\033[4m"
    BLINK        = "\033[5m"
    REVERSE      = "\033[7m"
    STRIKETHROUGH= "\033[9m"

    # Foreground colors
    BLACK        = "\033[30m"
    RED          = "\033[31m"
    GREEN        = "\033[32m"
    YELLOW       = "\033[33m"
    BLUE         = "\033[34m"
    MAGENTA      = "\033[35m"
    CYAN         = "\033[36m"
    WHITE        = "\033[37m"

    # Bright foreground
    BR_BLACK     = "\033[90m"
    BR_RED       = "\033[91m"
    BR_GREEN     = "\033[92m"
    BR_YELLOW    = "\033[93m"
    BR_BLUE      = "\033[94m"
    BR_MAGENTA   = "\033[95m"
    BR_CYAN      = "\033[96m"
    BR_WHITE     = "\033[97m"

    # Background colors
    BG_BLACK     = "\033[40m"
    BG_RED       = "\033[41m"
    BG_GREEN     = "\033[42m"
    BG_YELLOW    = "\033[43m"
    BG_BLUE      = "\033[44m"
    BG_MAGENTA   = "\033[45m"
    BG_CYAN      = "\033[46m"
    BG_WHITE     = "\033[47m"

    # Bright background
    BG_BR_BLACK  = "\033[100m"
    BG_BR_RED    = "\033[101m"
    BG_BR_GREEN  = "\033[102m"
    BG_BR_YELLOW = "\033[103m"
    BG_BR_BLUE   = "\033[104m"
    BG_BR_MAGENTA= "\033[105m"
    BG_BR_CYAN   = "\033[106m"
    BG_BR_WHITE  = "\033[107m"

    @staticmethod
    def rgb(r: int, g: int, b: int) -> str:
        """True color RGB foreground."""
        return f"\033[38;2;{r};{g};{b}m"

    @staticmethod
    def bg_rgb(r: int, g: int, b: int) -> str:
        """True color RGB background."""
        return f"\033[48;2;{r};{g};{b}m"

    @staticmethod
    def paint(text: str, *codes: str) -> str:
        """Apply multiple color codes to text and reset."""
        return "".join(codes) + text + Color.RESET


class Theme:
    """
    Calculator visual theme.
    All colors are centralized here — change the theme in one place.
    """
    PRIMARY      = Color.rgb(0,   200, 255)   # Electric cyan
    SECONDARY    = Color.rgb(255, 100, 0)     # Neon orange
    ACCENT       = Color.rgb(180, 0,   255)   # Deep violet
    SUCCESS      = Color.rgb(0,   255, 120)   # Matrix green
    WARNING      = Color.rgb(255, 220, 0)     # Solar yellow
    ERROR        = Color.rgb(255, 50,  50)    # Hot red
    MUTED        = Color.rgb(100, 120, 140)   # Slate
    HIGHLIGHT    = Color.rgb(255, 255, 100)   # Bright yellow
    BORDER       = Color.rgb(40,  80,  120)   # Dark blue-grey
    TITLE        = Color.rgb(0,   240, 200)   # Teal
    NUMBER       = Color.rgb(120, 220, 255)   # Light blue
    OPERATOR     = Color.rgb(255, 140, 60)    # Amber
    RESULT       = Color.rgb(60,  255, 160)   # Emerald

    @staticmethod
    def p(text: str) -> str:
        return Color.paint(text, Theme.PRIMARY, Color.BOLD)

    @staticmethod
    def s(text: str) -> str:
        return Color.paint(text, Theme.SECONDARY, Color.BOLD)

    @staticmethod
    def a(text: str) -> str:
        return Color.paint(text, Theme.ACCENT)

    @staticmethod
    def ok(text: str) -> str:
        return Color.paint(text, Theme.SUCCESS, Color.BOLD)

    @staticmethod
    def warn(text: str) -> str:
        return Color.paint(text, Theme.WARNING)

    @staticmethod
    def err(text: str) -> str:
        return Color.paint(text, Theme.ERROR, Color.BOLD)

    @staticmethod
    def muted(text: str) -> str:
        return Color.paint(text, Theme.MUTED)

    @staticmethod
    def hi(text: str) -> str:
        return Color.paint(text, Theme.HIGHLIGHT, Color.BOLD)

    @staticmethod
    def num(text: str) -> str:
        return Color.paint(text, Theme.NUMBER)

    @staticmethod
    def op(text: str) -> str:
        return Color.paint(text, Theme.OPERATOR, Color.BOLD)

    @staticmethod
    def res(text: str) -> str:
        return Color.paint(text, Theme.RESULT, Color.BOLD)


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 2: UI RENDERER
# ═══════════════════════════════════════════════════════════════════════════════

class UI:
    """
    Static UI rendering engine.
    Draws borders, boxes, tables, animations, and prompts.
    """
    WIDTH = 65

    @staticmethod
    def clear():
        os.system('clear' if os.name == 'posix' else 'cls')

    @staticmethod
    def _bar(left: str, fill: str, right: str, width: int = None) -> str:
        w = width or UI.WIDTH
        color = Color.rgb(40, 80, 120)
        return color + left + fill * (w - 2) + right + Color.RESET

    @staticmethod
    def top_bar(width: int = None) -> str:
        return UI._bar("╔", "═", "╗", width)

    @staticmethod
    def mid_bar(width: int = None) -> str:
        return UI._bar("╠", "═", "╣", width)

    @staticmethod
    def bot_bar(width: int = None) -> str:
        return UI._bar("╚", "═", "╝", width)

    @staticmethod
    def thin_bar(width: int = None) -> str:
        return UI._bar("╟", "─", "╢", width)

    @staticmethod
    def row(content: str, width: int = None) -> str:
        w = width or UI.WIDTH
        # Strip ANSI escape sequences to calculate true visible length
        import re
        ansi_escape = re.compile(r'\033\[[0-9;]*m')
        visible = ansi_escape.sub('', content)
        padding = w - 2 - len(visible)
        border_color = Color.rgb(40, 80, 120)
        return f"{border_color}║{Color.RESET}{content}{' ' * max(0, padding)}{border_color}║{Color.RESET}"

    @staticmethod
    def empty_row(width: int = None) -> str:
        w = width or UI.WIDTH
        border_color = Color.rgb(40, 80, 120)
        return f"{border_color}║{Color.RESET}{' ' * (w - 2)}{border_color}║{Color.RESET}"

    @staticmethod
    def center(text: str, width: int = None) -> str:
        """Center text accounting for ANSI codes."""
        import re
        w = width or UI.WIDTH - 2
        ansi_escape = re.compile(r'\033\[[0-9;]*m')
        visible_len = len(ansi_escape.sub('', text))
        pad = (w - visible_len) // 2
        return " " * pad + text + " " * (w - visible_len - pad)

    @staticmethod
    def print_box(lines: List[str], title: str = "", width: int = None):
        """Print a complete bordered box with optional title."""
        w = width or UI.WIDTH
        print(UI.top_bar(w))
        if title:
            print(UI.row(UI.center(title, w - 2), w))
            print(UI.thin_bar(w))
        for line in lines:
            print(UI.row(line, w))
        print(UI.bot_bar(w))

    @staticmethod
    def animate_text(text: str, delay: float = 0.03):
        """Typewriter animation for text."""
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print()

    @staticmethod
    def spinner(message: str, duration: float = 1.0):
        """Animated spinner for 'calculating'."""
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        end_time = time.time() + duration
        i = 0
        while time.time() < end_time:
            frame = frames[i % len(frames)]
            sys.stdout.write(f"\r  {Theme.p(frame)}  {Theme.muted(message)}   ")
            sys.stdout.flush()
            time.sleep(0.08)
            i += 1
        sys.stdout.write("\r" + " " * 50 + "\r")
        sys.stdout.flush()

    @staticmethod
    def progress_bar(label: str, duration: float = 0.4, width: int = 30):
        """Animated progress bar."""
        for i in range(width + 1):
            filled = "█" * i
            empty = "░" * (width - i)
            pct = int((i / width) * 100)
            bar = Theme.ok(filled) + Theme.muted(empty)
            sys.stdout.write(f"\r  {Theme.muted(label)}  [{bar}] {Theme.num(str(pct)+'%')}  ")
            sys.stdout.flush()
            time.sleep(duration / width)
        print()

    @staticmethod
    def input_prompt(prompt: str) -> str:
        """Styled input prompt."""
        arrow = Theme.p("▶ ")
        return input(f"\n  {arrow}{Theme.hi(prompt)} ")

    @staticmethod
    def success(message: str):
        icon = Theme.ok("✔")
        print(f"\n  {icon}  {Theme.ok(message)}")

    @staticmethod
    def error(message: str):
        icon = Theme.err("✘")
        print(f"\n  {icon}  {Theme.err(message)}")

    @staticmethod
    def warning(message: str):
        icon = Theme.warn("⚠")
        print(f"\n  {icon}  {Theme.warn(message)}")

    @staticmethod
    def info(message: str):
        icon = Theme.p("ℹ")
        print(f"\n  {icon}  {Theme.muted(message)}")

    @staticmethod
    def divider():
        color = Color.rgb(40, 60, 80)
        print(f"\n  {color}{'─' * (UI.WIDTH - 4)}{Color.RESET}\n")


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 3: CUSTOM EXCEPTIONS
# ═══════════════════════════════════════════════════════════════════════════════

class CalculatorError(Exception):
    """Base exception for all calculator errors."""
    def __init__(self, message: str, code: str = "CALC_ERR"):
        super().__init__(message)
        self.code    = code
        self.message = message
        self.ts      = datetime.datetime.now()

    def __str__(self):
        return f"[{self.code}] {self.message}"


class DivisionByZeroError(CalculatorError):
    def __init__(self):
        super().__init__("Division by zero is undefined.", "DIV_ZERO")


class NegativeSqrtError(CalculatorError):
    def __init__(self, value: float):
        super().__init__(
            f"Cannot take sqrt of a negative number ({value}).",
            "NEG_SQRT"
        )


class NegativeLogError(CalculatorError):
    def __init__(self, value: float):
        super().__init__(
            f"Logarithm undefined for non-positive numbers ({value}).",
            "NEG_LOG"
        )


class InvalidInputError(CalculatorError):
    def __init__(self, detail: str = ""):
        super().__init__(f"Invalid input. {detail}", "INV_INPUT")


class MemoryError(CalculatorError):
    def __init__(self, slot: int):
        super().__init__(f"Memory slot {slot} is empty.", "MEM_EMPTY")


class UndoError(CalculatorError):
    def __init__(self):
        super().__init__("Nothing to undo.", "UNDO_EMPTY")


class RedoError(CalculatorError):
    def __init__(self):
        super().__init__("Nothing to redo.", "REDO_EMPTY")


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 4: DATA CLASSES & ENUMS
# ═══════════════════════════════════════════════════════════════════════════════

class AngleUnit(Enum):
    """Unit for trigonometric functions."""
    DEGREES = auto()
    RADIANS = auto()
    GRADIANS = auto()

    def label(self) -> str:
        return {
            AngleUnit.DEGREES:  "DEG",
            AngleUnit.RADIANS:  "RAD",
            AngleUnit.GRADIANS: "GRAD",
        }[self]

    def to_radians(self, value: float) -> float:
        """Convert any angle unit to radians."""
        if self == AngleUnit.DEGREES:
            return math.radians(value)
        elif self == AngleUnit.GRADIANS:
            return value * math.pi / 200
        return value  # already radians


class OperationCategory(Enum):
    ARITHMETIC  = "Arithmetic"
    TRIGONOMETRY= "Trigonometry"
    ALGEBRA     = "Algebra"
    LOGARITHM   = "Logarithm"
    STATISTICS  = "Statistics"
    BITWISE     = "Bitwise"
    MEMORY      = "Memory"
    CONVERSION  = "Conversion"


@dataclass
class OperationResult:
    """
    Immutable data class representing the result of one calculation.
    Stored in history.
    """
    expression: str
    result:     Any
    category:   OperationCategory
    timestamp:  datetime.datetime = field(default_factory=datetime.datetime.now)
    angle_unit: str = "DEG"
    error:      Optional[str] = None
    is_error:   bool = False

    def display_line(self) -> str:
        ts = self.timestamp.strftime("%H:%M:%S")
        cat = Theme.a(f"[{self.category.value[:4].upper()}]")
        time_str = Theme.muted(f"[{ts}]")
        if self.is_error:
            expr = Theme.muted(self.expression)
            res  = Theme.err(f"✘ {self.error}")
        else:
            expr = Theme.num(self.expression)
            res  = Theme.res(f"= {self.result}")
        return f" {time_str} {cat} {expr} {res}"


@dataclass
class MemoryCell:
    """Represents one memory storage cell."""
    slot:  int
    value: Optional[float] = None
    label: str = ""

    def is_empty(self) -> bool:
        return self.value is None

    def store(self, value: float, label: str = ""):
        self.value = value
        self.label = label

    def recall(self) -> float:
        if self.is_empty():
            raise MemoryError(self.slot)
        return self.value

    def clear(self):
        self.value = None
        self.label = ""

    def display(self) -> str:
        if self.is_empty():
            val_str = Theme.muted("empty")
        else:
            val_str = Theme.res(str(self.value))
            if self.label:
                val_str += Theme.muted(f"  ({self.label})")
        return f"  M{self.slot}: {val_str}"


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 5: ABSTRACT OPERATION BASE — STRATEGY PATTERN
# ═══════════════════════════════════════════════════════════════════════════════

class Operation(ABC):
    """
    Abstract base class for every calculator operation.
    All operations must implement execute() and describe().
    This is the Strategy Pattern — each operation is an interchangeable strategy.
    """

    def __init__(self):
        self._category = OperationCategory.ARITHMETIC

    @property
    def category(self) -> OperationCategory:
        return self._category

    @abstractmethod
    def execute(self, *args: float, **kwargs) -> float:
        """Perform the calculation and return a numeric result."""
        pass

    @abstractmethod
    def describe(self, *args: float, **kwargs) -> str:
        """Return a human-readable expression string."""
        pass

    @abstractmethod
    def symbol(self) -> str:
        """Short symbol used in menus."""
        pass

    @abstractmethod
    def name(self) -> str:
        """Full display name."""
        pass

    @abstractmethod
    def arity(self) -> int:
        """How many operands this operation needs (1 or 2)."""
        pass

    def validate(self, *args: float):
        """
        Override this method in subclasses to validate inputs
        before execute() is called.
        Raise a CalculatorError if input is invalid.
        """
        pass

    def run(self, *args: float, **kwargs) -> OperationResult:
        """
        Full pipeline: validate → execute → wrap in OperationResult.
        """
        try:
            self.validate(*args, **kwargs)
            result = self.execute(*args, **kwargs)
            expr   = self.describe(*args, **kwargs)
            return OperationResult(
                expression=expr,
                result=self._format(result),
                category=self._category
            )
        except CalculatorError as e:
            expr = self.describe(*args, **kwargs)
            return OperationResult(
                expression=expr,
                result=None,
                category=self._category,
                error=str(e),
                is_error=True
            )

    @staticmethod
    def _format(value: float) -> str:
        """Format a float nicely — no unnecessary trailing zeros."""
        if isinstance(value, float):
            if value == int(value) and abs(value) < 1e15:
                return str(int(value))
            return f"{value:.10g}"
        return str(value)


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 6: ARITHMETIC OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

class AddOperation(Operation):
    def name(self):    return "Addition"
    def symbol(self):  return "+"
    def arity(self):   return 2

    def execute(self, a: float, b: float, **kw) -> float:
        return a + b

    def describe(self, a: float, b: float, **kw) -> str:
        return f"{a} + {b}"


class SubtractOperation(Operation):
    def name(self):    return "Subtraction"
    def symbol(self):  return "−"
    def arity(self):   return 2

    def execute(self, a: float, b: float, **kw) -> float:
        return a - b

    def describe(self, a: float, b: float, **kw) -> str:
        return f"{a} − {b}"


class MultiplyOperation(Operation):
    def name(self):    return "Multiplication"
    def symbol(self):  return "×"
    def arity(self):   return 2

    def execute(self, a: float, b: float, **kw) -> float:
        return a * b

    def describe(self, a: float, b: float, **kw) -> str:
        return f"{a} × {b}"


class DivideOperation(Operation):
    def name(self):    return "Division"
    def symbol(self):  return "÷"
    def arity(self):   return 2

    def validate(self, a: float, b: float, **kw):
        if b == 0:
            raise DivisionByZeroError()

    def execute(self, a: float, b: float, **kw) -> float:
        return a / b

    def describe(self, a: float, b: float, **kw) -> str:
        return f"{a} ÷ {b}"


class FloorDivideOperation(Operation):
    def name(self):    return "Floor Division"
    def symbol(self):  return "//‌"
    def arity(self):   return 2

    def validate(self, a: float, b: float, **kw):
        if b == 0:
            raise DivisionByZeroError()

    def execute(self, a: float, b: float, **kw) -> float:
        return a // b

    def describe(self, a: float, b: float, **kw) -> str:
        return f"⌊{a} ÷ {b}⌋"


class ModuloOperation(Operation):
    def name(self):    return "Modulo (Remainder)"
    def symbol(self):  return "%"
    def arity(self):   return 2

    def validate(self, a: float, b: float, **kw):
        if b == 0:
            raise DivisionByZeroError()

    def execute(self, a: float, b: float, **kw) -> float:
        return a % b

    def describe(self, a: float, b: float, **kw) -> str:
        return f"{a} mod {b}"


class PowerOperation(Operation):
    def name(self):    return "Power (xⁿ)"
    def symbol(self):  return "^"
    def arity(self):   return 2

    def execute(self, a: float, b: float, **kw) -> float:
        return a ** b

    def describe(self, a: float, b: float, **kw) -> str:
        return f"{a} ^ {b}"


class SqrtOperation(Operation):
    def name(self):    return "Square Root (√x)"
    def symbol(self):  return "√"
    def arity(self):   return 1

    def validate(self, a: float, **kw):
        if a < 0:
            raise NegativeSqrtError(a)

    def execute(self, a: float, **kw) -> float:
        return math.sqrt(a)

    def describe(self, a: float, **kw) -> str:
        return f"√{a}"


class CbrtOperation(Operation):
    def name(self):    return "Cube Root (∛x)"
    def symbol(self):  return "∛"
    def arity(self):   return 1

    def execute(self, a: float, **kw) -> float:
        if a < 0:
            return -((-a) ** (1/3))
        return a ** (1/3)

    def describe(self, a: float, **kw) -> str:
        return f"∛{a}"


class NthRootOperation(Operation):
    def name(self):    return "Nth Root (ⁿ√x)"
    def symbol(self):  return "ⁿ√"
    def arity(self):   return 2

    def execute(self, a: float, n: float, **kw) -> float:
        if n == 0:
            raise InvalidInputError("Root index cannot be 0.")
        if a < 0 and n % 2 == 0:
            raise NegativeSqrtError(a)
        return a ** (1 / n)

    def describe(self, a: float, n: float, **kw) -> str:
        return f"{int(n)}√{a}"


class AbsoluteOperation(Operation):
    def name(self):    return "Absolute Value |x|"
    def symbol(self):  return "|x|"
    def arity(self):   return 1

    def execute(self, a: float, **kw) -> float:
        return abs(a)

    def describe(self, a: float, **kw) -> str:
        return f"|{a}|"


class ReciprocalOperation(Operation):
    def name(self):    return "Reciprocal (1/x)"
    def symbol(self):  return "1/x"
    def arity(self):   return 1

    def validate(self, a: float, **kw):
        if a == 0:
            raise DivisionByZeroError()

    def execute(self, a: float, **kw) -> float:
        return 1 / a

    def describe(self, a: float, **kw) -> str:
        return f"1 ÷ {a}"


class PercentOperation(Operation):
    def name(self):    return "Percent (%)"
    def symbol(self):  return "%"
    def arity(self):   return 1

    def execute(self, a: float, **kw) -> float:
        return a / 100

    def describe(self, a: float, **kw) -> str:
        return f"{a}%"


class FactorialOperation(Operation):
    def name(self):    return "Factorial (n!)"
    def symbol(self):  return "n!"
    def arity(self):   return 1

    def validate(self, a: float, **kw):
        if a < 0:
            raise InvalidInputError("Factorial undefined for negative numbers.")
        if a != int(a):
            raise InvalidInputError("Factorial requires a whole number.")
        if a > 170:
            raise InvalidInputError("Number too large for factorial (max 170).")

    def execute(self, a: float, **kw) -> float:
        return float(math.factorial(int(a)))

    def describe(self, a: float, **kw) -> str:
        return f"{int(a)}!"


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 7: TRIGONOMETRIC OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

class TrigOperation(Operation):
    """Base for all trig operations — handles angle unit conversion."""

    def __init__(self):
        super().__init__()
        self._category  = OperationCategory.TRIGONOMETRY
        self._angle_unit: AngleUnit = AngleUnit.DEGREES

    def set_angle_unit(self, unit: AngleUnit):
        self._angle_unit = unit

    def _to_rad(self, value: float) -> float:
        return self._angle_unit.to_radians(value)


class SinOperation(TrigOperation):
    def name(self):    return "Sine (sin)"
    def symbol(self):  return "sin"
    def arity(self):   return 1

    def execute(self, a: float, **kw) -> float:
        return math.sin(self._to_rad(a))

    def describe(self, a: float, **kw) -> str:
        return f"sin({a}°)"


class CosOperation(TrigOperation):
    def name(self):    return "Cosine (cos)"
    def symbol(self):  return "cos"
    def arity(self):   return 1

    def execute(self, a: float, **kw) -> float:
        return math.cos(self._to_rad(a))

    def describe(self, a: float, **kw) -> str:
        return f"cos({a}°)"


class TanOperation(TrigOperation):
    def name(self):    return "Tangent (tan)"
    def symbol(self):  return "tan"
    def arity(self):   return 1

    def validate(self, a: float, **kw):
        rad = self._to_rad(a)
        if abs(math.cos(rad)) < 1e-10:
            raise InvalidInputError(f"tan({a}°) is undefined (vertical asymptote).")

    def execute(self, a: float, **kw) -> float:
        return math.tan(self._to_rad(a))

    def describe(self, a: float, **kw) -> str:
        return f"tan({a}°)"


class AsinOperation(TrigOperation):
    def name(self):    return "Arc Sine (asin)"
    def symbol(self):  return "asin"
    def arity(self):   return 1

    def validate(self, a: float, **kw):
        if not (-1 <= a <= 1):
            raise InvalidInputError(f"asin input must be between -1 and 1 (got {a}).")

    def execute(self, a: float, **kw) -> float:
        return math.degrees(math.asin(a))

    def describe(self, a: float, **kw) -> str:
        return f"asin({a})"


class AcosOperation(TrigOperation):
    def name(self):    return "Arc Cosine (acos)"
    def symbol(self):  return "acos"
    def arity(self):   return 1

    def validate(self, a: float, **kw):
        if not (-1 <= a <= 1):
            raise InvalidInputError(f"acos input must be between -1 and 1 (got {a}).")

    def execute(self, a: float, **kw) -> float:
        return math.degrees(math.acos(a))

    def describe(self, a: float, **kw) -> str:
        return f"acos({a})"


class AtanOperation(TrigOperation):
    def name(self):    return "Arc Tangent (atan)"
    def symbol(self):  return "atan"
    def arity(self):   return 1

    def execute(self, a: float, **kw) -> float:
        return math.degrees(math.atan(a))

    def describe(self, a: float, **kw) -> str:
        return f"atan({a})"


class SinhOperation(TrigOperation):
    def name(self):    return "Hyperbolic Sine (sinh)"
    def symbol(self):  return "sinh"
    def arity(self):   return 1

    def execute(self, a: float, **kw) -> float:
        return math.sinh(a)

    def describe(self, a: float, **kw) -> str:
        return f"sinh({a})"


class CoshOperation(TrigOperation):
    def name(self):    return "Hyperbolic Cosine (cosh)"
    def symbol(self):  return "cosh"
    def arity(self):   return 1

    def execute(self, a: float, **kw) -> float:
        return math.cosh(a)

    def describe(self, a: float, **kw) -> str:
        return f"cosh({a})"


class TanhOperation(TrigOperation):
    def name(self):    return "Hyperbolic Tangent (tanh)"
    def symbol(self):  return "tanh"
    def arity(self):   return 1

    def execute(self, a: float, **kw) -> float:
        return math.tanh(a)

    def describe(self, a: float, **kw) -> str:
        return f"tanh({a})"


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 8: LOGARITHMIC OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

class LogOperation(Operation):
    def __init__(self):
        super().__init__()
        self._category = OperationCategory.LOGARITHM

    def name(self):    return "Natural Log (ln)"
    def symbol(self):  return "ln"
    def arity(self):   return 1

    def validate(self, a: float, **kw):
        if a <= 0:
            raise NegativeLogError(a)

    def execute(self, a: float, **kw) -> float:
        return math.log(a)

    def describe(self, a: float, **kw) -> str:
        return f"ln({a})"


class Log10Operation(Operation):
    def __init__(self):
        super().__init__()
        self._category = OperationCategory.LOGARITHM

    def name(self):    return "Log Base 10 (log₁₀)"
    def symbol(self):  return "log₁₀"
    def arity(self):   return 1

    def validate(self, a: float, **kw):
        if a <= 0:
            raise NegativeLogError(a)

    def execute(self, a: float, **kw) -> float:
        return math.log10(a)

    def describe(self, a: float, **kw) -> str:
        return f"log₁₀({a})"


class Log2Operation(Operation):
    def __init__(self):
        super().__init__()
        self._category = OperationCategory.LOGARITHM

    def name(self):    return "Log Base 2 (log₂)"
    def symbol(self):  return "log₂"
    def arity(self):   return 1

    def validate(self, a: float, **kw):
        if a <= 0:
            raise NegativeLogError(a)

    def execute(self, a: float, **kw) -> float:
        return math.log2(a)

    def describe(self, a: float, **kw) -> str:
        return f"log₂({a})"


class LogBaseOperation(Operation):
    def __init__(self):
        super().__init__()
        self._category = OperationCategory.LOGARITHM

    def name(self):    return "Log Arbitrary Base"
    def symbol(self):  return "logₙ"
    def arity(self):   return 2

    def validate(self, a: float, base: float, **kw):
        if a <= 0:
            raise NegativeLogError(a)
        if base <= 0 or base == 1:
            raise InvalidInputError("Log base must be > 0 and ≠ 1.")

    def execute(self, a: float, base: float, **kw) -> float:
        return math.log(a, base)

    def describe(self, a: float, base: float, **kw) -> str:
        return f"log_{int(base)}({a})"


class ExpOperation(Operation):
    def __init__(self):
        super().__init__()
        self._category = OperationCategory.LOGARITHM

    def name(self):    return "Exponential (eˣ)"
    def symbol(self):  return "eˣ"
    def arity(self):   return 1

    def execute(self, a: float, **kw) -> float:
        return math.exp(a)

    def describe(self, a: float, **kw) -> str:
        return f"e^{a}"


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 9: STATISTICS OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

class StatisticsOperation(ABC):
    """
    Base for operations that take a list of numbers.
    Different from binary/unary Operation — uses a sequence.
    """
    def __init__(self):
        self._category = OperationCategory.STATISTICS

    @abstractmethod
    def compute(self, numbers: List[float]) -> float:
        pass

    @abstractmethod
    def name(self) -> str:
        pass


class MeanOperation(StatisticsOperation):
    def name(self): return "Arithmetic Mean (avg)"

    def compute(self, numbers: List[float]) -> float:
        if not numbers:
            raise InvalidInputError("Need at least one number.")
        return sum(numbers) / len(numbers)


class MedianOperation(StatisticsOperation):
    def name(self): return "Median"

    def compute(self, numbers: List[float]) -> float:
        if not numbers:
            raise InvalidInputError("Need at least one number.")
        s = sorted(numbers)
        n = len(s)
        mid = n // 2
        return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2


class ModeOperation(StatisticsOperation):
    def name(self): return "Mode"

    def compute(self, numbers: List[float]) -> float:
        from collections import Counter
        if not numbers:
            raise InvalidInputError("Need at least one number.")
        count = Counter(numbers)
        return count.most_common(1)[0][0]


class StdDevOperation(StatisticsOperation):
    def name(self): return "Standard Deviation (σ)"

    def compute(self, numbers: List[float]) -> float:
        if len(numbers) < 2:
            raise InvalidInputError("Need at least 2 numbers for std dev.")
        mean = sum(numbers) / len(numbers)
        variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
        return math.sqrt(variance)


class SumOperation(StatisticsOperation):
    def name(self): return "Sum (Σ)"

    def compute(self, numbers: List[float]) -> float:
        return sum(numbers)


class RangeStatOperation(StatisticsOperation):
    def name(self): return "Range (max − min)"

    def compute(self, numbers: List[float]) -> float:
        if not numbers:
            raise InvalidInputError("Need at least one number.")
        return max(numbers) - min(numbers)


class GeoMeanOperation(StatisticsOperation):
    def name(self): return "Geometric Mean"

    def compute(self, numbers: List[float]) -> float:
        if not numbers:
            raise InvalidInputError("Need at least one number.")
        if any(x <= 0 for x in numbers):
            raise InvalidInputError("All numbers must be positive for geometric mean.")
        product = 1
        for x in numbers:
            product *= x
        return product ** (1 / len(numbers))


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 10: BITWISE OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

class BitwiseOperation(Operation):
    def __init__(self):
        super().__init__()
        self._category = OperationCategory.BITWISE

    def _require_int(self, *values: float):
        for v in values:
            if v != int(v):
                raise InvalidInputError("Bitwise operations require whole numbers.")

    def _to_int(self, v: float) -> int:
        return int(v)


class BitwiseAndOperation(BitwiseOperation):
    def name(self):    return "Bitwise AND (&)"
    def symbol(self):  return "&"
    def arity(self):   return 2

    def validate(self, a: float, b: float, **kw):
        self._require_int(a, b)

    def execute(self, a: float, b: float, **kw) -> float:
        return float(self._to_int(a) & self._to_int(b))

    def describe(self, a: float, b: float, **kw) -> str:
        return f"{int(a)} & {int(b)}"


class BitwiseOrOperation(BitwiseOperation):
    def name(self):    return "Bitwise OR (|)"
    def symbol(self):  return "|"
    def arity(self):   return 2

    def validate(self, a: float, b: float, **kw):
        self._require_int(a, b)

    def execute(self, a: float, b: float, **kw) -> float:
        return float(self._to_int(a) | self._to_int(b))

    def describe(self, a: float, b: float, **kw) -> str:
        return f"{int(a)} | {int(b)}"


class BitwiseXorOperation(BitwiseOperation):
    def name(self):    return "Bitwise XOR (^)"
    def symbol(self):  return "XOR"
    def arity(self):   return 2

    def validate(self, a: float, b: float, **kw):
        self._require_int(a, b)

    def execute(self, a: float, b: float, **kw) -> float:
        return float(self._to_int(a) ^ self._to_int(b))

    def describe(self, a: float, b: float, **kw) -> str:
        return f"{int(a)} XOR {int(b)}"


class BitwiseNotOperation(BitwiseOperation):
    def name(self):    return "Bitwise NOT (~)"
    def symbol(self):  return "~"
    def arity(self):   return 1

    def validate(self, a: float, **kw):
        self._require_int(a)

    def execute(self, a: float, **kw) -> float:
        return float(~self._to_int(a))

    def describe(self, a: float, **kw) -> str:
        return f"~{int(a)}"


class LeftShiftOperation(BitwiseOperation):
    def name(self):    return "Left Shift (<<)"
    def symbol(self):  return "<<"
    def arity(self):   return 2

    def validate(self, a: float, b: float, **kw):
        self._require_int(a, b)
        if b < 0:
            raise InvalidInputError("Shift amount cannot be negative.")

    def execute(self, a: float, b: float, **kw) -> float:
        return float(self._to_int(a) << self._to_int(b))

    def describe(self, a: float, b: float, **kw) -> str:
        return f"{int(a)} << {int(b)}"


class RightShiftOperation(BitwiseOperation):
    def name(self):    return "Right Shift (>>)"
    def symbol(self):  return ">>"
    def arity(self):   return 2

    def validate(self, a: float, b: float, **kw):
        self._require_int(a, b)
        if b < 0:
            raise InvalidInputError("Shift amount cannot be negative.")

    def execute(self, a: float, b: float, **kw) -> float:
        return float(self._to_int(a) >> self._to_int(b))

    def describe(self, a: float, b: float, **kw) -> str:
        return f"{int(a)} >> {int(b)}"


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 11: HISTORY MANAGER — SINGLETON PATTERN
# ═══════════════════════════════════════════════════════════════════════════════

class HistoryManager:
    """
    Singleton class that manages the complete calculation history.
    Only ONE instance of this class ever exists.
    Implements the Singleton pattern.
    """
    _instance: Optional['HistoryManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._records: List[OperationResult] = []
            cls._instance._max_size: int = 200
        return cls._instance

    def push(self, result: OperationResult):
        self._records.append(result)
        if len(self._records) > self._max_size:
            self._records.pop(0)

    def all(self) -> List[OperationResult]:
        return list(self._records)

    def last(self, n: int = 10) -> List[OperationResult]:
        return self._records[-n:]

    def by_category(self, cat: OperationCategory) -> List[OperationResult]:
        return [r for r in self._records if r.category == cat]

    def clear(self):
        self._records.clear()

    def count(self) -> int:
        return len(self._records)

    def export_json(self, path: str):
        data = []
        for r in self._records:
            data.append({
                "expression": r.expression,
                "result":     str(r.result),
                "category":   r.category.value,
                "timestamp":  r.timestamp.isoformat(),
                "is_error":   r.is_error,
                "error":      r.error,
            })
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        return path

    def last_result_value(self) -> Optional[float]:
        """Returns the numeric result of the last successful operation."""
        for r in reversed(self._records):
            if not r.is_error and r.result is not None:
                try:
                    return float(r.result)
                except (ValueError, TypeError):
                    continue
        return None


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 12: MEMORY MANAGER
# ═══════════════════════════════════════════════════════════════════════════════

class MemoryManager:
    """
    Manages 10 independent memory slots.
    Each slot can store a labeled float value.
    """
    NUM_SLOTS = 10

    def __init__(self):
        self._cells: List[MemoryCell] = [
            MemoryCell(i) for i in range(self.NUM_SLOTS)
        ]

    def store(self, slot: int, value: float, label: str = ""):
        self._validate_slot(slot)
        self._cells[slot].store(value, label)

    def recall(self, slot: int) -> float:
        self._validate_slot(slot)
        return self._cells[slot].recall()

    def clear(self, slot: int):
        self._validate_slot(slot)
        self._cells[slot].clear()

    def clear_all(self):
        for cell in self._cells:
            cell.clear()

    def is_empty(self, slot: int) -> bool:
        self._validate_slot(slot)
        return self._cells[slot].is_empty()

    def add_to(self, slot: int, value: float):
        """M+ operation — add value to existing memory slot."""
        self._validate_slot(slot)
        if self._cells[slot].is_empty():
            self._cells[slot].store(value)
        else:
            self._cells[slot].store(self._cells[slot].value + value)

    def subtract_from(self, slot: int, value: float):
        """M- operation — subtract value from memory slot."""
        self._validate_slot(slot)
        if self._cells[slot].is_empty():
            self._cells[slot].store(-value)
        else:
            self._cells[slot].store(self._cells[slot].value - value)

    def display_all(self):
        for cell in self._cells:
            print(cell.display())

    def _validate_slot(self, slot: int):
        if not (0 <= slot < self.NUM_SLOTS):
            raise InvalidInputError(
                f"Memory slot must be 0–{self.NUM_SLOTS - 1} (got {slot})."
            )


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 13: COMMAND PATTERN (UNDO / REDO)
# ═══════════════════════════════════════════════════════════════════════════════

class Command(ABC):
    """Abstract command — supports undo/redo."""

    @abstractmethod
    def execute(self) -> Any:
        pass

    @abstractmethod
    def undo(self) -> str:
        pass

    def redo(self) -> Any:
        return self.execute()


class CalculationCommand(Command):
    """Wraps an Operation into a Command for undo/redo support."""

    def __init__(
        self,
        operation:  Operation,
        args:       Tuple[float, ...],
        history:    HistoryManager,
    ):
        self._operation = operation
        self._args      = args
        self._history   = history
        self._result:   Optional[OperationResult] = None

    def execute(self) -> OperationResult:
        self._result = self._operation.run(*self._args)
        self._history.push(self._result)
        return self._result

    def undo(self) -> str:
        """Remove this result from history."""
        records = self._history.all()
        if self._result in records:
            self._history._records.remove(self._result)
            return f"Undone: {self._result.expression}"
        return "Nothing to undo."


class CommandInvoker:
    """
    Manages the command stack for undo/redo.
    Implements the Invoker in the Command Pattern.
    """

    def __init__(self):
        self._done:   List[Command] = []
        self._undone: List[Command] = []
        self._max:    int = 50

    def run(self, cmd: Command) -> Any:
        result = cmd.execute()
        self._done.append(cmd)
        self._undone.clear()
        if len(self._done) > self._max:
            self._done.pop(0)
        return result

    def undo(self) -> str:
        if not self._done:
            raise UndoError()
        cmd = self._done.pop()
        msg = cmd.undo()
        self._undone.append(cmd)
        return msg

    def redo(self) -> Any:
        if not self._undone:
            raise RedoError()
        cmd = self._undone.pop()
        result = cmd.redo()
        self._done.append(cmd)
        return result

    def can_undo(self) -> bool:
        return len(self._done) > 0

    def can_redo(self) -> bool:
        return len(self._undone) > 0


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 14: OBSERVER PATTERN (EVENT SYSTEM)
# ═══════════════════════════════════════════════════════════════════════════════

class EventType(Enum):
    CALCULATION_DONE  = "calculation_done"
    ERROR_OCCURRED    = "error_occurred"
    HISTORY_CLEARED   = "history_cleared"
    MEMORY_STORED     = "memory_stored"
    MEMORY_RECALLED   = "memory_recalled"
    ANGLE_UNIT_CHANGED= "angle_unit_changed"


class Observer(ABC):
    """Abstract observer in the Observer Pattern."""

    @abstractmethod
    def on_event(self, event_type: EventType, data: Any):
        pass


class EventBus:
    """
    Simple event bus — the Subject in the Observer Pattern.
    Components subscribe to events and get notified.
    """

    def __init__(self):
        self._listeners: Dict[EventType, List[Observer]] = {
            et: [] for et in EventType
        }

    def subscribe(self, event: EventType, observer: Observer):
        self._listeners[event].append(observer)

    def emit(self, event: EventType, data: Any = None):
        for observer in self._listeners[event]:
            observer.on_event(event, data)


class SoundObserver(Observer):
    """Makes terminal bell sound on errors (optional)."""

    def on_event(self, event_type: EventType, data: Any):
        if event_type == EventType.ERROR_OCCURRED:
            sys.stdout.write("\a")
            sys.stdout.flush()


class LogObserver(Observer):
    """Silently logs all events for diagnostics."""

    def __init__(self):
        self._log: List[str] = []

    def on_event(self, event_type: EventType, data: Any):
        entry = f"{datetime.datetime.now().isoformat()} | {event_type.value} | {data}"
        self._log.append(entry)

    def get_log(self) -> List[str]:
        return list(self._log)


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 15: FACTORY PATTERN — OPERATION REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

class OperationFactory:
    """
    Factory that creates and organizes all available operations.
    Implements the Factory Pattern.
    New operations only need to be registered here — nothing else changes.
    """

    def __init__(self):
        self._registry: Dict[str, Operation] = {}
        self._categories: Dict[OperationCategory, List[str]] = {
            cat: [] for cat in OperationCategory
        }
        self._register_all()

    def _register(self, key: str, op: Operation):
        self._registry[key] = op
        self._categories[op.category].append(key)

    def _register_all(self):
        # Arithmetic
        self._register("add",        AddOperation())
        self._register("sub",        SubtractOperation())
        self._register("mul",        MultiplyOperation())
        self._register("div",        DivideOperation())
        self._register("fdiv",       FloorDivideOperation())
        self._register("mod",        ModuloOperation())
        self._register("pow",        PowerOperation())
        self._register("sqrt",       SqrtOperation())
        self._register("cbrt",       CbrtOperation())
        self._register("nthroot",    NthRootOperation())
        self._register("abs",        AbsoluteOperation())
        self._register("recip",      ReciprocalOperation())
        self._register("pct",        PercentOperation())
        self._register("fact",       FactorialOperation())

        # Trigonometry
        self._register("sin",        SinOperation())
        self._register("cos",        CosOperation())
        self._register("tan",        TanOperation())
        self._register("asin",       AsinOperation())
        self._register("acos",       AcosOperation())
        self._register("atan",       AtanOperation())
        self._register("sinh",       SinhOperation())
        self._register("cosh",       CoshOperation())
        self._register("tanh",       TanhOperation())

        # Logarithm
        self._register("ln",         LogOperation())
        self._register("log10",      Log10Operation())
        self._register("log2",       Log2Operation())
        self._register("logn",       LogBaseOperation())
        self._register("exp",        ExpOperation())

        # Bitwise
        self._register("band",       BitwiseAndOperation())
        self._register("bor",        BitwiseOrOperation())
        self._register("bxor",       BitwiseXorOperation())
        self._register("bnot",       BitwiseNotOperation())
        self._register("lsh",        LeftShiftOperation())
        self._register("rsh",        RightShiftOperation())

    def get(self, key: str) -> Optional[Operation]:
        return self._registry.get(key)

    def keys_by_category(self, cat: OperationCategory) -> List[str]:
        return self._categories.get(cat, [])

    def all_keys(self) -> List[str]:
        return list(self._registry.keys())

    def set_angle_unit(self, unit: AngleUnit):
        """Push angle unit to all trig operations."""
        for op in self._registry.values():
            if isinstance(op, TrigOperation):
                op.set_angle_unit(unit)


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 16: UNIT CONVERTER
# ═══════════════════════════════════════════════════════════════════════════════

class UnitConverter:
    """
    Converts between common units.
    Each conversion is a pair (from_unit → to_unit, factor).
    """

    _conversions: Dict[str, Dict[str, float]] = {
        "length": {
            "m":  1.0,
            "km": 0.001,
            "cm": 100,
            "mm": 1000,
            "mi": 0.000621371,
            "yd": 1.09361,
            "ft": 3.28084,
            "in": 39.3701,
        },
        "weight": {
            "kg":  1.0,
            "g":   1000,
            "mg":  1_000_000,
            "lb":  2.20462,
            "oz":  35.274,
            "ton": 0.001,
        },
        "temperature": {},  # Special case — handled separately
        "area": {
            "m2":  1.0,
            "km2": 0.000001,
            "cm2": 10000,
            "ft2": 10.7639,
            "in2": 1550.0,
            "ac":  0.000247105,
            "ha":  0.0001,
        },
        "speed": {
            "ms":   1.0,
            "kmh":  3.6,
            "mph":  2.23694,
            "knot": 1.94384,
        },
    }

    @staticmethod
    def convert_length(value: float, from_u: str, to_u: str) -> float:
        table = UnitConverter._conversions["length"]
        UnitConverter._check(from_u, to_u, table)
        base = value / table[from_u]
        return base * table[to_u]

    @staticmethod
    def convert_weight(value: float, from_u: str, to_u: str) -> float:
        table = UnitConverter._conversions["weight"]
        UnitConverter._check(from_u, to_u, table)
        base = value / table[from_u]
        return base * table[to_u]

    @staticmethod
    def convert_temperature(value: float, from_u: str, to_u: str) -> float:
        from_u, to_u = from_u.lower(), to_u.lower()
        # Convert to Celsius first
        if from_u == "c":
            c = value
        elif from_u == "f":
            c = (value - 32) * 5 / 9
        elif from_u == "k":
            c = value - 273.15
        else:
            raise InvalidInputError(f"Unknown temperature unit: {from_u}")

        # Convert from Celsius to target
        if to_u == "c":
            return c
        elif to_u == "f":
            return c * 9 / 5 + 32
        elif to_u == "k":
            return c + 273.15
        else:
            raise InvalidInputError(f"Unknown temperature unit: {to_u}")

    @staticmethod
    def convert_speed(value: float, from_u: str, to_u: str) -> float:
        table = UnitConverter._conversions["speed"]
        UnitConverter._check(from_u, to_u, table)
        base = value / table[from_u]
        return base * table[to_u]

    @staticmethod
    def _check(from_u: str, to_u: str, table: dict):
        if from_u not in table:
            raise InvalidInputError(f"Unknown unit: {from_u}")
        if to_u not in table:
            raise InvalidInputError(f"Unknown unit: {to_u}")


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 17: CONSTANTS DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MathConstant:
    name:    str
    symbol:  str
    value:   float
    description: str


class ConstantsDB:
    """Collection of important mathematical and physical constants."""

    CONSTANTS: List[MathConstant] = [
        MathConstant("Pi",              "π",   math.pi,         "Ratio of circumference to diameter"),
        MathConstant("Euler's Number",  "e",   math.e,          "Base of natural logarithm"),
        MathConstant("Golden Ratio",    "φ",   (1+math.sqrt(5))/2, "φ = (1+√5)/2"),
        MathConstant("Square Root 2",   "√2",  math.sqrt(2),    "Diagonal of unit square"),
        MathConstant("Square Root 3",   "√3",  math.sqrt(3),    "Height of equilateral triangle"),
        MathConstant("Tau",             "τ",   2 * math.pi,     "τ = 2π, full turn in radians"),
        MathConstant("Euler-Mascheroni","γ",   0.5772156649,    "Euler-Mascheroni constant"),
        MathConstant("Catalan",         "G",   0.9159655941,    "Catalan's constant"),
        MathConstant("Apery",           "ζ(3)",1.2020569031,    "Apéry's constant"),
        MathConstant("Speed of Light",  "c",   299_792_458.0,   "m/s in vacuum"),
        MathConstant("Planck",          "h",   6.62607015e-34,  "Planck constant (J·s)"),
        MathConstant("Boltzmann",       "kB",  1.380649e-23,    "Boltzmann constant (J/K)"),
        MathConstant("Avogadro",        "Nₐ",  6.02214076e23,   "Avogadro's number (mol⁻¹)"),
        MathConstant("Gravitational",   "G",   6.674e-11,       "Gravitational constant (m³kg⁻¹s⁻²)"),
        MathConstant("Earth Gravity",   "g",   9.80665,         "Standard gravity (m/s²)"),
    ]

    @classmethod
    def display_all(cls):
        print(UI.top_bar())
        print(UI.row(UI.center(Theme.p("  MATHEMATICAL & PHYSICAL CONSTANTS  "))))
        print(UI.thin_bar())
        for i, c in enumerate(cls.CONSTANTS):
            sym   = Theme.s(f" {c.symbol:<5}")
            name  = Theme.num(f"{c.name:<22}")
            val   = Theme.res(f"{c.value:.10g}")
            desc  = Theme.muted(f"  {c.description}")
            line  = f" {i+1:>2}. {sym} {name} {val}"
            print(UI.row(line))
        print(UI.bot_bar())

    @classmethod
    def get_by_index(cls, index: int) -> MathConstant:
        if not (1 <= index <= len(cls.CONSTANTS)):
            raise InvalidInputError(f"Pick 1–{len(cls.CONSTANTS)}.")
        return cls.CONSTANTS[index - 1]


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 18: NUMBER BASE CONVERTER
# ═══════════════════════════════════════════════════════════════════════════════

class BaseConverter:
    """
    Converts integers between number bases (binary, octal, decimal, hex).
    """

    @staticmethod
    def to_binary(n: int) -> str:
        return bin(n)

    @staticmethod
    def to_octal(n: int) -> str:
        return oct(n)

    @staticmethod
    def to_hex(n: int) -> str:
        return hex(n).upper().replace("0X", "0x")

    @staticmethod
    def from_binary(s: str) -> int:
        return int(s, 2)

    @staticmethod
    def from_octal(s: str) -> int:
        return int(s, 8)

    @staticmethod
    def from_hex(s: str) -> int:
        return int(s, 16)

    @staticmethod
    def all_representations(n: int) -> dict:
        return {
            "Decimal":  str(n),
            "Binary":   bin(n),
            "Octal":    oct(n),
            "Hex":      hex(n).upper().replace("0X", "0x"),
        }


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 19: MAIN CALCULATOR ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class Calculator:
    """
    Main calculator engine.
    Coordinates: factory, history, memory, commands, events.
    """

    def __init__(self):
        self._factory   = OperationFactory()
        self._history   = HistoryManager()
        self._memory    = MemoryManager()
        self._invoker   = CommandInvoker()
        self._event_bus = EventBus()
        self._log_obs   = LogObserver()
        self._angle_unit= AngleUnit.DEGREES

        # Register observers
        self._event_bus.subscribe(EventType.ERROR_OCCURRED, SoundObserver())
        self._event_bus.subscribe(EventType.CALCULATION_DONE, self._log_obs)
        self._event_bus.subscribe(EventType.ERROR_OCCURRED,  self._log_obs)

    # ── Calculation entry point ──────────────────────────────────────────────

    def calculate(self, key: str, *args: float) -> OperationResult:
        op = self._factory.get(key)
        if op is None:
            raise InvalidInputError(f"Unknown operation key: '{key}'.")

        cmd    = CalculationCommand(op, args, self._history)
        result = self._invoker.run(cmd)

        if result.is_error:
            self._event_bus.emit(EventType.ERROR_OCCURRED, result.error)
        else:
            self._event_bus.emit(EventType.CALCULATION_DONE, result.expression)

        return result

    # ── Statistics (multi-value) ─────────────────────────────────────────────

    def statistics(self, op_name: str, numbers: List[float]) -> OperationResult:
        ops = {
            "mean":    MeanOperation(),
            "median":  MedianOperation(),
            "mode":    ModeOperation(),
            "stddev":  StdDevOperation(),
            "sum":     SumOperation(),
            "range":   RangeStatOperation(),
            "geomean": GeoMeanOperation(),
        }
        op = ops.get(op_name)
        if op is None:
            raise InvalidInputError(f"Unknown stat op: '{op_name}'.")
        try:
            result  = op.compute(numbers)
            nums_str = ", ".join(str(n) for n in numbers)
            expr    = f"{op.name()}({nums_str})"
            res_obj = OperationResult(
                expression=expr,
                result=Operation._format(result),
                category=OperationCategory.STATISTICS
            )
            self._history.push(res_obj)
            return res_obj
        except CalculatorError as e:
            return OperationResult(
                expression=op_name,
                result=None,
                category=OperationCategory.STATISTICS,
                error=str(e),
                is_error=True
            )

    # ── Undo / Redo ──────────────────────────────────────────────────────────

    def undo(self) -> str:
        return self._invoker.undo()

    def redo(self) -> OperationResult:
        return self._invoker.redo()

    # ── Memory ───────────────────────────────────────────────────────────────

    def mem_store(self, slot: int, value: float, label: str = ""):
        self._memory.store(slot, value, label)
        self._event_bus.emit(EventType.MEMORY_STORED, (slot, value))

    def mem_recall(self, slot: int) -> float:
        value = self._memory.recall(slot)
        self._event_bus.emit(EventType.MEMORY_RECALLED, (slot, value))
        return value

    def mem_add(self, slot: int, value: float):
        self._memory.add_to(slot, value)

    def mem_sub(self, slot: int, value: float):
        self._memory.subtract_from(slot, value)

    def mem_clear(self, slot: int):
        self._memory.clear(slot)

    def mem_clear_all(self):
        self._memory.clear_all()

    def mem_display(self):
        self._memory.display_all()

    # ── Angle unit ───────────────────────────────────────────────────────────

    def set_angle_unit(self, unit: AngleUnit):
        self._angle_unit = unit
        self._factory.set_angle_unit(unit)
        self._event_bus.emit(EventType.ANGLE_UNIT_CHANGED, unit)

    def get_angle_unit(self) -> AngleUnit:
        return self._angle_unit

    # ── History ──────────────────────────────────────────────────────────────

    def get_history(self) -> List[OperationResult]:
        return self._history.all()

    def clear_history(self):
        self._history.clear()
        self._event_bus.emit(EventType.HISTORY_CLEARED, None)

    def last_answer(self) -> Optional[float]:
        return self._history.last_result_value()

    def export_history(self, path: str) -> str:
        return self._history.export_json(path)


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 20: SPLASH SCREEN & MENUS
# ═══════════════════════════════════════════════════════════════════════════════

class SplashScreen:
    """Draws the animated startup screen."""

    LOGO = [
        r"  ██╗   ██╗██╗  ████████╗██████╗  █████╗     ",
        r"  ██║   ██║██║  ╚══██╔══╝██╔══██╗██╔══██╗    ",
        r"  ██║   ██║██║     ██║   ██████╔╝███████║    ",
        r"  ██║   ██║██║     ██║   ██╔══██╗██╔══██║    ",
        r"  ╚██████╔╝███████╗██║   ██║  ██║██║  ██║    ",
        r"   ╚═════╝ ╚══════╝╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝   ",
        r"                                              ",
        r"         ██████╗ █████╗ ██╗      ██████╗     ",
        r"        ██╔════╝██╔══██╗██║     ██╔════╝     ",
        r"        ██║     ███████║██║     ██║           ",
        r"        ██║     ██╔══██║██║     ██║           ",
        r"        ╚██████╗██║  ██║███████╗╚██████╗     ",
        r"         ╚═════╝╚═╝  ╚═╝╚══════╝ ╚═════╝    ",
    ]

    @staticmethod
    def show():
        UI.clear()
        colors = [
            Color.rgb(0, 200, 255),
            Color.rgb(0, 220, 200),
            Color.rgb(0, 240, 150),
        ]
        for i, line in enumerate(SplashScreen.LOGO):
            c = colors[i % len(colors)]
            print(c + line + Color.RESET)
            time.sleep(0.04)

        print()
        taglines = [
            Theme.muted("  ► Full OOP Architecture with Design Patterns"),
            Theme.muted("  ► Strategy · Singleton · Factory · Command · Observer"),
            Theme.muted("  ► Scientific · Statistical · Bitwise · Converter"),
        ]
        for t in taglines:
            UI.animate_text(t, delay=0.01)
            time.sleep(0.05)

        print()
        UI.progress_bar("Initializing engine", duration=0.6)
        time.sleep(0.2)
        UI.clear()


class MenuRenderer:
    """Renders all menu screens."""

    @staticmethod
    def main_menu(calc: Calculator):
        now       = datetime.datetime.now().strftime("%H:%M:%S")
        angle     = calc.get_angle_unit().label()
        hist_cnt  = len(calc.get_history())

        print(UI.top_bar())
        print(UI.row(UI.center(Theme.p("  ◈  ULTRA CALC  ◈  Advanced OOP Calculator"))))
        print(UI.thin_bar())

        status = (
            f"  {Theme.muted('Time:')} {Theme.num(now)}  "
            f"{Theme.muted('Angle:')} {Theme.ok(angle)}  "
            f"{Theme.muted('History:')} {Theme.num(str(hist_cnt))}  "
            f"{Theme.muted('Undo:')} {Theme.ok('✔') if True else Theme.err('✘')}"
        )
        print(UI.row(status))
        print(UI.thin_bar())

        sections = [
            ("1", "Arithmetic",   "Basic math operations"),
            ("2", "Trigonometry", "sin, cos, tan & inverses"),
            ("3", "Logarithms",   "ln, log₁₀, log₂, eˣ"),
            ("4", "Statistics",   "mean, median, σ, sum…"),
            ("5", "Bitwise",      "AND, OR, XOR, shifts"),
            ("6", "Constants",    "π, e, φ, speed of light…"),
            ("7", "Memory",       "10 memory slots (M0–M9)"),
            ("8", "Converter",    "Length, weight, temp…"),
            ("9", "Base Conv.",   "Binary, octal, hex"),
            ("H", "History",      "View past calculations"),
            ("U", "Undo/Redo",    "Undo last operation"),
            ("S", "Settings",     "Angle unit & preferences"),
            ("X", "Export",       "Save history to JSON"),
            ("0", "Exit",         "Quit ULTRA CALC"),
        ]

        for key, label, desc in sections:
            k    = Theme.s(f" {key} ")
            lbl  = Theme.p(f"{label:<14}")
            d    = Theme.muted(desc)
            line = f"  [{k}]  {lbl} {d}"
            print(UI.row(line))

        print(UI.bot_bar())

    @staticmethod
    def arithmetic_menu():
        ops = [
            ("1",  "+",    "Addition (a + b)"),
            ("2",  "−",    "Subtraction (a − b)"),
            ("3",  "×",    "Multiplication (a × b)"),
            ("4",  "÷",    "Division (a ÷ b)"),
            ("5",  "//",   "Floor Division (a // b)"),
            ("6",  "%",    "Modulo / Remainder"),
            ("7",  "xⁿ",   "Power (a ^ n)"),
            ("8",  "√x",   "Square Root"),
            ("9",  "∛x",   "Cube Root"),
            ("10", "ⁿ√x",  "Nth Root"),
            ("11", "|x|",  "Absolute Value"),
            ("12", "1/x",  "Reciprocal"),
            ("13", "x%",   "Percent (x / 100)"),
            ("14", "n!",   "Factorial"),
            ("0",  "←",    "Back to main menu"),
        ]
        MenuRenderer._render_op_menu("ARITHMETIC OPERATIONS", ops)

    @staticmethod
    def trig_menu():
        ops = [
            ("1",  "sin",   "Sine"),
            ("2",  "cos",   "Cosine"),
            ("3",  "tan",   "Tangent"),
            ("4",  "asin",  "Arcsine (inverse sin)"),
            ("5",  "acos",  "Arccosine (inverse cos)"),
            ("6",  "atan",  "Arctangent (inverse tan)"),
            ("7",  "sinh",  "Hyperbolic Sine"),
            ("8",  "cosh",  "Hyperbolic Cosine"),
            ("9",  "tanh",  "Hyperbolic Tangent"),
            ("0",  "←",     "Back"),
        ]
        MenuRenderer._render_op_menu("TRIGONOMETRY", ops)

    @staticmethod
    def log_menu():
        ops = [
            ("1", "ln",     "Natural Logarithm ln(x)"),
            ("2", "log₁₀", "Log Base 10"),
            ("3", "log₂",  "Log Base 2"),
            ("4", "logₙ",  "Log Arbitrary Base"),
            ("5", "eˣ",    "Exponential e^x"),
            ("0", "←",      "Back"),
        ]
        MenuRenderer._render_op_menu("LOGARITHMS", ops)

    @staticmethod
    def stats_menu():
        ops = [
            ("1", "mean",    "Arithmetic Mean"),
            ("2", "median",  "Median"),
            ("3", "mode",    "Mode (most frequent)"),
            ("4", "stddev",  "Standard Deviation (σ)"),
            ("5", "sum",     "Summation (Σ)"),
            ("6", "range",   "Range (max − min)"),
            ("7", "geomean", "Geometric Mean"),
            ("0", "←",       "Back"),
        ]
        MenuRenderer._render_op_menu("STATISTICS", ops)

    @staticmethod
    def bitwise_menu():
        ops = [
            ("1", "&",   "Bitwise AND"),
            ("2", "|",   "Bitwise OR"),
            ("3", "XOR", "Bitwise XOR (exclusive OR)"),
            ("4", "~",   "Bitwise NOT (complement)"),
            ("5", "<<",  "Left Shift"),
            ("6", ">>",  "Right Shift"),
            ("0", "←",   "Back"),
        ]
        MenuRenderer._render_op_menu("BITWISE OPERATIONS", ops)

    @staticmethod
    def _render_op_menu(title: str, ops: list):
        print(UI.top_bar())
        print(UI.row(UI.center(Theme.p(f"  ◈  {title}  ◈"))))
        print(UI.thin_bar())
        for key, sym, desc in ops:
            k    = Theme.s(f" {key:>2} ")
            s    = Theme.op(f"{sym:<6}")
            d    = Theme.muted(desc)
            print(UI.row(f"  [{k}]  {s}  {d}"))
        print(UI.bot_bar())


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 21: INPUT HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def get_float(prompt: str, calc: Calculator = None) -> float:
    """
    Prompt for a float.
    Supports 'ans' to recall last answer.
    """
    raw = UI.input_prompt(prompt).strip()
    if raw.lower() == "ans" and calc:
        ans = calc.last_answer()
        if ans is None:
            raise InvalidInputError("No previous answer available.")
        print(f"  {Theme.muted('Using last answer:')} {Theme.res(str(ans))}")
        return ans
    try:
        return float(raw)
    except ValueError:
        raise InvalidInputError(f"'{raw}' is not a valid number.")


def get_int_list(prompt: str) -> List[float]:
    """Get a space-separated list of numbers."""
    raw = UI.input_prompt(prompt)
    parts = raw.strip().split()
    if not parts:
        raise InvalidInputError("Enter at least one number.")
    result = []
    for p in parts:
        try:
            result.append(float(p))
        except ValueError:
            raise InvalidInputError(f"'{p}' is not a valid number.")
    return result


def show_result(res: OperationResult):
    """Display an OperationResult beautifully."""
    print()
    if res.is_error:
        print(UI.top_bar())
        print(UI.row(UI.center(Theme.err("  CALCULATION ERROR  "))))
        print(UI.thin_bar())
        print(UI.row(f"  {Theme.muted('Expression:')} {Theme.num(res.expression)}"))
        print(UI.row(f"  {Theme.err('Error:')}      {Theme.err(res.error or 'Unknown error')}"))
        print(UI.bot_bar())
    else:
        UI.spinner("Computing", duration=0.3)
        print(UI.top_bar())
        print(UI.row(UI.center(Theme.ok("  RESULT  "))))
        print(UI.thin_bar())
        print(UI.row(f"  {Theme.muted('Expression:')}  {Theme.num(res.expression)}"))
        print(UI.row(f"  {Theme.res('=')} {Theme.res(str(res.result))}"))
        print(UI.row(f"  {Theme.muted('Category:')}   {Theme.a(res.category.value)}"))
        print(UI.row(f"  {Theme.muted('Time:')}        {Theme.muted(res.timestamp.strftime('%H:%M:%S'))}"))
        print(UI.bot_bar())


def wait():
    """Pause until user presses Enter."""
    input(f"\n  {Theme.muted('Press Enter to continue...')}")


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 22: SUB-MENU CONTROLLERS
# ═══════════════════════════════════════════════════════════════════════════════

def run_arithmetic(calc: Calculator):
    op_map = {
        "1": "add", "2": "sub", "3": "mul", "4": "div",
        "5": "fdiv", "6": "mod", "7": "pow", "8": "sqrt",
        "9": "cbrt", "10": "nthroot", "11": "abs",
        "12": "recip", "13": "pct", "14": "fact",
    }
    unary = {"8", "9", "11", "12", "13", "14"}

    while True:
        UI.clear()
        MenuRenderer.arithmetic_menu()
        choice = UI.input_prompt("Choose operation (0 to go back):").strip()
        if choice == "0":
            break
        if choice not in op_map:
            UI.error("Invalid choice.")
            wait()
            continue
        try:
            if choice in unary:
                a   = get_float("Enter number (or 'ans'):", calc)
                res = calc.calculate(op_map[choice], a)
            else:
                a   = get_float("Enter first number (or 'ans'):", calc)
                b   = get_float("Enter second number:", calc)
                res = calc.calculate(op_map[choice], a, b)
            show_result(res)
        except CalculatorError as e:
            UI.error(str(e))
        wait()


def run_trigonometry(calc: Calculator):
    op_map = {
        "1": "sin", "2": "cos", "3": "tan",
        "4": "asin", "5": "acos", "6": "atan",
        "7": "sinh", "8": "cosh", "9": "tanh",
    }
    while True:
        UI.clear()
        MenuRenderer.trig_menu()
        choice = UI.input_prompt("Choose operation:").strip()
        if choice == "0":
            break
        if choice not in op_map:
            UI.error("Invalid choice.")
            wait()
            continue
        try:
            a   = get_float("Enter angle / value (or 'ans'):", calc)
            res = calc.calculate(op_map[choice], a)
            show_result(res)
        except CalculatorError as e:
            UI.error(str(e))
        wait()


def run_logarithms(calc: Calculator):
    op_map = {"1": "ln", "2": "log10", "3": "log2", "4": "logn", "5": "exp"}
    while True:
        UI.clear()
        MenuRenderer.log_menu()
        choice = UI.input_prompt("Choose operation:").strip()
        if choice == "0":
            break
        if choice not in op_map:
            UI.error("Invalid choice.")
            wait()
            continue
        try:
            if choice == "4":  # logn — needs base
                a    = get_float("Enter number:", calc)
                base = get_float("Enter base:", calc)
                res  = calc.calculate("logn", a, base)
            else:
                a   = get_float("Enter number (or 'ans'):", calc)
                res = calc.calculate(op_map[choice], a)
            show_result(res)
        except CalculatorError as e:
            UI.error(str(e))
        wait()


def run_statistics(calc: Calculator):
    op_map = {
        "1": "mean", "2": "median", "3": "mode",
        "4": "stddev", "5": "sum", "6": "range", "7": "geomean",
    }
    while True:
        UI.clear()
        MenuRenderer.stats_menu()
        choice = UI.input_prompt("Choose stat:").strip()
        if choice == "0":
            break
        if choice not in op_map:
            UI.error("Invalid choice.")
            wait()
            continue
        try:
            nums = get_int_list("Enter numbers separated by spaces:")
            res  = calc.statistics(op_map[choice], nums)
            show_result(res)
        except CalculatorError as e:
            UI.error(str(e))
        wait()


def run_bitwise(calc: Calculator):
    op_map = {
        "1": "band", "2": "bor", "3": "bxor",
        "4": "bnot", "5": "lsh", "6": "rsh",
    }
    unary = {"4"}
    while True:
        UI.clear()
        MenuRenderer.bitwise_menu()
        choice = UI.input_prompt("Choose operation:").strip()
        if choice == "0":
            break
        if choice not in op_map:
            UI.error("Invalid choice.")
            wait()
            continue
        try:
            if choice in unary:
                a   = get_float("Enter integer:", calc)
                res = calc.calculate(op_map[choice], a)
            else:
                a   = get_float("Enter first integer:", calc)
                b   = get_float("Enter second integer:", calc)
                res = calc.calculate(op_map[choice], a, b)
            show_result(res)

            # Also show binary representation
            if not res.is_error:
                try:
                    n = int(float(str(res.result)))
                    reps = BaseConverter.all_representations(n)
                    print()
                    print(UI.top_bar())
                    print(UI.row(UI.center(Theme.p("  BIT REPRESENTATIONS  "))))
                    print(UI.thin_bar())
                    for base, val in reps.items():
                        print(UI.row(f"  {Theme.muted(f'{base:<10}')} {Theme.num(val)}"))
                    print(UI.bot_bar())
                except Exception:
                    pass

        except CalculatorError as e:
            UI.error(str(e))
        wait()


def run_constants():
    while True:
        UI.clear()
        ConstantsDB.display_all()
        choice = UI.input_prompt("Enter number to copy as ANS (0 = back):").strip()
        if choice == "0":
            break
        try:
            idx = int(choice)
            c   = ConstantsDB.get_by_index(idx)
            UI.success(f"Constant: {c.symbol} = {c.value}")
            UI.info(c.description)
        except (ValueError, CalculatorError) as e:
            UI.error(str(e))
        wait()


def run_memory(calc: Calculator):
    while True:
        UI.clear()
        print(UI.top_bar())
        print(UI.row(UI.center(Theme.p("  ◈  MEMORY MANAGER  ◈"))))
        print(UI.thin_bar())
        calc.mem_display()
        print(UI.thin_bar())
        ops = [
            ("1", "MS", "Store value in slot"),
            ("2", "MR", "Recall from slot"),
            ("3", "M+", "Add to slot"),
            ("4", "M-", "Subtract from slot"),
            ("5", "MC", "Clear one slot"),
            ("6", "MCA","Clear ALL slots"),
            ("0", "←",  "Back"),
        ]
        for k, sym, desc in ops:
            print(UI.row(f"  [{Theme.s(f' {k} ')}]  {Theme.op(sym):<8} {Theme.muted(desc)}"))
        print(UI.bot_bar())

        choice = UI.input_prompt("Choose:").strip()
        if choice == "0":
            break
        try:
            if choice == "1":
                slot  = int(UI.input_prompt("Slot (0–9):"))
                value = get_float("Value to store:", calc)
                label = UI.input_prompt("Label (optional):").strip()
                calc.mem_store(slot, value, label)
                UI.success(f"Stored {value} in M{slot}.")
            elif choice == "2":
                slot  = int(UI.input_prompt("Slot (0–9):"))
                value = calc.mem_recall(slot)
                UI.success(f"M{slot} = {value}")
            elif choice == "3":
                slot  = int(UI.input_prompt("Slot (0–9):"))
                value = get_float("Value to add:", calc)
                calc.mem_add(slot, value)
                UI.success(f"Added {value} to M{slot}.")
            elif choice == "4":
                slot  = int(UI.input_prompt("Slot (0–9):"))
                value = get_float("Value to subtract:", calc)
                calc.mem_sub(slot, value)
                UI.success(f"Subtracted {value} from M{slot}.")
            elif choice == "5":
                slot = int(UI.input_prompt("Slot (0–9):"))
                calc.mem_clear(slot)
                UI.success(f"M{slot} cleared.")
            elif choice == "6":
                calc.mem_clear_all()
                UI.success("All memory slots cleared.")
            else:
                UI.error("Invalid choice.")
        except (ValueError, CalculatorError) as e:
            UI.error(str(e))
        wait()


def run_converter():
    while True:
        UI.clear()
        print(UI.top_bar())
        print(UI.row(UI.center(Theme.p("  ◈  UNIT CONVERTER  ◈"))))
        print(UI.thin_bar())
        cats = [
            ("1", "Length",      "m, km, cm, mm, mi, yd, ft, in"),
            ("2", "Weight",      "kg, g, mg, lb, oz, ton"),
            ("3", "Temperature", "C, F, K"),
            ("4", "Speed",       "ms (m/s), kmh, mph, knot"),
            ("0", "←",           "Back"),
        ]
        for k, name, units in cats:
            print(UI.row(f"  [{Theme.s(f' {k} ')}]  {Theme.p(name):<18} {Theme.muted(units)}"))
        print(UI.bot_bar())

        choice = UI.input_prompt("Choose category:").strip()
        if choice == "0":
            break
        try:
            if choice == "1":
                value  = float(UI.input_prompt("Value:"))
                from_u = UI.input_prompt("From unit (m/km/cm/mm/mi/yd/ft/in):").lower()
                to_u   = UI.input_prompt("To unit:").lower()
                result = UnitConverter.convert_length(value, from_u, to_u)
                UI.success(f"{value} {from_u} = {result:.6g} {to_u}")
            elif choice == "2":
                value  = float(UI.input_prompt("Value:"))
                from_u = UI.input_prompt("From unit (kg/g/mg/lb/oz/ton):").lower()
                to_u   = UI.input_prompt("To unit:").lower()
                result = UnitConverter.convert_weight(value, from_u, to_u)
                UI.success(f"{value} {from_u} = {result:.6g} {to_u}")
            elif choice == "3":
                value  = float(UI.input_prompt("Value:"))
                from_u = UI.input_prompt("From unit (C/F/K):").upper()
                to_u   = UI.input_prompt("To unit (C/F/K):").upper()
                result = UnitConverter.convert_temperature(value, from_u.lower(), to_u.lower())
                UI.success(f"{value}°{from_u} = {result:.4g}°{to_u}")
            elif choice == "4":
                value  = float(UI.input_prompt("Value:"))
                from_u = UI.input_prompt("From (ms/kmh/mph/knot):").lower()
                to_u   = UI.input_prompt("To:").lower()
                result = UnitConverter.convert_speed(value, from_u, to_u)
                UI.success(f"{value} {from_u} = {result:.4g} {to_u}")
            else:
                UI.error("Invalid choice.")
        except (ValueError, CalculatorError) as e:
            UI.error(str(e))
        wait()


def run_base_converter():
    while True:
        UI.clear()
        print(UI.top_bar())
        print(UI.row(UI.center(Theme.p("  ◈  NUMBER BASE CONVERTER  ◈"))))
        print(UI.thin_bar())
        ops = [
            ("1", "Decimal → All",  "Show binary, octal, hex"),
            ("2", "Binary → Dec",   "0b... to decimal"),
            ("3", "Hex → Dec",      "0xFF... to decimal"),
            ("4", "Octal → Dec",    "0o... to decimal"),
            ("0", "←",              "Back"),
        ]
        for k, name, desc in ops:
            print(UI.row(f"  [{Theme.s(f' {k} ')}]  {Theme.p(name):<20} {Theme.muted(desc)}"))
        print(UI.bot_bar())

        choice = UI.input_prompt("Choose:").strip()
        if choice == "0":
            break
        try:
            if choice == "1":
                n    = int(UI.input_prompt("Enter decimal integer:"))
                reps = BaseConverter.all_representations(n)
                print()
                print(UI.top_bar())
                print(UI.row(UI.center(Theme.p("  REPRESENTATIONS  "))))
                print(UI.thin_bar())
                for base, val in reps.items():
                    print(UI.row(f"  {Theme.muted(f'{base:<12}')} {Theme.res(val)}"))
                print(UI.bot_bar())
            elif choice == "2":
                s = UI.input_prompt("Binary string (e.g. 1010):").strip()
                r = BaseConverter.from_binary(s)
                UI.success(f"Binary {s} = Decimal {r}")
            elif choice == "3":
                s = UI.input_prompt("Hex string (e.g. FF or 0xFF):").strip()
                r = BaseConverter.from_hex(s)
                UI.success(f"Hex {s} = Decimal {r}")
            elif choice == "4":
                s = UI.input_prompt("Octal string (e.g. 17):").strip()
                r = BaseConverter.from_octal(s)
                UI.success(f"Octal {s} = Decimal {r}")
            else:
                UI.error("Invalid choice.")
        except (ValueError, CalculatorError) as e:
            UI.error(f"Conversion error: {e}")
        wait()


def run_history(calc: Calculator):
    records = calc.get_history()
    UI.clear()
    print(UI.top_bar())
    print(UI.row(UI.center(Theme.p(f"  ◈  HISTORY ({len(records)} records)  ◈"))))
    print(UI.thin_bar())

    if not records:
        print(UI.row(UI.center(Theme.muted("No calculations yet."))))
    else:
        shown = records[-30:]  # Show last 30
        for i, r in enumerate(shown, 1):
            idx_str = Theme.muted(f"{i:>3}.")
            print(UI.row(f" {idx_str} {r.display_line()}"))

    print(UI.thin_bar())

    options = [
        ("C", "Clear all history"),
        ("E", "Export to JSON"),
        ("0", "Back"),
    ]
    for k, desc in options:
        print(UI.row(f"  [{Theme.s(f' {k} ')}]  {Theme.muted(desc)}"))
    print(UI.bot_bar())

    choice = UI.input_prompt("Choice:").strip().upper()
    if choice == "C":
        calc.clear_history()
        UI.success("History cleared.")
        wait()
    elif choice == "E":
        path = f"calc_history_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        saved = calc.export_history(path)
        UI.success(f"Exported to: {saved}")
        wait()


def run_undo_redo(calc: Calculator):
    UI.clear()
    print(UI.top_bar())
    print(UI.row(UI.center(Theme.p("  ◈  UNDO / REDO  ◈"))))
    print(UI.thin_bar())
    ops = [
        ("1", "Undo last operation"),
        ("2", "Redo last undone"),
        ("0", "Back"),
    ]
    for k, desc in ops:
        print(UI.row(f"  [{Theme.s(f' {k} ')}]  {Theme.muted(desc)}"))
    print(UI.bot_bar())

    choice = UI.input_prompt("Choice:").strip()
    if choice == "1":
        try:
            msg = calc.undo()
            UI.success(msg)
        except CalculatorError as e:
            UI.error(str(e))
    elif choice == "2":
        try:
            res = calc.redo()
            if isinstance(res, OperationResult):
                show_result(res)
            else:
                UI.success("Redo successful.")
        except CalculatorError as e:
            UI.error(str(e))
    wait()


def run_settings(calc: Calculator):
    while True:
        UI.clear()
        current = calc.get_angle_unit().label()
        print(UI.top_bar())
        print(UI.row(UI.center(Theme.p("  ◈  SETTINGS  ◈"))))
        print(UI.thin_bar())
        print(UI.row(f"  {Theme.muted('Current angle unit:')} {Theme.ok(current)}"))
        print(UI.thin_bar())
        opts = [
            ("1", "DEG", "Degrees (most common)"),
            ("2", "RAD", "Radians (math standard)"),
            ("3", "GRAD","Gradians (400 = full circle)"),
            ("0", "←",   "Back"),
        ]
        for k, sym, desc in opts:
            print(UI.row(f"  [{Theme.s(f' {k} ')}]  {Theme.op(sym):<8} {Theme.muted(desc)}"))
        print(UI.bot_bar())

        choice = UI.input_prompt("Choose:").strip()
        if choice == "0":
            break
        elif choice == "1":
            calc.set_angle_unit(AngleUnit.DEGREES)
            UI.success("Angle unit set to DEGREES.")
        elif choice == "2":
            calc.set_angle_unit(AngleUnit.RADIANS)
            UI.success("Angle unit set to RADIANS.")
        elif choice == "3":
            calc.set_angle_unit(AngleUnit.GRADIANS)
            UI.success("Angle unit set to GRADIANS.")
        else:
            UI.error("Invalid choice.")
        wait()


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 23: MAIN APPLICATION LOOP
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    SplashScreen.show()
    calc = Calculator()

    while True:
        UI.clear()
        MenuRenderer.main_menu(calc)
        choice = UI.input_prompt("Enter your choice:").strip().upper()

        if choice == "0":
            UI.clear()
            print()
            UI.animate_text(Theme.p("  Thanks for using ULTRA CALC!"), delay=0.02)
            UI.animate_text(Theme.muted("  Built with ♥ using Full OOP Architecture"), delay=0.01)
            print()
            break
        elif choice == "1":
            run_arithmetic(calc)
        elif choice == "2":
            run_trigonometry(calc)
        elif choice == "3":
            run_logarithms(calc)
        elif choice == "4":
            run_statistics(calc)
        elif choice == "5":
            run_bitwise(calc)
        elif choice == "6":
            run_constants()
        elif choice == "7":
            run_memory(calc)
        elif choice == "8":
            run_converter()
        elif choice == "9":
            run_base_converter()
        elif choice == "H":
            run_history(calc)
        elif choice == "U":
            run_undo_redo(calc)
        elif choice == "S":
            run_settings(calc)
        elif choice == "X":
            path = f"calc_history_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            saved = calc.export_history(path)
            UI.success(f"History exported to: {saved}")
            wait()
        else:
            UI.error("Invalid choice. Pick from the menu.")
            wait()


if __name__ == "__main__":
    main()