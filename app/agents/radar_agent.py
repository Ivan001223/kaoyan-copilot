import os
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools import DuckDuckGoSearchRun
from app.core.state import AgentState

# 1. 警报数据模型
class AlertMessage(BaseModel):
    has_critical_update: bool = Field(description="如果存在重磅新闻（例如教学大纲更改、发布考试日期），则为 True。")
    message: str = Field(description="简洁的警报消息，例如“警告：浙大将考试科目更改为 408”。")
    source_url: Optional[str] = Field(description="源 URL（如果可用）。")
    
# 2. 搜索逻辑
def check_school_updates(school_name: str) -> AlertMessage:
    """
    检查目标学校研究生招生的最新更新。
    """
    search_tool = DuckDuckGoSearchRun()
    
    # 计算目标年份（例如，如果今天是 2026-01-14，目标是 2027 年入学）
    # 但是，如果是 2026 年初/中期，人们可能仍在检查 2026 年的成绩或 2027 年的指南。
    # 通常“考研 202X”表示考试年份是 202X-1。
    # 2026 年入学（2025 年 12 月考试）。2027 年入学（2026 年 12 月考试）。
    # 如果今天是 2026 年 1 月，2026 年的考试已经结束。我们寻找 2027 年的指南（稍后发布）或 2026 年的调整。
    import datetime
    current_year = datetime.datetime.now().year
    # 如果我们在 1 月到 8 月，我们可能正在查看 current_year+1（下一个周期）。
    # 如果我们在 9 月到 12 月，我们肯定是在看 current_year+1。
    target_year = current_year + 1
    
    # 构建有针对性的查询
    queries = [
        f"{{school_name}} {target_year} 研究生招生简章",
        f"{{school_name}} {target_year} 考研 科目调整",
        f"{{school_name}} 考研 停招",
    ]
    
    combined_results = ""
    for q in queries:
        query_formatted = q.format(school_name=school_name)
        try:
            # 我们在搜索结果中添加一些上下文
            res = search_tool.invoke(query_formatted)
            combined_results += f"Query: {query_formatted}\nResult: {res}\n---\n"
        except Exception as e:
            print(f"Search error for {query_formatted}: {e}")
            
    if not combined_results:
        return AlertMessage(has_critical_update=False, message="未找到搜索结果。", source_url=None)

    # 3. LLM 分析
    # 3. LLM 分析
    from app.core.config_manager import config_manager
    llm_config = config_manager.get_config().get("llm", {})

    llm = ChatOpenAI(
        model=llm_config.get("model", "gpt-4o"),
        temperature=0,
        base_url=llm_config.get("base_url"),
        api_key=llm_config.get("api_key")
    )
    
    # 结构化输出包装器
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
    如果是警报：消息以“⚠️ 警告:”或“📢 通告:”开头。
    如果【没有】关键更新，必须精确输出：“目前未发现 {{school_name}} 的关键更新。”，不要包含其他变体或解释。
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_template.format(target_year=target_year, prev_year=target_year-1)),
        ("human", "Search Results:\n{results}")
    ])
    
    chain = prompt | analyzer
    
    try:
        alert = chain.invoke({"school_name": school_name, "results": combined_results})
        
        # --- Deduplication Logic (Based on Alert Content) ---
        import hashlib
        import json
        
        # We hash the generated message content. 
        # Since Temp=0, the same semantic info should result in same/similar text.
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
        
        # Save current hash (Update history always to keep "latest" state)
        history[school_name] = content_hash
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Failed to save history: {e}")

        if last_hash == content_hash:
            # Generate a specific "Duplicate" alert but keep the content for reference if needed
            # "获取信息应为直到获取到重复信息为止" - stop and report it's same.
            return AlertMessage(has_critical_update=False, message=f"目前未发现 {school_name} 的新更新（内容与上次检查一致）。", source_url=alert.source_url)
            
        return alert
    except Exception as e:
        return AlertMessage(has_critical_update=False, message=f"分析失败: {e}")

# 4. Agent 节点 (用于图)
# 1.5 提取模型
class SchoolExtraction(BaseModel):
    """从用户输入中提取的学校名称。"""
    school_name: Optional[str] = Field(description="用户想要监控的目标学校名称")

# ... (AlertMessage 和 check_school_updates 保持不变)

# 4. Agent 节点 (用于图)
def get_radar_node():
    # 初始化用于提取的 LLM
    # 初始化用于提取的 LLM
    from app.core.config_manager import config_manager
    llm_config = config_manager.get_config().get("llm", {})

    llm = ChatOpenAI(
        model=llm_config.get("model", "gpt-4o"),
        temperature=0, 
        base_url=llm_config.get("base_url"),
        api_key=llm_config.get("api_key")
    )
    
    extractor = llm.with_structured_output(SchoolExtraction)

    def radar_node(state: AgentState):
        messages = state['messages']
        last_content = messages[-1].content
        context = state.get("context", {})
        
        # 1. 确定目标学校
        # 优先级：用户当前消息 > 上下文中的学校 > 默认值
        
        target_school = None
        
        # 尝试从当前消息提取
        try:
            extraction = extractor.invoke(f"Extract the university name from: {last_content}")
            if extraction and extraction.school_name:
                target_school = extraction.school_name
        except:
            pass
            
        # 如果未提取到，检查上下文
        if not target_school:
            target_school = context.get("monitored_school")
            
        # 如果仍未找到，使用默认值
        if not target_school:
            target_school = "中国科学院大学杭州高等研究所"
            
        # 2. 执行检查
        alert = check_school_updates(target_school)
        
        # 3. 构造响应
        from langchain_core.messages import AIMessage
        
        response_content = ""
        if alert.has_critical_update:
            response_content = f"【{target_school} 监控警报】\n{alert.message} \n(来源: {alert.source_url})"
        else:
            response_content = f"目前未发现 {target_school} 的关键更新（招生简章/科目变更）。"
            
        return {
            "messages": [AIMessage(content=response_content)],
            "context": {"monitored_school": target_school} # 更新上下文
        }

    return radar_node
