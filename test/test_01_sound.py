# test_01_sound.py

import pygame
import os

# Set up mixer and initialize pygame
pygame.mixer.init()

# Define the path to the startup sound
sound_path = os.path.join("sounds", "startup.wav")

# Check if the file exists
if not os.path.isfile(sound_path):
    print(f"Sound file not found: {sound_path}")
else:
    sound = pygame.mixer.Sound(sound_path)
    sound.play()
    print("Playing startup sound...")
    while pygame.mixer.get_busy():
        pass  # Wait until the sound finishes playing
