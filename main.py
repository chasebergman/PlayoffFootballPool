import pandas as pd
import requests
import re
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="2026 Playoff Pool: LIVE", page_icon="🏈", layout="wide")
st_autorefresh(interval=60000, key="fpl_refresh")

# 2. CONFIG & ROSTERS
TEST_YEAR = 2025 
ROSTERS = {
    "Chase": ["Puka Nacua", "Josh Jacobs", "Christian McCaffrey", "Brock Purdy", "George Kittle", "Trevor Lawrence", "Travis Etienne Jr.", "Parker Washington", "Brian Thomas Jr.", "Colby Parkinson", "Blake Corum", "Tetairoa McMillan", "Tyler Higbee", "Jaylen Warren"],
    "Dustin": ["Josh Allen", "A.J. Brown", "DeVonta Smith", "Dallas Goedert", "Dalton Kincaid", "Christian Watson", "Rhamondre Stevenson", "Jayden Reed", "Kenneth Gainwell", "Kenneth Walker III", "DK Metcalf", "Jordan Love", "Kayshon Boutte", "Justin Herbert"],
    "David": ["James Cook", "Saquon Barkley", "Jalen Hurts", "Khalil Shakir", "Caleb Williams", "DJ Moore", "Omarion Hampton", "Ladd McConkey", "Colston Loveland", "Dawson Knox", "Quentin Johnston", "Brandin Cooks", "Jahan Dotson", "Ty Johnson"],
    "Jack": ["Jaxon Smith-Njigba", "Drake Maye", "Davante Adams", "TreVeyon Henderson", "Rome Odunze", "D'Andre Swift", "Sam Darnold", "Zach Charbonnet", "Luther Burden III", "Jauan Jennings", "Cooper Kupp", "Jayden Higgins", "Kyle Monangai", "Rashid Shaheed"],
    "Ty": ["Matthew Stafford", "Kyren Williams", "Nico Collins", "Stefon Diggs", "Courtland Sutton", "RJ Harvey", "Hunter Henry", "Bo Nix", "Dalton Schultz", "Woody Marks", "Troy Franklin", "Ricky Pearsall", "CJ Stroud", "Jakobi Meyers"]
}

POS_MAP = {
    "Puka Nacua": "WR", "Josh Jacobs": "RB", "Christian McCaffrey": "RB", "Brock Purdy": "QB", 
    "George Kittle": "TE", "Trevor Lawrence": "QB", "Travis Etienne Jr.": "RB", "Parker Washington": "WR", 
    "Brian Thomas Jr.": "WR", "Colby Parkinson": "TE", "Blake Corum": "RB", "Tetairoa McMillan": "WR", 
    "Tyler Higbee": "TE", "Jaylen Warren": "RB", "Josh Allen": "QB", "A.J. Brown": "WR", 
    "DeVonta Smith": "WR", "Dallas Goedert": "TE", "Dalton Kincaid": "TE", "Christian Watson": "WR", 
    "Rhamondre Stevenson": "RB", "Jayden Reed": "WR", "Kenneth Gainwell": "RB", "Kenneth Walker III": "RB", 
    "DK Metcalf": "WR", "Jordan Love": "QB", "Kayshon Boutte": "WR", "Justin Herbert": "QB",
    "James Cook": "RB", "Saquon Barkley": "RB", "Jalen Hurts": "QB", "Khalil Shakir": "WR", 
    "Caleb Williams": "QB", "DJ Moore": "WR", "Omarion Hampton": "RB", "Ladd McConkey": "WR", 
    "Colston Loveland": "TE", "Dawson Knox": "TE", "Quentin Johnston": "WR", "Brandin Cooks": "WR", 
    "Jahan Dotson": "WR", "Ty Johnson": "RB", "Jaxon Smith-Njigba": "WR", "Drake Maye": "QB", 
    "Davante Adams": "WR", "TreVeyon Henderson": "RB", "Rome Odunze": "WR", "D'Andre Swift": "RB", 
    "Sam Darnold": "QB", "Zach Charbonnet": "RB", "Luther Burden III": "WR", "Jauan Jennings": "WR", 
    "Cooper Kupp": "WR", "Jayden Higgins": "WR", "Kyle Monangai": "RB", "Rashid Shaheed": "WR",
    "Matthew Stafford": "QB", "Kyren Williams": "RB", "Nico Collins": "WR", "Stefon Diggs": "WR", 
    "Courtland Sutton": "WR", "RJ Harvey": "RB", "Hunter Henry": "TE", "Bo Nix": "QB", 
    "Dalton Schultz": "TE", "Woody Marks": "RB", "Troy Franklin": "WR", "Ricky Pearsall": "WR", 
    "CJ Stroud": "QB", "Jakobi Meyers": "WR"
}

