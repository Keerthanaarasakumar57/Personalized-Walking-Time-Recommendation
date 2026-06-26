import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score


data = pd.read_csv("Stress_dataset.csv")
data = data[['Sleep Duration','Heart Rate','Stress Level']]

data.dropna(inplace=True)

def stress_category(x):
    if x <= 3:
        return "Low"
    elif x <= 6:
        return "Medium"
    else:
        return "High"

data['Stress Category'] = data['Stress Level'].apply(stress_category)
X = data[['Sleep Duration','Heart Rate']]
y = data['Stress Category']

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42
)

model = RandomForestClassifier( n_estimators=200,random_state=42)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

accuracy = accuracy_score(y_test, y_pred)

print("Accuracy:", accuracy*100, "%")
print("Training Score:", model.score(X_train, y_train))
print("Testing Score:", model.score(X_test, y_test))

joblib.dump(model,"stress_model.pkl")


print("✅ Stress model trained")
print("Features used for training:")
print(X.columns)
print("Total features:", X.shape[1])