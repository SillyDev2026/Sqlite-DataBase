# backend.py

from Pipeline import Pipeline
from DataStore import AdvancedSecureDataStore


class Backend:
    def __init__(self, file_name="system.dat"):
        self.data = AdvancedSecureDataStore(file_name)

    # ==================================================
    # INTERNAL
    # ==================================================
    def pipeline(self):
        pipe = Pipeline()
        pipe.context["db"] = self.data
        pipe.context["backend"] = self
        return pipe

    # ==================================================
    # RAW DATASTORE METHODS
    # ==================================================
    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data.set(key, value)
        return value

    def exists(self, key):
        return self.data.exists(key)

    def delete(self, key):
        self.data.delete(key)

    def keys(self):
        return self.data.keys()

    def items(self):
        return self.data.items()

    def close(self):
        self.data.close()

    # ==================================================
    # GENERIC OPERATIONS (NO PRESETS)
    # ==================================================
    def increment(self, key, amount=1, default=0):
        pipe = self.pipeline()

        (
            pipe
            .step(
                lambda _, c: c["db"].get(key, default),
                f"load_{key}"
            )
            .step(
                lambda value, c: value + amount,
                f"increment_{key}"
            )
            .step(
                lambda value, c: (
                    c["db"].set(key, value),
                    value
                )[1],
                f"save_{key}"
            )
        )

        result, _ = pipe.run(None)
        return result

    def decrement(self, key, amount=1, default=0):
        return self.increment(key, -amount, default)

    def multiply(self, key, amount=2, default=0):
        pipe = self.pipeline()

        (
            pipe
            .step(
                lambda _, c: c["db"].get(key, default),
                f"load_{key}"
            )
            .step(
                lambda value, c: value * amount,
                f"multiply_{key}"
            )
            .step(
                lambda value, c: (
                    c["db"].set(key, value),
                    value
                )[1],
                f"save_{key}"
            )
        )

        result, _ = pipe.run(None)
        return result

    def divide(self, key, amount=2, default=0):
        pipe = self.pipeline()

        (
            pipe
            .step(
                lambda _, c: c["db"].get(key, default),
                f"load_{key}"
            )
            .step(
                lambda value, c: value / amount,
                f"divide_{key}"
            )
            .step(
                lambda value, c: (
                    c["db"].set(key, value),
                    value
                )[1],
                f"save_{key}"
            )
        )

        result, _ = pipe.run(None)
        return result

    def append(self, key, value, default=None):
        if default is None:
            default = []

        pipe = self.pipeline()

        (
            pipe
            .step(
                lambda _, c: c["db"].get(key, default),
                f"load_{key}"
            )
            .step(
                lambda arr, c: arr + [value],
                f"append_{key}"
            )
            .step(
                lambda arr, c: (
                    c["db"].set(key, arr),
                    arr
                )[1],
                f"save_{key}"
            )
        )

        result, _ = pipe.run(None)
        return result

    def remove(self, key, value, default=None):
        if default is None:
            default = []

        pipe = self.pipeline()

        (
            pipe
            .step(
                lambda _, c: c["db"].get(key, default),
                f"load_{key}"
            )
            .step(
                lambda arr, c: [x for x in arr if x != value],
                f"remove_{key}"
            )
            .step(
                lambda arr, c: (
                    c["db"].set(key, arr),
                    arr
                )[1],
                f"save_{key}"
            )
        )

        result, _ = pipe.run(None)
        return result

    def update(self, key, fn, default=None):
        pipe = self.pipeline()

        (
            pipe
            .step(
                lambda _, c: c["db"].get(key, default),
                f"load_{key}"
            )
            .step(
                lambda value, c: fn(value),
                f"update_{key}"
            )
            .step(
                lambda value, c: (
                    c["db"].set(key, value),
                    value
                )[1],
                f"save_{key}"
            )
        )

        result, _ = pipe.run(None)
        return result
