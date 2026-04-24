# Dota Analyzer — Project Context

> Global context: ~/.claude/CLAUDE.md (sameer-brain repo)

## What It Does
AI-powered Dota 2 match intelligence. OpenDota public API — no auth, no API key needed.
Player stats, match history, hero pool analysis, peer synergy, trends, behavior,
draft simulator, AI match analysis via local Ollama.

## Stack
Python, Streamlit, OpenDota API, Ollama, Plotly

## Structure
- app.py — main app, 9 tabs: Overview / Match History / Match Analyzer / Heroes / Peers / Trends / Behavior / Draft Simulator / About
- services/dota.py — OpenDota API wrapper

## Key Conventions
- Model selector: format_func=_model_label
- inject_tab_bg_switcher() — full-screen tab backgrounds
- Tab image mapping: heroes, cover, muerta, heroes, cover, heroes, muerta, heroes, logo (9 tabs)
- Footer: sameerbhalerao.com · Soul Spark · OpenDota API · GitHub
- About tab: Portfolio button (amber #f59e0b) first, then LinkedIn / GitHub / Soul Spark

## Deployment
Streamlit Cloud — auto-deploys on push to main (github.com/sameervb/dota-analyzer)

## Recent Changes (Apr 2026)
- Added sameerbhalerao.com to footer and About tab
- _model_label() added
- Tab-to-image mapping corrected (was misaligned)
