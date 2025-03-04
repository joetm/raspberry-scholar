#!/usr/bin/python3
# -*- coding: utf-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import os
import sys
import json
import random
import requests
from bs4 import BeautifulSoup
# import urllib.parse
from fake_useragent import UserAgent
from playsound import playsound


scholar_profile = 'ucO_QYQAAAAJ'
scholar_url = f'https://scholar.google.com/citations?user={scholar_profile}&hl=en'
cache_file = r'./result.json'
audiodir = './sounds'


seed = random.randint(0, 100000)
random.seed(seed)

ua = UserAgent(platforms='pc')
user_agent = ua.random


def play_audio(num=None):
  if num is not None:
    audiobasepath = os.path.join(audiodir, 'num', str(num))
    for path, subdirs, files in os.walk(audiobasepath, followlinks=False):
      if len(files) > 0:
        audiofiles = []
        for file in files: audiofiles.append(os.path.join(path, file))
        selected_audio = random.choice(audiofiles)
        print('playing - num')
        playsound(selected_audio)
        return
      else:
        audiobasepath = os.path.join(audiodir, 'repeatable')
        for path, subdirs, files in os.walk(audiobasepath, followlinks=False):
          audiofiles = []
          for file in files: audiofiles.append(os.path.join(path, file))
          selected_audio = random.choice(audiofiles)
          for i in range(0, num): playsound(selected_audio)
          print('playing - repeatable')
          return
  else:
    audiobasepath = os.path.join(audiodir, 'other', str(num))
    for path, subdirs, files in os.walk(audiobasepath, followlinks=False):
      audiofiles = []
      for file in files: audiofiles.append(os.path.join(path, file))
      selected_audio = random.choice(audiofiles)
      print('playing - other')
      playsound(selected_audio)
      return



lastscrape = None
if os.path.exists(cache_file):
  with open(cache_file, 'r') as f: lastscrape = json.load(f)


