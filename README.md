THIS PROJECT IS COMPLETELY AI GENERATED
MEANT TO MAKE PERSONAL STUDYING MORE EFFICIENT
# Net-Practice
Notes and Python Project to practice for CompTIA Network+
=======
# Network+ Quiz

Small Python quiz app built from the corrected note files in this directory.
The question bank now includes both `standard` and `hard` questions.

## Run

Terminal UI:

```bash
python3 main.py --cli
python3 main.py --ports
python3 main.py --secure-ports
```

GUI:

```bash
python3 main.py
```

If `tkinter` is not installed, the launcher automatically falls back to the terminal UI.

## Verify

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile main.py netplus_quiz/*.py tests/test_quiz.py
```

## Structure

- `main.py`: launcher and GUI-to-CLI fallback logic.
- `netplus_quiz/models.py`: core data model for quiz questions.
- `netplus_quiz/engine.py`: quiz session and scoring logic.
- `netplus_quiz/quiz_bank.py`: structured question bank tied to the source note files.
- `netplus_quiz/gui.py`: Tkinter interface.
- `netplus_quiz/cli.py`: terminal fallback interface.
- `tests/test_quiz.py`: smoke tests for the quiz bank and engine.

The GUI lets you filter by topic and difficulty before starting a quiz, and it now includes dedicated buttons for CompTIA protocols and ports practice plus secure-ports-only drilling.
During a GUI quiz, use the `A+` button to increase font size and `Exit Test` to return to the menu after confirmation.

## Upgrade Path

To add more content later:

1. Correct or expand the `.txt` source notes.
2. Add new `Question(...)` entries in `netplus_quiz/quiz_bank.py`.
3. Re-run the tests.

To change the interface later:

- Keep quiz logic in `engine.py`.
- Replace or extend only the UI modules.
>>>>>>> ca7f4ba (Initial Commit)
