"""
services/dota.py — OpenDota API helpers and Dota 2 draft logic.
"""
import random
import streamlit as st
import requests
from datetime import datetime

OPENDOTA_BASE_URL = "https://api.opendota.com/api"


@st.cache_data(ttl=900, show_spinner=False)
def fetch_opendota_json(endpoint, params=None):
    url = f"{OPENDOTA_BASE_URL}/{endpoint.lstrip('/')}"
    try:
        response = requests.get(url, params=params, timeout=12)
        if response.ok:
            return response.json()
    except Exception:
        pass
    return None


@st.cache_data(ttl=3600, show_spinner=False)
def get_opendota_hero_map():
    data = fetch_opendota_json("constants/heroes")
    if not isinstance(data, dict):
        return {}
    hero_map = {}
    cdn_base = "https://cdn.cloudflare.steamstatic.com"
    for _, hero in data.items():
        hero_id = hero.get("id")
        name = hero.get("localized_name") or hero.get("name")
        hero_img = hero.get("img")
        hero_icon = hero.get("icon")
        if hero_id is not None and name:
            hero_map[int(hero_id)] = {
                "name": name,
                "img": f"{cdn_base}{hero_img}" if hero_img else None,
                "icon": f"{cdn_base}{hero_icon}" if hero_icon else None,
            }
    return hero_map


@st.cache_data(ttl=1800, show_spinner=False)
def get_opendota_hero_stats():
    data = fetch_opendota_json("heroStats")
    return data if isinstance(data, list) else []


def build_hero_stats_index(hero_stats):
    return {
        (hero.get("localized_name") or hero.get("name")): hero
        for hero in hero_stats
        if hero.get("localized_name") or hero.get("name")
    }


def compute_hero_popularity_weight(hero_stat):
    total = sum(v for k, v in hero_stat.items() if k.endswith("_pick") and isinstance(v, (int, float)))
    pro_pick = hero_stat.get("pro_pick")
    if isinstance(pro_pick, (int, float)):
        total += pro_pick * 50
    return max(total, 1)


def get_matchup_multiplier(hero_stat, opponent_stat):
    multiplier = 1.0
    if hero_stat.get("primary_attr") and opponent_stat.get("primary_attr") and hero_stat["primary_attr"] != opponent_stat["primary_attr"]:
        multiplier *= 1.15
    if hero_stat.get("attack_type") and opponent_stat.get("attack_type") and hero_stat["attack_type"] != opponent_stat["attack_type"]:
        multiplier *= 1.1
    return multiplier


def weighted_choice(items, weights):
    if not items:
        return None
    total = sum(weights)
    if total <= 0:
        return random.choice(items)
    pick = random.uniform(0, total)
    current = 0
    for item, weight in zip(items, weights):
        current += weight
        if pick <= current:
            return item
    return items[-1]


def generate_random_draft(hero_options, hero_stats, existing_radiant=None, existing_dire=None):
    position_role_tags = {
        "pos1": {"Carry", "Durable", "Pusher"},
        "pos2": {"Carry", "Nuker", "Disabler", "Escape"},
        "pos3": {"Initiator", "Durable", "Disabler"},
        "pos4": {"Support", "Disabler", "Nuker", "Escape"},
        "pos5": {"Support", "Disabler", "Healer"},
    }
    hero_stats_by_name = build_hero_stats_index(hero_stats)
    hero_pool = [n for n in hero_options if n != "Select Hero" and n in hero_stats_by_name]
    if not hero_pool:
        hero_pool = [n for n in hero_options if n != "Select Hero"]

    existing_radiant = list(existing_radiant or [None] * 5)
    existing_dire = list(existing_dire or [None] * 5)
    used = {h for h in existing_radiant + existing_dire if h}

    def choose_hero(position_key, opponent_name=None):
        role_tags = position_role_tags.get(position_key, set())
        candidates = [
            n for n in hero_pool
            if n not in used and (
                not role_tags or not (hs := hero_stats_by_name.get(n, {})).get("roles") or
                set(hs.get("roles", [])).intersection(role_tags)
            )
        ]
        if not candidates:
            candidates = [n for n in hero_pool if n not in used]
        opponent_stat = hero_stats_by_name.get(opponent_name, {}) if opponent_name else {}
        weights = [
            compute_hero_popularity_weight(hero_stats_by_name.get(n, {})) *
            (get_matchup_multiplier(hero_stats_by_name.get(n, {}), opponent_stat) if opponent_stat else 1.0)
            for n in candidates
        ]
        choice = weighted_choice(candidates, weights)
        if choice:
            used.add(choice)
        return choice

    radiant = list(existing_radiant)
    dire = list(existing_dire)
    positions = ["pos1", "pos2", "pos3", "pos4", "pos5"]
    for i, pos in enumerate(positions):
        if not radiant[i]:
            radiant[i] = choose_hero(pos)
    fill_order = [2, 3, 1, 0, 4]
    opponents = [radiant[0], radiant[4], radiant[1], radiant[2], radiant[3]]
    for i, opp in zip(fill_order, opponents):
        if not dire[i]:
            dire[i] = choose_hero(positions[i], opponent_name=opp)
    return radiant, dire


