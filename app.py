import streamlit as st
from script import call_openrouter

st.set_page_config(
    page_title="OpenRouter Chat UI",
    page_icon="🤖",
    layout="wide"
)

st.title("Prompt your Query")

# Session state for memory
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# User input box
user_prompt = st.text_input(
    "Enter your prompt:",
    placeholder="Type your question here..."
)

# Send button
if st.button("Send"):

    if user_prompt:

        # Spinner while API runs
        with st.spinner("Generating response... 🤖"):

            # Call API
            response = call_openrouter(user_prompt)

        # Store history
        st.session_state.chat_history.append(
            {
                "question": user_prompt,
                "answer": response
            }
        )

# Display Chat History
st.subheader("Conversation History")

for chat in st.session_state.chat_history:

    st.markdown(
        f"**User:** {chat['question']}"
    )

    st.markdown(
        f"**Assistant:** {chat['answer']}"
    )

    st.markdown("---")