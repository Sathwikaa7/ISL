from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from backend.utils.translator import Translator
from backend.utils.speaker import Speaker
from backend.predictors.alphabet_predictor import predict
from backend.utils.rapidfuzz_utils import load_words, make_suggester

import tensorflow as tf
import numpy as np
import cv2

from PIL import Image

import base64
import io
import os
import time
from uuid import uuid4

from backend import state

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DICTIONARY_PATH = os.path.join(os.path.dirname(BASE_DIR), "data", "english_words.txt")
AUDIO_DIRECTORY = os.path.join(BASE_DIR, "generated_audio")

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
# Load Word Model
# -----------------------------------

print("Loading Word Model...")
WORD_MODEL_PATH = os.path.join(BASE_DIR, "models", "isl_word_model.keras")
word_model = tf.keras.models.load_model(WORD_MODEL_PATH)
print("Models loaded successfully!")

translator = Translator()
speaker = Speaker()
word_suggestions = make_suggester(load_words(DICTIONARY_PATH))

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

# FIX: confidence threshold for word mode
WORD_CONFIDENCE_THRESHOLD = 75.0

# -----------------------------------
# Routes
# -----------------------------------

@app.route("/")
def home():
    return jsonify({
        "project": "Offline AI Sign Language Communication Assistant",
        "status": "Running"
    })


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/suggest")
def suggest_words():
    """Return word choices once the user has signed at least three letters."""
    letter_sequence = request.args.get("prefix", "")
    if not letter_sequence.strip():
        return jsonify({"suggestions": []})

    return jsonify({"suggestions": word_suggestions(letter_sequence)})


@app.route("/api/translate", methods=["POST"])
def translate_text():
    """Keep the completed sentence in English and provide its Telugu translation."""
    payload = request.get_json(silent=True) or {}
    english = str(payload.get("text", "")).strip()
    if not english:
        return jsonify({"error": "Text is required."}), 400

    return jsonify({
        "english": english,
        "telugu": translator.translate(english)
    })


@app.route("/api/speak", methods=["POST"])
def synthesize_speech():
    """Generate an MP3 and return a same-origin URL that Vite can proxy."""
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    language = str(payload.get("lang", "en")).lower()

    if not text:
        return jsonify({"error": "Text is required."}), 400
    if language not in Speaker.SUPPORTED_LANGUAGES:
        return jsonify({"error": "Language must be 'en' or 'te'."}), 400

    filename = f"{uuid4().hex}.mp3"
    try:
        speaker.synthesize(text, language, os.path.join(AUDIO_DIRECTORY, filename))
    except Exception as error:
        print(f"Speech synthesis error: {error}")
        return jsonify({"error": "Could not generate speech audio."}), 502

    return jsonify({"audio_url": f"/api/audio/{filename}"})


@app.route("/api/audio/<path:filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_DIRECTORY, filename, mimetype="audio/mpeg")

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

    # FIX 1: removed print("RAW DATA:", data) — was spamming terminal

    start = time.time()
    mode = data.get("mode", "alphabet")

    try:

        image_data = data["image"].split(",")[1]
        image = Image.open(
            io.BytesIO(base64.b64decode(image_data))
        ).convert("RGB")

        frame = np.array(image)

        # -------------------------
        # Alphabet Mode
        # -------------------------
        if mode == "alphabet":

            label, confidence = predict(image)

            fps = round(1 / (time.time() - start), 2)

            # FIX 2: only emit if hand detected
            if label is None:
                emit("prediction", {
                    "label": "",
                    "confidence": round(confidence, 2),
                    "fps": fps
                })
                return

            print(f"[ALPHABET] {label} ({round(confidence, 2)}%)")

            state.current_prediction = label
            state.current_confidence = round(confidence, 2)

            emit("prediction", {
                "label": label,
                "confidence": round(confidence, 2),
                "fps": fps
            })

            return

        # -------------------------
        # Word Mode
        # NOTE: word model needs sequence of frames (LSTM)
        # This single-frame approach is temporary for demo
        # -------------------------
        image_resized = image.resize((224, 224))
        image_array = np.array(image_resized, dtype=np.float32)
        image_array = tf.keras.applications.mobilenet_v3.preprocess_input(image_array)
        image_array = np.expand_dims(image_array, axis=0)

        prediction = word_model.predict(image_array, verbose=0)

        idx = np.argmax(prediction)
        confidence = float(prediction[0][idx]) * 100

        fps = round(1 / (time.time() - start), 2)

        print(f"[WORD] {CLASS_NAMES[idx]} ({round(confidence, 2)}%)")

        state.current_prediction = CLASS_NAMES[idx]
        state.current_confidence = round(confidence, 2)

        emit("prediction", {
            "label": CLASS_NAMES[idx],
            "confidence": round(confidence, 2),
            "fps": fps
        })

    except Exception as e:

        print(f"[ERROR] {e}")

        emit("prediction", {
            "label": "Error",
            "confidence": 0,
            "fps": 0,
            "error": str(e)
        })

# -----------------------------------
# Add Word to Sentence
# -----------------------------------

@socketio.on("add_word")
def add_word():
    state.sentence.add_word(state.current_prediction)
    emit("sentence", {
        "sentence": state.sentence.get_sentence()
    }, broadcast=True)

# -----------------------------------
# Backspace
# -----------------------------------

@socketio.on("backspace")
def backspace():
    state.sentence.backspace()
    emit("sentence", {
        "sentence": state.sentence.get_sentence()
    }, broadcast=True)

# -----------------------------------
# Clear Sentence
# -----------------------------------

@socketio.on("clear_sentence")
def clear_sentence():
    state.sentence.clear()
    emit("sentence", {"sentence": ""}, broadcast=True)

# -----------------------------------
# Get Sentence
# -----------------------------------

@socketio.on("get_sentence")
def get_sentence():
    emit("sentence", {
        "sentence": state.sentence.get_sentence()
    })

# -----------------------------------
# Translate
# -----------------------------------

@socketio.on("translate")
def translate_sentence():
    sentence = state.sentence.get_sentence()
    translated = translator.translate(sentence)
    state.translated_text = translated
    emit("translated", {
        "english": sentence,
        "telugu": translated
    }, broadcast=True)

# -----------------------------------
# Run
# -----------------------------------

if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=False  # FIX 4: debug=False stops auto-reloader spam
    )
