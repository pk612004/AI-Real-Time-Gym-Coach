

import streamlit as st
from services.persistence.exercise_repository import get_or_create_user

def render_login_wall():
    if st.session_state.get("user_id") is not None:
        return True

    st.markdown(
        """
        <div style="text-align:center; margin-top: 2rem; margin-bottom: 2rem;">
            <h1 style="margin-bottom: 0.6rem;">🏋️‍♂️ AI Real-time GYM Trainer</h1>
            <h3 style="font-weight:600; margin:0; line-height:1.6;">
                Welcome!<br>
                Enter your name to begin your<br>
                AI-powered workout.
            </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="e.g. prakash_kumar")
            submit_button = st.form_submit_button("Start Training", width="stretch")

        if submit_button:
            if not username:
                st.error("Name cannot be empty.")
                return False

            user = get_or_create_user(username)

            st.session_state["user_id"] = user["id"]
            st.session_state["username"] = user["username"]

            st.rerun()

    return False