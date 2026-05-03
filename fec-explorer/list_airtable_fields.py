import os
import sys
import urllib.request
import urllib.error
import json

BASE_ID     = "appcYhoQfSuz8ozil"
TABLE_NAME  = "table principale"

token = os.environ.get("AIRTABLE_TOKEN")
if not token:
    print("Erreur : AIRTABLE_TOKEN non défini.")
    sys.exit(1)

url = f"https://api.airtable.com/v0/meta/bases/{BASE_ID}/tables"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
except urllib.error.HTTPError as e:
    print(f"Erreur HTTP {e.code} : {e.reason}")
    sys.exit(1)
except urllib.error.URLError as e:
    print(f"Erreur réseau : {e.reason}")
    sys.exit(1)

table = next((t for t in data.get("tables", []) if t["name"].lower() == TABLE_NAME.lower()), None)
if not table:
    print(f"Table '{TABLE_NAME}' introuvable. Tables disponibles :")
    for t in data.get("tables", []):
        print(f"  {t['name']}")
    sys.exit(1)

for field in table.get("fields", []):
    print(field["name"])
