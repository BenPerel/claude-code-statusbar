#!/usr/bin/env python3
import json, sys, subprocess, os

data = json.load(sys.stdin)

# --- Line 1: Session Info ---
model = data.get('model', {}).get('display_name', '?')
cwd = data.get('workspace', {}).get('current_dir', '') or data.get('cwd', '')
repo = os.path.basename(cwd) if cwd else '?'
cost = data.get('cost', {}).get('total_cost_usd', 0) or 0

RESET = '\033[0m'
GIT_GREEN = '\033[38;2;80;200;80m'
GIT_YELLOW = '\033[38;2;230;220;40m'

try:
    subprocess.check_output(['git', 'rev-parse', '--git-dir'], stderr=subprocess.DEVNULL)
    branch = subprocess.check_output(['git', 'branch', '--show-current'], text=True, stderr=subprocess.DEVNULL).strip() or '?'
    staged_out = subprocess.check_output(['git', 'diff', '--cached', '--numstat'], text=True, stderr=subprocess.DEVNULL).strip()
    modified_out = subprocess.check_output(['git', 'diff', '--numstat'], text=True, stderr=subprocess.DEVNULL).strip()
    staged = len(staged_out.split('\n')) if staged_out else 0
    modified = len(modified_out.split('\n')) if modified_out else 0
    git_status = ''
    if staged:
        git_status += f" {GIT_GREEN}+{staged}{RESET}"
    if modified:
        git_status += f" {GIT_YELLOW}~{modified}{RESET}"
except Exception:
    branch = '?'
    git_status = ''

print(f"\U0001f916 {model} | \U0001f4c1 {repo} | \U0001f33f {branch}{git_status}")

# --- Line 2: Color-coded progress bar ---
ctx = data.get('context_window', {})
pct = ctx.get('used_percentage', 0) or 0
pct = int(pct)
total = ctx.get('context_window_size', 200000) or 200000

# Calculate token counts for display
usage = ctx.get('current_usage') or {}
input_tok = usage.get('input_tokens', 0) or 0
cache_create = usage.get('cache_creation_input_tokens', 0) or 0
cache_read = usage.get('cache_read_input_tokens', 0) or 0
used_tokens = input_tok + cache_create + cache_read

# Use explicit RGB colors to avoid terminal theme interference
GREEN = '\033[38;2;80;200;80m'
YELLOW = '\033[38;2;230;220;40m'
ORANGE = '\033[38;2;230;160;40m'
RED = '\033[38;2;220;60;60m'
FREE_GRAY = '\033[38;2;100;100;100m'
AUTOCOMPACT = '\033[38;2;120;70;140m\033[48;2;45;25;55m'

BAR_WIDTH = 40
AUTOCOMPACT_PCT = 16.5

# How many bar chars for each zone
used_chars = round(pct * BAR_WIDTH / 100)
autocompact_chars = round(AUTOCOMPACT_PCT * BAR_WIDTH / 100)
free_chars = BAR_WIDTH - used_chars - autocompact_chars
if free_chars < 0:
    # If usage exceeds the free zone, eat into autocompact visually
    autocompact_chars = max(0, BAR_WIDTH - used_chars)
    free_chars = 0

# Build the used portion with color transitions
bar = ''
for i in range(used_chars):
    pos_pct = (i / BAR_WIDTH) * 100
    if pos_pct < 25:
        bar += f"{GREEN}\u2588"
    elif pos_pct < 50:
        bar += f"{YELLOW}\u2588"
    elif pos_pct < 70:
        bar += f"{ORANGE}\u2588"
    else:
        bar += f"{RED}\u2588"

# Free space
bar += f"{FREE_GRAY}" + '\u2591' * free_chars

# Autocompact buffer - uses background color to make it visually distinct
bar += f"{AUTOCOMPACT}" + '\u2592' * autocompact_chars

bar += RESET

# Format token counts (e.g. 36k, 200k)
def fmt_k(n):
    if n >= 1000:
        return f"{n / 1000:.0f}k"
    return str(n)

warn = ''
if pct >= 70:
    warn = f" {RED}\u26a0\ufe0f  CRITICAL{RESET}"
elif pct >= 50:
    warn = f" {ORANGE}\u26a0\ufe0f  HIGH{RESET}"

BORDER = '\033[38;2;80;80;80m'
cost_str = f"\U0001f4b0 ${cost:.2f}"
token_info = f"{fmt_k(used_tokens)} / {fmt_k(total)} ({pct}%){warn} | {cost_str}"
print(f"{BORDER}\u256d{'─' * BAR_WIDTH}\u256e{RESET}")
print(f"{BORDER}\u2502{RESET}{bar}{BORDER}\u2502{RESET}  {token_info}")
print(f"{BORDER}\u2570{'─' * BAR_WIDTH}\u256f{RESET}")
print(f"  {GREEN}\u25cf{RESET} 0-25%  {YELLOW}\u25cf{RESET} 25-50%  {ORANGE}\u25cf{RESET} 50-70%  {RED}\u25cf{RESET} 70-100%  {FREE_GRAY}\u25cf{RESET} Free  {AUTOCOMPACT}\u25cf{RESET} Autocompact")
