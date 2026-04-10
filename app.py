"""
Dota 2 Analyzer — Full Creative Redesign
Per-tab visual design, hero artwork backgrounds, custom HTML tables.
"""
from __future__ import annotations

import os, io, base64, json, time
import streamlit.components.v1 as components
from datetime import datetime
from pathlib import Path

import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from services.dota import (
    get_opendota_hero_map, get_opendota_hero_stats,
    get_opendota_player, get_opendota_recent_matches,
    get_opendota_win_loss, get_opendota_match,
    search_opendota_players, build_dota_match_context,
    generate_random_draft, get_hero_name, get_hero_image,
    get_opendota_player_heroes, get_opendota_peers,
    get_opendota_totals, get_opendota_wardmap,
    get_opendota_wordcloud, get_opendota_rankings,
    get_opendota_matches,
    build_heroes_context, build_peers_context,
    build_totals_context, build_behavior_context,
)

st.set_page_config(page_title="Dota 2 Analyzer", page_icon="🎮", layout="wide",
                   initial_sidebar_state="expanded")

# ── Asset loader ───────────────────────────────────────────────────────────────
def _b64(filename: str) -> str:
    p = Path(__file__).parent / "assets" / filename
    if p.exists():
        ext = p.suffix.lstrip(".")
        mime = {"jpg":"jpeg","jpeg":"jpeg","png":"png","webp":"webp","avif":"avif"}.get(ext,"jpeg")
        return f"data:image/{mime};base64," + base64.b64encode(p.read_bytes()).decode()
    return ""

@st.cache_data(show_spinner=False)
def load_assets():
    return {
        "heroes":  _b64("69a9ba48c4d63__940x492.webp"),
        "cover":   _b64("large_cover.original.jpg"),
        "logo":    _b64("dota-2-logo.jpg"),
        "muerta":  _b64("Dota_2___Muerta_0_35_screenshot.avif"),
    }

IMG = load_assets()

heroes_bg = f"url('{IMG['heroes']}')" if IMG["heroes"] else "none"
cover_bg  = f"url('{IMG['cover']}')"  if IMG["cover"]  else "none"
logo_bg   = f"url('{IMG['logo']}')"   if IMG["logo"]   else "none"
muerta_bg = f"url('{IMG['muerta']}')" if IMG["muerta"] else "none"

def inject_tab_bg_switcher(tab_imgs: list):
    """Inject JS that swaps full-screen app background per active tab.
    tab_imgs: list of raw data-URI strings (one per tab, in order).
    Uses a stacked gradient overlay to keep text readable.
    """
    imgs_js = json.dumps(tab_imgs)
    components.html(f"""
    <script>
    (function() {{
      var IMGS = {imgs_js};
      var OVERLAY = 'linear-gradient(rgba(8,12,20,0.76), rgba(8,12,20,0.76))';
      function applyBg(idx) {{
        var app = window.parent.document.querySelector('[data-testid="stAppViewContainer"]');
        if (!app) return;
        var img = IMGS[idx] || '';
        if (img) {{
          app.style.backgroundImage = OVERLAY + ", url('" + img + "')";
          app.style.backgroundSize = 'cover';
          app.style.backgroundPosition = 'center top';
          app.style.backgroundAttachment = 'fixed';
          app.style.backgroundRepeat = 'no-repeat';
        }}
      }}
      function setupObserver() {{
        var tabList = window.parent.document.querySelector('[data-baseweb="tab-list"]');
        if (!tabList) {{ setTimeout(setupObserver, 250); return; }}
        function syncActive() {{
          var tabs = tabList.querySelectorAll('[data-baseweb="tab"]');
          for (var i = 0; i < tabs.length; i++) {{
            if (tabs[i].getAttribute('aria-selected') === 'true') {{ applyBg(i); break; }}
          }}
        }}
        syncActive();
        new MutationObserver(syncActive).observe(tabList, {{
          attributes: true, subtree: true, attributeFilter: ['aria-selected']
        }});
      }}
      setupObserver();
    }})();
    </script>
    """, height=0, scrolling=False)

# ── Global CSS ─────────────────────────────────────────────────────────────────

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
*, *::before, *::after {{ font-family: 'Inter', sans-serif; box-sizing: border-box; }}

