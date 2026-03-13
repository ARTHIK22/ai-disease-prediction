import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report

# Load dataset
data = pd.read_csv("dataset.csv")

X = data.drop("Disease", axis=1)
y = data["Disease"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Create ML Pipeline
pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("model", RandomForestClassifier(
        n_estimators=200,
        max_depth=10,
        random_state=42
    ))
])

# Cross Validation
cv_scores = cross_val_score(pipeline, X, y, cv=5)

print("Cross Validation Accuracy:", cv_scores.mean())

# Train
pipeline.fit(X_train, y_train)

# Evaluate
predictions = pipeline.predict(X_test)
print(classification_report(y_test, predictions))

# Save model
pickle.dump(pipeline, open("model.pkl", "wb"))
print("Model saved successfully!")
