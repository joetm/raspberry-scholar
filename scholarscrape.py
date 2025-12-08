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
from fake_useragent import UserAgent
# ua = UserAgent(platforms='pc')
# user_agent = ua.random
user_agent = "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0"


BASEDIR = os.path.join(os.path.dirname(os.path.realpath(__file__)))



result_file = os.path.join(BASEDIR, 'citations.json')
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
def log_result(obj):
  global logs
  output = {"timestamp": datetime.now().isoformat()}
  output.update(obj)
  logs.append(output)
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



def build_parser():
    p = argparse.ArgumentParser()
    p.add_argument("-s", "--scholarid", dest="scholar_profile")
    return p

def main(argv=None):
    args = build_parser().parse_args(argv)
    return run(args.scholar_profile)

def run(scholar_profile):
  if not scholar_profile:
    scholar_profile = '___DEFAULTSCHOLARIDHERE___'
  scholar_url = f'https://scholar.google.com/citations?user={scholar_profile}&hl=en'

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

  # get total citations and hindex
  res = {'citations': None, 'hindex': None}
  stats = soup.select("table#gsc_rsb_st td.gsc_rsb_std") 
  if stats:
    res['citations'] = int(stats[0].text)
    res['hindex'] = int(stats[2].text)
    print(f"Citations: {res['citations']}")
    print(f"H-index: {res['hindex']}")

  # get citation history
  yearlycitations = []
  bars_box = soup.select("div.gsc_md_hist_b a.gsc_g_a span.gsc_g_al") 
  if bars_box:
    for bar in bars_box:
      count = int(bar.text)
      yearlycitations.append(count)
  print("Citations per year", yearlycitations)


  res['yearlycitations'] = yearlycitations

  log_result(res)

  return res


  # # Convert timestamps to datetime objects and sort by time
  # for log in logs: log["timestamp"] = datetime.fromisoformat(log["timestamp"])
  # logs.sort(key=lambda x: x["timestamp"])

  # # Get latest values
  # try: latest = logs[-1]
  # except: latest = None
  # try: second = logs[-2]
  # except: second = None

  # # check if changes
  # if (latest is None) and (second is None):
  #   print("Not enough log entries. Exiting.")
  #   sys.exit()

  # citations = str(latest["citations"])
  # hindex = str(latest["hindex"])

  # # time windows
  # now = datetime.now()
  # log_week = get_closest_log(now - timedelta(weeks=1))
  # log_biweek = get_closest_log(now - timedelta(weeks=2))
  # log_month = get_earliest_log(now - timedelta(days=30))

  # weekly_increase = compute_increase(latest, log_week)
  # biweekly_increase = compute_increase(latest, log_biweek)
  # monthly_increase = compute_increase(latest, log_month)


if __name__ == "__main__":
    main()

