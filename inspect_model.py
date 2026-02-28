import pickle
from ultralytics import YOLO
import sys

try:
    with open('yolov8n/data.pkl', 'rb') as f:
        data = pickle.load(f)
        print("Pickle loaded.")
        if hasattr(data, 'names'):
            print(f"Class names: {data.names}")
        else:
            print("No names attribute found.")
            print(f"Data type: {type(data)}")
            # If it's a dict
            if isinstance(data, dict):
                print(f"Keys: {data.keys()}")

except Exception as e:
    print(f"Error: {e}")
