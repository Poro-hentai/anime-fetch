import os
import uuid
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from pydub import AudioSegment, effects
from moviepy.editor import VideoFileClip, AudioFileClip

# Your token
TOKEN = "8006836827:AAERFD1tDpBDJhvKm_AHy20uSAzZdoRwbZc"

# Create fx folder if not exists
os.makedirs("fx", exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send me any audio or video (Phonk, Pop, English etc), I'll return 5 cool edited FX versions!")

def apply_effects(original_audio):
    edited_versions = []

    # 1. Normalized + Fade
    fx1 = effects.normalize(original_audio).fade_in(1000).fade_out(1000)
    edited_versions.append(('normalized_fade', fx1))

    # 2. Bass Boost + Whoosh
    fx2 = original_audio.low_pass_filter(100).apply_gain(10)
    if os.path.exists("fx/whoosh.wav"):
        whoosh = AudioSegment.from_file("fx/whoosh.wav") - 5
        fx2 = fx2.overlay(whoosh, position=1000)
    edited_versions.append(('bass_whoosh', fx2))

    # 3. Slowed + Glitch
    fx3 = original_audio._spawn(original_audio.raw_data, overrides={
        "frame_rate": int(original_audio.frame_rate * 0.85)
    }).set_frame_rate(original_audio.frame_rate)
    if os.path.exists("fx/glitch.wav"):
        glitch = AudioSegment.from_file("fx/glitch.wav") - 7
        fx3 = fx3.overlay(glitch, position=1500)
    edited_versions.append(('slowed_glitch', fx3))

    # 4. Chipmunk + Sword
    fx4 = original_audio._spawn(original_audio.raw_data, overrides={
        "frame_rate": int(original_audio.frame_rate * 1.25)
    }).set_frame_rate(original_audio.frame_rate)
    if os.path.exists("fx/sword.wav"):
        sword = AudioSegment.from_file("fx/sword.wav") - 3
        fx4 = fx4.overlay(sword, position=800)
    edited_versions.append(('chipmunk_sword', fx4))

    # 5. Echo + Fade
    fx5 = (original_audio - 8).overlay(original_audio - 8, delay=250).fade_in(500).fade_out(500)
    edited_versions.append(('echo_fade', fx5))

    return edited_versions

async def process_audio(file_path, update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎧 Processing your audio...")
    original = AudioSegment.from_file(file_path)
    edits = apply_effects(original)

    for name, audio in edits:
        temp = f"{uuid.uuid4()}.mp3"
        audio.export(temp, format="mp3")
        await update.message.reply_audio(audio=open(temp, "rb"), caption=f"🎵 {name}")
        os.remove(temp)

async def process_video(file_path, update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎥 Extracting and editing audio...")
    video = VideoFileClip(file_path)
    audio_file = f"{uuid.uuid4()}.mp3"
    video.audio.write_audiofile(audio_file)

    edits = apply_effects(AudioSegment.from_file(audio_file))

    for name, edited_audio in edits:
        temp_audio = f"{uuid.uuid4()}.mp3"
        temp_video = f"{uuid.uuid4()}.mp4"
        edited_audio.export(temp_audio, format="mp3")
        final = video.set_audio(AudioFileClip(temp_audio))
        final.write_videofile(temp_video, codec="libx264", audio_codec="aac")
        await update.message.reply_video(video=open(temp_video, "rb"), caption=f"🎬 {name}")
        os.remove(temp_audio)
        os.remove(temp_video)

    os.remove(audio_file)
    video.close()

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.audio or update.message.voice or update.message.video or update.message.document
    if not file:
        await update.message.reply_text("❌ Only audio/video supported.")
        return

    f = await file.get_file()
    file_path = f"{uuid.uuid4()}"
    await f.download_to_drive(file_path)

    if file.mime_type.startswith("audio"):
        await process_audio(file_path, update, context)
    elif file.mime_type.startswith("video"):
        await process_video(file_path, update, context)

    os.remove(file_path)

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.AUDIO | filters.VIDEO | filters.VOICE | filters.Document.VIDEO, handle_media))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
