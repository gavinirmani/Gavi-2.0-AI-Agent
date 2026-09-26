document.addEventListener("DOMContentLoaded", () => {
  const chatMessages = document.getElementById("chatMessages");
  const chatForm = document.getElementById("chatForm");
  const messageInput = document.getElementById("messageInput");
  const statusBadge = document.getElementById("statusBadge");
  const statusText = document.getElementById("statusText");
  const modelLabel = document.getElementById("modelLabel");
  const modeLabel = document.getElementById("modeLabel");
  const sidebar = document.getElementById("sidebar");
  const toggleSidebarBtn = document.getElementById("toggleSidebarBtn");

  const taskCountBadge = document.getElementById("taskCountBadge");
  const noteCountBadge = document.getElementById("noteCountBadge");
  const tasksList = document.getElementById("tasksList");
  const notesList = document.getElementById("notesList");
  const quickTaskForm = document.getElementById("quickTaskForm");
  const newTaskInput = document.getElementById("newTaskInput");
  const quickNoteForm = document.getElementById("quickNoteForm");

  // Tab switching
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      const targetPane = document.getElementById(btn.dataset.tab);
      if (targetPane) targetPane.classList.add("active");
    });
  });

  // Toggle sidebar
  toggleSidebarBtn.addEventListener("click", () => {
    sidebar.classList.toggle("hidden");
  });

  // Fetch status
  async function refreshStatus() {
    try {
      const res = await fetch("/api/status");
      if (!res.ok) throw new Error("Status check failed");
      const data = await res.json();

      if (data.live) {
        statusBadge.className = "status-badge status-online";
        statusText.textContent = "Online (Gemini)";
        modeLabel.textContent = "Gemini 3.8 Flash Live";
      } else {
        statusBadge.className = "status-badge status-offline";
        statusText.textContent = "Local Mode";
        modeLabel.textContent = "Offline (Local Tools)";
      }
      modelLabel.textContent = data.model || "gemini-3.8-flash";
    } catch (err) {
      statusBadge.className = "status-badge status-offline";
      statusText.textContent = "Disconnected";
    }
  }

  // Fetch and render Tasks
  async function loadTasks() {
    try {
      const res = await fetch("/api/tasks");
      const tasks = await res.json();
      taskCountBadge.textContent = tasks.filter((t) => !t.completed).length;

      if (!tasks || tasks.length === 0) {
        tasksList.innerHTML = `<div class="empty-state">No tasks yet.</div>`;
        return;
      }

      tasksList.innerHTML = tasks
        .map(
          (t) => `
        <div class="task-item ${t.completed ? "completed" : ""}" data-id="${t.id}">
          <div class="task-left">
            <input type="checkbox" ${t.completed ? "checked" : ""} class="task-check" data-id="${t.id}" />
            <span>${escapeHtml(t.title)}</span>
          </div>
          <button class="del-btn" data-id="${t.id}" title="Delete task">✕</button>
        </div>
      `
        )
        .join("");

      // Add event listeners for toggling and deleting
      document.querySelectorAll(".task-check").forEach((chk) => {
        chk.addEventListener("change", async (e) => {
          const id = e.target.dataset.id;
          await fetch(`/api/tasks/${id}/toggle`, { method: "PUT" });
          loadTasks();
        });
      });

      document.querySelectorAll(".task-item .del-btn").forEach((btn) => {
        btn.addEventListener("click", async (e) => {
          const id = e.target.dataset.id;
          await fetch(`/api/tasks/${id}`, { method: "DELETE" });
          loadTasks();
        });
      });
    } catch (e) {
      console.error("Failed to load tasks", e);
    }
  }

  // Fetch and render Notes
  async function loadNotes() {
    try {
      const res = await fetch("/api/notes");
      const notes = await res.json();
      noteCountBadge.textContent = notes.length;

      if (!notes || notes.length === 0) {
        notesList.innerHTML = `<div class="empty-state">No notes saved.</div>`;
        return;
      }

      notesList.innerHTML = notes
        .map(
          (n) => `
        <div class="note-card" data-id="${n.id}">
          <div style="display:flex; justify-content:space-between; align-items:flex-start;">
            <h5>${escapeHtml(n.title)}</h5>
            <button class="del-btn note-del-btn" data-id="${n.id}">✕</button>
          </div>
          <p>${escapeHtml(n.content)}</p>
        </div>
      `
        )
        .join("");

      document.querySelectorAll(".note-del-btn").forEach((btn) => {
        btn.addEventListener("click", async (e) => {
          const id = e.target.dataset.id;
          await fetch(`/api/notes/${id}`, { method: "DELETE" });
          loadNotes();
        });
      });
    } catch (e) {
      console.error("Failed to load notes", e);
    }
  }

  // Quick Task form submit
  quickTaskForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = newTaskInput.value.trim();
    if (!title) return;
    await fetch("/api/tasks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, priority: "medium" }),
    });
    newTaskInput.value = "";
    loadTasks();
  });

  // Quick Note form submit
  quickNoteForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("newNoteTitle").value.trim();
    const content = document.getElementById("newNoteContent").value.trim();
    if (!title || !content) return;
    await fetch("/api/notes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, content }),
    });
    document.getElementById("newNoteTitle").value = "";
    document.getElementById("newNoteContent").value = "";
    loadNotes();
  });

  // Append a chat message bubble
  function appendMessage(role, text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${role}-message`;
    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = role === "user" ? "You" : "G2";

    const content = document.createElement("div");
    content.className = "content";

    if (role === "assistant" && window.marked) {
      content.innerHTML = marked.parse(text);
    } else {
      content.textContent = text;
    }

    msgDiv.appendChild(avatar);
    msgDiv.appendChild(content);
    chatMessages.appendChild(msgDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return msgDiv;
  }

  // Send message
  async function sendMessage(text) {
    if (!text || !text.trim()) return;
    appendMessage("user", text);
    messageInput.value = "";
    messageInput.style.height = "auto";

    // Show temporary thinking bubble
    const thinkingBubble = appendMessage("assistant", "Thinking...");

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();
      thinkingBubble.remove();
      appendMessage("assistant", data.response);

      // Refresh tasks and notes in case tools were called
      loadTasks();
      loadNotes();
      refreshStatus();
    } catch (err) {
      thinkingBubble.remove();
      appendMessage("assistant", "⚠️ Error communicating with Gavi 2.0. Please check if the server is running.");
    }
  }

  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    sendMessage(messageInput.value);
  });

  // Enter to send, Shift+Enter for newline
  messageInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      chatForm.dispatchEvent(new Event("submit"));
    }
  });

  // Suggestion chips
  document.getElementById("quickChips").addEventListener("click", (e) => {
    const btn = e.target.closest(".chip");
    if (btn && btn.dataset.msg) {
      sendMessage(btn.dataset.msg);
    }
  });

  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Initial load
  refreshStatus();
  loadTasks();
  loadNotes();
});
