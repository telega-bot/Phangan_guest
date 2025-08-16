import os
import openai
import speech_recognition as sr
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    ContextTypes,
    filters,
)
from pydub import AudioSegment

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

user_context = {}

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await context.bot.get_file(update.message.voice.file_id)
    ogg_path = "voice.ogg"
    wav_path = "voice.wav"
    await file.download_to_drive(ogg_path)

    # Convert OGG to WAV
    sound = AudioSegment.from_ogg(ogg_path)
    sound.export(wav_path, format="wav")

    # Transcribe voice to text
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio)
    except:
        await update.message.reply_text("Sorry, I couldn't understand your voice.")
        return

    await update.message.reply_text(f"You said: {text}")

    # Build context and get GPT reply
    chat_id = str(update.effective_chat.id)
    previous = user_context.get(chat_id, "")
    prompt = previous + f"\nUser: {text}\nAssistant:"

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    reply = response.choices[0].message.content.strip()
    user_context[chat_id] = prompt + reply

    await update.message.reply_text(reply)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    print("🤖 Voice bot is running...")
    app.run_polling()
