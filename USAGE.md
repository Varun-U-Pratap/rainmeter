# DSATracker – Modular usage

The program is **modular** and can be reused in other projects.

---

## What is modular

| Part | Reusable | Notes |
|------|----------|--------|
| **stats.py** | Yes | Single script; all paths come from config or script folder. |
| **config.json** | Yes | Usernames, optional `base_dir` and `output_format`. |
| **LeetCode / GFG logic** | Yes | Fetchers are self-contained; config supplies usernames. |
| **Streak / history** | Yes | Stored in JSON; format is generic. |
| **Rainmeter skin** | Yes | Copy `DSATracker.ini` + `variables.inc` + images; point to your script folder. |

---

## Using in another folder or app

1. **Copy** `stats.py` and `config.json` into your project (or point the skin to this folder).
2. **config.json** – set `leetcode_username` and `gfg_username`. Optional:
   - **base_dir** – folder for `history.json`, `variables.inc`, `debug.log`. Empty = same folder as `stats.py`. Use another path to keep data elsewhere.
   - **output_format** – `"rainmeter"` (default) or `"json"`.
3. **Run** `python stats.py` or `pythonw stats.py` from that folder (or use full path in Rainmeter).

---

## Output formats

- **rainmeter** (default)  
  Writes `variables.inc` and prints one `RAINMETER:Streak=...|...` line for the skin.

- **json**  
  Same as above, and:
  - Writes **stats.json** with: `streak`, `total_solved`, `lc_count`, `gfg_count`, `fire_on`, `fire_img`.
  - Prints one JSON line to stdout so other apps can pipe or read it.

Example for a web app or another widget: set `"output_format": "json"`, run the script on a schedule, and read `stats.json` or the JSON line from stdout.

---

## Rainmeter in another skin

1. Copy the whole **DSATracker** folder under Skins (or merge into your layout).
2. **Python path (modular):** The .ini uses generic `PythonPath=pythonw` by default. To use a full path (e.g. to avoid the App Installer popup), edit **local.inc** in the same folder: uncomment the `PythonPath` and `PythonParam` lines and set your path. The main .ini never contains user-specific paths.
3. Keep `variables.inc` in the same folder as the .ini; the script will write it there (or to `base_dir` if set).

---

## Dependencies

- **Python 3** with standard library only (`json`, `urllib.request`, `re`, `datetime`, `os`, `time`).
- Network access for LeetCode and GFG.

No extra pip packages required.
