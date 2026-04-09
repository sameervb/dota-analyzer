"""
Dota 2 Analyzer — Standalone Streamlit App
Complete redesign with full feature parity with Soul Spark gaming tab.
Powered by OpenDota API + Ollama AI analysis.
"""
from __future__ import annotations

import os
import io
import csv
from datetime import datetime

import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

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

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif; }

[data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0a0e1a 0%, #0d1117 50%, #0a0e1a 100%);
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #111827 100%);
    border-right: 1px solid #1f2937;
}
[data-testid="stSidebar"] .stMarkdown { color: #9ca3af; }

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #111827;
    padding: 4px;
    border-radius: 12px;
    border: 1px solid #1f2937;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 8px;
    color: #6b7280;
    border: none;
    padding: 8px 20px;
    font-weight: 500;
    transition: all 0.2s;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #c84b31 0%, #9b2335 100%) !important;
    color: #ffffff !important;
    box-shadow: 0 4px 12px rgba(200,75,49,0.4);
}

/* Metric cards */
.kpi-card {
    background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
    border: 1px solid #374151;
    border-radius: 16px;
    padding: 20px 24px;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #c84b31, #e07b5a);
    border-radius: 16px 16px 0 0;
}
.kpi-card .kpi-value {
    font-size: 2rem;
    font-weight: 700;
    color: #f9fafb;
    line-height: 1;
    margin: 8px 0 4px;
}
.kpi-card .kpi-label {
    font-size: 0.75rem;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 500;
}
.kpi-card .kpi-sub {
    font-size: 0.8rem;
    color: #9ca3af;
    margin-top: 4px;
}

/* Hero chip */
.hero-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #1f2937;
    border: 1px solid #374151;
    border-radius: 20px;
    padding: 4px 12px 4px 6px;
    font-size: 0.8rem;
    color: #d1d5db;
    margin: 3px;
}

