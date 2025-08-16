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

# Память для контекста
user_context = {}

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await context.bot.get_file(update.message.voice.file_id)
    ogg_path = "voice.ogg"
    wav_path = "voice.wav"
    await file.download_to_drive(ogg_path)

    # Конвертируем OGG -> WAV
    sound = AudioSegment.from_ogg(ogg_path)
    sound.export(wav_path, format="wav")

    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio)
    except:
        await update.message.reply_text("Voice recognition failed😔")
        return

    await update.message.reply_text(f"You said: {text}")

    # Контекст
    chat_id = str(update.effective_chat.id)
    prev = user_context.get(chat_id, "")
    full_prompt = prev + "\nUser: " + text + "\nAssistant:"

    # Запрос к OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": full_prompt}],
    )
    reply = response.choices[0].message.content.strip()
    user_context[chat_id] = full_prompt + reply

    await update.message.reply_text(reply)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    print("🤖 Bot is running...")
    app.run_polling()
