# [@DotaUpcomingMatchesBot](https://t.me/DotaUpcomingMatchesBot)
Telegram bot that shows upcoming Dota2 matches and allows following to get 
notifications about matches.

Take a look at 
[this reddit post](https://www.reddit.com/r/DotA2/comments/10ifgvy/telegram_bot_that_tracks_upcoming_dota2_matches/)
for the details.


# Running
```bash
# Any string. But better contain your email. 
# Will be sent as User-Agent to liquipedia. 
# See https://liquipedia.net/api-terms-of-use
export LIQUIPEDIA_APP_NAME=YOUR_APP_NAME

# Id/Secret for twitch API. See https://dev.twitch.tv for details
export TWITCH_ID=YOUR_TWITCH_ID
export TWITCH_SECRET=YOUR_TWITCH_SECRET

# Telegram bot TOKEN. 
# See @BotFather https://core.telegram.org/bots/features#botfather for details
export TELEGRAM_BOT_TOKEN=YOUR_TOKEN

# A user with this ID will be able to call admin commands. Currently this is
# only /stats command that prints total users count.
export ADMIN_USER_ID=0

python -m pip install -r requirements
python telegram_bot/main.py
```

# Feedback and pull request
Feel free to submit feature requests or suggestions. Pull requests are welcome =)
