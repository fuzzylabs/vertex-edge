import questionary

styles = {
    "heading": "bold underline",
    "step": "bold",
    "substep": "",
    "success": "fg:ansigreen",
    "failure": "fg:ansired",
}

qmark = "  ?"


def print_heading(text: str):
    questionary.print(text, styles["heading"])


def strfmt_step(text: str):
    return f"* {text}"


def print_step(text: str):
    questionary.print(strfmt_step(text), styles["step"])


def strfmt_substep(text):
    return f"  {text}"


def print_substep(text: str):
    questionary.print(strfmt_substep(f". {text}"), styles["substep"])


def strfmt_substep_success(text):
    return strfmt_substep(f"✔ ️{text}")


def strfmt_substep_failure(text):
    return strfmt_substep(f"❌ {text}")


def strfmt_substep_not_done(text):
    return strfmt_substep(f"⏳ {text}")


def print_substep_success(text: str):
    questionary.print(strfmt_substep_success(text), styles["success"])


def print_substep_failure(text: str):
    questionary.print(strfmt_substep_failure(text), styles["failure"])


def print_substep_not_done(text: str):
    questionary.print(strfmt_substep_not_done(text), styles["substep"])


def strfmt_failure_explanation(text: str):
    return f"   - {text}"


def print_failure_explanation(text: str):
    questionary.print(strfmt_failure_explanation(text), styles["failure"])


def clear_last_line():
    print("\033[1A\033[0K", end="\r")
