import json
import os
import requests
import time
from atproto import Client as BlueskyClient
from mastodon import Mastodon

# --- GEHEIME ZUGANGSDATEN (Werden sicher von GitHub übergeben) ---
BLUESKY_HANDLE = os.environ.get("BLUESKY_HANDLE")
BLUESKY_PASSWORD = os.environ.get("BLUESKY_PASSWORD")
MASTODON_INSTANCE = os.environ.get("MASTODON_INSTANCE")
MASTODON_ACCESS_TOKEN = os.environ.get("MASTODON_ACCESS_TOKEN")

# Hier holt sich der Bot die News aus deinem Haupt-Repository!
NEWS_URL = "https://raw.githubusercontent.com/Blackfront161/Revolution-News-Data/main/news.json"
HISTORY_FILE = "gepostet.txt"

def lade_historie():
    if not os.path.exists(HISTORY_FILE):
        open(HISTORY_FILE, 'a').close() # Datei erstellen, falls nicht vorhanden
        return set()
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def speichere_in_historie(link):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")

def post_to_bluesky(text):
    if not BLUESKY_HANDLE or not BLUESKY_PASSWORD:
        return False
    try:
        bsky = BlueskyClient()
        bsky.login(BLUESKY_HANDLE, BLUESKY_PASSWORD)
        bsky.send_post(text)
        return True
    except Exception as e:
        print(f"[Fehler Bluesky]: {e}")
        return False

def post_to_mastodon(text):
    if not MASTODON_INSTANCE or not MASTODON_ACCESS_TOKEN:
        return False
    try:
        mastodon = Mastodon(access_token=MASTODON_ACCESS_TOKEN, api_base_url=MASTODON_INSTANCE)
        mastodon.toot(text)
        return True
    except Exception as e:
        print(f"[Fehler Mastodon]: {e}")
        return False

def main():
    print("Lade News aus dem Haupt-Repository...")
    try:
        req = requests.get(NEWS_URL)
        req.raise_for_status()
        artikel_liste = req.json()
    except Exception as e:
        print(f"Fehler beim Herunterladen der News: {e}")
        return

    gepostete_links = lade_historie()
    artikel_liste.reverse() # Älteste zuerst, für eine schöne Timeline
    neue_posts_zaehler = 0

    for artikel in artikel_liste:
        link = artikel.get("link")
        title = artikel.get("title", "Kein Titel")
        quelle = artikel.get("quelleName", "Unbekannte Quelle")

        if not link or link in gepostete_links:
            continue

        # WICHTIG: Max. 4 Posts pro Durchlauf, damit der Bot nicht als Spam blockiert wird
        if neue_posts_zaehler >= 4:
            print("Maximales Post-Limit für diesen Durchlauf erreicht. Rest folgt beim nächsten Mal.")
            break

        post_text = f"📢 {title}\n\nQuelle: {quelle}\n👉 {link}\n\n#WorldRevolutionNews #Antifascism #EcoAnarchism #LaborStruggles"
        print(f"Poste: {title}")
        
        b_success = post_to_bluesky(post_text)
        m_success = post_to_mastodon(post_text)

        if b_success or m_success:
            speichere_in_historie(link)
            neue_posts_zaehler += 1
            time.sleep(5) # Kurze Atempause für die Server
            
    print(f"Fertig! {neue_posts_zaehler} Artikel gepostet.")

if __name__ == "__main__":
    main()
