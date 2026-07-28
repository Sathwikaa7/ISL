import os
import json
import string
import tensorflow as tf
import matplotlib.pyplot as plt

# ==========================================
# Configuration
# ==========================================

DATASET_PATH = r"D:\SLD\dataset\alphabet"

MODEL_DIR = os.path.join("..", "models")
os.makedirs(MODEL_DIR, exist_ok=True)

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
STAGE1_EPOCHS = 5
STAGE2_EPOCHS = 15

# The downloaded archive also contains a non-letter folder named "{".  Keep
# the alphabet recognizer deliberately restricted to A-Z so its model outputs
# always match alphabet_classes.json and the website's letter buffer.
CLASS_NAMES = list(string.ascii_lowercase)

# ==========================================
# Load Dataset
# ==========================================

train_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_PATH,
    validation_split=0.2,
    subset="training",
    seed=42,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    class_names=CLASS_NAMES
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_PATH,
    validation_split=0.2,
    subset="validation",
    seed=42,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    class_names=CLASS_NAMES
)

class_names = CLASS_NAMES
num_classes = len(class_names)

print("\nClasses:")
print(class_names)

print("\nTotal Classes:", num_classes)

with open(os.path.join(MODEL_DIR, "alphabet_classes.json"), "w") as f:
    json.dump(class_names, f)

AUTOTUNE = tf.data.AUTOTUNE

train_ds = train_ds.shuffle(1000).prefetch(AUTOTUNE)
val_ds = val_ds.prefetch(AUTOTUNE)

# ==========================================
# Data Augmentation
# ==========================================

data_augmentation = tf.keras.Sequential([

    tf.keras.layers.RandomRotation(0.15),
    tf.keras.layers.RandomZoom(0.15),
    tf.keras.layers.RandomTranslation(0.08,0.08),
    tf.keras.layers.RandomContrast(0.2),
    tf.keras.layers.RandomBrightness(0.2),

])

# ==========================================
# MobileNetV3
# ==========================================

base_model = tf.keras.applications.MobileNetV3Small(

    input_shape=(224,224,3),
    include_top=False,
    weights="imagenet"

)

base_model.trainable = False

# ==========================================
# Build Model
# ==========================================

inputs = tf.keras.Input(shape=(224,224,3))

x = data_augmentation(inputs)

x = tf.keras.applications.mobilenet_v3.preprocess_input(x)

x = base_model(x, training=False)

x = tf.keras.layers.GlobalAveragePooling2D()(x)

x = tf.keras.layers.Dropout(0.3)(x)

outputs = tf.keras.layers.Dense(
    num_classes,
    activation="softmax"
)(x)

model = tf.keras.Model(inputs, outputs)

# ==========================================
# Callbacks
# ==========================================

callbacks = [

    tf.keras.callbacks.EarlyStopping(
        monitor="val_accuracy",
        patience=5,
        restore_best_weights=True,
        mode="max"
    ),

    tf.keras.callbacks.ReduceLROnPlateau(
        monitor="val_accuracy",
        factor=0.2,
        patience=2,
        verbose=1,
        mode="max"
    ),

    tf.keras.callbacks.ModelCheckpoint(
        filepath=os.path.join(MODEL_DIR, "isl_model.keras"),
        monitor="val_accuracy",
        save_best_only=True,
        mode="max",
        verbose=1
    )

]

# ==========================================
# Stage 1
# ==========================================

print("\n==========================")
print("Stage 1 Training")
print("==========================\n")

model.compile(

    optimizer=tf.keras.optimizers.Adam(1e-3),

    loss="sparse_categorical_crossentropy",

    metrics=["accuracy"]

)

history1 = model.fit(

    train_ds,

    validation_data=val_ds,

    epochs=STAGE1_EPOCHS,

    callbacks=callbacks,

    verbose=2

)

# ==========================================
# Stage 2 Fine Tuning
# ==========================================

print("\n==========================")
print("Stage 2 Fine Tuning")
print("==========================\n")

base_model.trainable = True

for layer in base_model.layers[:-40]:
    layer.trainable = False

model.compile(

    optimizer=tf.keras.optimizers.Adam(1e-5),

    loss="sparse_categorical_crossentropy",

    metrics=["accuracy"]

)

history2 = model.fit(

    train_ds,

    validation_data=val_ds,

    epochs=STAGE2_EPOCHS,

    callbacks=callbacks,

    verbose=2

)

# ==========================================
# Save Final Model
# ==========================================

model.save(os.path.join(MODEL_DIR,"isl_model.keras"))

print("\nTraining Completed Successfully!")

# ==========================================
# Merge History
# ==========================================

accuracy = history1.history["accuracy"] + history2.history["accuracy"]
val_accuracy = history1.history["val_accuracy"] + history2.history["val_accuracy"]

loss = history1.history["loss"] + history2.history["loss"]
val_loss = history1.history["val_loss"] + history2.history["val_loss"]

# ==========================================
# Accuracy Plot
# ==========================================

plt.figure(figsize=(8,5))

plt.plot(accuracy)

plt.plot(val_accuracy)

plt.title("Training Accuracy")

plt.xlabel("Epoch")

plt.ylabel("Accuracy")

plt.legend(["Train","Validation"])

plt.grid(True)

plt.show()

# ==========================================
# Loss Plot
# ==========================================

plt.figure(figsize=(8,5))

plt.plot(loss)

plt.plot(val_loss)

plt.title("Training Loss")

plt.xlabel("Epoch")

plt.ylabel("Loss")

plt.legend(["Train","Validation"])

plt.grid(True)

plt.show()
