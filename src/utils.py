import cv2
import numpy as np
import os

def download_haarcascade():
    """Download haarcascade classifier if not present"""
    cascade_path = 'models/haarcascade_frontalface_default.xml'
    
    if not os.path.exists(cascade_path):
        # Create models directory
        os.makedirs('models', exist_ok=True)
        
        # Download the classifier
        url = 'https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml'
        import urllib.request
        urllib.request.urlretrieve(url, cascade_path)
        print("Haarcascade classifier downloaded successfully!")
    else:
        print("Haarcascade classifier already exists!")
    
    return cascade_path

def preprocess_image(image):
    """Preprocess image for better face detection"""
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply histogram equalization for better contrast
    gray = cv2.equalizeHist(gray)
    
    return gray

def create_output_directory():
    """Create output directory if it doesn't exist"""
    os.makedirs('output', exist_ok=True)