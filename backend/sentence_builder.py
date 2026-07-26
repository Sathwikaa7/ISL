class SentenceBuilder:

    def __init__(self):
        self.sentence = []
        self.last_word = ""

    def add_word(self, word):

        if word == "":
            return

        # Prevent duplicate consecutive words
        if word == self.last_word:
            return

        self.sentence.append(word)
        self.last_word = word

    def get_sentence(self):
        return " ".join(self.sentence)

    def clear(self):
        self.sentence = []
        self.last_word = ""

    def backspace(self):
        if self.sentence:
            self.sentence.pop()

            if self.sentence:
                self.last_word = self.sentence[-1]
            else:
                self.last_word = ""