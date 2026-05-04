# envdiff

> Compare `.env` files across environments and surface missing or mismatched variables.

---

## Installation

```bash
pip install envdiff
```

Or install from source:

```bash
git clone https://github.com/yourname/envdiff.git && cd envdiff && pip install .
```

---

## Usage

```bash
envdiff .env.development .env.production
```

**Example output:**

```
Missing in .env.production:
  - DATABASE_URL
  - REDIS_HOST

Mismatched values:
  - LOG_LEVEL: "debug" vs "info"
  - PORT: "3000" vs "8080"

✔ 12 variables match across both files.
```

You can also compare multiple files at once:

```bash
envdiff .env.development .env.staging .env.production
```

Use the `--keys-only` flag to ignore values and check only for missing keys:

```bash
envdiff .env.development .env.production --keys-only
```

---

## Options

| Flag | Description |
|------|-------------|
| `--keys-only` | Only check for missing keys, ignore value differences |
| `--quiet` | Suppress matched variable output |
| `--json` | Output results as JSON |

---

## License

This project is licensed under the [MIT License](LICENSE).