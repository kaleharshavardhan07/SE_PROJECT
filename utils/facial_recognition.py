# import cv2
# import face_recognition
# import numpy as np
# import os
# import pickle
# from pymongo import MongoClient
# from bson.objectid import ObjectId
# import tempfile
# from datetime import datetime

# # MongoDB connection
# client = MongoClient(os.getenv('MONGO_URI', 'mongodb://localhost:27017/'))
# db = client[os.getenv('DB_NAME', 'facial_attendance_db')]

# def extract_faces_from_image(image_path):
#     """Extract face encodings from a single image"""
#     image = face_recognition.load_image_file(image_path)
#     face_locations = face_recognition.face_locations(image)
#     face_encodings = face_recognition.face_encodings(image, face_locations)
    
#     return face_encodings

# def register_student_face(student_id, image_path):
#     """Register a student's face in the database"""
#     # Extract face encodings
#     face_encodings = extract_faces_from_image(image_path)
    
#     if not face_encodings:
#         return False, "No face detected in the image"
    
#     if len(face_encodings) > 1:
#         return False, "Multiple faces detected. Please upload an image with only your face"
    
#     # Store the face encoding in the database
#     face_encoding = face_encodings[0].tolist()  # Convert numpy array to list for MongoDB
    
#     db.students.update_one(
#         {'_id': ObjectId(student_id)},
#         {'$set': {'face_encoding': face_encoding}}
#     )
    
#     return True, "Face registered successfully"

# def process_attendance_video(video_path, class_id, subject_id):
#     """Process a video file for attendance"""
#     # Create a temporary directory to store frames
#     temp_dir = tempfile.mkdtemp()
    
#     # Open the video file
#     video = cv2.VideoCapture(video_path)
    
#     # Get basic video info
#     fps = video.get(cv2.CAP_PROP_FPS)
#     frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
#     duration = frame_count / fps
    
#     # We'll process frames at 1-second intervals
#     frames_to_process = int(duration)
#     frame_interval = int(fps)
    
#     # Get all students in this class
#     students = list(db.students.find({'class_id': ObjectId(class_id)}))
#     known_face_encodings = []
#     known_face_ids = []
    
#     for student in students:
#         if 'face_encoding' in student:
#             known_face_encodings.append(np.array(student['face_encoding']))
#             known_face_ids.append(str(student['_id']))
    
#     # If no students with face encodings, return
#     if not known_face_encodings:
#         return {"error": "No registered students with facial data found for this class"}
    
#     # Track students who are detected in the video
#     detected_students = set()
    
#     # Process frames
#     for i in range(0, frames_to_process):
#         # Set the frame position
#         video.set(cv2.CAP_PROP_POS_FRAMES, i * frame_interval)
#         ret, frame = video.read()
        
#         if not ret:
#             break
            
#         # Save frame as a file
#         frame_path = os.path.join(temp_dir, f"frame_{i}.jpg")
#         cv2.imwrite(frame_path, frame)
        
#         # Process the frame for face recognition
#         rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         face_locations = face_recognition.face_locations(rgb_frame)
#         face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
#         # Check each face against known faces
#         for face_encoding in face_encodings:
#             matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)
#             face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            
#             if any(matches):
#                 best_match_index = np.argmin(face_distances)
#                 if matches[best_match_index]:
#                     student_id = known_face_ids[best_match_index]
#                     detected_students.add(student_id)
    
#     # Clean up
#     video.release()
    
#     # Create attendance session
#     session_id = db.attendance_sessions.insert_one({
#         'class_id': ObjectId(class_id),
#         'subject_id': ObjectId(subject_id),
#         'date': datetime.now(),
#         'video_path': video_path,
#         'processed': True
#     }).inserted_id
    
#     # Mark attendance for detected students
#     for student_id in detected_students:
#         db.attendance.insert_one({
#             'student_id': ObjectId(student_id),
#             'session_id': session_id,
#             'class_id': ObjectId(class_id),
#             'subject_id': ObjectId(subject_id),
#             'date': datetime.now(),
#             'present': True
#         })
    
#     # Mark absence for non-detected students
#     absent_students = set(str(student['_id']) for student in students) - detected_students
#     for student_id in absent_students:
#         db.attendance.insert_one({
#             'student_id': ObjectId(student_id),
#             'session_id': session_id,
#             'class_id': ObjectId(class_id),
#             'subject_id': ObjectId(subject_id),
#             'date': datetime.now(),
#             'present': False
#         })
    
