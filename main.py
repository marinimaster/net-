from __future__ import annotations

import argparse

from netplus_quiz.cli import run_cli, run_ports_cli


def main() -> None:
    parser = argparse.ArgumentParser(description="Network+ multiple choice quiz")
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run the terminal version instead of the Tkinter GUI.",
    )
    parser.add_argument(
        "--ports",
        action="store_true",
        help="Run the dedicated CompTIA protocols and ports practice mode.",
    )
    parser.add_argument(
        "--secure-ports",
        action="store_true",
        help="Run the secure-protocol ports practice mode.",
    )
    args = parser.parse_args()

    if args.secure_ports:
        run_ports_cli(secure_only=True)
        return

    if args.ports:
        run_ports_cli()
        return

    if args.cli:
        run_cli()
        return

    try:
        from netplus_quiz.gui import run_gui
    except ModuleNotFoundError as exc:
        if exc.name == "tkinter":
            print("Tkinter is not installed. Falling back to the terminal UI.\n")
            run_cli()
            return
        raise

    try:
        run_gui()
    except Exception as exc:
        if exc.__class__.__name__ == "TclError":
            print("Graphical display is unavailable. Falling back to the terminal UI.\n")
            run_cli()
            return
        raise


if __name__ == "__main__":
    main()
