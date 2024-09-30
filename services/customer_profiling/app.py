from fastapi import FastAPI, APIRouter
from smart.main import smart_main
from router.main import decide_route
from preferences.main import preferences_confirmation
from fallback.main import fallback


app = FastAPI()

chat_history = {
    "introduction_state": False,
    "profiling_state": False,
    "preferences_state": False,
    "history": "chat history between ai financial advisor and the investor : ",
    "risk_aversion": 2,
    "annual_return": 0.05,
    "allocation": None
}

router = APIRouter()


async def check_smart(initial_state: dict, chat_history: list):
    result = smart_main(initial_state)
    if result.get('is_achievable') == "True":
        chat_history['profiling_state'] = True
        print("changing profiling state to True")
    return {"answer": result.get('final_response')}


async def confirm_preferences(initial_state: dict, chat_history: list):
    result = preferences_confirmation(initial_state["query"], chat_history)
    if result.confirmation == "False":
        answer = "You should provide more specific preferences that concern the assets we are going to invest on"
    else:
        answer = f"do you confirm these preferences {result.preferences}"
    return {"answer": answer}


async def send_fallback(initial_state: dict, chat_history: list):
    result = fallback(initial_state["query"], chat_history)
    return {"answer": result}


@router.post("/initialize")
async def initialize_chat(data: dict):
    chat_history["introduction_state"] = True
    risk_aversion = data['risk_aversion_estimate'][0]
    chat_history['risk_aversion'] = risk_aversion
    if risk_aversion <= 1:
        chat_history['annual_return'] = 0.08
        chat_history['allocation'] = {"Stocks": 0.8, "Commodities": 0.05, "ETFs": 0.05, "Mutual Funds": 0.05, "Bonds": 0.05, "Cash": 0}
    elif risk_aversion > 1 and risk_aversion <= 5:
        chat_history['annual_return'] = 0.07
        chat_history['allocation'] = {"Stocks": 0.6, "Commodities": 0.1, "ETFs": 0.2, "Mutual Funds": 0.05, "Bonds": 0.05, "Cash": 0}
    elif risk_aversion > 5 and risk_aversion <= 10:
        chat_history['annual_return'] = 0.06
        chat_history['allocation'] = {"Stocks": 0.5, "Commodities": 0.1, "ETFs": 0.15, "Mutual Funds": 0.1, "Bonds": 0.15, "Cash": 0}
    elif risk_aversion > 10 and risk_aversion <= 15:
        chat_history['annual_return'] = 0.05
        chat_history['allocation'] = {"Stocks": 0.4, "Commodities": 0.05, "ETFs": 0.2, "Mutual Funds": 0.1, "Bonds": 0.15, "Cash": 0.1}
    elif risk_aversion > 15 and risk_aversion <= 20:
        chat_history['annual_return'] = 0.04
        chat_history['allocation'] = {"Stocks": 0.3, "Commodities": 0.05, "ETFs": 0.2, "Mutual Funds": 0.2, "Bonds": 0.1, "Cash": 0.05}
    elif risk_aversion > 20 and risk_aversion <= 30:
        chat_history['annual_return'] = 0.03
        chat_history['allocation'] = {"Stocks": 0.2, "Commodities": 0.0, "ETFs": 0.2, "Mutual Funds": 0.2, "Bonds": 0.1, "Cash": 0.1}
    elif risk_aversion > 30 and risk_aversion <= 50:
        chat_history['annual_return'] = 0.02
        chat_history['allocation'] = {"Stocks": 0.1, "Commodities": 0.0, "ETFs": 0.2, "Mutual Funds": 0.2, "Bonds": 0.2, "Cash": 0.1}
    elif risk_aversion > 50:
        chat_history['annual_return'] = 0.01
        chat_history['allocation'] = {"Stocks": 0.0, "Commodities": 0.0, "ETFs": 0.3, "Mutual Funds": 0.3, "Bonds": 0.2, "Cash": 0.2}
    print(f"changed : risk aversion {chat_history['risk_aversion']} annual return: {chat_history['annual_return']}")
    return {"message": "Introduction state updated"}


@router.post("/router")
async def route_request(initial_state: dict):

    endpoint = decide_route(initial_state)

    if endpoint == "check_smart":
        if chat_history['profiling_state']:
            response = await send_fallback(initial_state, chat_history)
        else:
            response = await check_smart(initial_state, chat_history)
        chat_history["history"] = chat_history["history"] + response['answer']
    elif endpoint == "preferences_confirmation":
        response = await confirm_preferences(initial_state, chat_history)
        chat_history["history"] = chat_history["history"] + response['answer']
    elif not chat_history['profiling_state']:
        response = await send_fallback(initial_state, chat_history)

    return response


app.include_router(router)