TEAM_MAP = {
    "Puka Nacua": "LAR", "Josh Jacobs": "GB", "Christian McCaffrey": "SF", "Brock Purdy": "SF",
    "George Kittle": "SF", "Trevor Lawrence": "JAX", "Travis Etienne Jr.": "JAX", "Parker Washington": "JAX",
    "Brian Thomas Jr.": "JAX", "Colby Parkinson": "LAR", "Blake Corum": "LAR", "Tetairoa McMillan": "CAR",
    "Tyler Higbee": "LAR", "Jaylen Warren": "PIT", "Josh Allen": "BUF", "A.J. Brown": "PHI",
    "DeVonta Smith": "PHI", "Dallas Goedert": "PHI", "Dalton Kincaid": "BUF", "Christian Watson": "GB",
    "Rhamondre Stevenson": "NE", "Jayden Reed": "GB", "Kenneth Gainwell": "PHI", "Kenneth Walker III": "SEA",
    "DK Metcalf": "PIT", "Jordan Love": "GB", "Kayshon Boutte": "NE", "Justin Herbert": "LAC",
    "James Cook": "BUF", "Saquon Barkley": "PHI", "Jalen Hurts": "PHI", "Khalil Shakir": "BUF",
    "Caleb Williams": "CHI", "DJ Moore": "CHI", "Omarion Hampton": "LAC", "Ladd McConkey": "LAC",
    "Colston Loveland": "CHI", "Dawson Knox": "BUF", "Quentin Johnston": "LAC", "Brandin Cooks": "BUF",
    "Jahan Dotson": "PHI", "Ty Johnson": "BUF", "Jaxon Smith-Njigba": "SEA", "Drake Maye": "NE",
    "Davante Adams": "LAR", "TreVeyon Henderson": "NE", "Rome Odunze": "CHI", "D'Andre Swift": "CHI",
    "Sam Darnold": "SEA", "Zach Charbonnet": "SEA", "Luther Burden III": "CHI", "Jauan Jennings": "SF",
    "Cooper Kupp": "SEA", "Jayden Higgins": "HOU", "Kyle Monangai": "CHI", "Rashid Shaheed": "SEA",
    "Matthew Stafford": "LAR", "Kyren Williams": "LAR", "Nico Collins": "HOU", "Stefon Diggs": "NE",
    "Courtland Sutton": "DEN", "RJ Harvey": "DEN", "Hunter Henry": "NE", "Bo Nix": "DEN",
    "Dalton Schultz": "HOU", "Woody Marks": "HOU", "Troy Franklin": "DEN", "Ricky Pearsall": "SF",
    "CJ Stroud": "HOU", "Jakobi Meyers": "JAX"
}

WILDCARD_ELIMINATED_TEAMS = ['GB', 'PIT', 'JAX', 'CAR', 'LAC', 'PHI']
DIVISIONAL_ELIMINATED_TEAMS = ['BUF', 'SF']
ALL_ELIMINATED_TEAMS = WILDCARD_ELIMINATED_TEAMS + DIVISIONAL_ELIMINATED_TEAMS

def get_elimination_tag(team):
    if team in WILDCARD_ELIMINATED_TEAMS:
        return f"{team} ❌ᵂᶜ"
    elif team in DIVISIONAL_ELIMINATED_TEAMS:
        return f"{team} ❌ᴰⁱᵛ"
    return team

def clean_name(name):
    return re.sub(r'[^a-z]', '', str(name).lower()) if name else ""

