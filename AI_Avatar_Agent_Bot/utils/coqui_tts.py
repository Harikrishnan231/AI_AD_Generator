from TTS.api import TTS

# Load model
tts = TTS(model_name="tts_models/multilingual/multi-dataset/your_tts", gpu=True)

# Input
# text = input("Enter the text to convert to speech: ")
# voice_type = input("Choose voice (m for male / f for female): ").strip().lower()

# Generate and save audio
def text_to_speech(text, speaker="male-en-2"):
    tts = TTS(model_name="tts_models/multilingual/multi-dataset/your_tts", gpu=True)
    tts.tts_to_file(
        text=text,
        speaker=speaker,
        language="en",
        file_path="AI_Avatar_Agent_Bot/output/final_voice.wav"
    )
    print(f"✅ Audio generated using {{speaker}}. File saved as AI_Avatar_Agent_Bot/output/final_voice.wav")
