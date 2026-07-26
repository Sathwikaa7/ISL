from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from backend.utils.translator import Translator

import tensorflow as tf
import numpy as np
from PIL import Image

import base64
import io
import os
import time

import state

# -----------------------------------
# Flask App
# -----------------------------------

app = Flask(__name__)
CORS(app)

socketio = SocketIO(
    app,
    cors_allowed_origins="*"
)

# -----------------------------------
# Load AI Model
# -----------------------------------

print("Loading Alphabet Model...")
alphabet_model = tf.keras.models.load_model(
    os.path.join("models", "isl_model.keras")
)

print("Loading Word Model...")
word_model = tf.keras.models.load_model(
    os.path.join("models", "isl_word_model.keras")
)

print("Both models loaded successfully!")

translator = Translator()

ALPHABET_CLASSES = [
    '1','2','3','4','5','6','7','8','9',
    'A','B','C','D','E','F','G','H','I',
    'J','K','L','M','N','O','P','Q','R',
    'S','T','U','V','W','X','Y','Z'
]

# -----------------------------------
# Class Names
# -----------------------------------

CLASS_NAMES = [
    'afternoon','animal','bad','beautiful','big','bird','blind','cat',
    'cheap','clothing','cold','cow','curved','deaf','dog','dress',
    'dry','evening','expensive','famous','fast','female','fish','flat',
    'friday','good','happy','hat','healthy','horse','hot','hour',
    'light','long','loose','loud','minute','monday','month','morning',
    'mouse','narrow','new','night','old','pant','pocket','quiet',
    'sad','saturday','second','shirt','shoes','short','sick','skirt',
    'slow','small','suit','sunday','t_shirt','tall','thursday','time',
    'today','tomorrow','tuesday','ugly','warm','wednesday','week',
    'wet','wide','year','yesterday','young'
]

# -----------------------------------
# Home
# -----------------------------------

@app.route("/")
def home():
    return jsonify({
        "project": "Offline AI Sign Language Communication Assistant",
        "status": "Running"
    })


@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok"
    })

# -----------------------------------
# Socket Events
# -----------------------------------

@socketio.on("connect")
def connected():
    print("Client Connected")


@socketio.on("disconnect")
def disconnected():
    print("Client Disconnected")

# -----------------------------------
# Predict Frame
# -----------------------------------

@socketio.on("frame")
def handle_frame(data):

    start = time.time()
    mode = data.get("mode", "phrase")

    try:

        image_data = data["image"]

        image_data = image_data.split(",")[1]

        image = Image.open(
            io.BytesIO(base64.b64decode(image_data))
        ).convert("RGB")

        # -------------------------
        # Alphabet Model
        # -------------------------
        if mode == "alphabet":

            image = image.resize((128, 128))

            image = np.array(image, dtype=np.float32)

            # CNN model expects values between 0 and 1
            image = image / 255.0

            image = np.expand_dims(image, axis=0)

            prediction = alphabet_model.predict(image, verbose=0)

            classes = ALPHABET_CLASSES

        # -------------------------
        # Word Model
        # -------------------------
        else:

            image = image.resize((128, 128))

            image = np.array(image, dtype=np.float32)

            image = tf.keras.applications.mobilenet_v3.preprocess_input(image)

            image = np.expand_dims(image, axis=0)

            prediction = word_model.predict(image, verbose=0)

            classes = CLASS_NAMES

        idx = np.argmax(prediction)

        confidence = float(prediction[0][idx]) * 100

        print("===================================")
        print("MODE:", mode)
        print("CLASS:", classes[idx])
        print("CONFIDENCE:", round(confidence, 2))
        print("===================================")

        fps = round(1 / (time.time() - start), 2)

        # Save current prediction
        state.current_prediction = classes[idx]
        state.current_confidence = round(confidence, 2)

        emit("prediction", {
            "label": classes[idx],
            "confidence": round(confidence, 2),
            "fps": fps
        })

    except Exception as e:

        print(e)

        emit("prediction", {
            "label": "Error",
            "confidence": 0,
            "fps": 0,
            "error": str(e)
        })

# -----------------------------------
# Add Current Prediction to Sentence
# -----------------------------------

@socketio.on("add_word")
def add_word():

    state.sentence.add_word(state.current_prediction)

    emit(
        "sentence",
        {
            "sentence": state.sentence.get_sentence()
        },
        broadcast=True
    )

# -----------------------------------
# Backspace
# -----------------------------------

@socketio.on("backspace")
def backspace():

    state.sentence.backspace()

    emit(
        "sentence",
        {
            "sentence": state.sentence.get_sentence()
        },
        broadcast=True
    )

# -----------------------------------
# Clear Sentence
# -----------------------------------

@socketio.on("clear_sentence")
def clear_sentence():

    state.sentence.clear()

    emit(
        "sentence",
        {
            "sentence": ""
        },
        broadcast=True
    )

# -----------------------------------
# Get Current Sentence
# -----------------------------------

@socketio.on("get_sentence")
def get_sentence():

    emit(
        "sentence",
        {
            "sentence": state.sentence.get_sentence()
        }
    )

# -----------------------------------
# Translate Sentence
# -----------------------------------

@socketio.on("translate")
def translate_sentence():

    sentence = state.sentence.get_sentence()

    translated = translator.translate(sentence)

    state.translated_text = translated

    emit(
        "translated",
        {
            "english": sentence,
            "telugu": translated
        },
        broadcast=True
    )

# -----------------------------------
# Run Server
# -----------------------------------

if __name__ == "__main__":

    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True
    )