from typing import Literal, TypedDict
import pydantic_core
from smart.tools import interact_with_llm_and_tools
from smart.chains import check_smt, achievable, accept, refuse, read_file
from langchain_openai import AzureChatOpenAI


class AgentState(TypedDict):
    query: str
    goal: str = ""
    initial_investment: float = 0
    monthly_contribution: float = 0
    annual_return: float = 0
    target_value: float = 0
    time_horizon: int = 0
    is_specific: str = "False"
    is_measurable: str = "False"
    is_time: str = "False"
    is_achievable: str = "False"
    future_investment_value: float = 0
    final_response: str = ""


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
        check_smt_chain = check_smt(self.llm)
        result = check_smt_chain.invoke({"goal": state['query']})
        print(f"check_smt_goal function getting result {result}")
        try:
            state['goal'] = result.goal
            state['initial_investment'] = result.initial_investment
            state['monthly_contribution'] = result.monthly_contribution
            state['annual_return'] = result.annual_return
            state['target_value'] = result.target_value
            state['time_horizon'] = result.time_horizon
            if result.goal != "":
                state['is_specific'] = "True"
            if (result.target_value > 0) and ((result.monthly_contribution > 0) or (result.initial_investment > 0)):
                state['is_measurable'] = "True"
            if result.time_horizon > 0:
                state['is_time'] = "True"
            state['query'] = f"""{state['query']} \n goal: {state['goal']} \n initial_investment: {state['initial_investment']} \n
            monthly_contribution: {state['monthly_contribution']} \n annual_return: {state['annual_return']} \n target_value: {state['target_value']} \n
            time_horizon: {state['time_horizon']} \n is_specific: {state['is_specific']} \n is_measurable: {state['is_measurable']} \n
            is_time: {state['is_time']}"""

        except pydantic_core._pydantic_core.ValidationError as e:
            print(f"check_smt_goal error : {e}")

        print(f" quiting check_smt_goal: Final state: {state}")
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

        print(f"check_achievable_goal: Final state: {state}")
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
        if state['time_horizon'] == 0:
            state['is_time'] = "False"
        if (state['initial_investment'] == 0.0) and (state['monthly_contribution'] == 0.0):
            state['is_measurable'] = "False"
        if state['target_value'] == 0.0:
            state['is_measurable'] = "False"
        if state['goal'] == "":
            state['is_specific'] = "False"
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
        print(f"sending final response: Current state: {state}")
        return state
