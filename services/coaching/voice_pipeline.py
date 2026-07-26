import time
import base64
import streamlit as st
import streamlit.components.v1 as components


class VoicePipeline:

    def __init__(self, llm, tts):
        self.llm = llm
        self.tts = tts
        self.last_spoken_at = 0

    def _find_form_issue(self, exercise, metrics):
        if not metrics:
            return None

        if "issue" in metrics:
            return metrics["issue"]

        if exercise == "Squats":
            depth = metrics.get("depth_status", "")
            back_angle = metrics.get("back_angle", 180)

            if depth == "TOO HIGH":
                return (
                    "The user's squat depth is too high. "
                    "Tell them to go lower."
                )

            if isinstance(back_angle, (int, float)) and back_angle < 130:
                return "The user is leaning too far forward during squat."

        elif exercise == "Push-ups":
            alignment = metrics.get("body_alignment", "")
            hip_status = metrics.get("hip_status", "")

            if alignment == "Poor Form":
                return "The user's body alignment is incorrect."

            if hip_status == "SAGGING":
                return "The user's hips are sagging."

            if hip_status == "PIKED UP":
                return "The user's hips are too high."

        elif exercise == "Biceps Curls (Dumbbell)":
            swing = metrics.get("swing_status", "")
            shoulder = metrics.get("shoulder_status", "")

            if swing == "SWINGING":
                return (
                    "The user is swinging during curls. "
                    "Keep the body stable."
                )

            if shoulder == "ELBOW DRIFTING":
                return "The user's elbow is drifting away from the body."

        elif exercise == "Shoulder Press":
            back_arch = metrics.get("back_arch_status", "")

            if back_arch == "Excessive Arch":
                return "The user is arching the lower back excessively."

            if back_arch == "Slight Arch":
                return "Slight back arch detected."

        elif exercise == "Lunges":
            balance = metrics.get("balance_status", "")

            if balance == "OFF BALANCE":
                return "The user is losing balance during lunges."

        return None

    def process_event(self, event, exercise, metrics):
        issue = self._find_form_issue(exercise, metrics)

        now = time.time()

        major_events = [
            "workout_started",
            "set_completed",
            "workout_completed"
        ]

        if event not in major_events:
            if not issue:
                return None

            if now - self.last_spoken_at < 5:
                return None

        try:
            text = self.llm.give_feedback(event, issue)

            voice = self.tts.speak(text)

            self.last_spoken_at = now

            return voice, text

        except Exception:
            return None


def autoplay_audio(audio_bytes):
    if not audio_bytes:
        return

    b64 = base64.b64encode(audio_bytes).decode()

    html = f"""
    <audio id="coach-audio" autoplay>
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    <script>
        const audio = document.getElementById("coach-audio");
        const playPromise = audio.play();
        if (playPromise !== undefined) {{
            playPromise.catch((error) => {{
                console.log("Autoplay blocked:", error);
            }});
        }}
    </script>
    """

    components.html(html, height=0)