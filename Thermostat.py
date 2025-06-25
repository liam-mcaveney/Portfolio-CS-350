#!/usr/bin/env python3
"""
Thermostat.py

Buttons:
  • GPIO24 → Toggle Off ↔ Heat ↔ Cool
  • GPIO25 → Increase Set Point (+1°F)
  • GPIO12 → Decrease Set Point (−1°F)
Features:
  - Default set-point: 72°F
  - AHT20 temperature via I2C (catches I/O errors)
  - LEDs pulse or solid for heating/cooling logic
  - LCD: Line1=Date/Time, Line2 alternates Temp & State/SetPt
  - UART: "state,temp,set_point" every 30s
"""

from time import sleep
from datetime import datetime
from statemachine import StateMachine, State
from statemachine.exceptions import TransitionNotAllowed
import board
import adafruit_ahtx0
import digitalio
import adafruit_character_lcd.character_lcd as characterlcd
import serial
from gpiozero import Button, PWMLED
from threading import Thread
from math import floor

# Debug flag
DEBUG = True  # Set True to enable console logging

# ── I2C & AHT20 Temperature Sensor ───────────────────────────────
i2c = board.I2C()
thSensor = adafruit_ahtx0.AHTx0(i2c)
last_temp = 72.0  # fallback if sensor read fails  # fallback if sensor read fails

# ── UART Output Setup ────────────────────────────────────────────
ser = serial.Serial(port='/dev/ttyS0', baudrate=9600, timeout=1)

# ── PWM LEDs: Red = Heat, Blue = Cool ─────────────────────────────
redLED = PWMLED(18)
blueLED = PWMLED(23)

# ── 16×2 LCD (4-bit Parallel) ────────────────────────────────────
class ManagedDisplay:
    def __init__(self):
        pins = dict(rs=board.D17, en=board.D27, d4=board.D5,
                    d5=board.D6, d6=board.D13, d7=board.D26)
        self.lcd = characterlcd.Character_LCD_Mono(
            digitalio.DigitalInOut(pins['rs']),
            digitalio.DigitalInOut(pins['en']),
            digitalio.DigitalInOut(pins['d4']),
            digitalio.DigitalInOut(pins['d5']),
            digitalio.DigitalInOut(pins['d6']),
            digitalio.DigitalInOut(pins['d7']),
            16, 2
        )
        self.lcd.clear()

    def update(self, line1, line2):
        self.lcd.clear()
        self.lcd.message = f"{line1}\n{line2}"

    def cleanup(self):
        self.lcd.clear()

# Initialize display
display = ManagedDisplay()

# ── Thermostat State Machine ──────────────────────────────────────
class Thermostat(StateMachine):
    off  = State(initial=True)
    heat = State()
    cool = State()

    set_point = 72  # default °F
    cycle = off.to(heat) | heat.to(cool) | cool.to(off)

    def on_enter_off(self):
        if DEBUG: print("State: OFF")
        redLED.off()
        blueLED.off()

    def on_enter_heat(self):
        if DEBUG: print("State: HEAT")
        self.control_led()

    def on_exit_heat(self):
        redLED.off()

    def on_enter_cool(self):
        if DEBUG: print("State: COOL")
        self.control_led()

    def on_exit_cool(self):
        blueLED.off()

    def read_fahrenheit(self):
        global last_temp
        try:
            c = thSensor.temperature
            last_temp = (c * 9/5) + 32
        except OSError:
            if DEBUG: print("Sensor I/O error, using last known temperature")
        return last_temp

    def control_led(self):
        temp = floor(self.read_fahrenheit())
        if DEBUG: print(f"Temp={temp}, SetPt={self.set_point}")
        if self.current_state.id == 'heat':
            if temp < self.set_point:
                redLED.pulse(fade_in_time=1, fade_out_time=1)
            else:
                redLED.value = 1
        elif self.current_state.id == 'cool':
            if temp > self.set_point:
                blueLED.pulse(fade_in_time=1, fade_out_time=1)
            else:
                blueLED.value = 1

    def send_uart(self):
        temp = self.read_fahrenheit()
        msg = f"{self.current_state.id},{temp:.1f},{self.set_point}\n"
        ser.write(msg.encode())
        if DEBUG: print("UART->", msg.strip())

    def display_loop(self):
        counter = 0
        toggle = False
        while True:
            now = datetime.now().strftime("%m/%d %H:%M:%S")
            temp = self.read_fahrenheit()
            line2 = (f"Temp:{temp:.1f}F" if toggle
                     else f"{self.current_state.id.upper()} {self.set_point}F")
            display.update(now, line2)
            if self.current_state.id in ('heat','cool'):
                self.control_led()
            if counter % 30 == 0:
                self.send_uart()
            counter += 1
            if counter % 5 == 0:
                toggle = not toggle
            sleep(1)

    def start(self):
        Thread(target=self.display_loop, daemon=True).start()

# Instantiate & start
thermo = Thermostat()
thermo.start()

# ── Buttons: Toggle / Increase / Decrease ─────────────────────────
toggle_btn   = Button(24, bounce_time=0.2)  # debounce presses
increase_btn = Button(25, bounce_time=0.2)  # debounce presses
decrease_btn = Button(12, bounce_time=0.2)  # debounce presses

def btn_toggle():
    try:
        thermo.cycle()
    except TransitionNotAllowed:
        pass

def btn_inc():
    thermo.set_point += 1
    if DEBUG: print(f"Set Point increased to {thermo.set_point}")

def btn_dec():
    thermo.set_point -= 1
    if DEBUG: print(f"Set Point decreased to {thermo.set_point}")

# Bind buttons
toggle_btn.when_pressed   = btn_toggle
increase_btn.when_pressed = btn_inc
decrease_btn.when_pressed = btn_dec

# ── Main Loop ─────────────────────────────────────────────────────
try:
    while True:
        sleep(1)
except KeyboardInterrupt:
    display.cleanup()
    redLED.off()
    blueLED.off()
    ser.close()

