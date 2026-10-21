"""Pflegt subscribers.enc anhand der Telegram-Befehle /subscribe, /unsubscribe, /stop und /start."""
import json
import os
import sys
from pathlib import Path

import requests
from cryptography.fernet import Fernet

from functions import get_telegram_token

script_dir = Path(__file__).parent
# Verschlüsselt, da das Repo öffentlich ist; Schlüssel kommt aus dem Secret SUBSCRIBERS_KEY
SUBSCRIBERS_FILE = script_dir / "subscribers.enc"


def _fernet():
    key = os.getenv("SUBSCRIBERS_KEY")
    if not key:
        raise RuntimeError("Umgebungsvariable SUBSCRIBERS_KEY ist nicht gesetzt.")
    return Fernet(key)


def load_subscribers(path=SUBSCRIBERS_FILE):
    if path.exists():
        return json.loads(_fernet().decrypt(path.read_bytes()))
    return {"subscribers": {}, "last_update_id": 0}


def save_subscribers(data, path=SUBSCRIBERS_FILE):
    path.write_bytes(_fernet().encrypt(json.dumps(data).encode()))


def describe_error(e):
    # Ohne URL ausgeben, da diese das Bot-Token enthält
    if e.response is None:
        return type(e).__name__
    try:
        description = e.response.json().get("description", "")
    except ValueError:
        description = ""
    return f"HTTP {e.response.status_code} {description}".strip()


def reply(token, chat_id, text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10,
        ).raise_for_status()
    except requests.RequestException as e:
        print(f"Fehler beim Senden der Antwort an {chat_id}: {describe_error(e)}")


def status_text(cities, subscribed):
    available = ", ".join(cities)
    current = ", ".join(subscribed) if subscribed else "keine"
    return (
        f"Verfügbare Städte: {available}\n"
        f"Deine Abos: {current}\n\n"
        "/subscribe <Stadt> [<Stadt> ...] oder /subscribe all\n"
        "/unsubscribe <Stadt> [<Stadt> ...]\n"
        "/stop - alle Abos beenden"
    )


def handle_command(command, args, chat_id, subscriptions, cities):
    """Verarbeitet einen Befehl und gibt die Antwort zurück (None = keine Antwort)."""
    subscribed = subscriptions.get(chat_id, [])

    if command in ("/subscribe", "/unsubscribe") and args:
        wanted = list(cities) if "all" in args else args
        unknown = [a for a in wanted if a not in cities]
        if unknown:
            return f"Unbekannte Stadt: {', '.join(unknown)}\n\n{status_text(cities, subscribed)}"
        if command == "/subscribe":
            subscribed = subscribed + [c for c in wanted if c not in subscribed]
        else:
            subscribed = [c for c in subscribed if c not in wanted]
    elif command == "/stop":
        subscribed = []
    elif command not in ("/start", "/help", "/cities", "/subscribe", "/unsubscribe"):
        return None

    if subscribed:
        subscriptions[chat_id] = subscribed
    else:
        subscriptions.pop(chat_id, None)
    return status_text(cities, subscribed)


def main():
    token = get_telegram_token()
    with open(script_dir / "cities.json", "r") as file:
        cities = json.load(file)
    data = load_subscribers()
    original = json.loads(json.dumps(data))
    subscriptions = data["subscribers"]

    try:
        response = requests.get(
            f"https://api.telegram.org/bot{token}/getUpdates",
            params={
                "offset": data["last_update_id"] + 1,
                "timeout": 0,
                "allowed_updates": json.dumps(["message"]),
            },
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Fehler beim Abrufen der Telegram-Updates: {describe_error(e)}")
        sys.exit(1)

    updates = response.json().get("result", [])
    print(f"{len(updates)} neue Telegram-Updates abgerufen.")
    for update in updates:
        data["last_update_id"] = max(data["last_update_id"], update["update_id"])
        message = update.get("message", {})
        text = (message.get("text") or "").strip()
        if not text.startswith("/"):
            continue
        parts = text.lower().split()
        command = parts[0].split("@")[0]
        chat_id = str(message["chat"]["id"])

        answer = handle_command(command, parts[1:], chat_id, subscriptions, cities)
        if answer:
            reply(token, chat_id, answer)
            print(f"Chat {chat_id}: {command} {' '.join(parts[1:])}".strip())

    # Fernet-Tokens sind nie identisch; nur bei Änderung speichern, um sinnlose Commits zu vermeiden
    if data != original:
        save_subscribers(data)


if __name__ == "__main__":
    main()
