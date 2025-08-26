# NAO Robot AI System

This project combines NAO robot control with AI-powered vision models for object detection, face recognition, and behavior prediction. The system enables autonomous robot behaviors including head tracking, peekaboo gameplay, and real-time visual analysis.

<small>To see how I used RL to make them walk, check out (here)[http://danielobolensky.com/posts/making_robots_walk.html]</small>

## Prerequisites
Python2.7 is required to run the NAO bot, Python3 is required to run the server.

Once both python versions are downloaded, create respective virtual environments for them and download their requirements

```
# If Python2.7 use requirements_py27.txt
# If Python3 use requirements_py3.txt
```
### Terminal 1: NAO Robot Control
```bash
source .venv_27/bin/activate
python2.7 src/main.py
```

### Terminal 2: Server
```bash
source .venv_3/bin/activate
python3 src/tflite_server.py
```

## AI Models Supported
The server can run multiple models for different tasks:

### 1. **TensorFlow Lite Model** (`/predict/tflite`)
- **File**: `models/peekaboo_model.tflite`
- **Purpose**: Custom peekaboo behavior prediction
- **Input**: 224x224 images
- **Output**: Behavior classification predictions

### 2. **YOLO Object Detection** (`/predict/yolo`)
- **File**: `models/yolov8n.pt` or `models/yolov7.pt`
- **Purpose**: Real-time object detection
- **Output**: Bounding boxes, confidence scores, class IDs
- **Classes**: 80 COCO dataset classes (person, car, etc.)

### 3. **Face Detection** (`/predict/face`)
- **Library**: face_recognition (HOG-based)
- **Purpose**: Detect human faces in images
- **Output**: Face bounding box coordinates
- **Features**: Optimized for speed with image downscaling

### 4. **Combined Inference** (`/predict/both`)
- Runs all available models on the same image
- Returns combined results from TFLite, YOLO, and face detection

## API Endpoints

- `POST /predict/tflite` - TensorFlow Lite model only
- `POST /predict/yolo` - YOLO object detection only  
- `POST /predict/face` - Face detection only
- `POST /predict/both` - All models
- `GET /status` - Check server and model status

## Models Directory

Ensure the `models/` directory contains:
- `peekaboo_model.tflite` - Custom TFLite model
- `yolov8n.pt` or `yolov7.pt` - YOLO weights
- `coco.names` - COCO class names

## Robot Capabilities

### Movement Control
- **Head Tracking**: Autonomous head movement following detected faces or objects
- **Posture Management**: Sitting, standing, and gesture control
- **Motor Control**: Joint-level movement with position feedback
- **Behavioral Responses**: Programmed reactions to visual stimuli

### Vision System
- **Real-time Video Capture**: 320x240 RGB at 30fps from NAO's camera
- **Multi-model Processing**: Simultaneous face detection, object recognition, and behavior prediction
- **Image Classification**: Custom TensorFlow Lite models for specialized tasks
- **Object Detection**: YOLO-based detection of 80 COCO dataset classes
- **Face Recognition**: HOG-based face detection optimized for robot interaction

### Interactive Features
- **Peekaboo Game**: AI-driven gameplay with behavioral prediction
- **Training Mode**: Capture and classify interaction data
- **GUI Control**: Real-time video monitoring and manual robot control
- **Data Collection**: Automatic image saving for model training (`covered/` and `uncovered/` directories)
