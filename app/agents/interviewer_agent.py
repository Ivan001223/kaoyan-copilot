import os
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage
from app.core.state import AgentState

# 1. 评分模型
class InterviewEvaluation(BaseModel):
    logic_score: int = Field(description="逻辑连贯性得分 (1-10)。")
    vocabulary_score: int = Field(description="词汇/专业术语得分 (1-10)。")
    confidence_score: int = Field(description="自信/语气得分 (1-10)。")
    comment: str = Field(description="对表现的简短点评。")

# 2. 逻辑
def get_interviewer_node():
    # 初始化 LLM
    # 初始化 LLM
    from app.core.llm_factory import get_llm
    llm = get_llm(temperature=0.2) # 低温以保持严谨
    
    # 评估器
    evaluator = llm.with_structured_output(InterviewEvaluation)

    def evaluate_response(user_text: str, current_question: str) -> InterviewEvaluation:
        system_tmpl = """你是张教授，一位严厉的面试官。
        请评估候选人对以下问题的回答："{question}"。
        
        标准：
        - 逻辑 (1-10)：回答是否有条理且切题？
        - 词汇 (1-10)：是否使用了专业术语？（如果是英语，检查语法）。
        - 自信 (1-10)：语气是否坚定？
        
        提供简短、严厉的点评（简体中文）。
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_tmpl),
            ("human", "{answer}")
        ])
        chain = prompt | evaluator
        return chain.invoke({"question": current_question, "answer": user_text})

    def generate_next_question(history_context: str) -> str:
        system_tmpl = """你是张教授，一位严厉的面试官。
        你正在进行研究生入学模拟复试。
        
        你的人设：
        - 姓名：张教授。
        - 语气：严厉、专业、直接。不要闲聊。
        - 方式：一次只问一个难题。
        
        根据上下文生成下一个专业问题。
        如果是开始，请要求进行自我介绍。
        
        输出简体中文。
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_tmpl),
            ("human", "{context}")
        ])
        return llm.invoke({"context": history_context}).content

    def interviewer_node(state: AgentState):
        messages = state['messages']
        last_message = messages[-1]
        
        # 状态管理（简单的模拟，如果有 state dict key，否则默认）
        stage = state.get('interview_stage', 'intro')
        q_count = state.get('question_count', 0)
        
        response_text = ""
        new_stage = stage
        new_count = q_count
        
        # 逻辑流
        if stage == 'intro':
            # 面试开始
            response_text = "我是张教授。现在开始复试模拟。请先做一个简短的自我介绍 (Self-introduction)。"
            new_stage = 'questioning'
            new_count = 0
            
        elif stage == 'questioning':
            # 用户刚刚回答了一个问题（或自我介绍）
            
            # 1. 评估之前的回答（如果不是触发此状态的第一次交互）
            # 用户消息在 last_message.content 中
            # 我们假设之前的系统消息是问题。
            
            # 简单 Hack：生成分数 + 下一个问题
            score = evaluate_response(last_message.content, "Previous Question")
            
            evaluation_text = (
                f"[评价]\n"
                f"逻辑: {score.logic_score}/10 | 词汇: {score.vocabulary_score}/10 | 自信: {score.confidence_score}/10\n"
                f"点评: {score.comment}\n"
            )
            
            if new_count >= 3:
                # 结束会话
                 response_text = f"{evaluation_text}\n\n面试结束。你的表现已记录。请回去等通知。"
                 new_stage = 'end'
            else:
                # 下一个问题
                next_q = generate_next_question(f"Candidate just said: {last_message.content}")
                response_text = f"{evaluation_text}\n\n下一个问题：{next_q}"
                new_count += 1
                
        elif stage == 'end':
            response_text = "面试已经结束了。请不要逗留。"
            
        return {
            "messages": [AIMessage(content=response_text)],
            "interview_stage": new_stage,
            "question_count": new_count
        }

    return interviewer_node
