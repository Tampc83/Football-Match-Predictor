import os
import requests
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

class FootballAPIClient:
    def __init__(self):
        self.base_url = "https://api-football-v1.p.rapidapi.com/v3"
        self.api_key = os.getenv("FOOTBALL_API_KEY")
        if not self.api_key:
            raise ValueError("FOOTBALL_API_KEY not set in .env!")
        self.headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
        }
        # Fallback team IDs for common clubs
        self.fallback_team_ids = {
            "premier league": {
                "southampton": 41,
                "aston villa": 66,
                "manchester city": 50,
                "crystal palace": 52,
                "arsenal": 42,
                "chelsea": 49,
                "liverpool": 40,
                "manchester united": 33
            },
            "la liga": {
                "barcelona": 529,
                "real madrid": 541
            },
            "serie a": {
                "juventus": 496,
                "inter milan": 505
            },
            "efl league one": {
                "birmingham city": 332,
                "wrexham": 346
            },
            "psl (south africa)": {
                "mamelodi sundowns": 1007,
                "orlando pirates": 1010
            }
        }

    def get_team_stats(self, team_id, league_id, season=2024):
        """Fetch stats for a team in a league."""
        url = f"{self.base_url}/teams/statistics"
        params = {"team": team_id, "league": league_id, "season": season}
        print(f"Requesting stats: {url} with params {params}")
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()["response"]
            print(f"Stats response: {data}")
            return data
        except requests.RequestException as e:
            print(f"Stats API error: {e}")
            st.error(f"Failed to fetch stats: {str(e)}")
            return None

    def get_head_to_head(self, team1_id, team2_id):
        """Fetch head-to-head stats."""
        url = f"{self.base_url}/fixtures/headtohead"
        params = {"h2h": f"{team1_id}-{team2_id}"}
        print(f"Requesting H2H: {url} with params {params}")
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()["response"]
            print(f"H2H response: {data}")
            return data
        except requests.RequestException as e:
            print(f"H2H API error: {e}")
            st.error(f"Failed to fetch H2H: {str(e)}")
            return []

    def get_team_id(self, team_name, league_id):
        """Search for a team’s ID by name and league."""
        team_name = team_name.strip().lower()
        # Map league_id to league name for fallback
        league_map = {
            39: "premier league",
            140: "la liga",
            135: "serie a",
            40: "efl league one",
            186: "psl (south africa)"
        }
        league_name = league_map.get(league_id, "unknown")
        
        # Check fallback first
        if league_name in self.fallback_team_ids and team_name in self.fallback_team_ids[league_name]:
            team_id = self.fallback_team_ids[league_name][team_name]
            print(f"Using fallback team ID for {team_name}: {team_id}")
            return team_id
        
        # API search
        url = f"{self.base_url}/teams"
        params = {"search": team_name}  # Removed league filter to broaden search
        print(f"Requesting team ID: {url} with params {params}")
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()["response"]
            print(f"Team ID response: {data}")
            for team in data:
                if team["team"]["name"].lower() == team_name:
                    return team["team"]["id"]
            st.warning(f"No team found for '{team_name}' in league ID {league_id}.")
            return None
        except requests.RequestException as e:
            print(f"Team ID API error: {e}")
            st.error(f"Failed to fetch team ID for {team_name}: {str(e)}")
            return None