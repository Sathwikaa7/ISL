from collections import deque, Counter

class PredictionBuffer:

    def __init__(self, size=10):
        self.buffer = deque(maxlen=size)

    def update(self, prediction):

        self.buffer.append(prediction)

        if len(self.buffer) < self.buffer.maxlen:
            return None

        most_common = Counter(self.buffer).most_common(1)[0][0]

        return most_common

    def clear(self):
        self.buffer.clear()