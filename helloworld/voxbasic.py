import pyautogui
import time

# Wait for a moment to give user time to focus on the window
time.sleep(2)

# Write "Hello World" using pyautogui
pyautogui.write("Hello World")

# Press enter
pyautogui.press('enter')
