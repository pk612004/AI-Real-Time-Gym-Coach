from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import os
import time
import pandas as pd
from services.auth.login_wall import render_login_wall
from services.state.session_defaults import initial_session_defaults
from services.config.workout_config import EXERCISE_OPTIONS
from services.ui.style_loader import load_css, inject_local_font, inject_webrtc_styles
from services.persistence.exercise_repository import init_db
from services.persistence.exercise_repository import add_exercise
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from services.vision.exercise_video_processor import VideoProcessorClass
from services.tracking.metrics import sync_metrics_update
from services.persistence.exercise_repository import get_users_exercises
from groq import Groq
from services.coaching.llm import LLMCoach
from services.coaching.tts import TextToSpeech
from services.coaching.voice_pipeline import VoicePipeline, autoplay_audio



EXERCISE_METRIC_MAP = {
    "Squats": [
        ("Knee Angle", "knee_angle", "°"),
        ("Back Angle", "back_angle", "°"),
        ("Depth Status", "depth_status", ""),
    ],
    "Push-ups": [
        ("Elbow Angle", "elbow_angle", "°"),
        ("Body Alignment", "body_alignment", ""),
        ("Hip Position", "hip_status", ""),
    ],
    "Biceps Curls (Dumbbell)": [
        ("Elbow Angle", "elbow_angle", "°"),
        ("Shoulder Stability", "shoulder_status", ""),
        ("Swing Detection", "swing_status", ""),
    ],
    "Shoulder Press": [
        ("Elbow Angle", "elbow_angle", "°"),
        ("Arm Extension", "extension_status", ""),
        ("Back Arch", "back_arch_status", ""),
    ],
    "Lunges": [
        ("Front Knee Angle", "front_knee_angle", "°"),
        ("Torso Angle", "torso_angle", "°"),
        ("Balance Status", "balance_status", ""),
    ],
}

def _row(label, value, accent=False):
    cls = "value accent" if accent else "value"
    return f'<div class="ai-row"><span class="label">{label}</span><span class="{cls}">{value}</span></div>'


def _status_pill(active, label):
    cls = "active" if active else "idle"
    return f'<span class="status-pill {cls}"><span class="status-dot"></span>{label}</span>'


