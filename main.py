import pandas as pd
import requests
import re
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="2026 Playoff Pool: LIVE", page_icon="🏈", layout="wide")
st_autorefresh(interval=60000, key="fpl_refresh")

# 2. CONFIG & ELIMINATED TEAMS (Update this list as rounds end)
TEST_YEAR = 2025 
ELIMINATED_TEAMS = ["JAX", "GB", "PHI", "PIT", "LAC", "CAR", "BUF", "SF"]

# 3. ROSTERS & PLAYER DATA (Position, Team)
PLAYER_DATA = {
    "Puka Nacua": ("WR", "LAR"), "Josh Jacobs": ("RB", "GB"), "Christian McCaffrey": ("RB", "SF"), 
    "Brock Purdy": ("QB", "SF"), "George Kittle": ("TE", "SF"), "Trevor Lawrence": ("QB", "JAX"), 
    "Travis Etienne Jr.": ("RB", "JAX"), "Parker Washington": ("WR", "JAX"), "Brian Thomas Jr.": ("WR", "JAX"), 
    "Colby Parkinson": ("TE", "LAR"), "Blake Corum": ("RB", "LAR"), "Tetairoa McMillan": ("WR", "ARI"), 
    "Tyler Higbee": ("TE", "LAR"), "Jaylen Warren": ("RB", "PIT"), "Josh Allen": ("QB", "BUF"), 
    "A.J. Brown": ("WR", "PHI"), "DeVonta Smith": ("WR", "PHI"), "Dallas Goedert": ("TE", "PHI"), 
    "Dalton Kincaid": ("TE", "BUF"), "Christian Watson": ("WR", "GB"), "Rhamondre Stevenson": ("RB", "NE"), 
    "Jayden Reed": ("WR", "GB"), "Kenneth Gainwell": ("RB", "PHI"), "Kenneth Walker III": ("RB", "SEA"), 
    "DK Metcalf": ("WR", "SEA"), "Jordan Love": ("QB", "GB"), "Kayshon Boutte": ("WR", "NE"), 
    "Justin Herbert": ("QB", "LAC"), "James Cook": ("RB", "BUF"), "Saquon Barkley": ("RB", "PHI"), 
    "Jalen Hurts": ("QB", "PHI"), "Khalil Shakir": ("WR", "BUF"), "Caleb Williams": ("QB", "CHI"), 
    "DJ Moore": ("WR", "CHI"), "Omarion Hampton": ("RB", "CHI"), "Ladd McConkey": ("WR", "LAC"), 
    "Colston Loveland": ("TE", "DET"), "Dawson Knox": ("TE", "BUF"), "Quentin Johnston": ("WR", "LAC"), 
    "Brandin Cooks": ("WR", "DAL"), "Jahan Dotson": ("WR", "PHI"), "Ty Johnson": ("RB", "BUF"), 
    "Jaxon Smith-Njigba": ("WR", "SEA"), "Drake Maye": ("QB", "NE"), "Davante Adams": ("WR", "NYJ"), 
    "Trayveon Henderson": ("RB", "OSU"), "Rome Odunze": ("WR", "CHI"), "D'Andre Swift": ("RB", "CHI"), 
    "Sam Darnold": ("QB", "SEA"), "Zach Charbonnet": ("RB", "SEA"), "Luther Burden III": ("WR", "MIZ"), 
    "Jauan Jennings": ("WR", "SF"), "Cooper Kupp": ("WR", "LAR"), "Jayden Higgins": ("WR", "ISU"), 
    "Kyle Monangai": ("RB", "RUT"), "Rashid Shaheed": ("WR", "NO"), "Matthew Stafford": ("QB", "LAR"), 
    "Kyren Williams": ("RB", "LAR"), "Nico Collins": ("WR", "HOU"), "Stefon Diggs": ("WR", "HOU"), 
    "Courtland Sutton": ("WR", "DEN"), "RJ Harvey": ("RB", "UCF"), "Hunter Henry": ("TE", "NE"), 
    "Bo Nix": ("QB", "DEN"), "Dalton Schultz": ("TE", "HOU"), "Woody Marks": ("RB", "USC"), 
    "Troy Franklin": ("WR", "DEN"), "Ricky Pearsall": ("WR", "SF"), "CJ Stroud": ("QB", "HOU"), 
    "Jakobi Meyers": ("WR", "LV")
}

ROSTERS = {
    "Chase": ["Puka Nacua", "Josh Jacobs", "Christian McCaffrey", "Brock Purdy", "George Kittle", "Trevor Lawrence", "Travis Etienne Jr.", "Parker Washington", "Brian Thomas Jr.", "Colby Parkinson", "Blake Corum", "Tetairoa McMillan", "Tyler Higbee", "Jaylen Warren"],
    "Dustin": ["Josh Allen", "A.J. Brown", "DeVonta Smith", "Dallas Goedert", "Dalton Kincaid", "Christian Watson", "Rhamondre Stevenson", "Jayden Reed", "Kenneth Gainwell", "Kenneth Walker III", "DK Metcalf", "Jordan Love", "Kayshon Boutte", "Justin Herbert"],
    "David": ["James Cook", "Saquon Barkley", "Jalen Hurts", "Khalil Shakir", "Caleb Williams", "DJ Moore", "Omarion Hampton", "Ladd McConkey", "Colston Loveland", "Dawson Knox", "Quentin Johnston", "Brandin Cooks", "Jahan Dotson", "Ty Johnson"],
    "Jack": ["Jaxon Smith-Njigba", "Drake Maye", "Davante Adams", "Trayveon Henderson", "Rome Odunze", "D'Andre Swift", "Sam Darnold", "Zach Charbonnet", "Luther Burden III", "Jauan Jennings", "Cooper Kupp", "Jayden Higgins", "Kyle Monangai", "Rashid Shaheed"],
    "Ty": ["Matthew Stafford", "Kyren Williams", "Nico Collins", "Stefon Diggs", "Courtland Sutton", "RJ Harvey", "Hunter Henry", "Bo Nix", "Dalton Schultz", "Woody Marks", "Troy Franklin", "Ricky Pearsall", "CJ Stroud", "Jakobi Meyers"]
}

