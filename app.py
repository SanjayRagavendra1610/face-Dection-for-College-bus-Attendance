
from flask import Flask, render_template, Response, request, redirect, url_for, session, jsonify
import cv2, os, pandas as pd
from datetime import datetime
from firebase_config import db

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Change this to a random secret key

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("trainer/trainer.yml")

faceCascade = cv2.CascadeClassifier("haarcascade.xml")
cam = cv2.VideoCapture(0)
os.makedirs("Attendance", exist_ok=True)

def gen_frames():
    while True:
        success, frame = cam.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = faceCascade.detectMultiScale(gray,1.2,5)

        for (x,y,w,h) in faces:
            id, conf = recognizer.predict(gray[y:y+h,x:x+w])
            if conf < 60:
                status = f"ID {id} Present"
                df = pd.DataFrame([[id, datetime.now().strftime("%d-%m-%Y"),
                                     datetime.now().strftime("%H:%M:%S")]],
                                     columns=["ID","Date","Time"])
                df.to_csv("Attendance/Attendance.csv",
                          mode="a", index=False,
                          header=not os.path.exists("Attendance/Attendance.csv"))
                color=(0,255,0)
            else:
                status="Wrong Face Detected"
                color=(0,0,255)

            cv2.rectangle(frame,(x,y),(x+w,y+h),color,2)
            cv2.putText(frame,status,(20,40),
                        cv2.FONT_HERSHEY_SIMPLEX,1,color,2)

        ret, buffer = cv2.imencode(".jpg", frame)
        frame = buffer.tobytes()
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n"+frame+b"\r\n")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/video")
def video():
    return Response(gen_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/admin")
def admin_login():
    return render_template("admin_login.html")

@app.route("/admin-login", methods=["POST"])
def admin_login_process():
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    # Admin credentials
    if username == "sanjayraga1610vino@gmail.com" and password == "161016":
        session["admin_logged_in"] = True
        session["admin_username"] = username
        return redirect(url_for("admin_dashboard"))
    else:
        return redirect(url_for("admin_login"))

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    return render_template("admin_dashboard.html")

@app.route("/admin-logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

# ==================== DASHBOARD ROUTES ====================

@app.route("/register")
def register():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    return render_template("register.html")

@app.route("/register", methods=["POST"])
def register_student():
    try:
        student_id = request.form.get("student_id")
        name = request.form.get("name")
        email = request.form.get("email")
        department = request.form.get("department")
        year = request.form.get("year")
        
        # Save to Firebase if available
        if db:
            db.collection("students").document(str(student_id)).set({
                "student_id": student_id,
                "name": name,
                "email": email,
                "department": department,
                "year": year,
                "status": "active",
                "created_at": datetime.now()
            })
        else:
            print(f"⚠️  Firebase unavailable - student data not saved to database")
        
        return redirect("/register")
    except Exception as e:
        print(f"Error registering student: {e}")
        return redirect("/register")

@app.route("/train")
def train():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    return render_template("train.html")

@app.route("/train", methods=["POST"])
def train_model():
    try:
        # Import train_model function
        from train_model import train_recognizer
        train_recognizer()
        return redirect("/train")
    except Exception as e:
        print(f"Error training model: {e}")
        return redirect("/train")

@app.route("/attendance")
def attendance():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    return render_template("attendance.html")

@app.route("/manage-users")
def manage_users():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    return render_template("manage_users.html")

# ==================== API ROUTES ====================

@app.route("/api/students", methods=["GET"])
def get_students():
    try:
        students = []
        if db:
            docs = db.collection("students").stream()
            for doc in docs:
                students.append(doc.to_dict())
        return jsonify({"students": students})
    except Exception as e:
        print(f"Error fetching students: {e}")
        return jsonify({"students": []})

@app.route("/api/students", methods=["POST"])
def add_student():
    try:
        data = request.get_json()
        student_id = data.get("student_id")
        
        if db:
            db.collection("students").document(str(student_id)).set({
                "student_id": student_id,
                "name": data.get("name"),
                "email": data.get("email"),
                "department": data.get("department"),
                "year": data.get("year"),
                "status": "active",
                "created_at": datetime.now()
            })
        else:
            print(f"⚠️  Firebase unavailable - student {student_id} not saved to database")
        
        return jsonify({"success": True, "message": "Student added successfully"})
    except Exception as e:
        print(f"Error adding student: {e}")
        return jsonify({"success": False, "message": str(e)}), 400

@app.route("/api/students/<student_id>", methods=["DELETE"])
def delete_student(student_id):
    try:
        if db:
            db.collection("students").document(str(student_id)).delete()
        return jsonify({"success": True, "message": "Student deleted successfully"})
    except Exception as e:
        print(f"Error deleting student: {e}")
        return jsonify({"success": False, "message": str(e)}), 400

@app.route("/api/attendance", methods=["GET"])
def get_attendance():
    try:
        records = []
        
        # Try to read from CSV first
        if os.path.exists("Attendance/Attendance.csv"):
            df = pd.read_csv("Attendance/Attendance.csv")
            for _, row in df.iterrows():
                records.append({
                    "date": str(row.get("Date", "")),
                    "time": str(row.get("Time", "")),
                    "student_id": str(row.get("ID", "")),
                    "status": "Present"
                })
        
        # Fetch from Firebase to enrich with names (if available)
        if db:
            students = {str(doc.id): doc.to_dict() for doc in db.collection("students").stream()}
        else:
            students = {}
        
        for record in records:
            student_info = students.get(record["student_id"], {})
            record["student_name"] = student_info.get("name", "Unknown")
            record["department"] = student_info.get("department", "")
        
        return jsonify({"records": records})
    except Exception as e:
        print(f"Error fetching attendance: {e}")
        return jsonify({"records": []})

@app.route("/api/stats", methods=["GET"])
def get_stats():
    try:
        # Get total students
        if db:
            students_count = len(list(db.collection("students").stream()))
        else:
            students_count = 0
        
        # Get total faces (count files in dataset)
        faces_count = 0
        for root, dirs, files in os.walk("dataset"):
            faces_count += len(files)
        
        return jsonify({
            "students": students_count,
            "faces": faces_count
        })
    except Exception as e:
        print(f"Error fetching stats: {e}")
        return jsonify({"students": 0, "faces": 0})

if __name__ == "__main__":
    app.run(debug=True)
