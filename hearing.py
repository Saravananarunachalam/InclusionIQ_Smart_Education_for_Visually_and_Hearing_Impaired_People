import json
from gtts import gTTS
import os
import platform
import time
import subprocess
import threading

# Verify current working directory
print(f"Current working directory: {os.getcwd()}")

# Load JSON data from a file
try:
    with open('hearing.json', 'r') as f:
        course_data = json.load(f)
    print("JSON loaded successfully")
except FileNotFoundError:
    print("Error: hearing.json not found")
    exit(1)
except json.JSONDecodeError:
    print("Error: hearing.json contains invalid JSON")
    exit(1)

def get_course_topics(course_name):
    """Return topics for a given course."""
    return course_data.get(course_name, [])

def get_topic_details(course_name, topic_index):
    """Return details of a specific topic in a course."""
    topics = get_course_topics(course_name)
    if 0 <= topic_index < len(topics):
        return topics[topic_index]
    return None

def get_video_path(course_name, topic_index):
    """Return the path to the video file."""
    video_file = f"static/videos/{course_name}_{topic_index}.mp4"
    if os.path.exists(video_file):
        return video_file
    print(f"Error: Video file {video_file} not found")
    return None

def text_to_speech(text, output_file="temp_audio.mp3"):
    """Convert text to speech using gTTS and save to file."""
    print(f"Converting text to speech: {text}")
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(output_file)
        if not os.path.exists(output_file):
            print("Error: Audio file was not created")
            return False
        return True
    except Exception as e:
        print(f"Error in text-to-speech: {e}")
        return False

def play_media(video_file, audio_file):
    """Play video and audio simultaneously."""
    print(f"Playing video: {video_file} and audio: {audio_file}")
    try:
        if not os.path.exists(video_file):
            print(f"Error: Video file {video_file} does not exist")
            return
        if not os.path.exists(audio_file):
            print(f"Error: Audio file {audio_file} does not exist")
            return

        def play_audio():
            if platform.system() == 'Darwin':  # macOS
                subprocess.run(["afplay", audio_file], check=True)
            elif platform.system() == 'Windows':
                subprocess.run(["start", "", audio_file], shell=True, check=True)
            else:  # Linux
                subprocess.run(["mpg123", audio_file], check=True)

        def play_video():
            if platform.system() == 'Darwin':  # macOS
                subprocess.run(["open", video_file], check=True)
            elif platform.system() == 'Windows':
                subprocess.run(["start", "", video_file], shell=True, check=True)
            else:  # Linux
                subprocess.run(["vlc", video_file, "--play-and-exit"], check=True)

        # Start audio and video in separate threads to play simultaneously
        audio_thread = threading.Thread(target=play_audio)
        video_thread = threading.Thread(target=play_video)
        audio_thread.start()
        video_thread.start()

        # Wait for both to finish
        audio_thread.join()
        video_thread.join()

        # Clean up audio file
        if os.path.exists(audio_file):
            os.remove(audio_file)
            print("Cleaned up temporary audio file")
    except Exception as e:
        print(f"Error playing media: {e}")

def play_topic_media(course_name, topic_index):
    """Play video and audio for a given topic."""
    topic = get_topic_details(course_name, topic_index)
    if not topic:
        print(f"Error: Topic index {topic_index} not found for course {course_name}")
        return

    video_file = get_video_path(course_name, topic_index)
    if not video_file:
        return

    audio_file = "temp_audio.mp3"
    summary = topic.get('summary', '')
    if summary and text_to_speech(summary, audio_file):
        play_media(video_file, audio_file)
    else:
        print("No audio generated, playing video only")
        play_media(video_file, audio_file=None)

# Test the function
if __name__ == "__main__":
    print("Testing media playback...")
    play_topic_media("SignLanguage101", 0)