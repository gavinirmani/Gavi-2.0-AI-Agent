# 🚀 Gavi 2.0 - Personal Autonomous AI Agent

**Gavi 2.0** is an intelligent, versatile, and proactive personal AI assistant designed to streamline your daily workflow, boost productivity, manage tasks and notes, perform calculations, and adapt to your preferences.

Powered by Google's latest **Gemini API** (`gemini-3.8-flash` via the official `google-genai` SDK) and equipped with an autonomous tool-calling engine, persistent memory, and dual interfaces (Web Dashboard + Terminal CLI).

---

## ✨ Key Features

- **🧠 Advanced Intelligence**: Leverages Google Gemini (`gemini-3.8-flash`) with automatic tool-calling and continuous context memory.
- **📋 Personal Task Manager**: Create, prioritize, track, complete, and delete to-do tasks through natural conversation or directly from the UI.
- **📝 Notes Vault**: Quickly record thoughts, code snippets, meeting summaries, and search them anytime.
- **🕒 System & Time Awareness**: Instant access to your local time, date, platform metrics, and environment details.
- **🔢 Safe Mathematical Engine**: Evaluates numerical formulas, statistics, trigonometric operations, and conversions safely.
- **🌐 Dual Interaction Modes**:
  - **Modern Web Dashboard**: Sleek dark-mode interface with live task tracking, note-taking drawer, and markdown rendering.
  - **Terminal CLI**: Rich, colorful command-line experience with slash commands (`/tasks`, `/notes`, `/time`, `/help`).
- **🛡️ Smart Offline Mode**: Gavi 2.0 functions immediately out of the box even before you supply an API key by handling your tools locally!

---

## 📁 Project Structure

```
gavi_2_0/
├── agent/
│   ├── __init__.py
│   ├── core.py             # GaviAgent core orchestrator & prompt persona
│   ├── memory.py           # Persistent JSON memory for tasks, notes, user facts
│   └── tools.py            # Executable tools (tasks, notes, system info, math)
├── data/                   # Persistent local storage (auto-created)
│   ├── memory.json
│   ├── tasks.json
│   └── notes.json
├── static/                 # Web Dashboard frontend assets
│   ├── index.html          # Sleek chat UI with sidebar & widgets
│   ├── style.css           # Modern dark-mode styling
│   └── app.js              # Real-time UI controller
├── tests/
│   └── test_agent.py       # Unit and integration test suite
├── cli.py                  # Interactive Terminal CLI with rich formatting
├── server.py               # FastAPI backend for Web Dashboard
├── pyproject.toml          # Project configuration & dependencies
├── run.bat                 # 1-click Windows launcher
├── .env                    # Environment variables template
└── README.md               # Documentation
```

---

## ⚡ Quick Start

### 1. Configure Your Gemini API Key (Optional but Recommended)
Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```
Open `.env` and paste your Gemini API key:
```ini
GEMINI_API_KEY=AIzaSy...
```
*(You can get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey))*

### 2. Launch Gavi 2.0

#### Option A: 1-Click Launcher (Windows)
Double-click `run.bat` or run:
```bat
run.bat
```
Select **[1]** for the Web Dashboard or **[2]** for the CLI.

#### Option B: Web Dashboard directly
```bash
uv run python server.py
```
Then open your browser at **http://127.0.0.1:8000**

#### Option C: Interactive Terminal CLI
```bash
uv run python cli.py
```

---

## 💬 Example Interactions

Here are things you can say to Gavi 2.0:

### 📋 Managing Tasks
- *"Gavi, add a task to finish the presentation slides by 5 PM"*
- *"What tasks are on my list?"*
- *"Check off the presentation task"*

### 📝 Taking Notes
- *"Save note: Docker command to prune unused volumes is `docker volume prune`"*
- *"Show me my saved notes"*

### 🕒 System & Utility
- *"What time and day is it?"*
- *"Calculate (150 * 1.18) + 45"*
- *"Remember that my primary project is Project Apollo"*

---

## 🔧 Adding Custom Tools

Extending Gavi 2.0 with custom tools is straightforward. Open [`agent/tools.py`](file:///C:/Users/User/.gemini/antigravity/scratch/gavi_2_0/agent/tools.py) and add your function to `_register_default_tools`:

```python
def check_weather(city: str) -> dict:
    """Gets the weather forecast for a given city."""
    return {"city": city, "forecast": "Sunny, 24°C"}

self.register("check_weather", check_weather)
```
Gavi 2.0 will automatically expose this tool to Gemini and can invoke it during conversation!
