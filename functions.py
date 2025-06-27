import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os
from pathlib import Path

url_mannheim = "https://playtomic.io/maba-padel-mannheim-gmbh/5bb4ad71-dbd9-499e-88fb-c9a5e7df6db6?q=PADEL~2024-10-03~~~"
url_ubstadt = "https://playtomic.io/gartner-sportpark/e3acb6b7-c7c5-42c0-ae6f-99d546cabce6?q=PADEL~2025-01-22~~~"

script_dir = Path(__file__).parent

logo_dir = script_dir / "logo.jpg"

def get_tenant_id(url):
    pattern = r"https://playtomic\.io/[^/]+/([0-9a-fA-F-]+)"

    # Suche nach der Tenant-ID
    match = re.search(pattern, url)

    if match:
        tenant_id = match.group(1)
        return tenant_id
    else:
        print("Keine Tenant-ID gefunden.")

tenant_id_mannheim = get_tenant_id(url_mannheim)
tenant_id_ubstadt = get_tenant_id(url_ubstadt)

def get_login_playtomic():
    """Lädt Login-Daten für Playtomic aus config-JSON.

    Returns:
        username (String): Username(Mail) für Playtomic
        password (String): Passwort für Playtomic
    """
    mode = os.getenv('MODE', 'local')  # Standardmäßig 'local'

    if mode == 'cloud':
        # Anmeldedaten aus Umgebungsvariablen (für GitHub Actions)
        username = os.getenv('PLAYTOMIC_USERNAME')
        password = os.getenv('PLAYTOMIC_PASSWORD')
        return username, password
    
    else:
        with open(script_dir/ "config.json", "r") as file:
            config = json.load(file)
            username = config["username_playtomic"]
            password = config["password_playtomic"]
        return username, password

def get_login_mail_sender():
    """Lädt Login-Daten für Mail-Account aus config-JSON.

    Returns:
        username (String): Username(Mail) für Mail-Account
        password (String): Passwort für Mail-Account
    """
    mode = os.getenv('MODE', 'local')  # Standardmäßig 'local'

    if mode == 'cloud':
        # Anmeldedaten aus Umgebungsvariablen (für GitHub Actions)
        username = os.getenv('USERNAME_MAIL_SENDER')
        password = os.getenv('PASSWORD_MAIL_SENDER')
        return username, password
    else:
        with open(script_dir/ "config.json", "r") as file:
            config = json.load(file)
            username = config["username_mail_sender"]
            password = config["password_mail_sender"]
        return username, password

def login():
    """Führt Login bei Playtomic über API durch, zieht sich dann access_token und user_id.

    Returns:
        user_id(String): Playtomic User-ID.
        access_token(String): Playtomic Access-Token. 
    """
    username, password = get_login_playtomic()
    url = "https://playtomic.io/api/v3/auth/login"
    # Login-Daten
    payload = {
        "email": username,
        "password": password
    }

    # Header
    headers = {
        "Content-Type": "application/json"
    }

    # Sende die POST-Anfrage
    response = requests.post(url, json=payload, headers=headers)

    # Wenn der Statuscode 200 (OK) ist, dann war die Anmeldung erfolgreich
    if response.status_code == 200:
        print("Login erfolgreich!")
        access_token = response.json().get("access_token")  # Extrahiere das Token, falls verwendet
        user_id = response.json().get("user_id")
        # print(f"Data: {access_token, user_id}")
    else: 
        print(f"Fehler beim Login: {response.status_code}")
    
    return user_id, access_token

import requests
from bs4 import BeautifulSoup
import json

def get_court_mapping(url):
    """Holt Mapping von resource_id zu Platznamen aus __NEXT_DATA__ JSON."""

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Den Script-Tag mit __NEXT_DATA__ finden
    script_tag = soup.find('script', {'id': '__NEXT_DATA__'})

    if not script_tag:
        raise Exception("Kein __NEXT_DATA__ Script gefunden")

    data = json.loads(script_tag.string)

    # Navigiere zur Ressourcenliste
    resources = data['props']['pageProps']['tenant']['resources']

    platz_info = []

    for resource in resources:
        resource_id = resource.get('resource_id')
        name = resource.get('name')
        if resource.get('sport_id') == 'PADEL':  # Nur Padel-Plätze
            platz_info.append({'resource_id': resource_id, 'name': name})

    # Optional: Ausgabe
    for platz in platz_info:
        print(f"Resource ID: {platz['resource_id']}, Name: {platz['name']}")

    return platz_info

