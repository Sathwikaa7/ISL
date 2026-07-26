from deep_translator import GoogleTranslator


class Translator:

    def __init__(self):

        self.translator = GoogleTranslator(
            source="en",
            target="te"
        )

    def translate(self, text):

        if text.strip() == "":
            return ""

        try:

            return self.translator.translate(text)

        except Exception as e:

            print("Translation Error:", e)

            return text