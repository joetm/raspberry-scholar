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


# libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
# if os.path.exists(libdir): sys.path.append(libdir)

BASEDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)))

parser = argparse.ArgumentParser()
parser.add_argument("--dev", dest="IS_DEV", action="store_true", help="Dev mode: output image")
args = parser.parse_args()
IS_DEV = args.IS_DEV
print("DEV", IS_DEV)

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
  except:
    IS_DEV = True
    pass

if IS_DEV:
    IS_PI = False
    epd = FAKE_EPD(width=250, height=122)
print("IS_PI", IS_PI)



picdir = './'
font_small = ImageFont.truetype(os.path.join(BASEDIR, 'Font.ttc'), 22)
font_large = ImageFont.truetype(os.path.join(BASEDIR, 'Font.ttc'), 80)



class DISPLAY:
  def __init__(self, epd, is_pi=False):
    self.epd = epd
    self.is_pi = is_pi
    if is_pi:
      self.image = Image.new('1', (self.epd.height, self.epd.width), 255)  # 255: clear the frame
    else:
      self.image = Image.new('1', (self.epd.width, self.epd.height), 255)  # 255: clear the frame

  def render(self, citations, hindex, diff, weekly_increase, monthly_increase):
    # image = Image.new('1', (epd.width, epd.height), 255)  # 255: clear the frame
    # draw = ImageDraw.Draw(image)
    # draw.rectangle([(2,2),(248,120)], outline=0)
    # draw.text((32, 3), citations, font=font_large, fill=0)
    # draw.text((95, 90), f"h = {hindex}", font=font_small, fill=0)
    # image.save("output.png")
    # image.show()
    # draw = ImageDraw.Draw(image)
    # draw.rectangle([(2,2),(248,120)], outline=0)
    # draw.text((32, 3), citations, font=font_large, fill=0)
    # draw.text((95, 90), f"h = {hindex}", font=font_small, fill=0)
    draw = ImageDraw.Draw(self.image)

    draw.rectangle([(1,1),(249,121)], outline=0)

    draw.text((5, 0), str(citations), font=font_large, fill=0)

    # draw.line([(2,90), (185,90)])
    # draw.line([(185,2),(185,120)])

    # draw.text((5, 90), f"h = {hindex}", font=font_small, fill=0)
    draw.text((195, 15), f"h.{str(hindex)}", font=font_small, fill=0)

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
    draw.text((15, 92), longtext, font=font_small, fill=0)
    # draw.text((15, 90), f"{dsign}{str(diff)}", font=font_small, fill=0)
    # try:
    #   draw.text((65, 90), f"w{wsign}{str(weekly_increase['citations_increase'])}", font=font_small, fill=0)
    # except: pass
    # try:
    #   draw.text((110, 90), f"b{bisign}{str(biweekly_increase['citations_increase'])}", font=font_small, fill=0)
    # except: pass
    # try:
    #   draw.text((165, 90), f"m{msign}{str(monthly_increase['citations_increase'])}", font=font_small, fill=0)
    # except: pass

    print(fiveyears)

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

# ---
scholar_profile = 'ucO_QYQAAAAJ'
scholar_url = f'https://scholar.google.com/citations?user={scholar_profile}&hl=en'
result_file = os.path.join(BASEDIR, 'result.json')
LOG_FILE = os.path.join(BASEDIR, "logs.json")
# ---


# Load logs
try:
    with open(LOG_FILE, "r") as f: logs = json.load(f)
except FileNotFoundError:
    logs = []

# Clean old logs
def clean_logs(logs):
  one_month_ago = datetime.now() - timedelta(days=30)
  logs = [log for log in logs if datetime.fromisoformat(log["timestamp"]) >= one_month_ago]
  return logs

# Add a new log entry
def log_result(citations, hindex):
  global logs
  logs.append({"timestamp": datetime.now().isoformat(), "citations": citations, "hindex": hindex})
  logs = clean_logs(logs)
  with open(LOG_FILE, "w") as f: json.dump(logs, f)

# Compute increases
def compute_increase(latest, past_log):
  if latest and past_log:
    return {
      "citations_increase": latest["citations"] - past_log["citations"],
      "hindex_increase": latest["hindex"] - past_log["hindex"]
    }
  return {"citations_increase": 0, "hindex_increase": 0}

# Function to get the closest log entry before a given time
def get_closest_log(past_time):
  return max((log for log in logs if log["timestamp"] <= past_time), 
    key=lambda x: x["timestamp"], default=None)

def get_earliest_log(past_time):
    eligible = [log for log in logs if log["timestamp"] <= past_time]
    if not eligible:
        return logs[0]  # fallback to oldest
    return max(eligible, key=lambda x: x["timestamp"])

print(f"Scraping {scholar_url}...")

cookie_file = os.path.join(BASEDIR, 'cookie.txt')
with open(cookie_file, 'rt') as f: cookie = f.read()
headers = {
  'User-Agent': user_agent,
  'referer': 'https://www.google.com/',
  'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
  'Accept-Encoding': 'gzip, deflate, br',
  'Accept-Language': 'en-US,en;q=0.5',
  'Cache-Control': 'no-cache',
  'Connection': 'keep-alive',
  'DNT': '1',
  'Pragma': 'no-cache',
  'Sec-Fetch-Dest': 'document',
  'Sec-Fetch-Mode': 'navigate',
  'Sec-Fetch-Site': 'none',
  'Sec-Fetch-User': '?1',
  'Sec-GPC': '1',
  'Upgrade-Insecure-Requests': '1',
  'Cookie': cookie.strip(),
}

try:
  response = requests.get(scholar_url, headers=headers)
except requests.exceptions.ConnectTimeout as e:
  print(f"ERROR ConnectTimeout: {requests.exceptions.ConnectTimeout}: {e}")
  sys.exit()

page_html = response.text
soup = BeautifulSoup(page_html, 'html.parser')

res = {'citations': None, 'hindex': None}
stats = soup.select("table#gsc_rsb_st td.gsc_rsb_std") 
if stats:
  res['citations'] = int(stats[0].text)
  res['hindex'] = int(stats[2].text)
  log_result(res['citations'], res['hindex'])
  print(f"Citations: {res['citations']}")
  print(f"H-index: {res['hindex']}")

fiveyears = []
bars_box = soup.select("div.gsc_md_hist_b a.gsc_g_a span.gsc_g_al") 
if bars_box:
  for bar in bars_box:
    count = int(bar.text)
    fiveyears.append(count)
fiveyears = fiveyears[-5:]
# print("Last five years", fiveyears)


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
log_week = get_closest_log(now - timedelta(weeks=1))
log_biweek = get_closest_log(now - timedelta(weeks=2))
log_month = get_earliest_log(now - timedelta(days=30))

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
  epaper.render(citations, hindex, diff, weekly_increase, monthly_increase)


# DEV = always pop up image on PC
if not IS_PI or IS_DEV:
  # output an image
  print("Output image...")
  epaper = DISPLAY(epd=epd, is_pi=IS_PI)
  print('citations', citations, 'hindex', hindex, 'diff', diff, 'weekly_increase', weekly_increase, 'monthly_increase', monthly_increase)
  epaper.render(citations, hindex, diff, weekly_increase, monthly_increase)
