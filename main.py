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
CONFIG_FILENAME = "animali.yaml"

# === Load config YAML from current working directory ===
YAML_PATH = os.path.join(os.getcwd(), CONFIG_FILENAME)
try:
    with open(YAML_PATH, "r") as f:
        config = yaml.safe_load(f)
except Exception as e:
    print(f"Failed to load config file: {YAML_PATH}")
    sys.exit(1)

# === Resolve paths relative to current working directory ===
def resolve_path(path):
    """Resolve ~ and relative paths against current working directory."""
    path = os.path.expanduser(path)
    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)
    return os.path.abspath(path)

# === Extract and resolve paths from config ===
LOG_DIR = resolve_path(config.get("log_dir", "log"))
SOUNDS_DIR = resolve_path(config.get("sounds_dir", "animal_sounds"))
STARTUP_SOUND = config.get("startup_sound")
BUTTONS = config.get("buttons", {})

# === Set up logging ===
os.makedirs(LOG_DIR, exist_ok=True)
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

# === Exception handling ===
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

# === Initialize pygame mixer ===
pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.mixer.init()
logger.info("Script started.")

# === Preload animal sounds ===
animal_sounds = {}
buttons = []

for pin_str, animal in BUTTONS.items():
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
    if os.path.exists(startup_path):
        try:
            pygame.mixer.Sound(startup_path).play()
            logger.info("Startup sound played.")
        except pygame.error:
            logger.error("Failed to play startup sound", exc_info=True)
    else:
        logger.warning(f"Startup sound not found at: {startup_path}")

# === Wait indefinitely for button presses ===
logger.info("System ready. Waiting for button presses...")
pause()
