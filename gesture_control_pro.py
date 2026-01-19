#!/usr/bin/env python3
"""
Professional AI-Based Hand Gesture Control System
==================================================
A comprehensive gesture control application with real-time detection,
professional GUI, advanced analytics, and complete laptop control.

Features:
- Real-time hand gesture detection using MediaPipe
- Professional GUI with live video feed
- Advanced gesture analytics and confidence metrics
- Customizable gesture mappings and sensitivity
- System control (volume, brightness, mouse, keyboard)
- Performance monitoring and statistics
- Recording and playback capabilities
- Multiple gesture profiles
"""

import cv2
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import mediapipe as mp
import numpy as np
import pyautogui
import threading
import time
import json
import os
import subprocess
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pickle
from collections import deque, defaultdict
import logging
from datetime import datetime
import queue

# Disable PyAutoGUI failsafe for smooth operation
pyautogui.FAILSAFE = False

class GestureControlPro:
    def __init__(self):
        """Initialize the Professional Gesture Control System"""
        self.setup_logging()
        self.setup_mediapipe()
        self.setup_variables()
        self.setup_gui()
        self.load_settings()
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('gesture_control.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_mediapipe(self):
        """Initialize MediaPipe components"""
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils
        
    def setup_variables(self):
        """Initialize application variables"""
        # Camera and detection variables
        self.cap = None
        self.is_running = False
        self.fps = 0
        self.frame_count = 0
        self.start_time = time.time()
        
        # Thread safety queue
        self.gui_queue = queue.Queue()
        
        # Gesture detection variables
        self.current_gesture = "None"
        self.gesture_confidence = 0.0
        self.gesture_history = deque(maxlen=30)  # Last 30 detections
        self.gesture_stats = defaultdict(int)
        
        # Drag state
        self.is_dragging = False
        self.last_gesture = None
        self.gesture_debounce_time = 0.3  # seconds between same gesture
        self.last_gesture_time = 0
        
        # Performance metrics
        self.fps_history = deque(maxlen=100)
        self.detection_times = deque(maxlen=100)
        
        # Control variables
        self.sensitivity = 0.5  # Lowered default sensitivity
        self.smoothing = 0.3
        self.mouse_control_enabled = True
        self.system_control_enabled = True
        
        # Comprehensive gesture mappings (A-Z features)
        self.gesture_mappings = {
            # Mouse control gestures
            'point': 'mouse_move',
            'fist': 'left_click',
            'pinch': 'drag',
            'victory': 'right_click',
            'double_tap': 'double_click',
            
            # Scrolling gestures
            'open_palm': 'scroll_up',
            'open_palm_down': 'scroll_down',
            'swipe_left': 'scroll_left',
            'swipe_right': 'scroll_right',
            
            # Volume control
            'thumbs_up': 'volume_up',
            'thumbs_down': 'volume_down',
            
            # Brightness control
            'ok_sign': 'brightness_up',
            'peace_inverted': 'brightness_down',
            
            # Window management
            'four_fingers': 'minimize_all',
            'three_fingers': 'mission_control',
            'spread_fingers': 'show_desktop',
            
            # Browser/Tab navigation
            'swipe_left_fast': 'prev_tab',
            'swipe_right_fast': 'next_tab',
            
            # Zoom control
            'zoom_in': 'zoom_in',
            'zoom_out': 'zoom_out',
            
            # Media controls
            'palm_stop': 'media_pause',
            'finger_gun': 'media_play',
            
            # Additional gestures
            'l_shape': 'screenshot',
            'call_me': 'open_terminal',
            'finger_crossed': 'undo',
            'rock_on': 'lock_screen'
        }
        
        # Screen dimensions
        self.screen_width, self.screen_height = pyautogui.size()
        
    def setup_gui(self):
        """Create the professional GUI interface"""
        self.root = tk.Tk()
        self.root.title("Professional AI Gesture Control System")
        self.root.geometry("1400x900")
        self.root.configure(bg='#121212')  # Darker background for modern look
        
        # Configure style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        
        # Create main layout
        self.create_header()
        self.create_main_content()
        self.create_control_panel()
        self.create_status_bar()
        
        # Start GUI update loop
        self.root.after(10, self.process_gui_queue)
        
    def configure_styles(self):
        """Configure custom styles for the GUI"""
        # Modern color palette
        self.colors = {
            'bg_dark': '#121212',
            'bg_panel': '#1E1E1E',
            'bg_card': '#252525',
            'accent': '#BB86FC',  # Purple accent
            'accent_secondary': '#03DAC6',  # Teal accent
            'text_primary': '#FFFFFF',
            'text_secondary': '#B0B0B0',
            'success': '#00E676',
            'error': '#CF6679',
            'warning': '#FFB74D'
        }
        
        self.style.configure('Header.TLabel', 
                           font=('Segoe UI', 18, 'bold'),
                           foreground=self.colors['text_primary'],
                           background=self.colors['bg_panel'])
        
        self.style.configure('Status.TLabel',
                           font=('Segoe UI', 10),
                           foreground=self.colors['success'],
                           background=self.colors['bg_dark'])
        
        self.style.configure('Card.TFrame', background=self.colors['bg_card'])
        
        # Button styles
        self.style.configure('Action.TButton',
                           font=('Segoe UI', 10, 'bold'),
                           background=self.colors['accent'],
                           foreground='black',
                           borderwidth=0,
                           focusthickness=0,
                           padding=10)
        self.style.map('Action.TButton',
                     background=[('active', '#9965f4')]) # Darker purple on hover
                     
        self.style.configure('Stop.TButton',
                           font=('Segoe UI', 10, 'bold'),
                           background=self.colors['error'],
                           foreground='black',
                           borderwidth=0,
                           padding=10)
        
    def create_header(self):
        """Create the application header"""
        header_frame = tk.Frame(self.root, bg=self.colors['bg_panel'], height=70)
        header_frame.pack(fill='x', padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Logo/Title area
        title_container = tk.Frame(header_frame, bg=self.colors['bg_panel'])
        title_container.pack(side='left', padx=20, pady=15)
        
        icon_label = tk.Label(title_container, text="🖐️", 
                            font=('Segoe UI', 24), bg=self.colors['bg_panel'])
        icon_label.pack(side='left', padx=(0, 10))
        
        title_label = tk.Label(title_container, 
                              text="AI Gesture Control Pro",
                              font=('Segoe UI', 20, 'bold'),
                              fg=self.colors['text_primary'], bg=self.colors['bg_panel'])
        title_label.pack(side='left')
        
        # Status indicators
        self.status_frame = tk.Frame(header_frame, bg=self.colors['bg_panel'])
        self.status_frame.pack(side='right', padx=20, pady=15)
        
        self.create_status_indicator("Camera", "OFF", self.colors['error'])
        self.create_status_indicator("AI Engine", "OFF", self.colors['error'])
        
    def create_status_indicator(self, label, status, color):
        frame = tk.Frame(self.status_frame, bg=self.colors['bg_panel'])
        frame.pack(side='right', padx=15)
        
        lbl = tk.Label(frame, text=label, 
                      fg=self.colors['text_secondary'], bg=self.colors['bg_panel'],
                      font=('Segoe UI', 9))
        lbl.pack(anchor='e')
        
        status_lbl = tk.Label(frame, text=status,
                            fg=color, bg=self.colors['bg_panel'],
                            font=('Segoe UI', 10, 'bold'))
        status_lbl.pack(anchor='e')
        
        # Store reference to update later
        setattr(self, f"{label.lower().replace(' ', '_')}_status_lbl", status_lbl)

    def create_main_content(self):
        """Create the main content area with video feed and controls"""
        main_frame = tk.Frame(self.root, bg=self.colors['bg_dark'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Left panel - Video feed
        video_container = tk.Frame(main_frame, bg=self.colors['bg_card'], bd=0)
        video_container.pack(side='left', fill='both', expand=True, padx=(0, 20))
        
        # Video Header
        tk.Label(video_container, text="Live Feed", 
                font=('Segoe UI', 12, 'bold'),
                bg=self.colors['bg_card'], fg=self.colors['text_primary']).pack(anchor='w', padx=15, pady=10)
        
        # Video display
        self.video_label = tk.Label(video_container, bg='black', text="Camera Feed Inactive",
                                   fg=self.colors['text_secondary'], font=('Segoe UI', 14))
        self.video_label.pack(padx=15, pady=(0, 15), fill='both', expand=True)
        
        # Video controls
        video_controls = tk.Frame(video_container, bg=self.colors['bg_card'])
        video_controls.pack(fill='x', padx=15, pady=15)
        
        self.start_button = ttk.Button(video_controls, text="▶ Start Camera",
                                     style='Action.TButton',
                                     command=self.start_detection)
        self.start_button.pack(side='left', padx=(0, 10))
        
        self.stop_button = ttk.Button(video_controls, text="⏹ Stop Camera",
                                    style='Stop.TButton',
                                    command=self.stop_detection)
        self.stop_button.pack(side='left', padx=(0, 10))
        
        # Right panel - Information and controls
        self.info_frame = tk.Frame(main_frame, bg=self.colors['bg_dark'], width=400)
        self.info_frame.pack(side='right', fill='y')
        self.info_frame.pack_propagate(False)
        
        self.create_info_displays()
        
    def create_info_displays(self):
        """Create information display panels"""
        # Current gesture card
        gesture_card = tk.Frame(self.info_frame, bg=self.colors['bg_card'], padx=20, pady=20)
        gesture_card.pack(fill='x', pady=(0, 20))
        
        tk.Label(gesture_card, text="Detected Gesture",
                font=('Segoe UI', 11), fg=self.colors['text_secondary'],
                bg=self.colors['bg_card']).pack(anchor='w')
                
        self.gesture_label = tk.Label(gesture_card, text="None",
                                     bg=self.colors['bg_card'], fg=self.colors['accent'],
                                     font=('Segoe UI', 32, 'bold'))
        self.gesture_label.pack(pady=10)
        
        self.confidence_bar = ttk.Progressbar(gesture_card, orient='horizontal', mode='determinate', length=200)
        self.confidence_bar.pack(fill='x', pady=5)
        
        self.confidence_label = tk.Label(gesture_card, text="Confidence: 0%",
                                        bg=self.colors['bg_card'], fg=self.colors['text_secondary'],
                                        font=('Segoe UI', 10))
        self.confidence_label.pack()
        
        # Performance metrics card
        perf_card = tk.Frame(self.info_frame, bg=self.colors['bg_card'], padx=20, pady=20)
        perf_card.pack(fill='x', pady=(0, 20))
        
        tk.Label(perf_card, text="System Performance",
                font=('Segoe UI', 11, 'bold'), fg=self.colors['text_primary'],
                bg=self.colors['bg_card']).pack(anchor='w', pady=(0, 10))
        
        self.fps_label = self.create_metric_row(perf_card, "FPS", "0")
        self.hands_detected_label = self.create_metric_row(perf_card, "Hands Detected", "0")
        self.processing_time_label = self.create_metric_row(perf_card, "Latency", "0ms")
        
        # Recent History
        history_card = tk.Frame(self.info_frame, bg=self.colors['bg_card'], padx=20, pady=20)
        history_card.pack(fill='both', expand=True)
        
        tk.Label(history_card, text="Recent Activity",
                font=('Segoe UI', 11, 'bold'), fg=self.colors['text_primary'],
                bg=self.colors['bg_card']).pack(anchor='w', pady=(0, 10))
                
        self.history_listbox = tk.Listbox(history_card, bg=self.colors['bg_panel'], 
                                        fg=self.colors['text_secondary'],
                                        selectbackground=self.colors['accent'],
                                        borderwidth=0, highlightthickness=0,
                                        font=('Segoe UI', 10))
        self.history_listbox.pack(fill='both', expand=True)
        
    def create_metric_row(self, parent, label, value):
        row = tk.Frame(parent, bg=self.colors['bg_card'])
        row.pack(fill='x', pady=2)
        
        tk.Label(row, text=label, fg=self.colors['text_secondary'],
                bg=self.colors['bg_card'], font=('Segoe UI', 10)).pack(side='left')
                
        val_label = tk.Label(row, text=value, fg=self.colors['text_primary'],
                           bg=self.colors['bg_card'], font=('Segoe UI', 10, 'bold'))
        val_label.pack(side='right')
        return val_label
            
    def create_control_panel(self):
        """Create the control panel with settings and options"""
        control_frame = tk.Frame(self.root, bg=self.colors['bg_panel'], height=100)
        control_frame.pack(fill='x', side='bottom')
        
        # Settings container
        settings_container = tk.Frame(control_frame, bg=self.colors['bg_panel'])
        settings_container.pack(fill='both', padx=20, pady=15)
        
        # Sensitivity Slider
        sens_frame = tk.Frame(settings_container, bg=self.colors['bg_panel'])
        sens_frame.pack(side='left', padx=20)
        
        tk.Label(sens_frame, text="Sensitivity", fg=self.colors['text_secondary'],
                bg=self.colors['bg_panel']).pack(anchor='w')
        
        self.sensitivity_var = tk.DoubleVar(value=0.7)
        self.sensitivity_scale = ttk.Scale(sens_frame, from_=0.1, to=1.0,
                                         variable=self.sensitivity_var, orient='horizontal', length=150)
        self.sensitivity_scale.pack()
        
        # Smoothing Slider
        smooth_frame = tk.Frame(settings_container, bg=self.colors['bg_panel'])
        smooth_frame.pack(side='left', padx=20)
        
        tk.Label(smooth_frame, text="Smoothing", fg=self.colors['text_secondary'],
                bg=self.colors['bg_panel']).pack(anchor='w')
        
        self.smoothing_var = tk.DoubleVar(value=0.3)
        self.smoothing_scale = ttk.Scale(smooth_frame, from_=0.0, to=1.0,
                                       variable=self.smoothing_var, orient='horizontal', length=150)
        self.smoothing_scale.pack()
        
        # Toggles
        toggle_frame = tk.Frame(settings_container, bg=self.colors['bg_panel'])
        toggle_frame.pack(side='left', padx=40)
        
        self.mouse_control_var = tk.BooleanVar(value=True)
        tk.Checkbutton(toggle_frame, text="Mouse Control", variable=self.mouse_control_var,
                      bg=self.colors['bg_panel'], fg=self.colors['text_primary'],
                      selectcolor=self.colors['bg_panel'], activebackground=self.colors['bg_panel']).pack(anchor='w')
                      
        self.system_control_var = tk.BooleanVar(value=True)
        tk.Checkbutton(toggle_frame, text="System Actions", variable=self.system_control_var,
                      bg=self.colors['bg_panel'], fg=self.colors['text_primary'],
                      selectcolor=self.colors['bg_panel'], activebackground=self.colors['bg_panel']).pack(anchor='w')

        # Action Buttons
        btn_frame = tk.Frame(settings_container, bg=self.colors['bg_panel'])
        btn_frame.pack(side='right')
        
        ttk.Button(btn_frame, text="Save Settings", command=self.save_settings).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Analytics", command=self.show_analytics).pack(side='left', padx=5)

    def create_status_bar(self):
        """Create the status bar at the bottom"""
        status_frame = tk.Frame(self.root, bg=self.colors['bg_dark'], height=25)
        status_frame.pack(fill='x', side='bottom')
        status_frame.pack_propagate(False)
        
        self.status_text = tk.Label(status_frame, text="Ready",
                                   bg=self.colors['bg_dark'], fg=self.colors['text_secondary'],
                                   font=('Segoe UI', 9))
        self.status_text.pack(side='left', padx=10)
        
        self.time_label = tk.Label(status_frame, text="",
                                  bg=self.colors['bg_dark'], fg=self.colors['text_secondary'],
                                  font=('Segoe UI', 9))
        self.time_label.pack(side='right', padx=10)
        
        self.update_time()
        
    def update_time(self):
        """Update the time display"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)
        
    def start_detection(self):
        """Start the gesture detection system"""
        if not self.is_running:
            try:
                self.cap = cv2.VideoCapture(0)
                if not self.cap.isOpened():
                    messagebox.showerror("Error", "Could not access camera")
                    return
                
                self.is_running = True
                self.camera_status_lbl.config(text="ON", fg=self.colors['success'])
                self.ai_engine_status_lbl.config(text="ACTIVE", fg=self.colors['success'])
                self.status_text.config(text="System Active - Detecting Gestures...")
                
                # Start detection thread
                self.detection_thread = threading.Thread(target=self.detection_loop)
                self.detection_thread.daemon = True
                self.detection_thread.start()
                
                self.logger.info("Gesture detection started")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start detection: {str(e)}")
                self.logger.error(f"Error starting detection: {e}")
                
    def stop_detection(self):
        """Stop the gesture detection system"""
        self.is_running = False
        
        # Release drag if active
        if self.is_dragging:
            try:
                pyautogui.mouseUp()
                self.is_dragging = False
            except:
                pass
        
        # Wait for thread to finish
        if hasattr(self, 'detection_thread') and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=2.0)
        
        # Release camera
        if self.cap:
            self.cap.release()
            self.cap = None
        
        self.camera_status_lbl.config(text="OFF", fg=self.colors['error'])
        self.ai_engine_status_lbl.config(text="OFF", fg=self.colors['error'])
        self.status_text.config(text="System Stopped")
        
        # Clear video display
        self.video_label.config(image='', text="Camera Feed Inactive")
        
        self.logger.info("Gesture detection stopped")
        
    def detection_loop(self):
        """Main detection loop running in separate thread"""
        prev_time = time.time()
        frame_delay = 1.0 / 30.0  # Target 30 FPS to reduce CPU load
        
        while self.is_running:
            try:
                loop_start = time.time()
                start_process = time.time()
                
                ret, frame = self.cap.read()
                if not ret:
                    self.logger.warning("Failed to read frame from camera")
                    time.sleep(0.1)
                    continue
                
                # Flip frame horizontally for mirror effect
                frame = cv2.flip(frame, 1)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Process with MediaPipe
                results = self.hands.process(frame_rgb)
                
                # Track number of hands detected
                hands_count = 0
                
                # Draw hand landmarks and detect gestures
                if results.multi_hand_landmarks:
                    hands_count = len(results.multi_hand_landmarks)
                    for hand_landmarks in results.multi_hand_landmarks:
                        self.mp_draw.draw_landmarks(
                            frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                        
                        # Extract landmarks and recognize gesture
                        landmarks = self.extract_landmarks(hand_landmarks, frame.shape)
                        gesture, confidence = self.recognize_gesture(landmarks)
                        
                        if confidence > self.sensitivity_var.get():
                            self.process_gesture(gesture, confidence, landmarks)
                        else:
                            # Update GUI without triggering action
                            if not self.gui_queue.full():
                                self.gui_queue.put({
                                    'type': 'debug',
                                    'gesture': gesture,
                                    'confidence': confidence
                                })
                else:
                    # No hands detected - release drag if active
                    if self.is_dragging:
                        try:
                            pyautogui.mouseUp()
                            self.is_dragging = False
                        except Exception as e:
                            self.logger.error(f"Error releasing drag: {e}")
                
                # Calculate FPS
                current_time = time.time()
                fps = 1 / (current_time - prev_time) if (current_time - prev_time) > 0 else 0
                prev_time = current_time
                self.fps = fps
                self.fps_history.append(fps)
                
                # Record processing time
                process_time = (time.time() - start_process) * 1000
                self.detection_times.append(process_time)
                
                # Queue update for GUI (don't block if queue is full)
                if not self.gui_queue.full():
                    self.gui_queue.put({
                        'type': 'frame',
                        'data': frame.copy(),  # Copy frame to avoid race conditions
                        'fps': fps,
                        'process_time': process_time,
                        'gesture': self.current_gesture,
                        'confidence': self.gesture_confidence,
                        'hands_count': hands_count
                    })
                
                # Frame rate limiting - sleep for remaining time
                elapsed = time.time() - loop_start
                sleep_time = max(0, frame_delay - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                self.logger.error(f"Error in detection loop: {e}", exc_info=True)
                time.sleep(0.1)
                
    def process_gui_queue(self):
        """Process updates from the detection thread safely in the main thread"""
        try:
            processed = 0
            max_process = 5  # Process max 5 items per call to avoid GUI freeze
            
            while processed < max_process:
                update = self.gui_queue.get_nowait()
                
                if update['type'] == 'frame':
                    self.update_video_display(update['data'])
                    self.update_info_displays(update)
                elif update['type'] == 'log':
                    self.history_listbox.insert(0, update['message'])
                    if self.history_listbox.size() > 50:
                        self.history_listbox.delete(50, tk.END)
                elif update['type'] == 'debug':
                    # Update labels even if action not taken
                    try:
                        self.gesture_label.config(text=f"{update['gesture'].replace('_', ' ').title()}")
                        self.confidence_label.config(text=f"Confidence: {update['confidence']:.0%}")
                        self.confidence_bar['value'] = update['confidence'] * 100
                    except Exception as e:
                        self.logger.error(f"Error updating debug info: {e}")
                
                processed += 1
                
        except queue.Empty:
            pass
        except Exception as e:
            self.logger.error(f"Error processing GUI queue: {e}")
        finally:
            # Schedule next check only if still running
            if self.root and self.root.winfo_exists():
                self.root.after(10, self.process_gui_queue)

    def extract_landmarks(self, hand_landmarks, frame_shape):
        """Extract normalized landmark coordinates"""
        landmarks = []
        h, w, _ = frame_shape
        
        for lm in hand_landmarks.landmark:
            landmarks.extend([lm.x, lm.y, lm.z])
            
        return np.array(landmarks)
        
    def recognize_gesture(self, landmarks):
        """Enhanced gesture recognition with more advanced gestures"""
        if len(landmarks) < 63:  # 21 landmarks * 3 coordinates
            return "unknown", 0.0
            
        # Convert to 2D points for easier analysis
        points = landmarks.reshape(-1, 3)[:, :2]
        
        # Get key landmarks (normalized coordinates 0-1)
        wrist = points[0]
        thumb_tip = points[4]
        thumb_ip = points[3]
        index_tip = points[8]
        index_pip = points[6]
        middle_tip = points[12]
        middle_pip = points[10]
        ring_tip = points[16]
        ring_pip = points[14]
        pinky_tip = points[20]
        pinky_pip = points[18]
        
        # Calculate distances for gesture detection
        thumb_index_dist = np.linalg.norm(thumb_tip - index_tip)
        index_middle_dist = np.linalg.norm(index_tip - middle_tip)
        
        # Count extended fingers with improved detection
        extended_fingers = []
        
        # Thumb (different logic due to thumb orientation)
        thumb_extended = False
        if wrist[0] < 0.5:  # Left hand
            thumb_extended = thumb_tip[0] > thumb_ip[0] + 0.03
        else:  # Right hand
            thumb_extended = thumb_tip[0] < thumb_ip[0] - 0.03
        
        if thumb_extended:
            extended_fingers.append('thumb')
            
        # Other fingers (check if tip is above PIP joint)
        if index_tip[1] < index_pip[1] - 0.015:
            extended_fingers.append('index')
        if middle_tip[1] < middle_pip[1] - 0.015:
            extended_fingers.append('middle')
        if ring_tip[1] < ring_pip[1] - 0.015:
            extended_fingers.append('ring')
        if pinky_tip[1] < pinky_pip[1] - 0.015:
            extended_fingers.append('pinky')
        
        extended_count = len(extended_fingers)
        
        # Advanced gesture recognition logic
        
        # Pinch gesture (thumb and index very close)
        if thumb_index_dist < 0.04:
            return "pinch", 0.92
            
        # OK sign (thumb and index in circle, other fingers extended)
        elif (thumb_index_dist < 0.06 and extended_count >= 3 and 
              'middle' in extended_fingers and 'ring' in extended_fingers):
            return "ok_sign", 0.90
            
        # Thumbs up (thumb up, other fingers down)
        elif ('thumb' in extended_fingers and extended_count == 1 and
              thumb_tip[1] < wrist[1] - 0.05):
            return "thumbs_up", 0.88
            
        # Thumbs down (thumb down, other fingers folded)
        elif ('thumb' in extended_fingers and extended_count == 1 and
              thumb_tip[1] > wrist[1] + 0.05):
            return "thumbs_down", 0.88
            
        # Point gesture (only index finger extended)
        elif extended_count == 1 and 'index' in extended_fingers:
            return "point", 0.85
            
        # Victory sign (index and middle extended, others folded)
        elif (extended_count == 2 and 'index' in extended_fingers and 
              'middle' in extended_fingers):
            # Check if fingers are spread apart (victory) vs close together (point variation)
            if index_middle_dist > 0.05:
                return "victory", 0.87
            else:
                return "point", 0.80
                
        # Peace sign inverted (for brightness down)
        elif (extended_count == 2 and 'index' in extended_fingers and 
              'middle' in extended_fingers and middle_tip[1] > index_tip[1]):
            return "peace_inverted", 0.85
            
        # Three fingers (mission control/expose)
        elif extended_count == 3 and all(f in extended_fingers for f in ['index', 'middle', 'ring']):
            return "three_fingers", 0.83
            
        # Four fingers (minimize all)
        elif extended_count == 4 and 'thumb' not in extended_fingers:
            return "four_fingers", 0.82
            
        # Open palm (all fingers extended)
        elif extended_count >= 4:
            # Check hand movement for scroll direction
            hand_center_y = np.mean([tip[1] for tip in [index_tip, middle_tip, ring_tip, pinky_tip]])
            if hand_center_y < wrist[1] - 0.02:
                return "open_palm", 0.85  # Hand up - scroll up
            else:
                return "open_palm_down", 0.85  # Hand down - scroll down
                
        # Fist (no fingers extended or very few)
        elif extended_count <= 1:
            return "fist", 0.80
            
        # Zoom gestures (advanced - requires hand tracking history)
        # For now, use simple approximations
        elif extended_count == 2 and 'thumb' in extended_fingers and 'index' in extended_fingers:
            if thumb_index_dist > 0.08:
                return "zoom_out", 0.75
            else:
                return "zoom_in", 0.75
        
        # L-shape (thumb and index perpendicular - screenshot)
        elif (extended_count == 2 and 'thumb' in extended_fingers and 'index' in extended_fingers and
              thumb_index_dist > 0.1):
            # Check if thumb and index form roughly 90 degree angle
            thumb_vector = thumb_tip - wrist
            index_vector = index_tip - wrist
            angle = np.arccos(np.dot(thumb_vector, index_vector) / 
                            (np.linalg.norm(thumb_vector) * np.linalg.norm(index_vector) + 1e-6))
            if abs(angle - np.pi/2) < 0.5:  # Roughly 90 degrees
                return "l_shape", 0.78
        
        # Call me gesture (thumb and pinky extended)
        elif (extended_count == 2 and 'thumb' in extended_fingers and 'pinky' in extended_fingers):
            return "call_me", 0.76
        
        # Rock on gesture (index and pinky extended, thumb out)
        elif (extended_count >= 2 and 'index' in extended_fingers and 'pinky' in extended_fingers and
              'middle' not in extended_fingers and 'ring' not in extended_fingers):
            return "rock_on", 0.77
        
        # Finger gun (thumb up, index extended forward)
        elif (extended_count == 2 and 'thumb' in extended_fingers and 'index' in extended_fingers and
              thumb_tip[1] < wrist[1]):
            return "finger_gun", 0.74
        
        # Spread fingers (all extended and spread apart)
        elif extended_count == 5:
            # Check if fingers are spread
            avg_spacing = (np.linalg.norm(index_tip - middle_tip) + 
                          np.linalg.norm(middle_tip - ring_tip) + 
                          np.linalg.norm(ring_tip - pinky_tip)) / 3
            if avg_spacing > 0.06:
                return "spread_fingers", 0.82
            else:
                return "open_palm", 0.80
        
        # Palm stop (all fingers together, facing camera)
        elif extended_count == 4 and 'thumb' not in extended_fingers:
            # Check if fingers are close together
            fingers_close = (np.linalg.norm(index_tip - middle_tip) < 0.04 and
                           np.linalg.norm(middle_tip - ring_tip) < 0.04)
            if fingers_close:
                return "palm_stop", 0.79
                
        else:
            return "unknown", 0.3
            
    def process_gesture(self, gesture, confidence, landmarks):
        """Process detected gesture and execute corresponding action"""
        current_time = time.time()
        
        # Handle drag release if we stop pinching
        if self.is_dragging and gesture != 'pinch':
            try:
                pyautogui.mouseUp()
                self.is_dragging = False
            except Exception as e:
                self.logger.error(f"Error releasing drag: {e}")
            
        self.current_gesture = gesture
        self.gesture_confidence = confidence
        
        # Debouncing - avoid repeating same gesture too quickly
        if gesture == self.last_gesture and (current_time - self.last_gesture_time) < self.gesture_debounce_time:
            # For continuous gestures like mouse_move, allow them through
            if gesture not in ['point', 'pinch', 'open_palm', 'open_palm_down']:
                return
        
        # Add to history
        timestamp = datetime.now().strftime("%H:%M:%S")
        # Only log if gesture changed
        if gesture != self.last_gesture:
            log_msg = f"{timestamp} - {gesture.replace('_', ' ').title()} ({confidence:.0%})"
            self.gesture_history.append(log_msg)
            if not self.gui_queue.full():
                self.gui_queue.put({'type': 'log', 'message': log_msg})
            
        self.gesture_stats[gesture] += 1
        self.last_gesture = gesture
        self.last_gesture_time = current_time
        
        # Execute gesture action
        if gesture in self.gesture_mappings:
            action = self.gesture_mappings[gesture]
            try:
                self.execute_action(action, landmarks, confidence)
            except Exception as e:
                self.logger.error(f"Error executing action {action}: {e}")
            
    def execute_action(self, action, landmarks, confidence):
        """Execute the mapped action for a gesture with enhanced controls"""
        try:
            # Volume controls
            if action == 'volume_up' and self.system_control_var.get():
                subprocess.run(['osascript', '-e', 'set volume output volume (output volume of (get volume settings) + 5)'], 
                             check=False, capture_output=True, timeout=1)
                
            elif action == 'volume_down' and self.system_control_var.get():
                subprocess.run(['osascript', '-e', 'set volume output volume (output volume of (get volume settings) - 5)'], 
                             check=False, capture_output=True, timeout=1)
                
            # Mouse controls with enhanced functionality
            elif action == 'mouse_move' and self.mouse_control_var.get():
                # Move mouse based on index finger position
                if len(landmarks) >= 24:  # Ensure we have index finger tip
                    points = landmarks.reshape(-1, 3)
                    index_tip = points[8][:2]  # x, y coordinates
                    
                    # Convert to screen coordinates
                    screen_x = int(index_tip[0] * self.screen_width)
                    screen_y = int(index_tip[1] * self.screen_height)
                    
                    # Apply smoothing
                    current_pos = pyautogui.position()
                    smooth_x = int(current_pos.x * self.smoothing_var.get() + 
                                 screen_x * (1 - self.smoothing_var.get()))
                    smooth_y = int(current_pos.y * self.smoothing_var.get() + 
                                 screen_y * (1 - self.smoothing_var.get()))
                    
                    pyautogui.moveTo(smooth_x, smooth_y)
                    
            elif action == 'left_click' and self.mouse_control_var.get():
                pyautogui.click()
                
            elif action == 'right_click' and self.mouse_control_var.get():
                pyautogui.rightClick()
                
            elif action == 'scroll_up' and self.mouse_control_var.get():
                pyautogui.scroll(3)
                
            elif action == 'scroll_down' and self.mouse_control_var.get():
                pyautogui.scroll(-3)
                
            elif action == 'drag' and self.mouse_control_var.get():
                # Start dragging if not already
                if not self.is_dragging:
                    pyautogui.mouseDown()
                    self.is_dragging = True
                
                # Move mouse while dragging (same logic as mouse_move)
                if len(landmarks) >= 24:
                    points = landmarks.reshape(-1, 3)
                    index_tip = points[8][:2]
                    
                    screen_x = int(index_tip[0] * self.screen_width)
                    screen_y = int(index_tip[1] * self.screen_height)
                    
                    current_pos = pyautogui.position()
                    smooth_x = int(current_pos.x * self.smoothing_var.get() + 
                                 screen_x * (1 - self.smoothing_var.get()))
                    smooth_y = int(current_pos.y * self.smoothing_var.get() + 
                                 screen_y * (1 - self.smoothing_var.get()))
                    
                    pyautogui.moveTo(smooth_x, smooth_y)

            # Advanced System Controls
            elif action == 'brightness_up' and self.system_control_var.get():
                # macOS brightness up - use AppleScript for better compatibility
                subprocess.run(['osascript', '-e', 
                              'tell application "System Events" to key code 144'], 
                             check=False, capture_output=True, timeout=1)
                
            elif action == 'brightness_down' and self.system_control_var.get():
                # macOS brightness down
                subprocess.run(['osascript', '-e', 
                              'tell application "System Events" to key code 145'], 
                             check=False, capture_output=True, timeout=1)
                
            elif action == 'minimize_all' and self.system_control_var.get():
                # Show Desktop on macOS
                subprocess.run(['osascript', '-e', 
                              'tell application "System Events" to key code 103 using {command down}'], 
                             check=False, capture_output=True, timeout=1)
                
            elif action == 'prev_tab' and self.system_control_var.get():
                pyautogui.hotkey('command', 'shift', '[')
                
            elif action == 'next_tab' and self.system_control_var.get():
                pyautogui.hotkey('command', 'shift', ']')
                
            elif action == 'zoom_in' and self.system_control_var.get():
                pyautogui.hotkey('command', '+')
                
            elif action == 'zoom_out' and self.system_control_var.get():
                pyautogui.hotkey('command', '-')
                
            elif action == 'double_click' and self.mouse_control_var.get():
                pyautogui.doubleClick()
                
            elif action == 'mission_control' and self.system_control_var.get():
                # Mission Control on macOS
                subprocess.run(['osascript', '-e', 
                              'tell application "System Events" to key code 160'], 
                             check=False, capture_output=True, timeout=1)
                             
            elif action == 'show_desktop' and self.system_control_var.get():
                # Show Desktop - F11
                pyautogui.press('f11')
                
            elif action == 'scroll_left' and self.mouse_control_var.get():
                pyautogui.hscroll(-3)
                
            elif action == 'scroll_right' and self.mouse_control_var.get():
                pyautogui.hscroll(3)
                
            elif action == 'media_pause' and self.system_control_var.get():
                pyautogui.press('playpause')
                
            elif action == 'media_play' and self.system_control_var.get():
                pyautogui.press('playpause')
                
            elif action == 'screenshot' and self.system_control_var.get():
                pyautogui.hotkey('command', 'shift', '4')
                
            elif action == 'open_terminal' and self.system_control_var.get():
                subprocess.run(['open', '-a', 'Terminal'], 
                             check=False, capture_output=True, timeout=1)
                             
            elif action == 'undo' and self.system_control_var.get():
                pyautogui.hotkey('command', 'z')
                
            elif action == 'lock_screen' and self.system_control_var.get():
                pyautogui.hotkey('command', 'ctrl', 'q')

        except subprocess.TimeoutExpired:
            self.logger.warning(f"Action {action} timed out")
        except Exception as e:
            self.logger.error(f"Error executing action {action}: {e}")
            
    def update_video_display(self, frame):
        """Update the video display with current frame"""
        try:
            # Resize frame for display
            display_frame = cv2.resize(frame, (640, 480))
            
            # Convert to PIL Image
            image = Image.fromarray(cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB))
            photo = ImageTk.PhotoImage(image)
            
            # Update display
            self.video_label.config(image=photo, text="")
            self.video_label.image = photo
            
        except Exception as e:
            self.logger.error(f"Error updating video display: {e}")
            
    def update_info_displays(self, data):
        """Update information displays"""
        try:
            # Update gesture info
            gesture_text = data.get('gesture', 'None').replace('_', ' ').title()
            self.gesture_label.config(text=gesture_text)
            
            confidence = data.get('confidence', 0.0)
            self.confidence_label.config(text=f"Confidence: {confidence:.0%}")
            self.confidence_bar['value'] = confidence * 100
            
            # Update performance metrics
            fps = data.get('fps', 0)
            self.fps_label.config(text=f"{fps:.1f}")
            
            process_time = data.get('process_time', 0)
            self.processing_time_label.config(text=f"{process_time:.1f}ms")
            
            # Update hands detected
            hands_count = data.get('hands_count', 0)
            self.hands_detected_label.config(text=f"{hands_count}")
            
        except Exception as e:
            self.logger.error(f"Error updating displays: {e}")
            
    def save_settings(self):
        """Save current settings to file"""
        try:
            settings = {
                'sensitivity': self.sensitivity_var.get(),
                'smoothing': self.smoothing_var.get(),
                'mouse_control': self.mouse_control_var.get(),
                'system_control': self.system_control_var.get(),
                'gesture_mappings': self.gesture_mappings
            }
            
            with open('gesture_settings.json', 'w') as f:
                json.dump(settings, f, indent=2)
                
            messagebox.showinfo("Settings", "Settings saved successfully!")
            self.logger.info("Settings saved")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
            self.logger.error(f"Error saving settings: {e}")
            
    def load_settings(self):
        """Load settings from file"""
        try:
            if os.path.exists('gesture_settings.json'):
                with open('gesture_settings.json', 'r') as f:
                    settings = json.load(f)
                
                self.sensitivity_var.set(settings.get('sensitivity', 0.7))
                self.smoothing_var.set(settings.get('smoothing', 0.3))
                self.mouse_control_var.set(settings.get('mouse_control', True))
                self.system_control_var.set(settings.get('system_control', True))
                self.gesture_mappings.update(settings.get('gesture_mappings', {}))
                
                self.logger.info("Settings loaded")
                
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")
            
    def show_analytics(self):
        """Show analytics window with performance charts"""
        if not hasattr(self, 'analytics_window') or self.analytics_window is None or not self.analytics_window.winfo_exists():
            self.create_analytics_window()
        else:
            self.analytics_window.lift()
            
    def create_analytics_window(self):
        """Create the analytics window"""
        self.analytics_window = tk.Toplevel(self.root)
        self.analytics_window.title("📊 Gesture Analytics")
        self.analytics_window.geometry("800x600")
        self.analytics_window.configure(bg=self.colors['bg_dark'])
        
        # Create notebook for different analytics tabs
        notebook = ttk.Notebook(self.analytics_window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Performance tab
        perf_frame = ttk.Frame(notebook)
        notebook.add(perf_frame, text="Performance")
        
        # Create performance charts
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
        fig.patch.set_facecolor(self.colors['bg_dark'])
        
        # FPS chart
        if self.fps_history:
            ax1.plot(list(self.fps_history), color=self.colors['success'], linewidth=2)
            ax1.set_title('FPS Over Time', color=self.colors['text_primary'])
            ax1.set_ylabel('FPS', color=self.colors['text_secondary'])
            ax1.tick_params(colors=self.colors['text_secondary'])
            ax1.set_facecolor(self.colors['bg_panel'])
            ax1.grid(True, alpha=0.1)
        
        # Processing time chart
        if self.detection_times:
            ax2.plot(list(self.detection_times), color=self.colors['warning'], linewidth=2)
            ax2.set_title('Processing Time', color=self.colors['text_primary'])
            ax2.set_ylabel('Time (ms)', color=self.colors['text_secondary'])
            ax2.set_xlabel('Frame', color=self.colors['text_secondary'])
            ax2.tick_params(colors=self.colors['text_secondary'])
            ax2.set_facecolor(self.colors['bg_panel'])
            ax2.grid(True, alpha=0.1)
        
        canvas = FigureCanvasTkAgg(fig, perf_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)
        
    def on_closing(self):
        """Handle application closing"""
        if self.is_running:
            self.stop_detection()
        
        self.save_settings()
        self.root.destroy()
        
    def run(self):
        """Run the application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

def main():
    """Main function to run the Professional Gesture Control System"""
    try:
        app = GestureControlPro()
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}")
        logging.error(f"Error starting application: {e}")

if __name__ == "__main__":
    main()
