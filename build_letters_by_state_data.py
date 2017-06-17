import sqlalchemy
from sqlalchemy import *
import pdb
import pandas as pd
from process_text import ProcessData

LETTERS_BY_STATE_DATA = 'data/LETTERS_BY_STATE.csv'
STATE_PARTY_CSV = 'data/STATE_PARTY.csv'

lte_db = create_engine('postgresql://burnssa@localhost/ccl_lte')
conn = lte_db.connect()
lte_df = pd.read_sql('LTE_FINAL', con=conn)

state_party_df = pd.read_csv(STATE_PARTY_CSV)


state_freq_df = pd.DataFrame(
    ProcessData.frequency_list(lte_df['State']),
    columns=['State', 'Letters']
)
state_freq_id_df = state_freq_df.merge(state_party_df, on='State')

state_freq_id_df.to_csv(LETTERS_BY_STATE_DATA, columns=['Letters', 'census_id'])