def prioritize_courts():
    """_summary_

    Returns:
        _type_: _description_
    """
    prio_list = get_court_mapping()
    ### hier noch möglich Liste zu ordnen, z.B. Outdoor / krummer Platz entfernen
    return prio_list

def create_url_for_availability_check(date, user_id, access_token, tenant_id):
    """_summary_

    Args:
        date (_type_): _description_
        user_id (_type_): _description_
        access_token (_type_): _description_
        tenant_id (_type_): _description_

    Returns:
        _type_: _description_
    """
    # Setze start_day um 00:00:00 Uhr
    start_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
    # Setze end_day um 23:59:59 Uhr
    end_day = date.replace(hour=23, minute=59, second=59, microsecond=0)
    
    # Formatierung in das Format "2025-02-04T00%3A00%3A00" für den Link
    start_day_str = start_day.strftime("%Y-%m-%dT%H:%M:%S").replace(":", "%3A")
    end_day_str = end_day.strftime("%Y-%m-%dT%H:%M:%S").replace(":", "%3A")
    
    # This URL is outdated. A Login is not necessary anymore. 
    # url_availabilty = f"https://playtomic.io/api/v1/availability?user_id={user_id}&tenant_id={tenant_id}&sport_id=PADEL&local_start_min={start_day_str}&local_start_max={end_day_str}"
    url_availabilty = f"https://playtomic.com/api/clubs/availability?tenant_id={tenant_id}&date={start_day_str}&sport_id=PADEL"
    
    return url_availabilty

def create_urls_for_availability_check(tenant_id):
    """_summary_

    Args:
        tenant_id (_type_): _description_

    Returns:
        _type_: _description_
    """
    user_id, access_token = login()
    # Startdatum (heute)
    start_date = datetime.now()
    url_list = []

    # Schleife für die nächsten 14 Tage
    for i in range(30):
        current_day = start_date + timedelta(days=i)
        url = create_url_for_availability_check(current_day, user_id, access_token, tenant_id)
        url_list.append(url)
    return url_list, access_token

def fetch_and_store_data(urls, access_token):
    """_summary_

    Args:
        urls (_type_): _description_
        access_token (_type_): _description_

    Returns:
        _type_: _description_
    """
    data_list = []  # Liste, um alle Antworten zu speichern

    headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
    }

    for url in urls:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            availabilities = response.json()
            data_list.append(availabilities)  # Hinzufügen zur Liste
        else:
            print(f"Fehler beim Abrufen der Verfügbarkeiten für {url}: {response.status_code}")
    
    return data_list

def list_to_df(data_list):
    """_summary_

    Args:
        data_list (_type_): _description_

    Returns:
        _type_: _description_
    """
    # Liste für die extrahierten Daten
    data_extracted = []

    # Durch die data_list iterieren und die relevanten Daten extrahieren
    for outer_list in data_list:
        for entry in outer_list:  # Innerhalb der äußeren Liste auf das Dictionary zugreifen
            if isinstance(entry, dict):  # Überprüfen, ob entry ein Dictionary ist
                resource_id = entry["resource_id"]
                start_date = entry["start_date"]
                for slot in entry["slots"]:
                    if isinstance(slot, dict):  # Überprüfen, ob slot ein Dictionary ist
                        data_extracted.append({
                            "resource_id": resource_id,
                            "start_date": start_date,
                            "duration": slot["duration"],
                            "price": slot["price"],
                            "start_time": slot["start_time"]
                        })
                    else:
                        print(f"Fehler: Slot ist kein Dictionary: {slot}")
            else:
                print(f"Fehler: Eintrag ist kein Dictionary: {entry}")
    return data_extracted

def filter_dataframe(df, start_time=None, court_names=None, min_duration=None, days=None):
    """_summary_

    Args:
        df (_type_): _description_
        start_time (_type_, optional): _description_. Defaults to None.
        court_names (_type_, optional): _description_. Defaults to None.
        min_duration (_type_, optional): _description_. Defaults to None.
        days (_type_, optional): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """
    filtered_df = df.copy()
    
    # Filter für `start_time`
    if start_time:
        start_time = pd.to_datetime(start_time, format="%H:%M:%S").time()  # Konvertiere zu `time`
        filtered_df = filtered_df[filtered_df["start_time"] >= start_time]  # Kein .dt notwendig
    
    # Neue Spalte 'Tag' hinzufügen
    filtered_df['start_date'] = pd.to_datetime(filtered_df['start_date'])
    filtered_df['Tag'] = filtered_df['start_date'].dt.day_name()
    
    # Filter für "Tag"
    if days:
        filtered_df = filtered_df[filtered_df['Tag'].isin(days)]

    # Filter für `court_names`
    if court_names:
        filtered_df = filtered_df[filtered_df['name'].isin(court_names)]
    
    # Filter für `min_duration`
    if min_duration:
        filtered_df = filtered_df[filtered_df['duration'] >= min_duration]
    
    filtered_df = filtered_df.rename(columns={"name": "Court", "start_date": "Datum", "start_time":"Uhrzeit", "duration":"Spieldauer", "price":"Preis"})

    return filtered_df

