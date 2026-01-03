import requests
import os
import sys

# Protocolo de Identidad: HND-SENTINEL-2029
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_stored_hash(hash_path):
    """
    Lee el hash previamente generado por download_and_hash.py
    para asegurar consistencia total entre Git y Telegram.
    """
    try:
        with open(hash_path, "r") as f:
            # Extrae solo el hash (asumiendo formato estándar: hash filename)
            content = f.read().strip().split()[0]
            return content
    except Exception as e:
        return f"HASH_READ_ERROR: {str(e)}"

def format_as_sentinel(raw_data, stored_hash=None):
    """
    Formatea el reporte con estética DedSec bilingüe.
    """
    header = (
        "<code>[!] DEDSEC_HND_SENTINEL_2029</code>\n"
        "<code>[!] STATUS: ANOMALY_REPORT // PROTOCOL: biling_v1</code>\n"
        "--------------------------------------------------\n\n"
    )
    
    hash_section = ""
    if stored_hash:
        hash_section = (
            f"\n--------------------------------------------------\n"
            f"<code>VERIFICATION_HASH (SHA-256):</code>\n"
            f"<code>{stored_hash}</code>"
        )
    
    footer = (
        "\n--------------------------------------------------\n"
        "<b>DEDSEC has given you the truth. Do what you will.</b>\n"
        "<b>DEDSEC te ha entregado la verdad. Haz lo que quieras.</b>"
    )
    
    return f"{header}{raw_data}{hash_section}{footer}"

def send_message(text, stored_hash=None):
    if not TOKEN or not CHAT_ID:
        print("[!] ERROR: SYSTEM_CREDENTIALS_MISSING")
        sys.exit(1)

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    payload = {
        "chat_id": CHAT_ID,
        "text": format_as_sentinel(text, stored_hash),
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
    # Uso esperado desde GitHub Actions:
    # python scripts/post_to_telegram.py "Mensaje técnico" "hashes/snapshot_XXXX.json.sha256"
    
    if len(sys.argv) > 2:
        msg = sys.argv[1]
        hash_file_path = sys.argv[2]
        file_hash = get_stored_hash(hash_file_path)
        send_message(msg, file_hash)
    elif len(sys.argv) == 2:
        send_message(sys.argv[1])
    else:
        # Heartbeat bilingüe si se ejecuta sin argumentos
        heartbeat = (
            "<b>[EN] MONITOR_STATUS:</b> Operational. Systems synchronized.\n"
            "<b>[ES] ESTADO_MONITOR:</b> Operativo. Sistemas sincronizados."
        )
        send_message(heartbeat)
