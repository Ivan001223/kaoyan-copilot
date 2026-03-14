import os
import re
import json
from datetime import datetime
from typing import List
from app.skills.common.search_tool import get_search_tool

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.runtime.graph.state import AgentState
from app.runtime.llm import get_llm
from langgraph.prebuilt import create_react_agent

def get_consultant_node():
    """
    返回 Consultant Agent 的 LangGraph 节点（可调用对象）。
    """
    search_tool = get_search_tool(return_results_obj=True)
    tools = [search_tool]

    llm = get_llm(temperature=0)

    try:
        llm_with_tools = llm.bind_tools(tools)
    except NotImplementedError:
        print("Warning: LLM does not support bind_tools. Running without tools.")
        llm_with_tools = llm
        tools = []

    system_prompt = """你是一位考研择校顾问。
    你的目标是提供关于大学、考试科目和政策的最新信息。

    指令：
    1. **必须**使用搜索工具查找最新信息（例如 2025 年的变动）。不要仅依赖你的内部知识。
    2. 搜索后，用简体中文清晰地总结信息。
    3. 如果用户询问具体变化（如科目变动），请重点突出差异。
    4. 如果搜索结果中有来源，请注明信息来源。

    当前日期：{date}
    """

    now = datetime.now()
    formatted_date = now.strftime("%Y-%m-%d")

    kaoyan_year = now.year + 1

    final_prompt = system_prompt.format(date=formatted_date)

    async def consultant_node(state: AgentState):
        messages = state['messages']

        web_search_enabled = state.get("web_search_enabled", False)

        active_tools = tools if web_search_enabled else []

        if web_search_enabled:
            current_prompt = f"""{final_prompt}

            重要提示：
            当前年份是 {now.year} 年。
            通常所说的"{kaoyan_year}考研"是指 {now.year} 年 12 月进行的初试，针对 {kaoyan_year} 年 9 月入学的研究生招生。
            用户如果询问"今年考研"或未指定年份，默认是指 **{kaoyan_year}考研**（即 {kaoyan_year} 届毕业生）。
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

        agent_app = create_react_agent(llm, active_tools)

        last_message = messages[-1]
        user_input = last_message.content

        messages_in = [
            SystemMessage(content=current_prompt),
            HumanMessage(content=user_input)
        ]

        try:
            result = await agent_app.ainvoke({"messages": messages_in})
        except Exception as e:
            print(f"Agent Execution Error: {e}")
            return {"messages": [AIMessage(content=f"抱歉，在执行任务时遇到了问题：{str(e)}。这可能是由于网络超时或搜索服务暂时不可用导致的。请稍后再试。")]}

        final_msg = result['messages'][-1]

        response_content = final_msg.content

        sources = []
        for msg in result['messages']:
            if hasattr(msg, 'type') and msg.type == 'tool':
                content = msg.content
                print(f"DEBUG: Tool Output: {content[:100]}...")

                try:
                    data = json.loads(content)
                    if isinstance(data, list) and len(data) > 0 and 'url' in data[0]:
                        for item in data:
                            sources.append({
                                "content": item.get('content', ''),
                                "title": item.get('title', 'Tavily Result'),
                                "url": item.get('url', '')
                            })
                        continue
                except:
                    pass

                items = re.split(r", snippet: ", content)
                for item in items:
                    txt = item
                    if not txt.startswith("snippet: "):
                        txt = "snippet: " + txt

                    link_match = re.search(r", link: (https?://.+)$", txt)
                    if not link_match:
                         link_match = re.search(r", link: (https?://\S+)", txt)

                    if link_match:
                        url = link_match.group(1).strip()
                        rest = txt[:link_match.start()]

                        title_split = rest.rsplit(", title: ", 1)
                        if len(title_split) == 2:
                            snippet = title_split[0].replace("snippet: ", "", 1).strip()
                            title = title_split[1].strip()

                            sources.append({
                                "content": snippet,
                                "title": title,
                                "url": url
                            })

        unique_sources = []
        seen_urls = set()
        for s in sources:
            if s["url"] not in seen_urls:
                unique_sources.append(s)
                seen_urls.add(s["url"])

        return {"messages": [AIMessage(content=response_content, additional_kwargs={"sources": unique_sources})]}

    return consultant_node
