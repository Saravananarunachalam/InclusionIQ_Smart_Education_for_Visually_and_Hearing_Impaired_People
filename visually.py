import speech_recognition as sr
import gtts
import os
import time
import json
import platform

# Internal speak function using gTTS with controlled pacing
def _speak_text(text):
    try:
        tts = gtts.gTTS(text=text, lang='en', slow=False)  # Normal speed
        temp_audio = "temp_audio.mp3"
        tts.save(temp_audio)
        if platform.system() == 'Darwin':  # macOS
            os.system(f"afplay {temp_audio} > /dev/null 2>&1")  # Run synchronously to avoid overlap
        else:  # Windows/Linux fallback
            os.system(f"start {temp_audio}" if platform.system() == 'Windows' else f"mpg123 {temp_audio} > /dev/null 2>&1")
        # Adjusted delay for natural pacing
        time.sleep(0.8 + len(text.split()) * 0.1)  # Approx 1x speed (150 words/min)
        os.remove(temp_audio)
    except Exception as e:
        print(f"Speech error: {e}")

# Public speak_text function for app.py
def speak_text(text):
    _speak_text(text)

# Set the path to the JSON file
JSON_FILE_PATH = "visual.json"

# Load course data (no immediate speech)
try:
    with open(JSON_FILE_PATH, 'r') as file:
        course_data = json.load(file)
    print("Course data loaded successfully from", JSON_FILE_PATH)
except FileNotFoundError:
    print(f"Error: The file {JSON_FILE_PATH} was not found.")
    course_data = {}
except json.JSONDecodeError:
    print(f"Error: The file {JSON_FILE_PATH} contains invalid JSON.")
    course_data = {}

# Voice command recognition with stable settings
def recognize_command(prompt):
    recognizer = sr.Recognizer()
    speak_text(prompt)  # Single speech trigger
    try:
        with sr.Microphone() as source:
            print(f"Say: {prompt}")
            recognizer.adjust_for_ambient_noise(source, duration=1.5)  # Balanced adjustment
            audio = recognizer.listen(source, timeout=6, phrase_time_limit=6)  # Extended for stability
            command = recognizer.recognize_google(audio, language='en-US').lower()
            print(f"Recognized: {command}")
            return command
    except sr.UnknownValueError:
        print("Sorry, I didn’t understand that.")
        speak_text("Sorry, I didn’t understand that. Please try again.")
        return ""
    except sr.RequestError as e:
        print(f"Couldn’t connect to the speech service: {e}")
        speak_text("Couldn’t connect to the speech service. Check your internet.")
        return ""
    except sr.WaitTimeoutError:
        print("Timed out waiting for speech.")
        speak_text("Timed out waiting for speech. Please try again.")
        return ""
    except Exception as e:
        print(f"Microphone error on {platform.system()}: {e}")
        speak_text(f"Microphone error on {platform.system()}. Ensure mic permissions are granted.")
        return ""

# Export for app.py
if __name__ == "__main__":
    pass  # No standalone execution; handled by app.py

# Make functions and data accessible
speak_text = speak_text
recognize_command = recognize_command
course_data = course_data