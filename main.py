import json
import os
from pathlib import Path

import pandas as pd

from functions import search_for_free_padel_slots, send_telegram, find_new_slots, get_tenant_id, load_config
from update_subscribers import load_subscribers

script_dir = Path(__file__).parent

#### Setze Parameter für Filterung der verfügbaren Slots ###
start_time = "18:00:00"
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
min_duration = 90

# Städte (Name, URL, Courts) werden in cities.json gepflegt
with open(script_dir / "cities.json", "r") as file:
    cities = json.load(file)


def get_subscribers():
    """Gibt {Stadt-Key: [Chat-IDs]} zurück."""
    if os.getenv("GITHUB_ACTIONS"):
        # Abonnenten werden von update_subscribers.py verschlüsselt in subscribers.enc gepflegt
        subscriptions = load_subscribers()["subscribers"]
        return {
            key: [chat_id for chat_id, keys in subscriptions.items() if key in keys]
            for key in cities
        }
    # Lokal: alle Chat-IDs aus config.local.json erhalten alle Städte
    chat_ids = load_config()["chat_ids"]
    return {key: chat_ids for key in cities}


def check_city(key, city, chat_ids):
    name = city["name"]
    storage_file_path = script_dir / f"freie_plaetze_{key}.csv"

    df = search_for_free_padel_slots(
        start_time,
        city["courts"],
        days,
        min_duration,
        city["url"],
        get_tenant_id(city["url"]),
    )
    pd.set_option("display.colheader_justify", "center")
    if not df.empty:
        print(f"Die folgenden Slots in {name} entsprechen den Filterkriterien:")
        df = df.reset_index(drop=True)
        print(df.to_string(index=False))
    else:
        print(f"Es wurden keine Slots in {name} gefunden, die den Filterkriterien entsprechen.")

    # Abgleich
    diff_df = find_new_slots(df, storage_file_path)
    if not diff_df.empty:
        print(f"Die folgenden neuen Slots in {name} entsprechen den Filterkriterien:")
        print(diff_df.to_string(index=False))
        send_telegram(
            diff_df,
            subject=f"Padel-Tennisplatz in {name} gefunden!",
            chat_ids=chat_ids,
            location=name,
        )
    else:
        print(
            f"Es wurden keine neuen Slots in {name} gefunden, die den Filterkriterien entsprechen. Keine Telegram-Nachricht gesendet."
        )


if __name__ == "__main__":
    subscribers = get_subscribers()
    for key, city in cities.items():
        if not subscribers[key]:
            print(f"Keine Abonnenten für {city['name']}, überspringe.")
            continue
        check_city(key, city, subscribers[key])
