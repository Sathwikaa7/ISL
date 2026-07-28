import json
import cv2
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt

# ----------------------------
# Load Model
# ----------------------------

MODEL_PATH = "backend/models/isl_model.keras"
CLASS_PATH = "backend/models/alphabet_classes.json"

model = tf.keras.models.load_model(MODEL_PATH)

with open(CLASS_PATH, "r") as f:
    class_names = json.load(f)

print("Model Loaded Successfully!")
print("Classes:", class_names)

# ----------------------------
# Test Image
# ----------------------------

IMAGE_PATH = r"D:\SLD\test_images\B2.jpeg"

image = cv2.imread(IMAGE_PATH)

if image is None:
    raise Exception("Image not found!")

display = image.copy()

# Convert to RGB
rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
rgb = cv2.resize(rgb, (224, 224))

# =====================================================
# Preview Training Augmentation
# =====================================================

data_augmentation = tf.keras.Sequential([
    tf.keras.layers.RandomRotation(0.15),
    tf.keras.layers.RandomZoom(0.15),
    tf.keras.layers.RandomTranslation(0.08, 0.08),
    tf.keras.layers.RandomContrast(0.2),
])

plt.figure(figsize=(10, 10))

for i in range(9):

    aug = data_augmentation(
        np.expand_dims(rgb.astype(np.float32), 0),
        training=True
    )

    plt.subplot(3, 3, i + 1)
    plt.imshow(aug[0].numpy().astype(np.uint8))
    plt.title(f"Aug {i+1}")
    plt.axis("off")

plt.suptitle("Training Augmented Images")
plt.tight_layout()
plt.show()

# =====================================================
# Prediction
# =====================================================

image = rgb.astype(np.float32)

image = tf.keras.applications.mobilenet_v3.preprocess_input(image)

image = np.expand_dims(image, axis=0)

prediction = model.predict(image, verbose=0)[0]

top5 = np.argsort(prediction)[::-1][:5]

print("\nTop 5 Predictions\n")

for rank, i in enumerate(top5, start=1):
    print(f"{rank}. {class_names[i]:<3} {prediction[i]*100:.2f}%")

idx = top5[0]

label = class_names[idx]

confidence = prediction[idx] * 100

print("\n======================")
print("Prediction :", label)
print("Confidence :", round(confidence, 2), "%")
print("======================")

# ----------------------------
# Show Prediction
# ----------------------------

cv2.putText(
    display,
    f"{label} ({confidence:.2f}%)",
    (20, 40),
    cv2.FONT_HERSHEY_SIMPLEX,
    1,
    (0, 255, 0),
    2
)

cv2.imshow("Prediction", display)

cv2.waitKey(0)

cv2.destroyAllWindows()