import unittest
from fastapi.testclient import TestClient
from server import app


class TestGaviServer(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_status_endpoint(self):
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "Gavi 2.0")
        self.assertIn("active_tasks_count", data)

    def test_tasks_crud(self):
        # Create
        res = self.client.post("/api/tasks", json={"title": "Test Task 1", "priority": "high"})
        self.assertEqual(res.status_code, 200)
        task = res.json()
        task_id = task["id"]
        self.assertEqual(task["title"], "Test Task 1")

        # List
        res_list = self.client.get("/api/tasks")
        self.assertEqual(res_list.status_code, 200)
        items = res_list.json()
        self.assertTrue(any(t["id"] == task_id for t in items))

        # Toggle
        res_toggle = self.client.put(f"/api/tasks/{task_id}/toggle")
        self.assertEqual(res_toggle.status_code, 200)
        self.assertTrue(res_toggle.json()["completed"])

        # Delete
        res_del = self.client.delete(f"/api/tasks/{task_id}")
        self.assertEqual(res_del.status_code, 200)

    def test_notes_crud(self):
        # Create note
        res = self.client.post("/api/notes", json={"title": "Note 1", "content": "Important note content"})
        self.assertEqual(res.status_code, 200)
        note = res.json()
        note_id = note["id"]

        # List notes
        res_list = self.client.get("/api/notes")
        self.assertEqual(res_list.status_code, 200)
        self.assertTrue(any(n["id"] == note_id for n in res_list.json()))

        # Delete note
        res_del = self.client.delete(f"/api/notes/{note_id}")
        self.assertEqual(res_del.status_code, 200)

    def test_chat_endpoint(self):
        res = self.client.post("/api/chat", json={"message": "What time is it?"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("response", data)


if __name__ == "__main__":
    unittest.main()
