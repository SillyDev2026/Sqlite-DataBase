import sqlite3
import os
import json
import hmac
import hashlib
import time
import base64
import threading
import queue
import uuid
from typing import Any

from Bnum import Bnum


SECRET_KEY = hashlib.sha256(
    os.getenv("APP_SECRET_KEY", "dev-key-change-me").encode()
).digest()


class AdvancedSecureDataStore:
    def __init__(self, file_name="data.db"):
        appdata = os.getenv("LOCALAPPDATA") or os.getcwd()
        folder = os.path.join(appdata, "MicrosoftCacheService")
        os.makedirs(folder, exist_ok=True)

        self.path = os.path.join(folder, file_name)

        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")

        self._setup()

        self.write_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.lock = threading.Lock()

        self.server_id = str(uuid.uuid4())

        self.worker = threading.Thread(target=self._worker, daemon=True)
        self.worker.start()

    def _setup(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS datastore (
                    key TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    value TEXT NOT NULL,
                    sig TEXT NOT NULL,
                    updated REAL NOT NULL
                )
            """)

            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    key TEXT PRIMARY KEY,
                    server TEXT NOT NULL,
                    expire REAL NOT NULL
                )
            """)

    def _sign(self, key, type_name, raw):
        payload = f"{key}|{type_name}|{raw}".encode()
        return hmac.new(SECRET_KEY, payload, hashlib.sha256).hexdigest()

    def _serialize(self, value: Any):
        if value is None:
            return "none", "null"
        if isinstance(value, bool):
            return "bool", "1" if value else "0"
        if isinstance(value, int):
            return "int", str(value)
        if isinstance(value, float):
            return "float", repr(value)
        if isinstance(value, str):
            return "str", value
        if isinstance(value, bytes):
            return "bytes", base64.b64encode(value).decode()
        if isinstance(value, (list, tuple, dict)):
            return "json", json.dumps(value, ensure_ascii=False, default=str)
        if hasattr(value, "__dict__"):
            return "object", json.dumps({
                "__class__": value.__class__.__name__,
                "__data__": value.__dict__
            }, ensure_ascii=False)

        return "str", str(value)

    def _deserialize(self, type_name, raw):
        try:
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
                    return Bnum.from_dict(obj.get("__data__", {}))
                return obj.get("__data__", obj)
        except:
            return None

        return raw

    def lock_session(self, key, ttl=120):
        now = time.time()
        expire = now + ttl

        with self.lock:
            self.conn.execute(
                "DELETE FROM sessions WHERE expire <= ?",
                (now,)
            )

            row = self.conn.execute(
                "SELECT server, expire FROM sessions WHERE key=?",
                (key,)
            ).fetchone()

            if row:
                if row["server"] == self.server_id:
                    self.conn.execute(
                        "UPDATE sessions SET expire=? WHERE key=?",
                        (expire, key)
                    )
                    self.conn.commit()
                    return True

                return False

            self.conn.execute(
                "INSERT INTO sessions (key, server, expire) VALUES (?, ?, ?)",
                (key, self.server_id, expire)
            )
            self.conn.commit()

        return True

    def unlock_session(self, key):
        with self.lock:
            self.conn.execute(
                "DELETE FROM sessions WHERE key=? AND server=?",
                (key, self.server_id)
            )
            self.conn.commit()

    def is_locked(self, key):
        now = time.time()

        row = self.conn.execute(
            "SELECT server, expire FROM sessions WHERE key=?",
            (key,)
        ).fetchone()

        if not row:
            return False

        if row["expire"] <= now:
            self.unlock_session(key)
            return False

        return True

    def set(self, key, value, sync=False):
        try:
            type_name, raw = self._serialize(value)
            sig = self._sign(key, type_name, raw)
            data = (key, type_name, raw, sig, time.time())

            if sync:
                self._write_batch([data])
            else:
                self.write_queue.put(data)

            return value

        except Exception as e:
            print("SET ERROR:", e)
            return None

    def _worker(self):
        batch = []
        last_flush = time.time()

        while not self.stop_event.is_set():
            try:
                try:
                    item = self.write_queue.get(timeout=0.1)
                    batch.append(item)
                except queue.Empty:
                    pass

                now = time.time()

                if batch and (len(batch) >= 50 or now - last_flush > 0.5):
                    self._write_batch(batch)
                    batch.clear()
                    last_flush = now

            except Exception as e:
                print("WORKER ERROR:", e)

    def _write_batch(self, batch):
        try:
            with self.lock:
                self.conn.executemany("""
                    REPLACE INTO datastore
                    (key, type, value, sig, updated)
                    VALUES (?, ?, ?, ?, ?)
                """, batch)

                self.conn.commit()

        except Exception as e:
            print("DB WRITE ERROR:", e)

    def get(self, key, default=None):
        try:
            row = self.conn.execute("""
                SELECT type, value, sig
                FROM datastore
                WHERE key=?
            """, (key,)).fetchone()

            if not row:
                return default

            if row["sig"] != self._sign(key, row["type"], row["value"]):
                return default

            return self._deserialize(row["type"], row["value"])

        except Exception as e:
            print("GET ERROR:", e)
            return default

    def delete(self, key):
        with self.lock:
            self.conn.execute(
                "DELETE FROM datastore WHERE key=?",
                (key,)
            )
            self.conn.commit()

    def items(self):
        cur = self.conn.execute(
            "SELECT key, type, value FROM datastore"
        )

        return {
            row["key"]: self._deserialize(
                row["type"],
                row["value"]
            )
            for row in cur.fetchall()
        }

    def close(self):
        self.stop_event.set()
        self.worker.join()

        self.conn.close()
