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
    level=logging.INFO,
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
    return yaml_files

def load_yaml_file(file_name):
    """Load a specific YAML configuration file."""
    yaml_path = os.path.join(CONFIG_DIR, file_name)
    try:
        with open(yaml_path, "r") as f:
            return yaml.safe_load(f)
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
logger.info("Script started.")

# === Preload animal sounds ===
animal_sounds = {}
buttons = []

def preload_sounds(config):
    """Preload sounds for each animal as per the given config."""
    global animal_sounds, buttons
    animal_sounds = {}
    buttons = []
    for pin_str, animal in config.get("buttons", {}).items():
        pin = int(pin_str)
        animal_path = os.path.join(SOUNDS_DIR, animal)
        sounds = []

        try:
            for file in os.listdir(animal_path):
                if file.endswith(('.wav', '.mp3', '.ogg')):
                    full_path = os.path.join(animal_path, file)
                    try:
                        sound = pygame.mixer.Sound(full_path)
                        sounds.append(sound)
                    except pygame.error:
                        logger.warning(f"Failed to load sound file: {full_path}")
            if not sounds:
                logger.warning(f"No valid sound files found for '{animal}' in {animal_path}")
        except Exception:
            logger.error(f"Error loading sounds for {animal}", exc_info=True)

        animal_sounds[animal] = sounds

        btn = Button(pin)
        btn.when_pressed = lambda a=animal: play_random_sound(a)
        buttons.append(btn)

# === Function to play a random sound ===
def play_random_sound(animal):
    sounds = animal_sounds.get(animal, [])
    if sounds:
        if pygame.mixer.get_busy():
            pygame.mixer.stop()
        random.choice(sounds).play()
        logger.info(f"Played sound for '{animal}'.")

# === Play startup sound ===
if STARTUP_SOUND:
    startup_path = os.path.join(SOUNDS_DIR, STARTUP_SOUND)
    if os.path.isfile(startup_path):
        try:
            pygame.mixer.Sound(startup_path).play()
            logger.info("Startup sound played.")
        except pygame.error:
            logger.error("Failed to play startup sound", exc_info=True)

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
        if os
