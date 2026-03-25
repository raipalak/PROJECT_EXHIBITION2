from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
from pydantic import BaseModel
from typing import Optional, List
import datetime
import os

app = FastAPI()

# SQLite Database setup
DB_PATH = "softcare.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS health_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            age INTEGER,
            gender TEXT,
            height INTEGER,
            weight INTEGER,
            hr INTEGER,
            sys INTEGER,
            dia INTEGER,
            sugar INTEGER,
            temp REAL,
            symptoms TEXT,
            duration TEXT,
            score INTEGER,
            risk TEXT,
            suggestion TEXT,
            dept TEXT,
            spo2 INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mood_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            mood_label TEXT,
            mood_score INTEGER,
            note TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            task TEXT,
            time TEXT,
            type TEXT,
            completed BOOLEAN DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Pydantic models for request bodies
class HealthData(BaseModel):
    device_id: str
    age: int
    gender: str
    height: int
    weight: int
    hr: int
    sys: int
    dia: int
    sugar: int
    temp: float
    spo2: int
    symptoms: List[str]
    duration: str

class MoodData(BaseModel):
    device_id: str
    mood_label: str
    mood_score: int
    note: Optional[str] = ""

class ReminderData(BaseModel):
    device_id: str
    task: str
    time: str
    type: str # 'medication' or 'checkup'

# API Routes
@app.post("/health-data")
def save_health(data: HealthData):
    score = 100
    
    # Vitals Scoring logic (Extended)
    if "Fever" in data.symptoms: score -= 10
    if "Chest Pain" in data.symptoms: score -= 30
    if data.sys > 140 or data.dia > 90: score -= 20
    if data.sugar > 180: score -= 20
    if data.hr < 60 or data.hr > 100: score -= 10
    if data.temp > 38: score -= 10
    if data.spo2 < 95: score -= 15
    if data.spo2 < 90: score -= 25 # Critical O2
    
    score = max(0, score)
    
    # Risk Level
    risk = "Normal"
    if score < 50: risk = "High Risk"
    elif score < 80: risk = "Moderate Risk"

    # Department Selection
    if "Chest Pain" in data.symptoms or data.sys > 160: dept = "Cardiology"
    elif data.sugar > 200: dept = "Endocrinology"
    elif data.temp > 38.5: dept = "Internal Medicine"
    else: dept = "General Physician"

    # Suggestion Logic
    if score < 50: suggestion = "Immediate hospitalization or ER visit recommended."
    elif score < 80: suggestion = "Consult a specialist within 24-48 hours."
    else: suggestion = "Maintain healthy habits and routine checkups."

    # Mock AI Prescription
    ai_rx = []
    if "Fever" in data.symptoms: ai_rx.append("Paracetamol 500mg (SOS)")
    if "Chest Pain" in data.symptoms: ai_rx.append("Aspirin 75mg (Emergency Use Only)")
    if data.sys > 150: ai_rx.append("Amlodipine 5mg (Consult Cardiologist)")
    if data.sugar > 200: ai_rx.append("Metformin 500mg (Consult Diabetologist)")
    if data.spo2 < 92: ai_rx.append("Oxygen Therapy (Immediate)")
    
    ai_rx_str = ", ".join(ai_rx) if ai_rx else "No acute medication recommended."

    # SQLite Save
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO health_checks 
            (device_id, age, gender, height, weight, hr, sys, dia, sugar, temp, symptoms, duration, score, risk, suggestion, dept, spo2)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.device_id, data.age, data.gender, data.height, data.weight, 
            data.hr, data.sys, data.dia, data.sugar, data.temp, 
            ",".join(data.symptoms), data.duration, score, risk, suggestion, dept, data.spo2
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")
        raise HTTPException(status_code=500, detail="Database insertion failed")

    return {
        "success": True,
        "score": score,
        "risk": risk,
        "suggestion": suggestion,
        "dept": dept,
        "ai_prescription": ai_rx_str
    }

