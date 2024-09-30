from langchain_core.prompts import ChatPromptTemplate
from smart.structured_output import CheckSpecificMesurableTimebound, CheckAchievable


def read_file(file_name):
    with open(f"prompt_repository/{file_name}.txt", "r") as file:
        string = file.read()
    return string


def check_smt(llm):
    structured_llm_smt_checker = llm.with_structured_output(CheckSpecificMesurableTimebound)
    smt_template = read_file("smt_template")

    smt_prompt = ChatPromptTemplate.from_messages(
        [("system", smt_template), ("human", "The investor goal :\n\n {goal}")]
    )
    check_smt = smt_prompt | structured_llm_smt_checker
    return check_smt


def achievable(llm):
    structured_llm_achievability_checker = llm.with_structured_output(CheckAchievable)
    achievable_template = """Extract the the future investment value and the is_achievable from the query"""
    achievable_prompt = ChatPromptTemplate.from_messages(
        [("system", achievable_template), ("human", "The query :\n\n {input}")]
    )
    achievable = achievable_prompt | structured_llm_achievability_checker
    return achievable


def accept(llm):
    accept_system = read_file("accept_system_template")
    accept_prompt = ChatPromptTemplate.from_messages(
        [("system", accept_system), ("human", "investment informations:\n\n {investment}")]
    )

    accept = accept_prompt | llm
    return accept


def refuse(llm):
    refuse_system = read_file("refuse_system_template")
    refuse_prompt = ChatPromptTemplate.from_messages(
        [("system", refuse_system), ("human", "investment informations:\n\n {investment}")]
    )

    refuse = refuse_prompt | llm
    return refuse
