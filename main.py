from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.purpose_graph import graph
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_invoke(request: ChatRequest):
    state = {"messages": [{"role": "user", "content": request.message}]}
    result = graph.invoke(state)
    response = result["messages"][-1].content
    return {"response": response}