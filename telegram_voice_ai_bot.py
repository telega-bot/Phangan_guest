
import os
import openai
import tempfile
import speech_recognition as sr
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    MessageHandler, filters
)
from pydub import AudioSegment

# === ЗАМЕНИ на свои ключи ===
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Память для каждого пользователя (контекст)
user_contexts = {}

# Кнопки
keyboard = ReplyKeyboardMarkup(
    [["rent", "places", "trips", "support"]],
    resize_keyboard=True
)

# Обработка текстовых сообщений
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # Добавляем сообщение в историю
    if user_id not in user_contexts:
        user_contexts[user_id] = []
    user_contexts[user_id].append({"role": "user", "content": text})

    # Ограничим длину истории (например, 100 сообщений)
    user_contexts[user_id] = user_contexts[user_id][-10:]

    # Получаем ответ от ChatGPT
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=user_contexts[user_id]
    )

    reply = response["choices"][0]["message"]["content"]
    user_contexts[user_id].append({"role": "assistant", "content": reply})
    await update.message.reply_text(reply, reply_markup=keyboard)

# Обработка голосовых сообщений
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    voice = await update.message.voice.get_file()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as f_ogg:
        await voice.download_to_drive(custom_path=f_ogg.name)
        ogg_path = f_ogg.name

    wav_path = ogg_path.replace(".ogg", ".wav")
    AudioSegment.from_ogg(ogg_path).export(wav_path, format="wav")

    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            update.message.text = text  # подставим как обычный текст
            await handle_text(update, context)
        except sr.UnknownValueError:
            await update.message.reply_text("Couldn't recognize the voice 😔")

    os.remove(ogg_path)
    os.remove(wav_path)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! I'm a voice AI bot with buttons. Ask a question or send a voice message 🎤", reply_markup=keyboard)

# Создаем приложение
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.VOICE, handle_voice))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

# Запуск
app.run_polling()
