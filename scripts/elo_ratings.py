import os
import pandas as pd
import json

INITIAL_RATING = 1200
K = 32
USE_SCORE_DIFFERENCE = False

input_csv_directory = 'input_csv'

all_data = []

player_stats = {}
player_ratings = {}
match_results = []

def expected_score(rating1, rating2):
    return 1 / (1 + 10 ** ((rating2 - rating1) / 400))

for filename in os.listdir(input_csv_directory):
    if filename.endswith(".csv"):
        filepath = os.path.join(input_csv_directory, filename)
        df = pd.read_csv(filepath, header=None)
        all_data.append(df)

combined_df = pd.concat(all_data, ignore_index=True)
combined_df[5] = pd.to_datetime(combined_df[5], format='%Y-%m-%d')
combined_df = combined_df.sort_values(by=5)
        
for index, row in combined_df.iterrows():
    date = row[5]
    player1_team1 = row[6]
    player2_team1 = row[9]
    player1_team2 = row[12]
    player2_team2 = row[15]
    score_team1 = row[19]
    score_team2 = row[20]

    if score_team1 == 0 and score_team2 == 0:
        continue

    match_results.append({
        'date': date.strftime('%Y-%m-%d'),
        'team1': [player1_team1, player2_team1],
        'team2': [player1_team2, player2_team2],
        'score_team1': score_team1,
        'score_team2': score_team2
    })
    
    for player in [player1_team1, player2_team1, player1_team2, player2_team2]:
        if player not in player_stats:
            player_stats[player] = {
                'current_rating': 1200,
                'rating_history': []
            }
            player_ratings[player] = 1200
    
    # Calculate team ratings
    team1_rating = (player_stats[player1_team1]['current_rating'] + player_stats[player2_team1]['current_rating']) / 2
    team2_rating = (player_stats[player1_team2]['current_rating'] + player_stats[player2_team2]['current_rating']) / 2
    
    # Calculate expected scores
    exp_team1 = expected_score(team1_rating, team2_rating)
    exp_team2 = expected_score(team2_rating, team1_rating)
    
    # Determine actual scores
    if score_team1 > score_team2:
        actual_team1 = 1
        actual_team2 = 0
    elif score_team1 < score_team2:
        actual_team1 = 0
        actual_team2 = 1
    else:
        actual_team1 = 0.5
        actual_team2 = 0.5

    score_diff = abs(score_team1 - score_team2)
    if USE_SCORE_DIFFERENCE:
        # Impact factor based on the score difference (you can adjust the scaling factor as needed)
        impact_factor = 1 + (score_diff / 10)
        team1_rating_change = impact_factor * K * (actual_team1 - exp_team1)
        team2_rating_change = impact_factor * K * (actual_team2 - exp_team2)
    else:
        team1_rating_change = K * (actual_team1 - exp_team1)
        team2_rating_change = K * (actual_team2 - exp_team2)

    rating_changes = {}
    for player in [player1_team1, player2_team1]:
        rating_changes[player] = team1_rating_change * (player_stats[player]['current_rating'] / team1_rating)
        player_stats[player]['current_rating'] += rating_changes[player]

    for player in [player1_team2, player2_team2]:
        rating_changes[player] = team2_rating_change * (player_stats[player]['current_rating'] / team2_rating)
        player_stats[player]['current_rating'] += rating_changes[player]                
    
    for player in [player1_team1, player2_team1, player1_team2, player2_team2]:
        rating = round(player_stats[player]['current_rating'])
        player_ratings[player] = rating

        if player in [player1_team1, player2_team1]:
            partner = player1_team1 if player == player2_team1 else player2_team1
        else:
            partner = player1_team2 if player == player2_team2 else player2_team2


        player_stats[player]['rating_history'].append({
            'date': date.strftime('%Y-%m-%d'),
            'rating': rating,
            'rating_change': round(rating_changes[player]),
            'partner': partner,
            'score': score_team1 if player in [player1_team1, player2_team1] else score_team2,
            'opponents': [player1_team2, player2_team2] if player in [player1_team1, player2_team1] else [player1_team1, player2_team1],
            'opponent_score': score_team2 if player in [player1_team1, player2_team1] else score_team1,
        })


with open('output_json/player_ratings.json', 'w') as f:
    json.dump(player_ratings, f)
with open('output_json/player_stats.json', 'w') as f:
    json.dump(player_stats, f)
with open('output_json/match_results.json', 'w') as f:
    json.dump(match_results, f)