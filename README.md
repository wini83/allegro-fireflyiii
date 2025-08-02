# Allegro FireflyIII

Narzędzia do dopasowywania płatności Allegro do transakcji Firefly III.

## Docker

Zbuduj obraz:

```bash
docker build -t allegro-fireflyiii .
```

### GUI w Streamlit

Uruchom interfejs:

```bash
docker run --rm -p 8501:8501 --env-file .env allegro-fireflyiii
```

Po uruchomieniu aplikacja będzie dostępna pod adresem `http://localhost:8501`.

### Worker

Worker może być uruchamiany przez zewnętrzny cron:

```bash
docker run --rm --env-file .env allegro-fireflyiii python worker.py
```

### Plik `.env`

Wymagane zmienne środowiskowe (zobacz `.env.example`):

- `FIREFLY_URL`
- `FIREFLY_TOKEN`
- `QXLSESSID`
- `TAG`
- `DESCRIPTION_FILTER`

