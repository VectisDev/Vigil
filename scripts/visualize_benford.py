import json
import matplotlib.pyplot as plt
import os
import collections
import math

def generate_benford_plot():
    # 1. Cargar el último reporte de anomalías o votos
    report_path = 'anomalies_report.json'
    if not os.path.exists(report_path):
        print("No hay reporte para visualizar.")
        return

    # Intentamos extraer datos de votos del archivo que generó tu analyze_rules
    # Nota: Aquí simulamos la captura de los primeros dígitos de la data real
    # En una integración real, este script leería directamente el snapshot procesado.
    
    # Datos ideales de Benford (Ley Matemática)
    digits = list(range(1, 10))
    benford_ideal = [math.log10(1 + 1/d) * 100 for d in digits]

    # Datos de ejemplo (sustituir por carga de datos reales del CNE)
    # Por ahora graficamos la curva base para validar que el motor gráfico funciona
    plt.figure(figsize=(10, 6))
    plt.plot(digits, benford_ideal, 'o-', label='Ley de Benford (Ideal)', color='blue', linewidth=2)
    
    plt.title('Sentinel 2029: Auditoría Estadística (Ley de Benford)')
    plt.xlabel('Primer Dígito')
    plt.ylabel('Frecuencia (%)')
    plt.xticks(digits)
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)

    # Guardar la imagen
    plt.savefig('plots/benford_analysis.png')
    print("Gráfica generada en plots/benford_analysis.png")

if __name__ == "__main__":
    generate_benford_plot()
