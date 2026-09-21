"""LangGraph workflow adapter for the travel assistant.

The domain agents remain reusable while the application flow is represented as
an explicit LangGraph state machine.  This keeps the migration incremental and
allows callers to invoke the complete flow with ``ainvoke``.
"""
from __future__ import annotations

import json
from typing import Any, Dict, TypedDict

from langgraph.graph import END, StateGraph
from langchain_core.runnables import RunnableLambda


class TravelState(TypedDict, total=False):
    messages: list[Any]
    intention: Any
    intention_data: Dict[str, Any]
    result: Any
    error: str


class TravelWorkflow:
    """Build and invoke the intention -> orchestration graph."""

    def __init__(self, intention_agent: Any, orchestrator: Any):
        self.intention_agent = intention_agent
        self.orchestrator = orchestrator
        graph = StateGraph(TravelState)
        graph.add_node("recognize_intention", self._recognize_intention)
        graph.add_node("orchestrate", self._orchestrate)
        graph.set_entry_point("recognize_intention")
        graph.add_edge("recognize_intention", "orchestrate")
        graph.add_edge("orchestrate", END)
        self.graph = graph.compile()
        # Expose the workflow as a standard LangChain Runnable as well.
        self.runnable = RunnableLambda(self.ainvoke)

    async def _recognize_intention(self, state: TravelState) -> TravelState:
        if state.get("intention") is not None:
            return state
        response = await self.intention_agent.reply(state.get("messages", []))
        try:
            data = json.loads(response.content)
        except (TypeError, json.JSONDecodeError) as exc:
            return {"intention": response, "error": f"Invalid intention format: {exc}"}
        return {"intention": response, "intention_data": data}

    async def _orchestrate(self, state: TravelState) -> TravelState:
        if state.get("error"):
            return state
        response = await self.orchestrator.reply(state["intention"])
        return {"result": response}

    async def ainvoke(self, messages: list[Any]) -> TravelState:
        return await self.graph.ainvoke({"messages": messages})

    async def ainvoke_from_intention(self, intention: Any) -> TravelState:
        """Continue the graph from an already validated intention response."""
        return await self.graph.ainvoke({"intention": intention})
