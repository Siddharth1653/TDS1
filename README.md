# Layered Configuration FastAPI

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Test:
```bash
curl 'http://127.0.0.1:8000/effective-config?set=port=9000&set=debug=true'
```

The service merges defaults -> `config.<APP_ENV>.yaml` -> `.env` -> OS `APP_*` variables -> repeated `set` query parameters. `api_key` is always masked. CORS allows cross-origin requests.
