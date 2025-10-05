#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import os
import sys
import json
# import time
# import logging
import argparse
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
# from fake_useragent import UserAgent
# ua = UserAgent(platforms='pc')
# user_agent = ua.random
user_agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0"
from scholarscrape import main as scrape
import time, socket
from known_credentials import KNOWN_NETWORKS


# ---
BASEDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)))
LOG_FILE = os.path.join(BASEDIR, "logs.json")
FONT_SMALL = ImageFont.truetype(os.path.join(BASEDIR, 'Font.ttc'), 22)
FONT_LARGE = ImageFont.truetype(os.path.join(BASEDIR, 'Font.ttc'), 80)
# ---
parser = argparse.ArgumentParser()
parser.add_argument("--dev", dest="IS_DEV", action="store_true", help="Dev mode: output image")
parser.add_argument("-s","--scholarid",dest="scholar_profile", help="Google Scholar ID")
args = parser.parse_args()
IS_DEV = args.IS_DEV
print("DEV", IS_DEV)
# ---
try:
    import network  # only exists on MicroPython
    IS_MICROPY = True
except ImportError:
    IS_MICROPY = False
if not IS_MICROPY:
    # stub out a minimal fake network module
    class DummyWLAN:
        def __init__(self, *_): pass
        def active(self, *_): return True
        def isconnected(self): return True
        def scan(self): return []
        def connect(self, *_, **__): pass
        def disconnect(self): pass
        def config(self, key=None):
            if key == "essid": return "ubuntu-test"
            return None
    network = type("network", (), {"WLAN": DummyWLAN, "STA_IF": 0})()
# ---
SCAN_TIMEOUT = 8
CONNECT_RETRIES = 2
MIN_RSSI = -90
INTERNET_CHECK_HOST = ("1.1.1.1", 80)
INTERNET_CHECK_TIMEOUT = 3
wlan = network.WLAN(network.STA_IF)
# ---

def _ensure_active():
    if not wlan.active():
        wlan.active(True)
        time.sleep(0.1)

def _internet_reachable():
    try:
        s = socket.socket()
        s.settimeout(INTERNET_CHECK_TIMEOUT)
        s.connect(INTERNET_CHECK_HOST)
        s.close()
        return True
    except Exception:
        try: s.close()
        except Exception: pass
        return False

def _current_ssid():
    try:
        # ifconnected and iface supports essid config
        if wlan.isconnected():
            try:
                essid = wlan.config("essid")
                if isinstance(essid, (bytes, bytearray)):
                    essid = essid.decode()
                return essid
            except Exception: return None
    except Exception: pass
    return None

def _scan_open_networks():
    _ensure_active()
    aps = wlan.scan()
    open_aps = []
    for ap in aps:
        ssid = ap[0].decode() if isinstance(ap[0], (bytes,bytearray)) else str(ap[0])
        rssi = ap[3]
        security = ap[4]
        if rssi < MIN_RSSI:
            continue
        if security == 0:
            open_aps.append((ssid, rssi))
    open_aps.sort(key=lambda x: x[1], reverse=True)
    seen = set(); unique = []
    for ssid, rssi in open_aps:
        if ssid not in seen: seen.add(ssid); unique.append((ssid, rssi))
    return unique

def connect_to(ssid, password=None, timeout=SCAN_TIMEOUT):
    _ensure_active()
    try: wlan.disconnect()
    except Exception: pass
    if password: wlan.connect(ssid, password)
    else: wlan.connect(ssid)
    start = time.time()
    while time.time() - start < timeout:
        if wlan.isconnected():
            if _internet_reachable(): return True
            else: return False
        time.sleep(0.2)
    return False

def try_existing_then_known_then_open():
    _ensure_active()
    # 1) If already connected and internet works, keep it
    if wlan.isconnected() and _internet_reachable():
        cur = _current_ssid()
        return True, cur or "connected (unknown ssid)"
    # 2) Try known networks (priority order)
    for ssid, pwd in KNOWN_NETWORKS:
        for attempt in range(CONNECT_RETRIES):
            if connect_to(ssid, password=pwd, timeout=SCAN_TIMEOUT):
                return True, ssid
            time.sleep(0.5 + attempt)
    # 3) Try open networks (strongest-first)
    open_aps = _scan_open_networks()
    for ssid, rssi in open_aps:
        for attempt in range(CONNECT_RETRIES):
            if connect_to(ssid, password=None, timeout=SCAN_TIMEOUT):
                return True, ssid
            time.sleep(0.5 + attempt)
    return False, None

