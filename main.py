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
    "Jack": ["Jaxon Smith-Njigba", "Drake Maye", "Davante Adams", "Trayveon Henderson", "Rome Odunze", "D'Andre Swift", "Sam Darnold", "Zach Charbonnet", "Luther Burden III", "Jauan Jennings", "Cooper Kupp", "Jayden Higgins", "Kyle Monangai", "Rasheed Shaheed"],
    "Ty": ["Matthew Stafford", "Kyren Williams", "Nico Collins", "Stefon Diggs", "Courtland Sutton", "RJ Harvey", "Hunter Henry", "Bo Nix", "Dalton Schultz", "Woody Marks", "Troy Franklin", "Ricky Pearsall", "CJ Stroud", "Jakobi Meyers"]
}

# Manual Position overrides to ensure QB/RB/WR/TE logic is ironclad
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
    "Davante Adams": "WR", "Trayveon Henderson": "RB", "Rome Odunze": "WR", "D'Andre Swift": "RB", 
    "Sam Darnold": "QB", "Zach Charbonnet": "RB", "Luther Burden III": "WR", "Jauan Jennings": "WR", 
    "Cooper Kupp": "WR", "Jayden Higgins": "WR", "Kyle Monangai": "RB", "Rasheed Shaheed": "WR",
    "Matthew Stafford": "QB", "Kyren Williams": "RB", "Nico Collins": "WR", "Stefon Diggs": "WR", 
    "Courtland Sutton": "WR", "RJ Harvey": "RB", "Hunter Henry": "TE", "Bo Nix": "QB", 
    "Dalton Schultz": "TE", "Woody Marks": "RB", "Troy Franklin": "WR", "Ricky Pearsall": "WR", 
    "CJ Stroud": "QB", "Jakobi Meyers": "WR"
}

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

# 4. BEST BALL ENGINE
st.title("🏈 2026 Playoff Pool Tracker")
st.markdown(f"**Last Sync:** {datetime.now().strftime('%I:%M:%S %p')}")

cumulative_scores = {name: 0 for name in ROSTERS}
team_history = {name: [] for name in ROSTERS}

for w in range(1, 5):
    week_stats = get_stats_for_week(TEST_YEAR, w)
    if week_stats.empty: continue
    
    for owner, roster in ROSTERS.items():
        owner_df = pd.DataFrame({'Player': roster, 'clean': [clean_name(p) for p in roster]})
        # Merge roster with stats and filter positions
        pool = pd.merge(owner_df, week_stats[['clean', 'pts', 'Pos']], on='clean', how='left').fillna(0)
        pool['Pos'] = pool['Player'].map(POS_MAP).fillna(pool['Pos'])
        
        # KEY FIX: Always sort by points BEFORE selecting positions
        pool = pool.sort_values('pts', ascending=False)
        
        starters, used_idx = [], []

        # 1. Mandatory Slots: Picks the highest scoring available player for each
        for pos, count in [('QB', 1), ('RB', 1), ('WR', 2)]:
            matched = pool[(pool['Pos'] == pos) & (~pool.index.isin(used_idx))].head(count)
            for _, row in matched.iterrows():
                starters.append({"Slot": pos, "Player": row['Player'], "Pts": row['pts']})
                used_idx.append(row.name)

        # 2. FLEX (RB/WR/TE ONLY - No QB allowed)
        flex_eligible = pool[(pool['Pos'].isin(['RB', 'WR', 'TE'])) & (~pool.index.isin(used_idx))].head(2)
        for _, row in flex_eligible.iterrows():
            starters.append({"Slot": "FLEX", "Player": row['Player'], "Pts": row['pts']})
            used_idx.append(row.name)
            
        # 3. BENCH
        bench = pool[~pool.index.isin(used_idx)].sort_values('pts', ascending=False)
        
        week_total = sum(s['Pts'] for s in starters)
        cumulative_scores[owner] += week_total
        team_history[owner].append({"week": w, "pts": week_total, "starters": starters, "bench": bench})

# 5. UI RENDER
lb_df = pd.DataFrame([{"Owner": k, "Total": round(v, 2)} for k, v in cumulative_scores.items()]).sort_values("Total", ascending=False)
st.subheader("🏆 Leaderboard")
st.table(lb_df)

st.divider()
tabs = st.tabs(list(ROSTERS.keys()))
for i, (owner, history) in enumerate(team_history.items()):
    with tabs[i]:
        st.metric("Total Score", f"{round(cumulative_scores[owner], 1)} pts")
        for entry in history:
            label = {1:"Wild Card", 2:"Divisional", 3:"Championship", 4:"Super Bowl"}[entry['week']]
            with st.expander(f"{label} ({round(entry['pts'], 1)} pts)"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write("**✅ Starters**")
                    st.dataframe(pd.DataFrame(entry['starters']), hide_index=True)
                with c2:
                    st.write("**🪑 Bench**")
                    st.dataframe(entry['bench'][['Player', 'Pos', 'pts']], hide_index=True)