/* ── App shell ── */
[data-testid="stAppViewContainer"] {{
    background: #080c14;
    background-size: cover !important;
    background-position: center top !important;
    background-attachment: fixed !important;
    background-repeat: no-repeat !important;
}}
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg,#0a0e1a 0%,#080c14 100%);
    border-right: 1px solid #1a2236;
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 2px; background: #0d1120; padding: 5px;
    border-radius: 14px; border: 1px solid #1a2236;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent; border-radius: 10px;
    color: #4b5a7a; border: none; padding: 9px 22px;
    font-weight: 600; font-size: 0.82rem; letter-spacing: 0.02em;
    transition: all 0.2s;
}}
.stTabs [aria-selected="true"] {{
    background: linear-gradient(135deg,#c84b31 0%,#8b1a0a 100%) !important;
    color: #fff !important;
    box-shadow: 0 4px 16px rgba(200,75,49,0.45);
}}

/* ── Banner ── */
.tab-banner {{
    border-radius: 20px; overflow: hidden; position: relative;
    margin-bottom: 28px; height: 180px;
    background-size: cover; background-position: center;
    display: flex; align-items: flex-end;
}}
.tab-banner .banner-overlay {{
    position: absolute; inset: 0;
    background: linear-gradient(to right, rgba(8,12,20,0.92) 0%, rgba(8,12,20,0.4) 60%, rgba(8,12,20,0.1) 100%);
}}
.tab-banner .banner-content {{
    position: relative; z-index: 1; padding: 24px 32px;
}}
.tab-banner .banner-title {{
    font-size: 2rem; font-weight: 800; color: #f1f5f9; line-height: 1;
    text-shadow: 0 2px 12px rgba(0,0,0,0.8);
}}
.tab-banner .banner-sub {{
    font-size: 0.85rem; color: #94a3b8; margin-top: 6px;
}}

/* ── KPI cards ── */
.kpi-grid {{ display: grid; gap: 14px; margin-bottom: 24px; }}
.kpi-card {{
    background: linear-gradient(135deg,#0f1825 0%,#131d2e 100%);
    border: 1px solid #1e2d42; border-radius: 18px;
    padding: 22px 20px 18px; position: relative; overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s;
}}
.kpi-card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 32px rgba(0,0,0,0.4); }}
.kpi-card .accent-bar {{
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    border-radius: 18px 18px 0 0;
}}
.kpi-card .kpi-icon {{ font-size: 1.4rem; margin-bottom: 8px; }}
.kpi-card .kpi-val {{
    font-size: 2rem; font-weight: 800; color: #f1f5f9; line-height: 1.1;
}}
.kpi-card .kpi-lbl {{
    font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em;
    color: #4b5a7a; font-weight: 600; margin-top: 4px;
}}
.kpi-card .kpi-sub {{ font-size: 0.78rem; color: #64748b; margin-top: 6px; }}

/* ── Section headers ── */
.sec-hdr {{
    display: flex; align-items: center; gap: 12px;
    margin: 32px 0 18px;
}}
.sec-hdr .sec-title {{
    font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.12em; color: #94a3b8; white-space: nowrap;
}}
.sec-hdr .sec-line {{
    flex: 1; height: 1px;
    background: linear-gradient(90deg, #1e2d42, transparent);
}}

/* ── Match history cards ── */
.match-card {{
    background: linear-gradient(135deg,#0d1520 0%,#111d2e 100%);
    border: 1px solid #1a2840; border-radius: 14px;
    padding: 14px 18px; margin-bottom: 8px;
    display: grid;
    grid-template-columns: 48px 1fr auto auto auto auto auto;
    align-items: center; gap: 16px;
    transition: border-color 0.2s, background 0.2s;
}}
.match-card:hover {{
    border-color: #2a3d5a;
    background: linear-gradient(135deg,#0f1a28 0%,#14223a 100%);
}}
.match-card.win {{ border-left: 4px solid #22c55e; }}
.match-card.loss {{ border-left: 4px solid #ef4444; }}
.match-result-win {{
    background: rgba(34,197,94,0.15); color: #86efac;
    border: 1px solid rgba(34,197,94,0.3);
    border-radius: 20px; padding: 3px 10px;
    font-size: 0.72rem; font-weight: 700; white-space: nowrap;
}}
.match-result-loss {{
    background: rgba(239,68,68,0.15); color: #fca5a5;
    border: 1px solid rgba(239,68,68,0.3);
    border-radius: 20px; padding: 3px 10px;
    font-size: 0.72rem; font-weight: 700; white-space: nowrap;
}}
.match-hero-name {{ font-weight: 700; color: #e2e8f0; font-size: 0.9rem; }}
.match-meta {{ font-size: 0.75rem; color: #4b5a7a; }}
.match-kda {{ font-size: 0.9rem; font-weight: 600; color: #94a3b8; }}
.match-stat {{ text-align: right; }}
.match-stat .val {{ font-size: 0.88rem; font-weight: 600; color: #cbd5e1; }}
.match-stat .lbl {{ font-size: 0.65rem; color: #4b5a7a; text-transform: uppercase; }}
.match-id-link {{ font-size: 0.7rem; color: #334155; font-family: monospace; }}

/* ── Hero breakdown cards ── */
.hero-breakdown-card {{
    background: linear-gradient(135deg,#0d1520,#111d2e);
    border: 1px solid #1a2840; border-radius: 12px;
    padding: 12px 16px; margin-bottom: 8px;
    display: grid; grid-template-columns: 1fr 60px 80px 1fr;
    align-items: center; gap: 12px;
}}
.hb-hero {{ font-weight: 700; color: #e2e8f0; font-size: 0.88rem; }}
.hb-games {{ font-size: 0.82rem; color: #64748b; text-align: center; }}
.hb-wr {{ font-weight: 800; font-size: 0.95rem; text-align: center; }}
.hb-wr.good {{ color: #22c55e; }}
.hb-wr.mid  {{ color: #f59e0b; }}
.hb-wr.bad  {{ color: #ef4444; }}
.hb-bar-wrap {{
    background: #1a2840; border-radius: 20px; height: 8px;
    overflow: hidden;
}}
.hb-bar-fill {{ height: 100%; border-radius: 20px; transition: width 0.6s; }}

/* ── Player performance table ── */
.perf-table {{ width: 100%; border-collapse: collapse; }}
.perf-table th {{
    background: #0a1020; color: #4b5a7a; font-size: 0.65rem;
    text-transform: uppercase; letter-spacing: 0.1em;
    padding: 10px 14px; border-bottom: 1px solid #1a2840;
    font-weight: 700; text-align: left;
}}
.perf-table td {{
    padding: 11px 14px; border-bottom: 1px solid #0d1520;
    font-size: 0.83rem; color: #94a3b8;
}}
.perf-table tr:hover td {{ background: rgba(255,255,255,0.02); }}
.perf-table tr.radiant-row td:first-child {{ border-left: 3px solid #22c55e; }}
.perf-table tr.dire-row td:first-child {{ border-left: 3px solid #ef4444; }}
.perf-table .hero-cell {{ font-weight: 700; color: #e2e8f0; }}
.perf-table .num {{ text-align: right; font-variant-numeric: tabular-nums; }}
.kda-pos {{ color: #86efac; }}
.kda-neg {{ color: #fca5a5; }}

/* ── Teamfight cards ── */
.tf-card {{
    background: linear-gradient(135deg,#0d1520,#111d2e);
    border: 1px solid #1a2840; border-radius: 12px;
    padding: 14px 18px; margin-bottom: 8px;
    display: grid; grid-template-columns: 70px 60px 1fr 1fr;
    align-items: center; gap: 16px;
}}
.tf-min {{ font-size: 1.2rem; font-weight: 800; color: #f1f5f9; }}
.tf-dur {{ font-size: 0.75rem; color: #4b5a7a; }}
.tf-gold-pos {{ color: #22c55e; font-weight: 700; font-size: 1rem; }}
.tf-gold-neg {{ color: #ef4444; font-weight: 700; font-size: 1rem; }}
.tf-bar-wrap {{
    background: #1a2840; border-radius: 4px; height: 6px;
    display: flex; overflow: hidden;
}}

/* ── Draft cards ── */
.draft-team-panel {{
    background: linear-gradient(180deg,#0d1824 0%,#0a1218 100%);
    border: 1px solid #1a2840; border-radius: 20px;
    padding: 20px 16px;
}}
.draft-pick-slot {{
    background: #0a1420; border: 1px solid #1e3050;
    border-radius: 12px; padding: 10px 14px; margin-bottom: 8px;
    display: flex; align-items: center; gap: 10px;
}}
.draft-pos-badge {{
    background: #1a2840; border-radius: 8px;
    padding: 4px 8px; font-size: 0.65rem; font-weight: 700;
    color: #4b5a7a; text-transform: uppercase; letter-spacing: 0.05em;
    white-space: nowrap; min-width: 60px; text-align: center;
}}
.vs-circle {{
    width: 64px; height: 64px; border-radius: 50%;
    background: linear-gradient(135deg,#c84b31,#8b1a0a);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.3rem; font-weight: 900; color: #fff;
    box-shadow: 0 0 32px rgba(200,75,49,0.6), 0 0 64px rgba(200,75,49,0.2);
    margin: auto;
}}

/* ── Lore box ── */
.lore-box {{
    background: linear-gradient(135deg,#130820,#1a1030);
    border: 1px solid #5b21b6; border-left: 4px solid #7c3aed;
    border-radius: 14px; padding: 18px 22px; margin: 16px 0;
    font-style: italic; color: #c4b5fd; line-height: 1.8; font-size: 0.95rem;
}}

/* ── AI output ── */
.ai-output {{
    background: linear-gradient(135deg,#0d1520,#111d2e);
    border: 1px solid #1e2d42; border-radius: 16px;
    padding: 20px 24px; color: #cbd5e1; line-height: 1.8;
}}

/* ── Advantage chart label ── */
.adv-label {{
    font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em;
    font-weight: 700; padding: 4px 10px; border-radius: 20px;
    display: inline-block; margin-bottom: 8px;
}}
.adv-radiant {{ background: rgba(34,197,94,0.15); color: #86efac; }}
.adv-dire {{ background: rgba(239,68,68,0.15); color: #fca5a5; }}

/* ── Hero chip ── */
.hero-chip {{
    display: inline-flex; align-items: center; gap: 6px;
    background: #0f1e30; border: 1px solid #1e3050;
    border-radius: 20px; padding: 4px 12px 4px 6px;
    font-size: 0.78rem; color: #cbd5e1; margin: 3px;
}}

/* ── Footer ── */
.footer {{
    margin-top: 60px; padding: 28px;
    text-align: center; border-top: 1px solid #1a2840;
    color: #334155; font-size: 0.8rem; line-height: 2;
}}
.footer a {{ color: #c84b31; text-decoration: none; }}
.footer strong {{ color: #64748b; }}

/* Streamlit overrides */
.stButton button {{
    border-radius: 12px; font-weight: 600;
    transition: all 0.2s; font-size: 0.85rem;
}}
.stSelectbox > div > div {{
    background: #0d1520 !important; border-color: #1a2840 !important;
    color: #cbd5e1 !important; border-radius: 10px !important;
}}
[data-testid="stTextInput"] input {{
    background: #0d1520 !important; border-color: #1a2840 !important;
    color: #cbd5e1 !important; border-radius: 10px !important;
}}

/* ── Peer cards ── */
.peer-card {{
    background: linear-gradient(135deg,#0d1520,#111d2e);
    border: 1px solid #1a2840; border-radius:14px;
    padding:14px 18px; margin-bottom:8px;
    display:grid; grid-template-columns:44px 1fr auto auto auto;
    align-items:center; gap:16px;
    transition: border-color 0.2s;
}}
.peer-card:hover {{ border-color:#2a3d5a; }}

/* ── Record / stat cards ── */
.record-card {{
    background: linear-gradient(135deg,#0d1520,#111d2e);
    border:1px solid #1a2840; border-radius:14px;
    padding:16px 20px; text-align:center;
}}
.record-val {{
    font-size:1.8rem; font-weight:900; line-height:1.1;
}}
.record-lbl {{
    font-size:0.68rem; text-transform:uppercase;
    letter-spacing:0.1em; color:#4b5a7a; margin-top:4px;
}}
.record-hero {{
    font-size:0.78rem; color:#64748b; margin-top:6px;
}}
</style>
""", unsafe_allow_html=True)


# ── Helpers ─────────────────────────────────────────────────────────────────────
def _get_ollama_url():
    try: return st.secrets.get("OLLAMA_BASE_URL") or os.environ.get("OLLAMA_BASE_URL")
    except: return os.environ.get("OLLAMA_BASE_URL")

def _get_ollama_model():
    override = st.session_state.get("selected_model")
    if override: return override
    try: return st.secrets.get("OLLAMA_MODEL") or os.environ.get("OLLAMA_MODEL","llama3.1")
    except: return os.environ.get("OLLAMA_MODEL","llama3.1")

@st.cache_data(ttl=30, show_spinner=False)
def detect_ollama_models():
    base_url = _get_ollama_url()
    if not base_url: return []
    try:
        r = requests.get(f"{base_url.rstrip('/')}/api/tags", timeout=5)
        if r.ok:
            return sorted(m["name"] for m in r.json().get("models", []))
    except Exception:
        pass
    return []

@st.cache_data(ttl=15, show_spinner=False)
def detect_gpu():
    base_url = _get_ollama_url()
    if not base_url: return None
    try:
        r = requests.get(f"{base_url.rstrip('/')}/api/ps", timeout=5)
        if r.ok:
            models = r.json().get("models", [])
            if not models: return None
            return any(m.get("size_vram", 0) > 0 for m in models)
    except Exception:
        pass
    return None

def _stream_ollama(prompt, system="", max_tokens=1000, temperature=0.70):
    base_url = _get_ollama_url()
    if not base_url:
        yield "⚠️ OLLAMA_BASE_URL not set in Streamlit secrets."
        return
    try:
        msgs = ([{"role":"system","content":system}] if system else []) + [{"role":"user","content":prompt}]
        r = requests.post(f"{base_url.rstrip('/')}/api/chat",
            json={"model":_get_ollama_model(),"messages":msgs,"stream":True,
                  "options":{"num_predict":max_tokens,"temperature":temperature}},
            timeout=120, stream=True)
        if r.ok:
            for line in r.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        token = chunk.get("message", {}).get("content", "")
                        if token:
                            yield token
                        if chunk.get("done"):
                            break
                    except Exception:
                        pass
        else:
            yield f"⚠️ Ollama HTTP {r.status_code}: {r.text[:200]}"
    except requests.Timeout:
        yield "⚠️ **Timeout** — Ollama is still processing. Try a faster model (mistral or phi3:mini)."
    except requests.ConnectionError:
        yield "⚠️ **Cannot reach Ollama.** Check your tunnel URL and restart the Cloudflare tunnel."
    except Exception as e:
        yield f"⚠️ Error: {e}"

def render_ai_output(prompt, system="", lore=True, max_tokens=800, temperature=0.70):
    """Stream Ollama response with elapsed timer, then render styled output. Returns full text."""
    start_t = time.perf_counter()
    status = st.status("⚡ Generating analysis...", expanded=True)
    full_text = ""
    with status:
        full_text = st.write_stream(_stream_ollama(prompt, system, max_tokens, temperature))
        elapsed = time.perf_counter() - start_t
        st.caption(f"Generated in {elapsed:.1f}s · Model: {_get_ollama_model()}")
    status.update(label=f"✅ Done · {elapsed:.1f}s", state="complete", expanded=False)

    if not full_text or full_text.startswith("⚠️"):
        if full_text:
            st.warning(full_text)
        return None

    if lore and "---" in full_text:
        parts = full_text.split("---", 1)
        st.markdown(f'<div class="lore-box">✨ {parts[0].strip()}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ai-output">{parts[1].strip()}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="ai-output">{full_text}</div>', unsafe_allow_html=True)
    return full_text

# Keep non-streaming version for programmatic use (followup chat history)
def query_ollama(prompt, system="", max_tokens=1000, temperature=0.70):
    base_url = _get_ollama_url()
    if not base_url: return None
    try:
        msgs = ([{"role":"system","content":system}] if system else []) + [{"role":"user","content":prompt}]
        r = requests.post(f"{base_url.rstrip('/')}/api/chat",
            json={"model":_get_ollama_model(),"messages":msgs,"stream":False,
                  "options":{"num_predict":max_tokens,"temperature":temperature}}, timeout=120)
        return r.json().get("message",{}).get("content","").strip() if r.ok else None
    except Exception:
        return None

_ai_available = bool(_get_ollama_url())

def _ai_warn():
    st.warning("Set `OLLAMA_BASE_URL` in Streamlit Cloud → Settings → Secrets and start your Cloudflare tunnel.")

def sec(title, icon=""):
    st.markdown(f'<div class="sec-hdr"><span class="sec-title">{icon}&nbsp;{title}</span><div class="sec-line"></div></div>', unsafe_allow_html=True)

def banner(bg_url, title, subtitle, height=180):
    st.markdown(f"""
    <div class="tab-banner" style="background-image:{bg_url};height:{height}px">
        <div class="banner-overlay"></div>
        <div class="banner-content">
            <div class="banner-title">{title}</div>
            <div class="banner-sub">{subtitle}</div>
        </div>
    </div>""", unsafe_allow_html=True)

def kpi(icon, label, value, sub="", color="#c84b31"):
    st.markdown(f"""
    <div class="kpi-card">
        <div class="accent-bar" style="background:linear-gradient(90deg,{color},transparent)"></div>
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-val" style="color:{color}">{value}</div>
        <div class="kpi-lbl">{label}</div>
        {'<div class="kpi-sub">'+sub+'</div>' if sub else ''}
    </div>""", unsafe_allow_html=True)

def adv_chart(data, title, color_pos="#22c55e", color_neg="#ef4444"):
    minutes = list(range(len(data)))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=minutes, y=data, mode="lines",
        line=dict(width=2.5, color=color_pos),
        fill="tozeroy", fillcolor=f"rgba({','.join(str(int(color_pos.lstrip('#')[i:i+2],16)) for i in (0,2,4))},0.12)" if color_pos.startswith('#') else "rgba(34,197,94,0.12)",
        hovertemplate="Min %{x}: %{y:+,}<extra></extra>", showlegend=False))
    # Shade negative regions
    neg_y = [min(0, v) for v in data]
    fig.add_trace(go.Scatter(x=minutes, y=neg_y, mode="none",
        fill="tozeroy", fillcolor="rgba(239,68,68,0.12)", showlegend=False))
    fig.add_hline(y=0, line_dash="dot", line_color="#1e2d42", line_width=1.5)
    fig.update_layout(
        title=dict(text=title, font=dict(color="#64748b", size=12), x=0),
        paper_bgcolor="#0d1520", plot_bgcolor="#0d1520", font_color="#64748b",
        height=200, margin=dict(l=8, r=8, t=36, b=8),
        xaxis=dict(gridcolor="#0f1e30", title="Min", tickfont=dict(size=9), showgrid=True),
        yaxis=dict(gridcolor="#0f1e30", zeroline=False, tickfont=dict(size=9)),
    )
    return fig

def winrate_trend(matches):
    results, cumwr = [], []
    for m in matches:
        slot = m.get("player_slot", 0)
        won = (slot < 128 and m.get("radiant_win")) or (slot >= 128 and not m.get("radiant_win"))
        results.append(won)
        cumwr.append(sum(results) / len(results) * 100)
    colors = ["#22c55e" if r else "#ef4444" for r in results]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(range(1, len(cumwr)+1)), y=cumwr,
        mode="lines+markers",
        line=dict(color="#c84b31", width=2.5),
        marker=dict(size=7, color=colors, line=dict(color="#0d1520", width=1.5)),
        fill="tozeroy", fillcolor="rgba(200,75,49,0.08)",
        hovertemplate="Match %{x}: %{y:.1f}%<extra></extra>",
        showlegend=False))
    fig.add_hline(y=50, line_dash="dot", line_color="#1e2d42", line_width=1.5)
    fig.update_layout(
        title=dict(text="Cumulative Win Rate Trend", font=dict(color="#64748b", size=12), x=0),
        paper_bgcolor="#0d1520", plot_bgcolor="#0d1520", font_color="#64748b",
        height=220, margin=dict(l=8, r=8, t=36, b=8),
        xaxis=dict(gridcolor="#0f1e30", title="Match #", tickfont=dict(size=9)),
        yaxis=dict(gridcolor="#0f1e30", range=[0,100], title="%", tickfont=dict(size=9)),
    )
    return fig

def render_match_cards(matches, hero_map):
    html = ""
    for m in matches:
        hid = m.get("hero_id")
        hname = get_hero_name(hero_map, hid)
        icon_url = get_hero_image(hero_map, hid, "icon")
        slot = m.get("player_slot", 0)
        is_rad = slot < 128
        rw = m.get("radiant_win")
        won = (is_rad and rw) or (not is_rad and not rw)
        dur = round(m.get("duration", 0) / 60, 1)
        start = m.get("start_time")
        date = datetime.fromtimestamp(start).strftime("%d %b") if start else ""
        kda = f"{m.get('kills',0)}/{m.get('deaths',0)}/{m.get('assists',0)}"
        gpm = m.get("gold_per_min", 0)
        xpm = m.get("xp_per_min", 0)
        mid = m.get("match_id", "")
        side_color = "#22c55e" if is_rad else "#ef4444"
        side_label = "Radiant" if is_rad else "Dire"
        result_class = "match-result-win" if won else "match-result-loss"
        result_text = "WIN" if won else "LOSS"
        card_class = "win" if won else "loss"
        img_html = f'<img src="{icon_url}" width="36" height="36" style="border-radius:8px;object-fit:cover">' if icon_url else '<div style="width:36px;height:36px;background:#1a2840;border-radius:8px"></div>'

        html += f"""
        <div class="match-card {card_class}">
            {img_html}
            <div>
                <div class="match-hero-name">{hname}</div>
                <div class="match-meta">{date} &middot; <span style="color:{side_color}">{side_label}</span> &middot; {dur}m</div>
            </div>
            <span class="{result_class}">{result_text}</span>
            <div class="match-stat">
                <div class="val">{kda}</div>
                <div class="lbl">K/D/A</div>
            </div>
            <div class="match-stat">
                <div class="val">{gpm}</div>
                <div class="lbl">GPM</div>
            </div>
            <div class="match-stat">
                <div class="val">{xpm}</div>
                <div class="lbl">XPM</div>
            </div>
            <div class="match-id-link">#{mid}</div>
        </div>"""
    st.markdown(html, unsafe_allow_html=True)

def render_hero_breakdown(hero_stats_rows):
    html = ""
    for hname, d in sorted(hero_stats_rows.items(), key=lambda x: -x[1]["games"]):
        g = d["games"]; wr = d["wins"] / g * 100
        avg_k = d["kills"]/g; avg_d = d["deaths"]/g; avg_a = d["assists"]/g
        wr_class = "good" if wr >= 55 else "mid" if wr >= 45 else "bad"
        bar_color = "#22c55e" if wr >= 55 else "#f59e0b" if wr >= 45 else "#ef4444"
        html += f"""
        <div class="hero-breakdown-card">
            <div class="hb-hero">{hname}</div>
            <div class="hb-games">{g} {'game' if g==1 else 'games'}</div>
            <div class="hb-wr {wr_class}">{wr:.0f}%</div>
            <div>
                <div class="hb-bar-wrap">
                    <div class="hb-bar-fill" style="width:{wr}%;background:{bar_color}"></div>
                </div>
                <div style="font-size:0.7rem;color:#4b5a7a;margin-top:4px">{avg_k:.1f}/{avg_d:.1f}/{avg_a:.1f} avg KDA</div>
            </div>
        </div>"""
    st.markdown(html, unsafe_allow_html=True)

def render_player_table(players, hero_map):
    rows_r = [p for p in players if p.get("isRadiant")]
    rows_d = [p for p in players if not p.get("isRadiant")]
    html = '<table class="perf-table"><thead><tr>'
    for col in ["Hero","Lvl","K/D/A","GPM","XPM","Net Worth","Hero Dmg","Last Hits"]:
        align = "right" if col not in ["Hero"] else "left"
        html += f'<th style="text-align:{align}">{col}</th>'
    html += "</tr></thead><tbody>"
    for side, rows, row_class in [("🟢 Radiant", rows_r, "radiant-row"), ("🔴 Dire", rows_d, "dire-row")]:
        side_color = "#22c55e" if "Radiant" in side else "#ef4444"
        html += f'<tr><td colspan="8" style="background:#0a1020;color:{side_color};font-size:0.7rem;font-weight:700;letter-spacing:0.1em;padding:8px 14px;text-transform:uppercase">{side}</td></tr>'
        for p in rows:
            hname = get_hero_name(hero_map, p.get("hero_id"))
            k,d,a = p.get("kills",0),p.get("deaths",0),p.get("assists",0)
            kda_color = "kda-pos" if k >= d else "kda-neg"
            html += f"""<tr class="{row_class}">
                <td class="hero-cell">{hname}</td>
                <td class="num">{p.get("level",0)}</td>
                <td class="num {kda_color}">{k}/{d}/{a}</td>
                <td class="num">{p.get("gold_per_min",0)}</td>
                <td class="num">{p.get("xp_per_min",0)}</td>
                <td class="num">{p.get("net_worth",0):,}</td>
                <td class="num">{p.get("hero_damage",0):,}</td>
                <td class="num">{p.get("last_hits",0)}</td>
            </tr>"""
    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

def render_teamfight_cards(teamfights):
    tf_rows = []
    for tf in teamfights:
        s, e = tf.get("start",0), tf.get("end",0)
        r_gold = sum(p.get("gold_delta",0) for p in tf.get("players",[]) if p.get("isRadiant"))
        tf_rows.append({"min": s//60, "dur": e-s, "gold": r_gold,
                         "deaths": sum(1 for p in tf.get("players",[]) if p.get("deaths",0)>0)})
    tf_rows.sort(key=lambda x: abs(x["gold"]), reverse=True)
    html = ""
    for i, tf in enumerate(tf_rows[:8]):
        gold_class = "tf-gold-pos" if tf["gold"] >= 0 else "tf-gold-neg"
        gold_str = f"{tf['gold']:+,}"
        advantage = "Radiant" if tf["gold"] >= 0 else "Dire"
        adv_color = "#22c55e" if tf["gold"] >= 0 else "#ef4444"
        bar_pct = min(100, abs(tf["gold"]) / 5000 * 100)
        bar_r = bar_pct if tf["gold"] >= 0 else 0
        bar_d = bar_pct if tf["gold"] < 0 else 0
        html += f"""
        <div class="tf-card">
            <div>
                <div class="tf-min">⚔️ {tf["min"]}m</div>
                <div class="tf-dur">{tf["dur"]}s &middot; {tf["deaths"]} deaths</div>
            </div>
            <div style="text-align:center">
                <div style="font-size:0.65rem;color:#4b5a7a;text-transform:uppercase;margin-bottom:4px">Gold Swing</div>
                <div class="{gold_class}">{gold_str}</div>
            </div>
            <div>
                <div style="font-size:0.65rem;color:{adv_color};margin-bottom:6px">↗ {advantage} advantage</div>
                <div class="tf-bar-wrap">
                    <div style="width:{bar_d}%;background:#ef4444;height:100%;border-radius:4px 0 0 4px"></div>
                    <div style="flex:1"></div>
                    <div style="width:{bar_r}%;background:#22c55e;height:100%;border-radius:0 4px 4px 0"></div>
                </div>
            </div>
            <div style="font-size:0.7rem;color:#334155;text-align:right">Fight #{i+1}</div>
        </div>"""
    st.markdown(html, unsafe_allow_html=True)

def render_followup_chat(session_key, context, system_prompt):
    hk = f"{session_key}_history"
    if hk not in st.session_state: st.session_state[hk] = []
    history = st.session_state[hk]
    if history:
        sec("Follow-up Chat", "💬")
        for msg in history:
            with st.chat_message(msg["role"], avatar="🎮" if msg["role"]=="assistant" else "👤"):
                st.markdown(msg["content"])
    user_q = st.chat_input("Ask a follow-up question...", key=f"chat_{session_key}")
    if user_q:
        if not _ai_available: _ai_warn(); return
        history.append({"role":"user","content":user_q})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_q)
        base_url = _get_ollama_url()
        msgs = [{"role":"system","content":system_prompt},
                {"role":"user","content":f"Context:\n{context}"}] + history
        def _chat_stream():
            try:
                r = requests.post(f"{base_url.rstrip('/')}/api/chat",
                    json={"model":_get_ollama_model(),"messages":msgs,"stream":True,
                          "options":{"num_predict":500,"temperature":0.70}},
                    timeout=90, stream=True)
                if r.ok:
                    for line in r.iter_lines():
                        if line:
                            try:
                                chunk = json.loads(line)
                                token = chunk.get("message",{}).get("content","")
                                if token: yield token
                                if chunk.get("done"): break
                            except Exception: pass
                else:
                    yield f"⚠️ HTTP {r.status_code}"
            except requests.Timeout:
                yield "⚠️ Timeout — try a faster model."
            except Exception as e:
                yield f"⚠️ {e}"
        with st.chat_message("assistant", avatar="🎮"):
            ans = st.write_stream(_chat_stream())
        history.append({"role":"assistant","content":ans})
        st.session_state[hk] = history

def footer():
    st.markdown("""
    <div class="footer">
        Built by <strong>Sameer Bhalerao</strong> · Senior Analytics & AI Product Leader · Amazon L6<br>
        <a href="https://sameerbhalerao.com" target="_blank">sameerbhalerao.com</a> ·
        Part of the <a href="https://soulspark.me" target="_blank">Soul Spark</a> portfolio ·
        Data: <a href="https://www.opendota.com" target="_blank">OpenDota API</a> ·
        <a href="https://github.com/sameervb/dota-analyzer" target="_blank">GitHub</a> ·
        No login required · No data stored
    </div>""", unsafe_allow_html=True)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    if IMG["logo"]:
        st.markdown(f"""
        <div style="border-radius:16px;overflow:hidden;margin-bottom:16px;height:120px;
                    background-image:{logo_bg};background-size:cover;background-position:center">
            <div style="height:100%;background:linear-gradient(to bottom,rgba(8,12,20,0.3),rgba(8,12,20,0.8));
                        display:flex;align-items:flex-end;padding:14px">
                <span style="font-size:0.75rem;font-weight:700;color:#94a3b8;letter-spacing:0.15em;text-transform:uppercase">Dota 2 Analyzer</span>
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div style="text-align:center;font-size:2rem;padding:20px">🎮</div>', unsafe_allow_html=True)

    st.markdown('<div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#334155;margin-bottom:8px">Search Player</div>', unsafe_allow_html=True)
    _sq = st.text_input("", placeholder="e.g. Miracle-", label_visibility="collapsed", key="search_q")
    if _sq:
        with st.spinner("Searching..."):
            _res = search_opendota_players(_sq)
        if _res:
            _opts = {f"{r.get('personaname','Unknown')} ({r.get('account_id')})": r.get("account_id") for r in _res[:10]}
            _sel = st.selectbox("", list(_opts.keys()), label_visibility="collapsed")
            if st.button("Load Player", use_container_width=True, type="primary"):
                st.session_state["account_id"] = str(_opts[_sel])
                for k in ["dota_match_data","dota_analysis","dota_draft_rec"]:
                    st.session_state.pop(k, None)
                st.rerun()
        else:
            st.caption("No players found.")

    st.markdown('<div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;color:#334155;margin:16px 0 8px">Account ID</div>', unsafe_allow_html=True)
    _aid = st.text_input("", value=st.session_state.get("account_id",""),
                          placeholder="e.g. 87278757", label_visibility="collapsed")
    if st.button("Load", use_container_width=True, type="primary", key="load_id"):
        if _aid.strip():
            st.session_state["account_id"] = _aid.strip()
            for k in ["dota_match_data","dota_analysis","dota_draft_rec"]:
                st.session_state.pop(k, None)
            st.rerun()

    st.markdown("---")
    if _ai_available:
        _MODEL_DESC = {
            "phi3:mini":    "⚡ fastest · ~5s",
            "phi3:medium":  "⚡ fast · ~10s",
            "mistral":      "⚖️ balanced · ~15s",
            "mistral:7b":   "⚖️ balanced · ~15s",
            "llama3.1:8b":  "🧠 capable · ~30s",
            "llama3.1:70b": "🧠 most capable · slow",
            "llama3:8b":    "🧠 capable · ~30s",
            "gemma:7b":     "⚖️ balanced · ~20s",
            "gemma2:9b":    "⚖️ balanced · ~20s",
            "qwen2.5:7b":   "⚖️ balanced · ~20s",
        }
        def _model_label(m: str) -> str:
            if m in _MODEL_DESC:
                return f"{m} — {_MODEL_DESC[m]}"
            n = m.lower()
            if any(x in n for x in ["34b","70b","72b","65b","40b"]): hint = "🐘 large · ~2m+"
            elif any(x in n for x in ["13b","14b","20b","30b"]): hint = "🧠 capable · ~1m"
            elif any(x in n for x in ["7b","8b","9b"]): hint = "⚖️ balanced · ~30s"
            elif any(x in n for x in ["3b","4b","6b"]): hint = "⚡ fast · ~15s"
            elif any(x in n for x in ["mini","tiny","small","nano"]): hint = "⚡ fastest · ~5s"
            elif "llava" in n: hint = "👁️ vision · ~30s"
            elif "deepseek" in n: hint = "🔬 reasoning · slow"
            elif "code" in n: hint = "💻 code · ~20s"
            elif any(x in n for x in ["neural","orca","chat"]): hint = "💬 chat · ~20s"
            elif any(x in n for x in ["mistral","llama","gemma","qwen","phi"]): hint = "⚖️ balanced · ~20s"
            else: hint = "🤖 ~20s"
            return f"{m} — {hint}"
        available_models = detect_ollama_models()
        if available_models:
            gpu_status = detect_gpu()
            gpu_label = "🟩 GPU" if gpu_status is True else "🟨 CPU" if gpu_status is False else ""
            st.markdown(f'<div style="background:#081a0f;border:1px solid #14532d;border-radius:10px;padding:10px 14px;color:#86efac;font-size:0.8rem;margin-bottom:8px">🟢 &nbsp;AI online &nbsp;{gpu_label}</div>', unsafe_allow_html=True)
            current_model = _get_ollama_model()
            default_idx = available_models.index(current_model) if current_model in available_models else 0
            chosen = st.selectbox(
                "Model", available_models, index=default_idx,
                label_visibility="collapsed",
                format_func=_model_label,
            )
            if chosen != st.session_state.get("selected_model"):
                st.session_state["selected_model"] = chosen
        else:
            st.markdown('<div style="background:#081a0f;border:1px solid #14532d;border-radius:10px;padding:10px 14px;color:#86efac;font-size:0.8rem">🟢 &nbsp;AI analysis online</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="background:#12141a;border:1px solid #1e2d42;border-radius:10px;padding:10px 14px;color:#4b5a7a;font-size:0.8rem">🔵 &nbsp;Set OLLAMA_BASE_URL in secrets to enable AI</div>', unsafe_allow_html=True)
    st.markdown("")
    st.caption("Data from OpenDota · No login needed")


# ── Data ───────────────────────────────────────────────────────────────────────
account_id = st.session_state.get("account_id")
with st.spinner("Loading hero data..."):
    hero_map = get_opendota_hero_map()
    hero_stats = get_opendota_hero_stats()
hero_names_sorted = sorted([h["name"] for h in hero_map.values() if h.get("name")], key=str.lower)

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📊 Overview", "🕹️ Match History", "🔍 Match Analyzer",
    "🦸 Heroes", "👥 Peers", "📈 Trends", "🗺️ Behavior",
    "⚔️ Draft Simulator", "ℹ️ About"
])

# Tab 0→heroes, 1→cover, 2→muerta, 3→heroes, 4→cover, 5→heroes, 6→muerta, 7→heroes, 8→logo
inject_tab_bg_switcher([
    IMG["heroes"], IMG["cover"], IMG["muerta"], IMG["heroes"], IMG["cover"],
    IMG["heroes"], IMG["muerta"], IMG["heroes"], IMG["logo"]
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Overview
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    if not account_id:
        # Welcome banner using heroes artwork
        st.markdown(f"""
        <div style="border-radius:24px;overflow:hidden;position:relative;height:360px;
                    background-image:{heroes_bg};background-size:cover;background-position:center top">
            <div style="position:absolute;inset:0;background:linear-gradient(135deg,rgba(8,12,20,0.95) 0%,rgba(8,12,20,0.6) 60%,rgba(8,12,20,0.2) 100%)"></div>
            <div style="position:relative;z-index:1;padding:48px;height:100%;display:flex;flex-direction:column;justify-content:center">
                <div style="font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.2em;color:#c84b31;margin-bottom:12px">OpenDota API · No Login Required</div>
                <div style="font-size:3rem;font-weight:900;color:#f1f5f9;line-height:1;margin-bottom:16px">Dota 2<br>Analyzer</div>
                <div style="color:#64748b;max-width:380px;line-height:1.8;font-size:0.9rem">
                    Enter a Steam Account ID in the sidebar to unlock player stats,
                    match history, AI-powered analysis, and draft strategy.
                </div>
                <div style="display:flex;gap:24px;margin-top:28px;flex-wrap:wrap">
                    {''.join(f'<div style="background:rgba(255,255,255,0.05);border:1px solid #1a2840;border-radius:10px;padding:10px 16px;font-size:0.8rem;color:#94a3b8">{x}</div>' for x in ['📊 Win Rate &amp; Stats','🕹️ Match History','🔍 Match Analysis','⚔️ Draft Simulator'])}
                </div>
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        with st.spinner("Loading..."):
            player_data = get_opendota_player(account_id)
            wl_data = get_opendota_win_loss(account_id)
            recent = get_opendota_recent_matches(account_id, limit=20)

        profile = player_data.get("profile") or {}
        name = profile.get("personaname") or f"Player {account_id}"
        avatar = profile.get("avatarfull") or profile.get("avatar")

        # Player header with artwork background
        avatar_html = f'<img src="{avatar}" width="80" height="80" style="border-radius:12px;border:2px solid #1a2840">' if avatar else '<div style="width:80px;height:80px;background:#1a2840;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:2.5rem">👤</div>'
        st.markdown(f"""
        <div style="border-radius:20px;overflow:hidden;position:relative;
                    background-image:{heroes_bg};background-size:cover;background-position:center;
                    margin-bottom:24px;padding:28px 32px">
            <div style="position:absolute;inset:0;background:rgba(8,12,20,0.88)"></div>
            <div style="position:relative;z-index:1;display:flex;align-items:center;gap:20px">
                {avatar_html}
                <div>
                    <div style="font-size:1.8rem;font-weight:800;color:#f1f5f9">{name}</div>
                    <div style="color:#4b5a7a;font-size:0.82rem;margin-top:4px">Account ID: {account_id}</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        # Compute stats
        wins = wl_data.get("win", 0); losses = wl_data.get("lose", 0)
        total = wins + losses; wr = (wins/total*100) if total else 0
        wr_col = "#22c55e" if wr>=52 else "#f59e0b" if wr>=48 else "#ef4444"

        hero_counts = {}; kills_l, deaths_l, assists_l, gpms_l = [],[],[],[]
        recent_wins = 0
        for m in (recent or []):
            hid = m.get("hero_id")
            if hid: hname=get_hero_name(hero_map,hid); hero_counts[hname]=hero_counts.get(hname,0)+1
            kills_l.append(m.get("kills",0)); deaths_l.append(m.get("deaths",0))
            assists_l.append(m.get("assists",0)); gpms_l.append(m.get("gold_per_min",0))
            slot=m.get("player_slot",0); is_r=slot<128
            if (is_r and m.get("radiant_win")) or (not is_r and not m.get("radiant_win")): recent_wins+=1

        top_hero = max(hero_counts.items(), key=lambda x:x[1]) if hero_counts else ("—",0)
        rwr = (recent_wins/len(recent)*100) if recent else 0
        rwr_col = "#22c55e" if rwr>=52 else "#f59e0b" if rwr>=48 else "#ef4444"
        avg_kda = f"{sum(kills_l)/len(kills_l):.1f}/{sum(deaths_l)/len(deaths_l):.1f}/{sum(assists_l)/len(assists_l):.1f}" if kills_l else "—"
        avg_gpm = f"{sum(gpms_l)/len(gpms_l):.0f}" if gpms_l else "—"

        c1,c2,c3,c4,c5 = st.columns(5)
        with c1: kpi("🎮","Total Games", str(total), f"{wins}W · {losses}L")
        with c2: kpi("🏆","Win Rate", f"{wr:.1f}%", "All time", wr_col)
        with c3: kpi("📈","Recent Form", f"{rwr:.0f}%", "Last 20", rwr_col)
        with c4: kpi("⚔️","Avg K/D/A", avg_kda, "Last 20")
        with c5: kpi("💰","Avg GPM", avg_gpm, f"Fav: {top_hero[0]}")

        st.markdown("")

        # Most played heroes with icons
        if hero_counts:
            sec("Most Played Heroes", "🦸")
            top_heroes = sorted(hero_counts.items(), key=lambda x:x[1], reverse=True)[:10]
            chips_html = ""
            for hname, cnt in top_heroes:
                hid = next((hid for hid,h in hero_map.items() if h.get("name")==hname), None)
                icon = get_hero_image(hero_map, hid, "icon") if hid else None
                img = f'<img src="{icon}" width="22" height="22" style="border-radius:4px">' if icon else "🧙"
                chips_html += f'<span class="hero-chip">{img} {hname} <strong style="color:#c84b31">×{cnt}</strong></span>'
            st.markdown(chips_html, unsafe_allow_html=True)

        # Charts
        if recent:
            st.markdown("")
            col_a, col_b = st.columns(2)
            with col_a:
                sec("Win Rate Trend", "📈")
                st.plotly_chart(winrate_trend(recent), use_container_width=True)
            with col_b:
                sec("Hero Distribution", "🎯")
                df_h = pd.DataFrame(top_heroes[:8], columns=["Hero","Games"])
                fig2 = px.bar(df_h, x="Games", y="Hero", orientation="h",
                               color="Games", color_continuous_scale=["#1a2840","#c84b31"])
                fig2.update_layout(paper_bgcolor="#0d1520",plot_bgcolor="#0d1520",
                    font_color="#64748b",showlegend=False,coloraxis_showscale=False,
                    height=240,margin=dict(l=0,r=10,t=10,b=10),
                    yaxis=dict(tickfont=dict(size=11)),xaxis=dict(gridcolor="#0f1e30"))
                st.plotly_chart(fig2, use_container_width=True)

        # AI
        sec("AI PERFORMANCE ANALYSIS", "✨")
        if st.button("Generate AI Analysis", type="primary", key="ai_ov"):
            if not _ai_available: _ai_warn()
            elif recent:
                ctx = f"Player: {name}\nWin rate: {wr:.1f}% ({wins}W/{losses}L)\nRecent form: {rwr:.0f}%\nAvg KDA: {avg_kda}\nAvg GPM: {avg_gpm}\nMost played: {', '.join(h for h,_ in top_heroes[:6])}"
                render_ai_output(ctx,
                    system="You are an expert Dota 2 coach. Be specific and actionable. 4-6 sentences.",
                    lore=False, max_tokens=400)

    footer()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Match History
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    banner(cover_bg, "Match History", "Last 20 matches · hero performance breakdown · win rate trends")

    if not account_id:
        st.info("Enter a player in the sidebar to view match history.")
    else:
        with st.spinner("Loading..."):
            matches = get_opendota_recent_matches(account_id, limit=20)

        if not matches:
            st.warning("No recent matches found.")
        else:
            sec(f"Last {len(matches)} Matches", "🕹️")
            render_match_cards(matches, hero_map)

            # Hero breakdown
            hero_stats_rows = {}
            for m in matches:
                hname = get_hero_name(hero_map, m.get("hero_id"))
                slot = m.get("player_slot",0); is_r = slot<128
                won = (is_r and m.get("radiant_win")) or (not is_r and not m.get("radiant_win"))
                if hname not in hero_stats_rows:
                    hero_stats_rows[hname] = {"games":0,"wins":0,"kills":0,"deaths":0,"assists":0}
                r = hero_stats_rows[hname]
                r["games"]+=1; r["wins"]+=(1 if won else 0)
                r["kills"]+=m.get("kills",0); r["deaths"]+=m.get("deaths",0); r["assists"]+=m.get("assists",0)

            sec("Hero Breakdown", "📊")
            col_hb, col_wrc = st.columns([1, 1])
            with col_hb:
                render_hero_breakdown(hero_stats_rows)
            with col_wrc:
                df_wr = pd.DataFrame([
                    {"Hero":h, "WR": d["wins"]/d["games"]*100, "G": d["games"]}
                    for h,d in sorted(hero_stats_rows.items(), key=lambda x:-x[1]["games"])
                ])
                fig_wr = go.Figure(go.Bar(
                    x=df_wr["WR"], y=df_wr["Hero"], orientation="h",
                    marker=dict(
                        color=df_wr["WR"],
                        colorscale=[[0,"#ef4444"],[0.5,"#f59e0b"],[1,"#22c55e"]],
                        cmin=0, cmax=100,
                        line=dict(color="#0d1520", width=1),
                    ),
                    text=[f"{v:.0f}%" for v in df_wr["WR"]],
                    textposition="outside", textfont=dict(size=10, color="#94a3b8"),
                    hovertemplate="%{y}: %{x:.0f}%<extra></extra>",
                ))
                fig_wr.add_vline(x=50, line_dash="dot", line_color="#1e2d42")
                fig_wr.update_layout(paper_bgcolor="#0d1520",plot_bgcolor="#0d1520",
                    font_color="#64748b",height=max(280,len(df_wr)*36),
                    margin=dict(l=0,r=40,t=10,b=10),
                    xaxis=dict(range=[0,115],gridcolor="#0f1e30",tickfont=dict(size=9)),
                    yaxis=dict(tickfont=dict(size=11)))
                st.plotly_chart(fig_wr, use_container_width=True)

            # CSV download + select for analyzer
            csv_buf = io.StringIO()
            rows_csv = []
            for m in matches:
                hname = get_hero_name(hero_map, m.get("hero_id"))
                slot = m.get("player_slot",0); is_r = slot<128; rw = m.get("radiant_win")
                won = (is_r and rw) or (not is_r and not rw)
                dur = round(m.get("duration",0)/60,1)
                start = m.get("start_time")
                rows_csv.append({"Date": datetime.fromtimestamp(start).strftime("%d %b %Y") if start else "",
                    "Hero":hname,"Side":"Radiant" if is_r else "Dire",
                    "Result":"Win" if won else "Loss",
                    "KDA":f"{m.get('kills',0)}/{m.get('deaths',0)}/{m.get('assists',0)}",
                    "GPM":m.get("gold_per_min",0),"XPM":m.get("xp_per_min",0),
                    "Duration":f"{dur}m","Match ID":str(m.get("match_id",""))})
            pd.DataFrame(rows_csv).to_csv(csv_buf, index=False)

            col_dl, col_sel, col_go = st.columns([1,3,1])
            with col_dl:
                st.download_button("⬇️ CSV", csv_buf.getvalue(),
                    file_name=f"dota_{account_id}.csv", mime="text/csv")
            with col_sel:
                match_ids = [str(m.get("match_id")) for m in matches if m.get("match_id")]
                selected = st.selectbox("Open in Match Analyzer", ["Select..."] + match_ids, label_visibility="visible")
            with col_go:
                st.markdown("<div style='margin-top:26px'>", unsafe_allow_html=True)
                if st.button("Open →", type="primary") and selected != "Select...":
                    st.session_state["selected_match_id"] = selected
                    st.info(f"Match {selected} queued → switch to Match Analyzer tab.")
                st.markdown("</div>", unsafe_allow_html=True)

    footer()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Match Analyzer
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    banner(muerta_bg if IMG["muerta"] else cover_bg, "Match Analyzer",
           "Gold & XP advantage · teamfight breakdowns · AI match analysis with Dota lore")

    col_inp, col_btn = st.columns([5,1])
    with col_inp:
        mid_val = st.text_input("Match ID", value=st.session_state.get("selected_match_id",""),
                                  placeholder="Enter a match ID e.g. 7891234567", label_visibility="visible")
    with col_btn:
        st.markdown("<div style='margin-top:26px'>", unsafe_allow_html=True)
        load_btn = st.button("Load", type="primary")
        st.markdown("</div>", unsafe_allow_html=True)

    if load_btn and mid_val.strip():
        st.session_state["selected_match_id"] = mid_val.strip()
        st.session_state.pop("dota_match_data", None)
        st.session_state.pop("dota_analysis", None)

    mid = st.session_state.get("selected_match_id")
    if mid:
        if "dota_match_data" not in st.session_state or st.session_state.get("_mid_loaded") != mid:
            with st.spinner(f"Fetching match {mid}..."):
                md = get_opendota_match(mid)
            st.session_state["dota_match_data"] = md
            st.session_state["_mid_loaded"] = mid
        else:
            md = st.session_state["dota_match_data"]

        if not md or not md.get("match_id"):
            st.error("Match not found or not yet parsed by OpenDota.")
        else:
            dur = md.get("duration",0); rw = md.get("radiant_win")
            rs = md.get("radiant_score",0); ds = md.get("dire_score",0)
            start_time = md.get("start_time")
            date_str = datetime.fromtimestamp(start_time).strftime("%d %b %Y %H:%M") if start_time else ""

            # Match header card
            winner_text = "🟢 Radiant Victory" if rw else "🔴 Dire Victory"
            winner_color = "#22c55e" if rw else "#ef4444"
            winner_bg = "rgba(34,197,94,0.08)" if rw else "rgba(239,68,68,0.08)"
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#0d1824,#111d2e);border:1px solid {winner_color}33;
                        border-radius:20px;padding:24px 32px;margin-bottom:24px;
                        background-image:linear-gradient(135deg,{winner_bg},{winner_bg})">
                <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px">
                    <div>
                        <div style="font-size:1.6rem;font-weight:800;color:{winner_color}">{winner_text}</div>
                        <div style="color:#334155;font-size:0.82rem;margin-top:6px">Match {mid} · {date_str}</div>
                    </div>
                    <div style="display:flex;align-items:center;gap:32px">
                        <div style="text-align:center">
                            <div style="font-size:2.5rem;font-weight:900;color:#22c55e;line-height:1">{rs}</div>
                            <div style="font-size:0.65rem;color:#4b5a7a;text-transform:uppercase;letter-spacing:0.1em;margin-top:4px">Radiant</div>
                        </div>
                        <div style="text-align:center">
                            <div style="font-size:1rem;font-weight:700;color:#334155">{round(dur/60,1)}m</div>
                            <div style="font-size:0.65rem;color:#4b5a7a;text-transform:uppercase">Duration</div>
                        </div>
                        <div style="text-align:center">
                            <div style="font-size:2.5rem;font-weight:900;color:#ef4444;line-height:1">{ds}</div>
                            <div style="font-size:0.65rem;color:#4b5a7a;text-transform:uppercase;letter-spacing:0.1em;margin-top:4px">Dire</div>
                        </div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

            # Draft
            picks_bans = md.get("picks_bans") or []
            if picks_bans:
                sec("Draft", "⚔️")
                rp=[get_hero_name(hero_map,pb["hero_id"]) for pb in picks_bans if pb.get("is_pick") and pb.get("team")==0]
                dp=[get_hero_name(hero_map,pb["hero_id"]) for pb in picks_bans if pb.get("is_pick") and pb.get("team")==1]
                rb=[get_hero_name(hero_map,pb["hero_id"]) for pb in picks_bans if not pb.get("is_pick") and pb.get("team")==0]
                db=[get_hero_name(hero_map,pb["hero_id"]) for pb in picks_bans if not pb.get("is_pick") and pb.get("team")==1]
                cr, cd = st.columns(2)
                with cr:
                    st.markdown('<span style="color:#22c55e;font-weight:800;font-size:0.9rem">🟢 RADIANT PICKS</span>', unsafe_allow_html=True)
                    chips = "".join(f'<span class="hero-chip">⚔️ {h}</span>' for h in rp)
                    st.markdown(chips or '<span style="color:#334155">No picks recorded</span>', unsafe_allow_html=True)
                    if rb: st.markdown(f'<div style="color:#334155;font-size:0.75rem;margin-top:6px">Bans: {", ".join(rb)}</div>', unsafe_allow_html=True)
                with cd:
                    st.markdown('<span style="color:#ef4444;font-weight:800;font-size:0.9rem">🔴 DIRE PICKS</span>', unsafe_allow_html=True)
                    chips = "".join(f'<span class="hero-chip">⚔️ {h}</span>' for h in dp)
                    st.markdown(chips or '<span style="color:#334155">No picks recorded</span>', unsafe_allow_html=True)
                    if db: st.markdown(f'<div style="color:#334155;font-size:0.75rem;margin-top:6px">Bans: {", ".join(db)}</div>', unsafe_allow_html=True)

            # Advantage charts
            gold_adv = md.get("radiant_gold_adv") or []
            xp_adv = md.get("radiant_xp_adv") or []
            if gold_adv or xp_adv:
                sec("Advantage Over Time", "📈")
                cg, cx = st.columns(2)
                with cg:
                    if gold_adv:
                        st.markdown('<span class="adv-label adv-radiant">Gold Advantage</span>', unsafe_allow_html=True)
                        st.plotly_chart(adv_chart(gold_adv,"Gold Advantage (Radiant +)"), use_container_width=True)
                with cx:
                    if xp_adv:
                        st.markdown('<span class="adv-label adv-dire">XP Advantage</span>', unsafe_allow_html=True)
                        st.plotly_chart(adv_chart(xp_adv,"XP Advantage (Radiant +)","#f59e0b","#7c3aed"), use_container_width=True)

            # Player performance
            players = md.get("players") or []
            if players:
                sec("Player Performance", "👥")
                render_player_table(players, hero_map)
                csv2 = io.StringIO()
                rows2 = [{"Side":"Radiant" if p.get("isRadiant") else "Dire",
                    "Hero":get_hero_name(hero_map,p.get("hero_id")),
                    "Level":p.get("level",0),
                    "KDA":f"{p.get('kills',0)}/{p.get('deaths',0)}/{p.get('assists',0)}",
                    "GPM":p.get("gold_per_min",0),"XPM":p.get("xp_per_min",0),
                    "Net Worth":p.get("net_worth",0),"Hero Dmg":p.get("hero_damage",0)} for p in players]
                pd.DataFrame(rows2).to_csv(csv2, index=False)
                st.markdown("<div style='margin-top:10px'>", unsafe_allow_html=True)
                st.download_button("⬇️ Download player stats CSV", csv2.getvalue(),
                    file_name=f"match_{mid}_players.csv", mime="text/csv")
                st.markdown("</div>", unsafe_allow_html=True)

            # Teamfights
            teamfights = md.get("teamfights") or []
            if teamfights:
                sec("Teamfight Swings", "⚡")
                render_teamfight_cards(teamfights)

            # AI Analysis
            sec("AI Match Analysis", "🤖")
            cp, ch = st.columns(2)
            with cp:
                perspective = st.selectbox("Perspective", ["Overall (Neutral)","Radiant","Dire"], key="mp")
            with ch:
                hero_list = ["All Heroes"] + [get_hero_name(hero_map,p.get("hero_id")) for p in players if p.get("hero_id")]
                hero_focus = st.selectbox("Hero Focus", hero_list, key="mhf")

            if st.button("🤖 Generate AI Match Analysis", type="primary", key="ai_m"):
                if not _ai_available: _ai_warn()
                else:
                    ctx = build_dota_match_context(md, hero_map)
                    hf_section = f"\n\nHERO FOCUS — Provide a dedicated section analyzing {hero_focus}'s specific performance: what went wrong, mistakes, missed opportunities, itemisation, and improvement advice." if hero_focus != "All Heroes" else ""
                    system = """You are an expert Dota 2 analyst. CRITICAL: Begin with 2-3 sentences of dramatic Dota 2 lore narrative describing this clash between these specific heroes. Reference actual lore, rivalries, character motivations. Then add --- and give your structured analysis.

Required sections:
1. Match Overview — winner, tempo, momentum shifts
2. Draft Analysis — team compositions, win conditions, lane matchups
3. Early Game (0-15min) — laning, first blood, towers
4. Mid Game (15-30min) — teamfights, key items, momentum
5. Late Game (30min+) — game-ending plays, buybacks
6. Critical Moments — 3-5 pivotal timestamps
7. Key Lessons — 3 specific actionable takeaways"""
                    result = render_ai_output(
                        f"Analyze this Dota 2 match from {perspective} perspective:{hf_section}\n\n{ctx}",
                        system=system, max_tokens=1500)
                    if result:
                        st.session_state["dota_analysis"] = result
                        st.session_state["dota_ctx"] = ctx
                        report = f"# Dota 2 Match Analysis\nMatch: {mid} | Perspective: {perspective}\n\n{result}"
                        st.download_button("⬇️ Download analysis", report,
                            file_name=f"dota_analysis_{mid}.md", mime="text/markdown")

            if st.session_state.get("dota_analysis"):
                render_followup_chat("match", st.session_state.get("dota_ctx",""),
                    "You are an expert Dota 2 analyst. Answer follow-up questions specifically, referencing match data.")

    footer()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Heroes
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    banner(heroes_bg, "Hero Pool", "Full hero stats · global rankings · playstyle analysis", height=160)

    if not account_id:
        st.info("Load a player in the sidebar to see hero stats.")
    else:
        with st.spinner("Loading hero pool..."):
            ph_data = get_opendota_player_heroes(account_id)
            rankings = get_opendota_rankings(account_id)

        if not ph_data:
            st.warning("No hero data available for this player.")
        else:
            ranking_map = {r.get("hero_id"): r for r in rankings}
            sorted_heroes = sorted(ph_data, key=lambda x: -x.get("games", 0))
            total_h = len([h for h in ph_data if h.get("games", 0) > 0])
            best_wr_heroes = [h for h in ph_data if h.get("games", 0) >= 5]
            best_h = max(best_wr_heroes, key=lambda x: x.get("win", 0) / x.get("games", 1)) if best_wr_heroes else {}
            best_h_name = get_hero_name(hero_map, best_h.get("hero_id")) if best_h else "—"
            best_h_wr = best_h.get("win", 0) / best_h.get("games", 1) * 100 if best_h else 0
            most_played = sorted_heroes[0] if sorted_heroes else {}
            mp_name = get_hero_name(hero_map, most_played.get("hero_id")) if most_played else "—"
            mp_games = most_played.get("games", 0)

            hkc1, hkc2, hkc3, hkc4 = st.columns(4)
            with hkc1: kpi("🦸", "Heroes Played", str(total_h), f"Of {len(ph_data)} total", "#8b5cf6")
            with hkc2: kpi("🏆", "Most Played", mp_name, f"{mp_games} games", "#c84b31")
            with hkc3: kpi("⭐", "Best WR (5+ games)", best_h_name, f"{best_h_wr:.0f}%", "#22c55e")
            with hkc4:
                ranked_count = len([h for h in ph_data if h.get("hero_id") in ranking_map])
                kpi("🌍", "Global Rankings", str(ranked_count), "heroes ranked", "#f59e0b")

            sec("HERO PERFORMANCE", "🦸")
            hero_html = ""
            for h in sorted_heroes[:30]:
                hid = h.get("hero_id")
                hname = get_hero_name(hero_map, hid)
                icon_url = get_hero_image(hero_map, hid, "icon")
                g = h.get("games", 0)
                if g == 0: continue
                w = h.get("win", 0)
                wr = w / g * 100
                wr_color = "#22c55e" if wr >= 55 else "#f59e0b" if wr >= 45 else "#ef4444"
                wr_class = "good" if wr >= 55 else "mid" if wr >= 45 else "bad"
                rank_data = ranking_map.get(hid)
                rank_html = f'<span style="font-size:0.68rem;color:#8b5cf6;margin-left:8px">#{rank_data.get("rank","?")}</span>' if rank_data else ""
                img_html = f'<img src="{icon_url}" width="32" height="32" style="border-radius:6px">' if icon_url else '<div style="width:32px;height:32px;background:#1a2840;border-radius:6px"></div>'
                last_ts = h.get("last_played")
                last_str = datetime.fromtimestamp(last_ts).strftime("%d %b") if last_ts else ""
                hero_html += f"""
                <div class="hero-breakdown-card">
                    <div style="display:flex;align-items:center;gap:10px">
                        {img_html}
                        <div>
                            <div class="hb-hero">{hname}{rank_html}</div>
                            <div style="font-size:0.68rem;color:#334155">{last_str}</div>
                        </div>
                    </div>
                    <div class="hb-games">{g} games</div>
                    <div class="hb-wr {wr_class}">{wr:.0f}%</div>
                    <div>
                        <div class="hb-bar-wrap">
                            <div class="hb-bar-fill" style="width:{wr}%;background:{wr_color}"></div>
                        </div>
                    </div>
                </div>"""
            st.markdown(hero_html, unsafe_allow_html=True)

            sec("ROLE DISTRIBUTION & WIN RATE SPREAD", "📊")
            role_counts = {}
            for h in ph_data:
                hid = h.get("hero_id")
                g = h.get("games", 0)
                if g == 0: continue
                hero_info = hero_map.get(hid, {})
                for hs in hero_stats:
                    if (hs.get("localized_name") or hs.get("name")) == hero_info.get("name"):
                        for role in hs.get("roles", []):
                            role_counts[role] = role_counts.get(role, 0) + g
                        break

            rc1, rc2 = st.columns(2)
            with rc1:
                if role_counts:
                    fig_role = go.Figure(data=[go.Pie(
                        labels=list(role_counts.keys()),
                        values=list(role_counts.values()),
                        hole=0.5,
                        marker_colors=["#c84b31","#8b5cf6","#22c55e","#f59e0b","#60a5fa","#ec4899","#14b8a6","#f97316"],
                        textfont=dict(color="#94a3b8"),
                    )])
                    fig_role.update_layout(
                        paper_bgcolor="#0d1520", font_color="#64748b", height=260,
                        margin=dict(l=0,r=0,t=24,b=0),
                        legend=dict(font=dict(color="#64748b",size=10)),
                        title=dict(text="Roles Played (by games)", font=dict(color="#64748b",size=12)),
                    )
                    st.plotly_chart(fig_role, use_container_width=True)
            with rc2:
                played_5plus = [h for h in ph_data if h.get("games", 0) >= 5]
                if played_5plus:
                    hero_wrs = [h.get("win", 0) / h.get("games", 1) * 100 for h in played_5plus]
                    fig_dist = go.Figure()
                    fig_dist.add_trace(go.Histogram(x=hero_wrs, nbinsx=10,
                        marker_color="#c84b31", opacity=0.8))
                    fig_dist.add_vline(x=50, line_dash="dot", line_color="#4b5a7a")
                    fig_dist.update_layout(
                        title=dict(text="Win Rate Distribution (5+ games)", font=dict(color="#64748b",size=12)),
                        paper_bgcolor="#0d1520", plot_bgcolor="#0d1520", font_color="#64748b",
                        height=260, margin=dict(l=8,r=8,t=36,b=8),
                        xaxis=dict(gridcolor="#0f1e30", title="Win Rate %", tickfont=dict(size=9)),
                        yaxis=dict(gridcolor="#0f1e30", title="Heroes", tickfont=dict(size=9)),
                    )
                    st.plotly_chart(fig_dist, use_container_width=True)

            if rankings:
                sec("GLOBAL RANKINGS (Top Heroes)", "🌍")
                rank_html = ""
                for r in sorted(rankings, key=lambda x: x.get("rank", 999999))[:10]:
                    hid = r.get("hero_id")
                    hname = get_hero_name(hero_map, hid)
                    icon_url = get_hero_image(hero_map, hid, "icon")
                    rank = r.get("rank", "?")
                    score = r.get("score", 0)
                    img_html = f'<img src="{icon_url}" width="28" height="28" style="border-radius:5px">' if icon_url else ""
                    rank_html += f"""
                    <div style="background:linear-gradient(135deg,#0d1520,#111d2e);border:1px solid #1a2840;
                                border-radius:12px;padding:12px 16px;margin-bottom:8px;
                                display:flex;align-items:center;gap:16px">
                        <div style="font-size:1.2rem;font-weight:900;color:#8b5cf6;min-width:52px">#{rank}</div>
                        {img_html}
                        <div style="flex:1;font-weight:700;color:#e2e8f0">{hname}</div>
                        <div style="font-size:0.8rem;color:#64748b">Score {score:.0f}</div>
                    </div>"""
                st.markdown(rank_html, unsafe_allow_html=True)

            sec("AI HERO ANALYSIS", "🤖")
            if st.button("Generate Hero Analysis", type="primary", key="ai_heroes"):
                if not _ai_available: _ai_warn()
                else:
                    ctx = build_heroes_context(ph_data, hero_map, rankings)
                    render_ai_output(
                        f"Player hero pool:\n{ctx}\n\nProvide:\n1. What playstyle does this hero pool reveal (support, carry, initiator, etc.)?\n2. Which 2-3 heroes should they focus on to climb rank?\n3. Any major gaps in their pool (no reliable carry, no disable)?\nStart with a 2-sentence Dota lore narrative about the player's signature hero, then ---.",
                        system="You are a Dota 2 expert coach. Be specific and actionable.",
                        max_tokens=800)
    footer()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — Peers
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    banner(cover_bg, "Teammates & Peers", "Most played with · win rate synergy · queue recommendations", height=160)

    if not account_id:
        st.info("Load a player in the sidebar to see peer data.")
    else:
        with st.spinner("Loading peer data..."):
            peers_data = get_opendota_peers(account_id)

        valid_peers = [p for p in peers_data if p.get("with_games", 0) >= 3]
        valid_peers.sort(key=lambda x: -x.get("with_games", 0))

        if not valid_peers:
            st.warning("Not enough peer data. Need 3+ games with the same player.")
        else:
            best_peer = max(valid_peers, key=lambda p: p.get("with_win", 0) / max(p.get("with_games", 1), 1))
            worst_peer = min(valid_peers, key=lambda p: p.get("with_win", 0) / max(p.get("with_games", 1), 1)) if len(valid_peers) > 1 else {}

            pkc1, pkc2, pkc3 = st.columns(3)
            with pkc1:
                kpi("👥", "Regular Teammates", str(len(valid_peers)), "3+ games together", "#8b5cf6")
            with pkc2:
                if best_peer:
                    bname = (best_peer.get("personaname") or f"Player {best_peer.get('account_id','?')}")[:16]
                    bwr = best_peer.get("with_win", 0) / max(best_peer.get("with_games", 1), 1) * 100
                    kpi("🤝", "Best Partner", bname, f"{bwr:.0f}% WR together", "#22c55e")
            with pkc3:
                if worst_peer:
                    wname = (worst_peer.get("personaname") or f"Player {worst_peer.get('account_id','?')}")[:16]
                    wwr = worst_peer.get("with_win", 0) / max(worst_peer.get("with_games", 1), 1) * 100
                    kpi("💀", "Worst Partner", wname, f"{wwr:.0f}% WR together", "#ef4444")

            sec("MOST PLAYED WITH", "🎮")
            peer_html = ""
            for p in valid_peers[:20]:
                name = p.get("personaname") or f"Player {p.get('account_id', '?')}"
                avatar = p.get("avatar")
                wg = p.get("with_games", 0)
                ww = p.get("with_win", 0)
                wwr = ww / wg * 100 if wg > 0 else 0
                ag = p.get("against_games", 0)
                wr_color = "#22c55e" if wwr >= 55 else "#f59e0b" if wwr >= 45 else "#ef4444"
                avatar_html = f'<img src="{avatar}" width="36" height="36" style="border-radius:8px;border:1px solid #1a2840">' if avatar else '<div style="width:36px;height:36px;background:#1a2840;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:1rem">👤</div>'
                peer_html += f"""
                <div style="background:linear-gradient(135deg,#0d1520,#111d2e);border:1px solid #1a2840;
                            border-left:4px solid {wr_color};border-radius:14px;padding:14px 18px;margin-bottom:8px;
                            display:grid;grid-template-columns:44px 1fr auto auto auto;align-items:center;gap:16px">
                    {avatar_html}
                    <div>
                        <div style="font-weight:700;color:#e2e8f0;font-size:0.9rem">{name}</div>
                        <div style="font-size:0.72rem;color:#4b5a7a">{wg} games together · {ag} against</div>
                    </div>
                    <div style="text-align:center">
                        <div style="font-size:1.1rem;font-weight:800;color:{wr_color}">{wwr:.0f}%</div>
                        <div style="font-size:0.62rem;color:#4b5a7a;text-transform:uppercase">With WR</div>
                    </div>
                    <div style="text-align:center">
                        <div style="font-size:0.95rem;font-weight:700;color:#94a3b8">{ww}/{wg - ww}</div>
                        <div style="font-size:0.62rem;color:#4b5a7a;text-transform:uppercase">W / L</div>
                    </div>
                    <div style="width:80px">
                        <div style="background:#1a2840;border-radius:20px;height:6px;overflow:hidden">
                            <div style="width:{min(wwr,100):.0f}%;height:100%;background:{wr_color};border-radius:20px"></div>
                        </div>
                    </div>
                </div>"""
            st.markdown(peer_html, unsafe_allow_html=True)

            if len(valid_peers) >= 3:
                sec("WIN RATE BY TEAMMATE", "📊")
                top_p = valid_peers[:15]
                p_names = [(p.get("personaname") or f"P{p.get('account_id','?')}")[:12] for p in top_p]
                p_wrs = [p.get("with_win", 0) / max(p.get("with_games", 1), 1) * 100 for p in top_p]
                bar_colors = ["#22c55e" if w >= 55 else "#f59e0b" if w >= 45 else "#ef4444" for w in p_wrs]
                fig_peers = go.Figure(go.Bar(x=p_names, y=p_wrs, marker_color=bar_colors,
                    text=[f"{w:.0f}%" for w in p_wrs], textposition="outside",
                    textfont=dict(color="#94a3b8", size=9)))
                fig_peers.add_hline(y=50, line_dash="dot", line_color="#1e2d42")
                fig_peers.update_layout(
                    paper_bgcolor="#0d1520", plot_bgcolor="#0d1520", font_color="#64748b",
                    height=260, margin=dict(l=8,r=8,t=20,b=8),
                    xaxis=dict(gridcolor="#0f1e30", tickfont=dict(size=9)),
                    yaxis=dict(gridcolor="#0f1e30", range=[0,110], title="Win Rate %", tickfont=dict(size=9)),
                    showlegend=False)
                st.plotly_chart(fig_peers, use_container_width=True)

            sec("AI TEAMMATE ANALYSIS", "🤖")
            if st.button("Analyze Teammates", type="primary", key="ai_peers"):
                if not _ai_available: _ai_warn()
                else:
                    ctx = build_peers_context(peers_data)
                    render_ai_output(
                        f"Teammate data:\n{ctx}\n\nAnalyze:\n1. Who are the top 2-3 players to queue with and why?\n2. Which players are hurting win rate?\n3. Any patterns — winning with certain player types (supports, carries)?\nStart with a 2-sentence Dota lore narrative about allies and teamwork then ---.",
                        system="You are a Dota 2 expert. Short, direct, actionable.",
                        max_tokens=600)
    footer()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — Trends & Records
# ══════════════════════════════════════════════════════════════════════════════
with tab6:
    banner(heroes_bg, "Trends & Records",
           "Activity by day & hour · stat totals · win/loss streaks · performance patterns", height=160)

    if not account_id:
        st.info("Load a player in the sidebar to see trends.")
    else:
        with st.spinner("Loading trends data..."):
            totals_data = get_opendota_totals(account_id)
            matches_300 = get_opendota_matches(account_id, limit=300)

        if matches_300:
            from collections import Counter
            dow_counts = Counter()
            dow_wins = Counter()
            hour_counts = Counter()
            for m in matches_300:
                st_time = m.get("start_time")
                if not st_time: continue
                d = datetime.fromtimestamp(st_time)
                dow = d.strftime("%a")
                dow_counts[dow] += 1
                hour_counts[d.hour] += 1
                slot = m.get("player_slot", 0)
                rw = m.get("radiant_win")
                won = (slot < 128 and rw) or (slot >= 128 and not rw)
                if won: dow_wins[dow] += 1

            dows = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
            dow_g = [dow_counts.get(d, 0) for d in dows]
            dow_wr = [dow_wins.get(d, 0) / max(dow_counts.get(d, 1), 1) * 100 for d in dows]

            sec("ACTIVITY PATTERNS", "📅")
            col_cal1, col_cal2 = st.columns(2)
            with col_cal1:
                fig_dow = go.Figure()
                fig_dow.add_trace(go.Bar(name="Games", x=dows, y=dow_g,
                    marker_color="#c84b31", opacity=0.75, yaxis="y"))
                fig_dow.add_trace(go.Scatter(name="Win %", x=dows, y=dow_wr,
                    mode="lines+markers", line=dict(color="#22c55e", width=2.5),
                    marker=dict(size=8), yaxis="y2"))
                fig_dow.add_hline(y=50, line_dash="dot", line_color="#1e2d42", yref="y2")
                fig_dow.update_layout(
                    title=dict(text="Games & Win Rate by Day", font=dict(color="#64748b",size=12)),
                    paper_bgcolor="#0d1520", plot_bgcolor="#0d1520", font_color="#64748b",
                    height=260, margin=dict(l=8,r=8,t=36,b=8),
                    xaxis=dict(gridcolor="#0f1e30", tickfont=dict(size=9)),
                    yaxis=dict(gridcolor="#0f1e30", title="Games", tickfont=dict(size=9)),
                    yaxis2=dict(range=[0,100], title="Win %", tickfont=dict(size=9), side="right", overlaying="y"),
                    legend=dict(font=dict(color="#64748b",size=10)),
                )
                st.plotly_chart(fig_dow, use_container_width=True)
            with col_cal2:
                hours = list(range(24))
                h_counts = [hour_counts.get(h, 0) for h in hours]
                fig_hour = go.Figure(go.Bar(x=hours, y=h_counts,
                    marker_color=["#c84b31" if (h >= 20 or h <= 3) else "#8b5cf6" if (14 <= h <= 19) else "#1e3d5a" for h in hours],
                    hovertemplate="Hour %{x}:00 — %{y} games<extra></extra>"))
                fig_hour.update_layout(
                    title=dict(text="Games by Hour (Local Time)", font=dict(color="#64748b",size=12)),
                    paper_bgcolor="#0d1520", plot_bgcolor="#0d1520", font_color="#64748b",
                    height=260, margin=dict(l=8,r=8,t=36,b=8),
                    xaxis=dict(gridcolor="#0f1e30", title="Hour", tickvals=list(range(0,24,3)), tickfont=dict(size=9)),
                    yaxis=dict(gridcolor="#0f1e30", title="Games", tickfont=dict(size=9)),
                )
                st.plotly_chart(fig_hour, use_container_width=True)

            sec("WIN / LOSS STREAKS", "🔥")
            results_300 = []
            for m in matches_300:
                slot = m.get("player_slot", 0)
                rw = m.get("radiant_win")
                won = (slot < 128 and rw) or (slot >= 128 and not rw)
                results_300.append(won)
            max_win = max_loss = cur_win = cur_loss = 0
            for r in results_300:
                if r:
                    cur_win += 1; cur_loss = 0; max_win = max(max_win, cur_win)
                else:
                    cur_loss += 1; cur_win = 0; max_loss = max(max_loss, cur_loss)

            sc1, sc2, sc3, sc4 = st.columns(4)
            with sc1: kpi("🔥", "Best Win Streak", str(max_win), "consecutive wins", "#22c55e")
            with sc2: kpi("💀", "Worst Loss Streak", str(max_loss), "consecutive losses", "#ef4444")
            with sc3:
                r10 = results_300[:10]
                kpi("📊", "Last 10 Games", f"{sum(r10)}W-{10-sum(r10)}L", "recent form",
                    "#22c55e" if sum(r10) >= 6 else "#ef4444")
            with sc4:
                wr_300 = sum(results_300) / len(results_300) * 100 if results_300 else 0
                kpi("🎯", f"Last {len(results_300)} Win Rate", f"{wr_300:.1f}%",
                    f"{sum(results_300)}W {len(results_300)-sum(results_300)}L", "#c84b31")

        if totals_data:
            sec("STAT TOTALS", "📊")
            display_fields = {
                "kills": ("⚔️", "Total Kills", "#ef4444"),
                "deaths": ("💀", "Total Deaths", "#94a3b8"),
                "assists": ("🤝", "Total Assists", "#22c55e"),
                "gold_per_min": ("💰", "Avg GPM", "#f59e0b"),
                "xp_per_min": ("⚡", "Avg XPM", "#8b5cf6"),
                "last_hits": ("🎯", "Total Last Hits", "#60a5fa"),
                "hero_damage": ("🔥", "Hero Damage", "#c84b31"),
                "tower_damage": ("🏰", "Tower Damage", "#f97316"),
                "hero_healing": ("💚", "Total Healing", "#10b981"),
            }
            total_rows = []
            for row in totals_data:
                field = row.get("field")
                n = row.get("n", 0)
                s = row.get("sum", 0)
                if field in display_fields and n > 0:
                    icon, label, color = display_fields[field]
                    avg = s / n
                    total_rows.append({"icon": icon, "label": label, "color": color,
                                       "total": s, "avg": avg, "n": n, "field": field})
            if total_rows:
                tcols = st.columns(3)
                for i, row in enumerate(total_rows):
                    with tcols[i % 3]:
                        if row["field"] in ("gold_per_min", "xp_per_min"):
                            val_str = f"{row['avg']:.0f}"
                            sub = f"over {row['n']} games"
                        else:
                            val_str = f"{row['total']:,.0f}"
                            sub = f"avg {row['avg']:.0f}/game"
                        kpi(row["icon"], row["label"], val_str, sub, row["color"])

        sec("AI PERFORMANCE ANALYSIS", "🤖")
        if st.button("Analyze Performance Trends", type="primary", key="ai_trends"):
            if not _ai_available: _ai_warn()
            else:
                ctx = build_totals_context(totals_data, matches_300)
                render_ai_output(
                    f"Performance data:\n{ctx}\n\nAnalyze:\n1. What habit or timing pattern stands out most (peak hours, day patterns)?\n2. Are there tilt indicators (long loss streaks, late-night losing)?\n3. One specific, actionable improvement to raise win rate.\nStart with a 2-sentence Dota lore narrative about perseverance then ---.",
                    system="You are a Dota 2 performance coach. Be specific and direct.",
                    max_tokens=600)
    footer()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — Behavior
# ══════════════════════════════════════════════════════════════════════════════
with tab7:
    banner(muerta_bg if IMG["muerta"] else cover_bg, "Behavior & Wards",
           "Ward heatmap · chat word cloud · support quality · AI behavior read", height=160)

    if not account_id:
        st.info("Load a player in the sidebar to see behavior data.")
    else:
        with st.spinner("Loading behavior data..."):
            wardmap_data = get_opendota_wardmap(account_id)
            wordcloud_data = get_opendota_wordcloud(account_id)

        obs = wardmap_data.get("obs") or {}
        sen = wardmap_data.get("sen") or {}
        my_words = wordcloud_data.get("my_word_counts") or {}

        def flatten_wards(ward_dict):
            pts = []
            for xk, ydict in ward_dict.items():
                if isinstance(ydict, dict):
                    for yk, cnt in ydict.items():
                        try:
                            pts.extend([(int(xk), int(yk))] * min(int(cnt), 15))
                        except Exception:
                            pass
            return pts

        obs_pts = flatten_wards(obs)
        sen_pts = flatten_wards(sen)

        bkc1, bkc2, bkc3, bkc4 = st.columns(4)
        with bkc1: kpi("👁️", "Observer Wards", str(len(obs_pts)), "placed across all games", "#60a5fa")
        with bkc2: kpi("🔍", "Sentry Wards", str(len(sen_pts)), "placed across all games", "#f59e0b")
        with bkc3:
            ratio = len(sen_pts) / max(len(obs_pts), 1)
            kpi("⚖️", "Sentry Ratio", f"{ratio:.2f}", "sentry per observer", "#8b5cf6")
        with bkc4:
            kpi("💬", "Words in Chat", f"{sum(my_words.values()):,}", f"{len(my_words)} unique words", "#22c55e")

        sec("WARD PLACEMENT HEATMAP", "🗺️")
        if obs_pts or sen_pts:
            fig_ward = go.Figure()
            if obs_pts:
                fig_ward.add_trace(go.Scatter(
                    x=[p[0] for p in obs_pts], y=[p[1] for p in obs_pts],
                    mode="markers", name="Observer",
                    marker=dict(size=7, color="rgba(96,165,250,0.65)", symbol="circle",
                                line=dict(color="rgba(96,165,250,0.2)", width=1)),
                    hovertemplate="Observer (%{x}, %{y})<extra></extra>",
                ))
            if sen_pts:
                fig_ward.add_trace(go.Scatter(
                    x=[p[0] for p in sen_pts], y=[p[1] for p in sen_pts],
                    mode="markers", name="Sentry",
                    marker=dict(size=7, color="rgba(251,191,36,0.65)", symbol="diamond",
                                line=dict(color="rgba(251,191,36,0.2)", width=1)),
                    hovertemplate="Sentry (%{x}, %{y})<extra></extra>",
                ))
            fig_ward.update_layout(
                paper_bgcolor="#080c14", plot_bgcolor="#0a0e1a",
                font_color="#64748b", height=420,
                margin=dict(l=8,r=8,t=16,b=8),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-50, 300]),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-50, 300]),
                legend=dict(font=dict(color="#94a3b8",size=11), bgcolor="rgba(0,0,0,0)",
                            x=0.01, y=0.99),
            )
            st.plotly_chart(fig_ward, use_container_width=True)
        else:
            st.info("No ward data available for this player.")

        if my_words:
            sec("CHAT WORD CLOUD", "💬")
            sorted_words = sorted(my_words.items(), key=lambda x: -x[1])[:60]
            max_count = sorted_words[0][1] if sorted_words else 1
            word_html = '<div style="display:flex;flex-wrap:wrap;gap:6px 10px;padding:20px;background:linear-gradient(135deg,#0d1520,#111d2e);border:1px solid #1a2840;border-radius:16px;line-height:1.8">'
            for word, count in sorted_words:
                pct = count / max_count
                size = max(10, min(28, int(10 + pct * 18)))
                weight = 700 if pct > 0.5 else 500 if pct > 0.25 else 400
                r = int(200 * pct + 96 * (1 - pct))
                g = int(75 * pct + 100 * (1 - pct))
                b = int(49 * pct + 140 * (1 - pct))
                alpha = max(0.45, min(1.0, 0.45 + pct * 0.55))
                word_html += f'<span title="{count}x" style="font-size:{size}px;color:rgba({r},{g},{b},{alpha});font-weight:{weight};cursor:default">{word}</span>'
            word_html += '</div>'
            st.markdown(word_html, unsafe_allow_html=True)

        sec("AI BEHAVIOR ANALYSIS", "🤖")
        if st.button("Analyze Behavior", type="primary", key="ai_behavior"):
            if not _ai_available: _ai_warn()
            else:
                ctx = build_behavior_context(wordcloud_data, wardmap_data)
                render_ai_output(
                    f"Player behavior data:\n{ctx}\n\nAnalyze:\n1. What does the chat behavior reveal (toxic, friendly, shot-caller, silent)?\n2. What does the ward placement ratio say about support quality and vision game?\n3. One specific change that would most improve their win rate from a behavioral standpoint.\nStart with a 2-sentence Dota lore narrative about vision and control of the map then ---.",
                    system="You are a Dota 2 behavioral analyst. Be direct and insightful.",
                    max_tokens=600)
    footer()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 8 — Draft Simulator
# ══════════════════════════════════════════════════════════════════════════════
with tab8:
    banner(heroes_bg, "Draft Simulator",
           "Build any draft · weighted random fill · AI strategy with hero lore", height=160)

    if "draft_r" not in st.session_state: st.session_state["draft_r"] = [None]*5
    if "draft_d" not in st.session_state: st.session_state["draft_d"] = [None]*5

    hero_opts = ["Select Hero"] + hero_names_sorted
    positions = ["Pos 1 · Carry","Pos 2 · Mid","Pos 3 · Offlane","Pos 4 · Support","Pos 5 · Hard Support"]
    pos_icons = ["🗡️","🔮","🛡️","💫","🕯️"]

    col_r, col_vs, col_d = st.columns([5,1,5])

    with col_r:
        st.markdown('<div style="color:#22c55e;font-weight:900;font-size:1rem;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:16px;padding-left:4px">🟢 RADIANT</div>', unsafe_allow_html=True)
        radiant_picks = []
        for i in range(5):
            curr = st.session_state["draft_r"][i]
            idx = hero_opts.index(curr) if curr and curr in hero_opts else 0
            st.markdown(f'<div style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;color:#22c55e;margin-bottom:2px">{pos_icons[i]} {positions[i]}</div>', unsafe_allow_html=True)
            h = st.selectbox("", hero_opts, index=idx, key=f"dr_{i}", label_visibility="collapsed")
            radiant_picks.append(None if h=="Select Hero" else h)

    with col_vs:
        st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="vs-circle">VS</div>', unsafe_allow_html=True)

    with col_d:
        st.markdown('<div style="color:#ef4444;font-weight:900;font-size:1rem;letter-spacing:0.08em;text-transform:uppercase;margin-bottom:16px;padding-left:4px">🔴 DIRE</div>', unsafe_allow_html=True)
        dire_picks = []
        for i in range(5):
            curr = st.session_state["draft_d"][i]
            idx = hero_opts.index(curr) if curr and curr in hero_opts else 0
            st.markdown(f'<div style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;color:#ef4444;margin-bottom:2px">{pos_icons[i]} {positions[i]}</div>', unsafe_allow_html=True)
            h = st.selectbox("", hero_opts, index=idx, key=f"dd_{i}", label_visibility="collapsed")
            dire_picks.append(None if h=="Select Hero" else h)

    st.markdown("")
    b1, b2, b3 = st.columns(3)
    with b1:
        if st.button("🎲 Random Draft", use_container_width=True):
            with st.spinner("Generating..."):
                rr, rd = generate_random_draft(hero_names_sorted, hero_stats,
                    existing_radiant=radiant_picks, existing_dire=dire_picks)
            st.session_state["draft_r"] = rr; st.session_state["draft_d"] = rd
            st.session_state.pop("dota_draft_rec", None)
            st.rerun()
    with b2:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state["draft_r"] = [None]*5; st.session_state["draft_d"] = [None]*5
            st.session_state.pop("dota_draft_rec", None)
            st.rerun()
    with b3:
        get_strat = st.button("✨ AI Strategy", use_container_width=True, type="primary")

    active_r = [h for h in radiant_picks if h]
    active_d = [h for h in dire_picks if h]

    if get_strat:
        if not active_r and not active_d:
            st.warning("Pick at least one hero first.")
        elif not _ai_available: _ai_warn()
        else:
            draft_ctx = f"Radiant: {', '.join(active_r) or 'TBD'}\nDire: {', '.join(active_d) or 'TBD'}"
            system = """You are a Dota 2 draft expert. CRITICAL: Begin with 2-3 sentences of vivid fantasy lore narrative about this specific matchup — reference actual Dota 2 hero lore, rivalries, and character motivations. Make it dramatic. Then add --- and give your analysis.

For each team provide:
- Win condition and primary strategy
- Power spike timing (early/mid/late)
- Key item priorities for each core
- What to be afraid of from the enemy draft
- Lane assignment recommendations

Be specific about the heroes picked."""
            result = render_ai_output(f"Analyze this Dota 2 draft:\n\n{draft_ctx}", system=system, max_tokens=900)
            if result:
                st.session_state["dota_draft_rec"] = result
                st.session_state["dota_draft_ctx"] = draft_ctx

    if st.session_state.get("dota_draft_rec") and not get_strat:
        st.markdown("")
        result = st.session_state["dota_draft_rec"]
        parts = result.split("---",1)
        if len(parts)==2:
            st.markdown(f'<div class="lore-box">✨ {parts[0].strip()}</div>', unsafe_allow_html=True)
            analysis = parts[1].strip()
        else:
            analysis = result

        cr2, cd2 = st.columns(2)
        mid_idx = -1
        for marker in ["**Dire","## Dire","### Dire","Dire:"]:
            if marker in analysis:
                mid_idx = analysis.index(marker); break
        if mid_idx > 0:
            with cr2:
                st.markdown('<div style="color:#22c55e;font-weight:800;margin-bottom:12px">🟢 Radiant Strategy</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="ai-output">{analysis[:mid_idx].strip()}</div>', unsafe_allow_html=True)
            with cd2:
                st.markdown('<div style="color:#ef4444;font-weight:800;margin-bottom:12px">🔴 Dire Strategy</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="ai-output">{analysis[mid_idx:].strip()}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="ai-output">{analysis}</div>', unsafe_allow_html=True)

    if st.session_state.get("dota_draft_rec"):
        result = st.session_state["dota_draft_rec"]
        report = f"# Dota 2 Draft Analysis\nRadiant: {', '.join(active_r)}\nDire: {', '.join(active_d)}\n\n{result}"
        st.download_button("⬇️ Download draft analysis", report,
            file_name="dota_draft_analysis.md", mime="text/markdown")
        render_followup_chat("draft", st.session_state.get("dota_draft_ctx",""),
            "You are an expert Dota 2 draft analyst. Answer follow-up questions about this specific draft — counter picks, item builds, lane assignments, timing windows.")

    footer()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 9 — About
# ══════════════════════════════════════════════════════════════════════════════
with tab9:
    # Full logo banner
    st.markdown(f"""
    <div style="border-radius:24px;overflow:hidden;position:relative;height:280px;
                background-image:{logo_bg};background-size:cover;background-position:center;
                margin-bottom:32px">
        <div style="position:absolute;inset:0;background:linear-gradient(135deg,rgba(8,12,20,0.9) 0%,rgba(8,12,20,0.5) 100%)"></div>
        <div style="position:relative;z-index:1;padding:48px;height:100%;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center">
            <div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.2em;color:#c84b31;margin-bottom:12px">Portfolio Project</div>
            <div style="font-size:2.5rem;font-weight:900;color:#f1f5f9;line-height:1">Dota 2 Analyzer</div>
            <div style="color:#64748b;margin-top:12px;max-width:500px;line-height:1.7">
                Full-featured Dota 2 analysis platform powered by OpenDota API and local AI.
                No login. No data stored. Fully open source.
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    ca, cb = st.columns(2)
    with ca:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#0d1824,#111d2e);border:1px solid #1a2840;border-radius:20px;padding:24px;margin-bottom:16px">
            <div style="font-weight:800;color:#f1f5f9;font-size:1rem;margin-bottom:16px">🎮 Features</div>
            <div style="color:#64748b;line-height:2.2;font-size:0.88rem">
                📊 <strong style="color:#94a3b8">Player Overview</strong> — Win rate, trends, hero distribution<br>
                🕹️ <strong style="color:#94a3b8">Match History</strong> — Visual cards, hero breakdown, CSV export<br>
                🔍 <strong style="color:#94a3b8">Match Analyzer</strong> — Gold/XP charts, teamfights, AI lore analysis<br>
                ⚔️ <strong style="color:#94a3b8">Draft Simulator</strong> — Smart random draft, AI strategy per team<br>
                💬 <strong style="color:#94a3b8">Follow-up Chat</strong> — Multi-turn Q&A after any AI analysis
            </div>
        </div>
        <div style="background:linear-gradient(135deg,#0d1824,#111d2e);border:1px solid #1a2840;border-radius:20px;padding:24px">
            <div style="font-weight:800;color:#f1f5f9;font-size:1rem;margin-bottom:16px">🔒 Privacy</div>
            <div style="color:#64748b;line-height:1.8;font-size:0.88rem">
                No data is stored server-side. All player data is fetched live from the public
                OpenDota API. AI analysis runs on a local Ollama instance — nothing is sent
                to OpenAI or any commercial AI provider.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with cb:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#0d1824,#111d2e);border:1px solid #1a2840;border-radius:20px;padding:24px;margin-bottom:16px">
            <div style="font-weight:800;color:#f1f5f9;font-size:1rem;margin-bottom:16px">👨‍💻 Built by</div>
            <div style="font-size:1.1rem;font-weight:700;color:#e2e8f0">Sameer Bhalerao</div>
            <div style="color:#4b5a7a;font-size:0.85rem;margin-top:2px">Senior Analytics & AI Product Leader · Amazon L6</div>
            <div style="margin-top:14px;display:flex;gap:10px;flex-wrap:wrap">
                <a href="https://sameerbhalerao.com" target="_blank" style="background:#12100a;border:1px solid #3d2e00;border-radius:8px;padding:6px 14px;color:#f59e0b;font-size:0.8rem;text-decoration:none">Portfolio</a>
                <a href="https://www.linkedin.com/in/sameervb" target="_blank" style="background:#0d1e30;border:1px solid #1a3050;border-radius:8px;padding:6px 14px;color:#60a5fa;font-size:0.8rem;text-decoration:none">LinkedIn</a>
                <a href="https://github.com/sameervb" target="_blank" style="background:#0d1e30;border:1px solid #1a3050;border-radius:8px;padding:6px 14px;color:#94a3b8;font-size:0.8rem;text-decoration:none">GitHub</a>
                <a href="https://soulspark.me" target="_blank" style="background:#1a0a08;border:1px solid #4a1a10;border-radius:8px;padding:6px 14px;color:#c84b31;font-size:0.8rem;text-decoration:none">Soul Spark</a>
            </div>
            <div style="color:#334155;font-size:0.82rem;line-height:1.7;margin-top:16px">
                This is one of 10 standalone public apps extracted from
                <a href="https://soulspark.me" style="color:#c84b31">Soul Spark</a> — a local-first
                personal intelligence platform built end-to-end in 8 weeks.
            </div>
        </div>
        <div style="background:linear-gradient(135deg,#0d1824,#111d2e);border:1px solid #1a2840;border-radius:20px;padding:24px">
            <div style="font-weight:800;color:#f1f5f9;font-size:1rem;margin-bottom:16px">🛠️ Tech Stack</div>
            <div style="display:flex;flex-wrap:wrap;gap:8px">
        """, unsafe_allow_html=True)
        for badge in ["Python 3.14","Streamlit","OpenDota API","Plotly","Pandas","Ollama (LLaMA 3.1)","Cloudflare Tunnel","Streamlit Community Cloud"]:
            st.markdown(f'<span style="background:#0a1420;border:1px solid #1e3050;border-radius:20px;padding:5px 12px;color:#94a3b8;font-size:0.75rem">{badge}</span>', unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)

    footer()
