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
    from app.core.config_manager import config_manager
    llm_config = config_manager.get_config().get("llm", {})

    llm = ChatOpenAI(
        model=llm_config.get("model", "gpt-4o"),
        temperature=0,
        base_url=llm_config.get("base_url"),
        api_key=llm_config.get("api_key")
    )

    # Bind structured output
    router_llm = llm.with_structured_output(RouteDecision)

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
    - `destination`: The next node name or "FINISH".
    - `reasoning`: Why you made this decision (e.g., "Tutor explained the concept, task complete" or "Consultant provided data, now Estimator needs to analyze it").
    - `refined_query`: The specific instruction for the next agent.
    """

    # Sanitize messages to ensure compatibility and avoid 'unknown type' errors
    sanitized_messages = []
    for msg in messages:
        content = getattr(msg, "content", str(msg))
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

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_template),
        MessagesPlaceholder(variable_name="messages"),
    ])

    chain = prompt | router_llm

    try:
        # Invoke with sanitized message history
        decision = chain.invoke({"messages": sanitized_messages})
        return decision
    except Exception as e:
        print(f"Routing failed: {e}")
        return RouteDecision(destination="general", reasoning=f"Error: {e}", refined_query="Help")
