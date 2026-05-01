"""
Standalone diagnostic script to list all available Anthropic models for the configured API key.

Uses the same environment settings as the main app (load_dotenv, .env at repo root).
"""

from pathlib import Path
import os
import sys
from dotenv import load_dotenv

# Load .env from project root (repo root, one level above scripts/)
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(ROOT))

from src.security import redact_secrets

try:
    from anthropic import Anthropic
except ImportError:
    print("Error: anthropic package not installed. Run: pip install anthropic")
    exit(1)


def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set. Add it to your .env file.")
        exit(1)

    try:
        client = Anthropic(api_key=api_key)
        page = client.models.list()
        models = page.data if hasattr(page, "data") else list(page)

        if not models:
            print("No models returned.")
            return

        print("\nAvailable Anthropic Models")
        print("-" * 60)
        for model in models:
            model_id = getattr(model, "id", str(model))
            display_name = getattr(model, "display_name", "—")
            print(f"  {model_id}\n    Display: {display_name}")
        print("-" * 60)
        print(f"Total: {len(models)} model(s)\n")

    except Exception as e:
        print(f"Error: {redact_secrets(str(e))}")
        if "401" in str(e) or "authentication" in str(e).lower():
            print("  → Check that ANTHROPIC_API_KEY is valid and has not expired.")
        elif "404" in str(e):
            print("  → API endpoint may have changed. Check Anthropic documentation.")
        exit(1)


if __name__ == "__main__":
    main()
