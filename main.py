#!/usr/bin/env python3

import os
import sys
import random
import yaml
import pygame
import logging
from gpiozero import Button
from signal import pause
from datetime import datetime
import time

# === Constants ===
CONFIG_DIR = "config"  # Directory containing YAML files

# === Set up logging ===
LOG_DIR = "log"  # Default log dir
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

log_filename = os.path.join(LOG_DIR, f"session_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# === Helper functions ===
def resolve_path(path):
    """Resolve ~ and relative paths against current working directory."""
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)
    logger.debug(f"Resolved path: {path}")
    return os.path.abspath(path)

def check_exists(path, is_dir=True, description=""):
    """Checks if a path exists and is a directory or file, based on `is_dir`."""
    if is_dir:
        if not os.path.isdir(path):
            return f"Missing directory: {description} ({path})"
    else:
        if not os.path.isfile(path):
            return f"Missing file: {description} ({path})"
    return None

def get_yaml_files():
    """Get all YAML files in the config directory."""
    if not os.path.isdir(CONFIG_DIR):
        logger.error(f"Config directory not found: {CONFIG_DIR}")
        sys.exit(1)
    yaml_files = [f for f in os.listdir(CONFIG_DIR) if f.endswith(".yaml")]
    yaml_files.sort()
    if not yaml_files:
        logger.error("No configuration files (.yaml) found in config directory.")
        sys.exit(1)
    logger.info(f"Found YAML config files: {yaml_files}")
    return yaml_files

def load_yaml_file(file_name):
    """Load a specific YAML configuration file."""
    yaml_path = os.path.join(CONFIG_DIR, file_name)
    try:
        with open(yaml_path, "r") as f:
            config = yaml.safe_load(f)
        logger.info(f"Loaded config file: {yaml_path}")
        return config
    except Exception as e:
        logger.error(f"Failed to load config file: {yaml_path}", exc_info=True)
        return None

def extract_config_paths(config):
    """Extract paths and settings from the given config dictionary."""
    log_dir = resolve_path(config.get("log_dir", "log"))
    sounds_dir = resolve_path(config.get("sounds_dir", "animal_sounds"))
    startup_sound = config.get("startup_sound")
    shutdown_sound = config.get("shutdown_sound")
    switch_sound = config.get("switch_sound")
    shutdown_button_pin = config.get("shutdown_button_pin")
    switch_button_pin = config.get("switch_button_pin")
    buttons = config.get("buttons", {})
    logger.debug(f"BUTTONS configuration: {buttons}")
    logger.debug(f"Extracted config paths: {log_dir}, {sounds_dir}")
    return log_dir, sounds_dir, startup_sound, shutdown_sound, switch_sound, shutdown_button_pin, switch_button_pin, buttons

# === Load initial configuration ===
yaml_files = get_yaml_files()
current_config_index = 0
current_config = load_yaml_file(yaml_files[current_config_index])
LOG_DIR, SOUNDS_DIR, STARTUP_SOUND, SHUTDOWN_SOUND, SWITCH_SOUND, SHUTDOWN_BUTTON_PIN, SWITCH_BUTTON_PIN, BUTTONS = extract_config_paths(current_config)

# === Sanity checks ===
errors = []

errors.append(check_exists(LOG_DIR, is_dir=True, description="log_dir"))
errors.append(check_exists(SOUNDS_DIR, is_dir=True, description="sounds_dir"))

for animal in BUTTONS.values():
    animal_path = os.path.join(SOUNDS_DIR, animal)
    errors.append(check_exists(animal_path, is_dir=True, description=f"sound folder for {animal}"))

if STARTUP_SOUND:
    startup_path = os.path.join(SOUNDS_DIR, STARTUP_SOUND)
    errors.append(check_exists(startup_path, is_dir=False, description="startup sound"))

errors = [e for e in errors if e]
if errors:
    for e in errors:
        logger.error(f"[ERROR] {e}")
    sys.exit(1)

# === Initialize pygame mixer ===
pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.mixer.init()
logger.info("Script started. Initializing pygame mixer.")

# === Preload animal sounds ===
animal_sounds = {}
buttons = []

