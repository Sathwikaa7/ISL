from gtts import gTTS
from playsound import playsound
import os


class Speaker:

    def speak(self, text):

        if text.strip() == "":
            return

        filename = "voice.mp3"

        # Generate speech
        tts = gTTS(
            text=text,
            lang="en"
        )

        tts.save(filename)

        # Play speech
        playsound(filename)

        # Delete temporary file
        if os.path.exists(filename):
            os.remove(filename)


# ==========================
# Test Speaker
# ==========================

if __name__ == "__main__":

    speaker = Speaker()

    print("===== Text To Speech Test =====")
    print("Type 'q' to quit.\n")

    while True:

        text = input("Enter text: ")

        if text.lower() == "q":
            break

        speaker.speak(text)

    print("\nSpeaker Closed.")