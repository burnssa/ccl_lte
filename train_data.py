import numpy as np
import pandas as pd
import sklearn
import sqlalchemy
from sqlalchemy import *
import psycopg2
from datetime import datetime
#import matplotlib.pyplot as plt
import pprint
from scipy import stats
from textwrap import wrap
import pdb

REQUIRED_COLS = ['Share Count', 'State']
US_CLEAN_LETTER_DATA = 'LTE_CLEAN'
NON_ROOT_LINK_DATA = 'LTE_NON_ROOT_LINK'

class TrainData(object):
    """ Trains a regression of facebook share count on a set of LTE features"""

    def __init__(self, data):
        self.data = data

    def filter_data_for_share_count_and_us(self):
        clean_data = self.data[ \
            np.isfinite(self.data['Share Count']) & \
            np.isfinite(self.data['house_dem']) \
        ]
        if not lte_db.dialect.has_table(lte_db, US_CLEAN_LETTER_DATA):
            clean_data.to_sql(
                name=US_CLEAN_LETTER_DATA,
                con=lte_db,
                index=False,
                if_exists='fail'
            )

    def filter_data_for_root_domains(self):
        root_domains = ['.com', '.net', '.org']
        pdb.set_trace()
        try:
            clean_data = pd.read_sql(US_CLEAN_LETTER_DATA, con=conn)
            pdb.set_trace()
            clean_data['link_last_four'] = \
                clean_data['Link to Published Media'].str[-4:]
            non_root_link_data = clean_data[
                ~clean_data['link_last_four'].isin(root_domains)
            ]
            pdb.set_trace()
            non_root_link_data.to_sql(
                name = NON_ROOT_LINK_DATA,
                con=lte_db,
                if_exists='fail',
                index=False
            )
        except psycopg2.OperationalError:
            print "Database doesn't exist"


def run_train_data(data):
    t = TrainData(data)
    t.filter_data_for_share_count_and_us()
    t.filter_data_for_root_domains()

lte_db = create_engine('postgresql://burnssa@localhost/ccl_lte')
conn = lte_db.connect()
lte_df = pd.read_sql('LTE_FINAL', con=conn)

run_train_data(lte_df)
