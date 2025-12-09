import cv2
import numpy as np
import os
import urllib.request

class FaceCountDetector:
    def __init__(self, scale_factor=1.1, min_neighbors=5, min_size=(30, 30)):
        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors
        self.min_size = min_size
        
        # Load the face cascade classifier
        cascade_path = self.get_cascade_path()
        self.ensure_cascade_exists(cascade_path)
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if self.face_cascade.empty():
            raise Exception("Could not load haarcascade classifier!")
        else:
            print("✅ Face cascade classifier loaded successfully!")
    
    def get_cascade_path(self):
        """Get the correct path for cascade file"""
        # Try different possible locations
        possible_paths = [
            'models/haarcascade_frontalface_default.xml',
            '../models/haarcascade_frontalface_default.xml',
            './models/haarcascade_frontalface_default.xml'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                print(f"📁 Found cascade at: {path}")
                return path
        
        # If not found, return the default path
        return 'models/haarcascade_frontalface_default.xml'
    
    def ensure_cascade_exists(self, cascade_path):
        """Ensure the haarcascade file exists, download if not"""
        # Create models directory if it doesn't exist
        models_dir = os.path.dirname(cascade_path)
        if models_dir and not os.path.exists(models_dir):
            os.makedirs(models_dir, exist_ok=True)
            print(f"📁 Created directory: {models_dir}")
        
        if not os.path.exists(cascade_path):
            print(f"📥 Downloading haarcascade classifier to: {cascade_path}")
            url = 'https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml'
            try:
                urllib.request.urlretrieve(url, cascade_path)
                print("✅ Haarcascade classifier downloaded successfully!")
            except Exception as e:
                print(f"❌ Error downloading cascade: {e}")
                # Try to use OpenCV's built-in cascade
                try:
                    # Try to load from OpenCV data
                    self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                    if not self.face_cascade.empty():
                        print("✅ Loaded cascade from OpenCV data directory")
                        return
                except:
                    pass
                raise Exception(f"Failed to download or load cascade classifier: {e}")
        else:
            print(f"✅ Haarcascade classifier found at: {cascade_path}")

# Test the detector
if __name__ == '__main__':
    try:
        detector = FaceCountDetector()
        print("✅ FaceCountDetector test: SUCCESS")
    except Exception as e:
        print(f"❌ FaceCountDetector test: FAILED - {e}")