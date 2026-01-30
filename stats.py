import json
import urllib.request
import urllib.error
import re
import datetime
import os
import sys
import time

# --- CONFIGURATION ---
# Loaded from config.json
# ---------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")
HISTORY_FILE = os.path.join(SCRIPT_DIR, "history.json")
VARIABLES_FILE = os.path.join(SCRIPT_DIR, "variables.inc")
DEBUG_LOG = os.path.join(SCRIPT_DIR, "debug.log")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Content-Type': 'application/json'
}

def log_message(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] {message}"
    print(formatted_msg)
    try:
        with open(DEBUG_LOG, "a") as f:
            f.write(formatted_msg + "\n")
    except:
        pass

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        log_message("Config file not found. Using defaults.")
        return {"leetcode_username": "upratapvarun", "gfg_username": "upratapim33"}

config = load_config()
LEETCODE_USER = config.get("leetcode_username", "upratapvarun")
GFG_USER = config.get("gfg_username", "upratapim33")

def get_leetcode_stats():
    """
    Fetches LeetCode total solved count using GraphQL.
    """
    log_message(f"Fetching LeetCode stats for {LEETCODE_USER}...")
    query = """
    query userProblemsSolved($username: String!) {
        allQuestionsCount {
            difficulty
            count
        }
        matchedUser(username: $username) {
            submitStats {
                acSubmissionNum {
                    difficulty
                    count
                    submissions
                }
            }
        }
    }
    """
    data = {
        "query": query,
        "variables": {"username": LEETCODE_USER}
    }
    
    try:
        req = urllib.request.Request(
            "https://leetcode.com/graphql", 
            data=json.dumps(data).encode('utf-8'), 
            headers=HEADERS
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            resp_json = json.loads(response.read().decode('utf-8'))
            if 'data' in resp_json and 'matchedUser' in resp_json['data']:
                # Get the 'All' count
                ac_submissions = resp_json['data']['matchedUser']['submitStats']['acSubmissionNum']
                for item in ac_submissions:
                    if item['difficulty'] == 'All':
                        return int(item['count'])
    except Exception as e:
        log_message(f"Error fetching LeetCode: {e}")
    return None

def get_gfg_stats():
    """
    Fetches GFG total solved count by scraping the profile page.
    Fallback: Vercel API.
    """
    log_message(f"Fetching GFG stats for {GFG_USER}...")
    # Method 1: Scrape Profile
    try:
        url = f"https://www.geeksforgeeks.org/user/{GFG_USER}/"
        # We need to accept text/html
        headers_html = HEADERS.copy()
        del headers_html['Content-Type']
        
        req = urllib.request.Request(url, headers=headers_html)
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # Look for the "Problem Solved" stats. 
            # The structure often changes, but usually the number is near the text.
            # Pattern: "Problem Solved" ... >21<
            # Trying a few patterns
            
            # Pattern 1: New Profile Design
            # <div class="...">Problem Solved</div> ... <div class="...">21</div>
            match = re.search(r"Problem Solved.*?(\d+)\s*<", html, re.IGNORECASE | re.DOTALL)
            if match:
                return int(match.group(1))
            
            # Pattern 2: Search for raw number if it follows specific class (riskier)
            # Let's try the Vercel API if scraping direct text fails, 
            # as GFG classes are randomized (e.g. scoreCard_head_left--score__3_M_E)
            
    except Exception as e:
        log_message(f"Error scraping GFG profile: {e}")

    # Method 2: Vercel API (Fallback)
    try:
        url = f"https://geeks-for-geeks-stats-card.vercel.app/?username={GFG_USER}"
        req = urllib.request.Request(url, headers={'User-Agent': HEADERS['User-Agent']})
        with urllib.request.urlopen(req, timeout=10) as response:
            svg_text = response.read().decode('utf-8')
            match = re.search(r"Problem Solved.*?>(\d+)<", svg_text, re.IGNORECASE | re.DOTALL)
            if match:
                return int(match.group(1))
            
            # Summation fallback
            def find_count(label):
                pattern = f"{label}.*?>(\\d+)<"
                m = re.search(pattern, svg_text, re.IGNORECASE | re.DOTALL)
                return int(m.group(1)) if m else 0
            
            total = find_count("School") + find_count("Basic") + find_count("Easy") + find_count("Medium") + find_count("Hard")
            if total > 0: 
                return total
    except Exception as e:
        log_message(f"Error fetching GFG via API: {e}")
        
    return None

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        "streak": 0,
        "last_lc_total": 0,
        "last_gfg_total": 0,
        "last_total": 0,
        "last_date": None,
        "daily_history": {},
        "last_activity_timestamp": 0
    }

