import streamlit as st
from api_client import FootballAPIClient
from llm_processor import MatchPredictor
from dotenv import load_dotenv

load_dotenv()

# Initialize components
api_client = FootballAPIClient()
predictor = MatchPredictor()

# Initialize session state
if 'prediction_history' not in st.session_state:
    st.session_state.prediction_history = []
if 'form_reset' not in st.session_state:
    st.session_state.form_reset = False

def render_form():
    print("Starting render_form")  # Debug
    # League options
    leagues = {
        "Premier League": 39,
        "La Liga": 140,
        "Serie A": 135,
        "EFL League One": 40,
        "PSL (South Africa)": 186
    }
    selected_league = st.selectbox("Select League", list(leagues.keys()))
    league_id = leagues[selected_league]
    
    # Mock fixtures for demo
    mock_fixtures = {
        "Premier League": [("Southampton", "Aston Villa"), ("Manchester City", "Crystal Palace"), ("Arsenal", "Chelsea"), ("Liverpool", "Manchester United"), ("Tottenham", "West Ham")],
        "La Liga": [("Barcelona", "Real Madrid"), ("Atlético Madrid", "Sevilla"), ("Villarreal", "Valencia"), ("Real Betis", "Celta Vigo")],
        "Serie A": [("Juventus", "Inter Milan"), ("AC Milan", "Napoli"), ("Roma", "Lazio"), ("Fiorentina", "Atalanta")],
        "EFL League One": [("Birmingham City", "Wrexham"), ("Huddersfield Town", "Stockport County"), ("Lincoln City", "Bolton"), ("Charlton Athletic", "Barnsley")],
        "PSL (South Africa)": [("Mamelodi Sundowns", "Orlando Pirates"), ("Kaizer Chiefs", "Cape Town City"), ("Stellenbosch", "SuperSport United"), ("Sekhukhune United", "AmaZulu")]
    }
    mock_pairs = mock_fixtures[selected_league]
    match_options = ["Enter teams manually"] + [f"{home} vs {away}" for home, away in mock_pairs]

    with st.form("prediction_form"):
        match_select = st.selectbox("Select Match or Enter Manually", match_options, key="match_select")
        manual_entry = match_select == "Enter teams manually"
        
        col1, col2 = st.columns(2)
        with col1:
            team1 = st.text_input("Team 1", placeholder=f"e.g., {mock_fixtures[selected_league][0][0]}", value="", key=f"team1_{st.session_state.form_reset}", disabled=not manual_entry)
        with col2:
            team2 = st.text_input("Team 2", placeholder=f"e.g., {mock_fixtures[selected_league][0][1]}", value="", key=f"team2_{st.session_state.form_reset}", disabled=not manual_entry)
        
        col_submit, col_reset = st.columns(2)
        with col_submit:
            submitted = st.form_submit_button("Predict Winner")
        with col_reset:
            reset = st.form_submit_button("New Prediction")

        if submitted:
            print(f"Form submitted: team1={team1}, team2={team2}, manual={manual_entry}")  # Debug
            if manual_entry and (not team1 or not team2):
                st.error("Please enter both team names!")
                return
            
            selected_teams = [team1.strip(), team2.strip()] if manual_entry else match_select.split(" vs ")
            if len(selected_teams) != 2:
                st.error("Invalid match selection!")
                return
            
            team1, team2 = selected_teams
            print(f"Selected teams: {team1} vs {team2}")  # Debug
            with st.spinner("Analyzing club match data..."):
                # Get team IDs
                team1_id = api_client.get_team_id(team1, league_id)
                team2_id = api_client.get_team_id(team2, league_id)
                
                if not team1_id or not team2_id:
                    st.error(f"Team not found: {team1 if not team1_id else team2}")
                    return
                
                print(f"Team IDs: {team1_id} vs {team2_id}")  # Debug
                # Fetch stats
                team1_stats = api_client.get_team_stats(team1_id, league_id)
                team2_stats = api_client.get_team_stats(team2_id, league_id)
                h2h = api_client.get_head_to_head(team1_id, team2_id)
                
                print(f"Stats: team1={team1_stats}, team2={team2_stats}, h2h={h2h}")  # Debug
                # Safely access stats
                team1_form = team1_stats.get('form', 'Unknown') if team1_stats else 'Unknown'
                team2_form = team2_stats.get('form', 'Unknown') if team2_stats else 'Unknown'
                team1_corners = "Unknown"
                team2_corners = "Unknown"
                if team1_stats and team1_stats.get('fixtures', {}).get('played', {}).get('total', 0) > 0:
                    team1_corners = team1_stats.get('fixtures', {}).get('corners', {}).get('total', 0) / team1_stats['fixtures']['played']['total']
                if team2_stats and team2_stats.get('fixtures', {}).get('played', {}).get('total', 0) > 0:
                    team2_corners = team2_stats.get('fixtures', {}).get('corners', {}).get('total', 0) / team2_stats['fixtures']['played']['total']
                
                # Safely calculate H2H
                team1_wins = 0
                team2_wins = 0
                if h2h:
                    for match in h2h:
                        if match.get('teams', {}).get('home', {}).get('id') == team1_id and match.get('teams', {}).get('home', {}).get('winner'):
                            team1_wins += 1
                        if match.get('teams', {}).get('away', {}).get('id') == team2_id and match.get('teams', {}).get('away', {}).get('winner'):
                            team2_wins += 1
                
                stats = f"""
                Club Match Data ({selected_league}, 2024/25 Season):
                - {team1} Form (Last 5): {team1_form}
                - {team2} Form (Last 5): {team2_form}
                - Head-to-Head (Recent):
                  * {team1} Wins: {team1_wins}
                  * {team2} Wins: {team2_wins}
                - Avg Corners: {team1_corners} ({team1}), {team2_corners} ({team2})
                """
                
                print(f"Stats string: {stats}")  # Debug
                # Display logos (placeholders, as mock fixtures lack logos)
                col1, col2 = st.columns(2)
                with col1:
                    st.image("https://via.placeholder.com/100?text=" + team1.replace(" ", "+"), caption=team1, width=100)
                with col2:
                    st.image("https://via.placeholder.com/100?text=" + team2.replace(" ", "+"), caption=team2, width=100)
                
                # Generate prediction
                prediction = predictor.predict_match(team1, team2, stats)
                prediction_text = prediction.content if hasattr(prediction, 'content') else str(prediction)
                
                print(f"Prediction text: {prediction_text}")  # Debug
                st.success("### Prediction Result")
                try:
                    pred_part = prediction_text.split('Prediction: ')[1].split('Score: ')[0].strip()
                    score_part = prediction_text.split('Score: ')[1].split('Corners: ')[0].strip()
                    corners_part = prediction_text.split('Corners: ')[1].split('Shots: ')[0].strip()
                    shots_part = prediction_text.split('Shots: ')[1].split('Reasoning: ')[0].strip()
                    reason_part = prediction_text.split('Reasoning: ')[1].strip()
                    
                    st.markdown(f"**Winner:** {pred_part}")
                    st.markdown(f"**Predicted Score:** {score_part}")
                    st.markdown(f"**Total Corners:** {corners_part}")
                    st.markdown(f"**Total Shots:** {shots_part}")
                    st.info(f"**Reasoning:** {reason_part}")
                    
                    st.session_state.prediction_history.append({
                        "team1": team1,
                        "team2": team2,
                        "prediction": pred_part,
                        "score": score_part,
                        "corners": corners_part,
                        "shots": shots_part,
                        "reasoning": reason_part
                    })
                except IndexError as e:
                    print(f"Prediction parsing error: {e}")  # Debug
                    st.error(f"Prediction format error: {e}")
                    st.markdown(f"**Raw Prediction:** {prediction_text}")
                    st.session_state.prediction_history.append({
                        "team1": team1,
                        "team2": team2,
                        "prediction": prediction_text,
                        "reasoning": "Format error"
                    })

        if reset:
            st.session_state.form_reset = not st.session_state.form_reset
            st.rerun()

# Streamlit UI setup
st.set_page_config(page_title="Club Match Predictor", page_icon="⚽", layout="wide")
st.title("⚽ AI Club Football Predictor")
st.markdown("Predict club match outcomes for the 2024/25 season in Premier League, La Liga, Serie A, EFL League One, or PSL (South Africa), powered by GPT-4o.")

# Sidebar for past predictions
with st.sidebar:
    st.header("Recent Predictions")
    for entry in st.session_state.prediction_history[-5:]:
        st.markdown(f"**{entry['team1']} vs {entry['team2']}**")
        st.write(f"Winner: {entry['prediction']}")
        st.write(f"Score: {entry.get('score', 'N/A')}")
        st.write(f"Corners: {entry.get('corners', 'N/A')}")
        st.write(f"Shots: {entry.get('shots', 'N/A')}")
        st.write(f"Reasoning: {entry['reasoning']}")
        st.markdown("---")
    if st.button("Clear History"):
        st.session_state.prediction_history = []

# Render the form
render_form()