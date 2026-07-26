class WordBuilder:

    def __init__(self):
        self.current_word = ""
        self.last_prediction = ""
        self.last_added = ""
        self.same_count = 0
        self.threshold = 10

    def update(self, prediction):

        if prediction == "":
            return self.current_word

        # Count consecutive identical predictions
        if prediction == self.last_prediction:
            self.same_count += 1
        else:
            self.same_count = 1
            self.last_prediction = prediction

        # Accept only after prediction is stable
        if self.same_count >= self.threshold:

            # Prevent repeated letters
            if prediction != self.last_added:
                self.current_word += prediction
                self.last_added = prediction

            self.same_count = 0

        return self.current_word

    def clear(self):
        self.current_word = ""
        self.last_prediction = ""
        self.last_added = ""
        self.same_count = 0

    def backspace(self):
        if self.current_word:
            self.current_word = self.current_word[:-1]