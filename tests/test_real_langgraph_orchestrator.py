"""tests/test_real_langgraph_orchestrator.py — Verifies real tool execution and SQLite checkpoints in LangGraph."""
import pytest
from pathlib import Path
from core.agent_orchestrator import AgentOrchestrator, SQLiteCheckpointManager


@pytest.mark.asyncio
async def test_langgraph_real_tool_execution_and_checkpoints(tmp_path):
    ckpt_db = tmp_path / "test_checkpoints.db"
    orchestrator = AgentOrchestrator(checkpoint_db=ckpt_db)

    # 1. Test memory recall intent
    res = await orchestrator.execute_task("Please remember my favourite colour", thread_id="thread_test_01")
    assert res["status"] in ("success", "fallback")
    assert res["steps_count"] >= 1
    assert len(res["step_results"]) >= 1
    
    # Assert real tool was run (not placeholder text)
    tool_executed = res["step_results"][0]["tool"]
    assert tool_executed in ("recall_memory", "context_lookup")
    assert "Executed" not in res["step_results"][0].get("result", "")  # old fake string was "Executed recall_memory successfully"
    assert "Plan executed for" in res["final_response"] or "Processed:" in res["final_response"]

    # 2. Test SQLite Checkpointing
    ckpt_mgr = SQLiteCheckpointManager(ckpt_db)
    saved_state = ckpt_mgr.load_checkpoint("thread_test_01")
    assert saved_state is not None
    assert saved_state["goal"] == "Please remember my favourite colour"
    assert "step_results" in saved_state


@pytest.mark.asyncio
async def test_langgraph_notes_execution(tmp_path):
    ckpt_db = tmp_path / "test_checkpoints_notes.db"
    orchestrator = AgentOrchestrator(checkpoint_db=ckpt_db)

    res = await orchestrator.execute_task("save note buy milk and eggs", thread_id="thread_note_01")
    assert res["status"] in ("success", "fallback")
    tools = [s["tool"] for s in res["step_results"]]
    assert "notes" in tools
    
    # Check that the note was actually recorded
    note_result = [s for s in res["step_results"] if s["tool"] == "notes"][0]
    assert "Note saved" in note_result["result"]
