from __future__ import annotations

import time
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from .engine import AnswerRecord, FlashcardSession, QuizSession, SubnetEngine
from .quiz_bank import (
    FLASHCARD_BANK,
    PROJECT_ROOT,
    QUESTION_BANK,
    available_domains,
    get_flashcards,
    get_global_stats,
    get_questions,
    save_flashcard_mastery,
    save_performance,
)

DOMAIN_NAMES = {
    1: "Networking Concepts",
    2: "Network Implementation",
    3: "Network Operations",
    4: "Network Security",
    5: "Network Troubleshooting"
}

class QuizApp(tk.Tk):
    """Network+ Study Suite with Quiz, Flashcards, and Subnetting."""

    def __init__(self) -> None:
        super().__init__()
        self.title("CompTIA Network+ Study Suite")
        self.geometry("1000x750")
        self.minsize(850, 650)
        
        self.font_size_offset = 0
        default_family = tkfont.nametofont("TkDefaultFont").cget("family")
        self.title_font = tkfont.Font(family=default_family, size=22, weight="bold")
        self.header_font = tkfont.Font(family=default_family, size=16, weight="bold")
        self.section_font = tkfont.Font(family=default_family, size=12, weight="bold")
        self.prompt_font = tkfont.Font(family=default_family, size=14, weight="bold")
        self.result_font = tkfont.Font(family=default_family, size=13)

        # Session state
        self.session: QuizSession | None = None
        self.fc_session: FlashcardSession | None = None
        self.last_record: AnswerRecord | None = None
        self._timer_after_id: str | None = None
        self._end_time: float = 0
        
        # UI Variables
        self.timer_var = tk.StringVar()
        self.feedback_var = tk.StringVar()
        self.subnet_challenge = {}
        
        self._build_main_menu()

    def _clear_window(self) -> None:
        if self._timer_after_id:
            self.after_cancel(self._timer_after_id)
            self._timer_after_id = None
        for child in self.winfo_children():
            child.destroy()

    def _build_main_menu(self) -> None:
        self._clear_window()
        
        frame = ttk.Frame(self, padding=40)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        # Header
        ttk.Label(frame, text="Network+ Study Suite", font=self.title_font).grid(row=0, column=0, columnspan=2, pady=(0, 30))

        # Dashboard / Stats
        stats_frame = ttk.LabelFrame(frame, text="Current Mastery (Historical Accuracy)", padding=20)
        stats_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 40))
        
        global_stats = get_global_stats()
        for i in range(1, 6):
            d_stats = global_stats[i]
            acc = (d_stats["correct"] / d_stats["total"] * 100) if d_stats["total"] > 0 else 0
            cov = (d_stats["seen"] / d_stats["bank_size"] * 100) if d_stats["bank_size"] > 0 else 0
            
            d_row = ttk.Frame(stats_frame)
            d_row.pack(fill="x", pady=4)
            ttk.Label(d_row, text=f"D{i}: {DOMAIN_NAMES[i]}", width=30).pack(side="left")
            
            pb = ttk.Progressbar(d_row, length=300, mode="determinate", value=acc)
            pb.pack(side="left", padx=20)
            ttk.Label(d_row, text=f"{acc:.0f}% Accuracy | {d_stats['seen']}/{d_stats['bank_size']} Covered").pack(side="left")

        # Action Buttons
        btn_style = {"width": 25, "padding": 10}
        
        ttk.Button(frame, text="Practice Quiz", command=self._build_quiz_config, **btn_style).grid(row=2, column=0, pady=10)
        ttk.Button(frame, text="Flashcard Mode", command=self._build_flashcard_config, **btn_style).grid(row=2, column=1, pady=10)
        ttk.Button(frame, text="Subnetting Challenge", command=self._start_subnetting, **btn_style).grid(row=3, column=0, pady=10)
        ttk.Button(frame, text="Study Notes", command=lambda: self._show_note_window(None), **btn_style).grid(row=3, column=1, pady=10)

    # --- Quiz Module ---

    def _build_quiz_config(self) -> None:
        self._clear_window()
        frame = ttk.Frame(self, padding=40)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="Configure Practice Quiz", font=self.header_font).pack(pady=(0, 20))
        
        # Domain selection
        domain_frame = ttk.LabelFrame(frame, text="Select Domains", padding=15)
        domain_frame.pack(fill="x", pady=10)
        
        self.selected_domains = {}
        for i in range(1, 6):
            var = tk.BooleanVar(value=True)
            self.selected_domains[i] = var
            count = sum(1 for q in QUESTION_BANK if q.domain_id == i)
            state = "normal" if count > 0 else "disabled"
            label = f"Domain {i}: {DOMAIN_NAMES[i]} ({count} questions)"
            ttk.Checkbutton(domain_frame, text=label, variable=var, state=state).pack(anchor="w", pady=2)

        # Options
        opt_frame = ttk.Frame(frame, padding=10)
        opt_frame.pack(fill="x")
        
        ttk.Label(opt_frame, text="Count:").pack(side="left")
        self.q_limit = tk.IntVar(value=10)
        ttk.Spinbox(opt_frame, from_=1, to=len(QUESTION_BANK), textvariable=self.q_limit, width=5).pack(side="left", padx=10)
        
        self.shuffle_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_frame, text="Shuffle", variable=self.shuffle_var).pack(side="left", padx=20)
        
        self.timed_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="Timed (10m)", variable=self.timed_var).pack(side="left")

        btn_bar = ttk.Frame(frame, padding=20)
        btn_bar.pack()
        ttk.Button(btn_bar, text="Back", command=self._build_main_menu).pack(side="left", padx=10)
        ttk.Button(btn_bar, text="Start Quiz", command=self._start_quiz).pack(side="left", padx=10)

    def _start_quiz(self) -> None:
        domains = [d for d, var in self.selected_domains.items() if var.get()]
        if not domains: return
        
        questions = get_questions(domains=domains, limit=self.q_limit.get(), shuffle=self.shuffle_var.get())
        if not questions: return
        
        limit = 600 if self.timed_var.get() else None
        self.session = QuizSession(questions, time_limit_seconds=limit)
        
        if limit:
            self._end_time = time.time() + limit
            self._update_timer()
            
        self._build_question_screen()
        self._render_question()

    def _update_timer(self) -> None:
        if not self.session or not self.timed_var.get(): return
        rem = self._end_time - time.time()
        if rem <= 0:
            self.session.set_timed_out()
            self._build_results_screen()
            return
        m, s = divmod(int(rem), 60)
        self.timer_var.set(f"{m:02d}:{s:02d}")
        self._timer_after_id = self.after(1000, self._update_timer)

    def _build_question_screen(self) -> None:
        self._clear_window()
        frame = ttk.Frame(self, padding=30)
        frame.pack(fill="both", expand=True)
        
        # Header: Progress and Timer
        head = ttk.Frame(frame)
        head.pack(fill="x", pady=(0, 20))
        self.prog_lbl = ttk.Label(head, text="", font=self.section_font)
        self.prog_lbl.pack(side="left")
        ttk.Label(head, textvariable=self.timer_var, font=self.section_font, foreground="red").pack(side="right")
        
        self.topic_lbl = ttk.Label(frame, text="", foreground="gray")
        self.topic_lbl.pack(anchor="w")
        
        self.prompt_lbl = ttk.Label(frame, text="", font=self.prompt_font, wraplength=850, justify="left")
        self.prompt_lbl.pack(anchor="w", pady=20)
        
        self.choices_frame = ttk.Frame(frame)
        self.choices_frame.pack(fill="x", pady=10)
        self.choice_widgets = []
        self.multi_vars = []
        self.single_var = tk.IntVar(value=-1)
        
        ttk.Separator(frame).pack(fill="x", pady=20)
        
        self.fb_lbl = ttk.Label(frame, textvariable=self.feedback_var, wraplength=850, justify="left")
        self.fb_lbl.pack(anchor="w")
        
        btns = ttk.Frame(frame, padding=20)
        btns.pack(side="bottom", fill="x")
        self.sub_btn = ttk.Button(btns, text="Submit", command=self._submit_answer)
        self.sub_btn.pack(side="left", padx=5)
        self.next_btn = ttk.Button(btns, text="Next", command=self._render_question, state="disabled")
        self.next_btn.pack(side="left", padx=5)
        ttk.Button(btns, text="Flag", command=self._toggle_flag).pack(side="left", padx=5)
        ttk.Button(btns, text="Quit", command=self._build_main_menu).pack(side="right")

    def _render_question(self) -> None:
        q = self.session.current_question()
        if not q:
            self._build_results_screen()
            return
            
        self.feedback_var.set("")
        self.prog_lbl.config(text=f"Question {self.session.position+1} of {self.session.total_questions} | Domain {q.domain_id}")
        self.topic_lbl.config(text=f"{q.topic} | {q.difficulty.title()}")
        self.prompt_lbl.config(text=q.prompt + (f" (Select {len(q.answer_indices)})" if q.is_multi_select else ""))
        
        for w in self.choice_widgets: w.destroy()
        self.choice_widgets.clear()
        self.multi_vars.clear()
        
        if q.is_multi_select:
            for i, c in enumerate(q.choices):
                v = tk.BooleanVar()
                self.multi_vars.append(v)
                w = ttk.Checkbutton(self.choices_frame, text=c, variable=v)
                w.pack(anchor="w", pady=5)
                self.choice_widgets.append(w)
        else:
            self.single_var.set(-1)
            for i, c in enumerate(q.choices):
                w = ttk.Radiobutton(self.choices_frame, text=c, value=i, variable=self.single_var)
                w.pack(anchor="w", pady=5)
                self.choice_widgets.append(w)
        
        self.sub_btn.config(state="normal")
        self.next_btn.config(state="disabled")

    def _submit_answer(self) -> None:
        q = self.session.current_question()
        if q.is_multi_select:
            sel = tuple(i for i, v in enumerate(self.multi_vars) if v.get())
            if len(sel) != len(q.answer_indices):
                messagebox.showwarning("Incomplete", f"Select exactly {len(q.answer_indices)}.")
                return
        else:
            if self.single_var.get() < 0: return
            sel = (self.single_var.get(),)
            
        rec = self.session.answer_current(sel)
        save_performance(q.id, rec.is_correct)
        
        for w in self.choice_widgets: w.config(state="disabled")
        prefix = "Correct!" if rec.is_correct else f"Incorrect. Correct: {', '.join(q.answer_texts)}"
        self.feedback_var.set(f"{prefix}\n\nExplanation: {q.explanation}")
        self.sub_btn.config(state="disabled")
        self.next_btn.config(state="normal")

    def _toggle_flag(self) -> None:
        q = self.session.current_question()
        if q: self.session.toggle_flag(q.id)

    def _build_results_screen(self) -> None:
        self._clear_window()
        frame = ttk.Frame(self, padding=40)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="Quiz Results", font=self.header_font).pack(pady=10)
        ttk.Label(frame, text=f"Final Score: {self.session.score} / {self.session.total_questions}", font=self.prompt_font).pack(pady=5)
        
        stats = self.session.domain_stats
        breakdown = ttk.LabelFrame(frame, text="Domain Breakdown", padding=15)
        breakdown.pack(fill="x", pady=20)
        for i in range(1, 6):
            s = stats[i]
            if s["total"] > 0:
                perc = (s["correct"]/s["total"])*100
                ttk.Label(breakdown, text=f"D{i}: {perc:.0f}% ({s['correct']}/{s['total']})").pack(anchor="w")

        ttk.Button(frame, text="Back to Menu", command=self._build_main_menu).pack(pady=20)

    # --- Flashcard Module ---

    def _build_flashcard_config(self) -> None:
        self._clear_window()
        frame = ttk.Frame(self, padding=40)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="Flashcard Mode", font=self.header_font).pack(pady=(0, 20))
        
        domain_frame = ttk.LabelFrame(frame, text="Select Domains", padding=15)
        domain_frame.pack(fill="x", pady=10)
        
        self.fc_domains = {}
        for i in range(1, 6):
            v = tk.BooleanVar(value=True)
            self.fc_domains[i] = v
            count = sum(1 for c in FLASHCARD_BANK if c.domain_id == i)
            state = "normal" if count > 0 else "disabled"
            ttk.Checkbutton(domain_frame, text=f"D{i}: {DOMAIN_NAMES[i]} ({count} cards)", variable=v, state=state).pack(anchor="w", pady=2)

        ttk.Button(frame, text="Start Session", command=self._start_flashcards).pack(pady=20)
        ttk.Button(frame, text="Back", command=self._build_main_menu).pack()

    def _start_flashcards(self) -> None:
        ds = [d for d, v in self.fc_domains.items() if v.get()]
        cards = get_flashcards(domains=ds)
        if not cards: return
        self.fc_session = FlashcardSession(cards)
        self._build_fc_screen()
        self._render_fc()

    def _build_fc_screen(self) -> None:
        self._clear_window()
        frame = ttk.Frame(self, padding=50)
        frame.pack(fill="both", expand=True)
        
        self.fc_prog = ttk.Label(frame, text="", font=self.section_font)
        self.fc_prog.pack(pady=(0, 30))
        
        # The Card
        self.card_frame = tk.Frame(frame, bg="white", relief="raised", bd=2, height=300, width=600)
        self.card_frame.pack_propagate(False)
        self.card_frame.pack(pady=20)
        
        self.card_text = tk.Label(self.card_frame, text="", font=self.title_font, bg="white", wraplength=550)
        self.card_text.pack(expand=True)
        
        self.is_flipped = False
        self.card_frame.bind("<Button-1>", lambda e: self._flip_card())
        self.card_text.bind("<Button-1>", lambda e: self._flip_card())
        
        ttk.Label(frame, text="(Click card to flip)", foreground="gray").pack()
        
        self.fc_actions = ttk.Frame(frame, padding=30)
        self.fc_actions.pack(fill="x")
        
        self.btn_known = ttk.Button(self.fc_actions, text="I Knew It", command=lambda: self._report_fc(True))
        self.btn_not_known = ttk.Button(self.fc_actions, text="Need Review", command=lambda: self._report_fc(False))
        
        ttk.Button(frame, text="Quit Session", command=self._build_main_menu).pack(side="bottom", pady=20)

    def _render_fc(self) -> None:
        c = self.fc_session.current_card
        if not c:
            self._build_main_menu()
            return
            
        self.is_flipped = False
        self.fc_prog.config(text=f"Card {self.fc_session.position+1} of {self.fc_session.total}")
        self.card_text.config(text=c.term, font=self.title_font, foreground="black")
        self.btn_known.pack_forget()
        self.btn_not_known.pack_forget()

    def _flip_card(self) -> None:
        c = self.fc_session.current_card
        if not self.is_flipped:
            self.card_text.config(text=c.definition, font=self.prompt_font, foreground="darkblue")
            self.btn_known.pack(side="left", expand=True)
            self.btn_not_known.pack(side="left", expand=True)
            self.is_flipped = True
        else:
            self.card_text.config(text=c.term, font=self.title_font, foreground="black")
            self.btn_known.pack_forget()
            self.btn_not_known.pack_forget()
            self.is_flipped = False

    def _report_fc(self, known: bool) -> None:
        c = self.fc_session.current_card
        save_flashcard_mastery(c.id, known)
        self.fc_session.report(known)
        self._render_fc()

    # --- Subnetting Module ---

    def _start_subnetting(self) -> None:
        self._clear_window()
        frame = ttk.Frame(self, padding=40)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="Subnetting Challenge", font=self.header_font).pack(pady=(0, 20))
        
        self.sub_chal = SubnetEngine.generate_challenge()
        
        ttk.Label(frame, text=f"Identify the following for: {self.sub_chal['ip']} / {self.sub_chal['cidr']}", font=self.prompt_font).pack(pady=20)
        
        form = ttk.Frame(frame)
        form.pack()
        
        self.sub_entries = {}
        for i, label in enumerate(["Subnet Mask", "Network ID", "Broadcast Address"]):
            ttk.Label(form, text=label + ":").grid(row=i, column=0, sticky="e", padx=10, pady=10)
            ent = ttk.Entry(form, width=25, font=self.prompt_font)
            ent.grid(row=i, column=1, sticky="w", pady=10)
            key = label.split()[0].lower()
            if key == "subnet": key = "mask"
            self.sub_entries[key] = ent

        self.sub_fb = ttk.Label(frame, text="", wraplength=600)
        self.sub_fb.pack(pady=20)
        
        btn_bar = ttk.Frame(frame)
        btn_bar.pack()
        self.sub_check_btn = ttk.Button(btn_bar, text="Check Answers", command=self._check_subnet)
        self.sub_check_btn.pack(side="left", padx=10)
        ttk.Button(btn_bar, text="New Challenge", command=self._start_subnetting).pack(side="left", padx=10)
        ttk.Button(btn_bar, text="Main Menu", command=self._build_main_menu).pack(side="left", padx=10)

    def _check_subnet(self) -> None:
        correct = True
        fb_msg = ""
        for key, ent in self.sub_entries.items():
            user_val = ent.get().strip()
            actual = self.sub_chal[key]
            if user_val == actual:
                ent.config(foreground="green")
            else:
                ent.config(foreground="red")
                correct = False
                fb_msg += f"{key.title()}: Expected {actual}\n"
        
        if correct:
            self.sub_fb.config(text="Perfect! All answers correct.", foreground="green")
        else:
            self.sub_fb.config(text=f"Some errors found:\n{fb_msg}", foreground="red")

    # --- Notes Viewer (Re-integrated) ---

    def _show_note_window(self, source_path: Path | None) -> None:
        window = tk.Toplevel(self)
        window.title("Study Notes")
        window.geometry("820x620")
        text = ScrolledText(window, wrap="word")
        text.pack(fill="both", expand=True, padx=12, pady=12)
        if source_path is None:
            parts = []
            notes_dir = PROJECT_ROOT / "notes"
            for path in sorted(notes_dir.glob("*.txt")):
                if path.name == "questions.json" or path.name == "flashcards.json": continue
                parts.append(f"=== {path.name} ===\n{path.read_text(encoding='utf-8')}\n")
            content = "\n".join(parts)
        else:
            content = source_path.read_text(encoding="utf-8")
        text.insert("1.0", content)
        text.config(state="disabled")

def run_gui() -> None:
    app = QuizApp()
    app.mainloop()
