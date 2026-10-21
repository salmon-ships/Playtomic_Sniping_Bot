# Playtomic-Sniping-Bot

This bot detects available time slots on Playtomic and notifies the user via Telegram when matching slots are found. You can configure filter criteria to search for specific times, durations, and preferred courts. The bot can be run either locally or through GitHub Actions.

Important considerations for usage:

- To run locally, copy `config.json` (a template) to `config.local.json` and fill in your values. `config.local.json` is git-ignored.
- Store the necessary secrets in GitHub if the bot is to run via GitHub Actions.
- Create a Telegram bot via @BotFather and set `telegram_bot_token` (secret `TELEGRAM_BOT_TOKEN` on GitHub). Each recipient must start a chat with the bot and subscribe to one or more cities: `/subscribe mannheim berlin`, `/subscribe all`, `/unsubscribe mannheim`, `/stop` (unsubscribe from everything), `/start` (show available cities and current subscriptions). On GitHub Actions, `update_subscribers.py` processes these commands on every run and stores the subscriptions encrypted in `subscribers.enc` (the repo is public, so chat IDs are never committed in plaintext). Generate the key once with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` and store it as the GitHub secret `SUBSCRIBERS_KEY`; keep a copy, since losing it makes `subscribers.enc` unreadable. Locally, chat IDs in `chat_ids` in `config.local.json` receive all cities.
- Cities are defined in `cities.json` (key, `name`, Playtomic `url`, `courts`). To add a city, add another entry; no code changes are needed. Cities without subscribers are skipped.
- The bot is set to German by default, so make sure to adjust the notification language if necessary.
- Customize the Playtomic booking URL for your club in `cities.json`.
- Set the filter criteria by defining `start_time`, `days` and `min_duration` in `main.py`, and the courts per city in `cities.json`.
