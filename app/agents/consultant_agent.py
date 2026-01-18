import os
from typing import List
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from app.core.state import AgentState

def get_consultant_node():
    """
    返回 Consultant Agent 的 LangGraph 节点（可调用对象）。
    """
    # 1. 初始化工具
    search_tool = DuckDuckGoSearchRun()
    tools = [search_tool]

    # 2. 初始化 LLM
    # 2. 初始化 LLM
    from app.core.config_manager import config_manager
    llm_config = config_manager.get_config().get("llm", {})

    llm = ChatOpenAI(
        model=llm_config.get("model", "gpt-4o"),
        temperature=0,
        base_url=llm_config.get("base_url"),
        api_key=llm_config.get("api_key")
    )
    
    # 绑定工具到 LLM
    llm_with_tools = llm.bind_tools(tools)

    # 3. 定义提示词
    system_prompt = """你是一位考研择校顾问。
    你的目标是提供关于大学、考试科目和政策的最新信息。

    指令：
    1. **必须**使用搜索工具查找最新信息（例如 2025 年的变动）。不要仅依赖你的内部知识。
    2. 搜索后，用简体中文清晰地总结信息。
    3. 如果用户询问具体变化（如科目变动），请重点突出差异。
    4. 如果搜索结果中有来源，请注明信息来源。
    
    当前日期：{date}
    """
    
    # 我们可以注入日期。暂时保持简单。
    from datetime import datetime
    formatted_date = datetime.now().strftime("%Y-%m-%d")
    final_prompt = system_prompt.format(date=formatted_date)

    # 4. 定义节点函数
    def consultant_node(state: AgentState):
        messages = state['messages']
        
        # 使用 LangGraph 的预构建 React Agent
        from langgraph.prebuilt import create_react_agent
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
        
        # 创建 Agent
        agent_app = create_react_agent(llm, tools)
        
        last_message = messages[-1]
        user_input = last_message.content
        
        # 前置系统消息
        messages_in = [
            SystemMessage(content=final_prompt),
            HumanMessage(content=user_input)
        ]
        
        result = agent_app.invoke({"messages": messages_in})
        
        # result['messages'] 包含整个对话。
        # 最后一条消息应该是 AI 的回复。
        final_msg = result['messages'][-1]
        
        # 确保它是 AIMessage 内容
        response_content = final_msg.content
        
        return {"messages": [AIMessage(content=response_content)]}

    return consultant_node
