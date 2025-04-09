



```markdown
# 👨‍🏫 Facial Recognition Attendance System

A web-based facial recognition attendance system built using **Flask**, **OpenCV**, **face-recognition**, and **MongoDB**, supporting **role-based authentication** for admins, teachers, and students.

---

## 🔍 Overview

This application enables facial recognition-based attendance management with secure login for different user roles:

- 👨‍💼 **Admin**: Manage users (add teachers/students), view logs.
- 👨‍🏫 **Teacher**: Mark and view attendance of their classes.
- 👨‍🎓 **Student**: View personal attendance records.

Facial verification ensures authenticated, tamper-proof attendance marking.

---

## 🧠 System Architecture

![Flowchart](./A_README_file_for_a_Facial_Recognition_Attendance_.png)

### 🔄 Workflow

1. **Login Page**: Role-based authentication via username & password.
2. **Admin Dashboard**:
   - Add new users with role.
   - View logs.
3. **Teacher Dashboard**:
   - Select class → Start camera.
   - System recognizes students using **face-recognition**.
   - Attendance marked in **MongoDB**.
4. **Student Dashboard**:
   - View individual attendance records.
5. **Facial Recognition**:
   - Utilizes **OpenCV** and **face-recognition** libraries to match real-time webcam input with stored encodings.

---

## 🚀 Technologies Used

| Technology        | Purpose                        |
|------------------|--------------------------------|
| Flask            | Web framework                  |
| MongoDB          | NoSQL database                 |
| OpenCV           | Camera interfacing             |
| face-recognition | Facial recognition             |
| gunicorn         | Production deployment          |
| python-dotenv    | Manage environment variables   |

---

## 📦 Requirements

Install dependencies with:

```bash
pip install -r requirements.txt
```

`requirements.txt` should include:

```
Flask==2.2.3
pymongo==4.3.3
python-dotenv==1.0.0
Werkzeug==2.2.3
opencv-python==4.7.0.72
face-recognition==1.3.0
numpy<=2
Pillow==9.4.0
gunicorn==20.1.0
```

---

## ⚙️ Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/kaleharshavardhan07/SE_PROJECT.git
cd SE_PROJECT
```

### 2. Set up `.env` file

Create a `.env` file in the root directory and add:

```bash
MONGO_URI=mongodb://localhost:27017/
DB_NAME=facial_attendance_db
SECRET_KEY=your-secret-key-for-sessions
```

### 3. Run MongoDB

Ensure MongoDB is running on your local machine:

```bash
mongod --dbpath /path/to/your/db
```

### 4. Run in development mode

```bash
python app.py
```

Visit `http://127.0.0.1:5000`

### 5. Run in production with Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

---

## 👤 User Roles & Permissions

| Role     | Features                                        |
|----------|-------------------------------------------------|
| Admin    | Add/view/delete users, view system logs         |
| Teacher  | Start attendance, view class attendance         |
| Student  | View personal attendance records                |

---

## 🧪 Face Registration & Attendance

- Each student must first register their face via the camera.
- Face encodings are stored securely.
- During attendance:
  - The system captures faces via webcam.
  - Encodings are compared with the database.
  - Match → Mark attendance with timestamp.

---



## 🧑‍💻 Author

**Harshavardhan Kale**  
COEP Technological University  
Software Engineering Project 2024-25  

---

## 📄 License

MIT License

---
