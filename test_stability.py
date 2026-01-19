#!/usr/bin/env python3
"""
Quick stability test for gesture control system
Tests for common issues that cause hanging/crashing
"""

import sys
import time

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    try:
        import cv2
        import tkinter
        import mediapipe
        import numpy
        import pyautogui
        import PIL
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_camera():
    """Test if camera can be accessed"""
    print("\nTesting camera access...")
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("✗ Cannot open camera")
            return False
        
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            print(f"✓ Camera working (frame size: {frame.shape})")
            return True
        else:
            print("✗ Cannot read from camera")
            return False
    except Exception as e:
        print(f"✗ Camera error: {e}")
        return False

def test_mediapipe():
    """Test MediaPipe hands initialization"""
    print("\nTesting MediaPipe...")
    try:
        import mediapipe as mp
        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        print("✓ MediaPipe initialized successfully")
        hands.close()
        return True
    except Exception as e:
        print(f"✗ MediaPipe error: {e}")
        return False

def test_pyautogui():
    """Test PyAutoGUI basic functions"""
    print("\nTesting PyAutoGUI...")
    try:
        import pyautogui
        screen_size = pyautogui.size()
        mouse_pos = pyautogui.position()
        print(f"✓ PyAutoGUI working (screen: {screen_size}, mouse: {mouse_pos})")
        return True
    except Exception as e:
        print(f"✗ PyAutoGUI error: {e}")
        return False

def test_gui():
    """Test if Tkinter GUI can be created"""
    print("\nTesting Tkinter GUI...")
    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide window
        root.after(100, root.destroy)  # Auto-close after 100ms
        root.mainloop()
        print("✓ Tkinter GUI working")
        return True
    except Exception as e:
        print(f"✗ GUI error: {e}")
        return False

def test_threading():
    """Test threading capabilities"""
    print("\nTesting threading...")
    try:
        import threading
        import queue
        
        test_queue = queue.Queue()
        
        def worker():
            test_queue.put("Thread executed")
        
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()
        thread.join(timeout=2.0)
        
        if not test_queue.empty():
            result = test_queue.get()
            print(f"✓ Threading working: {result}")
            return True
        else:
            print("✗ Thread did not execute")
            return False
    except Exception as e:
        print(f"✗ Threading error: {e}")
        return False

def test_syntax():
    """Test if gesture_control_pro.py has syntax errors"""
    print("\nTesting gesture_control_pro.py syntax...")
    try:
        import py_compile
        py_compile.compile('gesture_control_pro.py', doraise=True)
        print("✓ No syntax errors found")
        return True
    except py_compile.PyCompileError as e:
        print(f"✗ Syntax error: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Gesture Control System - Stability Test")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Camera", test_camera),
        ("MediaPipe", test_mediapipe),
        ("PyAutoGUI", test_pyautogui),
        ("GUI", test_gui),
        ("Threading", test_threading),
        ("Syntax", test_syntax)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
            results[test_name] = False
        time.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:20s} : {status}")
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! System should run without issues.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please fix issues before running.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
