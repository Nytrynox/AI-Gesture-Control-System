# AI Gesture Control System

## Overview
A sophisticated computer vision system that enables touch-free laptop control using hand gestures. This application utilizes advanced machine learning models to track hand movements in real-time and map them to system commands, offering a futuristic way to interact with your device.

## Features
-   **Cursor Control**: Precision mouse movement using index finger tracking.
-   **Click Operations**: Intuitive gestures for left-click (Fist) and right-click (Victory Sign).
-   **Scroll Navigation**: Smooth scrolling capabilities using Open Palm gestures.
-   **Media Control**: Volume adjustment and media playback control.
-   **Browser Navigation**: Swipe gestures for forward and backward navigation.

## Technology Stack
-   **Python 3.7+**: Core programming language.
-   **OpenCV**: Real-time computer vision and image processing.
-   **MediaPipe**: Efficient on-device hand tracking.
-   **PyAutoGUI**: Cross-platform GUI automation.

## Usage Flow
1.  **Initialize**: Launch the application to start the webcam feed.
2.  **Detect**: The system identifies your hand landmarks.
3.  **Recognize**: Gestures are classified in real-time.
4.  **Execute**: Corresponding system actions are performed.

## Quick Start
```bash
# Clone the repository
git clone https://github.com/Nytrynox/Gesture-Control-System.git

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## License
MIT License

## Author
**Karthik Idikuda**
