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

ELIMINATED_TEAMS = ['GB', 'SF', 'BUF', 'PIT', 'JAX', 'CAR', 'LAC', 'PHI']

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
st.title("🏈 2026 Playoff Pool Tracker")
st.markdown(f"**Last Sync:** {datetime.now().strftime('%I:%M:%S %p')}")

cumulative_scores = {name: 0 for name in ROSTERS}
team_history = {name: [] for name in ROSTERS}

for w in range(1, 5):
    week_stats = get_stats_for_week(TEST_YEAR, w)
    if week_stats.empty: continue
    
    for owner, roster in ROSTERS.items():
        owner_df = pd.DataFrame({'Player': roster, 'clean': [clean_name(p) for p in roster]})
        pool = pd.merge(owner_df, week_stats[['clean', 'pts', 'Pos']], on='clean', how='left').fillna(0)
        pool['Pos'] = pool['Player'].map(POS_MAP).fillna(pool['Pos'])
        pool['Team'] = pool['Player'].map(TEAM_MAP).fillna('')
        pool['Team'] = pool['Team'].apply(lambda t: f"{t} ❌" if t in ELIMINATED_TEAMS else t)
        
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

# Custom CSS for centered text in tables
st.markdown("""
<style>
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
        text-align: center !important;
    }
    [data-testid="stTable"] td, [data-testid="stTable"] th {
        text-align: center !important;
    }
</style>
""", unsafe_allow_html=True)

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
                    st.dataframe(
                        pd.DataFrame(entry['starters']),
                        hide_index=True,
                        column_config={
                            "Slot": st.column_config.TextColumn("Slot", width="small"),
                            "Player": st.column_config.TextColumn("Player", width="medium"),
                            "Team": st.column_config.TextColumn("Team", width="small"),
                            "Pts": st.column_config.NumberColumn("Pts", width="small", format="%.2f"),
                        }
                    )
                with c2:
                    st.write("**🪑 Bench**")
                    st.dataframe(
                        entry['bench'][['Player', 'Team', 'Pos', 'pts']],
                        hide_index=True,
                        column_config={
                            "Player": st.column_config.TextColumn("Player", width="medium"),
                            "Team": st.column_config.TextColumn("Team", width="small"),
                            "Pos": st.column_config.TextColumn("Pos", width="small"),
                            "pts": st.column_config.NumberColumn("Pts", width="small", format="%.2f"),
                        }
                    )
