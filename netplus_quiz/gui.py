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
    NOTES_DIR,
    PROJECT_ROOT,
    QUESTION_BANK,
    get_flashcards,
    get_global_stats,
    get_port_drill_questions,
    get_questions,
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

# Nord/CompTIA Palette
COLORS = {
    "dark": {
        "bg": "#2E3440",
        "sidebar": "#242933",
        "fg": "#ECEFF4",
        "primary": "#0072CE",  # CompTIA Blue
        "accent": "#FF8200",   # CompTIA Orange
        "nord_blue": "#88C0D0",
        "correct": "#A3BE8C",
        "wrong": "#BF616A",
        "hover": "#3B4252"
    },
    "light": {
        "bg": "#ECEFF4",
        "sidebar": "#D8DEE9",
        "fg": "#2E3440",
        "primary": "#0072CE",
        "accent": "#FF8200",
        "nord_blue": "#5E81AC",
        "correct": "#4F734F",
        "wrong": "#8B4B4B",
        "hover": "#E5E9F0"
    }
}

class QuizApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("CompTIA Network+ Study Suite")
        self.geometry("1100x800")
        self.minsize(900, 700)
        
        self.app_settings = load_settings()
        self.current_theme = self.app_settings.get("theme", "dark")
        self.palette = COLORS[self.current_theme]
        
        self._init_fonts()
        self._apply_theme_colors()

        # Session state
        self.session: QuizSession | None = None
        self.fc_session: FlashcardSession | None = None
        self._timer_after_id: str | None = None
        
        # UI Variables
        self.timer_var = tk.StringVar()
        self.feedback_var = tk.StringVar()
        
        self._build_layout()
        self._show_dashboard()

    def _init_fonts(self) -> None:
        base_size = self.app_settings.get("font_size", 12)
        family = "Roboto"
        self.title_font = tkfont.Font(family=family, size=base_size + 10, weight="bold")
        self.header_font = tkfont.Font(family=family, size=base_size + 4, weight="bold")
        self.ui_font = tkfont.Font(family=family, size=base_size)
        self.code_font = tkfont.Font(family="Courier", size=base_size)

    def _apply_theme_colors(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        p = self.palette
        
        self.configure(bg=p["bg"])
        
        style.configure("TFrame", background=p["bg"])
        style.configure("Sidebar.TFrame", background=p["sidebar"])
        style.configure("TLabel", background=p["bg"], foreground=p["fg"], font=self.ui_font)
        style.configure("Header.TLabel", font=self.header_font)
        style.configure("Title.TLabel", font=self.title_font)
        
        style.configure("TButton", font=self.ui_font, padding=6, background=p["sidebar"], foreground=p["fg"])
        style.map("TButton", 
                  background=[("active", p["hover"])],
                  foreground=[("active", p["fg"])])
        
        style.configure("Primary.TButton", background=p["primary"], foreground="white")
        style.map("Primary.TButton", 
                  background=[("active", p["nord_blue"])],
                  foreground=[("active", "white")])
        
        style.configure("Sidebar.TButton", background=p["sidebar"], foreground=p["fg"], borderwidth=0)
        style.map("Sidebar.TButton", 
                  background=[("active", p["bg"])],
                  foreground=[("active", p["fg"])])
        
        style.configure("TCheckbutton", background=p["bg"], foreground=p["fg"], font=self.ui_font)
        style.map("TCheckbutton", 
                  background=[("active", p["bg"])],
                  foreground=[("active", p["fg"])])
                  
        style.configure("TRadiobutton", background=p["bg"], foreground=p["fg"], font=self.ui_font)
        style.map("TRadiobutton", 
                  background=[("active", p["bg"])],
                  foreground=[("active", p["fg"])])

        style.configure("TProgressbar", thickness=10, background=p["nord_blue"])

    def _build_layout(self) -> None:
        self.sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        ttk.Label(self.sidebar, text="Net+", style="Title.TLabel", background=self.palette["sidebar"]).pack(pady=20)
        
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
            ttk.Button(self.sidebar, text=text, command=cmd, style="Sidebar.TButton").pack(fill="x", padx=10, pady=5)
            
        self.main_area = ttk.Frame(self)
        self.main_area.pack(side="right", fill="both", expand=True)

    def _clear_main(self) -> None:
        if self._timer_after_id:
            self.after_cancel(self._timer_after_id)
            self._timer_after_id = None
        for child in self.main_area.winfo_children():
            child.destroy()

    def _show_dashboard(self) -> None:
        self._clear_main()
        frame = ttk.Frame(self.main_area, padding=40)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="System Mastery", style="Title.TLabel").pack(anchor="w", pady=(0, 30))
        
        stats = get_global_stats()
        for i in range(1, 6):
            d_stats = stats[i]
            acc = (d_stats["correct"] / d_stats["total"] * 100) if d_stats["total"] > 0 else 0
            
            row = ttk.Frame(frame)
            row.pack(fill="x", pady=10)
            ttk.Label(row, text=f"Domain {i}: {DOMAIN_NAMES[i]}", width=30).pack(side="left")
            
            pb = ttk.Progressbar(row, length=400, mode="determinate", value=acc)
            pb.pack(side="left", padx=20)
            ttk.Label(row, text=f"{acc:.0f}% Accurate").pack(side="left")

    # --- Quiz Configuration ---
    def _show_quiz_config(self) -> None:
        self._clear_main()
        frame = ttk.Frame(self.main_area, padding=40)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="Practice Quiz", style="Title.TLabel").pack(anchor="w", pady=(0, 20))
        
        self.sel_domains = {i: tk.BooleanVar(value=True) for i in range(1, 6)}
        d_frame = ttk.LabelFrame(frame, text="Scope", padding=15)
        d_frame.pack(fill="x", pady=10)
        
        for i, var in self.sel_domains.items():
            count = sum(1 for q in QUESTION_BANK if q.domain_id == i)
            state = "normal" if count > 0 else "disabled"
            ttk.Checkbutton(d_frame, text=f"D{i}: {DOMAIN_NAMES[i]} ({count} items)", variable=var, state=state).pack(anchor="w")

        opt_frame = ttk.Frame(frame)
        opt_frame.pack(fill="x", pady=20)
        
        ttk.Label(opt_frame, text="Questions:").pack(side="left")
        self.q_count = tk.IntVar(value=10)
        ttk.Spinbox(opt_frame, from_=1, to=len(QUESTION_BANK), textvariable=self.q_count, width=5).pack(side="left", padx=10)
        
        self.q_shuffle = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_frame, text="Shuffle", variable=self.q_shuffle).pack(side="left", padx=20)
        
        ttk.Button(frame, text="Start Session", style="Primary.TButton", command=self._start_quiz).pack(pady=20)

    def _start_quiz(self) -> None:
        ds = [d for d, v in self.sel_domains.items() if v.get()]
        if not ds: return
        qs = get_questions(domains=ds, limit=self.q_count.get(), shuffle=self.q_shuffle.get())
        if not qs: return
        self.session = QuizSession(qs)
        self._render_quiz_view()

    # --- Port Practice ---
    def _show_port_config(self) -> None:
        self._clear_main()
        frame = ttk.Frame(self.main_area, padding=40)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="Port Drill Mode", style="Title.TLabel").pack(anchor="w", pady=(0, 20))
        ttk.Label(frame, text="Bidirectional Multiple Choice practice for all protocols and ports.", wraplength=600).pack(anchor="w")
        
        opt_frame = ttk.LabelFrame(frame, text="Options", padding=20)
        opt_frame.pack(fill="x", pady=30)
        
        self.port_secure_only = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="Secure Protocols Only (SSH, HTTPS, etc)", variable=self.port_secure_only).pack(anchor="w", pady=5)
        
        ttk.Label(opt_frame, text="Question Count:").pack(side="left", pady=10)
        self.port_q_count = tk.IntVar(value=20)
        ttk.Spinbox(opt_frame, from_=5, to=50, textvariable=self.port_q_count, width=5).pack(side="left", padx=10)
        
        ttk.Button(frame, text="Start Drill", style="Primary.TButton", command=self._start_port_drill).pack(pady=20)

    def _start_port_drill(self) -> None:
        qs = get_port_drill_questions(secure_only=self.port_secure_only.get(), limit=self.port_q_count.get())
        if not qs: return
        self.session = QuizSession(qs)
        self._render_quiz_view()

    def _render_quiz_view(self) -> None:
        self._clear_main()
        self.feedback_var.set("")
        q = self.session.current_question()
        if not q:
            self._show_results()
            return
            
        frame = ttk.Frame(self.main_area, padding=30)
        frame.pack(fill="both", expand=True)
        
        prog_bar = ttk.Progressbar(frame, mode="determinate", value=(self.session.position/self.session.total_questions)*100)
        prog_bar.pack(fill="x", pady=(0, 20))
        
        ttk.Label(frame, text=f"Question {self.session.position+1}/{self.session.total_questions} - {q.topic}", foreground="gray").pack(anchor="w")
        ttk.Label(frame, text=q.prompt, font=self.header_font, wraplength=700, justify="left").pack(anchor="w", pady=20)
        
        self.choice_frame = ttk.Frame(frame)
        self.choice_frame.pack(fill="both", expand=True)
        self.vars = []
        self.single_var = tk.IntVar(value=-1)
        
        if q.is_multi_select:
            for i, c in enumerate(q.choices):
                v = tk.BooleanVar()
                self.vars.append(v)
                ttk.Checkbutton(self.choice_frame, text=c, variable=v).pack(anchor="w", pady=5)
        else:
            for i, c in enumerate(q.choices):
                ttk.Radiobutton(self.choice_frame, text=c, value=i, variable=self.single_var).pack(anchor="w", pady=5)
                
        self.fb_lbl = ttk.Label(frame, textvariable=self.feedback_var, wraplength=700)
        self.fb_lbl.pack(pady=20)
        
        btn_bar = ttk.Frame(frame)
        btn_bar.pack(side="bottom", fill="x")
        
        self.sub_btn = ttk.Button(btn_bar, text="Submit", style="Primary.TButton", command=self._submit_quiz)
        self.sub_btn.pack(side="left", padx=5)
        self.next_btn = ttk.Button(btn_bar, text="Next", state="disabled", command=self._render_quiz_view)
        self.next_btn.pack(side="left", padx=5)
        ttk.Button(btn_bar, text="Source Note", command=lambda: self._show_notes(q.source_file)).pack(side="left", padx=5)

    def _submit_quiz(self) -> None:
        q = self.session.current_question()
        sel = tuple(i for i, v in enumerate(self.vars) if v.get()) if q.is_multi_select else (self.single_var.get(),)
        if not sel or (not q.is_multi_select and sel[0] < 0): return
        
        rec = self.session.answer_current(sel)
        # Don't save performance for drills to avoid skewing domain stats with synthetic questions
        if "drill" not in q.id:
            save_performance(q.id, rec.is_correct)
        
        p = self.palette
        color = p["correct"] if rec.is_correct else p["wrong"]
        prefix = "CORRECT" if rec.is_correct else f"INCORRECT. Answer: {', '.join(q.answer_texts)}"
        self.feedback_var.set(f"{prefix}\n\n{q.explanation}")
        self.fb_lbl.config(foreground=color)
        
        self.sub_btn.config(state="disabled")
        self.next_btn.config(state="normal")

    def _show_results(self) -> None:
        self._clear_main()
        frame = ttk.Frame(self.main_area, padding=40)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Session Complete", style="Title.TLabel").pack(pady=20)
        ttk.Label(frame, text=f"Score: {self.session.score} / {self.session.total_questions}", font=self.header_font).pack()
        ttk.Button(frame, text="Finish", command=self._show_dashboard).pack(pady=30)

    # --- Flashcards ---
    def _show_fc_config(self) -> None:
        self._clear_main()
        frame = ttk.Frame(self.main_area, padding=40)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Flashcards", style="Title.TLabel").pack(anchor="w", pady=(0, 20))
        
        self.fc_ds = {i: tk.BooleanVar(value=True) for i in range(1, 6)}
        for i, v in self.fc_ds.items():
            count = sum(1 for c in FLASHCARD_BANK if c.domain_id == i)
            ttk.Checkbutton(frame, text=f"Domain {i} ({count} cards)", variable=v, state="normal" if count > 0 else "disabled").pack(anchor="w")
            
        ttk.Button(frame, text="Start Session", style="Primary.TButton", command=self._start_fc).pack(pady=20)

    def _start_fc(self) -> None:
        ds = [d for d, v in self.fc_ds.items() if v.get()]
        cs = get_flashcards(domains=ds)
        if not cs: return
        self.fc_session = FlashcardSession(cs)
        self._render_fc()

    def _render_fc(self) -> None:
        self._clear_main()
        c = self.fc_session.current_card
        if not c:
            self._show_dashboard()
            return
            
        frame = ttk.Frame(self.main_area, padding=50)
        frame.pack(fill="both", expand=True)
        
        self.card_container = tk.Frame(frame, width=600, height=350, bg=self.palette["sidebar"], 
                                       highlightthickness=2, highlightbackground=self.palette["nord_blue"])
        self.card_container.pack_propagate(False)
        self.card_container.pack(pady=20)
        
        self.card = tk.Label(self.card_container, text=c.term, bg=self.palette["sidebar"], fg=self.palette["fg"], 
                             font=self.title_font, wraplength=550, justify="center")
        self.card.pack(fill="both", expand=True)
        
        self.card_container.bind("<Button-1>", lambda e: self._flip_fc(c))
        self.card.bind("<Button-1>", lambda e: self._flip_fc(c))
        
        ttk.Label(frame, text="Click card to flip", foreground="gray").pack()
        
        self.fc_btns = ttk.Frame(frame)
        self.fc_btns.pack(pady=20)

    def _flip_fc(self, card: any) -> None:
        self.card.config(text=card.definition, font=self.header_font, bg=self.palette["nord_blue"], fg="white")
        self.card_container.config(bg=self.palette["nord_blue"])
        for b in self.fc_btns.winfo_children(): b.destroy()
        ttk.Button(self.fc_btns, text="I Knew It", style="Primary.TButton", command=lambda: self._report_fc(True)).pack(side="left", padx=10)
        ttk.Button(self.fc_btns, text="Review Again", command=lambda: self._report_fc(False)).pack(side="left", padx=10)

    def _report_fc(self, known: bool) -> None:
        save_flashcard_mastery(self.fc_session.current_card.id, known)
        self.fc_session.report(known)
        self._render_fc()

    # --- Subnetting ---
    def _show_subnetting(self) -> None:
        self._clear_main()
        frame = ttk.Frame(self.main_area, padding=40)
        frame.pack(fill="both", expand=True)
        
        chal = SubnetEngine.generate_challenge()
        ttk.Label(frame, text="Subnetting Challenge", style="Title.TLabel").pack(anchor="w")
        ttk.Label(frame, text=f"IP/CIDR: {chal['ip']} / {chal['cidr']}", font=self.header_font).pack(pady=20)
        
        self.entries = {}
        self.correct_labels = {}
        for label in ["Mask", "Network", "Broadcast"]:
            f = ttk.Frame(frame)
            f.pack(fill="x", pady=5)
            ttk.Label(f, text=f"{label}:", width=15).pack(side="left")
            e = tk.Entry(f, font=self.ui_font, bg=self.palette["sidebar"], fg=self.palette["fg"], insertbackground=self.palette["fg"], bd=0, highlightthickness=1)
            e.config(highlightbackground=self.palette["sidebar"], highlightcolor=self.palette["primary"])
            e.pack(side="left", fill="x", expand=True)
            self.entries[label.lower()] = e
            
            cl = ttk.Label(f, text="", foreground=self.palette["nord_blue"])
            cl.pack(side="left", padx=10)
            self.correct_labels[label.lower()] = cl

        ttk.Button(frame, text="Check", style="Primary.TButton", command=lambda: self._check_subnet(chal)).pack(pady=20)
        self.sub_fb = ttk.Label(frame, text="")
        self.sub_fb.pack()
        ttk.Button(frame, text="New", command=self._show_subnetting).pack()

    def _check_subnet(self, chal: dict) -> None:
        correct = True
        for k, e in self.entries.items():
            user_val = e.get().strip()
            actual = chal[k]
            if user_val == actual:
                e.config(highlightbackground=self.palette["correct"], highlightcolor=self.palette["correct"])
                self.correct_labels[k].config(text="")
            else:
                e.config(highlightbackground=self.palette["wrong"], highlightcolor=self.palette["wrong"])
                self.correct_labels[k].config(text=f"Expected: {actual}")
                correct = False
        self.sub_fb.config(text="Perfect!" if correct else "Review the red fields and expected values.", 
                           foreground=self.palette["correct"] if correct else self.palette["wrong"])

    # --- Settings ---
    def _show_settings(self) -> None:
        self._clear_main()
        frame = ttk.Frame(self.main_area, padding=40)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="Settings", style="Title.TLabel").pack(anchor="w", pady=(0, 20))
        
        ttk.Label(frame, text="Base Font Size:").pack(anchor="w")
        fs_var = tk.IntVar(value=self.app_settings["font_size"])
        s = ttk.Scale(frame, from_=8, to=24, variable=fs_var, orient="horizontal")
        s.pack(fill="x", pady=10)
        
        theme_var = tk.StringVar(value=self.current_theme)
        ttk.Radiobutton(frame, text="Nord Dark", value="dark", variable=theme_var).pack(anchor="w")
        ttk.Radiobutton(frame, text="Nord Light", value="light", variable=theme_var).pack(anchor="w")
        
        ttk.Button(frame, text="Save & Restart", style="Primary.TButton", 
                   command=lambda: self._save_settings_logic(fs_var.get(), theme_var.get())).pack(pady=20)
        
        ttk.Separator(frame).pack(fill="x", pady=20)
        ttk.Button(frame, text="Reset Progress Data", command=self._reset_data_logic).pack()

    def _save_settings_logic(self, fs: int, theme: str) -> None:
        self.app_settings.update({"font_size": fs, "theme": theme})
        save_settings(self.app_settings)
        messagebox.showinfo("Restart", "Please restart the application to apply changes.")

    def _reset_data_logic(self) -> None:
        if messagebox.askyesno("Confirm", "Are you sure you want to delete all historical performance?"):
            reset_all_data()
            self._show_dashboard()

    # --- Notes ---
    def _show_notes(self, specific: Path = None) -> None:
        win = tk.Toplevel(self)
        win.title("Study Notes")
        win.geometry("800x600")
        win.configure(bg=self.palette["bg"])
        
        txt = ScrolledText(win, bg=self.palette["bg"], fg=self.palette["fg"], font=self.ui_font, padx=10, pady=10)
        txt.pack(fill="both", expand=True)
        
        if specific:
            content = specific.read_text(encoding="utf-8")
        else:
            parts = []
            for p in sorted(NOTES_DIR.glob("*.txt")):
                if p.name.endswith(".json"): continue
                parts.append(f"=== {p.name} ===\n{p.read_text()}\n")
            content = "\n".join(parts)
            
        txt.insert("1.0", content)
        txt.config(state="disabled")

def run_gui() -> None:
    app = QuizApp()
    app.mainloop()
