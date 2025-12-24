"""
Flask server for SSCAS (Smart Surveillance and Crowd Analysis System)
Handles video streaming, image processing, and communication with AI server
"""
from flask import Flask, render_template, Response, send_file, jsonify, abort
import cv2
import time
import numpy as np
import socket
import os
from threading import Thread, Lock
import shutil
import logging
from config import *

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')

# Global state management
class ApplicationState:
    def __init__(self):
        self.analysis_data = []
        self.ok = False
        self.lock = Lock()
        self.client_socket = None
        self.camera = None
        
    def update_analysis_data(self, data):
        with self.lock:
            self.analysis_data = data
            self.ok = True
    
    def get_analysis_data(self):
        with self.lock:
            return self.analysis_data.copy()
    
    def reset_ok_flag(self):
        with self.lock:
            self.ok = False
    
    def get_ok_flag(self):
        with self.lock:
            return self.ok

state = ApplicationState()


def initialize_connection():
    """Initialize socket connection to AI server"""
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_HOST, SERVER_PORT))
        state.client_socket = client_socket
        logger.info(f'Connected to server at {SERVER_HOST}:{SERVER_PORT}')
        return client_socket
    except Exception as e:
        logger.error(f'Failed to connect to server: {e}')
        return None

def initialize_camera():
    """Initialize camera connection"""
    try:
        camera = cv2.VideoCapture(CAMERA_URL)
        if not camera.isOpened():
            logger.warning(f'Failed to open camera at {CAMERA_URL}, trying default camera')
            camera = cv2.VideoCapture(CAMERA_INDEX)
        state.camera = camera
        logger.info('Camera initialized successfully')
        return camera
    except Exception as e:
        logger.error(f'Failed to initialize camera: {e}')
        return None

def recv_data(client_socket):
    """Receive analysis data from AI server in background thread"""
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                logger.warning('Connection lost to AI server')
                break
            
            decoded_data = data.decode().split(":")
            if decoded_data[0] == "analysis":
                logger.info(f'Received analysis data: {decoded_data}')
                state.update_analysis_data(decoded_data)
        except Exception as e:
            logger.error(f'Error receiving data: {e}')
            break

# Initialize connections
client_socket = initialize_connection()
camera = initialize_camera()

if client_socket:
    # Start background thread for receiving data
    recv_thread = Thread(target=recv_data, args=(client_socket,), daemon=True)
    recv_thread.start()


def generate_frames():
    """Generate video frames for streaming"""
    if not state.camera:
        logger.error('Camera not initialized')
        return
    
    cnt = 0
    last_save_time = 0
    
    while True:
        success, frame = state.camera.read()
        if not success:
            logger.error('Failed to read frame from camera')
            break
        
        try:
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                logger.error('Failed to encode frame')
                continue
                
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Save frame every CAPTURE_INTERVAL seconds
            current_time = time.time()
            if current_time - last_save_time >= CAPTURE_INTERVAL:
                frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
                img = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                
                if img is not None:
                    cv2.imwrite(PRE_PICTURE_PATH, img)
                    logger.debug(f'Saved frame to {PRE_PICTURE_PATH}')
                    
                    # Send recognition request to AI server
                    if state.client_socket and ((cnt != 0 and state.get_ok_flag()) or cnt == 0):
                        try:
                            state.client_socket.send(b"recog")
                            logger.info('Sent recognition request to AI server')
                            cnt += 1
                            state.reset_ok_flag()
                        except Exception as e:
                            logger.error(f'Failed to send recognition request: {e}')
                    
                    last_save_time = current_time
        except Exception as e:
            logger.error(f'Error processing frame: {e}')
            continue

@app.route('/')
def index():
    """Render main dashboard page"""
    try:
        # Initialize placeholder images
        if os.path.exists(WHITE_IMAGE_PATH):
            shutil.copy(WHITE_IMAGE_PATH, SAVED_PICTURE_PATH)
            shutil.copy(WHITE_IMAGE_PATH, HEATMAP_PATH)
            logger.info('Initialized placeholder images')
    except Exception as e:
        logger.error(f'Failed to initialize placeholder images: {e}')
    
    return render_template('index.html')


@app.route('/concert')
def concert():
    """Render concert hall page"""
    return render_template('concert.html')

@app.route('/path')
def path():
    """Render alley path page"""
    return render_template('path.html')

@app.route('/get_image/<string:no>')
def get_image(no):
    """Serve processed images"""
    image_paths = {
        '1': SAVED_PICTURE_PATH,
        '2': HEATMAP_PATH
    }
    
    image_path = image_paths.get(no)
    if not image_path or not os.path.exists(image_path):
        logger.warning(f'Image not found: {no}')
        abort(404)
    
    try:
        return send_file(image_path, mimetype='image/jpeg')
    except Exception as e:
        logger.error(f'Failed to send image {no}: {e}')
        abort(500)

@app.route('/video_feed')
def video_feed():
    """Stream video frames"""
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/get_character', methods=['GET'])
def get_character():
    """Get current analysis data"""
    analysis_data = state.get_analysis_data()
    
    if len(analysis_data) == 5:
        time_str = analysis_data[3].replace("'", ":")
        return jsonify({
            'place': analysis_data[4],
            'time': time_str,
            'person': analysis_data[2],
            'density': analysis_data[1]
        })
    
    return jsonify({
        'place': '',
        'time': '',
        'person': '',
        'density': ''
    })

@app.route('/poll_characters', methods=['GET'])
def poll_characters():
    """Long polling endpoint for analysis data updates"""
    start_time = time.time()
    
    while time.time() - start_time < POLLING_TIMEOUT:
        analysis_data = state.get_analysis_data()
        
        if len(analysis_data) == 5:
            return jsonify({
                'place': analysis_data[4],
                'time': analysis_data[3],
                'person': analysis_data[2],
                'density': analysis_data[1]
            })
        
        time.sleep(1)
    
    # Return empty data if timeout
    return jsonify({
        'place': '',
        'time': '',
        'person': '',
        'density': ''
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f'Internal server error: {error}')
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    try:
        logger.info(f'Starting Flask server on {FLASK_HOST}:{FLASK_PORT}')
        app.run(debug=DEBUG_MODE, host=FLASK_HOST, port=FLASK_PORT, threaded=True)
    except KeyboardInterrupt:
        logger.info('Server shutting down...')
    finally:
        if state.client_socket:
            state.client_socket.close()
        if state.camera:
            state.camera.release()
        logger.info('Cleanup complete')