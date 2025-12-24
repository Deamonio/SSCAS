"""
AI Server for SSCAS - Handles person detection and density analysis
Improved version with better structure, error handling, and modularity
"""
import socket
from threading import Thread
from roboflow import Roboflow
import cv2
import numpy as np
import json
import seaborn as sns
from datetime import datetime
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import logging
import sys
import os

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(__file__))
from config import *

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state
client_sockets = []

class DensityAnalyzer:
    """Handles density calculation and heatmap generation"""
    
    @staticmethod
    def calculate_density_levels(predictions, image_width, image_height):
        """
        Calculate density levels for a 5x5 grid
        Returns: 2D array of density levels (0-9)
        """
        # Initialize full area matrix
        full_area = np.zeros((image_height, image_width), dtype=int)
        
        # Mark person areas
        for pred in predictions:
            x, y = pred['x'], pred['y']
            width, height = pred['width'], pred['height']
            x1 = max(0, int(x - width / 2))
            y1 = max(0, int(y - height / 2))
            x2 = min(image_width, int(x + width / 2))
            y2 = min(image_height, int(y + height / 2))
            
            full_area[y1:y2, x1:x2] = 1
        
        # Calculate small area density (5x5 grid)
        grid_size = 5
        cell_width = image_width / grid_size
        cell_height = image_height / grid_size
        small_area = cell_width * cell_height
        
        density_grid = []
        for row in range(grid_size):
            row_densities = []
            for col in range(grid_size):
                x_start = int(col * cell_width)
                x_end = int((col + 1) * cell_width)
                y_start = int(row * cell_height)
                y_end = int((row + 1) * cell_height)
                
                cell_area = full_area[y_start:y_end, x_start:x_end]
                occupied = np.sum(cell_area)
                density_percent = (occupied / small_area) * 100
                
                # Convert to level (0-9)
                level = min(9, int(density_percent / 10))
                row_densities.append(level)
            
            density_grid.append(row_densities)
        
        return density_grid
    
    @staticmethod
    def generate_heatmap(density_levels, output_path):
        """Generate and save heatmap visualization"""
        try:
            plt.figure(figsize=(10, 8))
            sns.heatmap(
                density_levels,
                vmin=0,
                vmax=9,
                annot=True,
                fmt='d',
                cmap='RdPu',
                cbar_kws={'label': 'Density Level'}
            )
            plt.title('Crowd Density Heatmap')
            plt.savefig(output_path, format='jpg', dpi=150, bbox_inches='tight')
            plt.close()
            logger.info(f'Heatmap saved to {output_path}')
        except Exception as e:
            logger.error(f'Failed to generate heatmap: {e}')
            plt.close()

