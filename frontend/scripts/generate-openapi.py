import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend")))

from app.main import app

def generate_openapi():
    openapi_schema = app.openapi()
    output_dir = os.path.join(os.path.dirname(__file__), "..", "src", "api")
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, "openapi.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)
    print(f"Exported OpenAPI spec to {filepath}")

if __name__ == "__main__":
    generate_openapi()
