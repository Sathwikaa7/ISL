import os
import json
import tensorflow as tf
import numpy as np
from PIL import Image

MODEL_PATH = "backend/models/isl_model.keras"
CLASS_PATH = "backend/models/alphabet_classes.json"
DATASET_PATH = "dataset/alphabet"


model = tf.keras.models.load_model(MODEL_PATH)

with open(CLASS_PATH) as f:
    class_names = json.load(f)

correct = 0
total = 0

for true_class in class_names:

    folder = os.path.join(DATASET_PATH, true_class)

    if not os.path.isdir(folder):
        continue

    print(f"Testing {true_class}...")

    for file in os.listdir(folder):

        if not file.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        path = os.path.join(folder, file)

        img = Image.open(path).convert("RGB")
        img = img.resize((224,224))

        # The saved model contains MobileNetV3 preprocessing.
        img = np.array(img, dtype=np.float32)
        img = np.expand_dims(img,0)

        prediction = model.predict(img, verbose=0)[0]

        pred_class = class_names[np.argmax(prediction)]

        if pred_class == true_class:
            correct += 1

        total += 1

print("\n========================")
print("Correct :", correct)
print("Total   :", total)
print("Accuracy:", round(correct/total*100,2), "%")
