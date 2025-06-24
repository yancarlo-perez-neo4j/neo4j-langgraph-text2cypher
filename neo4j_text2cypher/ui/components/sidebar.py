import streamlit as st


def sidebar() -> None:
    """
    The Streamlit app side bar.
    """

    # Display example questions in sidebar
    if st.session_state.get("example_questions"):
        st.sidebar.subheader("Example Questions")
        for i, question in enumerate(st.session_state.example_questions):
            # Truncate long questions for better display
            display_text = question[:60] + "..." if len(question) > 60 else question
            if st.sidebar.button(display_text, key=f"sidebar_example_{i}", help=question):
                st.session_state["current_question"] = question
        
        st.sidebar.divider()

    # Reset chat button
    if len(st.session_state.get("messages", list())) > 0:
        if st.sidebar.button("Reset Chat", type="primary"):
            st.session_state["messages"] = []
            if "current_question" in st.session_state:
                del st.session_state["current_question"]
            st.rerun()
