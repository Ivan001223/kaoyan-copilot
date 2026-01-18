import os
from typing import List, Dict
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.core.state import AgentState

# 1. 数据模型
class TargetSchool(BaseModel):
    school_name: str
    major: str
    previous_year_score_line: float = Field(description="去年的总分线")
    subject_lines: Dict[str, float] = Field(description="单科分数线", default_factory=dict)
    acceptance_rate: float = Field(description="录取率（例如 0.15 表示 15%）")

class UserProgress(BaseModel):
    current_mock_scores: Dict[str, float] = Field(description="各科当前模拟成绩")
    study_hours_per_day: float

# 2. 计算逻辑
def calculate_gap(user: UserProgress, target: TargetSchool) -> Dict[str, float]:
    """计算用户成绩与目标成绩之间的差距。"""
    gaps = {}
    
    # 计算总分差距
    user_total = sum(user.current_mock_scores.values())
    gaps["total_gap"] = target.previous_year_score_line - user_total
    
    # 计算单科差距（如果有数据）
    for subject, target_score in target.subject_lines.items():
        user_score = user.current_mock_scores.get(subject, 0)
        gaps[subject] = target_score - user_score
        
    return gaps

def predict_success_probability(user: UserProgress, target: TargetSchool) -> float:
    """
    根据差距和学习习惯估算成功概率。
    基础逻辑：
    - 基础概率：50%
    - 分数差距：低于每1分 -2%，高于每1分 +1%。
    - 录取率：如果不低于 10%，-10%。如果高于 30%，+10%。
    - 学习时间：如果 > 8 小时/天，+5%。如果 < 4 小时/天，-10%。
    """
    prob = 0.50 # 基础
    
    # 1. 分数因素
    gaps = calculate_gap(user, target)
    total_gap = gaps["total_gap"]
    
    if total_gap > 0: # 用户低于目标线
        prob -= (total_gap * 0.02)
    else: # 用户高于目标线（差距为负）
        prob += (abs(total_gap) * 0.01)
        
    # 2. 录取率因素
    if target.acceptance_rate < 0.10:
        prob -= 0.10
    elif target.acceptance_rate > 0.30:
        prob += 0.10
        
    # 3. 学习时间因素
    if user.study_hours_per_day >= 8:
        prob += 0.05
    elif user.study_hours_per_day < 4:
        prob -= 0.10
        
    # 限制概率范围
    return max(0.01, min(0.99, prob))

from typing import Optional

# 1.5 提取模型
class ExtractionInput(BaseModel):
    """从用户输入中提取的用于估算的信息。"""
    target_school: Optional[str] = Field(description="目标大学名称")
    target_major: Optional[str] = Field(description="目标专业")
    target_score: Optional[float] = Field(description="目标分数线或往年分数线")
    current_score: Optional[float] = Field(description="用户当前模拟考试总分")
    study_hours: Optional[float] = Field(description="每日学习时长")
    acceptance_rate: Optional[float] = Field(description="录取率 (0-1的小数)", default=None)

# 2. 计算逻辑 (保持不变)
# ... (calculate_gap, predict_success_probability 已经在上面定义，无需重复)

# 3. Agent 节点
def get_estimator_node():
    """
    返回 Estimator Agent 的 LangGraph 节点。
    """
    # 初始化 LLM
    # 初始化 LLM
    from app.core.config_manager import config_manager
    llm_config = config_manager.get_config().get("llm", {})

    llm = ChatOpenAI(
        model=llm_config.get("model", "gpt-4o"),
        temperature=0.3, # 稍微增加一点创造性用于提取推断
        base_url=llm_config.get("base_url"),
        api_key=llm_config.get("api_key")
    )

    # 提取器
    extractor = llm.with_structured_output(ExtractionInput)

    # 报告生成链
    report_system_template = """你是一位考研数据分析师 (Data Analyst)。
    你的任务是根据计算出的成功概率生成一份报告。

    数据：
    - 目标院校：{school_name} ({major})
    - 录取率：{acceptance_rate:.0%}
    - 分数差距（总分）：{total_gap}
    - 预估成功率：{probability:.1%}
    - 每日学习时长：{study_hours}

    指令：
    1. 保持客观但带有情感。使用严肃但鼓励的语气。
    2. 明确提到差距数据（例如：“你距离目标还差 20 分...”）。
    3. 根据差距给出具体建议。
    4. 如果概率较低 (< 30%)，给出“警钟长鸣”。
    5. 如果概率较高 (> 70%)，提醒不要自满。
    
    输出简体中文。
    """
    
    report_prompt = ChatPromptTemplate.from_template(report_system_template)
    report_chain = report_prompt | llm

    def estimator_node(state: AgentState):
        messages = state['messages']
        last_content = messages[-1].content
        
        # 1. 提取信息
        try:
            extracted_data: ExtractionInput = extractor.invoke(f"请从以下文本中提取考研相关数据：\n{last_content}")
        except Exception as e:
            from langchain_core.messages import AIMessage
            return {"messages": [AIMessage(content=f"抱歉，数据解析失败: {e}")]}
            
        # 2. 验证必要字段
        # 我们至少需要：目标分数、当前分数。
        # 如果学校/专业缺失，我们可以用通用术语。
        # 如果学习时间缺失，我们可以假设一个平均值或者询问。
        
        missing_fields = []
        if not extracted_data.target_score:
            missing_fields.append("目标分数线")
        if not extracted_data.current_score:
            missing_fields.append("你目前的模拟分数")
            
        if missing_fields:
            from langchain_core.messages import AIMessage
            # 构造追问消息
            ask_msg = f"为了帮您准确估算成功率，我还需要了解以下信息：\n" + "\n".join([f"- {field}" for field in missing_fields])
            ask_msg += "\n\n(例如：我考了320分，目标分数是360分)"
            return {"messages": [AIMessage(content=ask_msg)]}

        # 3. 填充默认值
        school_name = extracted_data.target_school or "目标院校"
        major = extracted_data.target_major or "目标专业"
        study_hours = extracted_data.study_hours or 6.0 # 默认 6 小时
        acceptance_rate = extracted_data.acceptance_rate or 0.15 # 默认 15% 录取率

        # 4. 构造计算对象
        target = TargetSchool(
            school_name=school_name, 
            major=major, 
            previous_year_score_line=extracted_data.target_score,
            subject_lines={}, # 单科暂未提取，简化处理
            acceptance_rate=acceptance_rate
        )
        
        # 简化处理：我们将总分均分到各科或直接作为一个整体处理
        # 这里的 calculate_gap 使用 sum(values)，所以我们可以构造一个虚拟科目
        user = UserProgress(
            current_mock_scores={"总分": extracted_data.current_score},
            study_hours_per_day=study_hours
        )
        
        # 5. 计算逻辑
        gap_data = calculate_gap(user, target)
        prob = predict_success_probability(user, target)
        
        # 6. 生成报告
        response = report_chain.invoke({
            "school_name": target.school_name,
            "major": target.major,
            "acceptance_rate": target.acceptance_rate,
            "total_gap": gap_data["total_gap"],
            "probability": prob,
            "study_hours": user.study_hours_per_day
        })
        
        from langchain_core.messages import AIMessage
        return {"messages": [AIMessage(content=response.content)]}

    return estimator_node
