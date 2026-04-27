import streamlit as st
from script import call_openrouter

st.set_page_config(
    page_title="Resume Search UI",
    layout="wide"
)

st.title("Prompt your Query")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_prompt = st.text_input(
    "Enter your prompt:",
    placeholder="Type your question here..."
)

if st.button("Send"):
    if user_prompt:
        with st.spinner("Generating response..."):
            response = call_openrouter(user_prompt)

        st.session_state.chat_history.append(
            {
                "question": user_prompt,
                "answer": response
            }
        )

st.subheader("Conversation History")

for chat in st.session_state.chat_history:
    st.markdown(f"**User:** {chat['question']}")

    answer = chat["answer"]
    if isinstance(answer, dict):
        st.markdown(f"**Query:** {answer.get('query', chat['question'])}")
        st.markdown("**Assistant Summary:**")
        st.write(answer.get("summary", "No summary available."))

        st.markdown("**Generated SQL:**")
        st.code(answer.get("sql", "N/A"), language="sql")

        results = answer.get("results", [])
        st.markdown(f"**Retrieved Rows:** {len(results)}")
        if results:
            with st.expander("View retrieved rows"):
                st.json(results)

        stored_at = answer.get("stored_at")
        if stored_at:
            st.caption(f"Saved latest retrieval to: {stored_at}")
    else:
        st.markdown(f"**Assistant:** {answer}")

    st.markdown("---")