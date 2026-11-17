import pytest


@pytest.fixture(autouse=True)
def _no_plan_llm(monkeypatch):
    """Tests never call the local Qwen; tests of plan_llm switch it on themselves."""
    monkeypatch.setenv("PLAN_LLM", "off")