@st.cache_data(ttl=3600, show_spinner=False)
def get_opendota_ability_map():
    ability_ids = fetch_opendota_json("constants/ability_ids") or {}
    abilities = fetch_opendota_json("constants/abilities") or {}
    ability_map = {}
    for ability_id, ability_key in ability_ids.items():
        ability = abilities.get(ability_key, {})
        display = ability.get("dname") or ability.get("name") or ability_key
        try:
            ability_map[int(ability_id)] = display
        except (TypeError, ValueError):
            pass
    return ability_map


def get_hero_name(hero_map, hero_id):
    return (hero_map.get(hero_id) or {}).get("name") or f"Hero {hero_id}"


def get_hero_image(hero_map, hero_id, kind="img"):
    return (hero_map.get(hero_id) or {}).get(kind)


@st.cache_data(ttl=900, show_spinner=False)
def get_opendota_player(account_id):
    return fetch_opendota_json(f"players/{account_id}") or {}


@st.cache_data(ttl=900, show_spinner=False)
def get_opendota_recent_matches(account_id, limit=20):
    matches = fetch_opendota_json(f"players/{account_id}/recentMatches") or []
    return matches[:limit]


@st.cache_data(ttl=900, show_spinner=False)
def get_opendota_win_loss(account_id):
    return fetch_opendota_json(f"players/{account_id}/wl") or {}


@st.cache_data(ttl=900, show_spinner=False)
def get_opendota_match(match_id):
    return fetch_opendota_json(f"matches/{match_id}") or {}


@st.cache_data(ttl=900, show_spinner=False)
def search_opendota_players(query):
    if not query or len(query.strip()) < 2:
        return []
    results = fetch_opendota_json("search", params={"q": query.strip()})
    return results if isinstance(results, list) else []


def build_dota_match_context(match_data, hero_map):
    if not match_data:
        return "No match data available."

    parts = []
    match_id = match_data.get("match_id")
    duration = match_data.get("duration")
    start_time = match_data.get("start_time")
    if match_id:
        parts.append(f"Match ID: {match_id}")
    if start_time:
        parts.append(f"Date: {datetime.utcfromtimestamp(start_time).strftime('%Y-%m-%d %H:%M')} UTC")
    if duration:
        parts.append(f"Duration: {round(duration / 60, 1)} minutes")

    radiant_win = match_data.get("radiant_win")
    radiant_score = match_data.get("radiant_score")
    dire_score = match_data.get("dire_score")
    if radiant_win is not None:
        parts.append(f"Winner: {'Radiant' if radiant_win else 'Dire'}")
    if radiant_score is not None and dire_score is not None:
        parts.append(f"Final kills: Radiant {radiant_score} — Dire {dire_score}")

    gold_adv = match_data.get("radiant_gold_adv") or []
    if gold_adv:
        lead_changes = [i for i in range(1, len(gold_adv)) if (gold_adv[i-1] <= 0 < gold_adv[i]) or (gold_adv[i-1] >= 0 > gold_adv[i])]
        if lead_changes:
            parts.append(f"Lead changes (minute): {', '.join(str(m) for m in lead_changes[:6])}")

    picks_bans = match_data.get("picks_bans") or []
    if picks_bans:
        rp, dp, rb, db = [], [], [], []
        for pb in picks_bans:
            name = get_hero_name(hero_map, pb.get("hero_id"))
            (rp if pb.get("is_pick") and pb.get("team") == 0 else dp if pb.get("is_pick") else rb if pb.get("team") == 0 else db).append(name)
        if rp or dp:
            parts.append(f"Radiant picks: {', '.join(rp) or 'n/a'}")
            parts.append(f"Dire picks: {', '.join(dp) or 'n/a'}")
        if rb or db:
            parts.append(f"Radiant bans: {', '.join(rb) or 'n/a'}")
            parts.append(f"Dire bans: {', '.join(db) or 'n/a'}")

    players = match_data.get("players") or []
    radiant_players = [p for p in players if p.get("isRadiant")]
    dire_players = [p for p in players if not p.get("isRadiant")]

    def fmt_player(p):
        hero = get_hero_name(hero_map, p.get("hero_id"))
        kda = f"{p.get('kills',0)}/{p.get('deaths',0)}/{p.get('assists',0)}"
        return (f"{hero} (L{p.get('level',0)}) K/D/A {kda} | GPM {p.get('gold_per_min',0)} "
                f"XPM {p.get('xp_per_min',0)} | NW {p.get('net_worth',0):,} | "
                f"Hero Dmg {p.get('hero_damage',0):,}")

    if radiant_players:
        parts.append("\nRadiant:")
        parts.extend([f"  {fmt_player(p)}" for p in radiant_players])
    if dire_players:
        parts.append("\nDire:")
        parts.extend([f"  {fmt_player(p)}" for p in dire_players])

    if gold_adv and len(gold_adv) > 30:
        early = sum(gold_adv[5:15]) / 10
        mid = sum(gold_adv[15:30]) / 15
        late = sum(gold_adv[30:]) / max(1, len(gold_adv[30:]))
        parts.append(f"\nGold advantage by phase (Radiant+): Early {early:.0f} | Mid {mid:.0f} | Late {late:.0f}")

    return "\n".join(parts)
