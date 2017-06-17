import numpy as np
import statsmodels.api as sm
import pandas as pd
import sklearn
import sqlalchemy
from sqlalchemy import *
import psycopg2
from datetime import datetime
import pdb
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer as SIA
from process_text import ProcessData

REQUIRED_COLS = ['Share Count', 'State']
US_CLEAN_LETTER_DATA = 'LTE_CLEAN'
NON_ROOT_LINK_DATA = 'LTE_NON_ROOT_LINK'
SENTIMENT_DATA = 'SENTIMENT_DATA'

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
        root_domains = ['.com', '.net', '.org', 'com/', 'net/', 'tor/', 'org/']
        try:
            clean_data = pd.read_sql(US_CLEAN_LETTER_DATA, con=conn)
            clean_data['link_last_four'] = \
                clean_data['Link to Published Media'].str[-4:]
            non_root_link_data = clean_data[
                ~clean_data['link_last_four'].isin(root_domains)
            ]
            if not lte_db.dialect.has_table(lte_db, NON_ROOT_LINK_DATA):
                non_root_link_data.to_sql(
                    name=NON_ROOT_LINK_DATA,
                    con=lte_db,
                    if_exists='fail',
                    index=False
                )
        except psycopg2.OperationalError:
            print "Database doesn't exit"

    def add_sentiment_analysis(self):
        sid = SIA()
        pre_sentiment_data = pd.read_sql(NON_ROOT_LINK_DATA, con=conn)
        pre_sentiment_data['pos_score'] = \
            pre_sentiment_data['Text of Media'] \
            .apply(lambda x:sid.polarity_scores(x)['pos'])
        pre_sentiment_data['neg_score'] = \
            pre_sentiment_data['Text of Media'] \
            .apply(lambda x:sid.polarity_scores(x)['neg'])
        if not lte_db.dialect.has_table(lte_db, SENTIMENT_DATA):
            pre_sentiment_data.to_sql(
                name=SENTIMENT_DATA,
                con=lte_db,
                if_exists='fail',
                index=False
            )

    def print_most_shared(self):
        data = pd.read_sql(SENTIMENT_DATA, con=conn)
        print ProcessData.frequency_list('Share Count')

    def regress_share_count_on_features(self):
        final_data = pd.read_sql(SENTIMENT_DATA, con=conn)
        final_data['numeric_date'] = \
            pd.to_datetime(final_data['Date of Publication'])
        first_publication_date = final_data['numeric_date'].min(axis=0)
        final_data['days_since_first_letter'] = \
            (final_data['numeric_date'] - first_publication_date).dt.days
        final_data['word_count_quad_term'] = final_data['word_count']**2
        final_data['repub_days_interaction'] = \
            final_data['Share Congress Republican'] * \
            final_data['days_since_first_letter']

        X = final_data[[
            'Share Congress Republican',
            'word_count',
            'word_count_quad_term',
            'word_tax',
            'word_fee',
            'word_dividend',
            'days_since_first_letter',
            'pos_score',
            'neg_score',
            'repub_days_interaction'
        ]]
        Y = final_data['Share Count']

        X = sm.add_constant(X)
        est = sm.OLS(Y, X).fit()

        print est.summary()
        final_data.to_csv('data/SENTIMENT_ANALYSIS.csv', encoding='utf-8')
        final_data.to_excel('data/SENTIMENT_ANALYSIS.xlsx', encoding='utf-8')

def run_train_data(data):
    t = TrainData(data)
    #t.filter_data_for_share_count_and_us()
    #.filter_data_for_root_domains()
    #t.print_most_shared()
    #t.add_sentiment_analysis()
    t.regress_share_count_on_features()

lte_db = create_engine('postgresql://burnssa@localhost/ccl_lte')
conn = lte_db.connect()
lte_df = pd.read_sql('LTE_FINAL', con=conn)

run_train_data(lte_df)