# print(f"Scraping {scholar_url}...")

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
  'Cookie': 'NID=513=XzyIGQwFTp3Otr8LzzwQJX1p1lg3MClz7wP_1oBK5luE3TayZtJZtqh8d-h_QNSgVRcpjzRXdXwSPswMnyxSjDnNj7E2WwIpczTFCFJ3zBB7M6M_p431mJc40WfDwwkJnR0rVXtkvc6fdnVI-jdVMfCNZOtvDggTNVpgGhsUFk-cnpevOk7JA6qGiOcoZFXVbdc6csq0YnodziZl2iMlmHXZr1_P3qbGWYnd2tI4t66CEy5hIiYZQUrN9QHgkgO6sbHUufIiENA0bD1xqi3T8XFW2Jo2blm1TARV9bidyoHpblKy19ZH3TxrILv2XdlEhxEiqiOvy3BTNcgw76PfZMySP01_o4EmOGsGh3lRkaafSH0ACCQsjY8bGLndUh8KMFv5O_Aobin4Ag62olFNPJfB3awG2qaAW83BDHwDOYR7JB6eHNVqpKgfh0sepfL-Gyx55DpFkysfIDsZOtm59pLGFUXS1_EWcaY6DbImyZvP3-JWA_fkrLh9WGTyF0Dv82sBZUQiHlbtBcizrGFmsf4; GSP=A=TrFiHQ:CPTS=1714639725:LM=1714639725:S=EoGORSQq8bDuvR4y; SID=g.a000jAi5w659ZcrbJLUOQnQFgh84JGA5WJMKmIRt49-U3sY8p7Jdwm3ZC8q66RJILcyF-YCMUQACgYKAbESAQASFQHGX2Mil11amWb-Dh2HLWy1debbkRoVAUF8yKpIPwSo5Ws4gcfh8hNeO0CA0076; __Secure-1PSID=g.a000jAi5w659ZcrbJLUOQnQFgh84JGA5WJMKmIRt49-U3sY8p7Jdtfg3kk5oXvUy189Ln0VtvAACgYKAQISAQASFQHGX2MiTPsogTDrotiNw5hTAa5TmxoVAUF8yKrxo3RpN3dDEJbJCRlnbQUW0076; __Secure-3PSID=g.a000jAi5w659ZcrbJLUOQnQFgh84JGA5WJMKmIRt49-U3sY8p7JdiSeFr9Zvw4SunTALYKOPtgACgYKAXsSAQASFQHGX2MijPLtub0TJ_Zny-TJ0EKJ5RoVAUF8yKpi1Rs7bANjt_DHArow96lE0076; HSID=AdCWfZhiRA8lDCTJ8; SSID=AAWnOPkHf2kSYMlrr; APISID=WpMQQdGVqMJMiLqD/AsKFPlU55rX6P1oDp; SAPISID=jvaMXvtnebW5Y7Sh/ABBW5_CPA1hOBaAK1; __Secure-1PAPISID=jvaMXvtnebW5Y7Sh/ABBW5_CPA1hOBaAK1; __Secure-3PAPISID=jvaMXvtnebW5Y7Sh/ABBW5_CPA1hOBaAK1; SIDCC=AKEyXzVhdDKv2Hf9-iLEY2m_ZTZuWD1bcMQi-JFpImlelIpK2_Dx8FDTUeJ8nHhNQ-nBj-58yWnS; __Secure-1PSIDCC=AKEyXzWkEsd7Sw9d60_EplNERf2hY5uOOqnT7ASQ-UgyQgK_XF6qTSRndL7xmJDQMNTZP4oQuOl_; __Secure-3PSIDCC=AKEyXzUn9L_nPP1upyKSgqY99RdZH10YJ7W8Jl1J5pKEbmY_izO8uwSmgA_j8aef-EJECUMk0L4; __Secure-1PSIDTS=sidts-CjIBLwcBXEwW5iqsyTBn0FyzYZXXdMroqHVgaUXPMhXup9Kx0swqkUI0EFnL8fwZPL_2OxAA; __Secure-3PSIDTS=sidts-CjIBLwcBXEwW5iqsyTBn0FyzYZXXdMroqHVgaUXPMhXup9Kx0swqkUI0EFnL8fwZPL_2OxAA; __Secure-ENID=19.SE=GG-kND0Yh3RE7FPBg5EDjayjVNaEWsyZtjO387fyqGSs-b8i_BeGwm7lwLEEPEs-2def6K5pZDSbTWkHgxoruBxS9FyYnHo6w0cTfGqAmw32g5z0Tn8Ox6Ulw0Z-c1Hy6gv5ufS7d9GfAK7Pb3mF5GQwjFqFsP5G4Lb0H4--1Uf2V3ajWZS7iVv2jnAGnNqoLQUH2RXui-Z1RJP-Q8ELRgsSIAyt_wVz7yhHjs6CXJir0R0tXMC-0Sn7y82veiQVsiCWmpXa9HVdq-LRiIayuOA9POAOxtew3Ubo0lPkIgxvHSLUXdZ5EuzgYQ4QUYOA96tDVoWPiwv3tEqIQgdXpcBCN4XWum8zMEQn9_zLEWJ4gXCjxRWuBqmYM1YwaPEJUbeAY6AS9OednumzfTocuqSZQvgPlRVzl4dMWx8ZF55jQRuR6g; AEC=AQTF6Hz21lXPaipFl-GKlyHtKWSdX0p6SXuYUrZgMDnyzGxWw-Tfl1A81Q; S=billing-ui-v3=nKAm-QbWnH3Jrcm8vGTaySOfb4xNd85U:billing-ui-v3-efe=nKAm-QbWnH3Jrcm8vGTaySOfb4xNd85U',
}
try:
  response = requests.get(scholar_url, headers=headers)
except requests.exceptions.ConnectTimeout as e:
  print(f"ERROR ConnectTimeout: {requests.exceptions.ConnectTimeout}: {e}")
  sys.exit()

page_html = response.text
# with open(f'tmp.html', 'w') as f: f.write(page_html)

soup = BeautifulSoup(page_html, 'html.parser')

res = {}
res['citations'] = None
res['hindex'] = None

stats = soup.select("table#gsc_rsb_st td.gsc_rsb_std") 
if stats:
  res['citations'] = int(stats[0].text)
  res['hindex'] = int(stats[2].text)





if lastscrape and res['citations']:
  if res['citations'] == lastscrape['citations']:
    print(f'No changes [{res["citations"]} citations]')
    # playsound(get_audio())
    sys.exit()


diff = res['citations'] - lastscrape['citations']

# DEV
# diff = 3

print(f"{diff} new citations!")

play_audio(num=diff)

# write new stats to disk
with open(cache_file, 'wt') as f: json.dump(res, f)
print("written.")


