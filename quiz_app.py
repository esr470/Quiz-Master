"""
===================================================================
 Quiz Master - Timed Multiple-Choice Quiz Application
 Language : Python 3 (Tkinter - no external libraries required)
===================================================================
Features:
  - Category selection (General Knowledge, Science, Programming, Mixed)
  - Configurable number of questions and countdown timer per question
  - Live countdown bar; running out of time counts as a wrong answer
  - Animated progress bar across the quiz
  - Final results screen with a hand-drawn bar chart (correct vs
    wrong per category) - no external plotting library needed
  - Persistent leaderboard (saved to leaderboard.csv), top 5 shown
===================================================================
Run with:  python quiz_app.py
===================================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
import random
import csv
import os
import datetime

# ------------------------------------------------------------------
# Question bank
# ------------------------------------------------------------------
QUESTION_BANK = {
    "General Knowledge": [
        {"q": "What is the capital of Egypt?", "options": ["Cairo", "Alexandria", "Giza", "Luxor"], "answer": 0},
        {"q": "Which ocean is the largest on Earth?", "options": ["Atlantic", "Indian", "Arctic", "Pacific"], "answer": 3},
        {"q": "How many continents are there?", "options": ["5", "6", "7", "8"], "answer": 2},
        {"q": "Who painted the Mona Lisa?", "options": ["Van Gogh", "Da Vinci", "Picasso", "Monet"], "answer": 1},
        {"q": "What is the longest river in the world?", "options": ["Amazon", "Nile", "Yangtze", "Mississippi"], "answer": 1},
        {"q": "Which country hosted the 2022 FIFA World Cup?", "options": ["UAE", "Egypt", "Qatar", "Saudi Arabia"], "answer": 2},
    ],
    "Science": [
        {"q": "What gas do plants absorb from the atmosphere?", "options": ["Oxygen", "Nitrogen", "Carbon dioxide", "Hydrogen"], "answer": 2},
        {"q": "What is the chemical symbol for gold?", "options": ["Go", "Gd", "Au", "Ag"], "answer": 2},
        {"q": "How many bones are in the adult human body?", "options": ["186", "206", "226", "246"], "answer": 1},
        {"q": "What planet is known as the Red Planet?", "options": ["Venus", "Jupiter", "Mars", "Saturn"], "answer": 2},
        {"q": "What force pulls objects toward Earth?", "options": ["Magnetism", "Friction", "Gravity", "Tension"], "answer": 2},
        {"q": "What is the powerhouse of the cell?", "options": ["Nucleus", "Ribosome", "Mitochondria", "Golgi body"], "answer": 2},
    ],
    "Programming": [
        {"q": "Which symbol is used for comments in Python?", "options": ["//", "#", "<!-- -->", "--"], "answer": 1},
        {"q": "What does CRUD stand for in software development?", "options": [
            "Create, Read, Update, Delete", "Copy, Run, Undo, Debug",
            "Create, Run, Update, Deploy", "Compile, Read, Upload, Deploy"], "answer": 0},
        {"q": "Which data structure uses FIFO order?", "options": ["Stack", "Queue", "Tree", "Graph"], "answer": 1},
        {"q": "Which language is primarily used for Flutter apps?", "options": ["Kotlin", "Swift", "Dart", "Java"], "answer": 2},
        {"q": "What does SQL stand for?", "options": [
            "Structured Query Language", "Simple Query Logic",
            "Sequential Query Language", "Structured Question Language"], "answer": 0},
        {"q": "Which search algorithm is guaranteed optimal with admissible heuristics?", "options": [
            "DFS", "BFS", "A*", "Greedy Best-First"], "answer": 2},
    ],
}

TOTAL_CATEGORIES = list(QUESTION_BANK.keys()) + ["Mixed (All Categories)"]
LEADERBOARD_FILE = "leaderboard.csv"


# ------------------------------------------------------------------
# Quiz: pure logic, no GUI code -> easy to test independently
# ------------------------------------------------------------------
class Quiz:
    def __init__(self, category, num_questions, time_per_question):
        self.category = category
        self.time_per_question = time_per_question
        self.questions = self._pick_questions(category, num_questions)
        self.index = 0
        self.score = 0
        # per-category tally: {"Science": [correct, total], ...}
        self.breakdown = {}

    def _pick_questions(self, category, num_questions):
        if category == "Mixed (All Categories)":
            pool = []
            for cat, qs in QUESTION_BANK.items():
                for q in qs:
                    pool.append({**q, "category": cat})
        else:
            pool = [{**q, "category": category} for q in QUESTION_BANK[category]]

        num_questions = min(num_questions, len(pool))
        return random.sample(pool, num_questions)

    def current_question(self):
        if self.is_finished():
            return None
        return self.questions[self.index]

    def total(self):
        return len(self.questions)

    def is_finished(self):
        return self.index >= len(self.questions)

    def _record(self, cat, correct):
        stats = self.breakdown.setdefault(cat, [0, 0])
        stats[1] += 1
        if correct:
            stats[0] += 1

    def submit_answer(self, option_index):
        """Returns True if the chosen option is correct."""
        q = self.current_question()
        if q is None:
            raise RuntimeError("Quiz already finished.")
        correct = (option_index == q["answer"])
        if correct:
            self.score += 1
        self._record(q["category"], correct)
        self.index += 1
        return correct

    def time_up(self):
        """Call when the countdown reaches zero: counts as a wrong answer."""
        q = self.current_question()
        if q is None:
            return
        self._record(q["category"], False)
        self.index += 1

    def percentage(self):
        if self.total() == 0:
            return 0
        return round(100 * self.score / self.total(), 1)


# ------------------------------------------------------------------
# Leaderboard persistence (comma-delimited file, like the other
# CRUD projects in the portfolio)
# ------------------------------------------------------------------
def load_leaderboard():
    if not os.path.exists(LEADERBOARD_FILE):
        return []
    rows = []
    with open(LEADERBOARD_FILE, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) == 5:
                rows.append(row)
    return rows


def save_score(name, score, total, category, date_str):
    rows = load_leaderboard()
    rows.append([name, str(score), str(total), category, date_str])
    with open(LEADERBOARD_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)


def top_scores(n=5):
    rows = load_leaderboard()
    rows.sort(key=lambda r: int(r[1]) / max(int(r[2]), 1), reverse=True)
    return rows[:n]


# ------------------------------------------------------------------
# GUI
# ------------------------------------------------------------------
BG = "#0F172A"
CARD = "#1E293B"
ACCENT = "#38BDF8"
ACCENT_DARK = "#0EA5E9"
GOOD = "#22C55E"
BAD = "#EF4444"
TEXT = "#F1F5F9"
MUTED = "#94A3B8"


class QuizApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Quiz Master")
        self.geometry("760x560")
        self.configure(bg=BG)
        self.resizable(False, False)

        self.quiz = None
        self.timer_job = None
        self.time_left = 0
        self.selected_option = tk.IntVar(value=-1)

        self.container = tk.Frame(self, bg=BG)
        self.container.pack(fill="both", expand=True)

        self.show_start_screen()

    # ---------------- helpers ----------------
    def clear(self):
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None
        for widget in self.container.winfo_children():
            widget.destroy()

    def styled_button(self, parent, text, command, bg=ACCENT, fg="#0F172A"):
        return tk.Button(parent, text=text, command=command, bg=bg, fg=fg,
                         font=("Segoe UI", 12, "bold"), relief="flat",
                         activebackground=ACCENT_DARK, activeforeground="white",
                         padx=18, pady=8, cursor="hand2", bd=0)

    # ---------------- start screen ----------------
    def show_start_screen(self):
        self.clear()
        tk.Label(self.container, text="\U0001F3C6 Quiz Master", bg=BG, fg=TEXT,
                 font=("Segoe UI", 28, "bold")).pack(pady=(40, 5))
        tk.Label(self.container, text="Test your knowledge against the clock",
                 bg=BG, fg=MUTED, font=("Segoe UI", 12)).pack(pady=(0, 30))

        card = tk.Frame(self.container, bg=CARD, padx=30, pady=25)
        card.pack(pady=10)

        tk.Label(card, text="Your name", bg=CARD, fg=TEXT, font=("Segoe UI", 11, "bold")).grid(row=0, column=0, sticky="w", pady=6)
        self.name_entry = tk.Entry(card, font=("Segoe UI", 11), width=24)
        self.name_entry.grid(row=0, column=1, pady=6, padx=(10, 0))
        self.name_entry.insert(0, "Player")

        tk.Label(card, text="Category", bg=CARD, fg=TEXT, font=("Segoe UI", 11, "bold")).grid(row=1, column=0, sticky="w", pady=6)
        self.category_box = ttk.Combobox(card, values=TOTAL_CATEGORIES, state="readonly", width=22)
        self.category_box.current(len(TOTAL_CATEGORIES) - 1)
        self.category_box.grid(row=1, column=1, pady=6, padx=(10, 0))

        tk.Label(card, text="Number of questions", bg=CARD, fg=TEXT, font=("Segoe UI", 11, "bold")).grid(row=2, column=0, sticky="w", pady=6)
        self.num_q_box = ttk.Combobox(card, values=[5, 8, 10, 12, 15], state="readonly", width=22)
        self.num_q_box.current(2)
        self.num_q_box.grid(row=2, column=1, pady=6, padx=(10, 0))

        tk.Label(card, text="Seconds per question", bg=CARD, fg=TEXT, font=("Segoe UI", 11, "bold")).grid(row=3, column=0, sticky="w", pady=6)
        self.timer_box = ttk.Combobox(card, values=[10, 15, 20, 30], state="readonly", width=22)
        self.timer_box.current(1)
        self.timer_box.grid(row=3, column=1, pady=6, padx=(10, 0))

        self.styled_button(self.container, "Start Quiz \u25B6", self.start_quiz).pack(pady=25)

        leaders = top_scores(5)
        if leaders:
            board = tk.Frame(self.container, bg=BG)
            board.pack(pady=5)
            tk.Label(board, text="\U0001F31F Top Scores", bg=BG, fg=ACCENT,
                     font=("Segoe UI", 12, "bold")).pack()
            for i, row in enumerate(leaders, start=1):
                name, score, total, cat, date = row
                tk.Label(board, text=f"{i}. {name} \u2014 {score}/{total}  ({cat})",
                         bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack()

    def start_quiz(self):
        name = self.name_entry.get().strip() or "Player"
        self.player_name = name
        category = self.category_box.get()
        num_questions = int(self.num_q_box.get())
        time_per_q = int(self.timer_box.get())

        self.quiz = Quiz(category, num_questions, time_per_q)
        self.show_question()

    # ---------------- quiz screen ----------------
    def show_question(self):
        self.clear()
        q = self.quiz.current_question()
        if q is None:
            self.show_results()
            return

        top = tk.Frame(self.container, bg=BG)
        top.pack(fill="x", padx=30, pady=(20, 0))
        tk.Label(top, text=f"Question {self.quiz.index + 1} / {self.quiz.total()}",
                 bg=BG, fg=MUTED, font=("Segoe UI", 11, "bold")).pack(side="left")
        tk.Label(top, text=q["category"], bg=BG, fg=ACCENT,
                 font=("Segoe UI", 11, "bold")).pack(side="right")

        progress = ttk.Progressbar(self.container, length=680,
                                   maximum=self.quiz.total(), value=self.quiz.index)
        progress.pack(pady=12)

        self.timer_canvas = tk.Canvas(self.container, width=680, height=10, bg=CARD,
                                      highlightthickness=0)
        self.timer_canvas.pack(pady=(0, 20))
        self.timer_bar = self.timer_canvas.create_rectangle(0, 0, 680, 10, fill=GOOD, width=0)

        card = tk.Frame(self.container, bg=CARD, padx=25, pady=25)
        card.pack(fill="x", padx=30)
        tk.Label(card, text=q["q"], bg=CARD, fg=TEXT, font=("Segoe UI", 15, "bold"),
                 wraplength=620, justify="left").pack(anchor="w", pady=(0, 15))

        self.selected_option.set(-1)
        for idx, opt in enumerate(q["options"]):
            tk.Radiobutton(card, text=opt, variable=self.selected_option, value=idx,
                           bg=CARD, fg=TEXT, selectcolor=BG, font=("Segoe UI", 12),
                           activebackground=CARD, activeforeground=ACCENT,
                           anchor="w", padx=10, pady=6).pack(fill="x")

        self.styled_button(self.container, "Submit Answer \u2192", self.submit_answer).pack(pady=20)

        self.time_left = self.quiz.time_per_question
        self._tick()

    def _tick(self):
        total = self.quiz.time_per_question
        frac = self.time_left / total if total else 0
        self.timer_canvas.coords(self.timer_bar, 0, 0, 680 * frac, 10)
        color = GOOD if frac > 0.5 else ("#F59E0B" if frac > 0.2 else BAD)
        self.timer_canvas.itemconfig(self.timer_bar, fill=color)

        if self.time_left <= 0:
            self.quiz.time_up()
            self.show_question()
            return

        self.time_left -= 1
        self.timer_job = self.after(1000, self._tick)

    def submit_answer(self):
        choice = self.selected_option.get()
        if choice == -1:
            messagebox.showinfo("Quiz Master", "Please choose an answer first.")
            return
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None
        self.quiz.submit_answer(choice)
        self.show_question()

    # ---------------- results screen ----------------
    def show_results(self):
        self.clear()
        score = self.quiz.score
        total = self.quiz.total()
        pct = self.quiz.percentage()

        save_score(self.player_name, score, total, self.quiz.category,
                   datetime.date.today().isoformat())

        tk.Label(self.container, text="\U0001F3C1 Quiz Complete!", bg=BG, fg=TEXT,
                 font=("Segoe UI", 24, "bold")).pack(pady=(30, 5))
        tk.Label(self.container, text=f"{self.player_name}, you scored {score} / {total}  ({pct}%)",
                 bg=BG, fg=ACCENT, font=("Segoe UI", 14, "bold")).pack(pady=(0, 20))

        chart = tk.Canvas(self.container, width=680, height=220, bg=CARD, highlightthickness=0)
        chart.pack(padx=30, pady=10)
        self._draw_breakdown_chart(chart)

        btn_row = tk.Frame(self.container, bg=BG)
        btn_row.pack(pady=25)
        self.styled_button(btn_row, "Play Again", self.show_start_screen).pack(side="left", padx=8)
        self.styled_button(btn_row, "Quit", self.destroy, bg="#334155", fg=TEXT).pack(side="left", padx=8)

    def _draw_breakdown_chart(self, canvas):
        breakdown = self.quiz.breakdown
        if not breakdown:
            canvas.create_text(340, 110, text="No data", fill=MUTED, font=("Segoe UI", 12))
            return

        categories = list(breakdown.keys())
        n = len(categories)
        margin = 60
        bar_area_w = 680 - 2 * margin
        bar_w = min(70, bar_area_w / max(n, 1) - 30)
        gap = (bar_area_w - bar_w * n) / max(n, 1)
        base_y = 180
        max_h = 130

        canvas.create_line(margin - 10, base_y, 680 - margin + 10, base_y, fill=MUTED)

        x = margin
        for cat in categories:
            correct, total = breakdown[cat]
            frac = correct / total if total else 0
            h = max_h * frac
            x0, y0 = x, base_y - h
            x1, y1 = x + bar_w, base_y
            canvas.create_rectangle(x0, y0, x1, y1, fill=ACCENT, width=0)
            canvas.create_text((x0 + x1) / 2, y0 - 12, text=f"{correct}/{total}",
                               fill=TEXT, font=("Segoe UI", 10, "bold"))
            canvas.create_text((x0 + x1) / 2, base_y + 18, text=cat, fill=MUTED,
                               font=("Segoe UI", 9), width=bar_w + 40)
            x += bar_w + gap


if __name__ == "__main__":
    app = QuizApp()
    app.mainloop()