def clean_name(name):
    return re.sub(r'[^a-z]', '', str(name).lower()) if name else ""

# 4. DATA FETCHING
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
                            player_stats[p_name] = {'Player': p_name, 'pts': 0.0, 'clean': clean_name(p_name)}
                        
                        if cat_name == 'passing':
                            player_stats[p_name]['pts'] += (float(s.get('passingYards', 0)) * 0.04) + (float(s.get('passingTouchdowns', 0)) * 4) - (float(s.get('interceptions', 0)) * 2)
                        elif cat_name == 'rushing':
                            player_stats[p_name]['pts'] += (float(s.get('rushingYards', 0)) * 0.1) + (float(s.get('rushingTouchdowns', 0)) * 6)
                        elif cat_name == 'receiving':
                            player_stats[p_name]['pts'] += (float(s.get('receptions', 0)) * 1) + (float(s.get('receivingYards', 0)) * 0.1) + (float(s.get('receivingTouchdowns', 0)) * 6)
                        # SPECIAL TEAMS ADDITION (The Rashid Shaheed Rule)
                        elif cat_name in ['kickreturns', 'puntreturns']:
                            player_stats[p_name]['pts'] += (float(s.get('touchdowns', 0)) * 6)

                        if 'fumblesLost' in s:
                            player_stats[p_name]['pts'] -= (float(s.get('fumblesLost', 0)) * 2)
    except: pass
    return pd.DataFrame(list(player_stats.values()))

# 5. ENGINE
st.title("🏈 2026 Playoff Pool Tracker")
st.markdown(f"**Round:** Divisional | **Last Sync:** {datetime.now().strftime('%I:%M:%S %p')}")

cumulative_scores = {name: 0 for name in ROSTERS}
team_history = {name: [] for name in ROSTERS}

for w in range(1, 5):
    week_stats = get_stats_for_week(TEST_YEAR, w)
    if week_stats is None or week_stats.empty: continue
    
    for owner, roster in ROSTERS.items():
        owner_df = pd.DataFrame({'Player': roster, 'clean': [clean_name(p) for p in roster]})
        pool = pd.merge(owner_df, week_stats[['clean', 'pts']], on='clean', how='left').fillna(0)
        
        # Mapping Positions, Teams, and Elimination Status
        pool['Pos'] = pool['Player'].apply(lambda x: PLAYER_DATA.get(x, ("WR", "N/A"))[0])
        pool['Team'] = pool['Player'].apply(lambda x: PLAYER_DATA.get(x, ("WR", "N/A"))[1])
        pool['Status'] = pool['Team'].apply(lambda x: "❌" if x in ELIMINATED_TEAMS else "✅")
        
        pool = pool.sort_values('pts', ascending=False)
        starters, used_idx = [], []

        for pos, count in [('QB', 1), ('RB', 1), ('WR', 2)]:
            matched = pool[(pool['Pos'] == pos) & (~pool.index.isin(used_idx))].head(count)
            for _, row in matched.iterrows():
                starters.append({"Slot": pos, "Status": row['Status'], "Player": row['Player'], "Team": row['Team'], "Pts": row['pts']})
                used_idx.append(row.name)

        flex_eligible = pool[(pool['Pos'].isin(['RB', 'WR', 'TE'])) & (~pool.index.isin(used_idx))].head(2)
        for _, row in flex_eligible.iterrows():
            starters.append({"Slot": "FLEX", "Status": row['Status'], "Player": row['Player'], "Team": row['Team'], "Pts": row['pts']})
            used_idx.append(row.name)
            
        bench = pool[~pool.index.isin(used_idx)].sort_values('pts', ascending=False)
        week_total = sum(s['Pts'] for s in starters)
        cumulative_scores[owner] += week_total
        team_history[owner].append({"week": w, "pts": week_total, "starters": starters, "bench": bench})

# 6. UI RENDER
lb_df = pd.DataFrame([{"Owner": k, "Total": round(v, 2)} for k, v in cumulative_scores.items()]).sort_values("Total", ascending=False)
st.subheader("🏆 Leaderboard")
st.table(lb_df)

st.divider()
tabs = st.tabs(list(ROSTERS.keys()))
for i, (owner, history) in enumerate(team_history.items()):
    with tabs[i]:
        st.metric("Total Score", f"{round(cumulative_scores[owner], 2)} pts")
        for entry in history:
            label = {1:"Wild Card", 2:"Divisional", 3:"Championship", 4:"Super Bowl"}[entry['week']]
            with st.expander(f"{label} ({round(entry['pts'], 2)} pts)"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write("**✅ Starters**")
                    st.dataframe(pd.DataFrame(entry['starters']), hide_index=True)
                with c2:
                    st.write("**🪑 Bench**")
                    st.dataframe(entry['bench'][['Status', 'Player', 'Team', 'Pos', 'pts']], hide_index=True)
