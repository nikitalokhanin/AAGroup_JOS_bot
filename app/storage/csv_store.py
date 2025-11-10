import os
import csv
from typing import Optional, List
from datetime import datetime, timezone

USERS = "users.csv"
FEEDBACK = "feedback.csv"
CATEGORIES = "categories.csv"
VENUES = "venues.csv"

class CSVStore:
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self._ensure_files()

    # ---------- init & helpers ----------
    def _path(self, name: str) -> str:
        return os.path.join(self.data_dir, name)

    def _ensure_files(self):
        files = {
            USERS: ["telegram_id","username","full_name","role","venue","position","is_active","created_at","updated_at"],
            FEEDBACK: ["id","telegram_id","venue","position","employee_name","table_number","category","comment","created_at"],
            CATEGORIES: ["category","is_active"],
            VENUES: ["venue","is_active"],
        }
        for fname, header in files.items():
            fpath = self._path(fname)
            if not os.path.exists(fpath):
                with open(fpath, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(header)

    def _read_dicts(self, fname: str) -> List[dict]:
        with open(self._path(fname), newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def _append_row(self, fname: str, row: list):
        with open(self._path(fname), "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(row)

    def _write_dicts(self, fname: str, rows: List[dict]):
        # overwrite whole file preserving header order
        path = self._path(fname)
        with open(path, newline="", encoding="utf-8") as f:
            header = next(csv.reader(f))
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)

    # ---------- Users ----------
    def get_user(self, telegram_id: int) -> Optional[dict]:
        for r in self._read_dicts(USERS):
            if r.get("telegram_id") == str(telegram_id):
                return r
        return None

    def upsert_user(self, telegram_id: int, username: str, full_name: str,
                    role: str, venue: str, position: str, is_active: bool = True):
        rows = self._read_dicts(USERS)
        now = datetime.now(timezone.utc).isoformat()
        found = False
        for r in rows:
            if r.get("telegram_id") == str(telegram_id):
                r.update({
                    "username": username or "",
                    "full_name": full_name,
                    "role": role,
                    "venue": venue,
                    "position": position,
                    "is_active": str(bool(is_active)),
                    "updated_at": now,
                })
                found = True
                break
        if not found:
            rows.append({
                "telegram_id": str(telegram_id),
                "username": username or "",
                "full_name": full_name,
                "role": role,
                "venue": venue,
                "position": position,
                "is_active": str(bool(is_active)),
                "created_at": now,
                "updated_at": now,
            })
        self._write_dicts(USERS, rows)

    # ---------- Feedback ----------
    def add_feedback(self, telegram_id: int, venue: str, position: str, employee_name: str,
                     table_number: int, category: str, comment: str):
        rows = self._read_dicts(FEEDBACK)
        new_id = str(len(rows) + 1)
        now = datetime.now(timezone.utc).isoformat()
        self._append_row(FEEDBACK, [
            new_id, str(telegram_id), venue, position, employee_name,
            table_number, category, comment or "", now
        ])

    # ---------- Dictionaries ----------
    def list_categories(self) -> list[str]:
        rows = self._read_dicts(CATEGORIES)
        if not rows:
            # defaults on empty
            return ["Еда", "Напитки", "Сервис", "Атмосфера", "Скорость", "Чек/оплата", "Другое"]
        out = []
        for r in rows:
            active = (r.get("is_active", "").strip().lower() == "true")
            if active or r.get("is_active") == "":
                out.append(r.get("category", "").strip())
        return [x for x in out if x]

    def list_venues(self) -> list[str]:
        rows = self._read_dicts(VENUES)
        if not rows:
            return ["Заведение 1", "Заведение 2"]
        out = []
        for r in rows:
            active = (r.get("is_active", "").strip().lower() == "true")
            if active or r.get("is_active") == "":
                out.append(r.get("venue", "").strip())
        return [x for x in out if x]

    # ---------- Export ----------
    def feedback_csv_path(self) -> str:
        return self._path(FEEDBACK)