import matplotlib as mpl
import matplotlib.pyplot as plt
import sqlalchemy
from sqlalchemy import *
import pdb
import pandas as pd

lte_db = create_engine('postgresql://burnssa@localhost/ccl_lte')
conn = lte_db.connect()
lte_df = pd.read_sql('LTE_FINAL', con=conn)
lte_df['numeric_date'] = \
    pd.to_datetime(lte_df['Date of Publication'])

lte_df = lte_df.set_index('numeric_date', drop=False)

quarter_series = \
    lte_df['numeric_date'] \
    .groupby(pd.TimeGrouper(freq='Q')) \
    .agg({'count':'count'})

plt.plot(quarter_series, color='blue')

plt.show()
