import pandas as pd
from functions import search_for_free_padel_slots, send_telegram, find_new_slots, get_tenant_id, load_config
import os
from pathlib import Path
import json

script_dir = Path(__file__).parent
# Prüfen, ob wir in GitHub Actions oder lokal laufen
if os.getenv("GITHUB_ACTIONS"):
    # Komma-getrennte Chat-IDs aus Umgebungsvariablen (für GitHub Actions)
    chat_ids_mannheim = [c.strip() for c in os.getenv('CHAT_IDS_MANNHEIM', '').split(',') if c.strip()]
    chat_ids_ubstadt = [c.strip() for c in os.getenv('CHAT_IDS_UBSTADT', '').split(',') if c.strip()]
else:
    # Lokaler Pfad
    config = load_config()
    chat_ids_mannheim = config["chat_ids_mannheim"]
    chat_ids_ubstadt = config["chat_ids_ubstadt"]

storage_file_path_mannheim = script_dir / "freie_plaetze_mannheim.csv"
storage_file_path_ubstadt = script_dir / "freie_plaetze_ubstadt.csv"

#### Setze Parameter für Filterung der verfügbaren Slots ###
start_time = "18:00:00"
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
court_names_mannheim = [
    "Padel 1 indoor",
    "Padel 2 indoor",
    "Padel 3 indoor",
    "Padel 4 indoor",
    "Padel 5 Indoor",
    "Padel 6 Indoor",
    "Padel 7 Indoor",
    "Padel 8 Indoor",
    "Padel 9 Indoor"
]
court_names_ubstadt = ["Padel Halle 1","Padel Halle 2 ","Padel Halle 3"]
url_mannheim = "https://playtomic.io/maba-padel-mannheim-gmbh/5bb4ad71-dbd9-499e-88fb-c9a5e7df6db6?q=PADEL~2024-10-03~~~"
url_ubstadt = "https://playtomic.io/gartner-sportpark/e3acb6b7-c7c5-42c0-ae6f-99d546cabce6?q=PADEL~2025-01-22~~~"
min_duration = 90

tenant_id_mannheim = get_tenant_id(url_mannheim)
tenant_id_ubstadt = get_tenant_id(url_ubstadt)

if __name__ == "__main__":

    # Suche nach neuen Plätzen in Mannheim
    df_mannheim = search_for_free_padel_slots(
        start_time,
        court_names_mannheim,
        days,
        min_duration,
        url_mannheim,
        tenant_id_mannheim,
    )
    pd.set_option("display.colheader_justify", "center")
    if not df_mannheim.empty:
        print("Die folgenden Slots in Mannheim entsprechen den Filterkriterien:")
        df_mannheim = df_mannheim.reset_index(drop=True)
        print(df_mannheim.to_string(index=False))
    else:
        print(
            "Es wurden keine Slots in Mannheim gefunden, die den Filterkriterien entsprechen."
        )

    # Abgleich
    diff_df_mannheim = find_new_slots(df_mannheim, storage_file_path_mannheim)
    if not diff_df_mannheim.empty:
        print("Die folgenden neuen Slots in Mannheim entsprechen den Filterkriterien:")
        print(diff_df_mannheim.to_string(index=False))
        send_telegram(
            diff_df_mannheim,
            subject="Padel-Tennisplatz in Mannheim gefunden!",
            chat_ids=chat_ids_mannheim,
            location="Mannheim"
        )
    else:
        print(
            "Es wurden keine neuen in Mannheim Slots gefunden, die den Filterkriterien entsprechen. Keine Telegram-Nachricht gesendet."
        )

    # # Suche nach neuen Plätzen in Ubstadt
    df = search_for_free_padel_slots(
        start_time,
        court_names_ubstadt,
        days,
        min_duration,
        url_ubstadt,
        tenant_id_ubstadt,
    )
    pd.set_option("display.colheader_justify", "center")
    if not df.empty:
        print("Die folgenden Slots in Ubstadt entsprechen den Filterkriterien:")
        df = df.reset_index(drop=True)
        print(df.to_string(index=False))
    else:
        print(
            "Es wurden keine Slots in Ubstadt gefunden, die den Filterkriterien entsprechen."
        )

    # Abgleich
    diff_df = find_new_slots(df, storage_file_path_ubstadt)
    if not diff_df.empty:
        print("Die folgenden neuen Slots in Ubstadt entsprechen den Filterkriterien:")
        print(diff_df.to_string(index=False))
        send_telegram(
            diff_df,
            subject="Padel-Tennisplatz in Ubstadt gefunden!",
            chat_ids=chat_ids_ubstadt,
            location="Ubstadt"
        )
    else:
        print(
            "Es wurden keine neuen Slots in Ubstadt gefunden, die den Filterkriterien entsprechen. Keine Telegram-Nachricht gesendet."
        )