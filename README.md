# Dota 2 Analyzer

A public Streamlit app for exploring Dota 2 player stats, match history, and draft strategy — powered by the [OpenDota API](https://docs.opendota.com/) and a local LLM (Ollama).

## Features

- **Player Overview** — win rate, K/D/A, GPM/XPM, most-played heroes
- **Match History** — filterable table of recent matches with outcomes and stats
- **Match Analyzer** — full breakdown of any match: picks/bans, player performance, gold advantage chart, and AI analysis
- **Draft Simulator** — pick heroes for Radiant and Dire, auto-fill remaining slots with weighted-random logic, get AI strategy advice

## Tech Stack

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![OpenDota](https://img.shields.io/badge/OpenDota_API-public-blue)
![Ollama](https://img.shields.io/badge/LLM-Ollama-black)
![Plotly](https://img.shields.io/badge/Charts-Plotly-3F4F75?style=flat&logo=plotly)

- **Data**: OpenDota public API (no API key required)
- **AI Analysis**: Ollama running locally, tunnelled via Cloudflare for cloud deployment
- **Hosting**: Streamlit Community Cloud
- **No login. No profile. No data stored.**

## Local Setup

```bash
git clone https://github.com/YOUR_USERNAME/dota-analyzer
cd dota-analyzer
pip install -r requirements.txt

# Copy and fill in secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your Ollama URL

streamlit run app.py
```

## Streamlit Cloud Deployment

1. Push this repo to GitHub (keep `.streamlit/secrets.toml` in `.gitignore`)
2. Go to [share.streamlit.io](https://share.streamlit.io) → New app → select this repo
3. Under **Advanced settings → Secrets**, paste the contents of `secrets.toml.example` with your values filled in
4. Deploy

## Ollama via Cloudflare Tunnel

The AI features require an Ollama instance. For Streamlit Community Cloud:

```bash
# On your local machine (with Ollama running):
cloudflared tunnel --url http://localhost:11434
```

Copy the generated `*.trycloudflare.com` URL into your Streamlit Cloud secrets as `OLLAMA_BASE_URL`.

## Architecture

```
Browser → Streamlit Cloud → OpenDota API (public)
                         → Cloudflare Tunnel → Ollama (your machine)
```

No user data is stored. All API calls are read-only. The LLM prompt is built from match/player data and sent directly to Ollama — nothing is logged server-side.

---

Built as part of a standalone portfolio series extracted from [Soul Spark](https://soulspark.me) — a local-first personal intelligence platform.
