from dotenv import load_dotenv
import os
from smart.workflow import set_agentic_workflow
import logging


def main(initial_state):
    logging.info("Entering main function with inital_state")
    load_dotenv()
    API_KEY = os.getenv('AZURE_OPENAI_API_KEY')
    ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
    os.environ["AZURE_OPENAI_ENDPOINT"] = ENDPOINT
    os.environ["AZURE_OPENAI_API_KEY"] = API_KEY
    logging.info("Exported env variables")
    app = set_agentic_workflow()
    logging.info("invoking the inital state with the workflow app")
    result = app.invoke(initial_state)
    return result.get('final_response')
