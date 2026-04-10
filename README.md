<div align="center">

# 🎮 Dota 2 Analyzer

**Explore any player's stats, match breakdowns, hero pool, peer synergy, and draft strategy — powered by OpenDota's public API and a local LLM. No login. No API key needed.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![OpenDota](https://img.shields.io/badge/OpenDota_API-public-4A90D9?style=flat)](https://docs.opendota.com)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-black?style=flat)](https://ollama.ai)
[![Plotly](https://img.shields.io/badge/Charts-Plotly-3F4F75?style=flat&logo=plotly)](https://plotly.com)
[![License](https://img.shields.io/badge/license-MIT-22c55e?style=flat)](LICENSE)

[**Portfolio**](https://sameerbhalerao.com) · [**Soul Spark**](https://soulspark.me) · [**LinkedIn**](https://linkedin.com/in/sameervb) · [**GitHub**](https://github.com/sameervb)

</div>

---

## What It Does

Enter any Dota 2 account ID and get a full intelligence report — hero pool, win streaks, peer synergy, ward patterns, and behaviour score. Drill into any match for picks/bans, individual player performance, and an AI-generated game breakdown. Run draft simulations with AI strategy recommendations for both sides.

All data comes from [OpenDota's public API](https://docs.opendota.com) — no authentication, no scraping, no API key required.

---

## Features

| Tab | What you get |
|-----|-------------|
| **📊 Overview** | Win rate, K/D/A, GPM/XPM, most-played heroes, recent form summary |
| **🕹️ Match History** | Last 20 matches — hero, outcome, KDA, duration, lobby type |
| **🔍 Match Analyzer** | Full breakdown: picks/bans timeline, player performance table, gold advantage chart, AI match analysis |
| **🦸 Heroes** | Complete hero pool — games played, win rate, KDA, impact score vs. global benchmark |
| **👥 Peers** | Most frequent teammates — win rate synergy, games together, queue recommendations |
| **📈 Trends** | Activity heatmap by day and hour, win/loss streaks, performance trend lines |
| **🗺️ Behavior** | Ward placement map, behaviour score history, abandons, reports, commends |
| **⚔️ Draft Simulator** | Pick heroes for Radiant and Dire, auto-complete remaining slots, get AI strategy brief for both sides |
| **ℹ️ About** | Project context and links |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| UI & hosting | Streamlit |
| Data | OpenDota public API (no API key required) |
| Hero data | OpenDota hero stats + cached hero map |
| Visualisations | Plotly — bar charts, heatmaps, line charts, ward map |
| AI | Ollama (local LLM) via Cloudflare Tunnel |
| Language | Python 3.10+ |

---

## Quick Start

```bash
git clone https://github.com/sameervb/dota-analyzer
cd dota-analyzer
pip install -r requirements.txt

cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml — Ollama URL is optional

streamlit run app.py
```

---

## Secrets

```toml
# .streamlit/secrets.toml

# Optional — enables AI analysis in Match Analyzer, Draft Simulator, and Behavior tabs
OLLAMA_BASE_URL = "https://your-tunnel.trycloudflare.com"
OLLAMA_MODEL    = "llama3.1:8b"
```

Ollama is **optional**. All nine tabs work without it. AI-powered sections show a graceful fallback when no Ollama instance is reachable.

---

## How to Find Your Account ID

1. Go to [opendota.com](https://www.opendota.com)
2. Search your Steam username
3. Copy the numeric ID from the URL — e.g. `opendota.com/players/87278757`

Or search directly in the app sidebar.

---

## Deploying to Streamlit Cloud

1. Fork / push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → New App → select this repo
3. Under **Advanced settings → Secrets**, paste:

```toml
OLLAMA_BASE_URL = "https://your-cloudflare-url.trycloudflare.com"
OLLAMA_MODEL    = "llama3.1:8b"
```

### Cloudflare Tunnel — expose local Ollama to the cloud

```bash
# Run on your machine while Ollama is running on port 11434
cloudflared tunnel --url http://localhost:11434
```

Paste the generated `*.trycloudflare.com` URL as `OLLAMA_BASE_URL` in Streamlit Cloud secrets.

---

## Architecture

```
Browser → Streamlit Cloud → OpenDota API (public, read-only, no key)
                         │
                         ├── Player stats · Match data · Hero pool
                         ├── Peers · Trends · Wards · Behavior score
                         │
                         └── Cloudflare Tunnel ──→ Ollama (your machine)
                                                    ├── Match analysis
                                                    ├── Draft strategy
                                                    └── Behavior insights

No user data stored. All API calls are read-only.
All LLM inference runs on your local machine.
```

---

## Project Context

Built as a standalone portfolio app, part of a series extracted from [Soul Spark](https://soulspark.me) — a local-first personal intelligence platform integrating finance, health, career, and growth into a unified conversational AI advisor.

**Related apps in this series:**
- [jd-analyzer](https://github.com/sameervb/jd-analyzer) — Resume-to-JD fit scorer and cover letter generator
- [journey-planner](https://github.com/sameervb/journey-planner) — Multi-modal route optimizer and AI travel advisor

---

<div align="center">

Built by [Sameer Bhalerao](https://sameerbhalerao.com) · Senior Analytics & AI Product Leader · Amazon L6 BIE · Luxembourg

</div>
