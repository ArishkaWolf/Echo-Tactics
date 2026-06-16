import json
from pathlib import Path


class SaveManager:
    def __init__(self, path="save_data.json"):
        self.path = Path(path)
        self.data = {
            "unlocked_levels": 1,
            "best_results": {},
            "settings": {"volume": 0, "show_tutorial": True},
        }
        self.load()

    def load(self):
        if self.path.exists():
            try:
                self.data.update(json.loads(self.path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")

    def unlock_level(self, index):
        self.data["unlocked_levels"] = max(self.data.get("unlocked_levels", 1), index + 1)
        self.save()

    def record_result(self, level_name, stats):
        best = self.data.setdefault("best_results", {}).get(level_name)
        if best is None or stats["turns"] < best.get("turns", 9999):
            self.data["best_results"][level_name] = stats
            self.save()
