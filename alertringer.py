#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import neopixel
import redis
import sys
import signal
import logging


# LED strip configuration:
LED_COUNT      = 24      # Number of LED pixels per ring.
LED_RINGS      = 4       # Number of LED rings
LED_PIN        = 18      # GPIO pin connected to the pixels (must support PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 150     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)


leds = (LED_COUNT * LED_RINGS)
red        = neopixel.Color(0,255,0)
green      = neopixel.Color(255,0,0)
blue       = neopixel.Color(0,0,255)

yellow     = neopixel.Color(255,255,0)
black      = neopixel.Color(0,0,0)
halfgreen  = neopixel.Color(50,0,0)
halfyellow = neopixel.Color(150,150,0)


logfile = '/var/log/alertringer.log'
debug = True

logger = logging.getLogger("ringer")
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler = logging.FileHandler(logfile)
handler.setFormatter(formatter)
logger.addHandler(handler)


def signal_handler(signal, frame):
  logger.info('shutting down')
  for led in range(leds):
    strip.setPixelColor(led, black)
  strip.show()
  exit()


def rolling(strip, chart, color, wait_ms=(100/1000.0/2)):
  """ attempt for rolling x number of stuff """
  global paint
  #reset the things b4 
  for led in range(leds):
    strip.setPixelColor(led, black)

  # set the correct color
  for ring in range(LED_RINGS):
    if chart[ring]['red'] == 0 and chart[ring]['yellow'] == 0:
      for greenled in range(LED_COUNT):
        strip.setPixelColor((ring * LED_COUNT + (int(paint) - greenled + 1) % LED_COUNT), halfgreen)
    else:  
      # ringid * ledar/ring + ledid
      for redled in range(chart[ring]['red']):
        strip.setPixelColor((ring * LED_COUNT + (int(paint) - (redled + 1)) % LED_COUNT), red)
      for yellowled in range(chart[ring]['yellow']):
        strip.setPixelColor((ring * LED_COUNT + (int(paint) - (yellowled + 1) - (redled + 1)) % LED_COUNT), yellow)
  strip.show()
  time.sleep(wait_ms)
  paint = (paint + 1) % LED_COUNT


# Main program logic follows:
if __name__ == '__main__':
  logger.info('starting up')
  paint = 0
  signal.signal(signal.SIGTERM, signal_handler)
  r = redis.StrictRedis(host='localhost', port=6379, db=0)  
  # Create NeoPixel object with appropriate configuration.
  strip = neopixel.Adafruit_NeoPixel((LED_COUNT * LED_RINGS), LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)
  # Intialize the library (must be called once before other functions)
  strip.begin()
  while True:
    teams = {'access': 0, 'core': 0, 'powerpatrol': 0, 'services': 0}
    for key in r.scan_iter():
      team = key.split(':')[1] 
      teams[team] = teams[team] +1

    chart = {0: {'yellow': 0, 'red': teams['services']},
             1: {'yellow': 0, 'red': teams['core']},
             2: {'yellow': 0, 'red': teams['access']},
             3: {'yellow': 0, 'red': teams['powerpatrol']}}
    rolling(strip, chart, yellow) # Paint all the stuff
