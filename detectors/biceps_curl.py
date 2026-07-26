
from core.base_exercise import BaseExercise

class BicepsCurlDetector(BaseExercise):

    UP_THRESHOLD = 80
    DOWN_THRESHOLD = 140
    MIN_VISIBILITY = 0.7
    ELBOW_DRIFT_TOLERANCE = 0.06
    SWING_DRIFT_THRESHOLD = 0.10

    LEFT_SHOULDER = 11
    LEFT_ELBOW = 13
    LEFT_WRIST = 15
    RIGHT_SHOULDER = 12
    RIGHT_ELBOW = 14
    RIGHT_WRIST = 16

    def __init__(self):
        super().__init__()
        self._shoulder_x_baseline = None

    def reset(self) -> None:
        self.reps = 0
        self.stage = None
        self._shoulder_x_baseline = None

    def process(self, landmarks) -> dict:
        left_vis = landmarks[self.LEFT_ELBOW].visibility
        right_vis = landmarks[self.RIGHT_ELBOW].visibility

        if left_vis >= right_vis:
            shoulder_idx = self.LEFT_SHOULDER
            elbow_idx = self.LEFT_ELBOW
            wrist_idx = self.LEFT_WRIST
        else:
            shoulder_idx = self.RIGHT_SHOULDER
            elbow_idx = self.RIGHT_ELBOW
            wrist_idx = self.RIGHT_WRIST

        elbow_angle = self.calculate_angle(
            self.get_point(landmarks, shoulder_idx),
            self.get_point(landmarks, elbow_idx),
            self.get_point(landmarks, wrist_idx),
        )

        key_landmarks_visible = landmarks[shoulder_idx].visibility > self.MIN_VISIBILITY and landmarks[elbow_idx].visibility > self.MIN_VISIBILITY and landmarks[wrist_idx].visibility > self.MIN_VISIBILITY

        if key_landmarks_visible:
            if elbow_angle < self.UP_THRESHOLD:
                self.stage = "up"

            if elbow_angle > self.DOWN_THRESHOLD and self.stage == "up":
                self.stage = "down"
                self.reps += 1

        shoulder_x = landmarks[shoulder_idx].x
        elbow_x = landmarks[elbow_idx].x
        elbow_drift = abs(elbow_x - shoulder_x)

        if elbow_drift <= self.ELBOW_DRIFT_TOLERANCE:
            shoulder_status = "STABLE"
        else:
            shoulder_status = "ELBOW DRIFTING"

        # Swing detection using elbow drift from shoulder
        if elbow_drift > self.SWING_DRIFT_THRESHOLD:
            swing_status = "SWINGING"
        else:
            swing_status = "NO SWING"

        return {
            "reps": self.reps,
            "elbow_angle": int(elbow_angle),
            "shoulder_status": shoulder_status,
            "swing_status": swing_status,
        }

