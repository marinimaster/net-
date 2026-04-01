from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from .engine import AnswerRecord, QuizSession
from .quiz_bank import (
    PROJECT_ROOT,
    QUESTION_BANK,
    available_difficulties,
    available_topics,
    get_port_questions,
    get_questions,
)


class QuizApp(tk.Tk):
    """Simple Tkinter GUI with room for future extensions."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Network+ Multiple Choice Quiz")
        self.geometry("900x680")
        self.minsize(760, 560)
        self.font_size_offset = 0
        self._base_named_font_sizes = {
            name: tkfont.nametofont(name).cget("size")
            for name in (
                "TkDefaultFont",
                "TkTextFont",
                "TkHeadingFont",
                "TkCaptionFont",
                "TkMenuFont",
                "TkFixedFont",
                "TkIconFont",
                "TkTooltipFont",
            )
        }
        default_family = tkfont.nametofont("TkDefaultFont").cget("family")
        self.title_font = tkfont.Font(family=default_family, size=18, weight="bold")
        self.section_font = tkfont.Font(family=default_family, size=11, weight="bold")
        self.prompt_font = tkfont.Font(family=default_family, size=14, weight="bold")
        self.result_font = tkfont.Font(family=default_family, size=13)
        self._apply_font_scale()

        self.selected_topics = {
            topic: tk.BooleanVar(value=True) for topic in available_topics()
        }
        self.selected_difficulties = {
            difficulty: tk.BooleanVar(value=True)
            for difficulty in available_difficulties()
        }
        self.question_limit = tk.IntVar(value=min(10, len(QUESTION_BANK)))
        self.shuffle_questions = tk.BooleanVar(value=True)
        self.answer_var = tk.IntVar(value=-1)
        self.feedback_var = tk.StringVar(value="")
        self.session: QuizSession | None = None
        self.last_record: AnswerRecord | None = None

        self._build_start_screen()

    def _clear_window(self) -> None:
        for child in self.winfo_children():
            child.destroy()

    def _apply_font_scale(self) -> None:
        for name, base_size in self._base_named_font_sizes.items():
            tkfont.nametofont(name).configure(size=max(8, base_size + self.font_size_offset))

        self.title_font.configure(size=max(12, 18 + self.font_size_offset))
        self.section_font.configure(size=max(10, 11 + self.font_size_offset))
        self.prompt_font.configure(size=max(12, 14 + self.font_size_offset))
        self.result_font.configure(size=max(11, 13 + self.font_size_offset))

    def _increase_font_size(self) -> None:
        if self.font_size_offset >= 8:
            return
        self.font_size_offset += 1
        self._apply_font_scale()

    def _confirm_exit_quiz(self) -> None:
        if self.session is None:
            return
        confirmed = messagebox.askyesno(
            "Exit Test",
            "Exit the current test and return to the menu? Current progress will be lost.",
        )
        if confirmed:
            self.session = None
            self.last_record = None
            self.feedback_var.set("")
            self._build_start_screen()

    def _build_start_screen(self) -> None:
        self._clear_window()

        frame = ttk.Frame(self, padding=24)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=0)

        ttk.Label(
            frame,
            text="Network+ Quiz",
            font=self.title_font,
        ).grid(row=0, column=0, sticky="w")
        ttk.Button(frame, text="A+", command=self._increase_font_size).grid(
            row=0, column=1, sticky="e"
        )

        ttk.Label(
            frame,
            text="Questions are based on the corrected note files in this directory.",
            wraplength=760,
        ).grid(row=1, column=0, sticky="w", pady=(8, 18))

        topic_frame = ttk.LabelFrame(frame, text="Topics", padding=16)
        topic_frame.grid(row=2, column=0, sticky="nsew")
        topic_frame.columnconfigure(0, weight=1)
        topic_frame.columnconfigure(1, weight=1)

        for index, (topic, var) in enumerate(self.selected_topics.items()):
            ttk.Checkbutton(topic_frame, text=topic, variable=var).grid(
                row=index // 2,
                column=index % 2,
                sticky="w",
                padx=(0, 24),
                pady=4,
            )

        difficulty_frame = ttk.LabelFrame(frame, text="Difficulty", padding=16)
        difficulty_frame.grid(row=3, column=0, sticky="nsew", pady=(18, 0))

        for index, (difficulty, var) in enumerate(self.selected_difficulties.items()):
            label = difficulty.title()
            ttk.Checkbutton(difficulty_frame, text=label, variable=var).grid(
                row=0,
                column=index,
                sticky="w",
                padx=(0, 24),
                pady=4,
            )

        options = ttk.Frame(frame, padding=(0, 18, 0, 0))
        options.grid(row=4, column=0, sticky="w")

        ttk.Label(options, text="Question count:").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(
            options,
            from_=1,
            to=len(QUESTION_BANK),
            textvariable=self.question_limit,
            width=6,
        ).grid(row=0, column=1, sticky="w", padx=(8, 24))

        ttk.Checkbutton(
            options,
            text="Shuffle questions",
            variable=self.shuffle_questions,
        ).grid(row=0, column=2, sticky="w")

        button_bar = ttk.Frame(frame, padding=(0, 24, 0, 0))
        button_bar.grid(row=5, column=0, sticky="w")

        ttk.Button(button_bar, text="Start Quiz", command=self._start_quiz).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(
            button_bar,
            text="Ports Practice",
            command=lambda: self._start_ports_quiz(secure_only=False),
        ).grid(row=0, column=1, sticky="w", padx=(12, 0))
        ttk.Button(
            button_bar,
            text="Secure Ports",
            command=lambda: self._start_ports_quiz(secure_only=True),
        ).grid(row=0, column=2, sticky="w", padx=(12, 0))
        ttk.Button(
            button_bar,
            text="Open All Notes",
            command=lambda: self._show_note_window(None),
        ).grid(row=0, column=3, sticky="w", padx=(12, 0))

    def _selected_difficulties(self) -> list[str]:
        return [
            difficulty
            for difficulty, var in self.selected_difficulties.items()
            if var.get()
        ]

    def _start_session(self, questions: list) -> None:
        self.session = QuizSession(questions)
        self.last_record = None
        self._build_question_screen()
        self._render_question()

    def _start_quiz(self) -> None:
        selected_topics = [
            topic for topic, var in self.selected_topics.items() if var.get()
        ]
        if not selected_topics:
            messagebox.showerror("No Topics Selected", "Select at least one topic.")
            return

        selected_difficulties = self._selected_difficulties()
        if not selected_difficulties:
            messagebox.showerror("No Difficulty Selected", "Select at least one difficulty.")
            return

        limit = max(1, min(self.question_limit.get(), len(QUESTION_BANK)))
        questions = get_questions(
            topics=selected_topics,
            difficulties=selected_difficulties,
            limit=limit,
            shuffle=self.shuffle_questions.get(),
        )
        if not questions:
            messagebox.showerror("No Questions", "No questions matched the current topic selection.")
            return

        self._start_session(questions)

    def _start_ports_quiz(self, *, secure_only: bool) -> None:
        selected_difficulties = self._selected_difficulties()
        if not selected_difficulties:
            messagebox.showerror("No Difficulty Selected", "Select at least one difficulty.")
            return

        available = get_port_questions(
            secure_only=secure_only,
            difficulties=selected_difficulties,
            shuffle=self.shuffle_questions.get(),
        )
        if not available:
            messagebox.showerror("No Questions", "No ports questions matched the current difficulty selection.")
            return

        limit = max(1, min(self.question_limit.get(), len(available)))
        questions = get_port_questions(
            secure_only=secure_only,
            difficulties=selected_difficulties,
            limit=limit,
            shuffle=self.shuffle_questions.get(),
        )
        self._start_session(questions)

    def _build_question_screen(self) -> None:
        self._clear_window()

        frame = ttk.Frame(self, padding=24)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=0)
        frame.rowconfigure(3, weight=1)

        self.progress_label = ttk.Label(frame, text="")
        self.progress_label.grid(row=0, column=0, sticky="w")
        ttk.Button(frame, text="A+", command=self._increase_font_size).grid(
            row=0, column=1, sticky="e"
        )

        self.topic_label = ttk.Label(frame, text="", font=self.section_font)
        self.topic_label.grid(row=1, column=0, sticky="w", pady=(8, 8))

        self.prompt_label = ttk.Label(
            frame,
            text="",
            wraplength=820,
            font=self.prompt_font,
            justify="left",
        )
        self.prompt_label.grid(row=2, column=0, sticky="w", pady=(6, 14))

        choices_frame = ttk.Frame(frame)
        choices_frame.grid(row=3, column=0, sticky="nsew")
        choices_frame.columnconfigure(0, weight=1)

        self.choices_frame = choices_frame
        self.choice_buttons: list[ttk.Radiobutton] = []

        ttk.Separator(frame).grid(row=4, column=0, sticky="ew", pady=14)

        self.feedback_label = ttk.Label(
            frame,
            textvariable=self.feedback_var,
            wraplength=820,
            justify="left",
        )
        self.feedback_label.grid(row=5, column=0, sticky="w")

        actions = ttk.Frame(frame, padding=(0, 18, 0, 0))
        actions.grid(row=6, column=0, sticky="w")

        self.submit_button = ttk.Button(actions, text="Submit Answer", command=self._submit_answer)
        self.submit_button.grid(row=0, column=0, sticky="w")

        self.next_button = ttk.Button(actions, text="Next Question", command=self._next_question, state="disabled")
        self.next_button.grid(row=0, column=1, sticky="w", padx=(12, 0))

        self.source_button = ttk.Button(actions, text="Open Source Note", command=self._open_current_source)
        self.source_button.grid(row=0, column=2, sticky="w", padx=(12, 0))

        self.exit_button = ttk.Button(actions, text="Exit Test", command=self._confirm_exit_quiz)
        self.exit_button.grid(row=0, column=3, sticky="w", padx=(12, 0))

    def _render_question(self) -> None:
        assert self.session is not None
        question = self.session.current_question()
        if question is None:
            self._build_results_screen()
            return

        self.answer_var.set(-1)
        self.feedback_var.set("")
        self.last_record = None

        self.progress_label.config(
            text=f"Question {self.session.position + 1} of {self.session.total_questions} | Score: {self.session.score}"
        )
        self.topic_label.config(
            text=(
                f"Topic: {question.topic} | Difficulty: {question.difficulty.title()} | "
                f"Source: {question.source_file.name}"
            )
        )
        self.prompt_label.config(text=question.prompt)

        for button in self.choice_buttons:
            button.destroy()
        self.choice_buttons.clear()

        for index, choice in enumerate(question.choices):
            button = ttk.Radiobutton(
                self.choices_frame,
                text=choice,
                value=index,
                variable=self.answer_var,
            )
            button.grid(row=index, column=0, sticky="w", pady=8)
            self.choice_buttons.append(button)

        self.submit_button.config(state="normal")
        self.next_button.config(state="disabled")

    def _submit_answer(self) -> None:
        assert self.session is not None
        if self.answer_var.get() < 0:
            messagebox.showwarning("No Answer Selected", "Select one answer before submitting.")
            return

        record = self.session.answer_current(self.answer_var.get())
        self.last_record = record

        for button in self.choice_buttons:
            button.config(state="disabled")

        if record.is_correct:
            prefix = "Correct."
        else:
            prefix = f"Incorrect. Correct answer: {record.question.answer_text}."

        self.feedback_var.set(
            f"{prefix}\n\nExplanation: {record.question.explanation}\nSource note: {record.question.source_file.name}"
        )
        self.submit_button.config(state="disabled")
        self.next_button.config(state="normal")

    def _next_question(self) -> None:
        self._render_question()

    def _build_results_screen(self) -> None:
        assert self.session is not None

        self._clear_window()
        frame = ttk.Frame(self, padding=24)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=0)

        ttk.Label(
            frame,
            text="Quiz Complete",
            font=self.title_font,
        ).grid(row=0, column=0, sticky="w")
        ttk.Button(frame, text="A+", command=self._increase_font_size).grid(
            row=0, column=1, sticky="e"
        )

        ttk.Label(
            frame,
            text=f"Final score: {self.session.score} / {self.session.total_questions}",
            font=self.result_font,
        ).grid(row=1, column=0, sticky="w", pady=(10, 18))

        summary = ScrolledText(frame, height=20, wrap="word")
        summary.grid(row=2, column=0, sticky="nsew")
        frame.rowconfigure(2, weight=1)

        for index, record in enumerate(self.session.records, start=1):
            status = "Correct" if record.is_correct else f"Incorrect | Correct answer: {record.question.answer_text}"
            summary.insert(
                "end",
                f"{index}. {record.question.prompt}\n"
                f"   {status}\n"
                f"   Topic: {record.question.topic}\n"
                f"   Difficulty: {record.question.difficulty.title()}\n"
                f"   Source: {record.question.source_file.name}\n\n",
            )
        summary.config(state="disabled")

        actions = ttk.Frame(frame, padding=(0, 18, 0, 0))
        actions.grid(row=3, column=0, sticky="w")

        ttk.Button(actions, text="New Quiz", command=self._build_start_screen).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(
            actions,
            text="Open All Notes",
            command=lambda: self._show_note_window(None),
        ).grid(row=0, column=1, sticky="w", padx=(12, 0))

    def _open_current_source(self) -> None:
        if self.last_record is not None:
            source_path = self.last_record.question.source_file
        elif self.session is not None and self.session.current_question() is not None:
            source_path = self.session.current_question().source_file
        else:
            source_path = None
        self._show_note_window(source_path)

    def _show_note_window(self, source_path: Path | None) -> None:
        window = tk.Toplevel(self)
        window.title("Study Notes")
        window.geometry("820x620")

        text = ScrolledText(window, wrap="word")
        text.pack(fill="both", expand=True, padx=12, pady=12)

        if source_path is None:
            parts: list[str] = []
            for path in sorted(PROJECT_ROOT.glob("*.txt")):
                parts.append(f"=== {path.name} ===\n{path.read_text(encoding='utf-8')}\n")
            content = "\n".join(parts)
        else:
            content = source_path.read_text(encoding="utf-8")

        text.insert("1.0", content)
        text.config(state="disabled")


def run_gui() -> None:
    app = QuizApp()
    app.mainloop()