def render_idle_dashboard():
    """Dashboard card shown before a workout is started."""
    html = f"""
    <div class="ai-dashboard">
      <div class="ai-dashboard-header">
        <span class="title">AI Dashboard</span>
        {_status_pill(False, "Idle")}
      </div>
      <div class="ai-dashboard-body">
        {_row("Exercise", "—")}
        {_row("Reps", "0")}
        {_row("Sets", "0 / 0")}
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_active_dashboard():
    """Dashboard card shown while a workout is in progress. Reads the exact
    same st.session_state values the original Progress/metric widgets used."""
    exercise = st.session_state.get("exercise_type")
    total_reps = st.session_state.get("reps")
    current_set_reps = st.session_state.get("current_set_reps")
    reps_per_set = st.session_state.get("reps_per_set")
    sets_completed = st.session_state.get("sets_completed")
    target_sets = st.session_state.get("target_sets")

    main_rows = "".join([
        _row("Exercise", exercise, accent=True),
        _row("Reps", f"{total_reps}"),
        _row("Current Set", f"{current_set_reps} / {reps_per_set}"),
        _row("Sets", f"{sets_completed} / {target_sets}"),
    ])

    html = f"""
    <div class="ai-dashboard">
      <div class="ai-dashboard-header">
        <span class="title">AI Dashboard</span>
        {_status_pill(True, "Tracking")}
      </div>
      <div class="ai-dashboard-body">
        {main_rows}
      </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

    metric_rows = EXERCISE_METRIC_MAP.get(exercise)
    if metric_rows:
        rows_html = ""
        for label, key, suffix in metric_rows:
            val = st.session_state.get(key, "—")
            rows_html += _row(label, f"{val}{suffix}" if val != "—" else val)

        form_html = f"""
        <div class="ai-dashboard">
          <div class="ai-dashboard-header">
            <span class="title">Form Metrics</span>
          </div>
          <div class="ai-dashboard-body">
            {rows_html}
          </div>
        </div>
        """
        st.markdown(form_html, unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_icon="🏋️‍♀️",
        page_title="AI Real-time GYM Coach",
        initial_sidebar_state="expanded",
        layout="centered"
    )

    load_css(os.path.join(os.getcwd(), "static", "style.css"))
    inject_local_font(os.path.join(os.getcwd(), "static", "AdobeClean.otf"), "AdobeClean")

    init_db()

    # FIX 1: session defaults must exist BEFORE login wall runs,
    # otherwise st.session_state.username etc. may not exist yet.
    initial_session_defaults()

    if not render_login_wall():
        return

    if "voice_pipeline" not in st.session_state:
        try:
            print("========== INITIALIZING AI COACH ==========")

            # FIX 2: fail loudly if GROQ_API_KEY is missing
            api_key = os.getenv("GROQ_API_KEY", "")

            print("API KEY FOUND:", bool(api_key))

            if not api_key:
                raise Exception(
                    "GROQ_API_KEY missing. Add it to .env file"
                )

            groq_client = Groq(api_key=api_key)
            print("GROQ CLIENT CREATED")

            llm_coach = LLMCoach(groq_client)
            print("LLM CREATED")

            tts = TextToSpeech()
            print("TTS CREATED")

            st.session_state.voice_pipeline = VoicePipeline(llm_coach, tts)
            print("VOICE PIPELINE CREATED:", st.session_state.voice_pipeline)

        except Exception as e:
            print("========== VOICE PIPELINE INIT ERROR ==========")
            print(repr(e))
            st.session_state.voice_pipeline = None

    workout_started = st.session_state.get("workout_started", False)

    with st.sidebar:
        st.title("🏋️‍♂️ AI Personal Trainer")

        if st.session_state.username:
            st.caption(f"👤 Login as {st.session_state.username}")

        st.divider()

        st.subheader("Workout Plan")

        if not workout_started:
            plan_exercise = st.selectbox("Exercise", options=EXERCISE_OPTIONS, key="plan_exercise")

            plan_sets = st.number_input("Sets", min_value=0, max_value=50, key="plan_sets", step=1)

            plan_reps = st.number_input("Reps per Set", min_value=0, max_value=50, key="plan_reps", step=1)

            st.markdown("")

            start_session_button = st.button("Start Workout", width="stretch", key="start_session_button")

            if start_session_button:
                st.session_state.exercise_type = plan_exercise
                st.session_state.target_sets = int(plan_sets)
                st.session_state.reps_per_set = int(plan_reps)
                st.session_state.reps = 0
                st.session_state.current_set_reps = 0
                st.session_state.sets_completed = 0
                st.session_state.workout_completed = False
                st.session_state.last_saved_sets_completed = 0
                st.session_state.workout_started = True
                st.session_state.set_cycle_started_at = time.time()
                st.session_state.last_saved_sets_completed = 0

                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_started",
                        exercise=plan_exercise,
                        metrics={}
                    )

                    if result:
                        st.session_state.audio_to_play, st.session_state.coach_feedback = result

                st.session_state.last_notified_sets_completed = 0
                st.session_state.last_notified_workout_complete = False
                st.rerun()

            st.markdown("")
            render_idle_dashboard()
        else:
            exercise = st.session_state.get("exercise_type")
            sets = st.session_state.get("target_sets")
            reps = st.session_state.get("reps_per_set")

            st.info(f"**{exercise}** -- {sets} Sets / {reps} Reps")

            end_session_button = st.button("End Workout", key="end_session_button", width="stretch")

            if end_session_button:

                exercise = st.session_state.exercise_type

                total_reps = st.session_state.reps
                total_sets = st.session_state.sets_completed

                duration = int(
                    time.time() -
                    st.session_state.set_cycle_started_at
                )

                if total_reps > 0:

                    add_exercise(
                        st.session_state.user_id,
                        exercise,
                        total_reps,
                        total_sets,
                        duration,
                    )

                st.session_state.workout_started = False

                if st.session_state.voice_pipeline:

                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_completed",
                        exercise=exercise,
                        metrics={}
                    )

                    if result:
                        st.session_state.audio_to_play, st.session_state.coach_feedback = result

                st.rerun()

        if workout_started:
            st.divider()
            st.subheader("Live Metrics")
            render_active_dashboard()

    st.title("AI Real-time GYM Coach")
    st.markdown("#### Real-time pose detection with proactive AI voice coaching")

    if st.session_state.get("audio_to_play"):
        autoplay_audio(st.session_state.audio_to_play)

    if st.session_state.get("coach_feedback"):
        st.markdown("")
        st.success(f"🤖 **Coach:** {st.session_state.coach_feedback}")

    if not workout_started:
        st.markdown(
            """
            <div style="
                border: 10px dashed #444;
                border-radius: 0px;
                padding: 48px 32px;
                text-align: center;
                color: #888;
                margin-top: 32px;
                margin-bottom: 32px;
            ">
                <h2 style="color:#ccc; margin-bottom:8px;">👈 Set your workout plan</h2>
                <p style="font-size:1.05rem;">
                    Choose your exercise, sets and reps in the sidebar,<br>
                    then click <strong>Start Workout</strong> to activate the camera and AI coach.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        context = webrtc_streamer(
            key="exercise-analysis",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=VideoProcessorClass,
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
            media_stream_constraints={
                "video": True,
                "audio": False
            },
            async_processing=True
        )

        sync_metrics_update(context)

        if context.state.playing:
            time.sleep(0.25)
            st.rerun()

        inject_webrtc_styles()

    st.divider()

    st.markdown("#### Workout History")

    user_id = st.session_state.get("user_id", 0)

    if isinstance(user_id, int):
        history_rows = get_users_exercises(user_id)

        arr = [
            {
                "Exercise": row['exercise_name'],
                "Reps": row['reps'],
                "Sets": row['sets'],
                "Time (sec)": row['time'],
                "Date": row['created_at']
            }
            for row in history_rows
        ]

        df = pd.DataFrame(arr)

        if not df.empty:
            df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d %H:%M")

            df.index += 1

            st.table(df, border="horizontal")
        else:
            st.info("No workout history found.")


if __name__ == "__main__":
    main()