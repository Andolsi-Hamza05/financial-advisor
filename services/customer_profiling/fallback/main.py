from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
import os

load_dotenv()
API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
os.environ["AZURE_OPENAI_ENDPOINT"] = ENDPOINT
os.environ["AZURE_OPENAI_API_KEY"] = API_KEY


def fallback(query, chat_history):

    llm = AzureChatOpenAI(
        azure_deployment="gpt-4o-mini",
        api_version="2023-03-15-preview",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )
    history = chat_history['history']
    profiling_state = chat_history['profiling_state']
    preferences_state = chat_history['preferences_state']

    router_template = f"""
    You are a fallback message manager, kind and very concise and not talkative.
    You will be provided with the history {history} of a chat between an investor and ai agent, the profiling_state(True or False) {profiling_state}
    the preferences_state(True or False) {preferences_state}.
    if the preferences_state is False and the investor is still giving you other goals, or talking about any other topic instead of giving you their investing preferences!
    explain to him that you are not tasked to provide him with any insights, you are just here to support him to define a goal and then share with you his investment preferences.
    else if the preferences_state is True, Ask him if he is sure he mentioned all his preferences about asset type, nature, companies, markets he wants to invest in or not to invest in!
    You'll be given also the latest message by the investor to understand better why this message is considered as fallback
    """

    route_prompt = ChatPromptTemplate.from_messages(
        [("system", router_template), ("human", " The latest message by the user :{fallback}")]
    )
    router = route_prompt | llm
    response = router.invoke({"fallback": query})
    return str(response.content)
