# Huckleberry CLI

Command-line interface for the Huckleberry baby tracking app. Authenticate once
and log sleep, feeds, diapers, and growth from your terminal.

> **Note:** This is an unofficial tool and is not affiliated with Huckleberry.

## Install

```bash
pip install huckleberry-cli
```

Or install from source:

```bash
git clone https://github.com/jayhickey/huckleberry-cli.git
cd huckleberry-cli
pip install -e .
```

## Quick start

```bash
huckleberry login
# ✓ Authenticated! Found 1 child(ren)
huckleberry children
# • Eloise (uid: child_123)
```

## Commands

```bash
huckleberry children --json
# [
#   {
#     "name": "Eloise",
#     "uid": "child_123",
#     "birthDate": "2024-01-10"
#   }
# ]

huckleberry sleep start
huckleberry sleep pause
huckleberry sleep resume
huckleberry sleep stop

huckleberry feed start --side=left
huckleberry feed switch
huckleberry feed stop

huckleberry feed bottle 120 --type="Formula" --units=ml

huckleberry diaper poo --color=yellow --consistency=soft
huckleberry diaper both

huckleberry growth --weight=5.2 --height=52 --head=35

huckleberry --child "Eloise" sleep start
```

## Authentication

Configuration is stored at `~/.config/huckleberry/config.json`.

- Interactive login: `hb login`
- Environment variables:
  - `HUCKLEBERRY_EMAIL`
  - `HUCKLEBERRY_PASSWORD`
  - `HUCKLEBERRY_TIMEZONE` (optional, default: `America/Los_Angeles`)

## Requirements

- Python 3.10+

## License

MIT
