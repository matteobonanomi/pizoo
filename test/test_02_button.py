# test_02_button.py

from gpiozero import Button
import pygame
import os
from signal import pause

# Initialize pygame mixer
pygame.mixer.init()

# Path to shutdown sound
sound_path = os.path.join("sounds", "shutdown.wav")

if not os.path.isfile(sound_path):
    print(f"Shutdown sound not found: {sound_path}")
else:
    sound = pygame.mixer.Sound(sound_path)

    def handle_button_press():
        print("Button pressed! Playing shutdown sound...")
        sound.play()

    # Use GPIO pin 26 (you can change this)
    button = Button(26)
    button.when_pressed = handle_button_press

    print("Waiting for button press on GPIO17...")
    pause()
