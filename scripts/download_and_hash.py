#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
download_and_hash.py

Descarga snapshots de resultados electorales del CNE Honduras y genera hashes encadenados SHA-256 para integridad.
Download CNE Honduras election results snapshots and generate chained SHA-256 hashes for integrity.

Uso / Usage:
    python -m scripts.download_and_hash [--mock]

Dependencias / Dependencies: requests, pyyaml, hashlib, logging, argparse, pathlib, json, datetime

Este script es parte del proyecto C.E.N.T.I.N.E.L. – solo para auditoría ciudadana neutral.
This script is part of C.E.N.T.I.N.E.L. project – for neutral citizen audit only.
"""

import argparse
import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path
import requests
import yaml
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuración de logging global (inicializado temprano)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("centinel.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_config(config_path: str = "config.yaml") -> dict:
    """Carga la configuración desde config.yaml / Load configuration from config.yaml

    Args:
        config_path (str): Ruta al archivo de configuración / Path to config file

    Returns:
        dict: Configuración cargada / Loaded configuration

    Raises:
        FileNotFoundError: Si el archivo no existe / If file does not exist
        yaml.YAMLError: Si hay error de sintaxis YAML / If YAML syntax error
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"Configuración cargada desde {config_path} / Configuration loaded from {config_path}")
        return config
    except FileNotFoundError:
        logger.error(f"Archivo de configuración no encontrado: {config_path} / Config file not found: {config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error al parsear YAML: {e} / Error parsing YAML: {e}")
        raise

def compute_hash(data: bytes) -> str:
    """Calcula hash SHA-256 de los datos / Compute SHA-256 hash of data

    Args:
        data (bytes): Datos a hashear / Data to hash

    Returns:
        str: Hash hexadecimal / Hexadecimal hash
    """
    return hashlib.sha256(data).hexdigest()

def chain_hash(previous_hash: str, current_data: bytes) -> str:
    """Genera hash encadenado: hash(previous_hash + current_data) / Generate chained hash: hash(previous_hash + current_data)

    Args:
        previous_hash (str): Hash anterior / Previous hash
        current_data (bytes): Datos actuales / Current data

    Returns:
        str: Nuevo hash encadenado / New chained hash
    """
    combined = (previous_hash + current_data.decode('utf-8', errors='ignore')).encode('utf-8')
    return compute_hash(combined)

def fetch_with_retry(url: str, retries: int = 3, backoff_factor: float = 0.5) -> requests.Response:
    """Realiza request con reintentos / Perform request with retries

    Args:
        url (str): Endpoint a consultar / Endpoint to fetch
        retries (int): Número máximo de reintentos / Max retries
        backoff_factor (float): Factor de espera entre reintentos / Backoff factor

    Returns:
        requests.Response: Respuesta exitosa / Successful response

    Raises:
        requests.exceptions.RequestException: Si todos los reintentos fallan / If all retries fail
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logger.warning(f"Error en fetch: {e} / Fetch error: {e}")
        raise

def create_mock_snapshot():
    """Crea un snapshot mock para modo CI / Create a mock snapshot for CI mode

    Returns:
        Path: Ruta al archivo mock creado / Path to created mock file
    """
    from pathlib import Path
    import json
    from datetime import datetime

    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    mock_data = {
        "timestamp": datetime.now().isoformat(),
        "source": "MOCK_CI",
        "level": "NACIONAL",
        "porcentaje_escrutado": 0.0,
        "votos_totales": 0,
        "note": "Este es un snapshot mock para pruebas en CI - no datos reales / This is a mock snapshot for CI testing - no real data"
    }

    mock_file = data_dir / "snapshot_mock_ci.json"
    mock_file.write_text(json.dumps(mock_data, indent=2, ensure_ascii=False))
    logger.info(f"Snapshot mock creado: {mock_file} / Mock snapshot created: {mock_file}")
    return mock_file

def main():
    """Función principal del script / Main script function

    Descarga snapshots del CNE, genera hashes encadenados y guarda logs/alertas.
    Download CNE snapshots, generate chained hashes and save logs/alerts.
    """
    logger.info("Iniciando download_and_hash / Starting download_and_hash")

    # Parsear argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Descarga y hashea snapshots del CNE / Download and hash CNE snapshots")
    parser.add_argument("--mock", action="store_true", help="Modo mock para CI - no intenta fetch real / Mock mode for CI - skips real fetch")
    args = parser.parse_args()

    config = load_config()

    if args.mock:
        logger.info("MODO MOCK ACTIVADO (CI) - No se intentará descargar del CNE real / MOCK MODE ACTIVATED (CI) - No real CNE fetch will be attempted")
        create_mock_snapshot()
        # En modo mock, saltamos todo el fetch real y continuamos con hash/análisis del mock
        # (puedes extender aquí si necesitas más lógica para mock)
        logger.info("Modo mock completado - pipeline continúa con datos dummy / Mock mode completed - pipeline continues with dummy data")
    else:
        logger.info("Modo real activado - procediendo con fetch al CNE / Real mode activated - proceeding with CNE fetch")
        sources = config.get('sources', [])
        if not sources:
            logger.error("No se encontraron fuentes en config.yaml / No sources found in config.yaml")
            raise ValueError("No sources defined in config.yaml")

        previous_hash = "0" * 64  # hash inicial / initial hash

        for source in sources:
            endpoint = source.get('endpoint')
            if not endpoint:
                logger.error(f"Fuente sin endpoint definido: {source} / Source without endpoint: {source}")
                continue

            try:
                response = fetch_with_retry(endpoint)
                data = response.content
                current_hash = compute_hash(data)
                chained_hash = chain_hash(previous_hash, data)
                # Guarda data y hashes... (tu código original aquí)
                previous_hash = chained_hash
                logger.info(f"Snapshot descargado y hasheado para {source.get('id', 'unknown')} / Snapshot downloaded and hashed for {source.get('id', 'unknown')}")
            except Exception as e:
                logger.error(f"Fallo al descargar {endpoint}: {e} / Failed to download {endpoint}: {e}")

    logger.info("Proceso completado / Process completed")

if __name__ == "__main__":
    main()