def preload_sounds(config):
    """Preload sounds for each animal as per the given config."""
    global animal_sounds, buttons
    animal_sounds = {}
    buttons = []
    logger.debug("Starting to preload sounds...")
    
    for pin_str, animal in config.get("buttons", {}).items():
        pin = int(pin_str)
        animal_path = os.path.join(SOUNDS_DIR, animal)
        
        logger.debug(f"Checking sound directory for '{animal}' at path: {animal_path}")
        
        sounds = []
        
        if not os.path.isdir(animal_path):
            logger.warning(f"Animal sound directory not found: {animal_path}")
            continue

        try:
            for file in os.listdir(animal_path):
                if file.endswith(('.wav', '.mp3', '.ogg')):
                    full_path = os.path.join(animal_path, file)
                    try:
                        logger.debug(f"Attempting to load sound file: {full_path}")
                        sound = pygame.mixer.Sound(full_path)
                        sounds.append(sound)
                        logger.info(f"Loaded sound: {full_path} for animal: {animal}")
                    except pygame.error:
                        logger.warning(f"Failed to load sound file: {full_path}")
            if not sounds:
                logger.warning(f"No valid sound files found for '{animal}' in {animal_path}")
        except Exception as e:
            logger.error(f"Error loading sounds for {animal}: {str(e)}")

        animal_sounds[animal] = sounds

        btn = Button(pin)
        
        # Add debug log in the lambda function to confirm button presses
        btn.when_pressed = lambda a=animal: [play_random_sound(a), logger.debug(f"Button pressed for {a}")]
        buttons.append(btn)

# === Function to play a random sound ===
def play_random_sound(animal):
    sounds = animal_sounds.get(animal, [])
    if sounds:
        logger.debug(f"Playing sound for '{animal}' with {len(sounds)} sound(s) loaded")
        if pygame.mixer.get_busy():
            pygame.mixer.stop()
        sound = random.choice(sounds)
        sound.play()
        logger.info(f"Played sound for '{animal}'")
    else:
        logger.warning(f"No sounds available for '{animal}'")

# === Play startup sound ===
if STARTUP_SOUND:
    startup_path = os.path.join(SOUNDS_DIR, STARTUP_SOUND)
    logger.info(f"Trying to play startup sound from {startup_path}")
    if os.path.isfile(startup_path):
        try:
            pygame.mixer.Sound(startup_path).play()
            logger.info("Startup sound played.")
        except pygame.error:
            logger.error("Failed to play startup sound", exc_info=True)
    else:
        logger.warning(f"Startup sound file not found: {startup_path}")

# === Switch configuration ===
def switch_config():
    global current_config_index, current_config
    global LOG_DIR, SOUNDS_DIR, STARTUP_SOUND, SHUTDOWN_SOUND, SWITCH_SOUND, SHUTDOWN_BUTTON_PIN, SWITCH_BUTTON_PIN, BUTTONS

    current_config_index = (current_config_index + 1) % len(yaml_files)
    current_config = load_yaml_file(yaml_files[current_config_index])
    LOG_DIR, SOUNDS_DIR, STARTUP_SOUND, SHUTDOWN_SOUND, SWITCH_SOUND, SHUTDOWN_BUTTON_PIN, SWITCH_BUTTON_PIN, BUTTONS = extract_config_paths(current_config)
    preload_sounds(current_config)
    logger.info(f"Switched to config {yaml_files[current_config_index]}")

    if SWITCH_SOUND:
        switch_sound_path = os.path.join(SOUNDS_DIR, SWITCH_SOUND)
        if os.path.isfile(switch_sound_path):  # This checks if the switch sound file exists
            try:
                pygame.mixer.Sound(switch_sound_path).play()
                logger.info("Switch sound played.")
            except pygame.error:
                logger.error("Failed to play switch sound", exc_info=True)
        else:
            logger.warning(f"Switch sound file not found: {switch_sound_path}")

# === Wait indefinitely for button presses ===
logger.info("loading sounds")
preload_sounds(current_config)

if SWITCH_BUTTON_PIN is not None:
    try:
        switch_button = Button(int(SWITCH_BUTTON_PIN))
        switch_button.when_pressed = lambda: [logger.info("Switch button pressed."), switch_config()]
        logger.info(f"Switch button handler set on GPIO pin {SWITCH_BUTTON_PIN}")
    except Exception as e:
        logger.error(f"Failed to set up switch button on pin {SWITCH_BUTTON_PIN}: {str(e)}")

logger.info("System ready. Waiting for button presses...")
pause()
