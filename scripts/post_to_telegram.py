import requests
import os
import sys

# Protocolo de Identidad: HND-SENTINEL-2029
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def format_as_sentinel(raw_data):
    """
    Envuelve los datos en el protocolo de comunicación bilingüe DedSec.
    Se espera que raw_data sea un string con los hallazgos técnicos.
    """
    header = (
        "<code>[!] DEDSEC_HND_AUTOAUDIT_2029</code>\n"
        "<code>[!] STATUS: ANOMALY_DETECTED // EVENT_ID: #HND-29-LOG</code>\n"
        "--------------------------------------------------\n\n"
    )
    
    footer = (
        "\n--------------------------------------------------\n"
        "<b>DEDSEC has given you the truth. Do what you will.</b>\n"
        "<b>DEDSEC te ha entregado la verdad. Haz lo que quieras.</b>"
    )
    
    # Combinamos el mensaje asegurando que el contenido técnico use monoespaciado (HTML)
    full_message = f"{header}{raw_data}{footer}"
    return full_message

def send_message(text):
    if not TOKEN or not CHAT_ID:
        print("[!] ERROR: SYSTEM_CREDENTIALS_MISSING")
        sys.exit(1)

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    # Usamos parse_mode "HTML" para mejor control de la estética DedSec
    payload = {
        "chat_id": CHAT_ID,
        "text": format_as_sentinel(text),
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        print("[+] STATUS: TRANSMISSION_SUCCESSFUL")
    except Exception as e:
        print(f"[!] STATUS: TRANSMISSION_FAILED // ERR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Si hay argumentos, los procesa; si no, lanza un mensaje de latido del sistema (Heartbeat)
    if len(sys.argv) > 1:
        message_content = sys.argv[1]
    else:
        # Mensaje de inicialización estándar bilingüe
        message_content = (
            "<b>[EN] SYSTEM_HEARTBEAT:</b> Monitoring node is active. Watching data streams.\n"
            "<b>[ES] LATIDO_SISTEMA:</b> Nodo de monitoreo activo. Vigilando flujo de datos."
        )
    
    send_message(message_content)
