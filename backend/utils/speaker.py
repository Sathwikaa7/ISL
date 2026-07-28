from pathlib import Path

from gtts import gTTS


class Speaker:
    """Create MP3 files for the browser to play.

    Playing audio on the Flask machine with ``playsound`` does not play it for
    the person using the web app.  The API saves a file instead and returns its
    URL to the browser.
    """

    SUPPORTED_LANGUAGES = {"en", "te"}

    def synthesize(self, text, language, output_path):
        if not text or not text.strip():
            raise ValueError("Text is required for speech synthesis.")
        if language not in self.SUPPORTED_LANGUAGES:
            raise ValueError("Language must be 'en' or 'te'.")

        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        gTTS(text=text.strip(), lang=language).save(str(destination))
        return destination
