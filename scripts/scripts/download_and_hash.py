import json
import hashlib
from datetime import datetime
from pathlib import Path

# Directorios
data_dir = Path("data")
hash_dir = Path("hashes")

data_dir.mkdir(exist_ok=True)
hash_dir.mkdir(exist_ok=True)

# Simulación (luego será el CNE)
sample_data = {
    "timestamp": datetime.utcnow().isoformat(),
    "example": "placeholder"
}

timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
json_path = data_dir / f"snapshot_{timestamp}.json"
hash_path = hash_dir / f"snapshot_{timestamp}.sha256"

with open(json_path, "w") as f:
    json.dump(sample_data, f, indent=2)

hash_value = hashlib.sha256(
    json.dumps(sample_data, sort_keys=True).encode()
).hexdigest()

with open(hash_path, "w") as f:
    f.write(hash_value)

print("Snapshot y hash creados:", timestamp)
