# AI Context & Operational Mandates

## ⚠️ MANDATORY PROTOCOL: "START"
- **Restriction**: You are FORBIDDEN from modifying, creating, or deleting any files/code unless the user prompt explicitly contains the token `START`.
- **Pre-Authorization**: In the absence of `START`, limit actions to:
    - Read-only research and codebase mapping.
    - Architectural analysis and logic tracing.
    - Asking clarifying questions.
- **Post-Authorization**: Once `START` is provided, follow standard Plan-Act-Validate cycles.

## 🏗️ System Architecture
- **Router**: `main.py` (CLI/GUI dispatch).
- **Models**: `netplus_quiz/models.py` (Dataclasses for `Question` and `Flashcard`).
- **Logic**: `netplus_quiz/engine.py` (State machines for `QuizSession`, `ReviewSession`, `SubnetEngine`).
- **Data**: `netplus_quiz/quiz_bank.py` (Persistence, `TOPIC_MAPPING` for category grouping).
- **UI**: `netplus_quiz/gui.py` (Tkinter/Standard Palette), `netplus_quiz/cli.py` (Terminal).
- **Storage**: `notes/` (JSON DBs: `questions.json`, `flashcards.json`, `performance.json`).

## 📊 Data Schemas
### Question Object
`{id, topic, prompt, choices, answer_indices, explanation, source_file, domain_id, difficulty}`

### Performance Tracking
`{question_id: {correct, total, consecutive_correct}}`
- **Weak Questions**: Identified via `consecutive_correct < 3`.

## 🛠️ Key Logic Patterns
- **Topic Grouping**: `quiz_bank.py` uses `TOPIC_MAPPING` to aggregate ~100+ topics into 9 study categories.
- **Mastery Review**: `ReviewSession` in `engine.py` implements a 3-streak requirement to "clear" missed questions.
- **Subnetting**: Procedural generation in `SubnetEngine` (Range: /16 to /30).

## 🎯 Optimization Notes
- To save tokens, avoid reading `notes/questions.json` in full; it is >370KB. Use `grep` for specific IDs or topics.
- Prioritize `engine.py` for logic changes and `gui.py` for visual updates.
