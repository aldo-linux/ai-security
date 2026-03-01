import streamlit as st
from ai_security.agent import run_agent

st.title("AI Security Chatbot")
st.markdown("A LangGraph-powered chatbot backend")

if "messages" not in st.session_state:
    st.session_state.messages = []

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
                response = run_agent(prompt, st.session_state.messages[:-1])
                st.markdown(response)
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
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
