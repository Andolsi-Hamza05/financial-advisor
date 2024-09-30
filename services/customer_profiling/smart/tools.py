from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage


@tool
def check_achievable(initial_investment: float, monthly_contribution: float, annual_return: float, target_value: float, time_horizon: int):
    """
    Calculate the future value (FV) of an investment and compare it with the target value.

    Args:
    - initial_investment: The starting amount of investment (P).
    - monthly_contribution: The amount invested every month (C).
    - annual_return: Expected annual return rate.
    - target_value: The target future value that the investor wants to achieve.
    - time_horizon: The time horizon for the investment.

    Returns:
    - A boolean indicating if the goal is achievable (True/False) and the calculated future value (FV).
    """
    # Convert annual return to monthly return
    r = annual_return / 12
    # Calculate total months
    t = time_horizon * 12

    # Future value calculation
    FV = initial_investment * (1 + r) ** t + monthly_contribution * ((1 + r) ** t - 1) / r

    # Compare FV with the target value
    if FV >= target_value:
        return f"Achievable: True, Future Value: {FV:.2f}"
    else:
        return f"Achievable: False, Future Value: {FV:.2f}"


TOOLS = [check_achievable]
TOOL_MAPPING = {"check_achievable": check_achievable}


def interact_with_llm_and_tools(human_message: str, llm):
    print("Entered interact_with_llm_and_tools")
    llm = llm
    llm_with_tools_new = llm.bind_tools(TOOLS)

    messages = [HumanMessage(human_message)]

    llm_output = llm_with_tools_new.invoke(messages)
    messages.append(llm_output)

    for tool_call in llm_output.tool_calls:
        tool_name = tool_call["name"].lower()
        tool = TOOL_MAPPING.get(tool_name)

        if tool:
            tool_output = tool.invoke(tool_call["args"])
            messages.append(ToolMessage(tool_output, tool_call_id=tool_call["id"]))

    final_response = llm_with_tools_new.invoke(messages)
    print(f"getting the final response {final_response} from interact with llm and tools, exiting the function")
    return final_response
