import requests
import os
import sys

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_message(text):
    if not TOKEN or not CHAT_ID:
        print("Error: Faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID en secrets")
        sys.exit(1)

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("Mensaje enviado a Telegram exitosamente")
    except Exception as e:
        print(f"Error al enviar a Telegram: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Mensaje por defecto o desde argumento (puedes cambiarlo)
    message = sys.argv[1] if len(sys.argv) > 1 else "Prueba: Sistema Vigilante Electoral HN activo. Snapshot generado y hasheado. Ver repo: https://github.com/userf8a2c4/hnd-electoral-audit-2029"
    send_message(message)
