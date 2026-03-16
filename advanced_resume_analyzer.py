import streamlit as st
import pandas as pd
import sqlite3
import re
import pdfplumber
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
import tempfile

# ---------------- SESSION ----------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

# ---------------- DATABASE ----------------

conn = sqlite3.connect("resume_system.db", check_same_thread=False)
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS users(username TEXT,password TEXT)")
c.execute("CREATE TABLE IF NOT EXISTS resumes(username TEXT,score INTEGER)")

conn.commit()

# ---------------- SKILLS ----------------

skills_db = [
"python","java","c++","html","css","javascript","sql",
"machine learning","data science","react","node",
"django","flask","pandas","numpy"
]

# ---------------- COURSES ----------------

courses = {
"data science":[
"Machine Learning Course",
"Python for Data Science",
"Statistics for Data Science"
],
"web developer":[
"Full Stack Web Development",
"React Bootcamp",
"NodeJS Masterclass"
],
"software developer":[
"Advanced Python",
"Data Structures and Algorithms",
"System Design Basics"
]
}

# ---------------- FUNCTIONS ----------------

def extract_text(file):

    text=""

    with pdfplumber.open(file) as pdf:

        for page in pdf.pages:

            t=page.extract_text()

            if t:
                text+=t

    return text.lower()


def extract_email(text):

    pattern=r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"

    match=re.findall(pattern,text)

    return match[0] if match else "Not Found"


def extract_phone(text):

    pattern=r"\b\d{10}\b"

    match=re.findall(pattern,text)

    return match[0] if match else "Not Found"


def extract_skills(text):

    found=[]

    for skill in skills_db:

        if skill in text:
            found.append(skill)

    return found


def ats_score(skills):

    score=len(skills)*12

    if score>100:
        score=100

    return score


def predict_job(skills):

    if "machine learning" in skills or "data science" in skills:
        return "data science"

    if "html" in skills or "react" in skills:
        return "web developer"

    return "software developer"


def resume_suggestions(skills):

    suggestions=[]

    if "python" not in skills:
        suggestions.append("Add Python skill")

    if "sql" not in skills:
        suggestions.append("Add SQL skill")

    if "machine learning" not in skills:
        suggestions.append("Add Machine Learning")

    if len(skills)<5:
        suggestions.append("Add more technical skills")

    return suggestions


def generate_pdf_report(username,email,phone,skills,score,job):

    file=tempfile.NamedTemporaryFile(delete=False,suffix=".pdf")

    c=canvas.Canvas(file.name)

    c.drawString(50,800,"AI Resume Analysis Report")
    c.drawString(50,770,"Name: "+username)
    c.drawString(50,750,"Email: "+email)
    c.drawString(50,730,"Phone: "+phone)
    c.drawString(50,710,"Predicted Job Role: "+job)
    c.drawString(50,690,"ATS Score: "+str(score))

    y=660

    c.drawString(50,y,"Skills:")

    for s in skills:
        y-=20
        c.drawString(70,y,s)

    c.save()

    return file.name


# ---------------- DASHBOARD HEADER ----------------

st.title("AI Resume Analyzer System")

menu=st.sidebar.selectbox(
"Navigation",
["Register","Login","Admin Login"]
)

# ---------------- REGISTER ----------------

if menu=="Register":

    st.header("User Registration")

    user=st.text_input("Username")

    pwd=st.text_input("Password",type="password")

    if st.button("Create Account"):

        c.execute("INSERT INTO users VALUES (?,?)",(user,pwd))
        conn.commit()

        st.success("Account Created")

# ---------------- LOGIN ----------------

if menu=="Login":

    if not st.session_state.logged_in:

        st.header("User Login")

        user=st.text_input("Username")

        pwd=st.text_input("Password",type="password")

        if st.button("Login"):

            c.execute("SELECT * FROM users WHERE username=? AND password=?",(user,pwd))

            data=c.fetchall()

            if data:

                st.session_state.logged_in=True
                st.session_state.username=user

                st.success("Login Successful")
                st.rerun()

            else:

                st.error("Invalid Login")

    if st.session_state.logged_in:

        st.success("Welcome "+st.session_state.username)

        if st.button("Logout"):

            st.session_state.logged_in=False
            st.rerun()

        file=st.file_uploader("Upload Resume PDF",type=["pdf"])

        if file:

            text=extract_text(file)

            email=extract_email(text)

            phone=extract_phone(text)

            skills=extract_skills(text)

            score=ats_score(skills)

            job=predict_job(skills)

            suggestions=resume_suggestions(skills)

            c.execute("INSERT INTO resumes VALUES (?,?)",(st.session_state.username,score))
            conn.commit()

            st.subheader("Candidate Info")

            st.write("Email:",email)
            st.write("Phone:",phone)

            st.subheader("Skills Detected")

            st.write(skills)

            st.subheader("ATS Resume Score")

            st.progress(score/100)
            st.write(score,"/100")

            # PIE CHART

            if skills:

                st.subheader("Skill Distribution")

                fig,ax=plt.subplots()

                ax.pie([1]*len(skills),labels=skills,autopct="%1.1f%%")

                st.pyplot(fig)

            st.subheader("Predicted Job Role")

            st.success(job)

            st.subheader("Recommended Courses")

            for course in courses[job]:

                st.write("-",course)

            st.subheader("Resume Improvement Suggestions")

            for s in suggestions:

                st.write("-",s)

            # PDF REPORT

            if st.button("Download Resume Report"):

                pdf_path=generate_pdf_report(
                st.session_state.username,
                email,
                phone,
                skills,
                score,
                job
                )

                with open(pdf_path,"rb") as f:

                    st.download_button(
                    "Download PDF",
                    f,
                    file_name="resume_report.pdf"
                    )

# ---------------- ADMIN ----------------

if menu=="Admin Login":

    admin_user=st.text_input("Admin Username")

    admin_pass=st.text_input("Admin Password",type="password")

    if st.button("Admin Login"):

        if admin_user=="admin" and admin_pass=="admin123":

            st.success("Admin Login Successful")

            st.subheader("Registered Users")

            users=pd.read_sql_query("SELECT * FROM users",conn)
            st.dataframe(users)

            st.subheader("Resume Scores")

            scores=pd.read_sql_query("SELECT * FROM resumes",conn)
            st.dataframe(scores)

            st.subheader("Resume Ranking")

            ranking=scores.sort_values(by="score",ascending=False)
            st.dataframe(ranking)

        else:

            st.error("Wrong Admin Credentials")