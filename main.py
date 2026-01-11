import pandas as pd
import requests
import re
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# 1. PAGE SETUP: Wide layout for a professional dashboard feel
st.set_page_config(page_title="2026 Playoff Pool", page_icon="🏈", layout="wide")

# 2. AUTO-REFRESH: Automatically refreshes the app every 60 seconds
st_autorefresh(interval=60000, key="datarefresh")

# 3. CONFIG & ROSTERS
TEST_YEAR = 2025 

ROSTERS = {
    "Chase": ["Puka Nacua", "Josh Jacobs", "Christian McCaffrey", "Brock Purdy", "George Kittle", "Trevor Lawrence", "Travis Etienne", "Parker Washington", "Brian Thomas Jr.", "Colby Parkinson", "Blake Corum", "Tetairoa McMillan", "Tyler Higbee", "Jaylen Warren"],
    "Dustin": ["Josh Allen", "A.J. Brown", "DeVonta Smith", "Dallas Goedert", "Dalton Kincaid", "Christian Watson", "Rhamondre Stevenson", "Jayden Reed", "Kenneth Gainwell", "Kenneth Walker III", "DK Metcalf", "Jordan Love", "Kayshon Boutte", "Justin Herbert"],
    "David": ["James Cook", "Saquon Barkley", "Jalen Hurts", "Khalil Shakir", "Caleb Williams", "DJ Moore", "Omarion Hampton", "Ladd McConkey", "Colston Loveland", "Dawson Knox", "Quentin Johnston", "Brandin Cooks", "Jahan Dotson", "Ty Johnson"],
    "Jack": ["Jaxon Smith-Njigba", "Drake Maye", "Davante Adams", "Trayveon Henderson", "Rome Odunze", "D'Andre Swift", "Sam Darnold", "Zach Charbonnet", "Luther Burden III", "Juaun Jennings", "Cooper Kupp", "Jayden Higgins", "Kyle Monangai", "Rasheed Shaheed"],
    "Ty": ["Matthew Stafford", "Kyren Williams", "Nico Collins", "Stefon Diggs", "Courtland Sutton", "RJ Harvey", "Hunter Henry", "Bo Nix", "Dalton Schultz", "Woody Marks", "Troy Franklin", "Ricky Pearsall", "CJ Stroud", "Jakobi Meyers"]
}

POS_MAP = {
    "Puka Nacua": "WR", "Josh Jacobs": "RB", "Christian McCaffrey": "RB", "Brock Purdy": "QB", 
    "George Kittle": "TE", "Trevor Lawrence": "QB", "Travis Etienne": "RB", "Parker Washington": "WR", 
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
    "Sam Darnold": "QB", "Zach Charbonnet": "RB", "Luther Burden III": "WR", "Juaun Jennings": "WR", 
    "Cooper Kupp": "WR", "Jayden Higgins": "WR", "Kyle Monangai": "RB", "Rasheed Shaheed": "WR",
    "Matthew Stafford": "QB", "Kyren Williams": "RB", "Nico Collins": "WR", "Stefon Diggs": "WR", 
    "Courtland Sutton": "WR", "RJ Harvey": "RB", "Hunter Henry": "TE", "Bo Nix": "QB", 
    "Dalton Schultz": "TE", "Woody Marks": "RB", "Troy Franklin": "WR", "Ricky Pearsall": "WR", 
    "CJ Stroud": "QB", "Jakobi Meyers": "WR"
}

def clean_name(name):
    return re.sub(r'[^a-z]', '', str(name).lower()) if name else ""

@st.cache_data(ttl=300) # Prevents spamming ESPN; updates every 5 mins
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
                            if p_pos == "N/A": p_pos = POS_MAP.get(p_name, "WR")
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

# --- UI START ---
st.title("🏈 2026 Playoff Pool: LIVE")
st.markdown(f"**Current Round:** Wild Card | **Last Sync:** {datetime.now().strftime('%I:%M %p')}")

# --- CALCULATION LOGIC ---
cumulative = {name: 0 for name in ROSTERS}
team_breakdowns = {}

stats = get_stats_for_week(TEST_YEAR, 1)

for owner, roster in ROSTERS.items():
    clean_roster = [clean_name(p) for p in roster]
    owner_df = pd.DataFrame({'Player': roster, 'clean': clean_roster})
    available = pd.merge(owner_df, stats[['clean', 'pts', 'Pos']], on='clean', how='left').fillna({'pts': 0})
    available['Pos'] = available['Player'].map(POS_MAP).fillna(available['Pos'])
    available = available.sort_values('pts', ascending=False)
    
    starters, used_idx = [], []
    for pos in ['QB', 'RB']:
        m = available[(available['Pos'] == pos) & (~available.index.isin(used_idx))]
        if not m.empty: starters.append((pos, m.iloc[0])); used_idx.append(m.index[0])
    
    w = available[(available['Pos'] == 'WR') & (~available.index.isin(used_idx))]
    for i in range(min(2, len(w))): starters.append(("WR", w.iloc[i])); used_idx.append(w.index[i])
    
    f = available[(~available.index.isin(used_idx)) & (available['Pos'].isin(['RB', 'WR', 'TE']))]
    for i in range(min(2, len(f))): starters.append(("FLEX", f.iloc[i])); used_idx.append(f.index[i])
    
    round_sum = sum(row['pts'] for slot, row in starters)
    cumulative[owner] += round_sum
    team_breakdowns[owner] = {"score": round_sum, "starters": starters, "bench": available[~available.index.isin(used_idx)]}

# --- RENDER UI ---
st.divider()
leaderboard_df = pd.DataFrame([{"Owner": k, "Score": round(v, 2)} for k, v in cumulative.items()]).sort_values("Score", ascending=False)

col1, col2 = st.columns([1, 2])
with col1:
    st.subheader("🏆 Leaderboard")
    st.table(leaderboard_df)
with col2:
    st.subheader("📊 Momentum")
    st.bar_chart(leaderboard_df.set_index("Owner"))

st.divider()
st.subheader("🏠 Team Rosters")
# Create a grid: 5 columns for 5 owners
team_cols = st.columns(len(ROSTERS))
for i, (owner, data) in enumerate(team_breakdowns.items()):
    with team_cols[i]:
        st.info(f"**{owner.upper()}**")
        st.metric("Total", f"{round(data['score'], 1)} pts")
        
        # Starters Table
        s_table = pd.DataFrame([{"Slot": s, "Player": r['Player'], "Pts": round(r['pts'], 1)} for s, r in data['starters']])
        st.dataframe(s_table, hide_index=True)
        
        with st.expander("View Bench"):
            b_table = pd.DataFrame([{"Player": r['Player'], "Pts": round(r['pts'], 1)} for _, r in data['bench'].iterrows()])
            st.dataframe(b_table, hide_index=True)
