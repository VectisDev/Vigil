import json
import os
import glob
import math
import collections

# Protocolo HND-SENTINEL-2029: Auditoría Forense
# Basado en datos históricos 2025 

def load_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[!] ERROR_LOADING_FILE: {file_path} - {str(e)}")
        return None

def apply_benford_law(votos_lista):
    """
    Analiza la distribución del primer dígito de los votos por candidato.
    Detecta si los números parecen 'inventados' por humanos.
    """
    first_digits = []
    for c in votos_lista:
        votos = str(c.get('votos', '')).strip()
        if votos and votos != '0':
            first_digits.append(int(votos[0]))
    
    if not first_digits:
        return None
    
    counts = collections.Counter(first_digits)
    total = len(first_digits)
    
    # Distribución ideal de Benford para dígitos 1-9
    benford_ideal = {d: math.log10(1 + 1/d) * 100 for d in range(1, 10)}
    actual_dist = {d: (counts[d] / total) * 100 for d in range(1, 10)}
    
    # Si el dígito '1' es muy bajo (<20%) o los dígitos altos son muy frecuentes, hay anomalía
    is_anomaly = actual_dist.get(1, 0) < 20.0 or actual_dist.get(8, 0) > 15.0
    return {"is_anomaly": is_anomaly, "distribution": actual_dist}

def analyze_historical_stream(file_list):
    """
    Procesa el flujo de archivos (como los 63 raws de 2025).
    Mantiene un registro de 'votos máximos' para detectar regresiones históricas.
    """
    # Diccionario para rastrear el pico más alto de votos detectado por ID de candidato
    peak_votos = {} 
    all_anomalies = []

    # Ordenar archivos por nombre (asumiendo que tienen el timestamp en el nombre)
    sorted_files = sorted(file_list)

    print(f"[*] INICIANDO AUDITORÍA SOBRE {len(sorted_files)} ARCHIVOS...")

    for i in range(len(sorted_files)):
        current_file = sorted_files[i]
        data = load_json(current_file)
        if not data: continue

        votos_actuales = data.get('votos', [])
        file_name = os.path.basename(current_file)

        # 1. Regla de Monotonicidad (Regresión de Votos)
        for c in votos_actuales:
            c_id = c.get('id') or c.get('nombre') # Identificador dinámico
            votos_val = int(c.get('votos', 0))

            if c_id in peak_votos:
                if votos_val < peak_votos[c_id]['votos']:
                    anomaly = {
                        'timestamp': file_name,
                        'rule': 'NEGATIVE_VOTES',
                        'candidate': c.get('nombre'),
                        'loss': votos_val - peak_votos[c_id]['votos'],
                        'current': votos_val,
                        'peak': peak_votos[c_id]['votos']
                    }
                    all_anomalies.append(anomaly)
                    print(f"[!] ALERTA_REGRESIÓN: {c.get('nombre')} perdió {anomaly['loss']} votos en {file_name}")
            
            # Actualizar pico máximo si el valor actual es mayor
            if c_id not in peak_votos or votos_val > peak_votos[c_id]['votos']:
                peak_votos[c_id] = {'votos': votos_val, 'file': file_name}

        # 2. Análisis de Benford (cada 10 archivos o al final para tener muestra suficiente)
        if i % 10 == 0 or i == len(sorted_files) - 1:
            benford_report = apply_benford_law(votos_actuales)
            if benford_report and benford_report['is_anomaly']:
                print(f"[?] AVISO_ESTADÍSTICO: Distribución de votos inusual en {file_name} (Posible manipulación Benford)")

    return all_anomalies

if __name__ == "__main__":
    # Para probar con tus 63 archivos, asegúrate que estén en la carpeta 'data/'
    target_files = glob.glob('data/*.json')
    
    if not target_files:
        print("[!] No se encontraron archivos JSON en la carpeta 'data/'.")
        sys.exit(1)

    report = analyze_historical_stream(target_files)
    
    print("\n" + "="*50)
    print(f"RESUMEN DE AUDITORÍA: {len(report)} ANOMALÍAS DETECTADAS")
    print("="*50)
