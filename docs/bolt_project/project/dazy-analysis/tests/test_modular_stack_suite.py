"""tests/test_modular_stack_suite.py — Regression tests for LangGraph, Qdrant, APScheduler & Agent Orchestrator.
"""
import pytest
import asyncio
from core.vector_memory import VectorMemory, _simple_text_embedding
from core.scheduler_service import SchedulerService
from core.agent_orchestrator import AgentOrchestrator, AgentAction, AgentPlan


def test_simple_text_embedding():
    v1 = _simple_text_embedding("hello world", dim=64)
    v2 = _simple_text_embedding("hello world", dim=64)
    v3 = _simple_text_embedding("different phrase", dim=64)

    assert len(v1) == 64
    assert v1 == v2
    assert v1 != v3
    # Check normalization
    norm = sum(x * x for x in v1) ** 0.5
    assert abs(norm - 1.0) < 1e-4


def test_vector_memory_store_and_search():
    vm = VectorMemory(storage_dir=None)  # In-memory Qdrant / fallback
    vm.store_memory("mem1", "My favorite programming language is Python", category="preferences")
    vm.store_memory("mem2", "The capital of France is Paris", category="facts")
    vm.store_memory("mem3", "Python is great for AI development", category="preferences")

    results = vm.search_memories("python coding", limit=2)
    assert len(results) > 0
    top = results[0]
    assert "Python" in top["text"]
    assert top["score"] > 0.0

    # Test category filtering
    fact_results = vm.search_memories("python", category="facts")
    for r in fact_results:
        assert r["category"] == "facts"


def test_scheduler_service_lifecycle():
    sched = SchedulerService()
    sched.start()

    dummy_ran = []
    def dummy_task():
        dummy_ran.append(True)

    added = sched.add_interval_job("job_1", dummy_task, seconds=10)
    assert added is True

    jobs = sched.list_jobs()
    job_ids = [j["id"] for j in jobs]
    assert "job_1" in job_ids

    removed = sched.remove_job("job_1")
    assert removed is True
    sched.shutdown()


@pytest.mark.asyncio
async def test_agent_orchestrator_langgraph():
    orch = AgentOrchestrator()
    res = await orch.execute_task("Find the latest tech news and summarize")

    assert res["status"] in ("success", "fallback")
    assert res["steps_count"] >= 1
    assert "Find the latest tech news" in res["goal"]
