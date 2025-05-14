# 🐾 PiZoo | Animal Sound Game for Raspberry Pi

An interactive and educational soundboard game designed for children, utilizing physical buttons connected to a Raspberry Pi. Each button triggers a random animal sound, with additional buttons for switching configurations and safely shutting down the system.

---

## 🎯 Features

- **Interactive Soundboard**: Assign animal sounds to physical buttons; pressing a button plays a random sound associated with that animal.
- **Multiple Configurations**: Support for multiple YAML configuration files, allowing different setups without modifying the code.
- **Startup and Shutdown Sounds**: Play specific sounds during system startup and before shutdown for a complete user experience.
- **Safe Shutdown**: Dedicated shutdown button ensures the Raspberry Pi powers off safely after playing a shutdown sound.
- **Switch Configuration**: A switch button allows cycling through different configurations on the fly.
- **Robust Error Handling**: Logs warnings for missing audio files or directories without halting execution.

---

## 📁 Project Structure

```
animal-sound-game/
├── config/
│   ├── config.yaml
│   ├── config_1.yaml
│   └── config_2.yaml
├── animal_sounds/
│   ├── cat/
│   │   ├── meow1.wav
│   │   └── meow2.wav
│   ├── dog/
│   │   ├── bark1.wav
│   │   └── bark2.wav
│   └── cow/
│       ├── moo1.wav
│       └── moo2.wav
├── log/
├── main.py
└── README.md
```

---

## 🛠️ Requirements

- Raspberry Pi (any model with GPIO support)
- Python 3.7 or higher
- Physical buttons connected to GPIO pins
- Speakers or headphones connected to the Raspberry Pi

---

## 🐍 Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/yourusername/animal-sound-game.git
   cd animal-sound-game
   ```

2. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

   *Note: Ensure `gpiozero`, `pygame`, and `PyYAML` are included in your `requirements.txt`.*

3. **Set Up Audio Files**:

   Place your `.wav`, `.mp3`, or `.ogg` animal sound files into the corresponding directories under `animal_sounds/`. For example:

   ```
   animal_sounds/
   ├── cat/
   │   ├── meow1.wav
   │   └── meow2.wav
   └── dog/
       ├── bark1.wav
       └── bark2.wav
   ```

4. **Configure `config.yaml`**:

   Edit the `config/config.yaml` file to map GPIO pins to animal names and specify other settings. See the [Configuration](#gear-configuration) section below for details.

---

## ⚙️ Configuration

The `config.yaml` file defines the behavior of the game. Here's an example configuration:

```yaml
log_dir: "log"
sounds_dir: "animal_sounds"
startup_sound: "startup.wav"
shutdown_sound: "shutdown.wav"
switch_sound: "switch_sound.wav"
switch_button_pin: 17
shutdown_button_pin: 27

buttons:
  "2": cat
  "3": dog
  "4": cow
```

- `log_dir`: Directory where log files will be stored.
- `sounds_dir`: Directory containing subdirectories for each animal's sounds.
- `startup_sound`: Sound played when the program starts.
- `shutdown_sound`: Sound played before the system shuts down.
- `switch_sound`: Sound played when switching configurations.
- `switch_button_pin`: GPIO pin number for the switch configuration button.
- `shutdown_button_pin`: GPIO pin number for the shutdown button.
- `buttons`: Mapping of GPIO pins to animal names.

*Note: Ensure that the `startup_sound`, `shutdown_sound`, and `switch_sound` files are placed directly within the `sounds_dir`.*

---

## 🚀 Usage

1. **Run the Program**:

   ```bash
   python main.py
   ```

2. **Interact**:

   - Press the animal buttons to play random sounds associated with each animal.
   - Press the switch button to cycle through different configurations defined in the `config/` directory.
   - Press the shutdown button to play the shutdown sound and safely power off the Raspberry Pi.

---

## 📝 Logging

Logs are stored in the directory specified by `log_dir` in the configuration file. Each session generates a new log file named with the current timestamp, e.g., `session_2025-05-13_22-55-01.log`.

---

## ⚠️ Error Handling

- If the `config/` directory is missing or contains no `.yaml` files, the program will log an error and exit.
- Missing audio files or directories for specified animals will generate warnings in the log but will not stop the program from running.

---

## 📷 Visual Setup

*Include images or diagrams of your hardware setup here to assist users in replicating the physical configuration.*

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙏 Acknowledgments

Inspired by educational tools that combine physical interaction with auditory learning to engage children in a fun and interactive way.