def disconnect():
    try: wlan.disconnect()
    except Exception: pass
    try: wlan.active(False)
    except Exception: pass





class FAKE_EPD:
    def __init__(self, width, height):
        self.width = width
        self.height = height

if not IS_DEV:
  try:
    from waveshare_epd import epd2in13_V4
    epd = epd2in13_V4.EPD()
    IS_PI = True
    # logging.info("init and Clear")

    import network, time, credentials
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(credentials.ssid, credentials.password)
    while not wlan.isconnected(): time.sleep(1)
    print("Connected:", wlan.ifconfig())

  except:
    IS_DEV = True
    pass

if IS_DEV:
    IS_PI = False
    epd = FAKE_EPD(width=250, height=122)
print("IS_PI", IS_PI)






class DISPLAY:
  def __init__(self, epd, is_pi=False):
    self.epd = epd
    self.is_pi = is_pi
    if is_pi:
      self.image = Image.new('1', (self.epd.height, self.epd.width), 255)  # 255: clear the frame
    else:
      self.image = Image.new('1', (self.epd.width, self.epd.height), 255)  # 255: clear the frame

  def render(self, citations, hindex, diff, weekly_increase, monthly_increase, fiveyears):
    # image = Image.new('1', (epd.width, epd.height), 255)  # 255: clear the frame
    # draw = ImageDraw.Draw(image)
    # draw.rectangle([(2,2),(248,120)], outline=0)
    # draw.text((32, 3), citations, font=FONT_LARGE, fill=0)
    # draw.text((95, 90), f"h = {hindex}", font=FONT_SMALL, fill=0)
    # image.save("output.png")
    # image.show()
    # draw = ImageDraw.Draw(image)
    # draw.rectangle([(2,2),(248,120)], outline=0)
    # draw.text((32, 3), citations, font=FONT_LARGE, fill=0)
    # draw.text((95, 90), f"h = {hindex}", font=FONT_SMALL, fill=0)
    draw = ImageDraw.Draw(self.image)

    draw.rectangle([(1,1),(249,121)], outline=0)
    # draw.rectangle([(0,0),(250,122)], outline=0)

    draw.text((5, 0), str(citations), font=FONT_LARGE, fill=0)

    # draw.line([(2,90), (185,90)])
    # draw.line([(185,2),(185,120)])

    # draw.text((5, 90), f"h = {hindex}", font=FONT_SMALL, fill=0)
    draw.text((195, 15), f"h.{str(hindex)}", font=FONT_SMALL, fill=0)

    # dev
    if monthly_increase['citations_increase'] is None: monthly_increase['citations_increase'] = 0

    try: dsign = '+' if diff >= 0 else '-'
    except: dsign = ' '
    try: wsign = '+' if weekly_increase['citations_increase'] >= 0 else '-'
    except: wsign = ' '
    # try: bisign = '+' if biweekly_increase['citations_increase'] >= 0 else '-'
    # except: bisign = ' '
    try: msign = '+' if monthly_increase['citations_increase'] >= 0 else '-'
    except: msign = ' '

    longtext = f"{dsign}{str(abs(diff))}  w{wsign}{str(abs(weekly_increase['citations_increase']))}  m{msign}{str(abs(monthly_increase['citations_increase']))}"
    draw.text((15, 92), longtext, font=FONT_SMALL, fill=0)
    # draw.text((15, 90), f"{dsign}{str(diff)}", font=FONT_SMALL, fill=0)
    # try:
    #   draw.text((65, 90), f"w{wsign}{str(weekly_increase['citations_increase'])}", font=FONT_SMALL, fill=0)
    # except: pass
    # try:
    #   draw.text((110, 90), f"b{bisign}{str(biweekly_increase['citations_increase'])}", font=FONT_SMALL, fill=0)
    # except: pass
    # try:
    #   draw.text((165, 90), f"m{msign}{str(monthly_increase['citations_increase'])}", font=FONT_SMALL, fill=0)
    # except: pass

    barw, pad, H = 5, 5, 65
    minv, maxv = min(fiveyears), max(fiveyears)
    for i, y in enumerate(fiveyears):
        x0 = 190 + pad + i*(barw+pad)
        x1 = x0 + barw
        y1 = 115
        scale = (y - minv) / (maxv - minv) if maxv > minv else 0
        y0 = y1 - int(H * scale)
        draw.rectangle([(x0, y0), (x1, y1)], fill="black", outline=0)

    if self.is_pi:
      self.image = self.image.rotate(180) # rotate
      self.epd.init()
      self.epd.Clear(0xFF)
      self.epd.display(epd.getbuffer(self.image))
      self.epd.sleep()
    else:
      self.image.save("output.png")
      self.image.show()





