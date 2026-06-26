import pandas as pd
import joblib
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error

data = pd.read_csv("health_dataset.csv")

data = data[['age','bmi',
             'avg_heart_rate',
             'hours_sleep',
             'stress_level']]

data.dropna(inplace=True)

def bmi_adjustment(bmi):
    if bmi < 18.5:
        return 0
    elif bmi < 25:
        return 5
    elif bmi < 30:
        return 10
    else:
        return 20

data['recommended_duration'] = (
        data['stress_level']*3 +
        data['hours_sleep']*2 +
        data['avg_heart_rate']*0.05 +
        data['age']*0.1 +
        data['bmi'].apply(bmi_adjustment)
).clip(20,90)



X = data[['age','bmi',
          'avg_heart_rate',
          'hours_sleep',
          'stress_level']]

y = data['recommended_duration']


X_train,X_test,y_train,y_test = train_test_split(
    X,y,test_size=0.2,random_state=42
)

model = HistGradientBoostingRegressor(
    max_iter=300,
    learning_rate=0.05,
    max_depth=8,
    random_state=42
)

model.fit(X_train,y_train)

y_pred=model.predict(X_test)

print("R2 Score:",r2_score(y_test,y_pred)*100,"%")
print("MAE:",mean_absolute_error(y_test,y_pred))

print("Training Score:", model.score(X_train, y_train))
print("Testing Score:", model.score(X_test, y_test))

joblib.dump(model,"walk_model.pkl")

print("✅ Walk model trained")