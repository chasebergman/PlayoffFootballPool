import pandas as pd
import requests
import re

TEST_YEAR = 2025 

ROSTERS = {
    "Chase": ["Puka Nacua", "Josh Jacobs", "Christian McCaffrey", "Brock Purdy", "George Kittle", "Trevor Lawrence", "Travis Etienne", "Parker Washington", "Brian Thomas Jr.", "Colby Parkinson", "Blake Corum", "Tetairoa McMillan", "Tyler Higbee", "Jaylen Warren"],
    "Dustin": ["Josh Allen", "A.J. Brown", "DeVonta Smith", "Dallas Goedert", "Dalton Kincaid", "Christian Watson", "Rhamondre Stevenson", "Jayden Reed", "Kenneth Gainwell", "Kenneth Walker III", "DK Metcalf", "Jordan Love", "Kayshon Boutte", "Justin Herbert"],
    "David": ["James Cook", "Saquon Barkley", "Jalen Hurts", "Khalil Shakir", "Caleb Williams", "DJ Moore", "Omarion Hampton", "Ladd McConkey", "Colston Loveland", "Dawson Knox", "Quentin Johnston", "Brandin Cooks", "Jahan Dotson", "Ty Johnson"],
    "Jack": ["Jaxon Smith-Njigba", "Drake Maye", "Davante Adams", "Trayveon Henderson", "Rome Odunze", "D'Andre Swift", "Sam Darnold", "Zach Charbonnet", "Luther Burden III", "Juaun Jennings", "Cooper Kupp", "Jayden Higgins", "Kyle Monangai", "Rasheed Shaheed"],
    "Ty": ["Matthew Stafford", "Kyren Williams", "Nico Collins", "Stefon Diggs", "Courtland Sutton", "RJ Harvey", "Hunter Henry", "Bo Nix", "Dalton Schultz", "Woody Marks", "Troy Franklin", "Ricky Pearsall", "CJ Stroud", "Jakobi Meyers"]
}

# EXTENDED MAP: Ensuring N/A never happens for your key players
POS_MAP = {
    # --- CHASE ---
    "Puka Nacua": "WR", "Josh Jacobs": "RB", "Christian McCaffrey": "RB", "Brock Purdy": "QB", 
    "George Kittle": "TE", "Trevor Lawrence": "QB", "Travis Etienne": "RB", "Parker Washington": "WR", 
    "Brian Thomas Jr.": "WR", "Colby Parkinson": "TE", "Blake Corum": "RB", "Tetairoa McMillan": "WR", 
    "Tyler Higbee": "TE", "Jaylen Warren": "RB",

    # --- DUSTIN ---
    "Josh Allen": "QB", "A.J. Brown": "WR", "DeVonta Smith": "WR", "Dallas Goedert": "TE", 
    "Dalton Kincaid": "TE", "Christian Watson": "WR", "Rhamondre Stevenson": "RB", "Jayden Reed": "WR", 
    "Kenneth Gainwell": "RB", "Kenneth Walker III": "RB", "DK Metcalf": "WR", "Jordan Love": "QB", 
    "Kayshon Boutte": "WR", "Justin Herbert": "QB",

    # --- DAVID ---
    "James Cook": "RB", "Saquon Barkley": "RB", "Jalen Hurts": "QB", "Khalil Shakir": "WR", 
    "Caleb Williams": "QB", "DJ Moore": "WR", "Omarion Hampton": "RB", "Ladd McConkey": "WR", 
    "Colston Loveland": "TE", "Dawson Knox": "TE", "Quentin Johnston": "WR", "Brandin Cooks": "WR", 
    "Jahan Dotson": "WR", "Ty Johnson": "RB",

    # --- JACK ---
    "Jaxon Smith-Njigba": "WR", "Drake Maye": "QB", "Davante Adams": "WR", "Trayveon Henderson": "RB", 
    "Rome Odunze": "WR", "D'Andre Swift": "RB", "Sam Darnold": "QB", "Zach Charbonnet": "RB", 
    "Luther Burden III": "WR", "Juaun Jennings": "WR", "Cooper Kupp": "WR", "Jayden Higgins": "WR", 
    "Kyle Monangai": "RB", "Rasheed Shaheed": "WR",

    # --- TY ---
    "Matthew Stafford": "QB", "Kyren Williams": "RB", "Nico Collins": "WR", "Stefon Diggs": "WR", 
    "Courtland Sutton": "WR", "RJ Harvey": "RB", "Hunter Henry": "TE", "Bo Nix": "QB", 
    "Dalton Schultz": "TE", "Woody Marks": "RB", "Troy Franklin": "WR", "Ricky Pearsall": "WR", 
    "CJ Stroud": "QB", "Jakobi Meyers": "WR"
}

