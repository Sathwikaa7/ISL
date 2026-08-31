"""Train a pose, face, and hand temporal word-sign classifier."""

from __future__ import annotations

import argparse, json, sys
from pathlib import Path
import numpy as np
import tensorflow as tf

PROJECT_DIR = Path(__file__).resolve().parents[2]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from backend.training.word_holistic_landmarks import FEATURES, NUM_NODES

def load_dataset(root, minimum):
    x, y, classes = [], [], []
    for directory in sorted(path for path in root.iterdir() if path.is_dir()):
        files = sorted(directory.glob('*.npy'))
        if len(files) < minimum: continue
        classes.append(directory.name)
        x.extend(np.load(path).astype(np.float32) for path in files)
        y.extend([len(classes)-1] * len(files))
    return np.stack(x), np.asarray(y), classes

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=Path, default=PROJECT_DIR / 'dataset' / 'word_holistic_landmarks')
    parser.add_argument('--epochs', type=int, default=80)
    parser.add_argument('--min-samples', type=int, default=30)
    args = parser.parse_args()
    tf.keras.utils.set_random_seed(42)
    x, y, classes = load_dataset(args.dataset, args.min_samples)
    rng = np.random.default_rng(42); train=[]; val=[]
    for label in np.unique(y):
        indices=np.flatnonzero(y==label); rng.shuffle(indices); cut=max(1, round(len(indices)*.2)); val.extend(indices[:cut]); train.extend(indices[cut:])
    train, val = np.asarray(train), np.asarray(val)
    inputs=tf.keras.Input(shape=x.shape[1:])
    z=tf.keras.layers.Reshape((x.shape[1], NUM_NODES * FEATURES))(inputs)
    z=tf.keras.layers.LayerNormalization()(z)
    z=tf.keras.layers.Bidirectional(tf.keras.layers.GRU(128, return_sequences=True, dropout=.25))(z)
    z=tf.keras.layers.Bidirectional(tf.keras.layers.GRU(64, dropout=.25))(z)
    z=tf.keras.layers.Dense(128, activation='relu')(z); z=tf.keras.layers.Dropout(.35)(z)
    outputs=tf.keras.layers.Dense(len(classes), activation='softmax')(z)
    model=tf.keras.Model(inputs, outputs)
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    models=PROJECT_DIR/'backend'/'models'; models.mkdir(exist_ok=True)
    path=models/'isl_word_holistic.keras'
    callbacks=[tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=12, restore_best_weights=True), tf.keras.callbacks.ModelCheckpoint(str(path), monitor='val_loss', save_best_only=True)]
    model.fit(x[train], y[train], validation_data=(x[val],y[val]), epochs=args.epochs, batch_size=16, callbacks=callbacks, verbose=2)
    model.save(str(path))
    (models/'word_holistic_classes.json').write_text(json.dumps(classes, indent=2), encoding='utf-8')
    print(f'Saved {path} with {len(classes)} classes')

if __name__ == '__main__': main()
