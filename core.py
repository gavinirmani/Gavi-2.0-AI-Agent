import os
import re
from typing import Any, Callable, Dict, List, Optional
from dotenv import load_dotenv

from .memory import MemoryManager
from .tools import ToolRegistry

load_dotenv()

GAVI_SYSTEM_INSTRUCTION = """You are Gavi 2.0, an intelligent, versatile, proactive personal AI agent and companion.
Your mission is to assist the user with daily productivity, organization, learning, analysis, and problem solving.

Key Behaviors:
1. Persona: Sharp, encouraging, direct, and warm. You speak as a capable personal partner named Gavi 2.0.
2. Tools: You have access to tools for:
   - Managing tasks (add_task, list_tasks, complete_task, delete_task)
   - Keeping notes (save_note, search_notes)
   - Checking local system time and environment (get_system_and_time)
   - Remembering personal preferences and facts (remember_user_fact)
   - Performing math calculations (calculate)
3. Proactivity: Whenever the user mentions something they need to do, offer to add it or add it to their tasks. When they share an important piece of info, save it or remember it.
4. Formatting: Keep responses neatly structured with bullet points and bold highlights when appropriate.
"""


class GaviAgent:
    """Core Gavi 2.0 Agent orchestrator."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        data_dir: Optional[str] = None,
    ):
        self.memory = MemoryManager(data_dir=data_dir)
        self.tools = ToolRegistry(memory=self.memory)

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

        self.client = None
        self.chat_session = None
        self.is_live = False

        self._init_gemini_client()

    def _init_gemini_client(self):
        if not self.api_key or self.api_key.strip() in ("", "your_gemini_api_key_here"):
            self.is_live = False
            return

        try:
            from google import genai
            from google.genai import types

            self.client = genai.Client(api_key=self.api_key)

            # System prompt with persistent context
            context_summary = self.memory.get_context_summary()
            full_system_instruction = f"{GAVI_SYSTEM_INSTRUCTION}\n\nCurrent User Context:\n{context_summary}"

            # Provide tool functions directly for automatic function calling
            tool_funcs = self.tools.get_tool_functions()
            config = types.GenerateContentConfig(
                system_instruction=full_system_instruction,
                tools=tool_funcs,
                temperature=0.7,
            )

            self.chat_session = self.client.chats.create(
                model=self.model_name,
                config=config,
            )
            self.is_live = True
        except Exception as e:
            print(f"[Gavi 2.0 Warning] Could not initialize live Gemini API ({e}). Running in smart offline mode.")
            self.is_live = False

    def ask(self, user_message: str) -> Dict[str, Any]:
        """Processes a user message and returns Gavi's response and any tool actions."""
        if not user_message or not user_message.strip():
            return {
                "response": "Hello! I'm Gavi 2.0. How can I assist you today?",
                "tools_used": [],
                "live": self.is_live,
            }

        # If live API is connected, call Gemini chat session
        if self.is_live and self.chat_session:
            try:
                response = self.chat_session.send_message(user_message)
                return {
                    "response": response.text if response.text else "Done.",
                    "tools_used": [],
                    "live": True,
                }
            except Exception as e:
                # Fallback to smart offline handler if API rate limit or network issue occurs
                offline_res = self._offline_fallback_handler(user_message)
                return {
                    "response": f"[API note: {str(e)}]\n\n{offline_res['response']}",
                    "tools_used": offline_res.get("tools_used", []),
                    "live": False,
                }

        # Smart offline fallback mode: handles intent and tools natively
        return self._offline_fallback_handler(user_message)

    def _offline_fallback_handler(self, msg: str) -> Dict[str, Any]:
        """Provides full local tool execution and persona responses when no API key is supplied."""
        lower = msg.lower().strip()
        tools_used = []

        # 1. System time / date
        if any(w in lower for w in ["what time", "current time", "what date", "today's date", "what day"]):
            res = self.tools.execute("get_system_and_time")
            tools_used.append({"tool": "get_system_and_time", "result": res})
            return {
                "response": f"🕒 It is currently **{res['current_time']}** on **{res['current_date']}**.",
                "tools_used": tools_used,
                "live": False,
            }

        # 2. Add task
        add_task_match = re.search(r"(?:add task:?|remind me to:?|create task:?|todo:?)\s*(.+)", msg, re.IGNORECASE)
        if add_task_match:
            task_title = add_task_match.group(1).strip()
            res = self.tools.execute("add_task", title=task_title)
            tools_used.append({"tool": "add_task", "result": res})
            return {
                "response": f"✅ Got it! I've added **\"{task_title}\"** to your task list [ID: {res['task']['id']}].",
                "tools_used": tools_used,
                "live": False,
            }

        # 3. List tasks
        if any(w in lower for w in ["list tasks", "my tasks", "show tasks", "todo list", "what are my tasks"]):
            res = self.tools.execute("list_tasks", include_completed=False)
            tools_used.append({"tool": "list_tasks", "result": res})
            tasks = res.get("tasks", [])
            if not tasks:
                return {
                    "response": "📋 Your task list is clear! You have no pending tasks.",
                    "tools_used": tools_used,
                    "live": False,
                }
            lines = [f"- **[{t['id']}]** {t['title']} (Priority: {t['priority']})" for t in tasks]
            return {
                "response": f"📋 **Your Active Tasks ({len(tasks)}):**\n" + "\n".join(lines),
                "tools_used": tools_used,
                "live": False,
            }

        # 4. Complete task
        comp_match = re.search(r"(?:complete task:?|finish task:?|done with:?|check off:?)\s*([a-zA-Z0-9_\-\s]+)", msg, re.IGNORECASE)
        if comp_match:
            target = comp_match.group(1).strip()
            res = self.tools.execute("complete_task", task_id_or_keyword=target)
            tools_used.append({"tool": "complete_task", "result": res})
            if res.get("status") == "success":
                return {
                    "response": f"🎉 Excellent! I've marked **\"{res['task']['title']}\"** as completed.",
                    "tools_used": tools_used,
                    "live": False,
                }
            return {
                "response": f"⚠️ Could not find an active task matching \"{target}\".",
                "tools_used": tools_used,
                "live": False,
            }

        # 5. Notes
        save_note_match = re.search(r"(?:save note|take note|write note):?\s*(.+)", msg, re.IGNORECASE)
        if save_note_match:
            content = save_note_match.group(1).strip()
            title = content.splitlines()[0][:30] + ("..." if len(content.splitlines()[0]) > 30 else "")
            res = self.tools.execute("save_note", title=title, content=content)
            tools_used.append({"tool": "save_note", "result": res})
            return {
                "response": f"📝 Note saved: **\"{title}\"** [ID: {res['note']['id']}].",
                "tools_used": tools_used,
                "live": False,
            }

        if any(w in lower for w in ["list notes", "show notes", "my notes", "search notes"]):
            res = self.tools.execute("search_notes")
            tools_used.append({"tool": "search_notes", "result": res})
            notes = res.get("notes", [])
            if not notes:
                return {
                    "response": "📓 Your notes vault is empty right now.",
                    "tools_used": tools_used,
                    "live": False,
                }
            lines = [f"- **[{n['id']}] {n['title']}**: {n['content'][:50]}..." for n in notes]
            return {
                "response": f"📓 **Your Notes ({len(notes)}):**\n" + "\n".join(lines),
                "tools_used": tools_used,
                "live": False,
            }

        # 6. Math calculations
        calc_match = re.search(r"(?:calculate|eval|compute|what is)\s+([0-9\.\s\+\-\*\/\(\)\^\%sqrtlogpi]+)\??$", msg, re.IGNORECASE)
        if calc_match:
            expr = calc_match.group(1).strip()
            res = self.tools.execute("calculate", expression=expr)
            tools_used.append({"tool": "calculate", "result": res})
            if res.get("status") == "success":
                return {
                    "response": f"🔢 **{expr}** = **{res['result']}**",
                    "tools_used": tools_used,
                    "live": False,
                }

        # 7. Remember fact
        remember_match = re.search(r"(?:remember that|remember:|my name is)\s+(.+)", msg, re.IGNORECASE)
        if remember_match:
            fact = remember_match.group(1).strip()
            res = self.tools.execute("remember_user_fact", fact=fact)
            tools_used.append({"tool": "remember_user_fact", "result": res})
            return {
                "response": f"🧠 Understood. I've committed this to memory: *\"{fact}\"*.",
                "tools_used": tools_used,
                "live": False,
            }

        # General friendly fallback with instructions
        return {
            "response": (
                "👋 **I am Gavi 2.0**, your personal AI companion!\n\n"
                "I'm currently running in **Local Mode** because no `GEMINI_API_KEY` was found in your `.env` file.\n\n"
                "Even without an API key, you can use my personal tools right now:\n"
                "- 📋 **Tasks**: `add task Buy groceries`, `list tasks`, `complete task <id>`\n"
                "- 📝 **Notes**: `save note Meeting notes: follow up on Friday`, `list notes`\n"
                "- 🕒 **System & Time**: `what time is it?`, `what date is today?`\n"
                "- 🔢 **Math**: `calculate 25 * 14 + 180`\n"
                "- 🧠 **Memory**: `remember that my favorite programming language is Python`\n\n"
                "💡 *To unlock full Gemini 3.8 Flash intelligence and open-ended conversation, set your `GEMINI_API_KEY` in `.env` and restart!*"
            ),
            "tools_used": [],
            "live": False,
        }
