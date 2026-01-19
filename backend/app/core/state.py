from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict, total=False):
    """
    Master Agent 图的状态定义。
    """
    messages: Annotated[List[BaseMessage], operator.add]
    # 用于路由逻辑
    next_step: str
    # 上下文或其他共享数据可以在此处添加
    context: dict
    # 可选：用于持久化的用户 ID
    user_id: str
    
    # 路由推理过程
    reasoning: str
    
    # 面试模块状态
    # 注意：使用 get() 访问以防缺失
    interview_stage: str
    question_count: int

    # 复习模块状态
    review_queue: List[dict]
    
    # MCP 服务配置
    web_search_enabled: bool
