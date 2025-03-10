#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import os
import sys
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from fake_useragent import UserAgent
ua = UserAgent(platforms='pc')
user_agent = ua.random


# ---
scholar_profile = 'ucO_QYQAAAAJ'
scholar_url = f'https://scholar.google.com/citations?user={scholar_profile}&hl=en'
result_file = r'./result.json'
LOG_FILE = "logs.json"
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
  return {"citations_increase": None, "hindex_increase": None}

# Function to get the closest log entry before a given time
def get_closest_log(past_time):
  return max((log for log in logs if log["timestamp"] <= past_time), 
    key=lambda x: x["timestamp"], default=None)



print(f"Scraping {scholar_url}...")

with open('cookie.txt', 'rt') as f: cookie = f.read()
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



# Convert timestamps to datetime objects and sort by time
for log in logs: log["timestamp"] = datetime.fromisoformat(log["timestamp"])
logs.sort(key=lambda x: x["timestamp"])

# Get latest values
latest = logs[-1] if logs else None
second = logs[-2] if logs else None

# check if changes
if latest['citations'] == second['citations']:
  ### NOTHING NEW
  print(f'No changes [{latest["citations"]} citations]')
else:
  ### NEW CITATIONS
  diff = latest['citations'] - second['citations']
  print(f"{diff} new citations!")

  # time windows
  now = datetime.now()
  log_week = get_closest_log(now - timedelta(weeks=1))
  log_biweek = get_closest_log(now - timedelta(weeks=2))
  log_month = get_closest_log(now - timedelta(days=30))

  weekly_increase = compute_increase(latest, log_week)
  biweekly_increase = compute_increase(latest, log_biweek)
  monthly_increase = compute_increase(latest, log_month)

  # Print results
  print("Weekly Increase:", weekly_increase)
  print("Biweekly Increase:", biweekly_increase)
  print("Monthly Increase:", monthly_increase)

  # TODO: update the display




