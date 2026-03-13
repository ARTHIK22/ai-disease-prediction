import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import pickle
import hashlib
from datetime import datetime
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from reportlab.pdfgen import canvas

st.set_page_config(page_title="AI Health System", layout="wide")

# ---------------- UI STYLE ----------------

st.markdown("""
<style>
body{
background-color:#f4f8fb;
}
.stButton>button{
background:#1f77b4;
color:white;
border-radius:10px;
height:40px;
font-weight:bold;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DATABASE ----------------

def create_db():

    conn=sqlite3.connect("health.db")
    c=conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS patients(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER,
    gender TEXT,
    disease TEXT,
    confidence REAL,
    date TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS appointments(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name TEXT,
    doctor TEXT,
    date TEXT,
    problem TEXT,
    status TEXT
    )
    """)

    conn.commit()
    conn.close()

create_db()

# ---------------- AUTH ----------------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login(user,pwd):

    conn=sqlite3.connect("health.db")
    c=conn.cursor()

    c.execute("SELECT password,role FROM users WHERE username=?",(user,))
    result=c.fetchone()

    conn.close()

    if result and result[0]==hash_password(pwd):
        return result[1]

    return None


def register(user,pwd,role):

    conn=sqlite3.connect("health.db")
    c=conn.cursor()

    try:
        c.execute("INSERT INTO users VALUES(NULL,?,?,?)",
        (user,hash_password(pwd),role))
        conn.commit()
        conn.close()
        return True
    except:
        conn.close()
        return False


# ---------------- LOGIN ----------------

if "login" not in st.session_state:
    st.session_state.login=False

if not st.session_state.login:

    st.title("AI Health System Login")

    tab1,tab2=st.tabs(["Login","Register"])

    with tab1:

        user=st.text_input("Username")
        pwd=st.text_input("Password",type="password")
        role=st.selectbox("Role",["Admin","Doctor"])

        if st.button("Login"):

            auth=login(user,pwd)

            if auth and auth==role:
                st.session_state.login=True
                st.session_state.role=auth
                st.rerun()
            else:
                st.error("Invalid login")

    with tab2:

        user=st.text_input("New Username")
        pwd=st.text_input("New Password",type="password")
        role=st.selectbox("Account Type",["Admin","Doctor"])

        if st.button("Create Account"):

            if register(user,pwd,role):
                st.success("Account created")
            else:
                st.error("User exists")

    st.stop()

# ---------------- HEADER ----------------

st.title("AI Health Diagnostic System")

if st.button("Logout"):
    st.session_state.login=False
    st.rerun()

# ---------------- MENU ----------------

menu=st.sidebar.radio("Menu",
["Prediction","Chatbot","Blood Analyzer","Appointments","Dashboard"]
)

# ---------------- MODEL ----------------

model=pickle.load(open("model.pkl","rb"))

SYMPTOMS=[
"fever","cough","headache","fatigue",
"nausea","chest pain","body pain","sore throat"
]

# ---------------- DOCTOR MAP ----------------

DOCTOR_MAP={
"Heart Disease":"Cardiologist",
"Malaria":"General Physician",
"Typhoid":"General Physician",
"Dengue":"Infectious Disease Specialist",
"Pneumonia":"Pulmonologist",
"Diabetes":"Endocrinologist"
}

# ---------------- ADVICE ----------------

ADVICE_MAP={
"Malaria":["Drink fluids","Take antimalarial medicine","Use mosquito protection"],
"Typhoid":["Drink boiled water","Maintain hygiene","Take antibiotics"],
"Dengue":["Take rest","Drink fluids","Avoid mosquito bites"]
}

# ---------------- PDF ----------------

def generate_pdf(name,age,gender,disease,confidence,doctor):

    file="medical_report.pdf"

    c=canvas.Canvas(file)

    c.drawString(100,750,"AI Medical Report")
    c.drawString(100,720,f"Patient: {name}")
    c.drawString(100,700,f"Age: {age}")
    c.drawString(100,680,f"Gender: {gender}")
    c.drawString(100,650,f"Disease: {disease}")
    c.drawString(100,630,f"Confidence: {confidence:.2f}%")
    c.drawString(100,610,f"Doctor: {doctor}")

    c.save()

    return file


# ---------------- PREDICTION ----------------

