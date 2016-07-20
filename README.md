# LED Strip Controller
This is a simple web app to control RGB LEDs via a Raspberry Pi.

The front-end is a React app which talks to a Python Flask webserver.
The LEDs are controlled via GPIOs on the Raspberry Pi.

# Usage
  1. Make sure the Pi GPIO Daemon is running: `sudo pigpiod`
  1. Run the web server: `python server.py`

# Future Plans

Future plans include:
  - User login
  - Saved color palettes
  - More / better ways of picking a color
  - Scheduled lighting (e.g. turn on at 7am)
  - Transition control (e.g. sunrise/sunset simulation)
