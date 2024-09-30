from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, field_validator
import os


load_dotenv()
API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
os.environ["AZURE_OPENAI_ENDPOINT"] = ENDPOINT
os.environ["AZURE_OPENAI_API_KEY"] = API_KEY


class Router(BaseModel):
    endpoint: str = Field(
        description="The endpoint to route the request to"
    )

    @field_validator('endpoint')
    def validate_endpoint(cls, value):
        allowed_endpoints = ["check_smart", "fallback", "preferences_confirmation"]
        if value not in allowed_endpoints:
            raise ValueError(f"Invalid endpoint. Allowed endpoints are: {allowed_endpoints}")
        return value


def decide_route(query):
    load_dotenv()

    llm = AzureChatOpenAI(
        azure_deployment="gpt-4o-mini",
        api_version="2023-03-15-preview",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )
    print("The router is deciding...")
    structured_llm = llm.with_structured_output(Router)
    router_template = """
    You are tasked to route the discussion to one of the three endpoints:
    "check_smart": if the query is describing an investment goal mentioning what he wants to invest in, or how much to invest periodically!
    "preferences_confirmation": If the user is describing an investment preference(for instance i don't want to invest in IT industry, in companies that support a war!
    or i want to invest in companies supporting something, in european countries,) Accept anything that is related to investor preferences in term of investing
    "fallback": If the investor is trying to chat or ask anything else
    ## EXAMPLES:
    I want to buy a house worth 500 000$
    route to "check_smart"
    I want to invest in companies that respect nature!
    route to "preferences_confirmation"
    I want to invest in assets that are halal!
    route to "preferences_confirmation"
    I love investing and knowing about cool investing trends!
    route to "preferences_confirmation"
    """

    route_prompt = ChatPromptTemplate.from_messages(
        [("system", router_template), ("human", "The investor query :\n\n {query}")]
    )
    router = route_prompt | structured_llm
    response = router.invoke({"query": query})
    print(f"the router decided to route to {str(response.endpoint)}")
    return str(response.endpoint)