if menu=="Prediction":

    st.header("Disease Prediction")

    col1,col2=st.columns(2)

    with col1:
        name=st.text_input("Patient Name")
        age=st.number_input("Age",1,120,25)

    with col2:
        gender=st.selectbox("Gender",["Male","Female","Other"])

    symptoms=st.multiselect("Select Symptoms",SYMPTOMS)

    if st.button("Predict Disease"):

        vector=[1 if s in symptoms else 0 for s in SYMPTOMS]

        data=np.array([vector])

        pred=model.predict(data)
        prob=model.predict_proba(data)

        prob_df=pd.DataFrame({
        "Disease":model.classes_,
        "Probability":prob[0]
        }).sort_values(by="Probability",ascending=False).head(3)

        disease=prob_df.iloc[0]["Disease"]
        confidence=prob_df.iloc[0]["Probability"]*100

        doctor=DOCTOR_MAP.get(disease,"General Physician")

        st.success(f"Predicted Disease: {disease}")
        st.info(f"Recommended Doctor: {doctor}")

        # ---------------- Risk Meter ----------------

        st.subheader("Risk Meter")

        if confidence < 40:
            st.success("Low Risk")
        elif confidence < 70:
            st.warning("Moderate Risk")
        else:
            st.error("High Risk")

        st.progress(int(confidence))

        # ---------------- Advice ----------------

        st.subheader("Health Advice")

        advice=ADVICE_MAP.get(
        disease,
        ["Take rest","Drink water","Consult doctor"]
        )

        for a in advice:
            st.write("✔",a)

        # ---------------- 3D GRAPH ----------------

        fig = plt.figure(figsize=(4,4))
        ax = fig.add_subplot(111, projection='3d')

        x = np.arange(len(prob_df["Disease"]))
        y = np.zeros(len(prob_df["Disease"]))
        z = np.zeros(len(prob_df["Disease"]))

        dx = np.ones(len(prob_df["Disease"])) * 0.5
        dy = np.ones(len(prob_df["Disease"])) * 0.5
        dz = prob_df["Probability"] * 100

        colors = ["#ff4b4b","#1f77b4","#2ecc71"]

        ax.bar3d(x,y,z,dx,dy,dz,color=colors)

        ax.set_xticks(x)
        ax.set_xticklabels(prob_df["Disease"])

        ax.set_zlabel("Probability %")
        ax.set_title("Disease Prediction Graph")

        st.pyplot(fig)

        # ---------------- SAVE PATIENT ----------------

        conn=sqlite3.connect("health.db")
        c=conn.cursor()

        c.execute("""
        INSERT INTO patients VALUES(NULL,?,?,?,?,?,?)
        """,(name,age,gender,disease,confidence,str(datetime.now())))

        conn.commit()
        conn.close()

        # ---------------- PDF ----------------

        pdf=generate_pdf(name,age,gender,disease,confidence,doctor)

        with open(pdf,"rb") as f:
            st.download_button("Download Medical Report",f,file_name="report.pdf")


# ---------------- CHATBOT ----------------

elif menu=="Chatbot":

    st.header("Symptom Assistant")

    text=st.text_input("Describe symptoms")

    if st.button("Analyze"):

        df=pd.read_csv("diseases.csv")

        scores={}

        for _,row in df.iterrows():

            disease=row["disease"]
            symptoms=row["symptoms"].split(",")

            score=0

            for s in symptoms:
                if s.strip() in text.lower():
                    score+=1

            scores[disease]=score

        results=sorted(scores.items(),key=lambda x:x[1],reverse=True)

        for d,s in results[:3]:
            if s>0:
                st.write("Possible:",d)

# ---------------- BLOOD ANALYZER ----------------

elif menu=="Blood Analyzer":

    st.header("Blood Report Analyzer")

    hb=st.number_input("Hemoglobin")
    sugar=st.number_input("Glucose")
    chol=st.number_input("Cholesterol")

    if st.button("Analyze"):

        if hb<12:
            st.warning("Possible Anemia")

        if sugar>140:
            st.warning("Diabetes Risk")

        if chol>200:
            st.warning("Heart Disease Risk")


# ---------------- APPOINTMENTS ----------------

elif menu=="Appointments":

    st.header("Book Appointment")

    name=st.text_input("Patient Name")

    doctor=st.selectbox("Doctor",
    ["Dr Sharma","Dr Mehta","Dr Singh"])

    date=st.date_input("Appointment Date")

    problem=st.text_area("Problem")

    if st.button("Book"):

        conn=sqlite3.connect("health.db")
        c=conn.cursor()

        c.execute("""
        INSERT INTO appointments VALUES(NULL,?,?,?,?,?)
        """,(name,doctor,str(date),problem,"Pending"))

        conn.commit()
        conn.close()

        st.success("Appointment booked")


# ---------------- DASHBOARD ----------------

elif menu=="Dashboard":

    st.header("Doctor Dashboard")

    conn=sqlite3.connect("health.db")

    df=pd.read_sql_query("SELECT * FROM patients",conn)
    ap=pd.read_sql_query("SELECT * FROM appointments",conn)

    conn.close()

    col1,col2,col3=st.columns(3)

    col1.metric("Patients",len(df))
    col2.metric("Appointments",len(ap))
    col3.metric("Unique Diseases",df["disease"].nunique())

    st.subheader("Disease Distribution")

    fig,ax=plt.subplots()

    df["disease"].value_counts().plot(kind="bar",ax=ax,color=["red","blue","green","orange"])

    st.pyplot(fig)

    st.subheader("Patient History")
    st.dataframe(df)

    st.subheader("Appointments")
    st.dataframe(ap)

    st.download_button("Download Patients",df.to_csv(index=False),"patients.csv")
    st.download_button("Download Appointments",ap.to_csv(index=False),"appointments.csv")