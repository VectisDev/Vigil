from sentinel.core.normalize import normalize_snapshot, snapshot_to_canonical_json


def test_normalization_is_deterministic():
    raw = {
        "total_votes": 100,
        "valid_votes": 95,
        "null_votes": 3,
        "blank_votes": 2,
        "candidates": {
            "1": 40,
            "2": 30,
            "3": 25,
        },
    }

    snap1 = normalize_snapshot(raw, "Francisco Morazán", "2025-12-03T17:00:00Z")
    snap2 = normalize_snapshot(raw, "Francisco Morazán", "2025-12-03T17:00:00Z")

    json1 = snapshot_to_canonical_json(snap1)
    json2 = snapshot_to_canonical_json(snap2)

    assert json1 == json2
