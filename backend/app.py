from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from backend.utils.translator import Translator
from backend.utils.speaker import Speaker
from backend.predictors.alphabet_predictor import predict
from backend.utils.rapidfuzz_utils import load_words, make_suggester
from backend.word_mode import WordPredictor

import numpy as np

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

try:
    word_predictor = WordPredictor(os.path.join(BASE_DIR, "models"))
    print("Word ST-GCN model loaded successfully!")
except Exception as error:
    word_predictor = None
    print(f"Word mode unavailable: {error}")

translator = Translator()
speaker = Speaker()
word_suggestions = make_suggester(load_words(DICTIONARY_PATH))

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

            if word_predictor:
                word_predictor.reset()

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
        # Word Mode: a separate 48-frame landmark ST-GCN pipeline.
        # -------------------------
        if word_predictor is None:
            emit("prediction", {"label": "", "confidence": 0, "fps": 0, "status": "Word model is unavailable."})
            return

        word_result = word_predictor.process(frame)

        fps = round(1 / (time.time() - start), 2)

        state.current_prediction = word_result["label"]
        state.current_confidence = round(word_result["confidence"], 2)

        emit("prediction", {
            "label": word_result["label"],
            "confidence": round(word_result["confidence"], 2),
            "fps": fps,
            "stable": word_result["stable"],
            "status": word_result["status"],
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
