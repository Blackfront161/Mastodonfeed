import json
import os
import requests
import time
from mastodon import Mastodon

# --- KONFIGURATION (Daten kommen aus GitHub Secrets) ---
MASTODON_INSTANCE = os.environ.get("MASTODON_INSTANCE")
MASTODON_ACCESS_TOKEN = os.environ.get("MASTODON_ACCESS_TOKEN")

NEWS_URL = "https://raw.githubusercontent.com/Blackfront161/Revolution-News-Data/main/news.json"
HISTORY_FILE = "gepostet.txt"

def lade_historie():
    """Liest die bereits geposteten Links aus der Historien-Datei."""
    if not os.path.exists(HISTORY_FILE):
        return set()
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f if line.strip())

def speichere_in_historie(link):
    """Schreibt einen neu geposteten Link in die Historie."""
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")

def post_to_mastodon(text):
    """Sendet den Inhalt via API an Mastodon."""
    if not MASTODON_INSTANCE or not MASTODON_ACCESS_TOKEN:
        print("[FEHLER] Mastodon-Zugangsdaten (Secrets) fehlen!")
        return False
    try:
        # Hier findet das Einloggen über den Token statt (ohne Passwort)
        mastodon = Mastodon(
            access_token=MASTODON_ACCESS_TOKEN, 
            api_base_url=MASTODON_INSTANCE
        )
        mastodon.toot(text)
        return True
    except Exception as e:
        print(f"[FEHLER-DETAIL] Mastodon hat den Post abgelehnt: {e}")
        return False

def main():
    print("--- Starte Bot-Durchlauf ---")
    
    # News abrufen
    try:
        req = requests.get(NEWS_URL)
        req.raise_for_status()
        artikel_liste = req.json()
    except Exception as e:
        print(f"[FEHLER] Konnte news.json nicht laden: {e}")
        return

    gepostete_links = lade_historie()
    # Wir nehmen die neuesten Artikel (reversed für chronologische Reihenfolge)
    artikel_liste.reverse()
    
    neue_posts_zaehler = 0

    for artikel in artikel_liste:
        link = artikel.get("link")
        title = artikel.get("title", "Kein Titel")
        quelle = artikel.get("quelleName", "Unbekannte Quelle")

        # Prüfen, ob wir das schon mal gepostet haben
        if not link or link in gepostete_links:
            continue

        # Sicherheitsstopp: Max 4 Posts pro Durchlauf
        if neue_posts_zaehler >= 4:
            break

        post_text = f"📢 {title}\n\nQuelle: {quelle}\n👉 {link}\n\n#WorldRevolutionNews #News"
        
        print(f"Versuche zu posten: {title}")
        
        if post_to_mastodon(post_text):
            speichere_in_historie(link)
            neue_posts_zaehler += 1
            time.sleep(5) # Atempause, um nicht als Bot gesperrt zu werden
        else:
            # Falls ein Post fehlschlägt, brechen wir diesen Durchlauf ab
            break
            
    print(f"--- Fertig! {neue_posts_zaehler} Artikel wurden neu gepostet. ---")

if __name__ == "__main__":
    main()
