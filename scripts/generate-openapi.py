import os
import json
import sys

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.main import app

def generate_openapi_spec():
    openapi_schema = app.openapi()
    output_dir = os.path.join(os.path.dirname(__file__), "..", "frontend", "src", "api")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "openapi.json")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)
    print(f"Exported OpenAPI spec to {output_path}")

if __name__ == "__main__":
    generate_openapi_spec()
