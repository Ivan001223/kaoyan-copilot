import os
from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

# 1. Define Structured Output Model
class RouteDecision(BaseModel):
    """Router decision on which agent should handle the user request or if the task is finished."""
    destination: Literal["tutor", "consultant", "planner", "mentor", "estimator", "radar", "interviewer", "general", "FINISH"] = Field(
        description="The target agent to route the request to, or 'FINISH' if the user's request is satisfied."
    )
    reasoning: str = Field(
        description="Explanation of why this agent was chosen or why the task is finished."
    )
    refined_query: str = Field(
        description="A refined version of the user query optimized for the target agent. If finishing, can be a summary."
    )

# 2. Supervisor Implementation
def route_request(state: Dict[str, Any]) -> RouteDecision:
    """
    Analyzes the conversation state and routes to the appropriate expert agent or finishes the conversation.
    Acts as a Supervisor Node in the graph.
    """
    messages = state.get("messages", [])
    
    # Fallback if no messages
    if not messages:
        return RouteDecision(destination="general", reasoning="No messages found", refined_query="Hello")

    # Initialize LLM
    from app.core.llm_factory import get_llm
    # Use json_mode=True to encourage JSON output, though we will handle parsing manually for robustness
    llm = get_llm(temperature=0, json_mode=True)

    # System Prompt for Supervisor
    system_template = """You are the **Master Supervisor** of the "Grad School Copilot" system.
    Your goal is to orchestrate a team of expert agents to fully resolve the user's request.
    
    ### Your Team:
    1. **Tutor**: Subject expert (Math, English, Politics). Handles specific questions, concept explanations, calculation.
    2. **Consultant**: Admissions data expert. University stats, dates, policies, quotas.
    3. **Planner**: Study planning expert. Schedules, progress tracking, time management.
    4. **Mentor**: Psychological support. Motivation, stress relief, anxiety management.
    5. **Estimator**: Success probability analyst. Score gap analysis, prediction.
    6. **Radar**: News monitor. New syllabus, policy changes, alerts.
    7. **Interviewer**: Mock interview conductor. (Route here to start/continue an interview session).
    8. **General**: Fallback for greetings or ambiguous queries.

    ### Routing Logic:
    Review the **entire conversation history**, with special attention to the **last message**.
    
    1. **New Request**: If the last message is from the User (Human), analyze their intent and route to the best Agent.
    2. **Review Output**: If the last message is from an Agent (AI):
       - **CRITICAL**: Check if the agent has already addressed the user's request.
       - If the AI message says "Plan updated", "Here is the answer", or provides the requested information -> **YOU MUST OUTPUT `destination='FINISH'`**.
       - Do NOT route back to the same agent if they just successfully replied.
       - Only route to another agent if a specific follow-up step is required (e.g. "Now I need to calculate probabilities").
       - If the AI message indicates an error, route to `general` or retry.

    ### Common Pitfalls:
    - **Looping**: If the Planner just output a plan, do NOT send it back to the Planner. FINISH immediately.
    - **Redundancy**: If the Tutor just explained a concept, do NOT send it back to the Tutor. FINISH immediately.

    ### Output Requirements:
    You must output a valid JSON object strictly adhering to the following schema. 
    **Do NOT output any thinking process, markdown formatting, or extra text.**
    **CRITICAL**: Do NOT use LaTeX or backslashes in your 'reasoning' or 'refined_query' fields unless absolutely necessary. If you must, ensure they are properly escaped for JSON (e.g. "\\frac" becomes "\\\\frac").
    
    Schema:
    {{
        "destination": "tutor" | "consultant" | "planner" | "mentor" | "estimator" | "radar" | "interviewer" | "general" | "FINISH",
        "reasoning": "Explanation of why this agent was chosen or why the task is finished.",
        "refined_query": "A refined version of the user query optimized for the target agent."
    }}
    """

    # Sanitize messages to ensure compatibility and avoid 'unknown type' errors
    sanitized_messages = []
    for msg in messages:
        # Check if message content is list (Multimodal)
        raw_content = getattr(msg, "content", str(msg))
        
        # If it's a list (multimodal), we extract only the text part for the Orchestrator
        # The Orchestrator doesn't need the image itself, just the text intent.
        if isinstance(raw_content, list):
            text_parts = [item.get('text', '') for item in raw_content if item.get('type') == 'text']
            content = " ".join(text_parts)
            # Add a hint that an image was provided
            content += " [User provided an image]"
        else:
            content = raw_content

        msg_type = getattr(msg, "type", "human")
        
        if msg_type == "human":
            sanitized_messages.append(HumanMessage(content=content))
        elif msg_type == "ai":
            sanitized_messages.append(AIMessage(content=content))
        else:
            # Fallback for other types (system, tool, etc.) -> treat as Human context or ignore
            sanitized_messages.append(HumanMessage(content=f"[{msg_type}]: {content}"))
            
    # Debug: Print the last message seen by the supervisor
    if sanitized_messages:
        last_msg = sanitized_messages[-1]
        print(f"Supervisor Last Msg: Type={type(last_msg)}, Content={last_msg.content[:50]}...")
        
        # --- Heuristic Routing for Local Models ---
        
        # Check if the last message is from AI and indicates completion
        if isinstance(last_msg, AIMessage):
             print("Supervisor Decision: Heuristic -> FINISH (AI Replied)")
             return RouteDecision(
                destination="FINISH",
                reasoning="AI has already replied, ending turn.",
                refined_query="Task Completed"
            )

        last_content_lower = str(last_msg.content).lower()
        
        # 1. Image / Multimodal Check
        # If the user provided an image, it's almost certainly a Tutor task (math, OCR, etc.)
        if "[user provided an image]" in last_content_lower:
            print("Supervisor Decision: Heuristic -> tutor (Image Detected)")
            return RouteDecision(
                destination="tutor",
                reasoning="User provided an image, routing to Tutor for visual analysis.",
                refined_query=last_msg.content.replace(" [User provided an image]", "") # Pass original intent
            )
            
        # 2. Math / Subject Keywords
        math_keywords = ["math", "calculus", "algebra", "equation", "solve", "integrate", "derivative", "matrix", "probability", "statistics", "数学", "微积分", "代数", "方程", "解", "积分", "导数", "矩阵", "概率", "统计", "不等式", "函数", "极限", "x^2", "sin", "cos"]
        if any(kw in last_content_lower for kw in math_keywords):
             print("Supervisor Decision: Heuristic -> tutor (Math Keyword Detected)")
             return RouteDecision(
                destination="tutor",
                reasoning="Math keywords detected, routing to Tutor.",
                refined_query=last_msg.content
            )

        # 3. Politics Keywords
        politics_keywords = ["politics", "marxism", "maoism", "socialism", "communist", "party", "constitution", "ideology", "政治", "马克思", "毛泽东", "社会主义", "共产党", "宪法", "意识形态", "马原", "毛中特", "史纲", "思修"]
        if any(kw in last_content_lower for kw in politics_keywords):
             print("Supervisor Decision: Heuristic -> tutor (Politics Keyword Detected)")
             return RouteDecision(
                destination="tutor",
                reasoning="Politics keywords detected, routing to Tutor.",
                refined_query=last_msg.content
            )
            
        # 4. English Keywords
        english_keywords = ["english", "grammar", "vocabulary", "translation", "essay", "writing", "reading", "comprehension", "英语", "语法", "词汇", "翻译", "作文", "写作", "阅读", "理解", "长难句"]
        if any(kw in last_content_lower for kw in english_keywords):
             print("Supervisor Decision: Heuristic -> tutor (English Keyword Detected)")
             return RouteDecision(
                destination="tutor",
                reasoning="English keywords detected, routing to Tutor.",
                refined_query=last_msg.content
            )
            
        # 5. Planning Keywords
        planning_keywords = ["plan", "schedule", "timetable", "routine", "progress", "deadline", "todo", "task", "计划", "安排", "时间表", "进度", "截止", "待办", "任务", "规划"]
        if any(kw in last_content_lower for kw in planning_keywords):
             print("Supervisor Decision: Heuristic -> planner (Planning Keyword Detected)")
             return RouteDecision(
                destination="planner",
                reasoning="Planning keywords detected, routing to Planner.",
                refined_query=last_msg.content
            )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_template),
        MessagesPlaceholder(variable_name="messages"),
    ])

    chain = prompt | llm

    try:
        # Invoke with sanitized message history
        response = chain.invoke({"messages": sanitized_messages})
        content = response.content
        
        # Manual cleaning and parsing to handle Chain-of-Thought or Markdown artifacts
        import json
        import re
        
        # 1. Remove <think> tags if present
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL)
        
        # 2. Remove Markdown code blocks
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```', '', content)
        
        # 3. Strip whitespace
        content = content.strip()
        
        # 4. Parse JSON
        try:
            # Fix common JSON issues with LaTeX backslashes
            # Replace single backslashes with double backslashes, but be careful not to double escape
            # This is a simple heuristic: if we see \ followed by a non-special char, escape it.
            # However, regex cleaning is safer.
            
            # Simple escape for backslashes that look like LaTeX
            # We want to replace \ with \\, but not if it's already \\ or \" or \n
            # content = content.replace('\\', '\\\\') # This is too aggressive and might break existing escapes
            
            data = json.loads(content)
            return RouteDecision(**data)
        except json.JSONDecodeError:
            # Try to find JSON object if mixed with text
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                json_str = match.group(0)
                try:
                    data = json.loads(json_str)
                    return RouteDecision(**data)
                except json.JSONDecodeError:
                     # Attempt to fix escaped backslashes in the extracted JSON string
                     # This handles cases like "\frac" appearing in the string value
                     json_str_fixed = json_str.replace('\\', '\\\\')
                     try:
                        data = json.loads(json_str_fixed)
                        return RouteDecision(**data)
                     except:
                        pass
            
            raise ValueError(f"Could not parse JSON from content: {content[:100]}...")
                
    except Exception as e:
        print(f"Routing failed: {e}")
        # If routing fails, default to tutor if the last message looks like a question, otherwise mentor
        # But for now, stick to general -> mentor flow but with better error handling
        return RouteDecision(destination="general", reasoning=f"Error: {e}", refined_query="Help")
