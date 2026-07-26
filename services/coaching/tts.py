import os
import io
from dotenv import load_dotenv

from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
from gtts import gTTS


load_dotenv()


class TextToSpeech:

    def __init__(self):

        api_key = os.getenv("ELEVENLABS_API_KEY")

        if not api_key:
            raise Exception(
                "ELEVENLABS_API_KEY missing in .env file"
            )

        self.client = ElevenLabs(
            api_key=api_key
        )

        # ElevenLabs voice
        self.voice_id = "9bMxKyGi6BtYekefr6B5"

    def speak(self, text):

        cleaned = (text or "").strip()

        if not cleaned:
            return None

        audio_bytes = self._speak_elevenlabs(cleaned)

        if audio_bytes:
            return audio_bytes

        print("========== FALLING BACK TO gTTS ==========")
        return self._speak_gtts(cleaned)

    def _speak_elevenlabs(self, cleaned):

        try:

            audio = self.client.text_to_speech.convert(

                voice_id=self.voice_id,

                model_id="eleven_multilingual_v2",

                output_format="mp3_44100_128",

                text=cleaned,

                voice_settings=VoiceSettings(

                    stability=0.65,

                    similarity_boost=0.80,

                    style=0.35,

                    use_speaker_boost=True

                )

            )

            audio_bytes = b""

            for chunk in audio:
                audio_bytes += chunk

            print("ELEVENLABS TTS BYTES GENERATED:", len(audio_bytes))

            return audio_bytes

        except Exception as e:

            print("========== ELEVENLABS TTS ERROR ==========")
            print("status_code:", getattr(e, "status_code", None))
            print("body:", getattr(e, "body", None))

            return None

    def _speak_gtts(self, cleaned):

        try:
            buf = io.BytesIO()
            gTTS(text=cleaned, lang="en").write_to_fp(buf)
            audio_bytes = buf.getvalue()

            print("GTTS BYTES GENERATED:", len(audio_bytes))

            return audio_bytes

        except Exception as e:

            print("========== GTTS ERROR ==========")
            print(repr(e))

            return None