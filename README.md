# AI Security Chatbot

A Streamlit chatbot with a LangGraph agent backend featuring Auth0 authentication.

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

## Setup

1. **Install dependencies using uv:**

```bash
uv sync
```

2. **Configure environment variables:**

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL="https://api.openai.com/v1"

# Auth0 Configuration
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_CLIENT_ID=your_client_id
AUTH0_CLIENT_SECRET=your_client_secret
AUTH0_AUDIENCE=https://your-api-identifier
AUTH0_CALLBACK_URL=http://localhost:8501/callback
AUTH0_ADMIN_ROLE=admin
AUTH0_USER_ROLE=user
```

## Auth0 Setup

1. **Create an Auth0 Application:**
   - Go to [Auth0 Dashboard](https://manage.auth0.com/)
   - Create a Regular Web Application
   - Configure callback URLs: `http://localhost:8501/callback`
   - Configure allowed logout URLs: `http://localhost:8501`

2. **Create Roles:**
   - Go to User Management → Roles
   - Create `admin` role (can create, update, delete users)
   - Create `user` role (can view users)

3. **Assign Roles to Users:**
   - Add roles to users in the Auth0 dashboard

## Running the Application

Start the Streamlit app:

```bash
uv run streamlit run chatbot.py
```

The chatbot will be available at `http://localhost:8501`.

## Role-Based Access

| Tool | Required Role |
|------|---------------|
| `get_all_users` | user, admin |
| `get_user` | user, admin |
| `create_user` | admin |
| `update_user` | admin |
| `delete_user` | admin |

Users with the `admin` role can perform all operations. Users with only the `user` role can only view users.

## Project Structure

```
ai-security/
├── chatbot.py              # Streamlit UI
├── pyproject.toml         # Project configuration
├── README.md              # This file
└── src/
    └── ai_security/
        ├── __init__.py
        ├── agent.py       # LangGraph agent implementation
        └── auth.py       # Auth0 authentication
```
