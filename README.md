# AI Security Chatbot

A Streamlit chatbot with a LangGraph agent backend.

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

## Setup

1. **Install dependencies using uv:**

```bash
uv sync
```

2. **Configure environment variables:**

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
```

Or export them in your shell:

```bash
export OPENAI_API_KEY=your_openai_api_key_here
export OPENAI_MODEL=gpt-4o-mini
```

## Running the Application

Start the Streamlit app:

```bash
uv run streamlit run chatbot.py
```

The chatbot will be available at `http://localhost:8501`.

## Project Structure

```
ai-security/
├── chatbot.py              # Streamlit UI
├── pyproject.toml         # Project configuration
├── README.md              # This file
└── src/
    └── ai_security/
        ├── __init__.py
        └── agent.py       # LangGraph agent implementation
```
