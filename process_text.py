import nltk, re, pprint
from nltk import word_tokenize

import numpy as np
import pandas as pd
import sklearn
import pdb
from datetime import datetime
from sklearn.cluster import KMeans
from sklearn.mixture import GMM
from sklearn.metrics import silhouette_score
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from pandas.tools.plotting import scatter_matrix
import pprint
from sklearn.preprocessing import MinMaxScaler
from scipy import stats
from textwrap import wrap

np.set_printoptions(precision=3, suppress=True)
pd.set_option('display.float_format', lambda x: '%.3f' % x)

try:
    LTE_DATA = pd.read_csv("data/CCL_LTEs.csv")
    print 'Success importing data'
    print  """
        Dataset has {} samples with {} features each.
        """.format(*LTE_DATA.shape)
except:
    print "Dataset could not be loaded. Is the dataset missing?"

pdb.set_trace()
