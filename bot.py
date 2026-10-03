from flask import Flask
import threading
import requests
import time

app = Flask(__name__)

APIKEY = "3189307"
PHONE = "2290191083450"

@app.route('/')
def home():
    return "Bot trading en ligne - Odilon"

def run_web():
    app.run(host='0.0.0.0', port=10000)

# Lance le petit serveur web pour Render gratuit
threading.Thread(target=run_web, daemon=True).start()

# --- TON CODE DE TRADING EN DESSOUS ---
def send_whatsapp(msg):
    url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={msg}&apikey={APIKEY}"
    try:
        requests.get(url)
        print(f"WhatsApp envoyé: {msg}")
    except Exception as e:
        print(f"Erreur WhatsApp: {e}")

# Mets ta logique de trading ici
# Exemple :
while True:
    # ton code...
    # quand tu veux envoyer un signal :
    # send_whatsapp("BUY BTC maintenant")
    time.sleep(60)