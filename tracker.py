import streamlit as st
import random
import time


def step_tracker(goal_steps):

    st.subheader("🚶 Walking Progress Tracker")

    if goal_steps is None:
        st.warning("Generate recommendation first.")
        return

    # ---------------- SESSION STATE ----------------
    if "current_steps" not in st.session_state:
        st.session_state.current_steps = 0

    if "tracking" not in st.session_state:
        st.session_state.tracking = False

    if "paused" not in st.session_state:
        st.session_state.paused = False

    # ---------------- BUTTONS ----------------
    col1, col2, col3 = st.columns(3)

    if col1.button("▶ Start"):
        st.session_state.tracking = True
        st.session_state.paused = False

    if col2.button("⏸ Pause"):
        st.session_state.paused = True

    if col3.button("🔄 Reset"):
        st.session_state.current_steps = 0
        st.session_state.tracking = False
        st.session_state.paused = False

    # ---------------- PROGRESS ----------------
    progress = st.session_state.current_steps / goal_steps
    progress = min(progress, 1.0)

    st.progress(progress)

    st.write(
        f"Steps: {st.session_state.current_steps} / {goal_steps}"
    )

    calories = st.session_state.current_steps * 0.04
    st.write(f"Calories Burned: {calories:.1f} kcal")

    remaining = goal_steps - st.session_state.current_steps
    st.write(f"Remaining Steps: {max(remaining,0)}")

    # ---------------- TRACKING LOGIC ----------------
    if st.session_state.tracking and not st.session_state.paused:

        time.sleep(1)

        st.session_state.current_steps += random.randint(20, 50)

        if st.session_state.current_steps >= goal_steps:
            st.session_state.current_steps = goal_steps
            st.success("🎉 Goal Completed!")
            st.session_state.tracking = False

        st.rerun()