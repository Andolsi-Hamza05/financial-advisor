from dotenv import load_dotenv
import os
from smart.workflow import set_agentic_workflow


def smart_main(initial_state):
    print("Entering main function with inital_state")
    load_dotenv()
    API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
    ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
    os.environ["AZURE_OPENAI_ENDPOINT"] = ENDPOINT
    os.environ["AZURE_OPENAI_API_KEY"] = API_KEY
    print("Exported env variables")
    app = set_agentic_workflow()
    print("invoking the inital state with the workflow app")
    result = app.invoke(initial_state)
    return result
