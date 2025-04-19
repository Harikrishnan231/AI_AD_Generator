import os
import streamlit as st
import requests
import shutil
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import numpy as np
from tempfile import NamedTemporaryFile
from duckduckgo_search import DDGS
import google.generativeai as genai
from TTS.api import TTS
from moviepy.editor import (
    VideoFileClip, ImageClip, concatenate_videoclips,
    AudioFileClip, CompositeVideoClip, TextClip, CompositeAudioClip
)
from moviepy.audio.fx.all import audio_fadein, audio_fadeout
import textwrap
import threading

# === TEMP DIRECTORY SETUP === #
TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

def cleanup_temp_folder(delay_seconds=600):
    def delete_folder():
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
            print("🧹 Temp folder cleaned up.")
    threading.Timer(delay_seconds, delete_folder).start()

# === GEMINI API SETUP === #
genai.configure(api_key="AIzaSyCagnPGqPk2pPzyvkaA6DYxt1ReIVN2tOE")

# === AGENT FUNCTIONS === #
def generate_text(prompt, model="gemini-1.5-flash"):
    model = genai.GenerativeModel(model)
    response = model.generate_content(prompt)
    return response.text.strip()

def research_agent():
    return generate_text("Pick a trending topic of interest globally.")

def research_assistant(topic):
    return generate_text(f"Give a short 200-word casual paragraph about {topic}.")

def script_writer(conclusion):
    return generate_text(f"Write a casual, naturally flowing 200-word paragraph based on this info: {conclusion}")

def stylish_writer(script):
    return generate_text(f"Make this more rhythmic and natural for speech, with good punctuation and flow: {script}")

def bias_checker(script):
    return generate_text(f"Is this biased or neutral? Summarize briefly: {script}")

def sender_agent(summary):
    return f"{summary}\n\nCall to action: Visit us at example.com"

def full_script_pipeline(topic):
    conclusion = research_assistant(topic)
    script = script_writer(conclusion)
    styled_script = stylish_writer(script)
    bias_summary = bias_checker(styled_script)
    final_message = sender_agent(styled_script)
    return conclusion, script, styled_script, bias_summary, final_message

# === BACKGROUND MUSIC SELECTION === #
def select_background_music(keyword):
    music_map = {
        "technology": "tech_music.mp3",
        "health": "calm_music.mp3",
        "sports": "energetic_music.mp3",
        "finance": "corporate_music.mp3",
        "education": "inspiring_music.mp3"
    }
    for key in music_map:
        if key in keyword.lower():
            return music_map[key]
    return "AI_Avatar_Agent_Bot/default_music.mp3"

def keyword_extractor(script):
    prompt = f"""From the following script, identify the most important subject or topic discussed. Return only one phrase that represents the key point of the content.\nScript:\n{script}\n"""
    keyword = generate_text(prompt)
    return keyword.strip().replace("\n", "")

# === TEXT-TO-SPEECH FUNCTION === #
def text_to_speech(text, speaker, language="en"):
    tts = TTS(model_name="tts_models/multilingual/multi-dataset/your_tts", gpu=False)
    audio_path = os.path.join(TEMP_DIR, "final_audio.wav")
    tts.tts_to_file(text=text, speaker=speaker, language=language, file_path=audio_path)
    return audio_path

