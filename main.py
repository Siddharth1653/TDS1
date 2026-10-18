import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import dotenv_values
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent

DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

def coerce(key: str, value):
    text = str(value)
    normalized_key = key.lower()
    if normalized_key in {"port", "workers"}:
        try:
            return int(text)
        except (TypeError, ValueError):
            return value
    if normalized_key == "debug":
        return text.strip().lower() in {"true", "1", "yes", "on"}
    return text

def normalize_key(key: str) -> str:
    key = key.strip()
    aliases = {
        "APP_PORT": "port",
        "NUM_WORKERS": "workers",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }
    if key in aliases:
        return aliases[key]
    if key.startswith("APP_"):
        return key[4:].lower()
    return key.lower()

def read_effective_config(overrides: list[str]) -> dict:
    config = dict(DEFAULTS)

    # Layer 2: environment-specific YAML (development by default).
    environment = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "development"))
    yaml_path = BASE_DIR / f"config.{environment}.yaml"
    if yaml_path.exists():
        with yaml_path.open("r", encoding="utf-8") as f:
            yaml_config = yaml.safe_load(f) or {}
        for key, value in yaml_config.items():
            config[normalize_key(str(key))] = coerce(normalize_key(str(key)), value)

    # Layer 3: .env file. dotenv_values reads the file without changing os.environ.
    env_file = dotenv_values(BASE_DIR / ".env")
    for key, value in env_file.items():
        if value is not None:
            normalized = normalize_key(key)
            config[normalized] = coerce(normalized, value)

    # Layer 4: actual OS-level environment variables (APP_* prefix only).
    for key, value in os.environ.items():
        if key.startswith("APP_"):
            normalized = normalize_key(key)
            config[normalized] = coerce(normalized, value)

    # Highest precedence: repeated ?set=key=value query parameters.
    for item in overrides:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        normalized = normalize_key(key)
        config[normalized] = coerce(normalized, value)

    # Never expose the underlying secret.
    if "api_key" in config:
        config["api_key"] = "****"
    return config

app = FastAPI(title="Layered Configuration Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health():
    return {"status": "ok"}

@app.get("/effective-config")
def effective_config(set: Optional[list[str]] = Query(default=None)):
    return read_effective_config(set or [])
