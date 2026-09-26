import math
import os
import platform
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from .memory import MemoryManager


class ToolRegistry:
    """Registry and dispatcher of executable tools for Gavi 2.0."""

    def __init__(self, memory: MemoryManager):
        self.memory = memory
        self._tools: Dict[str, Callable] = {}
        self._register_default_tools()

    def register(self, name: str, func: Callable):
        self._tools[name] = func

    def get_tool(self, name: str) -> Optional[Callable]:
        return self._tools.get(name)

    def execute(self, name: str, **kwargs) -> Any:
        func = self.get_tool(name)
        if not func:
            return {"error": f"Tool '{name}' not found."}
        try:
            return func(**kwargs)
        except Exception as e:
            return {"error": f"Error executing tool '{name}': {str(e)}"}

    def _register_default_tools(self):
        # 1. Tasks
        def add_task(title: str, priority: str = "medium", due_date: Optional[str] = None) -> Dict[str, Any]:
            """Adds a new to-do task to the personal task manager."""
            task = self.memory.add_task(title=title, priority=priority, due_date=due_date)
            return {"status": "success", "message": f"Added task '{title}' [ID: {task['id']}]", "task": task}

        def list_tasks(include_completed: bool = False) -> Dict[str, Any]:
            """Lists all tasks from the personal task manager."""
            tasks = self.memory.list_tasks(include_completed=include_completed)
            return {"status": "success", "count": len(tasks), "tasks": tasks}

        def complete_task(task_id_or_keyword: str) -> Dict[str, Any]:
            """Marks a task as completed using its ID or keyword match."""
            task = self.memory.complete_task(task_id_or_keyword)
            if task:
                return {"status": "success", "message": f"Marked task '{task['title']}' as completed.", "task": task}
            return {"status": "not_found", "message": f"No matching task found for '{task_id_or_keyword}'."}

        def delete_task(task_id: str) -> Dict[str, Any]:
            """Deletes a task by ID."""
            ok = self.memory.delete_task(task_id)
            if ok:
                return {"status": "success", "message": f"Task {task_id} deleted."}
            return {"status": "not_found", "message": f"Task {task_id} not found."}

        # 2. Notes
        def save_note(title: str, content: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
            """Saves a note to the personal notes vault."""
            note = self.memory.add_note(title=title, content=content, tags=tags)
            return {"status": "success", "message": f"Saved note '{title}' [ID: {note['id']}]", "note": note}

        def search_notes(query: Optional[str] = None) -> Dict[str, Any]:
            """Searches or lists notes in the vault."""
            notes = self.memory.list_notes(search_query=query)
            return {"status": "success", "count": len(notes), "notes": notes}

        # 3. System & Time
        def get_system_and_time() -> Dict[str, Any]:
            """Retrieves current system time, date, day of week, and OS environment."""
            now = datetime.now()
            return {
                "current_time": now.strftime("%I:%M:%S %p"),
                "current_date": now.strftime("%A, %B %d, %Y"),
                "iso_timestamp": now.isoformat(),
                "os": platform.system(),
                "os_release": platform.release(),
                "python_version": platform.python_version(),
            }

        # 4. Memory / User facts
        def remember_user_fact(fact: str) -> Dict[str, Any]:
            """Stores a personal detail or preference about the user into long-term memory."""
            res = self.memory.add_fact(fact)
            return {"status": "success", "message": res}

        # 5. Safe Math Calculator
        def calculate(expression: str) -> Dict[str, Any]:
            """Safely computes a mathematical expression (e.g., '128 * 4.5', 'sqrt(144) + 10')."""
            allowed_names = {
                k: v for k, v in math.__dict__.items() if not k.startswith("__")
            }
            allowed_names.update({"abs": abs, "round": round, "min": min, "max": max, "sum": sum})
            try:
                # Compile in eval mode and restrict globals/locals
                code = compile(expression, "<calculator>", "eval")
                for name in code.co_names:
                    if name not in allowed_names:
                        return {"status": "error", "message": f"Name '{name}' is not allowed in math evaluation."}
                result = eval(code, {"__builtins__": {}}, allowed_names)
                return {"status": "success", "expression": expression, "result": result}
            except Exception as e:
                return {"status": "error", "message": f"Calculation error: {str(e)}"}

        self.register("add_task", add_task)
        self.register("list_tasks", list_tasks)
        self.register("complete_task", complete_task)
        self.register("delete_task", delete_task)
        self.register("save_note", save_note)
        self.register("search_notes", search_notes)
        self.register("get_system_and_time", get_system_and_time)
        self.register("remember_user_fact", remember_user_fact)
        self.register("calculate", calculate)

    def get_tool_functions(self) -> List[Callable]:
        return list(self._tools.values())