# Compute increases
def compute_increase(latest, past_log):
  if latest and past_log:
    return {
      "citations_increase": latest["citations"] - past_log["citations"],
      "hindex_increase": latest["hindex"] - past_log["hindex"]
    }
  return {"citations_increase": 0, "hindex_increase": 0}

# Function to get the closest log entry before a given time
def get_closest_log(past_time, logs):
  return max((log for log in logs if log["timestamp"] <= past_time), 
    key=lambda x: x["timestamp"], default=None)

def get_earliest_log(past_time, logs):
    eligible = [log for log in logs if log["timestamp"] <= past_time]
    if not eligible:
        return logs[0]  # fallback to oldest
    return max(eligible, key=lambda x: x["timestamp"])



def scrape_and_display(scholar_profile):
  res = scrape(["-s", scholar_profile])
  fiveyears = res['yearlycitations'][-5:]
  print("Last five years", fiveyears)

  # Load logs
  try:
      with open(LOG_FILE, "r") as f: logs = json.load(f)
  except FileNotFoundError:
      logs = []

  # Convert timestamps to datetime objects and sort by time
  for log in logs: log["timestamp"] = datetime.fromisoformat(log["timestamp"])
  logs.sort(key=lambda x: x["timestamp"])

  # Get latest values
  try: latest = logs[-1]
  except: latest = None
  try: second = logs[-2]
  except: second = None

  # check if changes
  if (latest is None) and (second is None):
    print("Not enough log entries. Exiting.")
    sys.exit()

  citations = str(latest["citations"])
  hindex = str(latest["hindex"])

  # time windows
  now = datetime.now()
  log_week = get_closest_log(now - timedelta(weeks=1), logs)
  log_biweek = get_closest_log(now - timedelta(weeks=2), logs)
  log_month = get_earliest_log(now - timedelta(days=30), logs)

  weekly_increase = compute_increase(latest, log_week)
  biweekly_increase = compute_increase(latest, log_biweek)
  monthly_increase = compute_increase(latest, log_month)

  if latest['citations'] == second['citations']:
    ### NOTHING NEW
    print(f'No changes [{latest["citations"]} citations]')
    diff = 0

  else:
    ### NEW CITATIONS
    diff = latest['citations'] - second['citations']
    print(f"{diff} new citations!")

    # Print results
    print("Weekly Increase:", weekly_increase)
    print("Biweekly Increase:", biweekly_increase)
    print("Monthly Increase:", monthly_increase)

    # update the display
    # print("Update display...")
    epaper = DISPLAY(epd=epd, is_pi=IS_PI)
    epaper.render(citations, hindex, diff, weekly_increase, monthly_increase, fiveyears)

  # DEV = always pop up image on PC
  if not IS_PI or IS_DEV:
    # output an image
    print("Output image...")
    epaper = DISPLAY(epd=epd, is_pi=IS_PI)
    print('citations', citations, 'hindex', hindex, 'diff', diff, 'weekly_increase', weekly_increase, 'monthly_increase', monthly_increase, 'fiveyears', fiveyears)
    epaper.render(citations, hindex, diff, weekly_increase, monthly_increase, fiveyears)




def main(scrape_callback, scholar_profile, disconnect_after=True):
    ok, used = try_existing_then_known_then_open()
    if not ok: return False, "no-network"
    try: scrape_callback(scholar_profile)
    finally:
        if disconnect_after: disconnect()
    return True, used


if __name__ == "__main__":
    ok, wifi_ssid = main(scrape_and_display, args.scholar_profile)
    if ok: print("Success, used:", wifi_ssid)
    else: print("Failed to get network:", wifi_ssid)


