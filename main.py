import os
import sys
import random
import yaml
import pygame
import logging
from gpiozero import Button
from signal import pause
from datetime import datetime

# === Setup logging ===
LOG_DIR = "/home/mbona/log"
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

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.error("Eccezione non gestita", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

# === Config ===
YAML_FILE = "/home/mbona/animali.yaml"
SOUNDS_DIR = "/home/mbona/animal_sounds"

pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.mixer.init()

logger.info("Avvio script...")

# === Carica YAML ===
try:
    with open(YAML_FILE, "r") as f:
        config = yaml.safe_load(f)
except Exception as e:
    logger.error("Errore nella lettura del file YAML", exc_info=True)
    sys.exit(1)

BUTTONS = config.get("buttons", {})
STARTUP_SOUND_PATH = config.get("startup_sound")

# === Precarica suoni ===
animal_sounds = {}
buttons = []

for pin_str, animale in BUTTONS.items():
    pin = int(pin_str)
    path = os.path.join(SOUNDS_DIR, animale)
    suoni = []
    try:
        for file in os.listdir(path):
            if file.endswith(('.wav', '.mp3', '.ogg')):
                full_path = os.path.join(path, file)
                sound = pygame.mixer.Sound(full_path)
                suoni.append(sound)
        logger.info(f"{animale}: {len(suoni)} suoni caricati.")
    except Exception as e:
        logger.error(f"Errore caricando i suoni per {animale}", exc_info=True)
    animal_sounds[animale] = suoni

    btn = Button(pin)
    btn.when_pressed = lambda a=animale: play_random_sound(a)
    buttons.append(btn)

def play_random_sound(animale):
    suoni = animal_sounds.get(animale, [])
    if suoni:
        if pygame.mixer.get_busy():
            pygame.mixer.stop()
        random.choice(suoni).play()
        logger.info(f"Riproduzione suono casuale per '{animale}'.")

# === Suono di avvio ===
if STARTUP_SOUND_PATH and os.path.exists(STARTUP_SOUND_PATH):
    try:
        start_sound = pygame.mixer.Sound(STARTUP_SOUND_PATH)
        start_sound.play()
        logger.info("Suono di avvio riprodotto.")
    except pygame.error:
        logger.error("Errore riproduzione suono di avvio", exc_info=True)

logger.info("Sistema pronto. In attesa della pressione dei pulsanti.")
pause()
