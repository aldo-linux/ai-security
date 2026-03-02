import os
from typing import Annotated, Literal, Union
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel
import requests

load_dotenv()


class AgentState(BaseModel):
    messages: list = []


BASE_URL = "https://jsonplaceholder.typicode.com/users"


@tool
def get_all_users() -> str:
    """Get all users from the API. Use when user wants to list or see all users."""
    response = requests.get(BASE_URL)
    response.raise_for_status()
    users = response.json()
    return f"Found {len(users)} users:\n{users}"


@tool
def get_user(user_id: int) -> str:
    """Get a specific user by ID. Use when user wants to see details of a specific user."""
    response = requests.get(f"{BASE_URL}/{user_id}")
    if response.status_code == 404:
        return f"User with ID {user_id} not found"
    response.raise_for_status()
    return str(response.json())


@tool
def create_user(name: str, username: str, email: str, **kwargs) -> str:
    """Create a new user. Required: name, username, email. Optional: phone, website, address, company."""
    payload = {
        "name": name,
        "username": username,
        "email": email,
    }
    if kwargs.get("phone"):
        payload["phone"] = kwargs["phone"]
    if kwargs.get("website"):
        payload["website"] = kwargs["website"]
    if kwargs.get("address"):
        payload["address"] = kwargs["address"]
    if kwargs.get("company"):
        payload["company"] = kwargs["company"]

    response = requests.post(BASE_URL, json=payload)
    response.raise_for_status()
    return f"User created successfully:\n{response.json()}"


@tool
def update_user(user_id: int, name: str = None, email: str = None, **kwargs) -> str:
    """Update an existing user. Required: user_id. Optional: name, email, phone, website."""
    payload = {}
    if name:
        payload["name"] = name
    if email:
        payload["email"] = email
    if kwargs.get("phone"):
        payload["phone"] = kwargs["phone"]
    if kwargs.get("website"):
        payload["website"] = kwargs["website"]

    response = requests.put(f"{BASE_URL}/{user_id}", json=payload)
    if response.status_code == 404:
        return f"User with ID {user_id} not found"
    response.raise_for_status()
    return f"User updated successfully:\n{response.json()}"


@tool
def delete_user(user_id: int) -> str:
    """Delete a user by ID. Use when user wants to delete a user."""
    response = requests.delete(f"{BASE_URL}/{user_id}")
    if response.status_code == 404:
        return f"User with ID {user_id} not found"
    response.raise_for_status()
    return f"User with ID {user_id} deleted successfully"


tools = [get_all_users, get_user, create_user, update_user, delete_user]


def create_model() -> ChatOpenAI:
    model = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        temperature=0.7,
    )
    return model.bind_tools(tools)


def should_continue(state: AgentState) -> Literal["tools", "end"]:
    last_message = state.messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "end"


def call_model(state: AgentState):
    model = create_model()
    response = model.invoke(state.messages)
    return {"messages": [response]}


def create_agent():
    workflow = StateGraph(AgentState)

    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))

    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )
    workflow.add_edge("tools", "agent")

    return workflow.compile()


graph = create_agent()


def run_agent(user_input: str, history: list = None) -> str:
    if history is None:
        history = []

    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=user_input))

    result = graph.invoke({"messages": messages})
    return result["messages"][-1].content
