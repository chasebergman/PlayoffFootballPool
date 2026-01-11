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
# Note: Kyle Monangai spelling is strictly enforced here.
TEST_YEAR = 2025 
ROSTERS = {
    "Chase": ["Puka Nacua", "Josh Jacobs", "Christian McCaffrey", "Brock Purdy", "George Kittle", "Trevor Lawrence", "Travis Etienne", "Parker Washington", "Brian Thomas Jr.", "Colby Parkinson", "Blake Corum", "Tetairoa McMillan", "Tyler Higbee", "Jaylen Warren"],
    "Dustin": ["Josh Allen", "A.J. Brown", "DeVonta Smith", "Dallas Goedert", "Dalton Kincaid", "Christian Watson", "Rhamondre Stevenson", "Jayden Reed", "Kenneth Gainwell", "Kenneth Walker III", "DK Metcalf", "Jordan Love", "Kayshon Boutte", "Justin Herbert"],
    "David": ["James Cook", "Saquon Barkley", "Jalen Hurts", "Khalil Shakir", "Caleb Williams", "DJ Moore", "Omarion Hampton", "Ladd McConkey", "Colston Loveland", "Dawson Knox", "Quentin Johnston", "Brandin Cooks", "Jahan Dotson", "Ty Johnson"],
    "Jack": ["Jaxon Smith-Njigba", "Drake Maye", "Davante Adams", "Trayveon Henderson", "Rome Odunze", "D'Andre Swift", "Sam Darnold", "Zach Charbonnet", "Luther Burden III", "Juaun Jennings", "Cooper Kupp", "Jayden Higgins", "Kyle Monangai", "Rasheed Shaheed"],
    "Ty": ["Matthew Stafford", "Kyren Williams", "Nico Collins", "Stefon Diggs", "Courtland Sutton", "RJ Harvey", "Hunter Henry", "Bo Nix", "Dalton Schultz", "Woody Marks", "Troy Franklin", "Ricky Pearsall", "CJ Stroud", "Jakobi Meyers"]
}

# Ensure RBs are mapped correctly for Flex/RB logic
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
    # seasontype=3 is Postseason; weeks 1-4 cover Wild Card to Super Bowl
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
                            player_stats[p_name]['pts'] += (float(s.get('passingYards', 0)) * 0.04) + (float(s.get('passingTouchdowns
