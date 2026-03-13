import pickle
import numpy as np

# Load trained model
model = pickle.load(open("model.pkl", "rb"))

print("=== AI Disease Prediction System ===")
print("Enter 1 if symptom is present, 0 if not.\n")

# Taking user input
fever = int(input("Fever: "))
cough = int(input("Cough: "))
headache = int(input("Headache: "))
fatigue = int(input("Fatigue: "))
nausea = int(input("Nausea: "))
chest_pain = int(input("Chest Pain: "))
body_pain = int(input("Body Pain: "))
sore_throat = int(input("Sore Throat: "))

# Create input array
input_data = np.array([[fever, cough, headache, fatigue,
                        nausea, chest_pain, body_pain, sore_throat]])

# Predict
prediction = model.predict(input_data)
probabilities = model.predict_proba(input_data)
confidence = max(probabilities[0]) * 100

print("\n🔎 Prediction Result")
print("Predicted Disease:", prediction[0])
print("Confidence: {:.2f}%".format(confidence))

print("\n⚠ Disclaimer: This is for educational purposes only.")
