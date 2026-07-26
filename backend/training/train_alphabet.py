import os
import json
import tensorflow as tf
import matplotlib.pyplot as plt

# ==========================
# Configuration
# ==========================

DATASET_PATH = r"D:\SLD\dataset\alphabet"

MODEL_DIR = os.path.join("..", "models")
os.makedirs(MODEL_DIR, exist_ok=True)

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 16
EPOCHS = 20

# ==========================
# Load Dataset
# ==========================

train_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_PATH,
    validation_split=0.2,
    subset="training",
    seed=42,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_PATH,
    validation_split=0.2,
    subset="validation",
    seed=42,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE
)

class_names = train_ds.class_names
num_classes = len(class_names)

print("\nClasses:")
print(class_names)

print("\nTotal Classes:", num_classes)

# Save class names for backend inference

with open(os.path.join(MODEL_DIR, "alphabet_classes.json"), "w") as f:
    json.dump(class_names, f)

AUTOTUNE = tf.data.AUTOTUNE

train_ds = train_ds.shuffle(1000).prefetch(AUTOTUNE)
val_ds = val_ds.prefetch(AUTOTUNE)

# ==========================
# Data Augmentation
# ==========================

data_augmentation = tf.keras.Sequential([
    tf.keras.layers.RandomFlip("horizontal"),
    tf.keras.layers.RandomRotation(0.1),
    tf.keras.layers.RandomZoom(0.1),
])

# ==========================
# MobileNetV3
# ==========================

base_model = tf.keras.applications.MobileNetV3Small(
    input_shape=(224,224,3),
    include_top=False,
    weights="imagenet"
)

base_model.trainable = False

# ==========================
# Build Model
# ==========================

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

# ==========================
# Compile
# ==========================

model.compile(
    optimizer=tf.keras.optimizers.Adam(1e-3),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

model.summary()

# ==========================
# Callbacks
# ==========================

callbacks = [

    tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=5,
        restore_best_weights=True
    ),

    tf.keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.2,
        patience=2
    ),

    tf.keras.callbacks.ModelCheckpoint(
        filepath=os.path.join(MODEL_DIR, "isl_model.keras"),
        save_best_only=True
    )

]

# ==========================
# Train
# ==========================
print("\nTraining dataset ready")
print("Validation dataset ready")
print("Starting training...\n")

history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS,
    callbacks=callbacks,
    verbose=2
)
print("\nmodel.fit finished successfully\n")

# ==========================
# Save Final Model
# ==========================

model.save(os.path.join(MODEL_DIR, "isl_model.keras"))

print("\nTraining completed successfully!")

# ==========================
# Accuracy Plot
# ==========================

plt.figure(figsize=(8,5))
plt.plot(history.history["accuracy"])
plt.plot(history.history["val_accuracy"])
plt.title("Training Accuracy")
plt.xlabel("Epoch")
plt.ylabel("Accuracy")
plt.legend(["Train","Validation"])
plt.grid(True)
plt.show()

# ==========================
# Loss Plot
# ==========================

plt.figure(figsize=(8,5))
plt.plot(history.history["loss"])
plt.plot(history.history["val_loss"])
plt.title("Training Loss")
plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.legend(["Train","Validation"])

plt.grid(True)
plt.show()