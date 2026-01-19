import pyautogui
import sys
import time

print("Testing PyAutoGUI...")
try:
    pos = pyautogui.position()
    print(f"Current mouse position: {pos}")
    
    # Try a small move
    print("Attempting to move mouse...")
    pyautogui.moveRel(10, 10)
    print("Mouse moved.")
    
    print("PyAutoGUI test passed.")
except Exception as e:
    print(f"PyAutoGUI error: {e}")
