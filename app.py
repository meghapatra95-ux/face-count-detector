import os
import sys
import cv2
import numpy as np
from flask import Flask, render_template, request, jsonify, Response
import threading
import time

# Add the src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
if src_dir not in sys.path:
    sys.path.append(src_dir)

try:
    from face_detector import FaceCountDetector
    print("✅ Successfully imported FaceCountDetector")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please make sure face_detector.py is in the src folder")
    sys.exit(1)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'

# Global variables for webcam
camera = None
face_detector = None
is_camera_active = False
current_frame = None
frame_lock = threading.Lock()
camera_initialized = False

def initialize_face_detector():
    """Initialize the face detector"""
    global face_detector
    try:
        face_detector = FaceCountDetector()
        print("✅ Face detector initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ Error initializing face detector: {e}")
        return False

def initialize_camera():
    """Initialize the camera"""
    global camera, is_camera_active
    
    try:
        # Initialize camera
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            # Try different camera indices
            for i in range(1, 4):
                camera = cv2.VideoCapture(i)
                if camera.isOpened():
                    print(f"✅ Camera found at index {i}")
                    break
            
            if not camera.isOpened():
                print("❌ No camera found!")
                return False
        
        # Set camera properties
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        camera.set(cv2.CAP_PROP_FPS, 30)
        
        is_camera_active = True
        print("✅ Camera initialized successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing camera: {e}")
        return False

def camera_worker():
    """Worker thread to continuously capture frames"""
    global camera, face_detector, is_camera_active, current_frame
    
    while is_camera_active:
        try:
            if camera and camera.isOpened():
                success, frame = camera.read()
                if success:
                    # Process frame for face detection
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    gray = cv2.equalizeHist(gray)
                    
                    # Detect faces
                    faces = face_detector.face_cascade.detectMultiScale(
                        gray,
                        scaleFactor=face_detector.scale_factor,
                        minNeighbors=face_detector.min_neighbors,
                        minSize=face_detector.min_size
                    )
                    
                    # Draw faces on frame
                    processed_frame = frame.copy()
                    for (x, y, w, h) in faces:
                        # Draw rectangle around face
                        cv2.rectangle(processed_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        
                        # Add face number
                        face_number = len([f for f in faces if f[1] < y]) + 1
                        cv2.putText(processed_frame, f'Face #{face_number}', 
                                   (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    
                    # Add face count display
                    cv2.putText(processed_frame, f'Faces Detected: {len(faces)}', 
                               (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                    
                    # Add FPS counter
                    cv2.putText(processed_frame, 'Live Webcam - Face Detection', 
                               (10, processed_frame.shape[0] - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    
                    # Update current frame
                    with frame_lock:
                        current_frame = processed_frame
                
                else:
                    print("⚠️ Failed to capture frame")
                    time.sleep(0.1)
            else:
                time.sleep(0.1)
                
        except Exception as e:
            print(f"❌ Error in camera worker: {e}")
            time.sleep(0.1)

def generate_frames():
    """Generate frames for MJPEG streaming"""
    while is_camera_active:
        with frame_lock:
            if current_frame is not None:
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', current_frame)
                frame = buffer.tobytes()
                
                # Yield frame in MJPEG format
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                # Send a placeholder frame if no camera feed
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(placeholder, 'Camera not active', (50, 240), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                ret, buffer = cv2.imencode('.jpg', placeholder)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                time.sleep(0.1)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/detection')
def detection():
    return render_template('detection.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_camera', methods=['POST'])
def start_camera():
    """Start the camera"""
    global is_camera_active, camera_initialized
    
    if is_camera_active:
        return jsonify({'success': True, 'message': 'Camera is already running'})
    
    # Initialize face detector if not already done
    if face_detector is None:
        if not initialize_face_detector():
            return jsonify({'success': False, 'message': 'Failed to initialize face detector'})
    
    success = initialize_camera()
    if success:
        # Start camera worker thread
        camera_thread = threading.Thread(target=camera_worker, daemon=True)
        camera_thread.start()
        camera_initialized = True
        return jsonify({'success': True, 'message': 'Camera started successfully'})
    else:
        return jsonify({'success': False, 'message': 'Failed to start camera'})

@app.route('/stop_camera', methods=['POST'])
def stop_camera():
    """Stop the camera"""
    global is_camera_active, camera
    
    is_camera_active = False
    time.sleep(0.5)  # Give time for worker thread to exit
    
    if camera:
        camera.release()
        camera = None
    
    # Clear current frame
    with frame_lock:
        current_frame = None
    
    return jsonify({'success': True, 'message': 'Camera stopped successfully'})

@app.route('/get_face_count', methods=['GET'])
def get_face_count():
    """Get current face count from the latest frame"""
    if not is_camera_active or current_frame is None:
        return jsonify({'face_count': 0, 'success': False, 'message': 'Camera not active'})
    
    try:
        with frame_lock:
            if current_frame is not None:
                # Convert to grayscale for face detection
                gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
                faces = face_detector.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=face_detector.scale_factor,
                    minNeighbors=face_detector.min_neighbors,
                    minSize=face_detector.min_size
                )
                return jsonify({
                    'face_count': len(faces), 
                    'success': True,
                    'message': f'Found {len(faces)} faces'
                })
    except Exception as e:
        return jsonify({'face_count': 0, 'success': False, 'message': str(e)})
    
    return jsonify({'face_count': 0, 'success': False, 'message': 'No frame available'})

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    camera_status = 'active' if is_camera_active else 'inactive'
    detector_status = 'ready' if face_detector else 'not ready'
    
    return jsonify({
        'status': 'healthy', 
        'service': 'Face Count Detector',
        'camera': camera_status,
        'detector': detector_status,
        'camera_initialized': camera_initialized
    })

@app.route('/api/camera_status')
def camera_status():
    """Check camera status"""
    return jsonify({
        'camera_active': is_camera_active,
        'face_detector_ready': face_detector is not None,
        'camera_initialized': camera_initialized
    })

# Initialize face detector when app starts
@app.before_request
def before_first_request():
    """Initialize face detector before first request"""
    global face_detector
    if face_detector is None:
        initialize_face_detector()

if __name__ == '__main__':
    # Ensure necessary directories exist
    if not os.path.exists('models'):
        os.makedirs('models', exist_ok=True)
    
    print("🚀 Starting Face Count Detector Website...")
    print("📍 Access the website at: http://localhost:5000")
    print("📷 Navigate to /detection for webcam face detection")
    print("🔧 Initializing face detector...")
    
    # Initialize face detector at startup
    if initialize_face_detector():
        print("✅ Face detector ready!")
    else:
        print("❌ Face detector failed to initialize!")
    
    app.run(debug=True, port=5000)