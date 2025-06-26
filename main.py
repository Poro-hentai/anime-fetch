import os
import uuid
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)
from pydub import AudioSegment, effects
from moviepy.editor import VideoFileClip, AudioFileClip

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

TOKEN = "8006836827:AAFQl8eVBBfI07CuHWh_oqxbFX5rYUyB-XE"  # Replace with your bot token
FX_FOLDER = "fx"

# Ensure fx folder exists
os.makedirs(FX_FOLDER, exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎶 Send me any audio or video file (Phonk, Pop, etc), and I'll return 5 cool FX-edited versions!"
    )

def apply_effects(original_audio):
    edited_versions = []

    # 1. Normalize + Fade
    fx1 = effects.normalize(original_audio).fade_in(1000).fade_out(1000)
    edited_versions.append(('normalized_fade', fx1))

    # 2. Bass Boost + Whoosh
    fx2 = original_audio.low_pass_filter(100).apply_gain(10)
    whoosh_path = os.path.join(FX_FOLDER, "whoosh.wav")
    if os.path.exists(whoosh_path):
        whoosh = AudioSegment.from_file(whoosh_path) - 5
        fx2 = fx2.overlay(whoosh, position=1000)
    edited_versions.append(('bass_whoosh', fx2))

    # 3. Slowed + Glitch
    fx3 = original_audio._spawn(original_audio.raw_data, overrides={
        "frame_rate": int(original_audio.frame_rate * 0.85)
    }).set_frame_rate(original_audio.frame_rate)
    glitch_path = os.path.join(FX_FOLDER, "glitch.wav")
    if os.path.exists(glitch_path):
        glitch = AudioSegment.from_file(glitch_path) - 7
        fx3 = fx3.overlay(glitch, position=1500)
    edited_versions.append(('slowed_glitch', fx3))

    # 4. Chipmunk + Sword
    fx4 = original_audio._spawn(original_audio.raw_data, overrides={
        "frame_rate": int(original_audio.frame_rate * 1.25)
    }).set_frame_rate(original_audio.frame_rate)
    sword_path = os.path.join(FX_FOLDER, "sword.wav")
    if os.path.exists(sword_path):
        sword = AudioSegment.from_file(sword_path) - 3
        fx4 = fx4.overlay(sword, position=800)
    edited_versions.append(('chipmunk_sword', fx4))

    # 5. Echo + Fade
    fx5 = (original_audio - 8).overlay(original_audio - 8, delay=250).fade_in(500).fade_out(500)
    edited_versions.append(('echo_fade', fx5))

    return edited_versions

async def process_audio(file_path, update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("🎧 Processing audio effects...")
        original = AudioSegment.from_file(file_path)
        edits = apply_effects(original)

        for name, audio in edits:
            temp = f"{uuid.uuid4()}.mp3"
            audio.export(temp, format="mp3")
            await update.message.reply_audio(audio=open(temp, "rb"), caption=f"🎵 {name.replace('_', ' ').title()}")
            os.remove(temp)

    except Exception as e:
        await update.message.reply_text(f"❌ Error processing audio: {e}")

async def process_video(file_path, update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("🎥 Extracting audio from video...")
        video = VideoFileClip(file_path)

        if video.audio is None:
            await update.message.reply_text("❌ No audio found in video.")
            video.close()
            return

        audio_file = f"{uuid.uuid4()}.mp3"
        video.audio.write_audiofile(audio_file, logger=None)

        original_audio = AudioSegment.from_file(audio_file)
        edits = apply_effects(original_audio)

        for name, edited_audio in edits:
            temp_audio = f"{uuid.uuid4()}.mp3"
            temp_video = f"{uuid.uuid4()}.mp4"
            edited_audio.export(temp_audio, format="mp3")

            final = video.set_audio(AudioFileClip(temp_audio))
            final.write_videofile(temp_video, codec="libx264", audio_codec="aac", verbose=False, logger=None)

            await update.message.reply_video(video=open(temp_video, "rb"), caption=f"🎬 {name.replace('_', ' ').title()}")

            os.remove(temp_audio)
            os.remove(temp_video)

        os.remove(audio_file)
        video.close()

    except Exception as e:
        await update.message.reply_text(f"❌ Error processing video: {e}")

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.audio or update.message.voice or update.message.video or update.message.document
    if not file:
        await update.message.reply_text("❌ Please send a valid audio or video file.")
        return

    f = await file.get_file()
    file_ext = os.path.splitext(f.file_path)[-1] or ".media"
    file_path = f"{uuid.uuid4()}{file_ext}"

    await f.download_to_drive(file_path)

    try:
        if file.mime_type.startswith("audio") or update.message.voice:
            await process_audio(file_path, update, context)
        elif file.mime_type.startswith("video") or file.mime_type == "video/mp4":
            await process_video(file_path, update, context)
        else:
            await update.message.reply_text("❌ Unsupported media type.")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        filters.AUDIO | filters.VIDEO | filters.VOICE | filters.Document.VIDEO, handle_media
    ))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
