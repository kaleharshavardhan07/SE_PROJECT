
# # utils/video_processing.py
# import cv2
# import os
# import tempfile
# from datetime import datetime

# def extract_frames(video_path, output_dir=None, interval_seconds=1):
#     """
#     Extract frames from a video at specified intervals
    
#     Args:
#         video_path: Path to the video file
#         output_dir: Directory to save frames (if None, creates a temp directory)
#         interval_seconds: Interval between frames in seconds
        
#     Returns:
#         List of paths to extracted frames
#     """
#     if output_dir is None:
#         output_dir = tempfile.mkdtemp()
    
#     # Open the video
#     video = cv2.VideoCapture(video_path)
    
#     # Get video properties
#     fps = video.get(cv2.CAP_PROP_FPS)
#     frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
#     duration = frame_count / fps
    
#     # Calculate frame interval
#     frame_interval = int(fps * interval_seconds)
    
#     frame_paths = []
#     frame_number = 0
    
#     while True:
#         # Set frame position
#         video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
#         ret, frame = video.read()
        
#         if not ret:
#             break
            
#         # Save the frame
#         timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
#         frame_path = os.path.join(output_dir, f"frame_{timestamp}.jpg")
#         cv2.imwrite(frame_path, frame)
#         frame_paths.append(frame_path)
        
#         # Move to next frame position
#         frame_number += frame_interval
#         if frame_number >= frame_count:
#             break
    
#     # Release the video
#     video.release()
    
#     return frame_paths

# utils/video_processing.py
def extract_frames(video_path, output_dir=None, interval_seconds=1):
    """
    Extract frames from a video at specified intervals
    Args:
        video_path: Path to the video file
        output_dir: Directory to save frames (if None, creates a temp directory)
        interval_seconds: Interval between frames in seconds
    Returns:
        List of paths to extracted frames
    """
    if output_dir is None:
        output_dir = tempfile.mkdtemp()
        
    # Open the video
    video = cv2.VideoCapture(video_path)
    
    # Get video properties
    fps = video.get(cv2.CAP_PROP_FPS)
    frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps
    
    # Calculate frame interval
    frame_interval = int(fps * interval_seconds)
    
    frame_paths = []
    frame_number = 0
    
    while True:
        # Set frame position
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = video.read()
        
        if not ret:
            break
            
        # Save the frame
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        frame_path = os.path.join(output_dir, f"frame_{timestamp}.jpg")
        cv2.imwrite(frame_path, frame)
        frame_paths.append(frame_path)
        
        # Move to next frame position
        frame_number += frame_interval
        if frame_number >= frame_count:
            break
    
    # Release the video
    video.release()
    
    return frame_paths