#     return {
#         "session_id": str(session_id),
#         "total_students": len(students),
#         "present": len(detected_students),
#         "absent": len(absent_students)
#     }


# facial_recognition.py
import cv2
import face_recognition
import numpy as np
import os
import pickle
import tempfile
from datetime import datetime
from bson.objectid import ObjectId

class FacialRecognition:
    def __init__(self, db):
        """Initialize with database connection"""
        self.db = db
        
    def extract_faces_from_image(self, image_path):
        """Extract face encodings from a single image"""
        image = face_recognition.load_image_file(image_path)
        face_locations = face_recognition.face_locations(image)
        face_encodings = face_recognition.face_encodings(image, face_locations)
        
        return face_encodings
    
    def register_student_face(self, student_id, image_path):
        """Register a student's face in the database"""
        # Extract face encodings
        face_encodings = self.extract_faces_from_image(image_path)
        
        if not face_encodings:
            return False, "No face detected in the image"
        
        if len(face_encodings) > 1:
            return False, "Multiple faces detected. Please upload an image with only your face"
        
        # Store the face encoding in the database
        face_encoding = face_encodings[0].tolist()  # Convert numpy array to list for MongoDB
        
        self.db.students.update_one(
            {'_id': ObjectId(student_id)},
            {'$set': {'face_encoding': face_encoding}}
        )
        
        return True, "Face registered successfully"
    
    def process_attendance_video(self, video_path, class_id, subject_id, teacher_id):
        """Process a video file for attendance"""
        # Create a temporary directory to store frames
        temp_dir = tempfile.mkdtemp()
        
        # Open the video file
        video = cv2.VideoCapture(video_path)
        
        # Get basic video info
        fps = video.get(cv2.CAP_PROP_FPS)
        frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        
        # We'll process frames at 1-second intervals
        frames_to_process = int(duration)
        frame_interval = int(fps)
        
        # Get all students in this class
        students = list(self.db.students.find({'class_id': ObjectId(class_id)}))
        known_face_encodings = []
        known_face_ids = []
        
        for student in students:
            if 'face_encoding' in student:
                known_face_encodings.append(np.array(student['face_encoding']))
                known_face_ids.append(str(student['_id']))
        
        # If no students with face encodings, return
        if not known_face_encodings:
            return {
                "error": "No registered students with facial data found for this class",
                "students": students
            }
        
        # Track students who are detected in the video
        detected_students = set()
        
        # Process frames
        for i in range(0, frames_to_process):
            # Set the frame position
            video.set(cv2.CAP_PROP_POS_FRAMES, i * frame_interval)
            ret, frame = video.read()
            
            if not ret:
                break
                
            # Save frame as a file
            frame_path = os.path.join(temp_dir, f"frame_{i}.jpg")
            cv2.imwrite(frame_path, frame)
            
            # Process the frame for face recognition
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            # Check each face against known faces
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)
                
                if True in matches:
                    face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        student_id = known_face_ids[best_match_index]
                        detected_students.add(student_id)
        
        # Clean up
        video.release()
        
        # Create attendance session
        session_id = self.db.attendance_sessions.insert_one({
            'teacher_id': ObjectId(teacher_id),
            'class_id': ObjectId(class_id),
            'subject_id': ObjectId(subject_id),
            'date': datetime.now(),
            'video_path': video_path,
            'processed': True
        }).inserted_id
        
        # Mark attendance for detected students
        for student_id in detected_students:
            self.db.attendance.insert_one({
                'student_id': ObjectId(student_id),
                'session_id': session_id,
                'class_id': ObjectId(class_id),
                'subject_id': ObjectId(subject_id),
                'date': datetime.now(),
                'present': True
            })
        
        # Mark absence for non-detected students
        absent_students = set(str(student['_id']) for student in students) - detected_students
        for student_id in absent_students:
            self.db.attendance.insert_one({
                'student_id': ObjectId(student_id),
                'session_id': session_id,
                'class_id': ObjectId(class_id),
                'subject_id': ObjectId(subject_id),
                'date': datetime.now(),
                'present': False
            })
        
        return {
            "session_id": str(session_id),
            "total_students": len(students),
            "present": len(detected_students),
            "absent": len(absent_students),
            "present_students": list(detected_students),
            "absent_students": list(absent_students)
        }