class PersonDetector:
    """Handles person detection using Roboflow API"""
    
    def __init__(self):
        self.model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize Roboflow model"""
        try:
            rf = Roboflow(api_key=ROBOFLOW_API_KEY)
            project = rf.workspace().project(ROBOFLOW_PROJECT)
            self.model = project.version(ROBOFLOW_VERSION).model
            logger.info('Roboflow model initialized successfully')
        except Exception as e:
            logger.error(f'Failed to initialize Roboflow model: {e}')
            raise
    
    def detect_persons(self, image_path):
        """
        Detect persons in image
        Returns: prediction JSON
        """
        try:
            prediction = self.model.predict(
                image_path,
                confidence=PREDICTION_CONFIDENCE,
                overlap=PREDICTION_OVERLAP
            ).json()
            logger.info(f'Detected {len(prediction.get("predictions", []))} persons')
            return prediction
        except Exception as e:
            logger.error(f'Failed to detect persons: {e}')
            return None
    
    @staticmethod
    def draw_bounding_boxes(image, predictions):
        """Draw bounding boxes on image"""
        for pred in predictions:
            x, y = pred['x'], pred['y']
            width, height = pred['width'], pred['height']
            
            x1 = int(x - width / 2)
            y1 = int(y - height / 2)
            x2 = int(x + width / 2)
            y2 = int(y + height / 2)
            
            # Draw rectangle
            cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Add label
            cv2.putText(
                image,
                "person",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )
        
        return image

def process_recognition_request(detector, analyzer):
    """Process a recognition request"""
    try:
        current_time = datetime.now()
        
        # Run detection
        pre_picture_path = os.path.join('..', 'frontend', 'static', 'assets', 'img', 'pre_picture.jpg')
        prediction = detector.detect_persons(pre_picture_path)
        if not prediction:
            logger.error('Failed to get prediction')
            return None
        
        # Save prediction to file
        with open("prediction.json", "w") as json_file:
            json.dump(prediction, json_file)
        logger.info('Prediction saved to prediction.json')
        
        # Extract image dimensions and predictions
        image_data = prediction.get('image', {})
        image_width = int(image_data.get('width', 640))
        image_height = int(image_data.get('height', 480))
        predictions = prediction.get('predictions', [])
        person_count = len(predictions)
        
        # Load and resize image
        pre_picture_path = os.path.join('..', 'frontend', 'static', 'assets', 'img', 'pre_picture.jpg')
        image = cv2.imread(pre_picture_path)
        if image is None:
            logger.error(f'Failed to load image: {pre_picture_path}')
            return None
        
        resized_image = cv2.resize(image, (image_width, image_height))
        
        # Draw bounding boxes
        annotated_image = detector.draw_bounding_boxes(resized_image, predictions)
        saved_picture_path = os.path.join('..', 'frontend', 'static', 'assets', 'img', 'saved_picture.jpg')
        cv2.imwrite(saved_picture_path, annotated_image)
        logger.info(f'Annotated image saved to {saved_picture_path}'))
        
        # Calculate overall density
        full_area = image_width * image_height
        people_area = sum(int(p['width']) * int(p['height']) for p in predictions)
        full_density = (people_area / full_area) * 100
        logger.info(f'Overall density: {full_density:.2f}%')
        
        # Calculate density grid and generate heatmap
        density_levels = analyzer.calculate_density_levels(
            predictions,
            image_width,
            image_height
        )
        heatmap_path = os.path.join('..', 'frontend', 'static', 'assets', 'img', 'heatmap.jpg')
        analyzer.generate_heatmap(density_levels, heatmap_path)
        
        # Format time string
        time_str = current_time.strftime("%Y-%m-%d %H'%M'%S")
        place = "지하철역"
        
        return {
            'density': round(full_density, 2),
            'person_count': person_count,
            'time': time_str,
            'place': place
        }
        
    except Exception as e:
        logger.error(f'Error processing recognition request: {e}')
        return None

def threaded(client_socket, addr, detector, analyzer):
    """Handle client connection in separate thread"""
    logger.info(f'Connected by {addr[0]}:{addr[1]}')
    
    try:
        while True:
            data = client_socket.recv(1024)
            
            if not data:
                logger.info(f'Disconnected by {addr[0]}:{addr[1]}')
                break
            
            # Broadcast to other clients
            for client in client_sockets:
                if client != client_socket:
                    try:
                        client.send(data)
                    except Exception as e:
                        logger.error(f'Failed to broadcast: {e}')
            
            # Process recognition request
            if data.decode() == "recog":
                logger.info(f'Received recognition request from {addr[0]}:{addr[1]}')
                
                result = process_recognition_request(detector, analyzer)
                
                if result:
                    # Send results to all clients
                    message = f"analysis:{result['density']}:{result['person_count']}:{result['time']}:{result['place']}"
                    for client in client_sockets:
                        try:
                            client.send(message.encode())
                        except Exception as e:
                            logger.error(f'Failed to send result: {e}')
    
    except ConnectionResetError:
        logger.warning(f'Connection reset by {addr[0]}:{addr[1]}')
    except Exception as e:
        logger.error(f'Error in client thread: {e}')
    finally:
        if client_socket in client_sockets:
            client_sockets.remove(client_socket)
            logger.info(f'Removed client. Active clients: {len(client_sockets)}')
        client_socket.close()

def main():
    """Main server function"""
    # Initialize detector and analyzer
    try:
        detector = PersonDetector()
        analyzer = DensityAnalyzer()
    except Exception as e:
        logger.error(f'Failed to initialize components: {e}')
        return
    
    # Create and bind socket
    host = socket.gethostbyname(socket.gethostname())
    logger.info(f'Starting server on {host}:{SERVER_PORT}')
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((host, SERVER_PORT))
        server_socket.listen()
        logger.info('Server listening for connections...')
        
        while True:
            logger.info('Waiting for client connection...')
            client_socket, addr = server_socket.accept()
            client_sockets.append(client_socket)
            
            # Start new thread for client
            client_thread = Thread(
                target=threaded,
                args=(client_socket, addr, detector, analyzer),
                daemon=True
            )
            client_thread.start()
            logger.info(f'Active clients: {len(client_sockets)}')
            
    except KeyboardInterrupt:
        logger.info('Server shutting down...')
    except Exception as e:
        logger.error(f'Server error: {e}')
    finally:
        server_socket.close()
        logger.info('Server closed')

if __name__ == '__main__':
    main()
