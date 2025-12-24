"""
Configuration settings for the SSCAS application
"""
import os

# Server Configuration
SERVER_HOST = '192.168.144.247'
SERVER_PORT = 9999

# Flask Configuration
FLASK_HOST = '127.0.0.1'
FLASK_PORT = 5000
DEBUG_MODE = True

# Camera Configuration
CAMERA_URL = "http://192.168.144.241:81/stream"
CAMERA_INDEX = 0  # Fallback to default camera

# Image Paths
STATIC_DIR = os.path.join('..', 'frontend', 'static', 'assets', 'img')
PRE_PICTURE_PATH = os.path.join(STATIC_DIR, 'pre_picture.jpg')
SAVED_PICTURE_PATH = os.path.join(STATIC_DIR, 'saved_picture.jpg')
HEATMAP_PATH = os.path.join(STATIC_DIR, 'heatmap.jpg')
WHITE_IMAGE_PATH = os.path.join(STATIC_DIR, 'white.jpg')

# AI Configuration
ROBOFLOW_API_KEY = "TiNMvhxIoHsoajs9cDg4"
ROBOFLOW_WORKSPACE = None
ROBOFLOW_PROJECT = "lg-cns"
ROBOFLOW_VERSION = 2
PREDICTION_CONFIDENCE = 40
PREDICTION_OVERLAP = 30

# Processing Configuration
CAPTURE_INTERVAL = 5  # seconds
POLLING_INTERVAL = 2  # seconds
POLLING_TIMEOUT = 10  # seconds
