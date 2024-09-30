from langgraph.graph import StateGraph, END
from smart.agent import Agent, AgentState


def set_agentic_workflow():
    print("Entering set_agentic_workflow")
    agent = Agent()

    workflow = StateGraph(AgentState)

    workflow.add_node("validate_smt", agent.check_smt_goal)
    workflow.add_node("validate_achievability", agent.check_achievable_goal)
    workflow.add_node("smart", agent.accepted)
    workflow.add_node("not_smart", agent.refused)
    workflow.add_node("respond", agent.send_final_answer)

    workflow.set_entry_point("validate_smt")

    workflow.add_conditional_edges(
        "validate_smt", agent.is_smt_goal, {"validate_achievability": "validate_achievability", "not_smart": "not_smart"}
    )

    workflow.add_conditional_edges(
        "validate_achievability",
        agent.is_achievable_goal,
        {"smart": "smart", "not_smart": "not_smart"}
    )

    workflow.add_edge("smart", "respond")

    workflow.add_edge("not_smart", "respond")

    workflow.add_edge("respond", END)

    app = workflow.compile()
    print("Compiling the workflow and returning the app")
    return app