/* Match row */
.match-win { color: #22c55e; font-weight: 600; }
.match-loss { color: #ef4444; font-weight: 600; }

/* Section header */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 28px 0 16px;
}
.section-header .line {
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, #374151, transparent);
}
.section-header h3 {
    color: #f9fafb !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    white-space: nowrap;
    margin: 0 !important;
}

/* VS divider */
.vs-badge {
    background: linear-gradient(135deg, #c84b31, #9b2335);
    border-radius: 50%;
    width: 56px;
    height: 56px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    font-weight: 800;
    color: white;
    margin: auto;
    box-shadow: 0 4px 20px rgba(200,75,49,0.5);
}

/* Draft position card */
.pos-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #6b7280;
    font-weight: 600;
    margin-bottom: 2px;
}

/* AI narrative box */
.lore-box {
    background: linear-gradient(135deg, #1a0a14 0%, #1f1030 100%);
    border: 1px solid #7c3aed;
    border-left: 4px solid #7c3aed;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 12px 0;
    font-style: italic;
    color: #c4b5fd;
    line-height: 1.7;
}

/* Win/loss indicator */
.win-badge { color: #22c55e; }
.loss-badge { color: #ef4444; }

/* Advantage positive/negative */
.adv-pos { color: #22c55e; }
.adv-neg { color: #ef4444; }

/* Footer */
.footer {
    margin-top: 60px;
    padding: 24px;
    text-align: center;
    border-top: 1px solid #1f2937;
    color: #4b5563;
    font-size: 0.8rem;
    line-height: 1.8;
}
.footer a { color: #c84b31; text-decoration: none; }

/* Team header */
.team-radiant { color: #22c55e; font-weight: 700; font-size: 1rem; }
.team-dire { color: #ef4444; font-weight: 700; font-size: 1rem; }

/* Streamlit overrides */
div[data-testid="stMetric"] { background: transparent; }
.stButton button {
    border-radius: 10px;
    font-weight: 500;
    transition: all 0.2s;
}
.stSelectbox > div > div {
    background: #1f2937 !important;
    border-color: #374151 !important;
    color: #f9fafb !important;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _get_ollama_url() -> str | None:
    try:
        return st.secrets.get("OLLAMA_BASE_URL") or os.environ.get("OLLAMA_BASE_URL")
    except Exception:
        return os.environ.get("OLLAMA_BASE_URL")


def _get_ollama_model() -> str:
    try:
        return st.secrets.get("OLLAMA_MODEL") or os.environ.get("OLLAMA_MODEL", "llama3.1")
    except Exception:
        return os.environ.get("OLLAMA_MODEL", "llama3.1")


def query_ollama(prompt: str, system: str = "", max_tokens: int = 1000) -> str | None:
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
            json={"model": _get_ollama_model(), "messages": messages, "stream": False,
                  "options": {"num_predict": max_tokens}},
            timeout=120,
        )
        if resp.ok:
            return resp.json().get("message", {}).get("content", "").strip()
    except Exception:
        pass
    return None


def _ai_unavailable_msg():
    st.warning("AI analysis requires Ollama. Set `OLLAMA_BASE_URL` in Streamlit Cloud → Settings → Secrets, then start your Cloudflare tunnel.")


def section_header(title: str, icon: str = ""):
    label = f"{icon} {title}" if icon else title
    st.markdown(f"""
    <div class="section-header">
        <h3>{label}</h3>
        <div class="line"></div>
    </div>""", unsafe_allow_html=True)


def kpi_card(label: str, value: str, sub: str = "", color: str = "#f9fafb"):
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value" style="color:{color}">{value}</div>
        {'<div class="kpi-sub">' + sub + '</div>' if sub else ''}
    </div>""", unsafe_allow_html=True)


def make_advantage_chart(data: list, title: str, color_pos: str = "#22c55e", color_neg: str = "#ef4444") -> go.Figure:
    minutes = list(range(len(data)))
    colors = [color_pos if v >= 0 else color_neg for v in data]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=minutes, y=data,
        mode="lines",
        line=dict(width=2, color="#6b7280"),
        showlegend=False,
        hovertemplate="Min %{x}: %{y:+,}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=minutes, y=data,
        marker_color=colors,
        marker_opacity=0.35,
        showlegend=False,
        hovertemplate="Min %{x}: %{y:+,}<extra></extra>",
    ))
    fig.add_hline(y=0, line_dash="dot", line_color="#374151", line_width=1)
    fig.update_layout(
        title=dict(text=title, font=dict(color="#9ca3af", size=13), x=0),
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font_color="#9ca3af",
        height=220,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(gridcolor="#1f2937", title="Minute", tickfont=dict(size=10)),
        yaxis=dict(gridcolor="#1f2937", zeroline=False, tickfont=dict(size=10)),
        barmode="overlay",
    )
    return fig


def make_cumulative_winrate_chart(matches: list, hero_map: dict) -> go.Figure:
    results = []
    for m in matches:
        slot = m.get("player_slot", 0)
        is_radiant = slot < 128
        won = (is_radiant and m.get("radiant_win")) or (not is_radiant and not m.get("radiant_win"))
        results.append(1 if won else 0)
    cumulative = [sum(results[:i+1]) / (i+1) * 100 for i in range(len(results))]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(1, len(cumulative)+1)),
        y=cumulative,
        mode="lines+markers",
        line=dict(color="#c84b31", width=2),
        marker=dict(size=5, color=[("#22c55e" if r else "#ef4444") for r in results]),
        fill="tozeroy",
        fillcolor="rgba(200,75,49,0.08)",
        hovertemplate="Match %{x}: %{y:.1f}%<extra></extra>",
    ))
    fig.add_hline(y=50, line_dash="dot", line_color="#374151", line_width=1)
    fig.update_layout(
        title=dict(text="Cumulative Win Rate", font=dict(color="#9ca3af", size=13), x=0),
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font_color="#9ca3af",
        height=220,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(gridcolor="#1f2937", title="Match #", tickfont=dict(size=10)),
        yaxis=dict(gridcolor="#1f2937", title="%", range=[0, 100], tickfont=dict(size=10)),
    )
    return fig


def render_footer():
    st.markdown("""
    <div class="footer">
        Built by <strong>Sameer Bhalerao</strong> · Senior Analytics & AI Product Leader · Amazon L6<br>
        Part of the <a href="https://soulspark.me" target="_blank">Soul Spark</a> portfolio ·
        Data from <a href="https://www.opendota.com" target="_blank">OpenDota API</a> ·
        <a href="https://github.com/sameervb/dota-analyzer" target="_blank">GitHub</a>
    </div>
    """, unsafe_allow_html=True)


def render_followup_chat(session_key: str, context: str, system_prompt: str):
    """Renders a multi-turn follow-up chat component."""
    history_key = f"{session_key}_history"
    if history_key not in st.session_state:
        st.session_state[history_key] = []

    history = st.session_state[history_key]

    if history:
        section_header("Follow-up Questions", "💬")
        for msg in history:
            role = msg["role"]
            with st.chat_message(role, avatar="🎮" if role == "assistant" else "👤"):
                st.markdown(msg["content"])

    user_q = st.chat_input("Ask a follow-up question about this analysis...", key=f"chat_{session_key}")
    if user_q:
        if not _get_ollama_url():
            _ai_unavailable_msg()
            return
        history.append({"role": "user", "content": user_q})
        messages_payload = [{"role": "system", "content": system_prompt}]
        messages_payload.append({"role": "user", "content": f"Context:\n{context}"})
        for h in history:
            messages_payload.append(h)
        base_url = _get_ollama_url()
        try:
            resp = requests.post(
                f"{base_url.rstrip('/')}/api/chat",
                json={"model": _get_ollama_model(), "messages": messages_payload, "stream": False,
                      "options": {"num_predict": 600}},
                timeout=90,
            )
            answer = resp.json().get("message", {}).get("content", "").strip() if resp.ok else "Error reaching AI."
        except Exception as e:
            answer = f"Error: {e}"
        history.append({"role": "assistant", "content": answer})
        st.session_state[history_key] = history
        st.rerun()


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:20px 0 12px">
        <div style="font-size:2.5rem">🎮</div>
        <div style="font-size:1.2rem;font-weight:700;color:#f9fafb;margin-top:4px">Dota 2 Analyzer</div>
        <div style="font-size:0.75rem;color:#6b7280;margin-top:2px">Powered by OpenDota API</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    st.markdown("**Search Player**")
    _search_query = st.text_input("Player name", placeholder="e.g. Miracle-", label_visibility="collapsed")
    if _search_query:
        with st.spinner("Searching..."):
            _results = search_opendota_players(_search_query)
        if _results:
            _options = {f"{r.get('personaname', 'Unknown')} ({r.get('account_id')})": r.get("account_id") for r in _results[:10]}
            _selected = st.selectbox("Select", list(_options.keys()), label_visibility="collapsed")
            if st.button("Load player", use_container_width=True, type="primary"):
                st.session_state["account_id"] = str(_options[_selected])
                for k in ["dota_match_data", "dota_draft_analysis", "dota_analysis", "dota_draft_rec"]:
                    st.session_state.pop(k, None)
                st.rerun()
        else:
            st.caption("No players found.")

    st.markdown("**Or enter Account ID**")
    _account_id_input = st.text_input("Steam Account ID", value=st.session_state.get("account_id", ""),
                                       placeholder="e.g. 87278757", label_visibility="collapsed")
    if st.button("Load", use_container_width=True, type="primary", key="load_id"):
        if _account_id_input.strip():
            st.session_state["account_id"] = _account_id_input.strip()
            for k in ["dota_match_data", "dota_draft_analysis", "dota_analysis", "dota_draft_rec"]:
                st.session_state.pop(k, None)
            st.rerun()

    st.divider()
    _ai_available = bool(_get_ollama_url())
    if _ai_available:
        st.markdown('<div style="background:#0f2818;border:1px solid #166534;border-radius:8px;padding:10px 14px;color:#86efac;font-size:0.82rem">🟢 &nbsp;AI analysis online</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="background:#1a1a2e;border:1px solid #374151;border-radius:8px;padding:10px 14px;color:#6b7280;font-size:0.82rem">🔵 &nbsp;AI offline — set OLLAMA_BASE_URL in secrets</div>', unsafe_allow_html=True)

    st.markdown("")
    st.caption("No login required · Data from OpenDota")


# ── Load core data ─────────────────────────────────────────────────────────────
account_id = st.session_state.get("account_id")

with st.spinner("Loading hero data..."):
    hero_map = get_opendota_hero_map()
    hero_stats = get_opendota_hero_stats()
hero_names_sorted = sorted([h["name"] for h in hero_map.values() if h.get("name")], key=lambda x: x.lower())

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab_overview, tab_matches, tab_analyzer, tab_draft, tab_about = st.tabs([
    "📊 Overview", "🕹️ Match History", "🔍 Match Analyzer", "⚔️ Draft Simulator", "ℹ️ About"
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Overview
# ══════════════════════════════════════════════════════════════════════════════
with tab_overview:
    if not account_id:
        st.markdown("""
        <div style="text-align:center;padding:60px 20px">
            <div style="font-size:4rem;margin-bottom:16px">🎮</div>
            <h2 style="color:#f9fafb;font-size:1.5rem;margin-bottom:8px">Welcome to Dota 2 Analyzer</h2>
            <p style="color:#6b7280;max-width:420px;margin:0 auto 24px">
                Enter a Steam Account ID or search by player name in the sidebar to get started.
            </p>
            <div style="color:#4b5563;font-size:0.85rem;line-height:2">
                📊 Player stats & win rate<br>
                🕹️ Last 20 matches with KDA and outcomes<br>
                🔍 Deep match analysis with gold & XP charts<br>
                ⚔️ AI-powered draft simulator
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        with st.spinner("Loading player data..."):
            player_data = get_opendota_player(account_id)
            wl_data = get_opendota_win_loss(account_id)
            recent = get_opendota_recent_matches(account_id, limit=20)

        profile = player_data.get("profile") or {}
        name = profile.get("personaname") or f"Player {account_id}"
        avatar = profile.get("avatarfull") or profile.get("avatar")

        # ── Player header ──
        col_av, col_info = st.columns([1, 6])
        with col_av:
            if avatar:
                st.image(avatar, width=72)
            else:
                st.markdown('<div style="width:72px;height:72px;background:#1f2937;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:2rem">👤</div>', unsafe_allow_html=True)
        with col_info:
            st.markdown(f"<h1 style='color:#f9fafb;font-size:1.8rem;margin:0'>{name}</h1>", unsafe_allow_html=True)
            st.markdown(f"<span style='color:#6b7280;font-size:0.85rem'>Account ID: {account_id}</span>", unsafe_allow_html=True)

        st.markdown("")

        # ── KPI Cards ──
        wins = wl_data.get("win", 0)
        losses = wl_data.get("lose", 0)
        total = wins + losses
        win_rate = (wins / total * 100) if total > 0 else 0
        wr_color = "#22c55e" if win_rate >= 52 else "#f59e0b" if win_rate >= 48 else "#ef4444"

        hero_counts: dict = {}
        kills_list, deaths_list, assists_list, gpms_list = [], [], [], []
        recent_wins = 0
        for m in (recent or []):
            hid = m.get("hero_id")
            if hid:
                hname = get_hero_name(hero_map, hid)
                hero_counts[hname] = hero_counts.get(hname, 0) + 1
            kills_list.append(m.get("kills", 0))
            deaths_list.append(m.get("deaths", 0))
            assists_list.append(m.get("assists", 0))
            gpms_list.append(m.get("gold_per_min", 0))
            slot = m.get("player_slot", 0)
            is_radiant = slot < 128
            if (is_radiant and m.get("radiant_win")) or (not is_radiant and not m.get("radiant_win")):
                recent_wins += 1

        top_hero = max(hero_counts.items(), key=lambda x: x[1]) if hero_counts else ("—", 0)
        recent_wr = (recent_wins / len(recent) * 100) if recent else 0
        recent_wr_color = "#22c55e" if recent_wr >= 52 else "#f59e0b" if recent_wr >= 48 else "#ef4444"

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            kpi_card("Total Games", str(total), f"{wins}W · {losses}L")
        with c2:
            kpi_card("Win Rate", f"{win_rate:.1f}%", "All time", color=wr_color)
        with c3:
            kpi_card("Recent Form", f"{recent_wr:.0f}%", "Last 20 matches", color=recent_wr_color)
        with c4:
            avg_kda = f"{sum(kills_list)/len(kills_list):.1f}/{sum(deaths_list)/len(deaths_list):.1f}/{sum(assists_list)/len(assists_list):.1f}" if kills_list else "—"
            kpi_card("Avg K/D/A", avg_kda, "Last 20 matches")
        with c5:
            avg_gpm = f"{sum(gpms_list)/len(gpms_list):.0f}" if gpms_list else "—"
            kpi_card("Avg GPM", avg_gpm, f"Most played: {top_hero[0]}")

        st.markdown("")

        # ── Most played heroes ──
        if hero_counts:
            section_header("Most Played Heroes", "🦸")
            top_heroes = sorted(hero_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            hero_html = ""
            for hname, count in top_heroes:
                # Try to get hero icon
                hid = next((hid for hid, h in hero_map.items() if h.get("name") == hname), None)
                icon_url = get_hero_image(hero_map, hid, "icon") if hid else None
                img_tag = f'<img src="{icon_url}" width="22" height="22" style="border-radius:4px">' if icon_url else "🧙"
                hero_html += f'<span class="hero-chip">{img_tag} {hname} <strong style="color:#c84b31">×{count}</strong></span>'
            st.markdown(hero_html, unsafe_allow_html=True)

        # ── Charts ──
        if recent:
            st.markdown("")
            col_chart1, col_chart2 = st.columns(2)
            with col_chart1:
                section_header("Cumulative Win Rate Trend", "📈")
                st.plotly_chart(make_cumulative_winrate_chart(recent, hero_map), use_container_width=True)
            with col_chart2:
                section_header("Recent Hero Distribution", "🎯")
                df_heroes = pd.DataFrame(top_heroes, columns=["Hero", "Games"])
                fig_bar = px.bar(df_heroes.head(8), x="Games", y="Hero", orientation="h",
                                  color="Games", color_continuous_scale=["#374151", "#c84b31"])
                fig_bar.update_layout(paper_bgcolor="#111827", plot_bgcolor="#111827",
                                       font_color="#9ca3af", showlegend=False,
                                       coloraxis_showscale=False, height=220,
                                       margin=dict(l=0, r=10, t=10, b=10),
                                       yaxis=dict(tickfont=dict(size=11)),
                                       xaxis=dict(gridcolor="#1f2937"))
                st.plotly_chart(fig_bar, use_container_width=True)

        # ── AI Performance Summary ──
        section_header("AI Performance Summary", "✨")
        if st.button("Generate AI performance analysis", type="primary", key="ai_overview"):
            if not _ai_available:
                _ai_unavailable_msg()
            elif recent:
                context = (
                    f"Player: {name} | Account: {account_id}\n"
                    f"Win rate: {win_rate:.1f}% ({wins}W / {losses}L)\n"
                    f"Recent form (last 20): {recent_wr:.0f}% wins\n"
                    f"Avg KDA: {avg_kda}\n"
                    f"Avg GPM: {avg_gpm}\n"
                    f"Most played heroes: {', '.join(h for h, _ in top_heroes[:6])}\n"
                )
                with st.spinner("Generating analysis..."):
                    result = query_ollama(
                        f"Analyse this Dota 2 player's performance and give specific, actionable insights:\n\n{context}",
                        system="You are an expert Dota 2 coach. Be specific, reference the actual data, and give actionable advice. 4-6 sentences.",
                        max_tokens=400,
                    )
                if result:
                    st.markdown(f'<div style="background:#111827;border:1px solid #374151;border-radius:12px;padding:16px 20px;color:#d1d5db;line-height:1.7">{result}</div>', unsafe_allow_html=True)
                else:
                    st.error("Could not reach Ollama. Check your tunnel.")

    render_footer()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Match History
# ══════════════════════════════════════════════════════════════════════════════
with tab_matches:
    if not account_id:
        st.info("Enter a player in the sidebar to view match history.")
    else:
        with st.spinner("Loading match history..."):
            matches = get_opendota_recent_matches(account_id, limit=20)

        if not matches:
            st.warning("No recent matches found for this player.")
        else:
            section_header(f"Last {len(matches)} Matches", "🕹️")

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
                    "Side": "🟢 Radiant" if is_radiant else "🔴 Dire",
                    "Result": "✅ Win" if won else "❌ Loss",
                    "K/D/A": f"{m.get('kills',0)}/{m.get('deaths',0)}/{m.get('assists',0)}",
                    "GPM": m.get("gold_per_min", 0),
                    "XPM": m.get("xp_per_min", 0),
                    "Duration": f"{duration_min}m",
                    "Match ID": str(m.get("match_id", "")),
                })

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True,
                          column_config={"Match ID": st.column_config.TextColumn(width="medium")})

            # Hero stats breakdown
            section_header("Hero Breakdown", "📊")
            hero_stats_rows = {}
            for i, m in enumerate(matches):
                hname = get_hero_name(hero_map, m.get("hero_id"))
                slot = m.get("player_slot", 0)
                is_radiant = slot < 128
                won = (is_radiant and m.get("radiant_win")) or (not is_radiant and not m.get("radiant_win"))
                if hname not in hero_stats_rows:
                    hero_stats_rows[hname] = {"games": 0, "wins": 0, "kills": 0, "deaths": 0, "assists": 0}
                r = hero_stats_rows[hname]
                r["games"] += 1
                r["wins"] += 1 if won else 0
                r["kills"] += m.get("kills", 0)
                r["deaths"] += m.get("deaths", 0)
                r["assists"] += m.get("assists", 0)

            hero_df_rows = []
            for hname, data in sorted(hero_stats_rows.items(), key=lambda x: -x[1]["games"]):
                g = data["games"]
                wr = data["wins"] / g * 100
                hero_df_rows.append({
                    "Hero": hname,
                    "Games": g,
                    "Win Rate": f"{wr:.0f}%",
                    "Avg K/D/A": f"{data['kills']/g:.1f}/{data['deaths']/g:.1f}/{data['assists']/g:.1f}",
                })

            col_h, col_chart = st.columns([1, 2])
            with col_h:
                st.dataframe(pd.DataFrame(hero_df_rows), use_container_width=True, hide_index=True)
            with col_chart:
                fig_wr = px.bar(
                    pd.DataFrame(hero_df_rows), x="Hero", y=[int(r["Win Rate"].replace("%","")) for r in hero_df_rows],
                    color=[int(r["Win Rate"].replace("%","")) for r in hero_df_rows],
                    color_continuous_scale=["#ef4444", "#f59e0b", "#22c55e"],
                    range_color=[0, 100],
                    labels={"y": "Win Rate %"},
                )
                fig_wr.add_hline(y=50, line_dash="dot", line_color="#374151")
                fig_wr.update_layout(paper_bgcolor="#111827", plot_bgcolor="#111827",
                                      font_color="#9ca3af", coloraxis_showscale=False,
                                      height=280, margin=dict(l=0, r=0, t=10, b=0),
                                      xaxis=dict(tickfont=dict(size=10), gridcolor="#1f2937"))
                st.plotly_chart(fig_wr, use_container_width=True)

            # CSV download
            csv_buf = io.StringIO()
            df.to_csv(csv_buf, index=False)
            st.download_button("⬇️ Download match history CSV", csv_buf.getvalue(),
                                file_name=f"dota_matches_{account_id}.csv", mime="text/csv")

            # Select for analyzer
            st.divider()
            match_ids = [str(m.get("match_id")) for m in matches if m.get("match_id")]
            col_sel, col_go = st.columns([3, 1])
            with col_sel:
                selected = st.selectbox("Open in Match Analyzer →", ["Select a match..."] + match_ids, label_visibility="visible")
            with col_go:
                st.markdown("<div style='margin-top:26px'>", unsafe_allow_html=True)
                if st.button("Open →", type="primary") and selected != "Select a match...":
                    st.session_state["selected_match_id"] = selected
                    st.info(f"Match {selected} queued. Switch to **Match Analyzer** tab.")
                st.markdown("</div>", unsafe_allow_html=True)

    render_footer()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Match Analyzer
# ══════════════════════════════════════════════════════════════════════════════
with tab_analyzer:
    section_header("Match Analyzer", "🔍")

    col_in, col_btn = st.columns([4, 1])
    with col_in:
        _match_id_input = st.text_input("Match ID", value=st.session_state.get("selected_match_id", ""),
                                          placeholder="e.g. 7891234567", label_visibility="visible")
    with col_btn:
        st.markdown("<div style='margin-top:26px'>", unsafe_allow_html=True)
        load_match = st.button("Load Match", type="primary")
        st.markdown("</div>", unsafe_allow_html=True)

    if load_match and _match_id_input.strip():
        st.session_state["selected_match_id"] = _match_id_input.strip()
        st.session_state.pop("dota_match_data", None)
        st.session_state.pop("dota_analysis", None)

    match_id_to_load = st.session_state.get("selected_match_id")

    if match_id_to_load:
        if "dota_match_data" not in st.session_state or st.session_state.get("dota_match_id_loaded") != match_id_to_load:
            with st.spinner(f"Loading match {match_id_to_load}..."):
                match_data = get_opendota_match(match_id_to_load)
            st.session_state["dota_match_data"] = match_data
            st.session_state["dota_match_id_loaded"] = match_id_to_load
        else:
            match_data = st.session_state["dota_match_data"]

        if not match_data or not match_data.get("match_id"):
            st.error("Match not found or not yet parsed by OpenDota. Try requesting a parse at opendota.com first.")
        else:
            duration = match_data.get("duration", 0)
            radiant_win = match_data.get("radiant_win")
            radiant_score = match_data.get("radiant_score", 0)
            dire_score = match_data.get("dire_score", 0)
            start_time = match_data.get("start_time")

            # ── Match header ──
            winner_label = "🟢 Radiant Victory" if radiant_win else "🔴 Dire Victory"
            winner_color = "#22c55e" if radiant_win else "#ef4444"
            date_str = datetime.fromtimestamp(start_time).strftime("%d %b %Y %H:%M") if start_time else ""

            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#111827,#1f2937);border:1px solid #374151;border-radius:16px;padding:20px 24px;margin-bottom:20px">
                <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px">
                    <div>
                        <div style="font-size:1.4rem;font-weight:700;color:{winner_color}">{winner_label}</div>
                        <div style="color:#6b7280;font-size:0.85rem;margin-top:4px">Match {match_id_to_load} · {date_str}</div>
                    </div>
                    <div style="display:flex;gap:32px">
                        <div style="text-align:center">
                            <div style="font-size:1.8rem;font-weight:700;color:#22c55e">{radiant_score}</div>
                            <div style="font-size:0.7rem;color:#6b7280;text-transform:uppercase">Radiant</div>
                        </div>
                        <div style="text-align:center;padding:0 8px">
                            <div style="font-size:1.2rem;font-weight:700;color:#6b7280">{round(duration/60, 1)}m</div>
                            <div style="font-size:0.7rem;color:#6b7280;text-transform:uppercase">Duration</div>
                        </div>
                        <div style="text-align:center">
                            <div style="font-size:1.8rem;font-weight:700;color:#ef4444">{dire_score}</div>
                            <div style="font-size:0.7rem;color:#6b7280;text-transform:uppercase">Dire</div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Draft ──
            picks_bans = match_data.get("picks_bans") or []
            if picks_bans:
                section_header("Draft", "⚔️")
                rp = [get_hero_name(hero_map, pb["hero_id"]) for pb in picks_bans if pb.get("is_pick") and pb.get("team") == 0]
                dp = [get_hero_name(hero_map, pb["hero_id"]) for pb in picks_bans if pb.get("is_pick") and pb.get("team") == 1]
                rb = [get_hero_name(hero_map, pb["hero_id"]) for pb in picks_bans if not pb.get("is_pick") and pb.get("team") == 0]
                db = [get_hero_name(hero_map, pb["hero_id"]) for pb in picks_bans if not pb.get("is_pick") and pb.get("team") == 1]

                col_r, col_d = st.columns(2)
                with col_r:
                    st.markdown('<span class="team-radiant">🟢 Radiant Picks</span>', unsafe_allow_html=True)
                    chips = "".join(f'<span class="hero-chip">🗡️ {h}</span>' for h in rp)
                    st.markdown(chips or "<span style='color:#6b7280'>No picks recorded</span>", unsafe_allow_html=True)
                    if rb:
                        st.markdown('<span style="color:#6b7280;font-size:0.8rem">Bans: ' + ", ".join(rb) + "</span>", unsafe_allow_html=True)
                with col_d:
                    st.markdown('<span class="team-dire">🔴 Dire Picks</span>', unsafe_allow_html=True)
                    chips = "".join(f'<span class="hero-chip">🗡️ {h}</span>' for h in dp)
                    st.markdown(chips or "<span style='color:#6b7280'>No picks recorded</span>", unsafe_allow_html=True)
                    if db:
                        st.markdown('<span style="color:#6b7280;font-size:0.8rem">Bans: ' + ", ".join(db) + "</span>", unsafe_allow_html=True)

            # ── Gold / XP advantage charts ──
            gold_adv = match_data.get("radiant_gold_adv") or []
            xp_adv = match_data.get("radiant_xp_adv") or []
            if gold_adv or xp_adv:
                section_header("Advantage Over Time", "📈")
                col_g, col_x = st.columns(2)
                with col_g:
                    if gold_adv:
                        st.plotly_chart(make_advantage_chart(gold_adv, "Gold Advantage (Radiant +)"), use_container_width=True)
                with col_x:
                    if xp_adv:
                        st.plotly_chart(make_advantage_chart(xp_adv, "XP Advantage (Radiant +)", "#f59e0b", "#7c3aed"), use_container_width=True)

            # ── Player performance table ──
            players = match_data.get("players") or []
            if players:
                section_header("Player Performance", "👥")
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
                        "Net Worth": f"{p.get('net_worth', 0):,}",
                        "Hero Dmg": f"{p.get('hero_damage', 0):,}",
                        "Tower Dmg": f"{p.get('tower_damage', 0):,}",
                        "Last Hits": p.get("last_hits", 0),
                    })
                st.dataframe(pd.DataFrame(player_rows), use_container_width=True, hide_index=True)

                # Download
                csv_buf2 = io.StringIO()
                pd.DataFrame(player_rows).to_csv(csv_buf2, index=False)
                st.download_button("⬇️ Download player stats CSV", csv_buf2.getvalue(),
                                    file_name=f"dota_match_{match_id_to_load}_players.csv", mime="text/csv")

            # ── Teamfight swings ──
            teamfights = match_data.get("teamfights") or []
            if teamfights:
                section_header("Teamfight Swings", "⚔️")
                tf_rows = []
                for tf in teamfights:
                    start_sec = tf.get("start", 0)
                    end_sec = tf.get("end", 0)
                    r_gold = sum(p.get("gold_delta", 0) for p in tf.get("players", []) if p.get("isRadiant"))
                    tf_rows.append({
                        "Minute": f"{start_sec//60:.0f}",
                        "Duration": f"{end_sec - start_sec}s",
                        "Radiant Gold Δ": f"{r_gold:+,}",
                        "Deaths": sum(1 for p in tf.get("players", []) if p.get("deaths", 0) > 0),
                    })
                tf_rows.sort(key=lambda x: abs(int(x["Radiant Gold Δ"].replace(",","").replace("+",""))), reverse=True)
                st.dataframe(pd.DataFrame(tf_rows[:8]), use_container_width=True, hide_index=True)

            # ── AI Analysis ──
            section_header("AI Match Analysis", "🤖")

            col_persp, col_hero = st.columns(2)
            with col_persp:
                perspective = st.selectbox("Perspective", ["Overall (Neutral)", "Radiant", "Dire"], key="match_perspective")
            with col_hero:
                all_heroes_in_match = ["All Heroes"] + [get_hero_name(hero_map, p.get("hero_id")) for p in players if p.get("hero_id")]
                hero_focus = st.selectbox("Hero focus", all_heroes_in_match, key="match_hero_focus")

            if st.button("🤖 Generate AI Match Analysis", type="primary", key="ai_match"):
                if not _ai_available:
                    _ai_unavailable_msg()
                else:
                    ctx = build_dota_match_context(match_data, hero_map)
                    hero_section = f"\n\nHERO FOCUS: Provide detailed analysis of {hero_focus}'s performance including mistakes, missed opportunities, and specific improvement advice." if hero_focus != "All Heroes" else ""
                    system = """You are an expert Dota 2 analyst. IMPORTANT: Begin with 2-3 sentences of dramatic fantasy lore narrative describing the clash between the heroes, referencing actual Dota 2 lore. Then add --- and provide your analysis.

Required sections:
1. Match Overview (winner, tempo, key advantage shifts)
2. Draft Analysis (compositions, win conditions, lane matchups)
3. Early Game (0-15min): laning, first blood, objective trades
4. Mid Game (15-30min): teamfights, momentum shifts, key items
5. Late Game (30min+): high-ground attempts, game-ending plays
6. 3-5 Critical Moments with timestamps
7. Key Lessons — 3 actionable takeaways"""
                    with st.spinner("Generating analysis... this may take 30-60 seconds"):
                        result = query_ollama(
                            f"Analyse this Dota 2 match from {perspective} perspective:{hero_section}\n\n{ctx}",
                            system=system,
                            max_tokens=1500,
                        )
                    if result:
                        parts = result.split("---", 1)
                        if len(parts) == 2:
                            st.markdown(f'<div class="lore-box">✨ {parts[0].strip()}</div>', unsafe_allow_html=True)
                            st.markdown(parts[1].strip())
                        else:
                            st.markdown(result)
                        st.session_state["dota_analysis"] = result
                        st.session_state["dota_analysis_ctx"] = build_dota_match_context(match_data, hero_map)

                        # Download
                        report = f"# Dota 2 Match Analysis\n**Match ID:** {match_id_to_load}\n**Perspective:** {perspective}\n\n{result}"
                        st.download_button("⬇️ Download analysis report", report,
                                            file_name=f"dota_analysis_{match_id_to_load}.md", mime="text/markdown")
                    else:
                        st.error("Could not reach Ollama. Check your tunnel.")

            # ── Follow-up chat ──
            if st.session_state.get("dota_analysis"):
                render_followup_chat(
                    "match_analysis",
                    st.session_state.get("dota_analysis_ctx", ""),
                    "You are an expert Dota 2 analyst. Answer follow-up questions specifically and concisely, referencing match data where relevant."
                )

    render_footer()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Draft Simulator
# ══════════════════════════════════════════════════════════════════════════════
with tab_draft:
    section_header("Draft Simulator", "⚔️")
    st.caption("Build a draft and get AI-powered strategy recommendations for both teams.")

    hero_options = ["Select Hero"] + hero_names_sorted
    positions = ["Pos 1 · Carry", "Pos 2 · Mid", "Pos 3 · Offlane", "Pos 4 · Support", "Pos 5 · Hard Support"]

    # Init draft state
    if "draft_radiant" not in st.session_state:
        st.session_state["draft_radiant"] = [None] * 5
    if "draft_dire" not in st.session_state:
        st.session_state["draft_dire"] = [None] * 5

    col_r, col_vs, col_d = st.columns([5, 1, 5])

    with col_r:
        st.markdown('<div class="team-radiant" style="margin-bottom:12px">🟢 RADIANT</div>', unsafe_allow_html=True)
        radiant_picks = []
        for i in range(5):
            current = st.session_state["draft_radiant"][i]
            default_idx = hero_options.index(current) if current and current in hero_options else 0
            st.markdown(f'<div class="pos-label">{positions[i]}</div>', unsafe_allow_html=True)
            h = st.selectbox("", hero_options, index=default_idx, key=f"draft_r_{i}", label_visibility="collapsed")
            radiant_picks.append(None if h == "Select Hero" else h)

    with col_vs:
        st.markdown('<div style="height:80px"></div>', unsafe_allow_html=True)
        st.markdown('<div class="vs-badge">VS</div>', unsafe_allow_html=True)

    with col_d:
        st.markdown('<div class="team-dire" style="margin-bottom:12px">🔴 DIRE</div>', unsafe_allow_html=True)
        dire_picks = []
        for i in range(5):
            current = st.session_state["draft_dire"][i]
            default_idx = hero_options.index(current) if current and current in hero_options else 0
            st.markdown(f'<div class="pos-label">{positions[i]}</div>', unsafe_allow_html=True)
            h = st.selectbox("", hero_options, index=default_idx, key=f"draft_d_{i}", label_visibility="collapsed")
            dire_picks.append(None if h == "Select Hero" else h)

    st.markdown("")
    btn1, btn2, btn3 = st.columns(3)
    with btn1:
        if st.button("🎲 Random Draft", use_container_width=True):
            with st.spinner("Generating draft..."):
                rand_r, rand_d = generate_random_draft(
                    hero_names_sorted, hero_stats,
                    existing_radiant=radiant_picks,
                    existing_dire=dire_picks,
                )
            st.session_state["draft_radiant"] = rand_r
            st.session_state["draft_dire"] = rand_d
            st.session_state.pop("dota_draft_rec", None)
            st.rerun()
    with btn2:
        if st.button("🔄 Reset Draft", use_container_width=True):
            st.session_state["draft_radiant"] = [None] * 5
            st.session_state["draft_dire"] = [None] * 5
            st.session_state.pop("dota_draft_rec", None)
            st.rerun()
    with btn3:
        get_strategy = st.button("✨ Get AI Strategy", use_container_width=True, type="primary")

    active_r = [h for h in radiant_picks if h]
    active_d = [h for h in dire_picks if h]

    if get_strategy:
        if not active_r and not active_d:
            st.warning("Pick at least one hero to get strategy recommendations.")
        elif not _ai_available:
            _ai_unavailable_msg()
        else:
            draft_ctx = f"Radiant: {', '.join(active_r) or 'TBD'}\nDire: {', '.join(active_d) or 'TBD'}"
            system = """You are a Dota 2 draft expert. IMPORTANT: Begin with 1-2 sentences of dramatic fantasy lore narrative describing the coming clash between these heroes, incorporating actual Dota 2 lore and character relationships. Then add --- and provide your analysis.

Then for each team cover:
- Win condition and team strategy
- Power spike timing
- Lane matchup advantages
- Key item priorities
- What to watch out for from the enemy draft

Be specific, practical, and reference the actual heroes picked."""
            with st.spinner("Analysing draft... this may take 20-40 seconds"):
                result = query_ollama(
                    f"Analyse this Dota 2 draft and give strategy recommendations:\n\n{draft_ctx}",
                    system=system,
                    max_tokens=800,
                )
            if result:
                st.session_state["dota_draft_rec"] = result
                st.session_state["dota_draft_ctx"] = draft_ctx
            else:
                st.error("Could not reach Ollama. Check your tunnel.")

    # ── Draft result display ──
    if st.session_state.get("dota_draft_rec"):
        st.divider()
        result = st.session_state["dota_draft_rec"]
        parts = result.split("---", 1)
        if len(parts) == 2:
            st.markdown(f'<div class="lore-box">✨ {parts[0].strip()}</div>', unsafe_allow_html=True)
            col_r2, col_d2 = st.columns(2)
            analysis_text = parts[1].strip()
            # Try to split by team sections
            if "Radiant" in analysis_text and "Dire" in analysis_text:
                mid = analysis_text.find("Dire")
                with col_r2:
                    st.markdown("#### 🟢 Radiant Strategy")
                    st.markdown(analysis_text[:mid].strip())
                with col_d2:
                    st.markdown("#### 🔴 Dire Strategy")
                    st.markdown(analysis_text[mid:].strip())
            else:
                st.markdown(analysis_text)
        else:
            st.markdown(result)

        # Download
        report = f"# Dota 2 Draft Analysis\nRadiant: {', '.join(active_r)}\nDire: {', '.join(active_d)}\n\n{result}"
        st.download_button("⬇️ Download draft analysis", report,
                            file_name="dota_draft_analysis.md", mime="text/markdown")

        # Follow-up chat
        render_followup_chat(
            "draft",
            st.session_state.get("dota_draft_ctx", ""),
            "You are an expert Dota 2 draft analyst. Answer follow-up questions about this specific draft — counter picks, item builds, lane assignments, timing windows."
        )

    render_footer()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — About
# ══════════════════════════════════════════════════════════════════════════════
with tab_about:
    st.markdown("""
    <div style="max-width:700px;margin:0 auto;padding:20px 0">

    <div style="text-align:center;margin-bottom:40px">
        <div style="font-size:3.5rem;margin-bottom:12px">🎮</div>
        <h1 style="color:#f9fafb;font-size:2rem;margin:0">Dota 2 Analyzer</h1>
        <p style="color:#6b7280;margin-top:8px">A public portfolio project by Sameer Bhalerao</p>
    </div>

    <div style="background:#111827;border:1px solid #374151;border-radius:16px;padding:24px;margin-bottom:20px">
        <h3 style="color:#f9fafb;margin-top:0">What this does</h3>
        <p style="color:#9ca3af;line-height:1.7">
        This app lets you explore any Dota 2 player's stats, match history, and get AI-powered analysis
        of matches and drafts — all without any login or account required. Data comes from the public
        OpenDota API. AI analysis uses a local Ollama instance via Cloudflare Tunnel.
        </p>
        <ul style="color:#9ca3af;line-height:2">
            <li><strong style="color:#d1d5db">Player Overview</strong> — Win rate, KDA trends, most played heroes</li>
            <li><strong style="color:#d1d5db">Match History</strong> — Last 20 matches with hero breakdown and win rate chart</li>
            <li><strong style="color:#d1d5db">Match Analyzer</strong> — Gold & XP advantage charts, teamfight swings, player stats, AI analysis with lore narrative</li>
            <li><strong style="color:#d1d5db">Draft Simulator</strong> — Build any draft, get weighted random fills, AI strategy per team</li>
        </ul>
    </div>

    <div style="background:#111827;border:1px solid #374151;border-radius:16px;padding:24px;margin-bottom:20px">
        <h3 style="color:#f9fafb;margin-top:0">Built by</h3>
        <div style="display:flex;align-items:center;gap:16px">
            <div style="font-size:2.5rem">👨‍💻</div>
            <div>
                <div style="color:#f9fafb;font-weight:600;font-size:1.05rem">Sameer Bhalerao</div>
                <div style="color:#6b7280;font-size:0.9rem">Senior Analytics & AI Product Leader · Amazon L6</div>
                <div style="color:#6b7280;font-size:0.85rem;margin-top:4px">
                    <a href="https://www.linkedin.com/in/sameervb" target="_blank" style="color:#c84b31">LinkedIn</a> ·
                    <a href="https://github.com/sameervb" target="_blank" style="color:#c84b31">GitHub</a> ·
                    <a href="https://soulspark.me" target="_blank" style="color:#c84b31">Soul Spark</a>
                </div>
            </div>
        </div>
        <p style="color:#9ca3af;line-height:1.7;margin-top:16px">
        This is one of 10 standalone public apps extracted from
        <a href="https://soulspark.me" style="color:#c84b31">Soul Spark</a> — a local-first personal
        intelligence platform I built end-to-end in 8 weeks. Each app demonstrates a specific module
        of the larger system as a public portfolio showcase.
        </p>
    </div>

    <div style="background:#111827;border:1px solid #374151;border-radius:16px;padding:24px;margin-bottom:20px">
        <h3 style="color:#f9fafb;margin-top:0">Tech Stack</h3>
        <div style="display:flex;flex-wrap:wrap;gap:10px">
    """, unsafe_allow_html=True)

    for badge in ["Streamlit", "Python", "OpenDota API", "Plotly", "Ollama (LLaMA 3.1)", "Cloudflare Tunnel", "Streamlit Cloud"]:
        st.markdown(f'<span style="background:#1f2937;border:1px solid #374151;border-radius:20px;padding:6px 14px;color:#d1d5db;font-size:0.8rem">{badge}</span>', unsafe_allow_html=True)

    st.markdown("""
        </div>
    </div>

    <div style="background:#111827;border:1px solid #374151;border-radius:16px;padding:24px">
        <h3 style="color:#f9fafb;margin-top:0">Privacy</h3>
        <p style="color:#9ca3af;line-height:1.7">
        No data is stored. No login required. All player data is fetched in real-time from the public
        OpenDota API using the account ID you provide. AI analysis is processed by a local Ollama
        instance — no data is sent to OpenAI or any commercial AI provider.
        </p>
    </div>

    </div>
    """, unsafe_allow_html=True)

    render_footer()
