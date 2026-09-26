import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from agent.core import GaviAgent

app = FastAPI(title="Gavi 2.0 Web Dashboard", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Initialize global agent instance
agent = GaviAgent()


class ChatRequest(BaseModel):
    message: str


class TaskCreate(BaseModel):
    title: str
    priority: str = "medium"
    due_date: Optional[str] = None


class NoteCreate(BaseModel):
    title: str
    content: str
    tags: Optional[List[str]] = None


@app.get("/")
def get_index():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="UI index.html not found.")
    return FileResponse(str(index_file))


@app.get("/api/status")
def get_status():
    tasks = agent.memory.list_tasks(include_completed=False)
    notes = agent.memory.list_notes()
    return {
        "name": "Gavi 2.0",
        "live": agent.is_live,
        "model": agent.model_name,
        "active_tasks_count": len(tasks),
        "notes_count": len(notes),
        "user_name": agent.memory.profile.get("user_name", "User"),
    }


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    result = agent.ask(req.message)
    return result


@app.get("/api/tasks")
def list_tasks():
    return agent.memory.list_tasks(include_completed=True)


@app.post("/api/tasks")
def create_task(req: TaskCreate):
    task = agent.memory.add_task(title=req.title, priority=req.priority, due_date=req.due_date)
    return task


@app.put("/api/tasks/{task_id}/toggle")
def toggle_task(task_id: str):
    task = agent.memory.complete_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    ok = agent.memory.delete_task(task_id)
    return {"success": ok}


@app.get("/api/notes")
def list_notes(q: Optional[str] = None):
    return agent.memory.list_notes(search_query=q)


@app.post("/api/notes")
def create_note(req: NoteCreate):
    note = agent.memory.add_note(title=req.title, content=req.content, tags=req.tags)
    return note


@app.delete("/api/notes/{note_id}")
def delete_note(note_id: str):
    ok = agent.memory.delete_note(note_id)
    return {"success": ok}


def run():
    host = os.getenv("GAVI_HOST", "127.0.0.1")
    port = int(os.getenv("GAVI_PORT", 8000))
    print(f"🚀 Starting Gavi 2.0 Web Server on http://{host}:{port}")
    uvicorn.run("server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    run()
