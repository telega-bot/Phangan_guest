import os
import openai
import tempfile
import speech_recognition as sr
from pydub import AudioSegment
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Load tokens from environment
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! 👋 Send me a voice or text message and I'll reply using AI 🤖")


# Handle voice messages
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    voice = update.message.voice

    # Download voice file
    file = await context.bot.get_file(voice.file_id)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as f_ogg:
        await file.download_to_drive(f_ogg.name)

        # Convert OGG to WAV
        sound = AudioSegment.from_ogg(f_ogg.name)
        wav_path = f_ogg.name.replace(".ogg", ".wav")
        sound.export(wav_path, format="wav")

    # Transcribe audio
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
        try:
            user_text = recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            await update.message.reply_text("❗ I couldn't understand the audio.")
            return
        except Exception as e:
            await update.message.reply_text(f"⚠️ Speech recognition error: {e}")
            return

    await update.message.reply_text(f"🗣 You said: {user_text}")

    # Send to OpenAI
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_text}],
        )
        ai_reply = response.choices[0].message.content
    except Exception as e:
        ai_reply = f"⚠️ OpenAI error: {e}"

    await update.message.reply_text(f"🤖 {ai_reply}")


# Handle text messages
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_text}],
        )
        ai_reply = response.choices[0].message["content"]
    except Exception as e:
        ai_reply = f"⚠️ OpenAI error: {e}"

    await update.message.reply_text(f"🤖 {ai_reply}")


# Main function to start the bot
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.run_polling()


if __name__ == "__main__":
    main()
