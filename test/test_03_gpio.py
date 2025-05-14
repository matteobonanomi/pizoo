from gpiozero import Button
from signal import pause
import logging

logging.basicConfig(level=logging.DEBUG)

button = Button(26)  # Replace with your pin number (e.g., 17)

def on_press():
    logging.debug("Button pressed!")

button.when_pressed = on_press
pause()  # Keeps the script running
