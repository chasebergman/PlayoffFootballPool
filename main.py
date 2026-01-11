import pandas as pd
import requests
import re
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="2026 Playoff Pool: LIVE", page_icon="🏈", layout="wide")

# 2. AUTO-REFRESH (Refreshes the script every 60 seconds)
st_autorefresh(interval=60000, key="fpl_refresh")

# 3. ROSTERS & POSITION MAPPING
TEST_YEAR = 2025 
ROSTERS = {
    "Chase": ["Puka Nacua", "Josh Jacobs", "Christian McCaffrey", "Brock Purdy", "George Kittle", "Trevor Lawrence", "Travis Etienne", "Parker Washington", "Brian Thomas Jr.", "Colby Parkinson", "Blake Corum", "Tetairoa McMillan", "Tyler Higbee", "Jaylen Warren"],
    "Dustin": ["Josh Allen", "A.J. Brown", "DeVonta Smith", "Dallas Goedert", "Dalton Kincaid", "Christian Watson", "Rhamondre Stevenson", "Jayden Reed", "Kenneth Gainwell", "Kenneth Walker III", "DK Metcalf", "Jordan Love", "Kayshon Boutte", "Justin Herbert"],
    "David": ["James Cook", "Saquon Barkley", "Jalen Hurts", "Khalil Shakir", "Caleb Williams", "DJ Moore", "Omarion Hampton", "Ladd McConkey", "Colston Loveland", "Dawson Knox", "Quentin Johnston", "Brandin Cooks", "Jahan Dotson", "Ty Johnson"],
    "Jack": ["Jaxon Smith-Njigba", "Drake Maye", "Davante Adams", "Trayveon Henderson", "Rome Odunze", "D'Andre Swift", "Sam Darnold", "Zach Charbonnet", "Luther Burden III", "Juaun Jennings", "Cooper Kupp", "Jayden Higgins", "Kyle Monangai", "Rasheed Shaheed"],
    "Ty": ["Matthew Stafford", "Kyren Williams", "Nico Collins", "Stefon Diggs", "Courtland Sutton", "RJ Harvey", "Hunter Henry", "Bo Nix", "Dalton Schultz", "Woody Marks", "Troy Franklin", "Ricky Pearsall", "CJ Stroud", "Jakobi Meyers"]
}

POS_MAP = {
    "Kyle Monangai": "RB", "Josh Jacobs": "RB", "Saquon Barkley": "RB", 
    "Christian McCaffrey": "RB", "James Cook": "RB", "Travis Etienne": "RB",
    "Rhamondre Stevenson": "RB", "Kenneth Walker III": "RB", "D'Andre Swift": "RB",
    "Kyren Williams": "RB", "Jaylen Warren": "RB", "Zach Charbonnet": "RB",
    "Woody Marks": "RB", "RJ Harvey": "RB", "Omarion Hampton": "RB", "Blake Corum": "RB"
}

def clean_name(name):
    return re.sub(r'[^a-z]', '', str(name).lower()) if name else ""

# 4. DATA FETCHING (Low TTL for live game updates)
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
                        
                        if cat_name == 'passing':
                            player_stats[p_name]['pts'] += (float(s.get('passingYards', 0)) * 0.04) + (float(s.get('passingTouchdowns', 0)) * 4) - (float(s.get('interceptions', 0)) * 2)
                        elif cat_name == 'rushing':
                            player_stats[p_name]['pts'] += (float(s.get('rushingYards', 0)) * 0.1) + (float(s.get('rushingTouchdowns', 0)) * 6)
                        elif cat_name == 'receiving':
                            player_stats[p_name]['pts'] += (float(s.get('receptions', 0)) * 1) + (float(s.get('receivingYards', 0)) * 0.1) + (float(s.get('receivingTouchdowns', 0)) * 6)
                        if 'fumblesLost' in s:
                            player_stats[p_name]['pts'] -= (float(s.get('fumblesLost', 0)) * 2)
    except: pass
    return pd.DataFrame(list(player_stats.values()))

# 5. CALCULATION & UI RENDER
st.title("🏈 2026 Playoff Pool Tracker")
st.markdown(f"**Last Sync:** {datetime.now().strftime('%I:%M:%S %p')} | Refresh: Every 60s")

cumulative_scores = {name: 0 for name in ROSTERS}
team_history = {name: [] for name in ROSTERS}

for w in range(1, 5):
    week_stats = get_stats_for_week(TEST_YEAR, w)
    if week_stats.empty: continue
    
    for owner, roster in ROSTERS.items():
        owner_df = pd.DataFrame({'Player': roster, 'clean': [clean_name(p) for p in roster]})
        available = pd.merge(owner_df, week_stats[['clean', 'pts', 'Pos']], on='clean', how='left').fillna(0)
        available['Pos'] = available['Player'].map(POS_MAP).fillna(available['Pos'])
        available = available.sort_values('pts', ascending=False)
        
        starters, used_idx = [], []
        for pos in ['QB', 'RB']:
            m = available[(available['Pos'] == pos) & (~available.index.isin(used_idx))]
            if not m.empty: starters.append((pos, m.iloc[0])); used_idx.append(m.index[0])
        
        wr_pool = available[(available['Pos'] == 'WR') & (~available.index.isin(used_idx))]
        for i in range(min(2, len(wr_pool))):
            starters.append(("WR", wr_pool.iloc[i])); used_idx.append(wr_pool.index[i])
            
        flex_pool = available[(~available.index.isin(used_idx)) & (available['Pos'].isin(['RB', 'WR', 'TE']))]
        for i in range(min(2, len(flex_pool))):
            starters.append(("FLEX", flex_pool.iloc[i])); used_idx.append(flex_pool.index[i])
            
        week_pts = sum(row['pts'] for slot, row in starters)
        cumulative_scores[owner] += week_pts
        team_history[owner].append({"week": w, "pts": week_pts, "starters": starters})

# Display Standings
st.divider()
lb_df = pd.DataFrame([{"Owner": k, "Total Score": round(v, 2)} for k, v in cumulative_scores.items()]).sort_values("Total Score", ascending=False)
st.subheader("🏆 Leaderboard")
st.table(lb_df)

# Display Individual Team Tabs
st.divider()
tabs = st.tabs(list(ROSTERS.keys()))
for i, (owner, history) in enumerate(team_history.items()):
    with tabs[i]:
        st.metric("Total Playoff Points", round(cumulative_scores[owner], 1))
        for entry in history:
            round_name = {1: "Wild Card", 2: "Divisional", 3: "Conference", 4: "Super Bowl"}.get(entry['week'])
            with st.expander(f"{round_name} Breakdown"):
                st.table(pd.DataFrame([{"Slot": s, "Player": r['Player'], "Pts": round(r['pts'], 1)} for s, r in entry['starters']]))
