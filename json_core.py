import json
from pathlib import Path


DATA_FILE = Path(__file__).with_name("user_data.json")


def read_json():
    if not DATA_FILE.exists():
        return {
            "appointments": [],
            "reviews": [],
            "clients": {},
        }

    with DATA_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    # На случай, если старый JSON был создан предыдущей версией бота.
    data.setdefault("appointments", [])
    data.setdefault("reviews", [])
    data.setdefault("clients", {})

    return data


def write_json(data):
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
