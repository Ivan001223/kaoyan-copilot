import os
import re
import json
from datetime import datetime
from typing import List
from app.core.tools.search_tool import get_search_tool

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.core.workflow.state import AgentState
from app.core.llm.llm_factory import get_llm
from langgraph.prebuilt import create_react_agent
def get_consultant_node():
    """
    返回 Consultant Agent 的 LangGraph 节点（可调用对象）。
    """
    # 1. 初始化工具
    # Consultant 需要详细的元数据（标题、链接），所以 return_results_obj=True (对 DDG)
    # Tavily 始终返回结构化数据
    search_tool = get_search_tool(return_results_obj=True)
    tools = [search_tool]

    # 2. 初始化 LLM
    # 2. 初始化 LLM
    llm = get_llm(temperature=0)
    
    # 绑定工具到 LLM
    try:
        llm_with_tools = llm.bind_tools(tools)
    except NotImplementedError:
        # Fallback for models that don't support tool binding (like LocalQwen2VL in some cases)
        print("Warning: LLM does not support bind_tools. Running without tools.")
        llm_with_tools = llm
        tools = [] # Disable tools effectively
    
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
    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d")
    
    # Calculate Kaoyan Year (Standard: Exam in Dec of Year X is for Year X+1 Admission, called "X+1 Kaoyan")
    # If we are in 2026, the next major exam is Dec 2026, which is "2027 Kaoyan".
    kaoyan_year = now.year + 1
    
    final_prompt = system_prompt.format(date=formatted_date)
    
    # 4. 定义节点函数
    async def consultant_node(state: AgentState):
        messages = state['messages']
        
        # 使用 LangGraph 的预构建 React Agent
        
        # 检查 MCP 服务配置
        web_search_enabled = state.get("web_search_enabled", False)
        
        active_tools = tools if web_search_enabled else []
        
        # 动态调整 Prompt
        if web_search_enabled:
            # Inject Kaoyan Year context for search
            current_prompt = f"""{final_prompt}
            
            重要提示：
            当前年份是 {now.year} 年。
            通常所说的“{kaoyan_year}考研”是指 {now.year} 年 12 月进行的初试，针对 {kaoyan_year} 年 9 月入学的研究生招生。
            用户如果询问“今年考研”或未指定年份，默认是指 **{kaoyan_year}考研**（即 {kaoyan_year} 届毕业生）。
            搜索时请务必关注 **{kaoyan_year} 年入学**（即 {now.year} 年发布）的最新招生简章和目录。
            
            格式要求：
            1. 在正文中引用链接时，必须使用 Markdown 格式：[标题](URL)。
            2. 不要直接粘贴裸露的 URL。
            3. **表格排版**：必须使用标准的 Markdown 表格语法。**每一行（包括表头、分隔线、数据行）末尾都必须有换行符**。严禁将多行表格内容压缩在同一行显示。
            """
        else:
            current_prompt = f"""你是一位考研择校顾问。
            你的目标是提供关于大学、考试科目和政策的信息。

            注意：**联网搜索功能目前已关闭**。
            
            指令：
            1. 请基于你已有的内部知识库回答用户问题。
            2. **明确告知用户**你无法访问实时互联网数据，因此无法提供最新的（如 {kaoyan_year} 年）具体变动信息。
            3. 建议用户开启联网搜索功能以获取更准确的最新资讯。
            4. 用简体中文回答。
            
            当前日期：{formatted_date}
            """

        # 创建 Agent
        # agent_app = create_react_agent(llm, active_tools) # Deprecated usage inside async function potentially
        
        # We should construct the graph explicitly or use the prebuilt one but ensuring we don't recreate it every time if possible.
        # But for now, let's just make sure we handle the execution correctly.
        # create_react_agent returns a CompiledGraph which supports ainvoke.
        agent_app = create_react_agent(llm, active_tools)
        
        last_message = messages[-1]
        user_input = last_message.content
        
        # 前置系统消息
        messages_in = [
            SystemMessage(content=current_prompt),
            HumanMessage(content=user_input)
        ]
        
        # 使用 ainvoke 进行异步调用
        try:
            result = await agent_app.ainvoke({"messages": messages_in})
        except Exception as e:
            # Catch exceptions like TimeoutException from tools
            print(f"Agent Execution Error: {e}")
            # Return a graceful error message instead of crashing
            return {"messages": [AIMessage(content=f"抱歉，在执行任务时遇到了问题：{str(e)}。这可能是由于网络超时或搜索服务暂时不可用导致的。请稍后再试。")]}
        
        # result['messages'] 包含整个对话。
        # 最后一条消息应该是 AI 的回复。
        final_msg = result['messages'][-1]
        
        # 确保它是 AIMessage 内容
        response_content = final_msg.content
        
        # 提取搜索来源
        sources = []
        for msg in result['messages']:
            if hasattr(msg, 'type') and msg.type == 'tool':
                # DuckDuckGoSearchResults 返回的格式通常是:
                # [snippet: ..., title: ..., link: ...], [snippet: ..., title: ..., link: ...]
                content = msg.content
                print(f"DEBUG: Tool Output: {content[:100]}...") # Debug log
                
                # Check if it is Tavily (JSON list) or DuckDuckGo (String)
                try:
                    # Tavily usually returns a list of dicts directly, but here it might be serialized to string in msg.content
                    # Let's try to parse as JSON first
                    data = json.loads(content)
                    if isinstance(data, list) and len(data) > 0 and 'url' in data[0]:
                        # It's likely Tavily
                        for item in data:
                            sources.append({
                                "content": item.get('content', ''),
                                "title": item.get('title', 'Tavily Result'),
                                "url": item.get('url', '')
                            })
                        continue # Skip DDG parsing
                except:
                    pass
                
                # 尝试解析 DuckDuckGo 搜索结果格式
                # 格式通常是: snippet: ..., title: ..., link: ..., snippet: ...
                # 我们使用 split 和 regex 组合来解析
                
                items = re.split(r", snippet: ", content)
                for item in items:
                    txt = item
                    if not txt.startswith("snippet: "):
                        txt = "snippet: " + txt
                    
                    # 提取 link (在末尾)
                    link_match = re.search(r", link: (https?://.+)$", txt)
                    if not link_match:
                         # 尝试非贪婪匹配，防止后面还有内容但没被 split 正确处理的情况
                         link_match = re.search(r", link: (https?://\S+)", txt)
                    
                    if link_match:
                        url = link_match.group(1).strip()
                        rest = txt[:link_match.start()]
                        
                        # 提取 title
                        title_split = rest.rsplit(", title: ", 1)
                        if len(title_split) == 2:
                            snippet = title_split[0].replace("snippet: ", "", 1).strip()
                            title = title_split[1].strip()
                            
                            sources.append({
                                "content": snippet,
                                "title": title,
                                "url": url
                            })
        
        # 去重 sources
        unique_sources = []
        seen_urls = set()
        for s in sources:
            if s["url"] not in seen_urls:
                unique_sources.append(s)
                seen_urls.add(s["url"])

        return {"messages": [AIMessage(content=response_content, additional_kwargs={"sources": unique_sources})]}

    return consultant_node