def clean_name(name):
    return re.sub(r'[^a-z]', '', str(name).lower()) if name else ""

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
                            # Try API position, then our POS_MAP, default WR
                            p_pos = athlete['athlete'].get('position', {}).get('abbreviation')
                            if not p_pos or p_pos == "N/A": p_pos = POS_MAP.get(p_name, "WR")
                            player_stats[p_name] = {'Player': p_name, 'Pos': p_pos, 'pts': 0.0, 'clean': clean_name(p_name)}
                        
                        if cat_name == 'passing':
                            player_stats[p_name]['pts'] += (float(s.get('passingYards', 0)) * 0.04) + (float(s.get('passingTouchdowns', 0)) * 4) - (float(s.get('interceptions', 0)) * 2)
                        elif cat_name == 'rushing':
                            player_stats[p_name]['pts'] += (float(s.get('rushingYards', 0)) * 0.1) + (float(s.get('rushingTouchdowns', 0)) * 6)
                        elif cat_name == 'receiving':
                            player_stats[p_name]['pts'] += (float(s.get('receptions', 0)) * 1) + (float(s.get('receivingYards', 0)) * 0.1) + (float(s.get('receivingTouchdowns', 0)) * 6)
                        
                        if 'fumblesLost' in s:
                            player_stats[p_name]['pts'] -= (float(s.get('fumblesLost', 0)) * 2)
    except Exception: pass
    return pd.DataFrame(list(player_stats.values()))

# --- EXECUTION ---
cumulative = {name: 0 for name in ROSTERS}
for w_num, w_name in {1: "Wild Card"}.items():
    stats = get_stats_for_week(TEST_YEAR, w_num)
    print(f"\n{'='*65}\n🏈 {w_name.upper()} ROUND BREAKDOWN\n{'='*65}")
    
    for owner, roster in ROSTERS.items():
        clean_roster = [clean_name(p) for p in roster]
        # Build owner dataframe to ensure all players are present
        owner_df = pd.DataFrame({'Player': roster, 'clean': clean_roster})
        available = pd.merge(owner_df, stats[['clean', 'pts', 'Pos']], on='clean', how='left').fillna({'pts': 0, 'Pos': 'WR'})
        
        # Overwrite Pos again from our map if API gave us N/A or wrong info
        available['Pos'] = available['Player'].map(POS_MAP).fillna(available['Pos'])
        available = available.sort_values('pts', ascending=False)
        
        starters, used_idx = [], []
        
        # 1. QB (1)
        q = available[available['Pos'] == 'QB']
        if not q.empty: starters.append(("QB", q.iloc[0])); used_idx.append(q.index[0])
        
        # 2. RB (1)
        r = available[(available['Pos'] == 'RB') & (~available.index.isin(used_idx))]
        if not r.empty: starters.append(("RB", r.iloc[0])); used_idx.append(r.index[0])
        
        # 3. WR (2)
        w = available[(available['Pos'] == 'WR') & (~available.index.isin(used_idx))]
        for i in range(min(2, len(w))): starters.append(("WR", w.iloc[i])); used_idx.append(w.index[i])
        
        # 4. FLEX (2) - Logic: Any RB, WR, or TE left that has the highest points
        f = available[(~available.index.isin(used_idx)) & (available['Pos'].isin(['RB', 'WR', 'TE']))]
        for i in range(min(2, len(f))): starters.append(("FLEX", f.iloc[i])); used_idx.append(f.index[i])
        
        # Print Results
        print(f"\n🏠 {owner.upper()}'S ROSTER:")
        round_sum = sum(row['pts'] for slot, row in starters)
        for slot, row in starters:
            print(f"{slot.ljust(5)}: {row['Player'].ljust(18)} ({row['Pos']}) | {round(row['pts'], 2)} pts")
        print("-" * 45)
        bench = available[~available.index.isin(used_idx)]
        for _, row in bench.iterrows():
            print(f"BENCH: {row['Player'].ljust(18)} ({row['Pos']}) | {round(row['pts'], 2)} pts")
        cumulative[owner] += round_sum

    # STANDINGS
    leaderboard = pd.DataFrame([{"Owner": k, "Total": round(v, 2)} for k, v in cumulative.items()]).sort_values("Total", ascending=False)
    print(f"\n📊 STANDINGS\n" + "-"*35 + f"\n{leaderboard.to_string(index=False)}")