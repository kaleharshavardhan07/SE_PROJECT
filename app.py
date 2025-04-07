

# app.py
from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-key-for-sessions')

# MongoDB connection
client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
db = client[os.getenv('DB_NAME', 'facial_attendance_db')]

# Authentication decorators
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            flash('Admin access required', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'teacher':
            flash('Teacher access required', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'student':
            flash('Student access required', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'info')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check in all collections
        user = None
        for role in ['admin', 'teacher', 'student']:
            user_doc = db[role+'s'].find_one({'email': email})
            if user_doc and check_password_hash(user_doc['password'], password):
                if role == 'student' and not user_doc.get('verified', False):
                    flash('Your account is pending verification by admin', 'warning')
                    return redirect(url_for('login'))
                
                user = user_doc
                session['user_id'] = str(user_doc['_id'])
                session['name'] = user_doc['name']
                session['email'] = user_doc['email']
                session['role'] = role
                
                flash(f'Welcome {user_doc["name"]}!', 'success')
                return redirect(url_for(f'{role}_dashboard'))
        
        flash('Invalid email or password', 'danger')
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

from utils.facial_recognition import FacialRecognition



# Initialize the facial recognition system with your database
facial_recognition = FacialRecognition(db)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        student_id = request.form.get('student_id')
        class_id = request.form.get('class_id')
        
        # Check if student ID or email already exists
        if db.students.find_one({'email': email}):
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        if db.students.find_one({'student_id': student_id}):
            flash('Student ID already registered', 'danger')
            return redirect(url_for('register'))
        
        # Handle photo upload for facial recognition
        if 'photo' not in request.files:
            flash('No photo uploaded', 'danger')
            return redirect(request.url)
            
        photo = request.files['photo']
        if photo.filename == '':
            flash('No photo selected', 'danger')
            return redirect(request.url)
        
        # Save photo and process for facial recognition
        photo_path = os.path.join('static/uploads/students', f"{student_id}.jpg")
        photo.save(photo_path)
        
        # Insert new student
        student = {
            'name': name,
            'email': email,
            'password': generate_password_hash(password),
            'student_id': student_id,
            'class_id': ObjectId(class_id) if class_id else None,
            'photo_path': photo_path,
            'verified': False,  # Needs admin verification
            'created_at': datetime.datetime.now()
        }
        
        student_id = db.students.insert_one(student).inserted_id
        
        # Register face encoding
        success, message = facial_recognition.register_student_face(student_id, photo_path)
        if not success:
            flash(f'Registration successful but face registration failed: {message}', 'warning')
        else:
            flash('Registration successful! Wait for admin verification.', 'success')
            
        return redirect(url_for('login'))
        
    classes = list(db.classes.find())
    return render_template('register.html', classes=classes)

# Admin routes
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    stats = {
        'teachers': db.teachers.count_documents({}),
        'students': db.students.count_documents({}),
        'classes': db.classes.count_documents({}),
        'subjects': db.subjects.count_documents({}),
        'pending_verifications': db.students.count_documents({'verified': False})
    }
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/teachers')
@admin_required
def manage_teachers():
    teachers = list(db.teachers.find())
    return render_template('admin/teachers.html', teachers=teachers)

@app.route('/admin/teachers/add', methods=['GET', 'POST'])
@admin_required
def add_teacher():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if db.teachers.find_one({'email': email}):
            flash('Email already registered', 'danger')
            return redirect(url_for('add_teacher'))
            
        teacher = {
            'name': name,
            'email': email,
            'password': generate_password_hash(password),
            'created_at': datetime.datetime.now()
        }
        
        db.teachers.insert_one(teacher)
        flash('Teacher added successfully', 'success')
        return redirect(url_for('manage_teachers'))
        
    return render_template('admin/add_teacher.html')

@app.route('/admin/teachers/delete/<teacher_id>')
@admin_required
def delete_teacher(teacher_id):
    db.teachers.delete_one({'_id': ObjectId(teacher_id)})
    flash('Teacher deleted successfully', 'success')
    return redirect(url_for('manage_teachers'))

@app.route('/admin/classes')
@admin_required
def manage_classes():
    classes = list(db.classes.find())
    return render_template('admin/classes.html', classes=classes)

@app.route('/admin/classes/add', methods=['GET', 'POST'])
@admin_required
def add_class():
    if request.method == 'POST':
        name = request.form.get('name')
        
        if db.classes.find_one({'name': name}):
            flash('Class already exists', 'danger')
            return redirect(url_for('add_class'))
            
        class_data = {
            'name': name,
            'created_at': datetime.datetime.now()
        }
        
        db.classes.insert_one(class_data)
        flash('Class added successfully', 'success')
        return redirect(url_for('manage_classes'))
        
    return render_template('admin/add_class.html')

@app.route('/admin/classes/delete/<class_id>')
@admin_required
def delete_class(class_id):
    db.classes.delete_one({'_id': ObjectId(class_id)})
    flash('Class deleted successfully', 'success')
    return redirect(url_for('manage_classes'))

@app.route('/admin/subjects')
@admin_required
def manage_subjects():
    subjects = list(db.subjects.find())
    classes = list(db.classes.find())
    return render_template('admin/subjects.html', subjects=subjects, classes=classes)

@app.route('/admin/subjects/add', methods=['GET', 'POST'])
@admin_required
def add_subject():
    if request.method == 'POST':
        name = request.form.get('name')
        class_id = request.form.get('class_id')
        
        if db.subjects.find_one({'name': name, 'class_id': ObjectId(class_id)}):
            flash('Subject already exists for this class', 'danger')
            return redirect(url_for('add_subject'))
            
        subject = {
            'name': name,
            'class_id': ObjectId(class_id),
            'created_at': datetime.datetime.now()
        }
        
        db.subjects.insert_one(subject)
        flash('Subject added successfully', 'success')
        return redirect(url_for('manage_subjects'))
    
    classes = list(db.classes.find())    
    return render_template('admin/add_subject.html', classes=classes)

@app.route('/admin/subjects/delete/<subject_id>')
@admin_required
def delete_subject(subject_id):
    db.subjects.delete_one({'_id': ObjectId(subject_id)})
    flash('Subject deleted successfully', 'success')
    return redirect(url_for('manage_subjects'))

@app.route('/admin/verifications')
@admin_required
def pending_verifications():
    students = list(db.students.find({'verified': False}))
    return render_template('admin/verifications.html', students=students)


@app.route('/admin/verify/<student_id>')
@admin_required
def verify_student(student_id):
    student = db.students.find_one({'_id': ObjectId(student_id)})
    
    if not student:
        flash('Student not found', 'danger')
        return redirect(url_for('pending_verifications'))
    
    # Check if face encoding exists
    if 'face_encoding' not in student:
        # Try to register face again
        success, message = facial_recognition.register_student_face(student_id, student['photo_path'])
        if not success:
            flash(f'Student verification failed: {message}', 'danger')
            return redirect(url_for('pending_verifications'))
    
    # Mark student as verified
    db.students.update_one(
        {'_id': ObjectId(student_id)},
        {'$set': {'verified': True}}
    )
    
    flash('Student verified successfully', 'success')
    return redirect(url_for('pending_verifications'))
# Teacher routes
@app.route('/teacher/dashboard')
@teacher_required
def teacher_dashboard():
    stats = {
        'classes': list(db.classes.find()),
        'subjects': list(db.subjects.find()),
        'attendance_sessions': db.attendance_sessions.count_documents({'teacher_id': ObjectId(session['user_id'])})
    }
    return render_template('teacher/dashboard.html', stats=stats)

@app.route('/teacher/take-attendance', methods=['GET', 'POST'])
@teacher_required
def take_attendance():
    if request.method == 'POST':
        class_id = request.form.get('class_id')
        subject_id = request.form.get('subject_id')
        
        # Handle video upload
        if 'video' not in request.files:
            flash('No video uploaded', 'danger')
            return redirect(request.url)
            
        video = request.files['video']
        if video.filename == '':
            flash('No video selected', 'danger')
            return redirect(request.url)
        
        # Save video temporarily
        video_path = os.path.join('static/uploads/attendance_videos', f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.mp4")
        os.makedirs(os.path.dirname(video_path), exist_ok=True)
        video.save(video_path)
        
        # Process video for facial recognition
        result = facial_recognition.process_attendance_video(
            video_path, 
            class_id, 
            subject_id, 
            session['user_id']
        )
        
        if 'error' in result:
            flash(f"Error processing attendance: {result['error']}", 'danger')
            return redirect(url_for('take_attendance'))
        
        flash(f"Attendance processed: {result['present']} present, {result['absent']} absent", 'success')
        return redirect(url_for('session_report', session_id=result['session_id']))
    
    classes = list(db.classes.find())
    subjects = list(db.subjects.find())
    return render_template('teacher/take_attendance.html', classes=classes, subjects=subjects)

@app.route('/teacher/process-attendance/<session_id>')
@teacher_required
def process_attendance(session_id):
    attendance_session = db.attendance_sessions.find_one({'_id': ObjectId(session_id)})
    if not attendance_session:
        flash('Attendance session not found', 'danger')
        return redirect(url_for('teacher_dashboard'))
    
    # Get the class and student information
    class_id = attendance_session['class_id']
    students = list(db.students.find({'class_id': class_id}))
    
    # Get attendance records for this session
    attendance_records = list(db.attendance.find({'session_id': ObjectId(session_id)}))
    
    # Create a dictionary mapping student IDs to attendance status
    attendance_map = {str(record['student_id']): record['present'] for record in attendance_records}
    
    # Add attendance status to student records
    for student in students:
        student['present'] = attendance_map.get(str(student['_id']), False)
    
    return render_template('teacher/process_attendance.html', 
                          attendance_session=attendance_session,
                          students=students)

@app.route('/teacher/mark-attendance', methods=['POST'])
@teacher_required
def mark_attendance():
    session_id = request.form.get('session_id')
    
    # Get the list of present students from form
    present_students = request.form.getlist('present_students')
    
    # Get all students in this class
    attendance_session = db.attendance_sessions.find_one({'_id': ObjectId(session_id)})
    class_id = attendance_session['class_id']
    students = list(db.students.find({'class_id': class_id}))
    
    # Delete existing attendance records for this session
    db.attendance.delete_many({'session_id': ObjectId(session_id)})
    
    # Mark attendance in database
    for student in students:
        student_id = str(student['_id'])
        is_present = student_id in present_students
        
        db.attendance.insert_one({
            'student_id': ObjectId(student_id),
            'session_id': ObjectId(session_id),
            'class_id': attendance_session['class_id'],
            'subject_id': attendance_session['subject_id'],
            'date': attendance_session['date'],
            'present': is_present
        })
    
    flash('Attendance marked successfully', 'success')
    return redirect(url_for('teacher_dashboard'))

@app.route('/teacher/reports')
@teacher_required
def attendance_reports():
    # Get all attendance sessions for this teacher
    sessions = list(db.attendance_sessions.find({'teacher_id': ObjectId(session['user_id'])}))

    for s in sessions:
        s['class'] = db.classes.find_one({'_id': s['class_id']})
        s['subject'] = db.subjects.find_one({'_id': s['subject_id']})

        # Get students who were present in this session
        present_entries = db.attendance.find({'session_id': s['_id'], 'present': True})

        present_students = []
        for record in present_entries:
            student = db.students.find_one({'_id': record['student_id']})
            if student:
                present_students.append(student['name'])

        s['present_students'] = present_students
        s['date'] = s['date'].strftime('%Y-%m-%d') if 'date' in s else 'N/A'

    return render_template('teacher/reports.html', sessions=sessions)

# @app.route('/teacher/reports')
# @teacher_required
# def attendance_reports():
#     # Get all attendance sessions for this teacher
#     sessions = list(db.attendance_sessions.find({'teacher_id': ObjectId(session['user_id'])}))
    
#     # Get class and subject names
#     for s in sessions:
#         s['class'] = db.classes.find_one({'_id': s['class_id']})
#         s['subject'] = db.subjects.find_one({'_id': s['subject_id']})
    
#     return render_template('teacher/reports.html', sessions=sessions)

@app.route('/teacher/report/<session_id>')
@teacher_required
def session_report(session_id):
    # Get attendance session details
    attendance_session = db.attendance_sessions.find_one({'_id': ObjectId(session_id)})
    if not attendance_session:
        flash('Attendance session not found', 'danger')
        return redirect(url_for('attendance_reports'))
    
    # Get class and subject info
    attendance_session['class'] = db.classes.find_one({'_id': attendance_session['class_id']})
    attendance_session['subject'] = db.subjects.find_one({'_id': attendance_session['subject_id']})
    
    # Get attendance records
    attendance_records = list(db.attendance.find({'session_id': ObjectId(session_id)}))
    
    # Get student details for each record
    for record in attendance_records:
        record['student'] = db.students.find_one({'_id': record['student_id']})
    
    return render_template('teacher/session_report.html', 
                          session=attendance_session,
                          records=attendance_records)

# Student routes
@app.route('/student/dashboard')
@student_required
def student_dashboard():
    student = db.students.find_one({'_id': ObjectId(session['user_id'])})
    
    # Get attendance statistics
    total_sessions = db.attendance_sessions.count_documents({'class_id': student.get('class_id', ObjectId())})
    attended_sessions = db.attendance.count_documents({
        'student_id': ObjectId(session['user_id']),
        'present': True
    })
    
    attendance_percentage = (attended_sessions / total_sessions * 100) if total_sessions > 0 else 0
    
    # Get recent attendance
    recent_attendance = list(db.attendance.find(
        {'student_id': ObjectId(session['user_id'])}
    ).sort('date', -1).limit(10))
    
    # Get session details for each attendance record
    for record in recent_attendance:
        record['session'] = db.attendance_sessions.find_one({'_id': record['session_id']})
        if record['session']:
            record['subject'] = db.subjects.find_one({'_id': record['session']['subject_id']})
    
    return render_template('student/dashboard.html', 
                          student=student,
                          stats={
                              'total_sessions': total_sessions,
                              'attended_sessions': attended_sessions,
                              'attendance_percentage': round(attendance_percentage, 2)
                          },
                          recent_attendance=recent_attendance)

@app.route('/student/attendance')
@student_required
def student_attendance():
    # Get all attendance records for this student
    records = list(db.attendance.find({'student_id': ObjectId(session['user_id'])}).sort('date', -1))
    
    # Get session and subject details for each record
    for record in records:
        record['session'] = db.attendance_sessions.find_one({'_id': record['session_id']})
        if record['session']:
            record['subject'] = db.subjects.find_one({'_id': record['session']['subject_id']})
            record['class'] = db.classes.find_one({'_id': record['session']['class_id']})
    
    return render_template('student/attendance.html', records=records)


if __name__ == '__main__':
    # Create admin user if none exists
    if db.admins.count_documents({}) == 0:
        db.admins.insert_one({
            'name': 'Admin',
            'email': 'admin@example.com',
            'password': generate_password_hash('admin123'),
            'created_at': datetime.datetime.now()
        })
        print("Admin user created with email: admin@example.com and password: admin123")
    
    app.run(debug=True)