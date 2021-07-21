import sys
from typing import Optional
import questionary
from enum import Enum
from edge.exception import EdgeException

styles = {
    "heading": "bold underline",
    "step": "bold",
    "substep": "",
    "success": "fg:ansigreen",
    "failure": "fg:ansired",
    "warning": "fg:ansiyellow",
}

qmark = "    ?"


def print_heading(text: str):
    questionary.print(text, styles["heading"])


def strfmt_step(text: str, emoji: str = "*"):
    return f"{emoji} {text}"


def print_step(text: str, emoji: str = "*"):
    questionary.print(strfmt_step(text, emoji), styles["step"])


def strfmt_substep(text):
    return f"  {text}"


def print_substep(text: str):
    questionary.print(strfmt_substep(f"◻️ {text}"), styles["substep"])


def strfmt_substep_success(text):
    return strfmt_substep(f"✔ ️{text}")


def strfmt_substep_failure(text):
    return strfmt_substep(f"❌ {text}")


def strfmt_substep_warning(text):
    return strfmt_substep(f"⚠️ {text}")


def strfmt_substep_not_done(text):
    return strfmt_substep(f"⏳ {text}")


def print_substep_success(text: str):
    questionary.print(strfmt_substep_success(text), styles["success"])


def print_substep_failure(text: str):
    questionary.print(strfmt_substep_failure(text), styles["failure"])


def print_substep_not_done(text: str):
    questionary.print(strfmt_substep_not_done(text), styles["substep"])


def print_substep_warning(text: str):
    questionary.print(strfmt_substep_warning(text), styles["warning"])


def strfmt_failure_explanation(text: str):
    return f"   - {text}"


def print_failure_explanation(text: str):
    questionary.print(strfmt_failure_explanation(text), styles["failure"])


def print_warning_explanation(text: str):
    questionary.print(strfmt_failure_explanation(text), styles["warning"])


def clear_last_line():
    print("\033[1A\033[0K", end="\r")


class TUIStatus(Enum):
    NEUTRAL = "neutral"
    PENDING = "pending"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    WARNING = "warning"


class TUI(object):
    def __init__(
        self,
        intro: str,
        success_title: str,
        success_message: str,
        failure_title: str,
        failure_message: str,
    ):
        self.intro = intro
        self.success_title = success_title
        self.success_message = success_message
        self.failure_title = failure_title
        self.failure_message = failure_message

    def __enter__(self):
        questionary.print(self.intro, "bold underline")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            print()
            questionary.print(self.success_title, style="fg:ansigreen")
            print()
            print(self.success_message)
            sys.exit(0)
        elif exc_type is EdgeException:
            print()
            questionary.print(self.failure_title, style="fg:ansired")
            print()
            questionary.print(self.failure_message, style="fg:ansired")
            sys.exit(1)
        else:
            return False


class StepTUI(object):
    def __init__(self, message: str, emoji: str = "*"):
        self.message = message
        self.emoji = emoji

    def __enter__(self):
        self.print()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False  # Do not suppress

    def print(self):
        questionary.print(f"{self.emoji} {self.message}", "bold")


class SubStepTUI(object):
    style = {
        TUIStatus.NEUTRAL: "",
        TUIStatus.PENDING: "",
        TUIStatus.SUCCESSFUL: styles["success"],
        TUIStatus.FAILED: styles["failure"],
        TUIStatus.WARNING: styles["warning"]
    }

    emoji = {
        TUIStatus.NEUTRAL: "◻️",
        TUIStatus.PENDING: "⏳",
        TUIStatus.SUCCESSFUL: "✔",
        TUIStatus.FAILED: "❌",
        TUIStatus.WARNING: "⚠️"
    }

    def __init__(self, message: str, status=TUIStatus.PENDING):
        self.message = message
        self.status = status
        self.written = False
        self._entered = False
        self._dirty = False

    def __enter__(self):
        self._entered = True
        self.print()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        suppress = True
        if exc_type is None:  # sub-step exited with errors
            if self.status == TUIStatus.PENDING:
                self.update(status=TUIStatus.SUCCESSFUL)
        elif exc_type is EdgeException:
            if exc_val.fatal:
                self.update(status=TUIStatus.FAILED)
                suppress = False
            else:
                self.update(status=TUIStatus.WARNING)
            self.add_explanation(str(exc_val))
        else:
            return False

        self._entered = False

        return suppress

    def print(self):
        if not self._entered:
            return
        if self.written and not self._dirty:
            clear_last_line()
        line = f"  {self.emoji[self.status]} {self.message}"
        questionary.print(line, self.style[self.status])
        self.written = True

    def update(self, message: Optional[str] = None, status: Optional[TUIStatus] = None):
        if message is not None:
            self.message = message
        if status is not None:
            self.status = status
        self.print()

    def add_explanation(self, text: str):
        self._dirty = True
        line = f"   - {text}"
        questionary.print(line, self.style[self.status])

    def set_dirty(self):
        self._dirty = True