# --- MOOD LOGS & REMINDERS API ---
@app.post("/mood-log")
def log_mood(data: MoodData):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO mood_logs (device_id, mood_label, mood_score, note) VALUES (?, ?, ?, ?)", 
                   (data.device_id, data.mood_label, data.mood_score, data.note))
    conn.commit()
    conn.close()
    return {"success": True}

@app.get("/mood-history/{device_id}")
def get_mood_history(device_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mood_logs WHERE device_id = ? ORDER BY timestamp DESC LIMIT 30", (device_id,))
    rows = cursor.fetchall()
    conn.close()
    return {"history": [dict(r) for r in rows]}

@app.post("/reminder")
def add_reminder(data: ReminderData):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO reminders (device_id, task, time, type) VALUES (?, ?, ?, ?)", 
                   (data.device_id, data.task, data.time, data.type))
    conn.commit()
    conn.close()
    return {"success": True}

@app.get("/reminders/{device_id}")
def get_reminders(device_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reminders WHERE device_id = ? AND completed = 0 ORDER BY time ASC", (device_id,))
    rows = cursor.fetchall()
    conn.close()
    return {"reminders": [dict(r) for r in rows]}

@app.delete("/reminder/{rem_id}")
def delete_reminder(rem_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reminders WHERE id = ?", (rem_id,))
    conn.commit()
    conn.close()
    return {"success": True}

# --- 50 FAKE DOCTORS DATA ---
DOCTORS = [
    {"id": i, "name": f"Dr. {name}", "specialty": spec, "exp": exp, "rating": 4.5 + (i % 5) / 10, "fees": 500 + (i * 10)}
    for i, (name, spec, exp) in enumerate([
        ("Arjun Mehta", "Cardiology", "15 years"), ("Sanya Iyer", "Neurology", "10 years"), 
        ("Rohan Sharma", "Orthopedics", "12 years"), ("Ananya Gupta", "Pediatrics", "8 years"),
        ("Vikram Singh", "Dermatology", "20 years"), ("Priya Das", "Gastroenterology", "11 years"),
        ("Kabir Khan", "Psychiatry", "14 years"), ("Ishani Roy", "Ophthalmology", "9 years"),
        ("Amitabh Bose", "Oncology", "18 years"), ("Sneha Patil", "Urology", "7 years"),
        ("Rahul Verma", "Endocrinology", "13 years"), ("Zara Sheikh", "ENT", "10 years"),
        ("Kunal Sen", "Nephrology", "16 years"), ("Ritu Malik", "Gynecology", "15 years"),
        ("Sahil Kapur", "Pulmonology", "12 years"), ("Tanya Bajaj", "Dentistry", "8 years"),
        ("Abhay Joshi", "Rheumatology", "19 years"), ("Mansi Negi", "Hematology", "11 years"),
        ("Neil D'Souza", "General Physician", "14 years"), ("Pooja Hegde", "Plastic Surgery", "9 years"),
        ("Varun Dhawan", "Cardiology", "11 years"), ("Alia Bhatt", "Neurology", "15 years"),
        ("Ranbir Kapoor", "Orthopedics", "12 years"), ("Deepika Padukone", "Pediatrics", "18 years"),
        ("Hrithik Roshan", "Dermatology", "14 years"), ("Katrina Kaif", "Gastroenterology", "9 years"),
        ("Akshay Kumar", "Psychiatry", "22 years"), ("Kareena Kapoor", "Ophthalmology", "16 years"),
        ("Salman Khan", "Oncology", "19 years"), ("Priyanka Chopra", "Urology", "13 years"),
        ("Aamir Khan", "Endocrinology", "17 years"), ("Anushka Sharma", "ENT", "11 years"),
        ("Vicky Kaushal", "Nephrology", "8 years"), ("Janhavi Kapoor", "Gynecology", "10 years"),
        ("Kartik Aaryan", "Pulmonology", "9 years"), ("Sara Ali Khan", "Dentistry", "7 years"),
        ("Ayushmann Khurrana", "Rheumatology", "14 years"), ("Taapsee Pannu", "Hematology", "12 years"),
        ("Rajkummar Rao", "General Physician", "13 years"), ("Bhumi Pednekar", "Plastic Surgery", "11 years"),
        ("Shah Rukh Khan", "Cardiology", "25 years"), ("Madhuri Dixit", "Neurology", "20 years"),
        ("Amitabh Bachchan", "Orthopedics", "35 years"), ("Tabu", "Pediatrics", "22 years"),
        ("Irrfan Khan", "Dermatology", "30 years"), ("Vidya Balan", "Gastroenterology", "18 years"),
        ("Naseeruddin Shah", "Psychiatry", "40 years"), ("Shabana Azmi", "Ophthalmology", "38 years"),
        ("Pankaj Tripathi", "Oncology", "15 years"), ("Radhika Apte", "Urology", "12 years")
    ])
]

@app.get("/doctors")
def get_doctors():
    return DOCTORS

# --- END OF DOCTOR DATA ---

@app.get("/health-history/{device_id}")
def get_history(device_id: str):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM health_checks WHERE device_id = ? ORDER BY timestamp DESC", (device_id,))
    rows = cursor.fetchall()
    conn.close()

    history = []
    for r in rows:
        history.append({
            "id": r["id"],
            "date": r["timestamp"].split(" ")[0] if r["timestamp"] else "N/A",
            "score": r["score"],
            "risk": r["risk"],
            "dept": r["dept"],
            "suggestion": r["suggestion"],
            "sys": r["sys"],
            "dia": r["dia"],
            "sugar": r["sugar"]
        })
    
    trend = "Stable"
    if len(history) >= 2:
        if history[0]["score"] > history[1]["score"]: trend = "Health Improving"
        elif history[0]["score"] < history[1]["score"]: trend = "Health Declining"

    return {"history": history, "trend": trend}

@app.delete("/health-entry/{entry_id}")
def delete_entry(entry_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM health_checks WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()
    return {"success": True}

@app.delete("/health-history/{device_id}")
def delete_history(device_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM health_checks WHERE device_id = ?", (device_id,))
    conn.commit()
    conn.close()
    return {"success": True}

# Web Routes
@app.get("/", response_class=HTMLResponse)
def serve_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/login", response_class=HTMLResponse)
def serve_login():
    with open("login.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard():
    with open("pateintportal.html", "r", encoding="utf-8") as f:
        return f.read().replace("{{ user_name }}", "Patient")

@app.get("/health-check")
async def health_check_page():
    return FileResponse("health-check.html")

@app.get("/reports")
async def reports_page():
    return FileResponse("reports.html")

@app.get("/appointments")
async def appointments_page():
    return FileResponse("appointments.html")

@app.get("/reminders-page")
async def reminders_page():
    return FileResponse("reminders.html")

@app.get("/prescriptions")
async def prescriptions_page():
    return FileResponse("prescriptions.html")

@app.get("/bmi-check")
async def bmi_check_page():
    return FileResponse("bmi-check.html")

@app.get("/mood-check")
async def mood_check_page():
    return FileResponse("mood-check.html")

@app.get("/logout")
def serve_logout():
    # Because there's no auth, we just redirect them home gracefully if they smash Logout
    return RedirectResponse(url="/")

@app.get("/appointment")
@app.get("/appointments")
def redirect_appointments():
    return RedirectResponse(url="/dashboard#appointments")

@app.get("/report")
@app.get("/reports")
def redirect_reports():
    return RedirectResponse(url="/dashboard#reports")

# Mount static files (like style.css)
app.mount("/", StaticFiles(directory="."), name="static")

if __name__ == "__main__":
    import uvicorn
    # Use 0.0.0.0 to listen on all IPv4 interfaces for maximum compatibility
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)
