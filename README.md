C:\Users\<ur username>\AppData\Local\MicrosoftCacheService
example
C:\Users\wow\AppData\Local\MicrosoftCacheService
find system.dat
if found then delete for a new start if u are doing a new save system
if not then create a new save file 
# Backend.py — Quick Start

A secure Python backend for games and apps.

---

## Install

Place files:
backend.py
Pipeline.py
Sqlite.py

Import:
from backend import Backend

---

## Create Database

db = Backend()

---

## Save Data

db.set("Coins", 100)
db.set("Name", "Player")

---

## Load Data

coins = db.get("Coins", 0)

---

## Basic Operations

db.increment("Coins", 5)
db.decrement("Coins", 2)

db.append("Inventory", "Sword")
db.remove("Inventory", "Sword")

---

## Done

You are ready to build games.

## Examples
# Backend.py

A secure and flexible Python backend module built with:

* **Pipeline system** for chained operations
* **Secure SQLite datastore**
* **Automatic type detection**
* **Tamper protection**
* Easy methods like:

```python
increment()
decrement()
multiply()
divide()
append()
remove()
update()
get()
set()
```

Perfect for:

* Games
* Save systems
* Simulators
* Clicker games
* Local app storage
* Automation systems

---

# Installation

Put these files in your project:

```text
backend.py
Pipeline.py
DataStore.py
```

Then import:

```python
from backend import Backend
```

---

# Quick Start

```python
from backend import Backend

db = Backend()
```

This creates a secure save file automatically.

---

# Basic Usage

# Save Data

```python
db.set("Coins", 100)
db.set("Name", "Player1")
db.set("Music", True)
db.set("Volume", 0.75)
```

---

# Load Data

```python
coins = db.get("Coins", 0)
name = db.get("Name", "Guest")
```

---

# Automatic Types

Backend automatically stores and restores types:

```python
db.set("Coins", 150)
db.set("Price", 2.5)
db.set("Name", "Alex")
db.set("Inventory", ["Sword", "Potion"])
db.set("Settings", {"music": True})
```

Returns:

```python
int
float
str
list
dict
```

---

# Numeric Operations

## Increment

```python
db.increment("Coins", 5)
```

## Decrement

```python
db.decrement("Coins", 2)
```

## Multiply

```python
db.multiply("Coins", 3)
```

## Divide

```python
db.divide("Coins", 2)
```

---

# Lists

## Append

```python
db.append("Inventory", "Sword")
db.append("Inventory", "Potion")
```

## Remove

```python
db.remove("Inventory", "Potion")
```

---

# Update Any Value

```python
db.update("Coins", lambda x: x + 50, 0)
```

Example:

```python
db.update("Name", lambda x: x.upper(), "guest")
```

---

# Exists Check

```python
if db.exists("Coins"):
    print("Player has coins")
```

---

# Delete Key

```python
db.delete("Coins")
```

---

# Get All Keys

```python
print(db.keys())
```

---

# Get All Data

```python
print(db.items())
```

---

# Example: Clicker Game

```python
from backend import Backend

db = Backend()

coins = db.get("Coins", 0)
power = db.get("ClickPower", 1)

coins += power

db.set("Coins", coins)
```

---

# Example: Inventory System

```python
db.append("Inventory", "Sword")
db.append("Inventory", "Shield")
db.remove("Inventory", "Sword")
```

---

# Example: Rebirth System

```python
coins = db.get("Coins", 0)

if coins >= 1000:
    db.set("Coins", 0)
    db.increment("Rebirths", 1)
```

---

# Security Features

Your data is protected with:

* SQLite database
* HMAC signatures
* Tamper detection
* Hidden AppData storage
* Automatic fallback defaults

If users manually edit values, invalid entries are rejected.

---

# Save File Location (Windows)

```text
LOCALAPPDATA/MicrosoftCacheService/system.dat
```

---

# Close Database

When quitting app/game:

```python
db.close()
```

---

# Recommended For Games

Use keys like:

```python
Coins
Rebirths
ClickPower
Inventory
Pets
Upgrades
Settings
Volume
```

---

# Why Use Backend.py?

Instead of:

```python
coins = coins + 1
```

Use:

```python
db.increment("Coins")
```

Instead of:

```python
inventory.append("Sword")
```

Use:

```python
db.append("Inventory", "Sword")
```

Cleaner. Safer. Easier.

---

# License

Free to use and modify.

---

# Author

Built for Python developers who want a powerful local backend system.
