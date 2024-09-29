from fastapi import FastAPI
from smart.main import main

app = FastAPI()


@app.post("/check_smart")
async def process_state(initial_state: dict):
    result = main(initial_state)
    return {"answer": result}
