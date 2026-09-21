"""Streamlit web UI for the LangChain/LangGraph travel assistant."""
import asyncio
import json
import uuid
import streamlit as st
from agentscope.model import OpenAIChatModel
from config import LLM_CONFIG, SYSTEM_CONFIG
from config_agentscope import init_agentscope
from context.memory_manager import MemoryManager
from agents.intention_agent import IntentionAgent
from agents.orchestration_agent import OrchestrationAgent
from agents.lazy_agent_registry import LazyAgentRegistry
from langgraph_workflow import TravelWorkflow

def run(coro):
    return asyncio.run(coro)

@st.cache_resource(show_spinner=False)
def build_runtime(user_id):
    init_agentscope()
    model = OpenAIChatModel(model_name=LLM_CONFIG["model_name"], api_key=LLM_CONFIG["api_key"],
        client_kwargs={"base_url": LLM_CONFIG["base_url"], "timeout": float(SYSTEM_CONFIG.get("timeout", 60))},
        temperature=LLM_CONFIG.get("temperature", 0.7), max_tokens=LLM_CONFIG.get("max_tokens", 2000))
    memory = MemoryManager(user_id=user_id, session_id=str(uuid.uuid4())[:8], llm_model=model)
    intention = IntentionAgent(name="IntentionAgent", model=model)
    registry = LazyAgentRegistry(model=model, cache={}, memory_manager=memory)
    orchestrator = OrchestrationAgent(name="OrchestrationAgent", agent_registry=registry, memory_manager=memory)
    return memory, TravelWorkflow(intention, orchestrator)

def render_result(result):
    if hasattr(result, "content"):
        try: result = json.loads(result.content)
        except (TypeError, json.JSONDecodeError): st.write(result.content); return
    st.json(result) if isinstance(result, dict) else st.write(result)

st.set_page_config(page_title="差旅晓问", page_icon="✈️", layout="wide")
st.title("✈️ 差旅晓问")
st.caption("LangChain + LangGraph 旅行助手")
with st.sidebar:
    st.header("会话设置")
    user_id = st.text_input("用户 ID", value="default_user")
    if st.button("清空当前对话"):
        st.session_state.messages = []
        st.rerun()
    st.info("输入出差、行程、交通、住宿或知识库问题。")
if "messages" not in st.session_state: st.session_state.messages = []
if st.session_state.get("runtime_user") != user_id:
    with st.spinner("初始化助手..."):
        st.session_state.memory, st.session_state.workflow = build_runtime(user_id)
        st.session_state.runtime_user = user_id
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        render_result(message["content"]) if message.get("kind") == "result" else st.markdown(message["content"])
query = st.chat_input("例如：帮我规划下周上海到北京的出差行程")
if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"): st.markdown(query)
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            from agentscope.message import Msg
            recent = st.session_state.memory.short_term.get_recent_context(n_turns=5)
            context = [Msg(name=m["role"], content=m["content"], role=m["role"]) for m in recent]
            context.append(Msg(name="user", content=query, role="user"))
            state = run(st.session_state.workflow.ainvoke(context))
            if state.get("error"): st.error(state["error"])
            else:
                render_result(state.get("result"))
                st.session_state.messages.append({"role": "assistant", "kind": "result", "content": state.get("result")})
            st.session_state.memory.add_message("user", query)
