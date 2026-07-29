"""Train an isolated-word ISL ST-GCN model from extracted hand landmarks.

This training path is separate from the existing alphabet MobileNet model.
It reads ``dataset/word_landmarks`` and writes only word-specific files:
``models/isl_word_stgcn.keras``, ``models/word_classes.json``, and metrics.

Run from D:\\SLD after landmark extraction:
    venv_train\\Scripts\\python.exe backend\\training\\train_word_stgcn.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import tensorflow as tf


DATASET_DIR = Path(r"D:\SLD\dataset\word_landmarks")
MODELS_DIR = Path(r"D:\SLD\backend\models")
NUM_NODES = 42  # 21 left-hand nodes, followed by 21 right-hand nodes


def hand_adjacency() -> np.ndarray:
    """Create the two-hand MediaPipe skeleton graph used by ST-GCN."""
    # Wrist-to-fingertip edges for one MediaPipe hand.
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 4),
        (0, 5), (5, 6), (6, 7), (7, 8),
        (0, 9), (9, 10), (10, 11), (11, 12),
        (0, 13), (13, 14), (14, 15), (15, 16),
        (0, 17), (17, 18), (18, 19), (19, 20),
    ]
    adjacency = np.eye(NUM_NODES, dtype=np.float32)
    for offset in (0, 21):
        for start, end in edges:
            adjacency[offset + start, offset + end] = 1.0
            adjacency[offset + end, offset + start] = 1.0
    # Lets the model learn signs whose meaning depends on both hands together.
    adjacency[0, 21] = adjacency[21, 0] = 1.0
    degree = adjacency.sum(axis=1)
    return adjacency / np.sqrt(np.outer(degree, degree))


@tf.keras.utils.register_keras_serializable(package="isl_word")
class GraphConvolution(tf.keras.layers.Layer):
    """Fixed skeleton aggregation followed by a learnable channel projection."""

    def __init__(self, units: int, adjacency: list[list[float]], **kwargs):
        super().__init__(**kwargs)
        self.units = units
        self.adjacency = np.asarray(adjacency, dtype=np.float32)
        self.projection = tf.keras.layers.Dense(units, use_bias=False)

    def call(self, inputs):
        # inputs: (batch, frames, nodes, features)
        neighbours = tf.einsum("btvc,vw->btwc", inputs, self.adjacency)
        return self.projection(neighbours)

    def get_config(self):
        config = super().get_config()
        config.update({"units": self.units, "adjacency": self.adjacency.tolist()})
        return config


@tf.keras.utils.register_keras_serializable(package="isl_word")
class STGCNBlock(tf.keras.layers.Layer):
    """Spatial graph convolution plus a temporal convolution with residuals."""

    def __init__(self, units: int, adjacency: list[list[float]], **kwargs):
        super().__init__(**kwargs)
        self.units = units
        self.adjacency = adjacency
        self.gcn = GraphConvolution(units, adjacency)
        self.spatial_norm = tf.keras.layers.BatchNormalization()
        self.temporal = tf.keras.layers.Conv2D(units, (9, 1), padding="same", use_bias=False)
        self.temporal_norm = tf.keras.layers.BatchNormalization()
        self.residual_projection = None

    def build(self, input_shape):
        if input_shape[-1] != self.units:
            self.residual_projection = tf.keras.layers.Dense(self.units, use_bias=False)
        super().build(input_shape)

    def call(self, inputs, training=None):
        residual = inputs if self.residual_projection is None else self.residual_projection(inputs)
        x = self.gcn(inputs)
        x = tf.nn.relu(self.spatial_norm(x, training=training))
        # Conv2D already accepts (batch, frames, nodes, channels).  Adding a
        # fifth dimension here would make the feature channels look like a
        # spatial axis and produces an invalid (.., channels, filters) output.
        x = self.temporal(x)
        x = self.temporal_norm(x, training=training)
        return tf.nn.relu(x + residual)

    def get_config(self):
        config = super().get_config()
        config.update({"units": self.units, "adjacency": self.adjacency})
        return config


def load_dataset(dataset_dir: Path, min_samples: int) -> tuple[np.ndarray, np.ndarray, list[str]]:
    class_dirs = sorted(path for path in dataset_dir.iterdir() if path.is_dir())
    if len(class_dirs) < 2:
        raise RuntimeError("At least two word class folders are required.")

    samples, labels, included_classes = [], [], []
    for class_dir in class_dirs:
        files = sorted(class_dir.glob("*.npy"))
        if len(files) < min_samples:
            print(f"Skipping {class_dir.name}: {len(files)} sequences (minimum is {min_samples})")
            continue
        class_index = len(included_classes)
        included_classes.append(class_dir.name)
        for file_path in files:
            sequence = np.load(file_path).astype(np.float32)
            if sequence.ndim != 3 or sequence.shape[1:] != (NUM_NODES, 4):
                raise ValueError(f"Unexpected shape in {file_path}: {sequence.shape}")
            samples.append(sequence)
            labels.append(class_index)
        print(f"{class_dir.name}: {len(files)} sequences")
    if len(included_classes) < 2:
        raise RuntimeError(f"Fewer than two classes have at least {min_samples} sequences.")
    return np.stack(samples), np.asarray(labels, dtype=np.int32), included_classes


def stratified_split(labels: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Create an 8/2/2-style split for the available 12 clips per class."""
    random = np.random.default_rng(seed)
    train, validation, test = [], [], []
    for label in np.unique(labels):
        indices = np.flatnonzero(labels == label)
        random.shuffle(indices)
        holdout = max(1, round(len(indices) * 0.2))
        if len(indices) - 2 * holdout < 1:
            raise RuntimeError(f"Class {label} has too few samples for train/validation/test splitting.")
        test.extend(indices[:holdout])
        validation.extend(indices[holdout : 2 * holdout])
        train.extend(indices[2 * holdout :])
    return np.array(train), np.array(validation), np.array(test)


