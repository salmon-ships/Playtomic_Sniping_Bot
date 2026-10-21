# Playtomic-Sniping-Bot

This bot detects available time slots on Playtomic and notifies the user via Telegram when matching slots are found. You can configure filter criteria to search for specific times, durations, and preferred courts. The bot can be run either locally or through GitHub Actions.

Important considerations for usage:

- To run locally, copy `config.json` (a template) to `config.local.json` and fill in your values. `config.local.json` is git-ignored.
- Store the necessary secrets in GitHub if the bot is to run via GitHub Actions.
- Create a Telegram bot via @BotFather and set `telegram_bot_token` (secret `TELEGRAM_BOT_TOKEN` on GitHub). Each recipient must start a chat with the bot first; put their chat IDs in `chat_ids` (comma-separated secret `CHAT_IDS` on GitHub).
- The bot is set to German by default, so make sure to adjust the notification language if necessary.
- Customize the Playtomic booking URL for your club in the @main.py file.
- Set the filter criteria by defining parameters like start_time, days, court_names, and min_duration.