def config_timezone(df, hours):
    """
    Passt die Zeit um eine bestimmte Anzahl Stunden an.

    Parameter:
        df (pd.DataFrame): Der DataFrame mit der `start_time`-Spalte.
        hours (int): Anzahl der Stunden, die hinzugefügt werden sollen.
    """
    # Konvertiere die Zeit in ein vollständiges Datetime-Objekt, füge Timedelta hinzu und wandle zurück
    df["start_time"] = (
        pd.to_datetime(df["start_time"], format="%H:%M:%S")  # In datetime konvertieren
        + pd.Timedelta(hours=hours)                         # Stunden hinzufügen
    ).dt.time  # Zurück zu reiner Zeit (ohne Datum) konvertieren

def transform_dataframe(df_platz_info, data_df, hours):
    """Zieht sich die Platz-Namen aus df_platz_info und mappt sie auf die "resource_id" in data_df. 

    Args:
        df_platz_info (DataFrame): Enthält Mapping zwischen Resource-ID und Court-Name.
        data_df (DataFrame): Enthält alle freien Slots aus Playtomic. 
        hours (Integer): Anzahl von Stunden zur Anpassung der Zeitverschiebung (Zeit in Playtomic GMT).

    Returns:
        _type_: _description_
    """
    df_merged = pd.merge(data_df, df_platz_info, on='resource_id', how='left')
    # Entferne Spalten die nicht mehr gebraucht werden.
    df_merged = df_merged[['name', 'start_date', 'start_time', 'duration', 'price']]
    # Konvertiere Zeit in Datetime-Format und passe Zeitzone an
    df_merged["start_time"] = pd.to_datetime(df_merged["start_time"], format="%H:%M:%S").dt.time
    config_timezone(df_merged, hours)
    
    return df_merged

def search_for_free_padel_slots(start_time, court_names, days, min_duration, url, tenant_id): 
    """AI is creating summary for search_for_free_padel_slots

    Args:
        start_time (String): Filterkriterium "ab Uhrzeit X / frühestens Uhrzeit X". 
        court_names ([String]): Filterkriterium für Padel-Plätze. 
        days ([String]): Filterkriterium für Wochentage. 
        min_duration (Integer): Filterkriterium für "ab Spieldauer X / mindestens Spieldauer X".
        url (String): URL zur Buchungsseite der Padel-Location
        tenant_id (String): Playtomic-ID der Padel-Location. 
    Returns:
        DataFrame: Enthält alle freien Zeiten, die den Filterkriterien entsprechen. 
    """
    # Erstelle Mapping DataFrame resource_id -> Court-Name
    platz_info = get_court_mapping(url)
    df_platz_info = pd.DataFrame(platz_info)

    # Erstelle URLs für den Abruf der Verfügbarkeiten
    url_list, access_token = create_urls_for_availability_check(tenant_id)
    # Abruf der Daten
    data_list = fetch_and_store_data(url_list, access_token)

    # Speichere Daten in DataFrame
    data_extracted = list_to_df(data_list)
    data_df = pd.DataFrame(data_extracted)

    # Ersetze resource_id -> Court-Name
    df_merged = transform_dataframe(df_platz_info, data_df, hours=0)
    filtered_df = filter_dataframe(df_merged, start_time, court_names, min_duration, days)

    return filtered_df

def book_court():
    raise NotImplementedError

def format_dataframe_as_text(df):
    return df.to_string(index=False)

