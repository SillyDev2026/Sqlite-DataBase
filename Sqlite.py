import sqlite3
import os
import json
import hmac
import hashlib
import time
import base64
from typing import Any
from Bnum import Bnum


# ---------------- SECURITY KEY ----------------
SECRET_KEY = hashlib.sha256(
    os.getenv("APP_SECRET_KEY", "dev-key-change-me").encode()
).digest()


class AdvancedSecureDataStore:
    def __init__(self, file_name="system.dat"):
        appdata = os.getenv("LOCALAPPDATA") or os.getcwd()

        folder = os.path.join(appdata, "MicrosoftCacheService")
        os.makedirs(folder, exist_ok=True)

        self.path = os.path.join(folder, file_name)

        # safer sqlite config
        self.conn = sqlite3.connect(
            self.path,
            check_same_thread=False
        )
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()

        # faster + safer writes
        self.conn.execute("PRAGMA journal_mode=WAL")

        self._setup()

    # ---------------- SETUP ----------------
    def _setup(self):
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS datastore (
            key TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            value TEXT NOT NULL,
            sig TEXT NOT NULL,
            updated REAL NOT NULL
        )
        """)
        self.conn.commit()

    # ---------------- SIGNING ----------------
    def _sign(self, key: str, type_name: str, raw: str):
        payload = f"{key}|{type_name}|{raw}".encode()
        return hmac.new(SECRET_KEY, payload, hashlib.sha256).hexdigest()

    # ---------------- SERIALIZE ----------------
    def _serialize(self, value: Any):
        if value is None:
            return "none", "null"

        t = type(value)

        if t is bool:
            return "bool", "1" if value else "0"

        if t is int:
            return "int", str(value)

        if t is float:
            return "float", repr(value)

        if t is str:
            return "str", str(value)

        if t is bytes:
            return "bytes", base64.b64encode(value).decode()

        if t in (list, tuple, dict):
            return "json", json.dumps(value, ensure_ascii=False, default=str)

        # safer object fallback
        if hasattr(value, "__dict__"):
            return "object", json.dumps({
                "__class__": value.__class__.__name__,
                "__data__": value.__dict__
            }, ensure_ascii=False)

        return "str", str(value)

    # ---------------- DESERIALIZE ----------------
    def _deserialize(self, type_name: str, raw: str):
        if type_name == "none":
            return None

        if type_name == "bool":
            return raw == "1"

        if type_name == "int":
            return int(raw)

        if type_name == "float":
            return float(raw)

        if type_name == "str":
            return raw

        if type_name == "bytes":
            return base64.b64decode(raw.encode())

        if type_name == "json":
            return json.loads(raw)

        if type_name == "object":
            obj = json.loads(raw)
            if obj.get("__class__") == "Bnum":
                return Bnum.from_dict(obj["__data__"])
            return obj["__data__"]

        return raw

    # ---------------- CORE OPS ----------------
    def set(self, key: str, value: Any):
        type_name, raw = self._serialize(value)
        sig = self._sign(key, type_name, raw)

        self.cur.execute("""
        REPLACE INTO datastore (key, type, value, sig, updated)
        VALUES (?, ?, ?, ?, ?)
        """, (key, type_name, raw, sig, time.time()))

        self.conn.commit()
        return value

    def get(self, key: str, default=None):
        self.cur.execute("""
        SELECT type, value, sig
        FROM datastore
        WHERE key=?
        """, (key,))

        row = self.cur.fetchone()
        if not row:
            return default

        type_name = row["type"]
        raw = row["value"]
        sig = row["sig"]

        # tamper check
        if sig != self._sign(key, type_name, raw):
            return default

        try:
            return self._deserialize(type_name, raw)
        except:
            return default

    def exists(self, key: str):
        self.cur.execute("SELECT 1 FROM datastore WHERE key=?", (key,))
        return self.cur.fetchone() is not None

    def delete(self, key: str):
        self.cur.execute("DELETE FROM datastore WHERE key=?", (key,))
        self.conn.commit()

    # ---------------- FAST OPERATIONS ----------------
    def increment(self, key: str, amount=1):
        value = self.get(key, 0)

        if not isinstance(value, (int, float)):
            raise TypeError(f"{key} is not numeric")

        value = round(value + amount, 10) if isinstance(value, float) else value + amount
        self.set(key, value)
        return value

    def update(self, key: str, fn, default=None):
        value = self.get(key, default)
        new_value = fn(value)
        self.set(key, new_value)
        return new_value

    # ---------------- BULK OPS (FIXED PERFORMANCE) ----------------
    def keys(self):
        self.cur.execute("SELECT key FROM datastore")
        return [r["key"] for r in self.cur.fetchall()]

    def items(self):
        self.cur.execute("SELECT key, type, value FROM datastore")

        result = {}
        for row in self.cur.fetchall():
            try:
                result[row["key"]] = self._deserialize(row["type"], row["value"])
            except:
                continue

        return result

    # ---------------- CLOSE ----------------
    def close(self):
        try:
            self.conn.close()
        except:
            pass