def save_history(data):
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        log_message(f"Error saving history: {e}")

def get_current_week_dates():
    """Returns a list of 7 dates (YYYY-MM-DD) for the current week (Mon-Sun)."""
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday()) # Monday
    dates = []
    for i in range(7):
        day = start_of_week + datetime.timedelta(days=i)
        dates.append(day.strftime("%Y-%m-%d"))
    return dates

def main():
    log_message("--- Starting Update ---")
    
    # 1. Get Totals
    lc_count = get_leetcode_stats()
    if lc_count: log_message(f"LeetCode Success: {lc_count}")
    
    gfg_count = get_gfg_stats()
    if gfg_count: log_message(f"GFG Success: {gfg_count}")
    
    # Load History
    history = load_history()
    
    # Handle missing keys for migration
    if "last_lc_total" not in history: history["last_lc_total"] = 0
    if "last_gfg_total" not in history: history["last_gfg_total"] = 0
    if "last_activity_timestamp" not in history: history["last_activity_timestamp"] = 0
    
    last_lc = history.get("last_lc_total", 0)
    last_gfg = history.get("last_gfg_total", 0)
    
    # Use last known values if API fails
    final_lc = lc_count if lc_count is not None else last_lc
    final_gfg = gfg_count if gfg_count is not None else last_gfg
    
    # Calculate total
    total_now = final_lc + final_gfg
    
    today = datetime.date.today()
    today_str = today.strftime("%Y-%m-%d")
    yesterday = today - datetime.timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    
    # 2. Activity & Streak Logic
    
    # Check if we have solved anything NEW
    lc_increased = (lc_count is not None) and (lc_count > last_lc)
    gfg_increased = (gfg_count is not None) and (gfg_count > last_gfg)
    
    # Check if we were already active today (from previous run)
    was_active_today = history.get("daily_history", {}).get(today_str, False)
    
    current_timestamp = time.time()
    
    # Update timestamp if we have NEW activity
    if lc_increased or gfg_increased:
        history["last_activity_timestamp"] = current_timestamp
        was_active_today = True
        
    # Migration: If timestamp is 0 but we are active today, assume activity happened recently
    if history["last_activity_timestamp"] == 0 and was_active_today:
        history["last_activity_timestamp"] = current_timestamp

    # Update stored totals if they increased
    if lc_count is not None and lc_count > last_lc:
        history["last_lc_total"] = lc_count
    if gfg_count is not None and gfg_count > last_gfg:
        history["last_gfg_total"] = gfg_count
    
    # Recalculate Total based on stored bests (to avoid drops)
    history["last_total"] = history["last_lc_total"] + history["last_gfg_total"]
    
    # Update Daily History
    if "daily_history" not in history:
        history["daily_history"] = {}
    history["daily_history"][today_str] = was_active_today
    
    # Update Streak (Calendar Day based)
    streak_calc = 0
    check_date = today if was_active_today else yesterday
    
    while True:
        d_str = check_date.strftime("%Y-%m-%d")
        if history["daily_history"].get(d_str, False):
            streak_calc += 1
            check_date -= datetime.timedelta(days=1)
        else:
            break
            
    history["streak"] = streak_calc
    if was_active_today:
        history["last_date"] = today_str
        
    save_history(history)
    
    # 3. Generate variables.inc
    
    # Fire Logic: "Solved problem in past 24 hrs"
    # Strict 24h window check
    last_activity_ts = history.get("last_activity_timestamp", 0)
    time_since_activity = current_timestamp - last_activity_ts
    is_fire_on = time_since_activity < 86400 # 24 hours in seconds
    
    output_lines = []
    output_lines.append(f"Streak={history['streak']}")
    output_lines.append(f"TotalSolved={history['last_total']}")
    output_lines.append(f"LC_Count={history['last_lc_total']}")
    output_lines.append(f"GFG_Count={history['last_gfg_total']}")
    
    if is_fire_on:
        output_lines.append("FireImg=fireon.png")
    else:
        output_lines.append("FireImg=fireoff.png")
        
    # Weekly View Colors (Kept for compatibility/future use)
    week_dates = get_current_week_dates()
    COLOR_ACTIVE = "255,255,255,255"
    COLOR_INACTIVE = "60,60,60,255"
    
    for i, date_str in enumerate(week_dates):
        status = history["daily_history"].get(date_str, False)
        color = COLOR_ACTIVE if status else COLOR_INACTIVE
        output_lines.append(f"Day{i+1}Color={color}")
        
    with open(VARIABLES_FILE, "w") as f:
        f.write("[Variables]\n")
        f.write("\n".join(output_lines))
        f.write("\n")
    log_message("Stats updated successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_message(f"CRITICAL ERROR: {e}")
