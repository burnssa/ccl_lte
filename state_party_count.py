import json
import requests
import csv
import os
import pandas as pd
import pdb

STATE_PARTY_CSV = 'data/STATE_PARTY.csv'

PARTY_URL = 'https://api.propublica.org/congress/v1/states/members/party.json'
API_KEY = os.environ['PROPUBLICA_API_KEY']

headers = {'X-API-Key': API_KEY}

response = requests.get(PARTY_URL, headers=headers)
parsed_response = json.loads(response.content)

house = parsed_response['results']['house']
senate = parsed_response['results']['senate']

house_df = pd.DataFrame()
senate_df = pd.DataFrame()

def congress_value(state, party):
    reps = filter(None, [value.get(party) for value in state.values()[0]])
    if len(reps) == 0:
        return 0
    else:
        return int(reps[0])

for i, state in enumerate(house):
    house_df.loc[i, 'state'] = state.keys()[0]
    house_df.loc[i, 'house_rep'] = congress_value(state, 'REP')
    house_df.loc[i, 'house_dem'] = congress_value(state, 'DEM')

for i, state in enumerate(senate):
    senate_df.loc[i, 'state'] = state.keys()[0]
    senate_df.loc[i, 'senate_rep'] = congress_value(state, 'REP')
    senate_df.loc[i, 'senate_dem'] = congress_value(state, 'DEM')

congress_df = house_df.merge(senate_df, on='state')
print congress_df

congress_df.to_csv(STATE_PARTY_CSV)
