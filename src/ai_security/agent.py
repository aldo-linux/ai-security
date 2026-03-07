import os
import json
from typing import Optional
from dotenv import load_dotenv
import requests
import openai

from ai_security.auth import validate_tool_access_with_context

load_dotenv()


BASE_URL = "https://jsonplaceholder.typicode.com/users"

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_all_users",
            "description": "Get all users from the API. Use when user wants to list or see all users.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user",
            "description": "Get a specific user by ID. Use when user wants to see details of a specific user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "description": "The user ID to retrieve",
                    },
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_user",
            "description": "Create a new user. Required: name, username, email. Optional: phone, website, address, company.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Full name of the user"},
                    "username": {"type": "string", "description": "Username"},
                    "email": {"type": "string", "description": "Email address"},
                    "phone": {"type": "string", "description": "Phone number"},
                    "website": {"type": "string", "description": "Website URL"},
                    "address": {"type": "string", "description": "Address"},
                    "company": {"type": "string", "description": "Company name"},
                },
                "required": ["name", "username", "email"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_user",
            "description": "Update an existing user. Required: user_id. Optional: name, email, phone, website.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "description": "The user ID to update",
                    },
                    "name": {"type": "string", "description": "Full name of the user"},
                    "email": {"type": "string", "description": "Email address"},
                    "phone": {"type": "string", "description": "Phone number"},
                    "website": {"type": "string", "description": "Website URL"},
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_user",
            "description": "Delete a user by ID. Use when user wants to delete a user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "description": "The user ID to delete",
                    },
                },
                "required": ["user_id"],
            },
        },
    },
]


def get_all_users() -> str:
    """Get all users from the API."""
    response = requests.get(BASE_URL)
    response.raise_for_status()
    users = response.json()
    return f"Found {len(users)} users:\n{users}"


def get_user(user_id: int) -> str:
    """Get a specific user by ID."""
    response = requests.get(f"{BASE_URL}/{user_id}")
    if response.status_code == 404:
        return f"User with ID {user_id} not found"
    response.raise_for_status()
    return str(response.json())


def create_user(name: str, username: str, email: str, **kwargs) -> str:
    """Create a new user."""
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


def update_user(user_id: int, name: str = None, email: str = None, **kwargs) -> str:
    """Update an existing user."""
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


def delete_user(user_id: int) -> str:
    """Delete a user by ID."""
    response = requests.delete(f"{BASE_URL}/{user_id}")
    if response.status_code == 404:
        return f"User with ID {user_id} not found"
    response.raise_for_status()
    return f"User with ID {user_id} deleted successfully"


TOOL_FUNCTIONS = {
    "get_all_users": get_all_users,
    "get_user": get_user,
    "create_user": create_user,
    "update_user": update_user,
    "delete_user": delete_user,
}


def create_client() -> openai.OpenAI:
    return openai.OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    )


def execute_tool(tool_name: str, arguments: dict, user_role: Optional[str]) -> str:
    if not validate_tool_access_with_context(tool_name, user_role):
        raise PermissionError(
            f"Access denied: You don't have permission to execute '{tool_name}'. "
            f"Admin role is required for this operation."
        )

    tool_func = TOOL_FUNCTIONS.get(tool_name)
    if not tool_func:
        return f"Error: Unknown tool '{tool_name}'"

    try:
        return tool_func(**arguments)
    except Exception as e:
        return f"Error executing tool: {str(e)}"


def run_agent(user_input: str, history: list = None, user_role: str = None) -> str:
    """Run the agent with user context.

    Args:
        user_input: The user's input message
        history: Previous conversation history
        user_role: The authenticated user's role (e.g., 'admin', 'user')
    """
    if history is None:
        history = []

    client = create_client()
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append({"role": "user", "content": msg["content"]})
        elif msg["role"] == "assistant":
            messages.append({"role": "assistant", "content": msg["content"]})

    messages.append({"role": "user", "content": user_input})

    max_iterations = 10
    for _ in range(max_iterations):
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            temperature=0.7,
        )

        choice = response.choices[0]
        message = choice.message

        if message.tool_calls:
            messages.append(
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in message.tool_calls
                    ],
                }
            )

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                tool_result = execute_tool(tool_name, arguments, user_role)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result,
                    }
                )
        else:
            return message.content

    return "Agent reached maximum iterations"
