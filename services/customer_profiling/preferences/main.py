from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import os


load_dotenv()
API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
os.environ["AZURE_OPENAI_ENDPOINT"] = ENDPOINT
os.environ["AZURE_OPENAI_API_KEY"] = API_KEY


class Preferences(BaseModel):
    preferences: list[str] = Field(
        description="A list of natural language texts(each text is a clearly defined preference)"
    )
    confirmation: str = Field(
        default="False",
        description="True if the investor gave his preferences, else it is False"
    )


def preferences_confirmation(query, chat_history):
    llm = AzureChatOpenAI(
        azure_deployment="gpt-4o-mini",
        api_version="2023-03-15-preview",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )
    structured_llm_preferences = llm.with_structured_output(Preferences)
    router_template = """
    You are a financial advisor helpful but not talkative. Be concise, kind but dont talk too much.
    You are tasked to get the preferences of the investor.
    If the investor give you his preferences thank him and ask him to wait till the asset selection and portfolio optimization complete workflow is completed successfully.
    Else Tell him to provide you with his preferences.
    Example of investor preferences: I want to invest in halal investment, I dont want to invest in industry like healthcare more than others! I prefer to invest in arabic countries if possible
    you should provide an output :
    preferences ["halal investment", "prefer healtchare sector/industry related companies", "prefer arabic countries"]
    confirmation: "True"
    Another example of not clearly defined preferences: I want to invest in good companies and that can give me a lot of wealth
    you should provide an output :
    preferences: []
    confirmation: "False"
    """

    preferences_prompt = ChatPromptTemplate.from_messages(
        [("system", router_template), ("human", "The investor preferences :\n\n {preferences}")]
    )
    preferences = preferences_prompt | structured_llm_preferences
    response = preferences.invoke({"preferences": query})
    if response.confirmation == "True":
        chat_history['preferences_state'] = True
    return response
