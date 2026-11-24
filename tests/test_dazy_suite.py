import sys
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import os
import sys
import unittest
from pathlib import Path

# Add DAZY root to path
DAZY_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(DAZY_DIR))


class TestDazyCoreSuite(unittest.TestCase):

    def test_01_proactive_monitoring_no_name_error(self):
        """Verify proactive monitoring handles psutil metrics without undefined variable or crashes."""
        from actions.proactive import ProactiveEngine
        engine = ProactiveEngine()
        self.assertIsNotNone(engine)
        prompt = engine.build_prompt(memory={}, monitors=["python"])
        self.assertIn("[PROACTIVE_CHECK]", prompt)

    def test_02_tts_indian_voice_synthesis(self):
        """Verify EdgeTTS synthesis with Indian female voice profile (en-IN-NeerjaNeural)."""
        import asyncio
        from core.tts import EdgeTTSEngine
        tts = EdgeTTSEngine(voice="en-IN-NeerjaNeural")
        audio = asyncio.run(tts._synth("Namaste Tarik"))
        self.assertIsInstance(audio, bytes)
        self.assertGreater(len(audio), 1000)

    def test_03_code_helper_sandbox_execution(self):
        """Verify code_helper runs in memory/sandbox when raw code is passed."""
        from actions.code_helper import code_helper
        res = code_helper(parameters={"action": "run", "code": "print('DAZY_SANDBOX_OK')"})
        self.assertIn("DAZY_SANDBOX_OK", str(res))

    def test_04_agent_task_queue_integration(self):
        """Verify Mark-XXXIX-OR agent task queue enqueues and processes tasks."""
        from agent.task_queue import TaskQueue, TaskPriority
        queue = TaskQueue()
        task_id = queue.submit(goal="Research Indian Voice Repositories", priority=TaskPriority.HIGH)
        self.assertIsNotNone(task_id)
        self.assertIn(task_id, queue._tasks)
        self.assertEqual(queue._tasks[task_id].goal, "Research Indian Voice Repositories")

    def test_05_agent_planner_integration(self):
        """Verify agent planner module decomposes complex requests with DAZY prompt."""
        from agent.planner import _fallback_plan, PLANNER_PROMPT
        self.assertIn("DAZY AI", PLANNER_PROMPT)
        plan = _fallback_plan("Search for top Indian TTS models")
        self.assertIn("steps", plan)
        self.assertGreater(len(plan["steps"]), 0)

    def test_06_dashboard_favicon_exists(self):
        """Verify favicon.ico exists and is non-empty."""
        fav = DAZY_DIR / "dashboard" / "static" / "favicon.ico"
        self.assertTrue(fav.exists())
        self.assertGreater(fav.stat().st_size, 1000)

    def test_07_prompt_identity_girlfriend_tarik(self):
        """Verify DAZY girlfriend persona and Tarik addressing rules."""
        prompt = (DAZY_DIR / "core" / "prompt.txt").read_text(encoding="utf-8")
        self.assertIn("DAZY", prompt)
        self.assertIn("Tarik", prompt)
        self.assertIn("ALWAYS LISTEN BEFORE SPEAKING", prompt)
        self.assertIn("NEVER TALK TO YOURSELF", prompt)

    def test_08_obscura_browser_resolution(self):
        """Verify Obscura stealth browser resolution in browser_control."""
        from actions.browser_control import _resolve_browser
        spec = _resolve_browser("obscura")
        self.assertIsNotNone(spec)
        self.assertEqual(spec["engine"], "obscura")

    def test_09_obscura_module_structure(self):
        """Verify Obscura module functions exist."""
        from core import obscura_browser
        self.assertTrue(hasattr(obscura_browser, "find_obscura_binary"))
        self.assertTrue(hasattr(obscura_browser, "is_obscura_available"))
        self.assertTrue(hasattr(obscura_browser, "fetch_text_or_markdown"))

    def test_10_agent_error_handler_companion(self):
        """Verify error_handler and executor do not use 'sir' or 'boss'."""
        eh_text = (DAZY_DIR / "agent" / "error_handler.py").read_text(encoding="utf-8")
        self.assertNotIn("sir", eh_text.lower())
        self.assertNotIn("boss", eh_text.lower())
        ex_text = (DAZY_DIR / "agent" / "executor.py").read_text(encoding="utf-8")
        self.assertNotIn("address the user as 'sir'", ex_text.lower())


if __name__ == "__main__":
    unittest.main()
