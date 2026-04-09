"""
Dota 2 Analyzer — Standalone Streamlit App
Player stats, match history, match analysis, and draft simulator.
Powered by OpenDota API. AI analysis via Ollama (optional).
"""
from __future__ import annotations

import os
import json
from datetime import datetime

import requests
import streamlit as st
import pandas as pd

from services.dota import (
    get_opendota_hero_map,
    get_opendota_hero_stats,
    get_opendota_player,
    get_opendota_recent_matches,
    get_opendota_win_loss,
    get_opendota_match,
    search_opendota_players,
    build_dota_match_context,
    generate_random_draft,
    get_hero_name,
    get_hero_image,
    build_hero_stats_index,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dota 2 Analyzer",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Minimal CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #0d1117; }
[data-testid="stSidebar"] { background: #161b22; }
h1, h2, h3 { color: #e6edf3; }
.metric-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
}
.win { color: #3fb950; }
.loss { color: #f85149; }
.hero-chip {
    display: inline-block;
    background: #21262d;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 4px 10px;
    font-size: 13px;
    margin: 2px;
}
</style>
""", unsafe_allow_html=True)


# ── Ollama helper ──────────────────────────────────────────────────────────────
def _get_ollama_url() -> str | None:
    try:
        return st.secrets.get("OLLAMA_BASE_URL") or os.environ.get("OLLAMA_BASE_URL")
    except Exception:
        return os.environ.get("OLLAMA_BASE_URL")


def _get_ollama_model() -> str:
    try:
        return st.secrets.get("OLLAMA_MODEL") or os.environ.get("OLLAMA_MODEL", "llama3")
    except Exception:
        return os.environ.get("OLLAMA_MODEL", "llama3")


def query_ollama(prompt: str, system: str = "") -> str | None:
    base_url = _get_ollama_url()
    if not base_url:
        return None
    try:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        resp = requests.post(
            f"{base_url.rstrip('/')}/api/chat",
            json={"model": _get_ollama_model(), "messages": messages, "stream": False},
            timeout=90,
        )
        if resp.ok:
            return resp.json().get("message", {}).get("content", "").strip()
    except Exception:
        pass
    return None


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎮 Dota 2 Analyzer")
    st.markdown("---")

    _search_query = st.text_input("Search player by name", placeholder="e.g. Miracle-")
    if _search_query:
        with st.spinner("Searching..."):
            _results = search_opendota_players(_search_query)
        if _results:
            _options = {f"{r.get('personaname', 'Unknown')} ({r.get('account_id')})": r.get("account_id") for r in _results[:10]}
            _selected = st.selectbox("Select player", list(_options.keys()))
            if st.button("Load player", use_container_width=True):
                st.session_state["account_id"] = str(_options[_selected])
                st.rerun()
        else:
            st.warning("No players found.")

    st.markdown("**Or enter Account ID directly**")
    _account_id_input = st.text_input("Steam Account ID", value=st.session_state.get("account_id", ""), placeholder="e.g. 87278757")
    if st.button("Load", use_container_width=True, type="primary"):
        if _account_id_input.strip():
            st.session_state["account_id"] = _account_id_input.strip()
            st.rerun()

    st.markdown("---")
    st.caption("Data from [OpenDota API](https://www.opendota.com). No login required.")

    _ai_available = bool(_get_ollama_url())
    if _ai_available:
        st.success("🟢 AI analysis available")
    else:
        st.info("🔵 AI analysis offline\n\nSet `OLLAMA_BASE_URL` in secrets to enable.")


# ── Main content ───────────────────────────────────────────────────────────────
account_id = st.session_state.get("account_id")

if not account_id:
    st.markdown("# 🎮 Dota 2 Analyzer")
    st.markdown("Search for a player or enter a Steam Account ID in the sidebar to get started.")
    st.markdown("""
    **What this tool does:**
    - 📊 Player overview — rank, win rate, recent performance
    - 🕹️ Match history — last 20 games with hero, KDA, outcome
    - 🔍 Match analyzer — deep breakdown of any match + AI commentary
    - ⚔️ Draft simulator — build a draft, get AI strategy recommendations
    """)
    st.stop()


# ── Load core data ─────────────────────────────────────────────────────────────
with st.spinner("Loading hero data..."):
    hero_map = get_opendota_hero_map()
    hero_stats = get_opendota_hero_stats()

hero_names_sorted = sorted(
    [h["name"] for h in hero_map.values() if h.get("name")],
    key=lambda x: x.lower()
)


# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_overview, tab_matches, tab_analyzer, tab_draft = st.tabs([
    "📊 Player Overview",
    "🕹️ Match History",
    "🔍 Match Analyzer",
    "⚔️ Draft Simulator",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Player Overview
# ══════════════════════════════════════════════════════════════════════════════
with tab_overview:
    with st.spinner(f"Loading player {account_id}..."):
        player_data = get_opendota_player(account_id)
        wl_data = get_opendota_win_loss(account_id)
        recent = get_opendota_recent_matches(account_id, limit=20)

    profile = player_data.get("profile") or {}
    name = profile.get("personaname") or f"Player {account_id}"
    avatar = profile.get("avatarfull") or profile.get("avatar")
    rank_tier = player_data.get("rank_tier")

    # Header
    col_av, col_info = st.columns([1, 4])
    with col_av:
        if avatar:
            st.image(avatar, width=80)
    with col_info:
        st.markdown(f"## {name}")
        st.caption(f"Account ID: {account_id}")

    st.markdown("---")

    # Stats
    wins = wl_data.get("win", 0)
    losses = wl_data.get("lose", 0)
    total = wins + losses
    win_rate = (wins / total * 100) if total > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Wins", wins)
    with c2:
        st.metric("Losses", losses)
    with c3:
        st.metric("Win Rate", f"{win_rate:.1f}%")
    with c4:
        st.metric("Total Games", total)

    # Recent performance from last 20 matches
    if recent:
        kills = [m.get("kills", 0) for m in recent]
        deaths = [m.get("deaths", 0) for m in recent]
        assists = [m.get("assists", 0) for m in recent]
        gpms = [m.get("gold_per_min", 0) for m in recent]
        recent_wins = sum(1 for m in recent if (m.get("radiant_win") and m.get("player_slot", 0) < 128) or (not m.get("radiant_win") and m.get("player_slot", 128) >= 128))

        st.markdown("### Last 20 matches")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.metric("Avg Kills", f"{sum(kills)/len(kills):.1f}")
        with c2:
            st.metric("Avg Deaths", f"{sum(deaths)/len(deaths):.1f}")
        with c3:
            st.metric("Avg Assists", f"{sum(assists)/len(assists):.1f}")
        with c4:
            st.metric("Avg GPM", f"{sum(gpms)/len(gpms):.0f}")
        with c5:
            st.metric("Recent Win Rate", f"{recent_wins/len(recent)*100:.0f}%")

        # Most played heroes
        hero_counts: dict = {}
        for m in recent:
            hid = m.get("hero_id")
            if hid:
                hname = get_hero_name(hero_map, hid)
                hero_counts[hname] = hero_counts.get(hname, 0) + 1

        st.markdown("**Most played heroes (last 20):**")
        top_heroes = sorted(hero_counts.items(), key=lambda x: x[1], reverse=True)[:8]
        chips = " ".join(f'<span class="hero-chip">{h} × {c}</span>' for h, c in top_heroes)
        st.markdown(chips, unsafe_allow_html=True)

    # AI overview
    if recent and st.button("✨ Generate AI performance summary", key="ai_overview"):
        if not _ai_available:
            st.warning("AI analysis requires Ollama. Set `OLLAMA_BASE_URL` in Streamlit Cloud → Settings → Secrets.")
        else:
            context = f"Player: {name}\nWin rate: {win_rate:.1f}% ({wins}W/{losses}L)\n"
            context += f"Avg KDA (last 20): {sum(kills)/len(kills):.1f}/{sum(deaths)/len(deaths):.1f}/{sum(assists)/len(assists):.1f}\n"
            context += f"Avg GPM: {sum(gpms)/len(gpms):.0f}\n"
            context += f"Most played: {', '.join(h for h, _ in top_heroes[:5])}\n"
            with st.spinner("Analysing..."):
                analysis = query_ollama(
                    f"Analyse this Dota 2 player's recent performance and give concise insights:\n\n{context}",
                    system="You are a Dota 2 coach. Be specific, direct, and helpful. 3-5 sentences max."
                )
            if analysis:
                st.info(analysis)
            else:
                st.error("Could not reach Ollama. Check your tunnel URL in secrets.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Match History
# ══════════════════════════════════════════════════════════════════════════════
with tab_matches:
    with st.spinner("Loading match history..."):
        matches = get_opendota_recent_matches(account_id, limit=20)

    if not matches:
        st.warning("No recent matches found.")
    else:
        st.markdown(f"### Last {len(matches)} matches")

        rows = []
        for m in matches:
            hid = m.get("hero_id")
            hname = get_hero_name(hero_map, hid)
            slot = m.get("player_slot", 0)
            is_radiant = slot < 128
            radiant_win = m.get("radiant_win")
            won = (is_radiant and radiant_win) or (not is_radiant and not radiant_win)
            duration_min = round((m.get("duration", 0)) / 60, 1)
            start = m.get("start_time")
            date_str = datetime.fromtimestamp(start).strftime("%d %b %Y") if start else "-"
            rows.append({
                "Date": date_str,
                "Hero": hname,
                "Result": "✅ Win" if won else "❌ Loss",
                "K/D/A": f"{m.get('kills',0)}/{m.get('deaths',0)}/{m.get('assists',0)}",
                "GPM": m.get("gold_per_min", 0),
                "XPM": m.get("xp_per_min", 0),
                "Duration": f"{duration_min}m",
                "Match ID": str(m.get("match_id", "")),
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, width="stretch", hide_index=True)

        # Quick select for match analyzer
        match_ids = [str(m.get("match_id")) for m in matches if m.get("match_id")]
        selected_match = st.selectbox("Analyse a match →", ["Select a match..."] + match_ids)
        if selected_match and selected_match != "Select a match...":
            st.session_state["selected_match_id"] = selected_match
            st.info(f"Match {selected_match} selected. Go to **Match Analyzer** tab.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Match Analyzer
# ══════════════════════════════════════════════════════════════════════════════
with tab_analyzer:
    st.markdown("### Match Analyzer")

    _match_id_input = st.text_input(
        "Match ID",
        value=st.session_state.get("selected_match_id", ""),
        placeholder="e.g. 7891234567"
    )

    if _match_id_input and st.button("Load match", key="load_match", type="primary"):
        st.session_state["selected_match_id"] = _match_id_input.strip()

    match_id_to_load = st.session_state.get("selected_match_id")

    if match_id_to_load:
        with st.spinner(f"Loading match {match_id_to_load}..."):
            match_data = get_opendota_match(match_id_to_load)

        if not match_data or not match_data.get("match_id"):
            st.error("Match not found or not parsed by OpenDota yet.")
        else:
            duration = match_data.get("duration", 0)
            radiant_win = match_data.get("radiant_win")
            radiant_score = match_data.get("radiant_score", 0)
            dire_score = match_data.get("dire_score", 0)
            start_time = match_data.get("start_time")

            # Header
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Duration", f"{round(duration/60, 1)}m")
            with c2:
                winner = "🟢 Radiant" if radiant_win else "🔴 Dire"
                st.metric("Winner", winner)
            with c3:
                st.metric("Score", f"{radiant_score} — {dire_score}")

            if start_time:
                st.caption(f"Played: {datetime.fromtimestamp(start_time).strftime('%d %b %Y %H:%M')}")

            # Picks/bans
            picks_bans = match_data.get("picks_bans") or []
            if picks_bans:
                st.markdown("#### Draft")
                rp = [get_hero_name(hero_map, pb["hero_id"]) for pb in picks_bans if pb.get("is_pick") and pb.get("team") == 0]
                dp = [get_hero_name(hero_map, pb["hero_id"]) for pb in picks_bans if pb.get("is_pick") and pb.get("team") == 1]
                col_r, col_d = st.columns(2)
                with col_r:
                    st.markdown("**🟢 Radiant picks**")
                    st.markdown(" ".join(f'<span class="hero-chip">{h}</span>' for h in rp), unsafe_allow_html=True)
                with col_d:
                    st.markdown("**🔴 Dire picks**")
                    st.markdown(" ".join(f'<span class="hero-chip">{h}</span>' for h in dp), unsafe_allow_html=True)

            # Player table
            players = match_data.get("players") or []
            if players:
                st.markdown("#### Player performance")
                player_rows = []
                for p in players:
                    hname = get_hero_name(hero_map, p.get("hero_id"))
                    side = "🟢 Radiant" if p.get("isRadiant") else "🔴 Dire"
                    player_rows.append({
                        "Side": side,
                        "Hero": hname,
                        "Level": p.get("level", 0),
                        "K/D/A": f"{p.get('kills',0)}/{p.get('deaths',0)}/{p.get('assists',0)}",
                        "GPM": p.get("gold_per_min", 0),
                        "XPM": p.get("xp_per_min", 0),
                        "Net Worth": p.get("net_worth", 0),
                        "Hero Dmg": p.get("hero_damage", 0),
                        "Tower Dmg": p.get("tower_damage", 0),
                    })
                st.dataframe(pd.DataFrame(player_rows), use_container_width=True, hide_index=True)

            # Gold advantage chart
            gold_adv = match_data.get("radiant_gold_adv") or []
            if gold_adv:
                st.markdown("#### Gold advantage over time (Radiant +)")
                chart_df = pd.DataFrame({
                    "Minute": list(range(len(gold_adv))),
                    "Radiant Gold Advantage": gold_adv,
                })
                st.line_chart(chart_df.set_index("Minute"))

            # AI analysis
            if st.button("✨ AI match analysis", key="ai_match"):
                if not _ai_available:
                    st.warning("AI analysis requires Ollama. Set `OLLAMA_BASE_URL` in Streamlit Cloud → Settings → Secrets.")
                else:
                    ctx = build_dota_match_context(match_data, hero_map)
                    with st.spinner("Analysing match..."):
                        analysis = query_ollama(
                            f"Analyse this Dota 2 match and give key insights — turning points, standout performers, strategic decisions:\n\n{ctx}",
                            system="You are a Dota 2 analyst. Be specific and insightful. Use the data provided. 150-250 words."
                        )
                    if analysis:
                        st.markdown("**AI analysis:**")
                        st.markdown(analysis)
                    else:
                        st.error("Could not reach Ollama. Check your tunnel URL in secrets.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Draft Simulator
# ══════════════════════════════════════════════════════════════════════════════
with tab_draft:
    st.markdown("### Draft Simulator")
    st.caption("Build a draft, get AI strategy recommendations.")

    hero_options = ["Select Hero"] + hero_names_sorted

    col_r, col_d = st.columns(2)

    with col_r:
        st.markdown("#### 🟢 Radiant")
        radiant_picks = []
        for i in range(5):
            h = st.selectbox(f"Pos {i+1}", hero_options, key=f"draft_r_{i}")
            radiant_picks.append(None if h == "Select Hero" else h)

    with col_d:
        st.markdown("#### 🔴 Dire")
        dire_picks = []
        for i in range(5):
            h = st.selectbox(f"Pos {i+1}", hero_options, key=f"draft_d_{i}")
            dire_picks.append(None if h == "Select Hero" else h)

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("🎲 Random draft", use_container_width=True):
            with st.spinner("Generating draft..."):
                rand_r, rand_d = generate_random_draft(
                    hero_names_sorted, hero_stats,
                    existing_radiant=radiant_picks,
                    existing_dire=dire_picks,
                )
            st.session_state["rand_radiant"] = rand_r
            st.session_state["rand_dire"] = rand_d
            st.rerun()

    with btn_col2:
        if st.button("✨ Get AI strategy", use_container_width=True, type="primary"):
            active_r = [h for h in radiant_picks if h]
            active_d = [h for h in dire_picks if h]
            if not active_r and not active_d:
                st.warning("Pick at least one hero to get a strategy.")
            elif not _ai_available:
                st.warning("AI analysis requires Ollama. Set `OLLAMA_BASE_URL` in Streamlit Cloud → Settings → Secrets.")
            else:
                draft_context = f"Radiant: {', '.join(active_r) or 'unknown'}\nDire: {', '.join(active_d) or 'unknown'}"
                with st.spinner("Generating strategy..."):
                    strategy = query_ollama(
                        f"Analyse this Dota 2 draft and give strategy recommendations for both teams:\n\n{draft_context}",
                        system=(
                            "You are a Dota 2 coach. For each team: explain the win condition, "
                            "key timing spikes, itemisation priorities, and what to watch out for. "
                            "Be specific and practical. 200-300 words total."
                        )
                    )
                if strategy:
                    st.markdown("**Draft strategy:**")
                    st.markdown(strategy)
                else:
                    st.error("Could not reach Ollama. Check your tunnel URL in secrets.")

    # Show random draft result
    if st.session_state.get("rand_radiant"):
        st.markdown("---")
        st.markdown("**Generated draft:**")
        rc, dc = st.columns(2)
        with rc:
            st.markdown("**🟢 Radiant**")
            for i, h in enumerate(st.session_state["rand_radiant"]):
                st.markdown(f"Pos {i+1}: **{h or '—'}**")
        with dc:
            st.markdown("**🔴 Dire**")
            for i, h in enumerate(st.session_state["rand_dire"]):
                st.markdown(f"Pos {i+1}: **{h or '—'}**")
