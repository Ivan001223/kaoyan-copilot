import os
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from app.core.state import AgentState
from app.core.orchestrator import route_request, RouteDecision

# Import Agent Nodes
from app.agents.tutor_agent import get_tutor_node
from app.agents.consultant_agent import get_consultant_node
from app.agents.planner_agent import get_planner_node
from app.agents.mentor_agent import get_mentor_node
from app.agents.estimator_agent import get_estimator_node
from app.agents.radar_agent import get_radar_node
from app.agents.interviewer_agent import get_interviewer_node

def run_app():
    """
    Constructs and compiles the main LangGraph application with Supervisor Architecture.
    """
    # 1. Initialize Nodes
    tutor_node = get_tutor_node()
    consultant_node = get_consultant_node()
    planner_node = get_planner_node()
    mentor_node = get_mentor_node()
    estimator_node = get_estimator_node()
    radar_node = get_radar_node()
    interviewer_node = get_interviewer_node()
    
    # 2. Define Orchestrator Node (Supervisor)
    def orchestrator_node(state: AgentState):
        """
        Supervisor node that decides the next step based on conversation history.
        """
        # Sticky Routing for Interview
        # If we are in an interview loop, prioritize returning to the interviewer
        interview_stage = state.get("interview_stage")
        if interview_stage and interview_stage in ["intro", "questioning"]:
            # Check if user explicitly wants to exit (logic can be enhanced)
            return {"next_step": "interviewer"}
            
        # Call the Supervisor LLM to route
        decision: RouteDecision = route_request(state)
        
        # We can log the decision here for debugging
        print(f"Supervisor Decision: {decision.destination} | Reasoning: {decision.reasoning}")
        
        return {"next_step": decision.destination, "reasoning": decision.reasoning}

    # 3. Build Graph
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("tutor", tutor_node)
    workflow.add_node("consultant", consultant_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("mentor", mentor_node)
    workflow.add_node("estimator", estimator_node)
    workflow.add_node("radar", radar_node)
    workflow.add_node("interviewer", interviewer_node)
    
    # Set Entry Point
    workflow.set_entry_point("orchestrator")
    
    # 4. Define Conditional Edges from Orchestrator
    def router(state: AgentState):
        step = state.get('next_step')
        if step == "general":
            return "mentor" # Fallback to mentor for general chat
        return step

    workflow.add_conditional_edges(
        "orchestrator",
        router,
        {
            "tutor": "tutor",
            "consultant": "consultant",
            "planner": "planner",
            "mentor": "mentor",
            "estimator": "estimator",
            "radar": "radar",
            "interviewer": "interviewer",
            "general": "mentor",
            "FINISH": END
        }
    )
    
    # 5. Define Cyclic Edges (Agents -> Orchestrator)
    # Instead of ending, agents report back to the supervisor.
    workflow.add_edge("tutor", "orchestrator")
    workflow.add_edge("consultant", "orchestrator")
    workflow.add_edge("planner", "orchestrator")
    workflow.add_edge("mentor", "orchestrator")
    workflow.add_edge("estimator", "orchestrator")
    workflow.add_edge("radar", "orchestrator")
    workflow.add_edge("interviewer", "orchestrator")
    
    # Compile
    app = workflow.compile()
    return app

# Expose the app instance
app = run_app()
