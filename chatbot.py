import os
import streamlit as st
from dotenv import load_dotenv
from ai_security.agent import run_agent
from ai_security.auth import (
    auth0_manager,
    is_authenticated,
    get_user_role,
)

load_dotenv()


def init_session_state():
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "access_token" not in st.session_state:
        st.session_state.access_token = None
    if "user_role" not in st.session_state:
        st.session_state.user_role = None
    if "messages" not in st.session_state:
        st.session_state.messages = []


def login_ui():
    st.markdown(
        """
        <style>
        .login-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 50px;
        }
        .stButton > button {
            width: 200px;
            height: 50px;
            font-size: 18px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="login-container">
            <h1>AI Security Chatbot</h1>
            <p>Please log in to continue</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    login_url = auth0_manager.get_login_url()
    st.markdown(
        f"""
        <div style="text-align: center;">
            <a href="{login_url}" target="_self">
                <button style="
                    background-color: #EB5424;
                    color: white;
                    padding: 12px 24px;
                    border: none;
                    border-radius: 4px;
                    font-size: 16px;
                    cursor: pointer;
                ">Log in with Auth0</button>
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def logout_ui():
    st.markdown(
        """
        <style>
        .user-info {
            padding: 10px;
            background-color: #f0f2f6;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    user_info = st.session_state.user_info
    user_role = st.session_state.user_role

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            f"""
            <div class="user-info">
                <strong>Logged in as:</strong> {user_info.get("name", user_info.get("email", "Unknown"))}<br>
                <strong>Role:</strong> {user_role}
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        logout_url = auth0_manager.get_logout_url()
        st.markdown(
            f'<a href="{logout_url}" target="_self"><button>Logout</button></a>',
            unsafe_allow_html=True,
        )


def handle_callback():
    query_params = st.query_params
    if "code" in query_params:
        code = query_params["code"]
        try:
            token_response = auth0_manager.get_token(code)
            access_token = token_response.get("access_token")
            user_info = auth0_manager.get_user_info(access_token)

            st.session_state.access_token = access_token
            st.session_state.user_info = user_info

            user_id = user_info.get("sub")
            roles = auth0_manager.get_user_roles(user_id, access_token)
            if auth0_manager.admin_role in roles:
                st.session_state.user_role = auth0_manager.admin_role
            else:
                st.session_state.user_role = auth0_manager.user_role

            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Authentication error: {str(e)}")
            return False
    return True


def main():
    st.set_page_config(
        page_title="AI Security Chatbot",
        page_icon="🔒",
    )

    init_session_state()

    if not is_authenticated():
        handle_callback()
        login_ui()
        return

    st.title("AI Security Chatbot")
    st.markdown("A LangGraph-powered chatbot backend with Auth0 authentication")

    logout_ui()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What would you like to ask?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = run_agent(prompt, st.session_state.messages[:-1], user_role=st.session_state.user_role)
                    st.markdown(response)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response}
                    )
                except PermissionError as e:
                    error_msg = str(e)
                    st.error(f"Access Denied: {error_msg}")
                    st.session_state.messages.append(
                        {"role": "assistant", "content": f"Access Denied: {error_msg}"}
                    )
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": f"Sorry, I encountered an error: {str(e)}",
                        }
                    )

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()


if __name__ == "__main__":
    main()
