# 🤖 AI-Generated Tool Disclaimer
**This entire application, including the code, and data structures, were created with the assistance of Artificial Intelligence.** I am using this tool for my personal study efficiency; please do not attribute the technical implementation or design to me.
# The code based its content on my own study notes and module Exams/Quizes/Reviews
---

# Network+ Study Suite (Nord-CompTIA Edition)
A modernized Python-based study application designed to help you prepare for the **CompTIA Network+ (N10-009)** certification. This suite uses a Nord-inspired aesthetic with official CompTIA color palettes and provides multiple interactive modes for efficient learning.

## 🚀 Key Features
*   **Practice Quiz**: Standard and Hard difficulty questions mapped directly to the 5 CompTIA Domains. Features include "Select TWO/THREE" multi-select formats, countdown timers, and "Flag for Review."
*   **Port Practice**: Dedicated bidirectional multiple-choice drills for all CompTIA-required protocols and ports, including a "Secure-Only" mode.
*   **Flashcard Mode**: A "Flip-card" interface for rapid Term-Definition memorization with persistent mastery tracking.
*   **Subnetting Challenge**: A procedural generator that creates random IPv4 subnetting problems (Mask, Network ID, Broadcast) with real-time text-entry validation.
*   **System Mastery Dashboard**: Persistent historical analytics showing your accuracy and question bank coverage per Domain.
*   **Modern GUI**: A responsive sidebar-based layout with Nord Light/Dark themes and dynamic font scaling.

## 🛠️ Installation & Run
### Requirements
*   Python 3.10+
*   `tkinter` (Usually bundled with Python; required for GUI)

### Launching the Suite
To open the graphical interface:
```bash
python3 main.py
```

### Terminal Fallback
If you are in a CLI-only environment or don't have Tkinter:
```bash
python3 main.py --cli
```

## 📂 Project Structure
*   `notes/`: The heart of the program. Contains:
    *   `questions.json`: The externalized question bank (175+ items).
    *   `flashcards.json`: Term-definition pairs for the flashcard module.
    *   `*.txt`: Topic-specific study notes referenced by the "Source Note" feature.
    *   `performance.json`: Your local historical quiz data.
*   `netplus_quiz/`:
    *   `models.py`: Dataclasses for Questions and Flashcards.
    *   `engine.py`: Logical engines for quiz sessions and subnet generation.
    *   `gui.py`: The modernized sidebar-based Tkinter interface.
    *   `quiz_bank.py`: Data loading and analytics logic.

## ⚙️ Customization
Use the **Settings** tab in the sidebar to:
*   Adjust **Base Font Size** for better readability.
*   Toggle between **Nord Dark** and **Nord Light** themes.
*   **Reset Progress Data**: Permanently clear your historical accuracy and flashcard mastery to start fresh.

## ✅ Verification
Run the unit tests to ensure the scoring and subnet logic are functioning correctly:
```bash
python3 -m unittest tests/test_quiz.py
```
