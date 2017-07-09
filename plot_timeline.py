import matplotlib as mpl
import matplotlib.pyplot as plt
import sqlalchemy
from sqlalchemy import *
import pdb
import pandas as pd
from datetime import datetime

lte_db = create_engine('postgresql://burnssa@localhost/ccl_lte')
conn = lte_db.connect()
lte_df = pd.read_sql('LTE_FINAL', con=conn)
lte_df['numeric_date'] = \
    pd.to_datetime(lte_df['Date of Publication'])

lte_df = lte_df.set_index('numeric_date', drop=False)

# Limit to data after 2013
lte_df = lte_df[lte_df['numeric_date'] >= datetime(2013, 1, 1)]

quarter_series = \
    lte_df['numeric_date'] \
    .groupby(pd.TimeGrouper(freq='Q')) \
    .agg({'count':'count'})

fig = plt.figure()
ax = fig.add_subplot(111)

ax.set_ylabel('Total Letters Published')
ax.set_title('CCL Letters to Editor Published by Quarter')
ax.set_xlabel('Quarter Ending')

ax.bar(
    quarter_series.index,
    quarter_series['count'],
    color='blue',
    width=60
)
ax.set_xticklabels(quarter_series.index, rotation=45)
ax.set_xticks(quarter_series.index)

qrt_fmt = mpl.dates.DateFormatter('%b %Y')

ax.xaxis_date()
ax.xaxis.set_major_formatter(qrt_fmt)
for tick in ax.xaxis.get_majorticklabels():
    tick.set_horizontalalignment('center')
plt.tight_layout()
plt.grid(color='gray', linestyle='--', linewidth=0.5)
plt.savefig('plots/letter_timeline.png')
plt.show()
