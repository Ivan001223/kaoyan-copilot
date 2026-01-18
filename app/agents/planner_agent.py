import os
from typing import List, Literal, Union, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from app.core.state import AgentState
import pandas as pd

# 1. 结构化输出模型
class StudyTask(BaseModel):
    """单个学习任务。"""
    date: Optional[str] = Field(None, description="任务日期")
    subject: Optional[str] = Field(None, description="科目")
    task_content: Optional[str] = Field(None, description="详细内容")
    estimated_hours: Optional[float] = Field(None, description="预计耗时")
    priority: Optional[Union[str, int]] = Field(None, description="优先级")

class Schedule(BaseModel):
    """学习任务列表。"""
    tasks: List[StudyTask] = Field(description="每日学习任务列表")

# 2. Planner 节点
def get_planner_node():
    """
    返回 Planner Agent 的 LangGraph 节点。
    """
    # 初始化 LLM
    # 初始化 LLM
    from app.core.config_manager import config_manager
    llm_config = config_manager.get_config().get("llm", {})

    llm = ChatOpenAI(
        model=llm_config.get("model", "gpt-4o"),
        temperature=0,
        base_url=llm_config.get("base_url"),
        api_key=llm_config.get("api_key")
    )
    
    # 强制结构化输出
    structured_llm = llm.with_structured_output(Schedule)

    # 系统提示
    system_template = """你是考研资深教务主任（Senior Academic Dean）。
    你的目标是根据用户的情况创建或调整学习计划。
    
    当前时间：{current_time}
    
    现有计划（如果有）：
    {existing_plan_context}

    规则：
    1. 严谨且现实。时间分配必须合理。
    2. 关注用户的“弱项”。
    3. 如果有现有计划，请根据用户的请求对其进行修改（例如“推迟任务”或“添加新任务”）。
    4. 输出必须是具有特定字段的结构化 JSON。
    5. 如果用户说“今天没完成任务”，你必须将未完成的任务重新安排到未来的日期，并提高优先级。
    """
    
    prompt = ChatPromptTemplate.from_template(system_template)
    chain = prompt | structured_llm

    def planner_node(state: AgentState):
        messages = state['messages']
        last_message = messages[-1]
        user_input = last_message.content
        context = state.get("context", {})
        
        # 1. 获取现有计划
        existing_plan_data = context.get("study_plan", None)
        existing_plan_str = "无"
        if existing_plan_data:
            # 简单整理一下给 LLM 看
            try:
                tasks = existing_plan_data.get("tasks", [])
                existing_plan_str = "\n".join([f"- [{t.get('date')}] {t.get('subject')}: {t.get('task_content')}" for t in tasks])
            except:
                existing_plan_str = "解析现有计划失败"

        # 2. 生成/更新计划
        import datetime
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        schedule_obj = chain.invoke({
            "input": user_input, 
            "current_time": current_time,
            "existing_plan_context": existing_plan_str
        })
        
        # 3. 持久化保存到 Context
        # 我们将更新后的计划存回 state.context
        # 注意：LangGraph 的 state 更新通常是浅合并，对于嵌套字典需要小心。
        # 这里我们返回 clear 的 key update。
        new_plan_dict = schedule_obj.model_dump()
        
        # 4. 生成回复
        # 不再直接甩 CSV，而是生成一段友好的总结，并告知计划已更新
        task_count = len(schedule_obj.tasks)
        
        summary_lines = []
        for task in schedule_obj.tasks[:5]: # 只列出前几个
            summary_lines.append(f"- {task.date} | {task.subject}: {task.task_content}")
        
        if task_count > 5:
            summary_lines.append(f"... 等共 {task_count} 项任务")
            
        response_text = f"已为您更新学习计划，共 {task_count} 项任务。\n\n近期安排：\n" + "\n".join(summary_lines)
        
        from langchain_core.messages import AIMessage
        return {
            "messages": [AIMessage(content=response_text)],
            "context": {"study_plan": new_plan_dict} # 更新 Context
        }

    return planner_node
