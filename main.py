import os
import sys
import random
import yaml
import pygame
import logging
from gpiozero import Button
from signal import pause
from datetime import datetime

# === Constants ===
CONFIG_DIR = "config"  # Directory containing YAML files
SWITCH_BUTTON_PIN = 17  # Pin for switch button (change as needed)
SWITCH_SOUND = "switch_sound.wav"  # Optional sound for switch action

# === Set up logging before sanity check ===
LOG_DIR = "log"  # Default log dir
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

# === Get list of YAML configuration files ===
def get_yaml_files():
    """Get all YAML files in the config directory."""
    yaml_files = [f for f in os.listdir(CONFIG_DIR) if f.endswith(".yaml")]
    yaml_files.sort()  # Ensure they are sorted (config_1.yaml, config_2.yaml, etc.)
    return yaml_files

yaml_files = get_yaml_files()

# === Load YAML file from the list ===
def load_yaml_file(file_name):
    """Load a specific YAML configuration file."""
    yaml_path = os.path.join(CONFIG_DIR, file_name)
    try:
        with open(yaml_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load config file: {yaml_path}", exc_info=True)
        return None

# === Resolve paths relative to current working directory ===
def resolve_path(path):
    """Resolve ~ and relative paths against current working directory."""
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)
    return os.path.abspath(path)

# === Switch state variables ===
current_config_index = 0  # Track the current YAML file being used
current_config = load_yaml_file(yaml_files[current_config_index])  # Load initial config

# === Extract and resolve paths from config ===
def extract_config_paths(config):
    """Extract paths from the given config dictionary."""
    log_dir = resolve_path(config.get("log_dir", "log"))
    sounds_dir = resolve_path(config.get("sounds_dir", "animal_sounds"))
    startup_sound = config.get("startup_sound")
    buttons = config.get("buttons", {})
    return log_dir, sounds_dir, startup_sound, buttons

# Initial paths extraction
LOG_DIR, SOUNDS_DIR, STARTUP_SOUND, BUTTONS = extract_config_paths(current_config)

# === Sanity check helper function ===
def check_exists(path, is_dir=True, description=""):
    """Checks if a path exists and is a directory or file, based on `is_dir`."""
    if is_dir:
        if not os.path.isdir(path):
            return f"Missing directory: {description} ({path})"
    else:
        if not os.path.isfile(path):
            return f"Missing file: {description} ({path})"
    return None

# === Sanity checks ===
errors = []

# Check log_dir, sounds_dir, and animal sound directories
errors.append(check_exists(LOG_DIR, is_dir=True, description="log_dir"))
errors.append(check_exists(SOUNDS_DIR, is_dir=True, description="sounds_dir"))

# Check for each animal sound directory
for animal in BUTTONS.values():
    animal_path = os.path.join(SOUNDS_DIR, animal)
    errors.append(check_exists(animal_path, is_dir=True, description=f"sound folder for {animal}"))

# Check if startup sound exists
if STARTUP_SOUND:
    startup_path = os.path.join(SOUNDS_DIR, STARTUP_SOUND)
    errors.append(check_exists(startup_path, is_dir=False, description="startup sound"))

# Exit if any sanity check failed
errors = [e for e in errors if e]  # Filter out None values
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
                    sound = pygame.mixer.Sound(full_path)
                    sounds.append(sound)
            logger.info(f"{animal}: {len(sounds)} sound(s) loaded.")
        except Exception:
            logger.error(f"Error loading sounds for {animal}", exc_info=True)

        animal_sounds[animal] = sounds

        btn = Button(pin)
        btn.when_pressed = lambda a=animal: play_random_sound(a)
        buttons.append(btn)

# Initial preload
preload_sounds(current_config)

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
    try:
        pygame.mixer.Sound(startup_path).play()
        logger.info("Startup sound played.")
    except pygame.error:
        logger.error("Failed to play startup sound", exc_info=True)

# === Switch button functionality ===
def switch_config():
    """Switch to the next YAML config and reload the sounds."""
    global current_config_index, current_config
    current_config_index = (current_config_index + 1) % len(yaml_files)  # Loop back to 0 when we reach the end
    current_config = load_yaml_file(yaml_files[current_config_index])
    LOG_DIR, SOUNDS_DIR, STARTUP_SOUND, BUTTONS = extract_config_paths(current_config)
    preload_sounds(current_config)
    logger.info(f"Switched to config {yaml_files[current_config_index]}")

    # Play switch sound if available
    if SWITCH_SOUND and os.path.isfile(SWITCH_SOUND):
        pygame.mixer.Sound(SWITCH_SOUND).play()
        logger.info("Switch sound played.")

# === Set up the switch button (if present) ===
if SWITCH_BUTTON_PIN:
    switch_button = Button(SWITCH_BUTTON_PIN)
    switch_button.when_pressed = switch_config

# === Wait indefinitely for button presses ===
logger.info("System ready. Waiting for button presses...")
pause()
