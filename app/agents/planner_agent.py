import os
import datetime
from typing import List, Literal, Union, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, AIMessage
import pandas as pd

from app.runtime.graph.state import AgentState
from app.runtime.llm import get_llm
from app.infrastructure.utils.json_parser import parse_json

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

def get_planner_node():
    """
    返回 Planner Agent 的 LangGraph 节点。
    """
    llm = get_llm(temperature=0)

    try:
        structured_llm = llm.with_structured_output(Schedule)
    except NotImplementedError:
        structured_llm = llm

    system_template = """你是考研资深教务主任（Senior Academic Dean）。
    你的目标是根据用户的情况创建或调整学习计划。

    当前时间：{current_time}

    现有计划（如果有）：
    {existing_plan_context}

    规则：
    1. 严谨且现实。时间分配必须合理。
    2. 关注用户的"弱项"。
    3. 如果有现有计划，请根据用户的请求对其进行修改（例如"推迟任务"或"添加新任务"）。
    4. 必须输出符合以下 JSON Schema 的 JSON 对象：
    {{
        "tasks": [
            {{
                "date": "YYYY-MM-DD",
                "subject": "科目名称",
                "task_content": "任务详情",
                "estimated_hours": 2.5,
                "priority": "高/中/低"
            }}
        ]
    }}
    5. 如果用户说"今天没完成任务"，你必须将未完成的任务重新安排到未来的日期，并提高优先级。
    6. 不要输出任何额外的解释文本，只输出 JSON。
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_template),
        ("human", "{input}")
    ])

    chain = prompt | structured_llm

    def planner_node(state: AgentState):
        messages = state['messages']
        last_message = messages[-1]
        user_input = last_message.content
        context = state.get("context", {})

        existing_plan_data = context.get("study_plan", None)
        existing_plan_str = "无"
        if existing_plan_data:
            try:
                tasks = existing_plan_data.get("tasks", [])
                existing_plan_str = "\n".join([f"- [{t.get('date')}] {t.get('subject')}: {t.get('task_content')}" for t in tasks])
            except:
                existing_plan_str = "解析现有计划失败"

        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        try:
            response = chain.invoke({
                "input": user_input,
                "current_time": current_time,
                "existing_plan_context": existing_plan_str
            })

            if isinstance(response, Schedule):
                schedule_obj = response
            else:
                content = response.content
                try:
                    data = parse_json(content)
                    schedule_obj = Schedule(**data)
                except Exception as e:
                    print(f"Failed to parse Planner JSON: {e}, content: {content[:100]}...")
                    schedule_obj = Schedule(tasks=[])

        except Exception as e:
            print(f"Planner Chain Error: {e}")
            schedule_obj = Schedule(tasks=[])

        if schedule_obj:
            new_plan_dict = schedule_obj.model_dump()
        else:
            new_plan_dict = {}

        task_count = len(schedule_obj.tasks)

        summary_lines = []
        for task in schedule_obj.tasks[:5]:
            summary_lines.append(f"- {task.date} | {task.subject}: {task.task_content}")

        if task_count > 5:
            summary_lines.append(f"... 等共 {task_count} 项任务")

        response_text = f"已为您更新学习计划，共 {task_count} 项任务。\n\n近期安排：\n" + "\n".join(summary_lines)

        return {
            "messages": [AIMessage(content=response_text)],
            "context": {"study_plan": new_plan_dict}
        }

    return planner_node
