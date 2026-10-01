import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import agent


class ToolTests(unittest.TestCase):
    def test_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(agent, "WORKSPACE", Path(directory).resolve()):
            with self.assertRaises(ValueError):
                agent.safe_path("../secret")

    def test_list_and_read_file(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(agent, "WORKSPACE", Path(directory).resolve()):
            Path(directory, "hello.txt").write_text("hello", encoding="utf-8")
            self.assertEqual(agent.run_tool("list_files", {}), {"entries": ["hello.txt"]})
            self.assertEqual(agent.run_tool("read_file", {"path": "hello.txt"}), {"content": "hello"})

    def test_unknown_tool_is_an_error(self):
        self.assertIn("error", agent.run_tool("shell", {"command": "whoami"}))


if __name__ == "__main__":
    unittest.main()
