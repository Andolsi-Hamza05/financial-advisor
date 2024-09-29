from typing import Literal, TypedDict
from smart.tools import interact_with_llm_and_tools
from smart.chains import check_smt, achievable, accept, refuse, read_file
from langchain_openai import AzureChatOpenAI


class AgentState(TypedDict):
    query: str
    goal: str = None
    initial_investment: float = None
    monthly_contribution: float = None
    annual_return: float = None
    target_value: float = None
    time_horizon: int = None
    is_specific: str = None
    is_measurable: str = None
    is_time: str = None
    is_achievable: str = None
    future_investment_value: float = None
    final_response: str = None


class Agent:
    def __init__(self):
        self.llm = AzureChatOpenAI(
            azure_deployment="gpt-4o-mini",
            api_version="2023-03-15-preview",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
        )

    def check_smt_goal(self, state: AgentState) -> AgentState:
        print(f"check_smt_goal: Current state: {state}")
        check_smt_chain = check_smt(self.llm)
        result = check_smt_chain.invoke({"goal": state['query']})
        state['goal'] = result.goal
        state['initial_investment'] = result.initial_investment
        state['monthly_contribution'] = result.monthly_contribution
        state['annual_return'] = result.annual_return
        state['target_value'] = result.target_value
        state['time_horizon'] = result.time_horizon
        state['is_specific'] = result.is_specific
        state['is_measurable'] = result.is_measurable
        state['is_time'] = result.is_time
        state['query'] = f"""{state['query']} \n goal: {state['goal']} \n initial_investment: {state['initial_investment']} \n
        monthly_contribution: {state['monthly_contribution']} \n annual_return: {state['annual_return']} \n target_value: {state['target_value']} \n
        time_horizon: {state['time_horizon']} \n is_specific: {state['is_specific']} \n is_measurable: {state['is_measurable']} \n
        is_time: {state['is_time']}"""
        return state

    def check_achievable_goal(self, state: AgentState) -> AgentState:
        print(f"check_achievable_goal: Current state: {state}")
        query = state['query']
        achievable_template = read_file("achievable_template")
        response = str(interact_with_llm_and_tools(achievable_template + query, self.llm))
        achievable_chain = achievable(self.llm)
        result = achievable_chain.invoke(
            {
                "input": response
            }
        )
        state['is_achievable'] = result.is_achievable
        state['future_investment_value'] = result.future_investment_value
        state['query'] = f"""{state['query']} \n is_achievable: {state['is_achievable']} \n
        future_investment_value: {state['future_investment_value']}"""
        return state

    def accepted(self, state: AgentState) -> AgentState:
        print(f"accepted: Current state: {state}")
        investment = state["query"]
        accept_chain = accept(self.llm)
        result = accept_chain.invoke({"investment": investment})
        state["final_response"] = result.content
        return state

    def refused(self, state: AgentState) -> AgentState:
        print(f"refused: Current state: {state}")
        goal = state["query"]
        refuse_chain = refuse(self.llm)
        result = refuse_chain.invoke({"investment": goal})
        state["final_response"] = result.content
        return state

    @staticmethod
    def is_smt_goal(state: AgentState) -> Literal["validate_achievability", "not_smart"]:
        print(f"is_smt_goal: Current state: {state}")
        if (state['is_specific'] == "True") and (state['is_time'] == "True") and (state['is_measurable'] == "True"):
            return "validate_achievability"
        else:
            return "not_smart"

    @staticmethod
    def is_achievable_goal(state: AgentState) -> Literal["smart", "not_smart"]:
        print(f"is_achievable_goal: Current state: {state}")
        if state['is_achievable'] == "True":
            return "smart"
        else:
            return "not_smart"

    @staticmethod
    def direct_to_respond(state: AgentState) -> Literal["respond"]:
        return "respond"

    @staticmethod
    def send_final_answer(state: AgentState):
        print(f"is_achievable_goal: Current state: {state}")
        return state
