import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class MemoryManager:
    """Manages persistent memory, tasks, notes, and conversation logs for Gavi 2.0."""

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            base_path = Path(__file__).resolve().parent.parent
            self.data_dir = base_path / "data"
        else:
            self.data_dir = Path(data_dir)

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.memory_file = self.data_dir / "memory.json"
        self.tasks_file = self.data_dir / "tasks.json"
        self.notes_file = self.data_dir / "notes.json"

        self.profile: Dict[str, Any] = self._load_json(
            self.memory_file,
            default={
                "user_name": "User",
                "agent_name": "Gavi 2.0",
                "preferences": {},
                "custom_facts": [],
                "created_at": datetime.now().isoformat(),
            },
        )
        self.tasks: List[Dict[str, Any]] = self._load_json(self.tasks_file, default=[])
        self.notes: List[Dict[str, Any]] = self._load_json(self.notes_file, default=[])

    def _load_json(self, path: Path, default: Any) -> Any:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return default
        return default

    def _save_json(self, path: Path, data: Any) -> None:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[MemoryManager Warning] Failed to save {path.name}: {e}")

    # --- Profile & Facts ---
    def update_user_name(self, name: str) -> str:
        self.profile["user_name"] = name
        self._save_json(self.memory_file, self.profile)
        return f"User name updated to {name}."

    def add_fact(self, fact: str) -> str:
        if fact not in self.profile.setdefault("custom_facts", []):
            self.profile["custom_facts"].append(fact)
            self._save_json(self.memory_file, self.profile)
            return f"Remembered: '{fact}'"
        return "Fact already remembered."

    def get_context_summary(self) -> str:
        facts = self.profile.get("custom_facts", [])
        facts_str = "\n".join(f"- {f}" for f in facts) if facts else "None recorded yet."
        pending_tasks = [t for t in self.tasks if not t.get("completed", False)]
        return (
            f"User Name: {self.profile.get('user_name', 'User')}\n"
            f"Known Facts & Preferences:\n{facts_str}\n"
            f"Active Pending Tasks: {len(pending_tasks)}"
        )

    # --- Task Management ---
    def add_task(self, title: str, priority: str = "medium", due_date: Optional[str] = None) -> Dict[str, Any]:
        task = {
            "id": str(uuid.uuid4())[:8],
            "title": title,
            "priority": priority.lower(),
            "completed": False,
            "due_date": due_date,
            "created_at": datetime.now().isoformat(),
        }
        self.tasks.append(task)
        self._save_json(self.tasks_file, self.tasks)
        return task

    def list_tasks(self, include_completed: bool = False) -> List[Dict[str, Any]]:
        if include_completed:
            return self.tasks
        return [t for t in self.tasks if not t.get("completed", False)]

    def complete_task(self, task_id_or_keyword: str) -> Optional[Dict[str, Any]]:
        target = None
        for t in self.tasks:
            if t["id"] == task_id_or_keyword or task_id_or_keyword.lower() in t["title"].lower():
                t["completed"] = True
                t["completed_at"] = datetime.now().isoformat()
                target = t
                break
        if target:
            self._save_json(self.tasks_file, self.tasks)
        return target

    def delete_task(self, task_id: str) -> bool:
        initial_len = len(self.tasks)
        self.tasks = [t for t in self.tasks if t["id"] != task_id]
        if len(self.tasks) < initial_len:
            self._save_json(self.tasks_file, self.tasks)
            return True
        return False

    # --- Notes Management ---
    def add_note(self, title: str, content: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        note = {
            "id": str(uuid.uuid4())[:8],
            "title": title,
            "content": content,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
        }
        self.notes.append(note)
        self._save_json(self.notes_file, self.notes)
        return note

    def list_notes(self, search_query: Optional[str] = None) -> List[Dict[str, Any]]:
        if not search_query:
            return self.notes
        q = search_query.lower()
        return [
            n for n in self.notes
            if q in n["title"].lower() or q in n["content"].lower() or any(q in tag.lower() for tag in n.get("tags", []))
        ]

    def delete_note(self, note_id: str) -> bool:
        initial_len = len(self.notes)
        self.notes = [n for n in self.notes if n["id"] != note_id]
        if len(self.notes) < initial_len:
            self._save_json(self.notes_file, self.notes)
            return True
        return False
