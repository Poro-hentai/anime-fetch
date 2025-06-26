import os
import uuid
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)
from pydub import AudioSegment, effects
from moviepy.editor import VideoFileClip, AudioFileClip

# Logging setup
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
)

TOKEN = "YOUR_BOT_TOKEN"  # Replace with your actual token
FX_FOLDER = "fx"
os.makedirs(FX_FOLDER, exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎧 Send me an audio/video (Phonk, Pop, Remix, etc.)\n"
        "I'll return 5 FX-edited versions! Effects: Normalize, Bass, Glitch, Chipmunk, Echo."
    )

def apply_effects(original_audio: AudioSegment):
    edited_versions = []

    fx1 = effects.normalize(original_audio).fade_in(1000).fade_out(1000)
    edited_versions.append(("Normalized + Fade", fx1))

    fx2 = original_audio.low_pass_filter(100).apply_gain(10)
    whoosh = os.path.join(FX_FOLDER, "whoosh.wav")
    if os.path.exists(whoosh):
        fx2 = fx2.overlay(AudioSegment.from_file(whoosh) - 5, position=1000)
    edited_versions.append(("Bass Boost + Whoosh", fx2))

    fx3 = original_audio._spawn(original_audio.raw_data, {
        "frame_rate": int(original_audio.frame_rate * 0.85)
    }).set_frame_rate(original_audio.frame_rate)
    glitch = os.path.join(FX_FOLDER, "glitch.wav")
    if os.path.exists(glitch):
        fx3 = fx3.overlay(AudioSegment.from_file(glitch) - 7, position=1500)
    edited_versions.append(("Slowed + Glitch", fx3))

    fx4 = original_audio._spawn(original_audio.raw_data, {
        "frame_rate": int(original_audio.frame_rate * 1.25)
    }).set_frame_rate(original_audio.frame_rate)
    sword = os.path.join(FX_FOLDER, "sword.wav")
    if os.path.exists(sword):
        fx4 = fx4.overlay(AudioSegment.from_file(sword) - 3, position=800)
    edited_versions.append(("Chipmunk + Sword", fx4))

    fx5 = (original_audio - 8).overlay(original_audio - 8, delay=250).fade_in(500).fade_out(500)
    edited_versions.append(("Echo + Fade", fx5))

    return edited_versions

async def process_audio(file_path, update, context):
    try:
        await update.message.reply_text("🎧 Processing audio...")
        original = AudioSegment.from_file(file_path)
        for name, fx in apply_effects(original):
            temp = f"{uuid.uuid4()}.mp3"
            fx.export(temp, format="mp3")
            await update.message.reply_audio(audio=open(temp, "rb"), caption=f"🎵 {name}")
            os.remove(temp)
    except Exception as e:
        logging.exception(e)
        await update.message.reply_text(f"❌ Error: {e}")

async def process_video(file_path, update, context):
    try:
        await update.message.reply_text("🎥 Extracting & editing video audio...")
        video = VideoFileClip(file_path)
        if not video.audio:
            await update.message.reply_text("❌ No audio track found.")
            return

        base_audio = f"{uuid.uuid4()}.mp3"
        video.audio.write_audiofile(base_audio, logger=None)
        original = AudioSegment.from_file(base_audio)

        for name, fx in apply_effects(original):
            fx_audio = f"{uuid.uuid4()}.mp3"
            fx.export(fx_audio, format="mp3")
            out_video = f"{uuid.uuid4()}.mp4"
            video.set_audio(AudioFileClip(fx_audio)).write_videofile(
                out_video, codec="libx264", audio_codec="aac", logger=None, verbose=False
            )
            await update.message.reply_video(video=open(out_video, "rb"), caption=f"🎬 {name}")
            os.remove(fx_audio)
            os.remove(out_video)

        os.remove(base_audio)
        video.close()

    except Exception as e:
        logging.exception(e)
        await update.message.reply_text(f"❌ Video error: {e}")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    file = msg.audio or msg.voice or msg.video or msg.document
    if not file:
        await msg.reply_text("❌ Only audio/video supported.")
        return

    f = await file.get_file()
    ext = os.path.splitext(f.file_path)[-1] or ".media"
    temp_file = f"{uuid.uuid4()}{ext}"
    await f.download_to_drive(temp_file)

    try:
        if file.mime_type.startswith("audio") or msg.voice:
            await process_audio(temp_file, update, context)
        elif file.mime_type.startswith("video") or file.mime_type == "video/mp4":
            await process_video(temp_file, update, context)
        else:
            await msg.reply_text("❌ Unsupported file type.")
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(
        filters.AUDIO | filters.VIDEO | filters.VOICE | filters.Document.VIDEO,
        handle
    ))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
