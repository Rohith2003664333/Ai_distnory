from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import speech_recognition as sr
import spacy
from nltk.corpus import wordnet, stopwords
import os
import nltk

# Download necessary NLTK resources
nltk.download("wordnet")
nltk.download("stopwords")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")

@app.route('/')
def serve_index():
    return send_from_directory('', 'index.html')

def record_audio(filename="output.wav", duration=5, samplerate=44100):
    audio_data = sd.rec(int(samplerate * duration), samplerate=samplerate, channels=1, dtype=np.int16)
    sd.wait()  # Wait for recording to finish
    wav.write(filename, samplerate, audio_data)

def voice_to_text(filename):
    recognizer = sr.Recognizer()
    with sr.AudioFile(filename) as source:
        audio = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return "Sorry, I couldn't understand the audio."
        except sr.RequestError as e:
            return f"Could not request results; {e}"

def extract_goal_word(question):
    stop_words = set(stopwords.words("english"))
    common_question_words = {"what", "is", "the", "meaning", "of", "define", "explain", "term", "word"}
    stop_words.update(common_question_words)
    doc = nlp(question)

    goal_words = [
        token.lemma_ for token in doc 
        if token.text.lower() not in stop_words and token.pos_ in ["NOUN", "PROPN", "ADJ", "VERB"]
    ]

    if not goal_words:
        root_token = [token.lemma_ for token in doc if token.dep_ == "ROOT"]
        goal_words = root_token if root_token else []

    return goal_words

def get_word_definitions(goal_word):
    synsets = wordnet.synsets(goal_word)
    if not synsets:
        return [f"No definitions found for '{goal_word}'."]

    return [synset.definition() for synset in synsets]

@app.route('/api/message', methods=['POST'])
def process_message():
    data = request.json
    question = data.get("text", "")
    goal_words = extract_goal_word(question)

    if not goal_words:
        return jsonify({"reply": "I couldn't extract a goal word from your input."})

    goal_word = ""
    for word in goal_words:
        word = word.lower()
        if word not in {"meaning", "define", "explain", "term", "word"}:
            goal_word = word
            break

    if not goal_word:
        return jsonify({"reply": "Could not determine a goal word from the question."})

    definitions = get_word_definitions(goal_word)
    return jsonify({"reply": "\n".join(definitions)})

@app.route('/api/record', methods=['POST'])
def record_message():
    filename = "output.wav"
    record_audio(filename)
    transcription = voice_to_text(filename)
    os.remove(filename)  # Cleanup
    return jsonify({"transcription": transcription})

if __name__ == "__main__":
    app.run(debug=True)
