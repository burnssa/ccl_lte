import nltk, re, pprint
import operator
import requests
import numpy as np
import pandas as pd
import pdb
import requests
import csv
import json
import time
import os
import sqlalchemy
from sqlalchemy import *
import psycopg2

np.set_printoptions(precision=3, suppress=True)
pd.set_option('display.float_format', lambda x: '%.3f' % x)

ORIGINAL_CSV_FILE = 'data/CCL_LTEs.csv'
ENRICHED_CSV_FILE = 'data/CCL_LTEs_ENRICHED.csv'
STATE_PARTY = 'data/STATE_PARTY.csv'
FINAL_DATA = 'data/FINAL_DATA.csv'
FINAL_DATA_CONGRESS = 'data/FINAL_DATA_CONGRESS.csv'
FINAL_DATA_WORDS = 'data/FINAL_DATA_WORDS.xlsx'

FINAL_DATA = pd.read_csv('data/ccl_lte_final.csv')
LTE_DATA = pd.read_csv(ORIGINAL_CSV_FILE)

class ProcessData(object):
    """ Prints summary insights about letters to editor dataset """

    def __init__(self, data):
        self.data = data

    def check_data_load(self):
        """ Print data shape if data successfully loads, raise if otherwise """
        try:
            print 'Success importing data'
            print  """
                Dataset has {} samples with {} features each.
                """.format(self.data.shape)
        except:
            print "Dataset could not be loaded. Is the dataset missing?"

    ### Static methods

    @staticmethod
    def frequency_list(column):
        """ Return an ordered dict of most common categories """
        unique, counts = np.unique(column, return_counts=True)
        freq_dict = dict(zip(unique, counts))
        sorted_dict = sorted(
            freq_dict.items(),
            key=operator.itemgetter(1), reverse=True
        )
        return sorted_dict

    @staticmethod
    def ascii_characters(string):
        return ''.join(
            [x for x in unicode(string, errors='replace') if ord(x) < 128]
        )

    @staticmethod
    def check_for_word_in_text(series, word):
        return series.str.contains(word).fillna(0).astype(int)

    ### Dataset enrichment

    def add_facebook_share_count(self, file_path):
        current_data = pd.read_csv(file_path)
        if len(current_data) > 0:
            last_row_id = \
                current_data['Field Report Name'].iloc[-1]
            append_start_row = \
                self.data[self.data['Field Report Name'] == last_row_id] \
                    .index.values[0] + 1
        else:
            append_start_row = 1
        with open(file_path, 'ab') as fout:
            writer = csv.writer(fout, delimiter=',')
            for _, row in self.data[append_start_row:].iterrows():
                media_url = self.ascii_characters(row['Link to Published Media'])
                base_url = "http://graph.facebook.com/?client_id={0}&id=" \
                    .format(os.environ['FACEBOOK_APP_ID'])
                if type(media_url) is not str:
                    continue
                if media_url.startswith('http://') is False:
                    continue
                response = requests.get("%s%s" % (base_url, media_url))
                parsed_response = json.loads(response.content)
                print response.content
                print media_url
                if parsed_response.get('error') and \
                    parsed_response['error']['message'][1:3] == '#4':
                        time.sleep(600)
                        response = requests.get("%s%s" % (base_url, media_url))
                        parsed_response = json.loads(response.content)
                time.sleep(1.5)
                if response.ok:
                    share = parsed_response.get('share')
                    if share is not None:
                        share_count = share.get('share_count')
                    row['Share Count'] = share_count
                    print row['Share Count']
                    writer.writerow(row)

    def find_state(self, place):
        if type(place) != str:
            return 'N/A'
        base_url = 'https://maps.googleapis.com/maps/api/geocode/json'
        api_key = os.environ['GOOGLE_MAPS_API_KEY']
        response = requests.get(
            "%s?address=%s&key=%s" % (base_url, place, api_key)
        )
        if response.ok:
            parsed_response = json.loads(response.content)
            results = parsed_response.get('results')
            if results != None and results != []:
                components = results[0].get('address_components')
                admin_area_level_one = next(
                    (
                        item for item in components \
                        if 'administrative_area_level_1' in \
                        item['types']
                    ), None
                )
                if admin_area_level_one is not None:
                    state_abbrev = admin_area_level_one.get('short_name')
                    return self.ascii_characters(state_abbrev)
                else:
                    'N/A'

    def create_final_df(self):
        old_data = self.data
        enriched_data = pd.read_csv(ENRICHED_CSV_FILE)

        with_share_count_df = old_data.merge(
            enriched_data[['Field Report Name', 'Share Count']],
            on='Field Report Name',
            how='left'
        )

        with open(FINAL_DATA, 'ab') as fout:
            reader = pd.read_csv(FINAL_DATA)
            new_starting_row = len(reader)
            writer = csv.writer(fout, delimiter=',', lineterminator=os.linesep)
            for index, row in with_share_count_df[new_starting_row:].iterrows():
                place = self.ascii_characters(
                    unicode(str(row['City of Publication']), errors='replace')
                )
                with_share_count_df.loc[index, 'State'] = self.find_state(place)
                print with_share_count_df.loc[index]
                writer.writerow(with_share_count_df.loc[index])

    def add_representation_to_final_df(self):
        final_df = pd.read_csv(FINAL_DATA, encoding = "ISO-8859-1")
        #final_df['Text of Media'] = final_df['Text of Media'].decode('utf-8')
        state_data = pd.read_csv(STATE_PARTY)
        final_congress_df = final_df.merge(
            state_data[['State', 'house_rep', 'house_dem']],
            on='State',
            how='left'
        )

        final_congress_df['Share Congress Republican'] = \
            final_congress_df['house_rep'] / \
            (final_congress_df['house_rep'] + final_congress_df['house_dem'])
        print final_congress_df.columns.values
        print final_congress_df.shape
        final_congress_df.to_csv(FINAL_DATA_CONGRESS, encoding='ISO-8859-1')

    def add_word_count_to_final_df(self):
        final_df = pd.read_csv(
            FINAL_DATA_CONGRESS,
            engine='c',
            encoding ="latin-1",
            lineterminator='\n'
        )
        print final_df.shape
        print final_df.columns.values
        final_df['word_count'] = final_df['Text of Media'].apply(
            lambda x: len(self.words_in_text(x))
        )

        lte_db = create_engine('postgresql://burnssa@localhost/ccl_lte')
        try:
            lte_db.connect()
            metadata = MetaData(lte_db)
            ccl_table = Table('LTE', metadata, autoload=True)
            result = lte_db.execute('SELECT * FROM "LTE"')

        except psycopg2.OperationalError:
            final_df.to_sql(name='LTE', con=lte_db, if_exists='fail')

        final_df.to_csv(FINAL_DATA_CONGRESS, encoding='ISO-8859-1')

    def add_select_word_dummies(self):
        lte_db = create_engine('postgresql://burnssa@localhost/ccl_lte')
        conn = lte_db.connect()
        lte_df = pd.read_sql('LTE', con=conn)
        lte_df['word_tax'] = \
            self.check_for_word_in_text(lte_df['Text of Media'], 'tax')
        lte_df['word_fee'] = \
            self.check_for_word_in_text(lte_df['Text of Media'], 'fee')
        lte_df['word_dividend'] = \
            self.check_for_word_in_text(lte_df['Text of Media'], 'dividend')
        if not lte_db.dialect.has_table(lte_db, 'LTE_FINAL'): 
            lte_df.to_sql(
                name='LTE_FINAL',
                con=lte_db,
                if_exists='fail',
                index=False
            )
        lte_df.to_excel(FINAL_DATA_WORDS, encoding='UTF-8')

    ### Summary output

    def print_publications(self):
        """ Print the 20 most common publications """
        publication_list = self.frequency_list(self.data['Media Title'])
        print publication_list[:20]

    def print_cities(self):
        """ Print the 20 most common cities """
        city_list = self.frequency_list(self.data['City of Publication'])
        print city_list[:20]

    def print_word_count_histogram(self):
        """ Print a histogram of dataset letter lengths """
        lengths_array = np.asarray(
            [
                len(
                    self.words_in_text(text)
                ) for text in self.data['Text of Media']
                .dropna(0)
            ]
        )

        letter_lengths = np.histogram(
            lengths_array,
            bins=[0, 100, 200, 300, 400, 500, 1000, 10000]
        )
        print letter_lengths

    def words_in_text(self, string):
        """ Return the number of words in a text string """
        tokenizer = nltk.tokenize.RegexpTokenizer(r'\w+')
        if type(string) != unicode:
            string = self.ascii_characters(
                unicode(str(string), errors='replace').encode('utf-8')
            )
        tokens = tokenizer.tokenize(string)
        return tokens

    def print_most_frequent_words(self):
        """ Print the 60 most common non-stop words """
        stopwords = nltk.corpus.stopwords.words('english')
        all_text = ''.join(
            text.lower() for text in self.data['Text of Media'].dropna(0)
        )
        all_words = self.words_in_text(all_text)

        non_stop_words = [word for word in all_words if word not in stopwords]
        print self.frequency_list(non_stop_words)[:60]

def field_exists(df, field):
    if field not in df.columns:
        return False
    elif len(df.get(field)) == 0:
        return False
    else:
        return True

def run_process_data(data):
    p = ProcessData(data)
    p.check_data_load()
    if not field_exists(data, 'Share Count'):
        p.add_facebook_share_count(data)
    if not field_exists(data, 'word_tax'):
        p.add_select_word_dummies()
    if not field_exists(data, 'word_count'):
        p.add_word_count_to_final_df()
    if not field_exists(data, 'Share Congress Republican'):
        p.add_representation_to_final_df()
        p.create_final_df()
    # p.print_publications()
    # p.print_cities()
    # p.print_word_count_histogram()
    # p.print_most_frequent_words()

run_process_data(FINAL_DATA)
