from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, Response
import webbrowser
from gtts import gTTS
import speech_recognition as sr
import visually  # Import visually.py (
import hearing  # Import hearing.py
import threading
import time
import requests  # For server-side Google Form submission
import os
import platform

app = Flask(__name__)

# State for visually impaired navigation
current_course = None
current_index = 0
topics_content = []

def ask_visually_impaired():
    """
    Function to ask if the user is visually impaired and handle the response.
    Returns True if the user says 'yes', False otherwise.
    """
    def text_to_speech(text):
        try:
            tts = gTTS(text=text, lang='en', slow=False)
            temp_file = "temp_audio.mp3"
            tts.save(temp_file)
            if platform.system() == 'Darwin':  # macOS
                os.system(f"afplay {temp_file} > /dev/null 2>&1")
            else:  # Windows/Linux fallback
                os.system(f"start {temp_file}" if platform.system() == 'Windows' else f"mpg123 {temp_file} > /dev/null 2>&1")
            time.sleep(0.8 + len(text.split()) * 0.1)
            os.remove(temp_file)
        except Exception as e:
            print(f"Error in text-to-speech: {e}")

    print("Speaking: Are you visually impaired?")
    text_to_speech("Are you visually impaired?")
    print("Finished speaking, now listening...")

    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Say something (say 'yes' to redirect)...")
        try:
            audio = recognizer.listen(source)
            response = recognizer.recognize_google(audio).lower()
            print(f"Recognized: '{response}'")
            if any(word in response for word in ["yes", "yeah", "yep", "yup"]):
                return True
            return False
        except sr.UnknownValueError:
            print("Could not understand the audio.")
            return False
        except sr.RequestError as e:
            print(f"Google API error: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False

@app.route('/')
def index():
    print("Entering index route...")
    is_visually_impaired = ask_visually_impaired()
    print(f"ask_visually_impaired returned: {is_visually_impaired}")
    if is_visually_impaired:
        print("User said 'yes', redirecting to /visually")
        return redirect('/visually')
    print("User did not say 'yes', rendering index.html")
    return render_template('index.html')

@app.route('/visually', methods=['GET'])
def visually_impaired():
    global current_course, current_index, topics_content
    print("Entered /visually route, rendering visual.html")
    current_course = None
    current_index = 0
    topics_content = []
    
    threading.Thread(target=voice_navigation, daemon=True).start()
    
    initial_content = {"title": "Please select a course", "summary": "Use voice to select Python or Java to begin.", "example": ""}
    return render_template('visual.html', courses=visually.course_data, current_course=current_course, current_index=current_index, content=initial_content)

def voice_navigation():
    global current_course, current_index, topics_content
    available_courses = ["Python", "Java"]
    visually.speak_text("Welcome! Please say Python or Java to start a course.")
    while True:
        course_command = visually.recognize_command("Which course? Say Python or Java.")
        course = course_command.capitalize()
        if course in available_courses:
            current_course = course
            topics_content = visually.course_data[course]
            visually.speak_text(f"Starting {current_course} course.")
            current_index = 0
            break
        else:
            visually.speak_text("Invalid course. Please say Python or Java.")

    while current_course and current_index < len(topics_content):
        topic = topics_content[current_index]
        content = f"Topic: {topic['title']}. Summary: {topic['summary']}"
        if "example" in topic:
            content += f" Example: {topic['example']}"
        visually.speak_text(content)
        
        while True:
            command = visually.recognize_command("What would you like to do? Say repeat, next, previous, or stop.")
            if "repeat" in command:
                visually.speak_text(content)
            elif "next" in command:
                if current_index < len(topics_content) - 1:
                    current_index += 1
                    break
                else:
                    visually.speak_text("No more topics. Say repeat, previous, or stop.")
            elif "previous" in command:
                if current_index > 0:
                    current_index -= 1
                    break
                else:
                    visually.speak_text("Already at the first topic. Say repeat, next, or stop.")
            elif "stop" in command:
                visually.speak_text("Stopping the course. Goodbye.")
                current_course = None
                current_index = 0
                topics_content = []
                return
            time.sleep(0.5)
    if current_course:
        visually.speak_text("All topics covered. Goodbye.")
        current_course = None
        current_index = 0
        topics_content = []

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')

        # Google Form submission URL and data
        google_form_url = 'https://docs.google.com/forms/d/e/1FAIpQLSfUZskTLTH4VAsOUsSD7T1FLpMZrBQUIfL3ozTgiL-HAD2l6w/formResponse'
        form_data = {
            'entry.1087795436': name,  # Full Name
            'entry.1751763089': email,  # Email Address
            'entry.711138081': phone   # Phone Number
        }

        # Submit to Google Form
        try:
            response = requests.post(google_form_url, data=form_data)
            # Google Forms returns 200 on success, or 0 in no-cors mode
            if response.status_code in [200, 0]:
                print("Form submitted successfully, redirecting to index...")
                return redirect(url_for('index'))  # Redirect to index route
            else:
                print(f"Form submission failed with status {response.status_code}")
                return render_template('profile.html', error="Failed to submit form. Please try again.")
        except Exception as e:
            print(f"Error submitting to Google Form: {e}")
            return render_template('profile.html', error="An error occurred. Please try again.")

    # GET request: Render the profile page
    return render_template('profile.html')

@app.route('/api/state', methods=['GET'])
def get_state():
    global current_course, current_index, topics_content
    content = topics_content[current_index] if current_course and topics_content and current_index < len(topics_content) else None
    return jsonify({
        'course': current_course,
        'index': current_index,
        'total': len(topics_content),
        'content': content if content else {"title": "No content", "summary": "Please navigate using voice.", "example": ""}
    })

@app.route('/api/navigate', methods=['POST'])
def navigate():
    global current_course, current_index, topics_content
    command = request.json.get('command', '').lower()
    
    if not current_course or not topics_content:
        return jsonify({'error': 'No course selected'})

    if command == "repeat":
        topic = topics_content[current_index]
    elif command == "next":
        if current_index < len(topics_content) - 1:
            current_index += 1
    elif command == "previous":
        if current_index > 0:
            current_index -= 1
    elif command == "stop":
        current_course = None
        current_index = 0
        topics_content = []
        return jsonify({'command': 'stop'})
    
    topic = topics_content[current_index]
    return jsonify({
        'course': current_course,
        'index': current_index,
        'total': len(topics_content),
        'content': {"title": topic["title"], "summary": topic["summary"] or "No summary available", "example": topic.get("example", "")}
    })

@app.route('/courses')
def courses():
    return render_template('courses.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

# Hearing-impaired routes (integrated from previous solution)
@app.route('/hearing')
def hearing_home():
    courses = list(hearing.course_data.keys())
    return render_template('hearing.html', page='home', courses=courses)

@app.route('/hearing/course/<course_name>')
def hearing_course(course_name):
    topic_index = int(request.args.get('topic_index', 0))
    topic = hearing.get_topic_details(course_name, topic_index)
    if not topic:
        return "Topic not found", 404

    total_topics = len(hearing.get_course_topics(course_name))
    return render_template(
        'hearing.html',
        page='course',
        course_name=course_name,
        topic=topic,
        topic_index=topic_index,
        total_topics=total_topics
    )

@app.route('/video/<course_name>/<int:topic_index>')
def stream_video(course_name, topic_index):
    video_path = hearing.get_video_path(course_name, topic_index)
    if not video_path:
        return "Video not found", 404

    # Trigger audio playback in a separate thread
    def play_audio():
        hearing.play_topic_media(course_name, topic_index)

    threading.Thread(target=play_audio, daemon=True).start()

    # Stream video
    return send_file(video_path, mimetype='video/mp4')

if __name__ == '__main__':
    app.run(debug=True)