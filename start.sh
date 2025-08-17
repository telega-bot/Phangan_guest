#!/usr/bin/env bash

apt-get update && apt-get install -y ffmpeg

python telegram_voice_ai_bot.py