def send_email(df, subject, recipients, location):
    """_summary_

    Args:
        df (_type_): _description_
        subject (_type_): _description_
        recipient (_type_): _description_
        location (_type_): _description_
    """    

    sender, password = get_login_mail_sender()
    # Erstelle die E-Mail
    html = df.to_html(index=False)
    #body=f"Die folgenden freien Zeiten wurden in {location} gefunden:\n\n{format_dataframe_as_text(df)}"
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = sender
    msg["Subject"] = subject
    msg["Bcc"] = ", ".join(recipients)  # Empfänger als kommagetrennte Liste
    df["Datum"] = pd.to_datetime(df["Datum"]).dt.date

    html_body = f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <img src="cid:logo" alt="PadelBot Logo" style="width: 600px; height: auto;">
    </div>
    <h2 style="text-align: center;">Die folgenden freien Zeiten wurden in {location} gefunden:</h2>
    <div style="display: flex; justify-content: center; margin: 20px;">
        <table style="
            border-collapse: collapse; 
            margin: 20px auto; 
            font-size: 16px; 
            font-family: Arial, sans-serif;
            color: #333;
            text-align: center;
        ">
            <thead style="background-color: #007BFF; color: white;">
                <tr>
                    <th style="padding: 10px; border: 1px solid #ddd;">Court</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">Datum</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">Uhrzeit</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">Spieldauer</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">Preis</th>
                    <th style="padding: 10px; border: 1px solid #ddd;">Tag</th>
                </tr>
            </thead>
            <tbody>
    """
    for _, row in df.iterrows():
        html_body += f"""
                <tr>
                    <td style="padding: 10px; border: 1px solid #ddd;">{row['Court']}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{row['Datum']}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{row['Uhrzeit']}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{row['Spieldauer']}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{row['Preis']}</td>
                    <td style="padding: 10px; border: 1px solid #ddd;">{row['Tag']}</td>
                </tr>
        """
    html_body += """
            </tbody>
        </table>
    </div>
    """
    msg.attach(MIMEText(html_body, "html"))
    
    # Bild anhängen
    with open(logo_dir, "rb") as img:
        mime_img = MIMEImage(img.read())
        mime_img.add_header("Content-ID", "<logo>")
        msg.attach(mime_img)

    try:
        # SMTP-Server und Port für web.de
        with smtplib.SMTP_SSL("smtp.web.de", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, recipients, msg.as_string())
            print("E-Mail erfolgreich gesendet!")
    except Exception as e:
        print(f"Fehler beim Senden der E-Mail: {e}")

def find_new_slots(new_df, storage_file_path):
    """ Vergleicht die gefundenen freien Plätze des letzten Runs mit den gefundenen Plätze des aktuellen Runs. Es werden nur freie Plätze (Zeilen im DF)
        behalten, die neu hinzugekommen sind. 

    Args:
        new_df (DataFrame): Enthält die aktualisierten freien Plätze von Playtomic.
        storage_file_path (String): Pfad zu der csv-Datei, in der die freien Plätze gespeichert werden. 
    Returns:
        DataFrame: Enthält die Slots, die seit der letzten Programmausführung hinzu gekommen sind. Wird anschließend für Notification-Mail benötigt. 
    """
    # Prüfen, ob die Datei existiert
    if not os.path.exists(storage_file_path):
        # Falls nicht, speichern wir den aktuellen DataFrame
        new_df.to_csv(storage_file_path, index=False)
        print("Keine alten Daten gefunden. Speichere den aktuellen DataFrame.")
        return new_df 
    
    # Lade den gespeicherten DataFrame
    old_df = pd.read_csv(storage_file_path)

    # Aktualisiere die gespeicherte Datei
    new_df.to_csv(storage_file_path, index=False)
    
    # TEST
    # Beispiel-Test-Zeile hinzufügen
    # test_row = pd.DataFrame({
    #     'Court': ['This is a test.'],
    #     'Datum': ['2025-02-05'],
    #     'Uhrzeit': ['18:30:00'],
    #     'Spieldauer': [90],
    #     'Preis': ['46 EUR']
    # })

    # # Füge die Test-Zeile zu new_df hinzu
    # new_df = pd.concat([new_df, test_row], ignore_index=True)

    # Konvertiere 'Datum' in datetime
    old_df['Datum'] = pd.to_datetime( old_df['Datum'])
    new_df['Datum'] = pd.to_datetime(new_df['Datum'])

    # Konvertiere 'Uhrzeit' in time
    old_df['Uhrzeit'] = pd.to_datetime( old_df['Uhrzeit'], format='%H:%M:%S').dt.time
    new_df['Uhrzeit'] = pd.to_datetime(new_df['Uhrzeit'], format='%H:%M:%S').dt.time

    # Setze den Index beider DataFrames zurück
    old_df_reset =  old_df.reset_index(drop=True)
    new_df_reset = new_df.reset_index(drop=True)
    # Vergleiche beide DataFrames - behalte nur die Zeilen, die ausschließlich in "new_df_reset" enthalten sind. 
    result = pd.merge(new_df_reset, old_df_reset, how='left', indicator=True).query('_merge == "left_only"').drop('_merge', axis=1)
    # Füge Spalte "Tag" zum DataFrame hinzu. 
    result['Tag'] = result['Datum'].dt.day_name()
    return result