# 3. DATA FETCHING
@st.cache_data(ttl=120) 
def get_stats_for_week(year, week):
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={year}&seasontype=3&week={week}"
    player_stats = {}
    try:
        data = requests.get(url).json()
        for game in data.get('events', []):
            if game.get('status', {}).get('type', {}).get('name') == "STATUS_SCHEDULED": continue
            res = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={game['id']}").json()
            for team in res.get('boxscore', {}).get('players', []):
                for cat in team.get('statistics', []):
                    cat_name, keys = cat['name'].lower(), cat['keys']
                    for athlete in cat['athletes']:
                        p_name = athlete['athlete']['displayName']
                        s = dict(zip(keys, athlete['stats']))
                        if p_name not in player_stats:
                            p_pos = athlete['athlete'].get('position', {}).get('abbreviation', "WR")
                            player_stats[p_name] = {'Player': p_name, 'Pos': p_pos, 'pts': 0.0, 'clean': clean_name(p_name)}
                        
                        # OFFENSIVE SCORING
                        if cat_name == 'passing':
                            player_stats[p_name]['pts'] += (float(s.get('passingYards', 0)) * 0.04) + (float(s.get('passingTouchdowns', 0)) * 4) - (float(s.get('interceptions', 0)) * 2)
                        elif cat_name == 'rushing':
                            player_stats[p_name]['pts'] += (float(s.get('rushingYards', 0)) * 0.1) + (float(s.get('rushingTouchdowns', 0)) * 6)
                        elif cat_name == 'receiving':
                            player_stats[p_name]['pts'] += (float(s.get('receptions', 0)) * 1) + (float(s.get('receivingYards', 0)) * 0.1) + (float(s.get('receivingTouchdowns', 0)) * 6)
                        
                        # SPECIAL TEAMS SCORING (The Shaheed Rule)
                        elif 'return' in cat_name:
                            # ESPN uses different keys for return TDs depending on game type
                            rt_tds = float(s.get('touchdowns', 0)) + float(s.get('kickReturnTouchdowns', 0)) + float(s.get('puntReturnTouchdowns', 0))
                            player_stats[p_name]['pts'] += (rt_tds * 6)

                        if 'fumblesLost' in s:
                            player_stats[p_name]['pts'] -= (float(s.get('fumblesLost', 0)) * 2)
    except: pass
    return pd.DataFrame(list(player_stats.values()))

# 4. BEST BALL ENGINE
cumulative_scores = {name: 0 for name in ROSTERS}
team_history = {name: [] for name in ROSTERS}
active_players = {name: 0 for name in ROSTERS}

for w in range(1, 5):
    week_stats = get_stats_for_week(TEST_YEAR, w)
    if week_stats.empty: continue
    
    for owner, roster in ROSTERS.items():
        owner_df = pd.DataFrame({'Player': roster, 'clean': [clean_name(p) for p in roster]})
        pool = pd.merge(owner_df, week_stats[['clean', 'pts', 'Pos']], on='clean', how='left').fillna(0)
        pool['Pos'] = pool['Player'].map(POS_MAP).fillna(pool['Pos'])
        pool['Team'] = pool['Player'].map(TEAM_MAP).fillna('')
        pool['Eliminated'] = pool['Team'].isin(ALL_ELIMINATED_TEAMS)
        pool['Team'] = pool['Team'].apply(get_elimination_tag)
        
        # Count active players (not eliminated)
        active_players[owner] = len(pool[~pool['Eliminated']])
        
        pool = pool.sort_values('pts', ascending=False)
        starters, used_idx = [], []

        # 1. Mandatory Slots
        for pos, count in [('QB', 1), ('RB', 1), ('WR', 2)]:
            matched = pool[(pool['Pos'] == pos) & (~pool.index.isin(used_idx))].head(count)
            for _, row in matched.iterrows():
                starters.append({"Slot": pos, "Player": row['Player'], "Team": row['Team'], "Pts": round(row['pts'], 2)})
                used_idx.append(row.name)

        # 2. FLEX (RB/WR/TE)
        flex_eligible = pool[(pool['Pos'].isin(['RB', 'WR', 'TE'])) & (~pool.index.isin(used_idx))].head(2)
        for _, row in flex_eligible.iterrows():
            starters.append({"Slot": "FLEX", "Player": row['Player'], "Team": row['Team'], "Pts": round(row['pts'], 2)})
            used_idx.append(row.name)
            
        bench = pool[~pool.index.isin(used_idx)].sort_values('pts', ascending=False).copy()
        bench['pts'] = bench['pts'].round(2)
        
        week_total = sum(s['Pts'] for s in starters)
        cumulative_scores[owner] += week_total
        team_history[owner].append({"week": w, "pts": week_total, "starters": starters, "bench": bench})

