import json
import os
import glob
import math
import collections
import sys

# PROTOCOLO HND-SENTINEL-2029 // AUDITORÍA RESILIENTE
# Versión optimizada para datos históricos 2025 y futuros 2029

def load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] ERROR_CARGA: {file_path} - {str(e)}")
        return None

def safe_int(value, default=0):
    """Convierte a entero de forma segura, manejando strings y nulls."""
    try:
        if value is None: return default
        return int(str(value).replace(',', '').split('.')[0])
    except (ValueError, TypeError):
        return default

def apply_benford_law(votos_lista):
    """Analiza la distribución del primer dígito (Ley de Benford)."""
    # Solo procesamos si hay suficientes datos para evitar falsos positivos
    if len(votos_lista) < 10: 
        return None

    first_digits = []
    for c in votos_lista:
        votos_str = str(c.get('votos', '')).strip()
        if votos_str and votos_str not in ['0', 'None']:
            first_digits.append(int(votos_str[0]))
    
    if not first_digits: return None
    
    counts = collections.Counter(first_digits)
    total = len(first_digits)
    
    # Análisis de anomalía: El '1' debe ser ~30%. Si es < 20%, sospecha de manipulación.
    dist_1 = (counts[1] / total) * 100
    is_anomaly = dist_1 < 20.0
    
    return {"is_anomaly": is_anomaly, "prop_1": dist_1}

def run_audit(target_directory='data/'):
    peak_votos = {} 
    anomalies_log = []

    # Obtener archivos ordenados por nombre (cronología de timestamps)
    file_list = sorted(glob.glob(os.path.join(target_directory, '*.json')))
    
    if not file_list:
        print(f"[!] No se encontraron archivos en {target_directory}")
        return

    print(f"[*] PROCESANDO {len(file_list)} SNAPSHOTS ELECTORALES...")

    for file_path in file_list:
        data = load_json(file_path)
        if not data: continue
        
        file_name = os.path.basename(file_path)
        # Soporta diferentes estructuras de JSON del CNE (votos o candidates)
        votos_actuales = data.get('votos') or data.get('candidates') or []

        # 1. REGLA DE MONOTONICIDAD (PEAK-TRACKING)
        for c in votos_actuales:
            # Identificador robusto: ID o Nombre
            c_id = str(c.get('id') or c.get('nombre') or 'unknown')
            v_actual = safe_int(c.get('votos'))

            if c_id in peak_votos:
                if v_actual < peak_votos[c_id]['valor']:
                    diff = v_actual - peak_votos[c_id]['valor']
                    print(f"[!] REGRESIÓN: {c_id} perdió {diff} votos en {file_name}")
                    anomalies_log.append({
                        "file": file_name,
                        "type": "NEGATIVE_DELTA",
                        "entity": c_id,
                        "loss": diff
                    })
            
            # Actualizar el pico histórico si el valor actual es mayor
            if c_id not in peak_votos or v_actual > peak_votos[c_id]['valor']:
                peak_votos[c_id] = {'valor': v_actual, 'file': file_name}

        # 2. LEY DE BENFORD (MONITOREO ESTADÍSTICO)
        benford = apply_benford_law(votos_actuales)
        if benford and benford['is_anomaly']:
            print(f"[?] SOSPECHA: Distribución Benford anómala en {file_name} (Dígito 1: {benford['prop_1']:.1f}%)")

    # Guardar resultados para uso del Bot de Telegram o Visualizador
    with open('anomalies_report.json', 'w') as f:
        json.dump(anomalies_log, f, indent=4)
    print(f"\n[*] AUDITORÍA FINALIZADA. Reporte guardado en anomalies_report.json")

if __name__ == "__main__":
    run_audit()
