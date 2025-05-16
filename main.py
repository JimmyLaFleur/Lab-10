import os
import json
import queue
import requests
import pyttsx3
import pyaudio
from vosk import Model, KaldiRecognizer


tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 150)
q = queue.Queue()

p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000,
                input=True, frames_per_buffer=8000)
stream.start_stream()


def speak(text):
    print("Ассистент:", text)
    tts_engine.say(text)
    tts_engine.runAndWait()


def translate(text, lang_from="ru", lang_to="en"):
    try:
        response = requests.get("https://api.mymemory.translated.net/get",
                                params={"q": text, "langpair": f"{lang_from}|{lang_to}"})
        result = response.json()
        return result["responseData"]["translatedText"]
    except Exception as e:
        return f"Ошибка перевода: {e}"


recognizer = KaldiRecognizer(model, 16000)
print("Говорите...")

command_mode = None
last_translation = None
last_text = None
glossary = {}

while True:
    data = stream.read(4000, exception_on_overflow=False)
    if recognizer.AcceptWaveform(data):
        result = json.loads(recognizer.Result())
        text = result.get("text", "").strip().lower()

        if not text:
            continue

        print("Вы сказали:", text)

        if command_mode == "translate":
            translation = translate(text)
            last_translation = translation
            last_text = text
            speak("Перевод на английский: " + translation)
            command_mode = None
            continue

        if command_mode == "save":
            if glossary:
                with open("glossary.json", "w", encoding="utf-8") as f:
                    json.dump(glossary, f, ensure_ascii=False, indent=4)
                speak("Перевод сохранён.")
                command_mode = None
            else:
                speak("Словарь пуст!")
                command_mode = None
            continue

        if command_mode == "addGlossary":
            if last_text != None and last_translation != None:
                glossary[last_text] = last_translation
                command_mode = None
            else:
                print("Вы ничего еще не перевели")
                command_mode = None
            continue

        if command_mode == "delete":
            if glossary:
                glossary.popitem()
                command_mode = None
            else:
                print("Словарь скорее всего пуст...")
                command_mode = None
            continue

        if "перевод" in text:
            command_mode = "translate"

        elif "сохранить" in text:
            command_mode = "save"

        elif "словарь" in text:
            command_mode = "addGlossary"

        elif "удалить" in text:
            command_mode = "delete"

        else:
            speak("Я не понял команду.")
