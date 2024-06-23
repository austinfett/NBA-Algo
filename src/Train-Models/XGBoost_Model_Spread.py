import sqlite3

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from tqdm import tqdm

dataset = "dataset_2012-23"
con = sqlite3.connect("Data/dataset.sqlite")
data = pd.read_sql_query(f"select * from \"{dataset}\"", con, index_col="index")
con.close()
data = data.fillna(-1)
data = data[data['Spread-Cover'] != -1]
data = data[data['OU-Cover'] != -1]
data = data[data['Spread-Cover'] != 2]
spread = data['Spread-Cover']
total = data['OU']
line = data['Spread']
data.drop(['Score', 'Home-Team-Win', 'TEAM_NAME', 'Date', 'TEAM_NAME.1', 'Date.1', 'OU-Cover', 'OU', 'Spread-Cover', 'Spread'], axis=1, inplace=True)

data['OU'] = np.asarray(total)
data['Spread'] = np.asarray(line)
data = data.values
data = data.astype(float)
acc_results = []

for x in tqdm(range(100)):
    x_train, x_test, y_train, y_test = train_test_split(data, spread, test_size=.1)

    train = xgb.DMatrix(x_train, label=y_train)
    test = xgb.DMatrix(x_test)

    param = {
        'max_depth': 20,
        'eta': 0.05,
        'objective': 'multi:softprob',
        'num_class': 3
    }
    epochs = 750

    model = xgb.train(param, train, epochs)

    predictions = model.predict(test)
    y = []

    for z in predictions:
        y.append(np.argmax(z))

    acc = round(accuracy_score(y_test, y) * 100, 1)
    print(f"{acc}%")
    acc_results.append(acc)
    # only save results if they are the best so far
    if acc == max(acc_results):
        model.save_model('Models/XGBoost_{}%_Spread-min.json'.format(acc))