# === AUDIO SEGMENTATION === #
def calculate_audio_segments(audio_path):
    audio_clip = AudioFileClip(audio_path)
    audio_duration = audio_clip.duration
    num_segments = int(audio_duration // 10)
    remaining_duration = audio_duration % 10
    return num_segments, remaining_duration

# === IMAGE UPLOAD HANDLING === #
def handle_image_upload(st, auto_selected_images, selected_images):
    num_images_needed, _ = calculate_audio_segments("audio_path")
    images_available = len(selected_images) + len(auto_selected_images)
    if images_available < num_images_needed:
        st.warning(f"⚠️ You need at least {num_images_needed} images. Currently, you have {images_available}.")
    return images_available, num_images_needed

# === TEXT OVERLAY IMAGE === #
def create_text_image(text, size=(700, 150), font_size=30):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()

    # Wrap text to fit inside the width
    max_width = size[0] - 40  # add some horizontal padding
    lines = []
    words = text.split()
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        line_width = draw.textlength(test_line, font=font)
        if line_width <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    lines.append(line)

    # Center the lines vertically
    y = (size[1] - len(lines) * font_size) / 2
    for line in lines:
        line_width = draw.textlength(line, font=font)
        x = (size[0] - line_width) / 2
        draw.text((x, y), line, font=font, fill="white")
        y += font_size + 5  # line spacing

    return img


def split_script_into_chunks(script, total_duration, chunk_duration=5):
    sentences = textwrap.wrap(script, width=40)
    num_chunks = int(total_duration // chunk_duration)
    if num_chunks == 0:
        return [(script, 0, total_duration)]
    chunks = []
    chunk_len = len(sentences) // num_chunks or 1
    start_time = 0
    for i in range(0, len(sentences), chunk_len):
        chunk_text = ' '.join(sentences[i:i+chunk_len])
        duration = chunk_duration
        chunks.append((chunk_text, start_time, duration))
        start_time += duration
    return chunks

# === FINAL VIDEO GENERATION === #
def generate_final_video(user_video_path, images, audio_path, output_path="final_output.mp4", keyword="", final_message=""):
    user_clip = VideoFileClip(user_video_path).without_audio().resize(width=720)
    audio_narration = AudioFileClip(audio_path)
    total_audio_duration = audio_narration.duration
    image_duration = total_audio_duration / len(images) if images else 0
    overlay_clips, text_clips = [], []

    start_time = 0
    for img_file in images:
        img = Image.open(img_file).convert("RGB")  # Convert image to RGB format
        img_np = np.array(img)
        img_clip = (
            ImageClip(img_np)
            .set_duration(image_duration)
            .resize(width=720)
            .set_position("center")
            .set_start(start_time)
            .fadein(0.5)
            .fadeout(0.5)
        )

        overlay_clips.append(img_clip)
        start_time += image_duration

    text_chunks = split_script_into_chunks(final_message, total_audio_duration, chunk_duration=5)
    for chunk_text, start, duration in text_chunks:
        text_image = create_text_image(chunk_text, size=(700, 150), font_size=30)
        text_overlay_path = os.path.join(TEMP_DIR, f"text_overlay_{int(start)}.png")
        Image.fromarray(np.array(text_image)).save(text_overlay_path)
        dynamic_text_clip = (
            ImageClip(text_overlay_path)
            .set_duration(duration)
            .set_position(("center", "bottom"))
            .set_start(start)
            .fadein(0.5)
            .fadeout(0.5)
        )
        text_clips.append(dynamic_text_clip)

    full_composite = CompositeVideoClip([user_clip] + overlay_clips + text_clips).set_duration(total_audio_duration)
    bg_music_path = select_background_music(keyword)
    if not os.path.exists(bg_music_path):
        bg_music_path = "AI_Avatar_Agent_Bot/default_music.mp3"
    background_music = AudioFileClip(bg_music_path).volumex(0.1).set_duration(audio_narration.duration)
    final_audio = CompositeAudioClip([audio_narration, background_music])
    final_video = full_composite.set_audio(final_audio)

    final_path = os.path.join(TEMP_DIR, output_path)
    final_video.write_videofile(final_path, codec="libx264", audio_codec="aac")
    return final_path

# === STREAMLIT UI === #
st.set_page_config(page_title="🎙️ AI Spokesperson Video Generator")

if "auto_selected_images" not in st.session_state:
    st.session_state.auto_selected_images = []

auto_selected_images = st.session_state.auto_selected_images
selected_images = []

st.title("🎙️ AI Spokesperson Video Generator")
voice_choice = st.selectbox("Choose Voice:", ["Male (male-en-2)", "Female (female-en-5)"])
speaker_id = "male-en-2" if "Male" in voice_choice else "female-en-5"
language_choice = st.selectbox("Choose Language:", ["en", "fr-fr", "pt-br"])

styled_script = ""
audio_path = ""

mode = st.radio("Select mode:", ["Manual Mode", "Auto Agent Mode"])
topic_input = st.text_input("Enter your topic (optional in auto mode):")

if mode:
    topic = topic_input if topic_input else research_agent()
    st.success(f"✅ Topic: {topic}")
    conclusion, script, styled_script, bias_summary, final_message = full_script_pipeline(topic)
    st.markdown("### 📜 Styled Script:")
    st.code(styled_script)
    audio_path = text_to_speech(final_message, speaker=speaker_id, language=language_choice)
    st.audio(audio_path)

st.markdown("### 🤖 Auto Image Selection from Script")
if styled_script and st.button("🔍 Auto Search Images"):
    keyword = keyword_extractor(styled_script)
    st.info(f"🔑 Keyword: {keyword}")
    with st.spinner("Searching images..."):
        with DDGS() as ddgs:
            results = [r for r in ddgs.images(keyword, max_results=3)]
        for idx, result in enumerate(results):
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(result["image"], headers=headers, timeout=10)
                img = Image.open(BytesIO(response.content))
                img_path = os.path.join(TEMP_DIR, f"auto_img_{idx}.png")
                img.save(img_path)
                st.session_state.auto_selected_images.append(img_path)
                st.image(img, caption=f"Auto Image {idx+1}", use_column_width=True)
            except Exception as e:
                st.warning(f"Image {idx+1} failed: {e}")

st.markdown("### 📸 Add Your Own Images")
user_images = st.file_uploader("Upload images", type=["png", "jpg"], accept_multiple_files=True)
if user_images:
    for idx, file in enumerate(user_images):
        with NamedTemporaryFile(delete=False, dir=TEMP_DIR, suffix=".png") as tmp_img:
            tmp_img.write(file.read())
            selected_images.append(tmp_img.name)
            st.image(tmp_img.name, caption=f"Uploaded Image {idx+1}", use_column_width=True)

# === VIDEO PATH (hardcoded or uploaded) === #
user_video_path = r"AI_Avatar_Agent_Bot\uploads\WIN_20250418_10_53_30_Pro.mp4"
if os.path.exists(user_video_path) and (selected_images or auto_selected_images) and audio_path:
    if st.button("🎬 Generate Final Video"):
        with st.spinner("Creating final video..."):
            images_to_use = selected_images + auto_selected_images
            final_path = generate_final_video(user_video_path, images_to_use, audio_path, "final_output.mp4", keyword=topic, final_message=final_message)
            st.success("✅ Video created successfully!")
            st.video(final_path)
            st.download_button("📥 Download Final Video", open(final_path, "rb"), file_name="final_output.mp4")
            cleanup_temp_folder(delay_seconds=600)
else:
    st.info("📥 Please provide a valid video path and add/select images to proceed.")

