from __future__ import annotations

import time
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from .engine import AnswerRecord, FlashcardSession, QuizSession, ReviewSession, SubnetEngine
from .quiz_bank import (
    FLASHCARD_BANK,
    NOTES_DIR,
    PROJECT_ROOT,
    QUESTION_BANK,
    available_topics,
    get_flashcards,
    get_global_stats,
    get_port_drill_questions,
    get_questions,
    get_weak_questions,
    load_settings,
    reset_all_data,
    save_flashcard_mastery,
    save_performance,
    save_settings,
)

DOMAIN_NAMES = {
    1: "Networking Concepts",
    2: "Network Implementation",
    3: "Network Operations",
    4: "Network Security",
    5: "Network Troubleshooting"
}

# CompTIA Red & White Palette
COLORS = {
    "bg": "#FFFFFF",
    "sidebar": "#BC2026", # CompTIA Red
    "ribbon": "#FFFFFF",
    "fg_dark": "#1A1A1A",
    "fg_light": "#FFFFFF",
    "accent": "#BC2026",
    "correct": "#2D8A2D",
    "wrong": "#D92128",
    "hover": "#8B181C"
}

class QuizApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("CompTIA Network+ Study Suite")
        self.geometry("1100x800")
        self.minsize(900, 700)
        self.app_settings = load_settings()
        self.palette = COLORS
        self._init_fonts(); self._apply_theme_colors()
        self.session: QuizSession | ReviewSession | None = None
        self.fc_session: FlashcardSession | None = None
        self._timer_after_id: str | None = None
        self.timer_var = tk.StringVar(); self.feedback_var = tk.StringVar()
        self._build_layout(); self._show_dashboard()

    def _init_fonts(self) -> None:
        base_size = self.app_settings.get("font_size", 12); family = "Roboto"
        self.title_font = tkfont.Font(family=family, size=base_size + 10, weight="bold")
        self.header_font = tkfont.Font(family=family, size=base_size + 4, weight="bold")
        self.ui_font = tkfont.Font(family=family, size=base_size)
        self.code_font = tkfont.Font(family="Courier", size=base_size)

    def _apply_theme_colors(self) -> None:
        style = ttk.Style(); style.theme_use("clam"); p = self.palette; self.configure(bg=p["bg"])
        style.configure("TFrame", background=p["bg"])
        style.configure("Sidebar.TFrame", background=p["sidebar"])
        style.configure("Ribbon.TFrame", background=p["ribbon"])
        
        style.configure("TLabel", background=p["bg"], foreground=p["fg_dark"], font=self.ui_font)
        style.configure("Sidebar.TLabel", background=p["sidebar"], foreground=p["fg_light"], font=self.ui_font)
        style.configure("Ribbon.TLabel", background=p["ribbon"], foreground=p["fg_dark"], font=self.header_font)
        
        style.configure("Header.TLabel", font=self.header_font)
        style.configure("Title.TLabel", font=self.title_font)
        
        style.configure("TButton", font=self.ui_font, padding=6, background="#E0E0E0", foreground=p["fg_dark"])
        style.map("TButton", background=[("active", "#CCCCCC")])
        
        style.configure("Primary.TButton", background=p["sidebar"], foreground=p["fg_light"])
        style.map("Primary.TButton", background=[("active", p["hover"])], foreground=[("active", p["fg_light"])])
        
        style.configure("Sidebar.TButton", background=p["sidebar"], foreground=p["fg_light"], borderwidth=0)
        style.map("Sidebar.TButton", background=[("active", p["hover"])], foreground=[("active", p["fg_light"])])
        
        style.configure("TCheckbutton", background=p["bg"], foreground=p["fg_dark"], font=self.ui_font)
        style.configure("TRadiobutton", background=p["bg"], foreground=p["fg_dark"], font=self.ui_font)
        style.configure("TProgressbar", thickness=10, background=p["sidebar"])

    def _build_layout(self) -> None:
        # Upper Ribbon
        self.ribbon = ttk.Frame(self, style="Ribbon.TFrame", height=60)
        self.ribbon.pack(side="top", fill="x")
        self.ribbon.pack_propagate(False)
        ttk.Label(self.ribbon, text="CompTIA Network+ Study Suite", style="Ribbon.TLabel").pack(side="left", padx=20, pady=15)
        ttk.Label(self.ribbon, text="NET+", font=self.title_font, foreground=self.palette["sidebar"], background="white").pack(side="right", padx=20, pady=10)
        
        # Sidebar
        self.sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # Spacer
        ttk.Frame(self.sidebar, height=20, style="Sidebar.TFrame").pack()
        
        nav_items = [
            ("Dashboard", self._show_dashboard), 
            ("Practice Quiz", self._show_quiz_config), 
            ("Port Practice", self._show_port_config), 
            ("Flashcards", self._show_fc_config), 
            ("Subnetting", self._show_subnetting), 
            ("Study Notes", self._show_notes), 
            ("Settings", self._show_settings)
        ]
        for text, cmd in nav_items: 
            ttk.Button(self.sidebar, text=text, command=lambda c=cmd: self._safe_nav(c), style="Sidebar.TButton").pack(fill="x", padx=15, pady=5)
            
        self.main_area = ttk.Frame(self)
        self.main_area.pack(side="right", fill="both", expand=True)

    def _safe_nav(self, destination_cmd: callable) -> None:
        if self.session and not self.session.finished:
            if not messagebox.askyesno("Quit Session", "An active quiz session is running. Are you sure you want to quit? Progress will be lost."): return
        self.session = None; self.fc_session = None; destination_cmd()

    def _clear_main(self) -> None:
        if self._timer_after_id: self.after_cancel(self._timer_after_id); self._timer_after_id = None
        for child in self.main_area.winfo_children(): child.destroy()

    def _show_dashboard(self) -> None:
        self._clear_main(); frame = ttk.Frame(self.main_area, padding=40); frame.pack(fill="both", expand=True); ttk.Label(frame, text="System Mastery", style="Title.TLabel").pack(anchor="w", pady=(0, 30))
        stats = get_global_stats()
        for i in range(1, 6):
            d_stats = stats[i]; acc = (d_stats["correct"] / d_stats["total"] * 100) if d_stats["total"] > 0 else 0
            row = ttk.Frame(frame); row.pack(fill="x", pady=10); ttk.Label(row, text=f"Domain {i}: {DOMAIN_NAMES[i]}", width=30).pack(side="left"); pb = ttk.Progressbar(row, length=400, mode="determinate", value=acc); pb.pack(side="left", padx=20); ttk.Label(row, text=f"{acc:.0f}% Accurate").pack(side="left")

        # Topic Practice Section
        topic_frame = ttk.LabelFrame(frame, text="Focused Topic Practice", padding=15)
        topic_frame.pack(fill="x", pady=20)
        
        self.topic_selector = ttk.Combobox(topic_frame, values=available_topics(), state="readonly", font=self.ui_font)
        self.topic_selector.set("Choose a specific topic...")
        self.topic_selector.pack(side="left", padx=10, fill="x", expand=True)
        
        ttk.Button(topic_frame, text="Start Topic Quiz", style="Primary.TButton", 
                   command=lambda: self._start_focused_practice([self.topic_selector.get()], 15)).pack(side="left", padx=10)

        # Smart Practice Section
        smart_frame = ttk.Frame(frame); smart_frame.pack(fill="x", pady=10)
        def start_weak():
            qs = get_weak_questions(limit=15)
            if not qs: messagebox.showinfo("Smart Quiz", "No weak areas identified yet. Complete some standard quizzes first!")
            else: self.session = QuizSession(qs); self._render_quiz_view()
            
        ttk.Button(smart_frame, text="Practice Weakest Questions", command=start_weak).pack(side="left")

    def _show_quiz_config(self) -> None:
        self._clear_main(); frame = ttk.Frame(self.main_area, padding=40); frame.pack(fill="both", expand=True); ttk.Label(frame, text="Practice Quiz", style="Title.TLabel").pack(anchor="w", pady=(0, 20))
        self.sel_domains = {i: tk.BooleanVar(value=True) for i in range(1, 6)}
        d_frame = ttk.LabelFrame(frame, text="Scope", padding=15); d_frame.pack(fill="x", pady=10)
        for i, var in self.sel_domains.items():
            count = sum(1 for q in QUESTION_BANK if q.domain_id == i); state = "normal" if count > 0 else "disabled"
            ttk.Checkbutton(d_frame, text=f"D{i}: {DOMAIN_NAMES[i]} ({count} items)", variable=var, state=state).pack(anchor="w")
        opt_frame = ttk.Frame(frame); opt_frame.pack(fill="x", pady=20); ttk.Label(opt_frame, text="Questions:").pack(side="left"); self.q_count = tk.IntVar(value=10); ttk.Spinbox(opt_frame, from_=1, to=len(QUESTION_BANK), textvariable=self.q_count, width=5).pack(side="left", padx=10); self.q_shuffle = tk.BooleanVar(value=True); ttk.Checkbutton(opt_frame, text="Shuffle", variable=self.q_shuffle).pack(side="left", padx=20); ttk.Button(frame, text="Start Session", style="Primary.TButton", command=self._start_quiz).pack(pady=20)

    def _start_quiz(self) -> None:
        ds = [d for d, v in self.sel_domains.items() if v.get()]; qs = get_questions(domains=ds, limit=self.q_count.get(), shuffle=self.q_shuffle.get())
        if qs: self.session = QuizSession(qs); self._render_quiz_view()

    def _show_port_config(self) -> None:
        self._clear_main(); frame = ttk.Frame(self.main_area, padding=40); frame.pack(fill="both", expand=True); ttk.Label(frame, text="Port Drill Mode", style="Title.TLabel").pack(anchor="w", pady=(0, 20))
        opt_frame = ttk.LabelFrame(frame, text="Options", padding=20); opt_frame.pack(fill="x", pady=30); self.port_secure_only = tk.BooleanVar(value=False); ttk.Checkbutton(opt_frame, text="Secure Protocols Only", variable=self.port_secure_only).pack(anchor="w", pady=5); ttk.Label(opt_frame, text="Count:").pack(side="left"); self.port_q_count = tk.IntVar(value=20); ttk.Spinbox(opt_frame, from_=5, to=50, textvariable=self.port_q_count, width=5).pack(side="left", padx=10); ttk.Button(frame, text="Start Drill", style="Primary.TButton", command=self._start_port_drill).pack(pady=20)

    def _start_port_drill(self) -> None:
        qs = get_port_drill_questions(secure_only=self.port_secure_only.get(), limit=self.port_q_count.get()); self.session = QuizSession(qs); self._render_quiz_view()

    def _show_poe_config(self) -> None: self._show_simple_config("PoE Practice", ["PoE Standards"], "Master Power over Ethernet standards.")
    def _show_wifi_config(self) -> None: self._show_simple_config("WiFi Practice", ["Wireless Standards"], "Master 802.11 standards.")
    def _show_cabling_config(self) -> None: self._show_simple_config("Cabling Practice", ["Cat Cabling"], "Master Category copper cabling.")

    def _show_simple_config(self, title: str, topics: list[str], description: str) -> None:
        self._clear_main(); frame = ttk.Frame(self.main_area, padding=40); frame.pack(fill="both", expand=True); ttk.Label(frame, text=title, style="Title.TLabel").pack(anchor="w", pady=(0, 20)); ttk.Label(frame, text=description, wraplength=600).pack(anchor="w"); opt_frame = ttk.LabelFrame(frame, text="Options", padding=20); opt_frame.pack(fill="x", pady=30); q_count = tk.IntVar(value=10); ttk.Spinbox(opt_frame, from_=5, to=50, textvariable=q_count, width=5).pack(side="left", padx=10); ttk.Button(frame, text="Start Practice", style="Primary.TButton", command=lambda: self._start_focused_practice(topics, q_count.get())).pack(pady=20)

    def _start_focused_practice(self, topics: list[str], count: int) -> None:
        qs = get_questions(topics=topics, limit=count, shuffle=True); self.session = QuizSession(qs); self._render_quiz_view()

    def _render_quiz_view(self) -> None:
        self._clear_main(); self.feedback_var.set(""); q = self.session.current_question()
        if not q: self._show_results(); return
        frame = ttk.Frame(self.main_area, padding=30); frame.pack(fill="both", expand=True); prog_bar = ttk.Progressbar(frame, mode="determinate", value=(self.session.position/self.session.total_questions)*100); prog_bar.pack(fill="x", pady=(0, 20))
        header_text = f"Question {self.session.position+1}/{self.session.total_questions}"; 
        if self.session.is_review: header_text += " [MASTERY REVIEW]"
        ttk.Label(frame, text=header_text, foreground="gray").pack(anchor="w"); ttk.Label(frame, text=q.prompt, font=self.header_font, wraplength=700, justify="left").pack(anchor="w", pady=20)
        self.choice_frame = ttk.Frame(frame); self.choice_frame.pack(fill="both", expand=True); self.vars = []; self.single_var = tk.IntVar(value=-1)
        
        # Use session choices if mastery review (they are shuffled)
        if hasattr(self.session, "current_choices") and self.session.is_review:
            choices = self.session.current_choices
        else:
            choices = q.choices
        
        if q.is_multi_select:
            for i, c in enumerate(choices):
                v = tk.BooleanVar(); self.vars.append(v); ttk.Checkbutton(self.choice_frame, text=c, variable=v).pack(anchor="w", pady=5)
        else:
            for i, c in enumerate(choices): ttk.Radiobutton(self.choice_frame, text=c, value=i, variable=self.single_var).pack(anchor="w", pady=5)
        self.fb_lbl = ttk.Label(frame, textvariable=self.feedback_var, wraplength=700); self.fb_lbl.pack(pady=20)
        btn_bar = ttk.Frame(frame); btn_bar.pack(side="bottom", fill="x")
        self.sub_btn = ttk.Button(btn_bar, text="Submit", style="Primary.TButton", command=self._submit_quiz); self.sub_btn.pack(side="left", padx=5)
        self.next_btn = ttk.Button(btn_bar, text="Next", state="disabled", command=self._render_quiz_view); self.next_btn.pack(side="left", padx=5)
        ttk.Button(btn_bar, text="Source Note", command=lambda: self._show_notes(q.source_file)).pack(side="left", padx=5)

    def _submit_quiz(self) -> None:
        q = self.session.current_question(); sel = tuple(i for i, v in enumerate(self.vars) if v.get()) if q.is_multi_select else (self.single_var.get(),)
        if not sel or (not q.is_multi_select and sel[0] < 0): return
        rec = self.session.answer_current(sel)
        
        # Only save performance for REAL questions, not procedurally generated drills or review sessions
        is_drill = q.id.startswith("drill-p-") or q.id.startswith("drill-n-") or q.id.startswith("subnet-")
        if not is_drill and not self.session.is_review:
            save_performance(q.id, rec.is_correct)
            
        p = self.palette; color = p["correct"] if rec.is_correct else p["wrong"]; prefix = "CORRECT" if rec.is_correct else f"INCORRECT. Answer: {', '.join(rec.question.answer_texts)}"
        self.feedback_var.set(f"{prefix}\n\n{q.explanation}"); self.fb_lbl.config(foreground=color); self.sub_btn.config(state="disabled"); self.next_btn.config(state="normal")

    def _show_results(self) -> None:
        self._clear_main(); frame = ttk.Frame(self.main_area, padding=40); frame.pack(fill="both", expand=True); ttk.Label(frame, text="Session Complete", style="Title.TLabel").pack(pady=20); ttk.Label(frame, text=f"Final Score: {self.session.score} / {self.session.total_questions}", font=self.header_font).pack()
        if not self.session.is_review:
            missed = self.session.missed_questions
            if missed:
                ttk.Label(frame, text=f"You missed {len(missed)} questions in this session.").pack(pady=10)
                ttk.Button(frame, text="Start Mastery Review", style="Primary.TButton", command=lambda: self._start_instant_review(missed)).pack(pady=10)
        ttk.Button(frame, text="Back to Dashboard", command=self._show_dashboard).pack(pady=20)

    def _start_instant_review(self, questions: list) -> None:
        self.session = ReviewSession(questions, QUESTION_BANK); self._render_quiz_view()

    # --- Flashcards / Subnetting / Notes / Settings ---
    def _show_fc_config(self) -> None:
        self._clear_main(); frame = ttk.Frame(self.main_area, padding=40); frame.pack(fill="both", expand=True); ttk.Label(frame, text="Flashcards", style="Title.TLabel").pack(anchor="w", pady=(0, 20))
        self.fc_ds = {i: tk.BooleanVar(value=True) for i in range(1, 6)}
        for i, v in self.fc_ds.items():
            count = sum(1 for c in FLASHCARD_BANK if c.domain_id == i); ttk.Checkbutton(frame, text=f"Domain {i} ({count} cards)", variable=v, state="normal" if count > 0 else "disabled").pack(anchor="w")
        ttk.Button(frame, text="Start Session", style="Primary.TButton", command=self._start_fc).pack(pady=20)

    def _start_fc(self) -> None:
        ds = [d for d, v in self.fc_ds.items() if v.get()]; cs = get_flashcards(domains=ds)
        if cs: self.fc_session = FlashcardSession(cs); self._render_fc()

    def _render_fc(self) -> None:
        self._clear_main(); c = self.fc_session.current_card
        if not c: self._show_dashboard(); return
        frame = ttk.Frame(self.main_area, padding=50); frame.pack(fill="both", expand=True); self.card_container = tk.Frame(frame, width=600, height=350, bg=self.palette["sidebar"], highlightthickness=2, highlightbackground=self.palette["sidebar"]); self.card_container.pack_propagate(False); self.card_container.pack(pady=20); self.card = tk.Label(self.card_container, text=c.term, bg=self.palette["sidebar"], fg=self.palette["fg_light"], font=self.title_font, wraplength=550, justify="center"); self.card.pack(fill="both", expand=True); self.card_container.bind("<Button-1>", lambda e: self._flip_fc(c)); self.card.bind("<Button-1>", lambda e: self._flip_fc(c)); ttk.Label(frame, text="Click card to flip", foreground="gray").pack(); self.fc_btns = ttk.Frame(frame); self.fc_btns.pack(pady=20)

    def _flip_fc(self, card: any) -> None:
        self.card.config(text=card.definition, font=self.header_font, bg=self.palette["bg"], fg=self.palette["fg_dark"]); self.card_container.config(bg=self.palette["bg"]); [b.destroy() for b in self.fc_btns.winfo_children()]; ttk.Button(self.fc_btns, text="I Knew It", style="Primary.TButton", command=lambda: self._report_fc(True)).pack(side="left", padx=10); ttk.Button(self.fc_btns, text="Review Again", command=lambda: self._report_fc(False)).pack(side="left", padx=10)

    def _report_fc(self, known: bool) -> None: save_flashcard_mastery(self.fc_session.current_card.id, known); self.fc_session.report(known); self._render_fc()

    def _show_subnetting(self) -> None:
        self._clear_main(); frame = ttk.Frame(self.main_area, padding=40); frame.pack(fill="both", expand=True); chal = SubnetEngine.generate_challenge(); ttk.Label(frame, text="Subnetting Challenge", style="Title.TLabel").pack(anchor="w"); ttk.Label(frame, text=f"IP/CIDR: {chal['ip']} / {chal['cidr']}", font=self.header_font).pack(pady=20); self.entries = {}; self.correct_labels = {}
        
        # Grid for the 6 fields
        grid_f = ttk.Frame(frame); grid_f.pack(fill="x", pady=10)
        fields = [
            ("Mask", "mask"), ("Network ID", "network"), ("Broadcast", "broadcast"),
            ("First Usable", "first_usable"), ("Last Usable", "last_usable"), ("Hosts", "num_hosts")
        ]
        
        for idx, (label, key) in enumerate(fields):
            row = idx // 2; col = idx % 2
            f = ttk.Frame(grid_f, padding=5); f.grid(row=row, column=col, sticky="ew")
            ttk.Label(f, text=f"{label}:", width=12).pack(side="left")
            e = tk.Entry(f, font=self.ui_font, bg="white", fg="black", insertbackground="black", bd=0, highlightthickness=1)
            e.config(highlightbackground="#E0E0E0", highlightcolor=self.palette["sidebar"])
            e.pack(side="left", fill="x", expand=True)
            self.entries[key] = e
            cl = ttk.Label(f, text="", font=("Roboto", 10), foreground=self.palette["accent"])
            cl.pack(side="bottom", anchor="w", padx=15)
            self.correct_labels[key] = cl

        grid_f.columnconfigure(0, weight=1); grid_f.columnconfigure(1, weight=1)
        
        btn_f = ttk.Frame(frame); btn_f.pack(pady=20)
        ttk.Button(btn_f, text="Check Answers", style="Primary.TButton", command=lambda: self._check_subnet(chal)).pack(side="left", padx=10)
        ttk.Button(btn_f, text="New Challenge", command=self._show_subnetting).pack(side="left", padx=10)
        self.sub_fb = ttk.Label(frame, text="", font=self.header_font); self.sub_fb.pack()

    def _check_subnet(self, chal: dict) -> None:
        all_correct = True
        for k, e in self.entries.items():
            if e.cget("state") == "readonly":
                continue
                
            u = e.get().strip(); a = str(chal[k])
            if u == a: 
                e.config(highlightbackground=self.palette["correct"], 
                         highlightcolor=self.palette["correct"], 
                         state="readonly", 
                         readonlybackground="#E8F5E9") # Light green for correct
                self.correct_labels[k].config(text="✓ Correct", foreground=self.palette["correct"])
            else: 
                e.config(highlightbackground=self.palette["wrong"], highlightcolor=self.palette["wrong"])
                self.correct_labels[k].config(text=f"Expected: {a}", foreground=self.palette["wrong"])
                all_correct = False
        
        if all_correct:
            # Check if truly all are correct (some might have been locked previously)
            truly_all = all(self.entries[key].get().strip() == str(chal[key]) for key in self.entries)
            if truly_all:
                self.sub_fb.config(text="✓ CHALLENGE COMPLETE", foreground=self.palette["correct"])
            else:
                self.sub_fb.config(text="✗ FIX HIGHLIGHTED FIELDS", foreground=self.palette["wrong"])
        else:
            self.sub_fb.config(text="✗ FIX HIGHLIGHTED FIELDS", foreground=self.palette["wrong"])

    def _show_settings(self) -> None:
        self._clear_main()
        frame = ttk.Frame(self.main_area, padding=40)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Settings", style="Title.TLabel").pack(anchor="w", pady=(0, 20))
        
        ttk.Label(frame, text="Base Font Size:").pack(anchor="w")
        fs_var = tk.IntVar(value=self.app_settings.get("font_size", 12))
        s = ttk.Scale(frame, from_=8, to=24, variable=fs_var, orient="horizontal")
        s.pack(fill="x", pady=10)
        
        ttk.Button(frame, text="Save & Restart", style="Primary.TButton", 
                   command=lambda: self._save_settings_logic(fs_var.get())).pack(pady=20)
        
        ttk.Separator(frame).pack(fill="x", pady=20)
        ttk.Button(frame, text="Reset Progress Data", command=self._reset_data_logic).pack()

    def _save_settings_logic(self, fs: int) -> None:
        self.app_settings["font_size"] = fs
        save_settings(self.app_settings)
        messagebox.showinfo("Restart", "Please restart the application to apply changes.")

    def _reset_data_logic(self) -> None:
        if messagebox.askyesno("Confirm", "Are you sure?"): 
            reset_all_data()
            self._show_dashboard()

    def _show_notes(self, specific: Path = None) -> None:
        win = tk.Toplevel(self); win.title("Study Notes"); win.geometry("800x600")
        win.configure(bg=self.palette["bg"])
        txt = ScrolledText(win, bg=self.palette["bg"], fg=self.palette["fg_dark"], 
                          font=self.ui_font, padx=10, pady=10)
        txt.pack(fill="both", expand=True)
        if specific: content = specific.read_text(encoding="utf-8")
        else:
            p_list = sorted(NOTES_DIR.glob("*.txt"))
            content = "\n".join([f"=== {p.name} ===\n{p.read_text()}\n" for p in p_list if not p.name.endswith(".json")])
        txt.insert("1.0", content); txt.config(state="disabled")

def run_gui() -> None: QuizApp().mainloop()
