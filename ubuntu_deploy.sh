#!/bin/bash
set -e

apt update & apt install -y git python3-pip python3

ssh-keygen -t ed25519 -C "s.krivohatskiy@gmail.com"

read -p "$(cat /root/.ssh/id_ed25519.pub)"

git clone git@github.com:SergeyKrivohatskiy/dota2_matches_bot.git
cd dota2_matches_bot/
python3 -m pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN=""
python3 telegram_bot/main.py
