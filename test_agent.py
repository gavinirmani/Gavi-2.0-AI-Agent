import unittest
import shutil
import tempfile
from pathlib import Path

from agent.memory import MemoryManager
from agent.tools import ToolRegistry
from agent.core import GaviAgent


class TestGaviAgent(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.memory = MemoryManager(data_dir=self.test_dir)
        self.tools = ToolRegistry(memory=self.memory)
        self.agent = GaviAgent(data_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_memory_tasks(self):
        task = self.memory.add_task("Prepare weekly summary", priority="high")
        self.assertEqual(task["title"], "Prepare weekly summary")
        self.assertFalse(task["completed"])

        active_tasks = self.memory.list_tasks()
        self.assertEqual(len(active_tasks), 1)

        completed = self.memory.complete_task(task["id"])
        self.assertIsNotNone(completed)
        self.assertTrue(completed["completed"])

        self.assertEqual(len(self.memory.list_tasks()), 0)

    def test_memory_notes(self):
        note = self.memory.add_note("Project Apollo", "Target launch in Q4", tags=["work"])
        self.assertEqual(note["title"], "Project Apollo")

        results = self.memory.list_notes(search_query="Apollo")
        self.assertEqual(len(results), 1)

    def test_tools_calculation(self):
        res = self.tools.execute("calculate", expression="sqrt(64) + 12 * 2")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["result"], 32.0)

    def test_agent_offline_interaction(self):
        # Test adding a task via agent natural language
        res = self.agent.ask("Add task: Send invoice to client")
        self.assertIn("invoice", res["response"].lower())

        # Test listing tasks
        res_list = self.agent.ask("List tasks")
        self.assertIn("invoice", res_list["response"].lower())

        # Test time query
        res_time = self.agent.ask("What time is it?")
        self.assertIn("currently", res_time["response"].lower())


if __name__ == "__main__":
    unittest.main()
