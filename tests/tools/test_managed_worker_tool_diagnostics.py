"""In a managed worker (every Kanban card) ``delegate_task`` works through owner-reserved children
(#141793), so asking for it in a turn whose toolsets leave delegation off gets the ordinary
"not available in this execution context" answer: never "call it directly", and never a claim that
the worker boundary itself forbids delegation."""
import json

import pytest

import tools.delegate_tool  # registers delegate_task in the global registry
from agent import runtime_session_store
from agent.conversation_loop import _invalid_tool_name_error_content
from tools.tool_search import ToolSearchConfig, dispatch_tool_describe, resolve_underlying_call


@pytest.mark.parametrize("worker", [True, False])
def test_delegate_task_absent_from_a_turn_is_reported_as_unavailable(monkeypatch, worker):
    monkeypatch.setattr(runtime_session_store, "_worker_process", worker)
    turn_tools = [{"type": "function", "function": {"name": "kanban_create", "parameters": {}}}]
    _, _, call_err = resolve_underlying_call({"calls": [{"name": "delegate_task", "arguments": {}}]},
                                             {"kanban_create"})
    described = json.loads(dispatch_tool_describe({"names": ["delegate_task"]}, current_tool_defs=turn_tools,
                                                  config=ToolSearchConfig.from_raw({})))
    for message in (call_err or "", described["errors"]["delegate_task"]):
        assert "not available in this execution context" in message, message
        assert "Call it directly" not in message and "managed worker" not in message, message
    assert "managed worker" not in _invalid_tool_name_error_content("delegate_task", ["kanban_create"])


def test_a_turn_that_has_delegate_task_keeps_the_ordinary_guidance(monkeypatch):
    monkeypatch.setattr(runtime_session_store, "_worker_process", True)
    _, _, err = resolve_underlying_call({"calls": [{"name": "delegate_task", "arguments": {}}]},
                                        {"delegate_task"})
    assert "Call it directly" in (err or "")
