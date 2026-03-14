import os
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.skills.common.search_tool import get_search_tool
from app.runtime.graph.state import AgentState
import datetime
import hashlib
import json
from app.infrastructure.config.settings import settings
from app.runtime.llm import get_llm
from langchain_core.messages import AIMessage

class AlertMessage(BaseModel):
    has_critical_update: bool = Field(description="如果存在重磅新闻（例如教学大纲更改、发布考试日期），则为 True。")
    message: str = Field(description="简洁的警报消息，例如：警告：浙大将考试科目更改为 408。")
    source_url: Optional[str] = Field(description="源 URL（如果可用）。")

def check_school_updates(school_name: str) -> AlertMessage:
    """
    检查目标学校研究生招生的最新更新。
    """
    search_tool = get_search_tool(return_results_obj=False)

    current_year = datetime.datetime.now().year
    target_year = current_year + 1

    queries = [
        f"{{school_name}} {target_year} 研究生招生简章",
        f"{{school_name}} {target_year} 考研 科目调整",
        f"{{school_name}} 考研 停招",
    ]

    combined_results = ""
    for q in queries:
        query_formatted = q.format(school_name=school_name)
        try:
            res = search_tool.invoke(query_formatted)
            combined_results += f"Query: {query_formatted}\nResult: {res}\n---\n"
        except Exception as e:
            print(f"Search error for {query_formatted}: {e}")

    if not combined_results:
        return AlertMessage(has_critical_update=False, message="未找到搜索结果。", source_url=None)

    llm_config = settings.llm

    llm = ChatOpenAI(
        model=llm_config.model,
        temperature=0,
        base_url=llm_config.base_url,
        api_key=llm_config.api_key,
        streaming=True
    )

    analyzer = llm.with_structured_output(AlertMessage)

    system_template = """你是一位考研情报分析师 (Intelligence Analyst)。
    分析提供的搜索片段，确定是否有关于 {target_year} 年入学的 {{school_name}} 的任何关键或突发新闻。

    关键事件 (设置 has_critical_update=True):
    1. 发布 {target_year} 招生简章。
    2. 考试科目变更（例如，从自命题改为 408）。
    3. 停止招生 (停招) 或名额大幅减少。
    4. 发布考试日期（如果以前未知）。

    忽略:
    - 旧闻 ({prev_year} 或更早)。
    - 一般废话或广告。
    - 没有可信度的谣言。

    输出语言：简体中文。
    如果是警报：消息以"⚠️ 警告:"或"📢 通告:"开头。
    如果【没有】关键更新，必须精确输出："目前未发现 {{school_name}} 的关键更新。"，不要包含其他变体或解释。
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_template.format(target_year=target_year, prev_year=target_year-1)),
        ("human", "Search Results:\n{results}")
    ])

    chain = prompt | analyzer

    try:
        alert = chain.invoke({"school_name": school_name, "results": combined_results})

        content_hash = hashlib.md5(alert.message.encode('utf-8')).hexdigest()

        history_file = "radar_history.json"
        history = {}
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except:
                history = {}

        last_hash = history.get(school_name)

        history[school_name] = content_hash
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save history: {e}")

        if last_hash == content_hash:
            return AlertMessage(has_critical_update=False, message=f"目前未发现 {school_name} 的新更新（内容与上次检查一致）。", source_url=alert.source_url)

        return alert
    except Exception as e:
        return AlertMessage(has_critical_update=False, message=f"分析失败: {e}")

class SchoolExtraction(BaseModel):
    """从用户输入中提取的学校名称。"""
    school_name: Optional[str] = Field(description="用户想要监控的目标学校名称")

def get_radar_node():
    llm = get_llm(temperature=0)

    extractor = llm.with_structured_output(SchoolExtraction)

    def radar_node(state: AgentState):
        messages = state['messages']
        last_content = messages[-1].content
        context = state.get("context", {})

        target_school = None

        try:
            extraction = extractor.invoke(f"Extract the university name from: {last_content}")
            if extraction and extraction.school_name:
                target_school = extraction.school_name
        except:
            pass

        if not target_school:
            target_school = context.get("monitored_school")

        if not target_school:
            target_school = "中国科学院大学杭州高等研究所"

        alert = check_school_updates(target_school)

        response_content = ""
        sources = []

        if alert.has_critical_update:
            response_content = f"【{target_school} 监控警报】\n{alert.message}"
            if alert.source_url:
                 sources.append({"title": "来源链接", "url": alert.source_url, "content": "监控到的更新来源"})
        else:
            response_content = f"目前未发现 {target_school} 的关键更新（招生简章/科目变更）。"

        return {
            "messages": [AIMessage(content=response_content, additional_kwargs={"sources": sources})],
            "context": {"monitored_school": target_school}
        }

    return radar_node
