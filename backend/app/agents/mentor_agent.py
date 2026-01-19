import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.state import AgentState

def get_mentor_node():
    """
    返回 Mentor Agent 的 LangGraph 节点。
    """
    # 初始化 LLM
    # 初始化 LLM
    from app.core.llm_factory import get_llm
    llm = get_llm(temperature=0.7) # 较高的温度以增加同理心

    # 系统提示
    system_template = """你是一位考研心态教练（Kaoyan Mentor）。
    你是一位温柔但坚定的“过来人”。
    你的目标是提供情感支持和现实检验。

    指令：
    1. 首先分析用户的隐含情绪（焦虑、疲惫、自满或正常）。
    2. 如果用户焦虑/疲惫（例如：“累”、“想放弃”、“害怕”）：
       - 首先共情。
       - 提供鼓励和可执行的小步骤。
       - **不要**强迫他们立即去学习。
    3. 如果用户自满（例如：“太简单”、“不需要复习”）：
       - 进行“现实检验”。提醒他竞争的激烈程度。
    4. 使用温暖、支持性的语气（简体中文）。
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_template),
        ("human", "{input}"),
    ])

    # 链
    chain = prompt | llm

    def mentor_node(state: AgentState):
        messages = state['messages']
        last_message = messages[-1]
        user_input = last_message.content
        
        response = chain.invoke({"input": user_input})
        
        from langchain_core.messages import AIMessage
        return {"messages": [AIMessage(content=response.content)]}

    return mentor_node
