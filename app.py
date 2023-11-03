# app.py

from flask import Flask, render_template, request, redirect, url_for
import os
import mimetypes
import moviepy.editor as mp
import speech_recognition as sr

app = Flask(__name__)

# Configure the upload folder and allowed file extensions
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'flv', 'mkv', 'mp3', 'wav', 'ogg', 'webm'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_duration(filename):
    try:
        # Calculate the duration of the file using moviepy
        video_clip = mp.VideoFileClip(filename)
        duration = video_clip.duration
        video_clip.close()
        return duration
    except Exception as e:
        print(f"Error calculating duration: {e}")
        return None

def get_file_info():
    file_info = []  # Initialize an empty list to store file details
    # List all files in the "uploads" folder and extract their information
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.isfile(file_path):
            file_name = filename
            file_type = mimetypes.guess_type(file_path)[0]
            file_size = os.path.getsize(file_path)
            file_duration = calculate_duration(file_path)
            if file_duration is not None:
                file_info.append((file_name, file_type, file_size, file_duration))
    return file_info

@app.route('/')
def index():
    file_info = get_file_info()
    return render_template('index.html', file_info=file_info, text="", file_duration=0)  # Initialize file_duration as 0

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)

    if file and allowed_file(file.filename):
        # Save the uploaded file
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)

        # Calculate the file duration
        file_duration = calculate_duration(filename)

        if file_duration is None:
            return "Error: Unable to calculate file duration."

        # Convert video to audio (if needed)
        if filename.lower().endswith(('.mp4', '.avi', '.flv', '.mkv')):
            video_clip = mp.VideoFileClip(filename)
            audio_clip = video_clip.audio
            audio_file = os.path.join(app.config['UPLOAD_FOLDER'], f"{file.filename}.wav")
            audio_clip.write_audiofile(audio_file)
            audio_clip.close()
            video_clip.close()
        else:
            audio_file = filename

        # Perform speech recognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio)

        file_info = get_file_info()  # Update the file information
        return render_template('index.html', text=text, file_info=file_info, file_duration=file_duration)

    return redirect(request.url)

if __name__ == '__main__':
    app.run(debug=True)