# 5. UI RENDER

# Clean, modern CSS with focus on whitespace and hierarchy
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    
    /* Global resets and base */
    .stApp {
        font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    section[data-testid="stSidebar"] { display: none; }
    
    .block-container {
        padding: 2rem 1rem 4rem 1rem;
        max-width: 1100px;
    }
    
    @media (min-width: 768px) {
        .block-container {
            padding: 3rem 2rem 5rem 2rem;
        }
    }
    
    /* Header */
    .site-header {
        text-align: center;
        padding: 2.5rem 1rem 3rem 1rem;
    }
    
    @media (min-width: 768px) {
        .site-header {
            padding: 3.5rem 2rem 4rem 2rem;
        }
    }
    
    .site-header .emoji {
        font-size: 3rem;
        margin-bottom: 0.75rem;
        display: block;
    }
    
    .site-header h1 {
        font-size: 2rem;
        font-weight: 700;
        color: forestgreen;
        margin: 0 0 0.5rem 0;
        letter-spacing: -0.5px;
    }
    
    @media (min-width: 768px) {
        .site-header h1 {
            font-size: 2.75rem;
        }
    }
    
    .site-header .tagline {
        color: #71717a;
        font-size: 0.875rem;
        font-weight: 500;
        letter-spacing: 0.5px;
    }
    
    .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        padding: 0.35rem 0.75rem;
        border-radius: 100px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-top: 1rem;
    }
    
    .live-badge .dot {
        width: 6px;
        height: 6px;
        background: #ef4444;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.4; }
    }
    
    /* Section headers */
    .section-label {
        font-size: 0.7rem;
        font-weight: 600;
        color: #71717a;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 1.25rem;
    }
    
    /* Standings rows */
    .standing-row {
        margin-bottom: 0.75rem;
        display: grid;
        grid-template-columns: auto 1fr auto auto;
        align-items: center;
        gap: 1rem;
        padding: 1rem 1.25rem;
        background: #18181b;
        border-radius: 12px;
        border: 1px solid #27272a;
        transition: border-color 0.2s ease;
    }
    
    @media (min-width: 768px) {
        .standing-row {
            padding: 1.25rem 1.5rem;
            gap: 1.5rem;
        }
    }
    
    .standing-row:hover {
        border-color: #3f3f46;
    }
    
    .standing-row.leader {
        background: linear-gradient(135deg, #1c1917 0%, #18181b 100%);
        border-color: #ca8a04;
    }
    
    .rank {
        font-size: 1.1rem;
        font-weight: 700;
        color: #a1a1aa;
        width: 28px;
        text-align: center;
    }
    
    .rank.first { color: #facc15; }
    .rank.second { color: #d1d5db; }
    .rank.third { color: #d97706; }
    
    .owner-info {
        display: flex;
        flex-direction: column;
        gap: 0.2rem;
        min-width: 0;
    }
    
    .owner-name {
        font-size: 1rem;
        font-weight: 600;
        color: #fafafa;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    @media (min-width: 768px) {
        .owner-name {
            font-size: 1.1rem;
        }
    }
    
    .owner-meta {
        font-size: 0.75rem;
        color: #71717a;
    }
    
    .active-tag {
        color: #4ade80;
    }
    
    .score-block {
        text-align: right;
    }
    
    .score-value {
        font-size: 1.35rem;
        font-weight: 700;
        color: #fafafa;
        letter-spacing: -0.5px;
    }
    
    @media (min-width: 768px) {
        .score-value {
            font-size: 1.5rem;
        }
    }
    
    .score-diff {
        font-size: 0.75rem;
        color: #71717a;
        font-weight: 500;
    }
    
    .score-diff.behind { color: #ef4444; }
    
    /* Divider */
    .section-divider {
        height: 1px;
        background: #27272a;
        margin: 2rem 0;
    }
    
    @media (min-width: 768px) {
        .section-divider {
            margin: 3rem 0;
        }
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: #18181b;
        border-radius: 10px;
        padding: 0.35rem;
        border: 1px solid #27272a;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-family: 'DM Sans', sans-serif;
        font-weight: 600;
        font-size: 0.875rem;
        color: #71717a;
        background: transparent;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        border: none;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #a1a1aa;
        background: #27272a;
    }
    
    .stTabs [aria-selected="true"] {
        color: #fafafa !important;
        background: #27272a !important;
    }
    
    .stTabs [data-baseweb="tab-highlight"] {
        display: none;
    }
    
    .stTabs [data-baseweb="tab-border"] {
        display: none;
    }
    
    /* Metrics */
    [data-testid="stMetric"] {
        background: #18181b;
        border: 1px solid #27272a;
        border-radius: 10px;
        padding: 1rem 1.25rem;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem;
        font-weight: 500;
        color: #71717a;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: 700;
        color: #fafafa;
    }
    
    /* Expanders */
    [data-testid="stExpander"] {
        border: 1px solid #27272a !important;
        border-radius: 10px !important;
        background: #18181b !important;
        margin-bottom: 0.75rem;
    }
    
    [data-testid="stExpander"] details {
        background: #18181b !important;
    }
    
    [data-testid="stExpander"] summary {
        font-family: 'DM Sans', sans-serif;
        font-weight: 600;
        font-size: 0.95rem;
        color: #fafafa !important;
        padding: 1rem 1.25rem;
        background: #18181b !important;
    }
    
    [data-testid="stExpander"] summary:hover {
        background: #1f1f23 !important;
    }
    
    [data-testid="stExpander"] summary svg {
        color: #71717a !important;
    }
    
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        padding: 0 1.25rem 1.25rem 1.25rem;
        background: #18181b !important;
    }
    
    [data-testid="stExpander"] > div {
        background: #18181b !important;
    }
    
    /* Table headers */
    .table-label {
        font-size: 0.7rem;
        font-weight: 600;
        color: #71717a;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.75rem;
        padding-left: 0.25rem;
    }
    
    /* DataFrames */
    [data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
    }
    
    [data-testid="stDataFrame"] td, 
    [data-testid="stDataFrame"] th {
        text-align: center !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu, footer, header { visibility: hidden; }
    
    /* Custom hr */
    hr {
        border: none;
        border-top: 1px solid #27272a;
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ============ HEADER ============
st.markdown(f"""
<div class="site-header">
    <span class="emoji">🏈</span>
    <h1>Playoff Pool 2026</h1>
    <div class="tagline">Best Ball • PPR Scoring</div>
    <div class="live-badge">
        <span class="dot"></span>
        LIVE · {datetime.now().strftime('%I:%M %p')}
    </div>
</div>
""", unsafe_allow_html=True)

# ============ STANDINGS ============
sorted_owners = sorted(cumulative_scores.items(), key=lambda x: x[1], reverse=True)
leader_score = sorted_owners[0][1] if sorted_owners else 0

st.markdown('<p class="section-label">Standings</p>', unsafe_allow_html=True)

for rank, (owner, score) in enumerate(sorted_owners, 1):
    rank_class = "first" if rank == 1 else "second" if rank == 2 else "third" if rank == 3 else ""
    row_class = "leader" if rank == 1 else ""
    rank_display = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else str(rank)
    
    gap = score - leader_score
    if gap == 0:
        diff_text = "Leader"
        diff_class = ""
    else:
        diff_text = f"{gap:.1f}"
        diff_class = "behind"
    
    active = active_players.get(owner, 0)
    
    st.markdown(f"""<div class="standing-row {row_class}">
        <div class="rank {rank_class}">{rank_display}</div>
        <div class="owner-info">
            <div class="owner-name">{owner}</div>
            <div class="owner-meta"><span class="active-tag">{active} active</span> · 14 rostered</div>
        </div>
        <div class="score-block">
            <div class="score-value">{score:.2f}</div>
            <div class="score-diff {diff_class}">{diff_text}</div>
        </div>
    </div>""", unsafe_allow_html=True)

# ============ TEAM DETAILS ============
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.markdown('<p class="section-label">Team Rosters</p>', unsafe_allow_html=True)

tabs = st.tabs([owner for owner, _ in sorted_owners])

for i, (owner, _) in enumerate(sorted_owners):
    history = team_history[owner]
    with tabs[i]:
        
        # Compact stats summary
        weeks_played = len([h for h in history if h['pts'] > 0])
        eliminated = 14 - active_players[owner]
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 1.5rem; padding: 1rem 1.25rem; background: #18181b; border: 1px solid #27272a; border-radius: 10px; margin: 1rem 0 1.5rem 0; flex-wrap: wrap;">
            <div style="display: flex; align-items: baseline; gap: 0.4rem;">
                <span style="font-size: 1.5rem; font-weight: 700; color: #fafafa;">{cumulative_scores[owner]:.2f}</span>
                <span style="font-size: 0.75rem; color: #71717a; text-transform: uppercase;">pts</span>
            </div>
            <div style="width: 1px; height: 24px; background: #27272a;"></div>
            <div style="display: flex; align-items: baseline; gap: 0.4rem;">
                <span style="font-size: 1.1rem; font-weight: 600; color: #4ade80;">{active_players[owner]}</span>
                <span style="font-size: 0.75rem; color: #71717a;">active</span>
                <span style="font-size: 0.75rem; color: #71717a; margin: 0 0.25rem;">·</span>
                <span style="font-size: 1.1rem; font-weight: 600; color: #ef4444;">{eliminated}</span>
                <span style="font-size: 0.75rem; color: #71717a;">eliminated</span>
            </div>
            <div style="width: 1px; height: 24px; background: #27272a;"></div>
            <div style="display: flex; align-items: baseline; gap: 0.4rem;">
                <span style="font-size: 1.1rem; font-weight: 600; color: #fafafa;">{weeks_played}</span>
                <span style="font-size: 0.75rem; color: #71717a;">weeks scored</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Week breakdown
        for entry in history:
            week_labels = {1: "Wild Card", 2: "Divisional", 3: "Conference", 4: "Super Bowl"}
            week_icons = {1: "🎴", 2: "⚔️", 3: "👑", 4: "🏆"}
            
            is_latest = entry['week'] == max(e['week'] for e in history)
            label = f"{week_icons[entry['week']]}  {week_labels[entry['week']]}  —  {entry['pts']:.2f} pts"
            
            with st.expander(label, expanded=is_latest):
                st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                
                with c1:
                    st.markdown('<p class="table-label">Starting Lineup</p>', unsafe_allow_html=True)
                    st.dataframe(
                        pd.DataFrame(entry['starters']),
                        hide_index=True,
                        use_container_width=True,
                        column_config={
                            "Slot": st.column_config.TextColumn("POS", width="small"),
                            "Player": st.column_config.TextColumn("Player", width="medium"),
                            "Team": st.column_config.TextColumn("Team", width="small"),
                            "Pts": st.column_config.NumberColumn("PTS", width="small", format="%.1f"),
                        }
                    )
                
                with c2:
                    st.markdown('<p class="table-label">Bench</p>', unsafe_allow_html=True)
                    st.dataframe(
                        entry['bench'][['Player', 'Team', 'Pos', 'pts']],
                        hide_index=True,
                        use_container_width=True,
                        column_config={
                            "Player": st.column_config.TextColumn("Player", width="medium"),
                            "Team": st.column_config.TextColumn("Team", width="small"),
                            "Pos": st.column_config.TextColumn("POS", width="small"),
                            "pts": st.column_config.NumberColumn("PTS", width="small", format="%.1f"),
                        }
                    )
                
                st.markdown("<div style='height: 0.25rem'></div>", unsafe_allow_html=True)