def build_model(frames: int, features: int, num_classes: int) -> tf.keras.Model:
    adjacency = hand_adjacency().tolist()
    inputs = tf.keras.Input(shape=(frames, NUM_NODES, features), name="hand_landmarks")
    x = STGCNBlock(64, adjacency, name="stgcn_block_1")(inputs)
    x = tf.keras.layers.Dropout(0.20)(x)
    x = STGCNBlock(128, adjacency, name="stgcn_block_2")(x)
    x = tf.keras.layers.Dropout(0.25)(x)
    x = STGCNBlock(128, adjacency, name="stgcn_block_3")(x)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dense(128, activation="relu")(x)
    x = tf.keras.layers.Dropout(0.35)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax", name="word")(x)
    return tf.keras.Model(inputs, outputs, name="isl_word_stgcn")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a word-only ST-GCN model.")
    parser.add_argument("--dataset", type=Path, default=DATASET_DIR)
    parser.add_argument("--models-dir", type=Path, default=MODELS_DIR)
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--min-samples", type=int, default=60,
        help="Exclude classes with fewer sequences than this (default: 60).",
    )
    args = parser.parse_args()

    tf.keras.utils.set_random_seed(args.seed)
    sequences, labels, class_names = load_dataset(args.dataset, args.min_samples)
    train_index, validation_index, test_index = stratified_split(labels, args.seed)
    print(f"Split: train={len(train_index)}, validation={len(validation_index)}, test={len(test_index)}")

    model = build_model(sequences.shape[1], sequences.shape[3], len(class_names))
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy", tf.keras.metrics.SparseTopKCategoricalAccuracy(k=3, name="top_3_accuracy")],
    )
    args.models_dir.mkdir(parents=True, exist_ok=True)
    model_path = args.models_dir / "isl_word_stgcn.keras"
    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=15, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", patience=6, factor=0.5, min_lr=1e-5),
        tf.keras.callbacks.ModelCheckpoint(str(model_path), monitor="val_loss", save_best_only=True),
    ]
    model.fit(
        sequences[train_index], labels[train_index],
        validation_data=(sequences[validation_index], labels[validation_index]),
        epochs=args.epochs,
        batch_size=args.batch_size,
        callbacks=callbacks,
        verbose=2,
    )

    # Reload the checkpoint, so test metrics always report the best validation model.
    best_model = tf.keras.models.load_model(model_path)
    test_loss, test_accuracy, test_top3 = best_model.evaluate(
        sequences[test_index], labels[test_index], verbose=0
    )
    with (args.models_dir / "word_classes.json").open("w", encoding="utf-8") as file:
        json.dump(class_names, file, indent=2)
    metrics = {
        "test_loss": float(test_loss),
        "test_accuracy": float(test_accuracy),
        "test_top_3_accuracy": float(test_top3),
        "classes": class_names,
        "split_sizes": {"train": len(train_index), "validation": len(validation_index), "test": len(test_index)},
    }
    with (args.models_dir / "isl_word_stgcn_metrics.json").open("w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2)
    print(json.dumps(metrics, indent=2))
    print(f"Saved word-only model: {model_path}")


if __name__ == "__main__":
    main()
