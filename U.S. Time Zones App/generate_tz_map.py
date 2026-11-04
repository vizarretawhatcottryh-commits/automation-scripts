import sys
import subprocess

# ------------------------------------------------------------------
# METHOD 1: AUTOMATIC SELF-UPDATING TZDATA ROUTINE
# ------------------------------------------------------------------
def auto_update_tzdata():
    """
    Silently checks PyPI and updates the Python tzdata package 
    to the latest official IANA release at startup.
    Falls back gracefully if offline.
    """
    try:
        print("Checking for official IANA time zone database updates (tzdata)...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", "--quiet", "tzdata"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("Time zone database is up to date!")
    except Exception as e:
        print(f"Skipped auto-update (using installed database version): {e}")

# Run auto-update before loading zoneinfo dependencies
auto_update_tzdata()

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime, timezone
import zoneinfo
import urllib.request
import xml.etree.ElementTree as ET
import textwrap

# ------------------------------------------------------------------
# 1. NIST TIME.GOV ATOMIC SYNC FUNCTION
# ------------------------------------------------------------------
def get_nist_metadata():
    """
    Fetches official atomic time metadata from nist.time.gov.
    Returns a dictionary with NIST server timestamp and sync status.
    Falls back gracefully to local system clock if offline.
    """
    url = "https://nist.time.gov/actualtime.cgi?lz=1"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read().decode('utf-8')
            root = ET.fromstring(xml_data)
            
            time_microseconds = int(root.attrib.get('time', 0))
            is_dst_active = root.attrib.get('dst', '0') == '1'
            
            utc_datetime = datetime.fromtimestamp(time_microseconds / 1000000.0, tz=timezone.utc)
            
            return {
                'status': 'Online (NIST Atomic Sync)',
                'datetime': utc_datetime,
                'dst_flag': is_dst_active
            }
            
    except Exception:
        now_utc = datetime.now(timezone.utc)
        return {
            'status': 'Offline (Local Clock Fallback)',
            'datetime': now_utc,
            'dst_flag': None
        }

# ------------------------------------------------------------------
# 2. DYNAMIC TIME ZONE CALCULATOR FUNCTION
# ------------------------------------------------------------------
def get_live_tz_info(iana_tz, ref_datetime=None):
    """Calculates active timezone abbreviation & UTC offset dynamically."""
    if ref_datetime is None:
        ref_datetime = datetime.now(timezone.utc)
    try:
        local_dt = ref_datetime.astimezone(zoneinfo.ZoneInfo(iana_tz))
        tz_abbr = local_dt.strftime('%Z')
        raw_offset = local_dt.strftime('%z')
        hours = int(raw_offset[:3])
        sign = "+" if hours > 0 else ""
        utc_offset = f"UTC{sign}{hours}" if hours != 0 else "UTC+0"
        return tz_abbr, utc_offset
    except Exception:
        return "N/A", "N/A"

def check_if_observes_dst(iana_tz, current_year):
    """
    AUTOMATIC DETECTOR: Checks if a location observes DST in a given year.
    Compares winter (Jan 15) and summer (Jul 15) offsets. 
    If offsets match, DST is NOT observed.
    """
    try:
        jan_dt = datetime(current_year, 1, 15, tzinfo=timezone.utc).astimezone(zoneinfo.ZoneInfo(iana_tz))
        jul_dt = datetime(current_year, 7, 15, tzinfo=timezone.utc).astimezone(zoneinfo.ZoneInfo(iana_tz))
        return jan_dt.utcoffset() != jul_dt.utcoffset()
    except Exception:
        return False

# ------------------------------------------------------------------
# 3. GLOBAL CONFIGURATION & PALETTE
# ------------------------------------------------------------------
TZ_COLORS = {
    'SST': '#4B0082',    # Indigo
    'HST': '#8A2BE2',    # Violet
    'AKST': '#3CB371',   # SeaGreen
    'PST': '#4682B4',    # SteelBlue
    'MST': '#20B2AA',    # LightSeaGreen
    'CST': '#F4A460',    # SandyBrown
    'EST': '#FFD700',    # Gold
    'AST': '#FF7F50',    # Coral
    'ChST': '#C71585',   # MediumVioletRed
}

# Sync with NIST atomic clock
nist_data = get_nist_metadata()
ref_datetime = nist_data['datetime']
current_year = ref_datetime.year
today_str = ref_datetime.strftime("%B %d, %Y (%H:%M UTC)")
sync_status = nist_data['status']
dst_2026_note = "2026 DST Schedule: March 8, 2026 (Clocks Forward 1 Hr @ 2:00 AM)  |  November 1, 2026 (Clocks Back 1 Hr @ 2:00 AM)"

# ------------------------------------------------------------------
# 4. COMPREHENSIVE GRANULAR LOCATIONS & SPLIT-ZONE DATABASE
# ------------------------------------------------------------------
US_GRANULAR_DATABASE = [
    # Split States & Cities
    {"location": "Panama City & Pensacola, FL", "state": "FL", "iana_tz": "America/Chicago", "details": "Florida Panhandle (West of Apalachicola River)"},
    {"location": "Miami, Orlando & Tampa, FL", "state": "FL", "iana_tz": "America/New_York", "details": "Peninsular Florida"},
    {"location": "Gary & Evansville, IN", "state": "IN", "iana_tz": "America/Chicago", "details": "12 Split Counties (NW & SW)"},
    {"location": "Indianapolis, IN", "state": "IN", "iana_tz": "America/Indiana/Indianapolis", "details": "Most of Indiana"},
    {"location": "Bowling Green & Paducah, KY", "state": "KY", "iana_tz": "America/Chicago", "details": "Western Kentucky"},
    {"location": "Louisville & Lexington, KY", "state": "KY", "iana_tz": "America/New_York", "details": "Eastern Kentucky"},
    {"location": "Iron Mountain & Escanaba, MI", "state": "MI", "iana_tz": "America/Menominee", "details": "4 Upper Peninsula Counties bordering WI"},
    {"location": "Detroit & Grand Rapids, MI", "state": "MI", "iana_tz": "America/Detroit", "details": "Main Michigan Peninsula"},
    {"location": "Nashville & Memphis, TN", "state": "TN", "iana_tz": "America/Chicago", "details": "Middle & West Tennessee"},
    {"location": "Knoxville & Chattanooga, TN", "state": "TN", "iana_tz": "America/New_York", "details": "East Tennessee"},
    {"location": "Goodland, KS (Sherman Co.)", "state": "KS", "iana_tz": "America/Denver", "details": "4 Far-Western Kansas Counties"},
    {"location": "Wichita & Topeka, KS", "state": "KS", "iana_tz": "America/Chicago", "details": "Most of Kansas"},
    {"location": "Scottsbluff, NE", "state": "NE", "iana_tz": "America/Denver", "details": "Nebraska Panhandle (Western 1/3)"},
    {"location": "Omaha & Lincoln, NE", "state": "NE", "iana_tz": "America/Chicago", "details": "Eastern 2/3 of Nebraska"},
    {"location": "Dickinson, ND", "state": "ND", "iana_tz": "America/North_Dakota/Center", "details": "Southwestern North Dakota"},
    {"location": "Fargo & Bismarck, ND", "state": "ND", "iana_tz": "America/Chicago", "details": "Most of North Dakota"},
    {"location": "Rapid City, SD", "state": "SD", "iana_tz": "America/Denver", "details": "Western South Dakota (West of Missouri River)"},
    {"location": "Sioux Falls, SD", "state": "SD", "iana_tz": "America/Chicago", "details": "Eastern South Dakota"},
    {"location": "El Paso, TX", "state": "TX", "iana_tz": "America/Denver", "details": "El Paso & Hudspeth Counties"},
    {"location": "Houston, Dallas & Austin, TX", "state": "TX", "iana_tz": "America/Chicago", "details": "Most of Texas"},
    {"location": "Coeur d'Alene, ID", "state": "ID", "iana_tz": "America/Los_Angeles", "details": "Northern Idaho Panhandle (North of Salmon River)"},
    {"location": "Boise, ID", "state": "ID", "iana_tz": "America/Boise", "details": "Southern & Central Idaho"},
    {"location": "Ontario, OR (Malheur Co.)", "state": "OR", "iana_tz": "America/Boise", "details": "Northern 80% of Malheur County"},
    {"location": "Portland & Eugene, OR", "state": "OR", "iana_tz": "America/Los_Angeles", "details": "Most of Oregon"},
    {"location": "West Wendover, NV", "state": "NV", "iana_tz": "America/Denver", "details": "Observes Mountain Time legally"},
    {"location": "Las Vegas & Reno, NV", "state": "NV", "iana_tz": "America/Los_Angeles", "details": "Most of Nevada"},

    # Special Reservation & Island Splits
    {"location": "Phoenix & Tucson, AZ", "state": "AZ", "iana_tz": "America/Phoenix", "details": "Arizona stays on MST year-round (No DST)"},
    {"location": "Window Rock, AZ (Navajo Nation)", "state": "AZ", "iana_tz": "America/Denver", "details": "Navajo Nation DOES observe DST (MDT in summer)"},
    {"location": "Anchorage, AK", "state": "AK", "iana_tz": "America/Anchorage", "details": "Most of Alaska"},
    {"location": "Adak, AK (Aleutian Islands)", "state": "AK", "iana_tz": "America/Adak", "details": "Aleutian Islands West of 169.5° W (Hawaii-Aleutian Time)"},

    # Territories
    {"location": "Pago Pago, American Samoa", "state": "AS", "iana_tz": "Pacific/Pago_Pago", "details": "Samoa Standard Time (SST, UTC-11, No DST)"},
    {"location": "Hagåtña, Guam", "state": "GU", "iana_tz": "Pacific/Guam", "details": "Chamorro Standard Time (ChST, UTC+10, No DST)"},
    {"location": "Saipan, Northern Mariana Islands", "state": "MP", "iana_tz": "Pacific/Saipan", "details": "Chamorro Standard Time (ChST, UTC+10, No DST)"},
    {"location": "San Juan, Puerto Rico", "state": "PR", "iana_tz": "America/Puerto_Rico", "details": "Atlantic Standard Time (AST, UTC-4, No DST)"},
    {"location": "Charlotte Amalie, U.S. Virgin Islands", "state": "VI", "iana_tz": "America/St_Thomas", "details": "Atlantic Standard Time (AST, UTC-4, No DST)"}
]

# AUTOMATIC SPLIT-STATE DETECTOR
state_offsets = {}
for entry in US_GRANULAR_DATABASE:
    st = entry["state"]
    _, offset = get_live_tz_info(entry["iana_tz"], ref_datetime)
    state_offsets.setdefault(st, set()).add(offset)

auto_split_states = {st for st, offsets in state_offsets.items() if len(offsets) > 1}

# ------------------------------------------------------------------
# 5. STATE TILE RENDERING FUNCTION WITH INTROSPECTION
# ------------------------------------------------------------------
def render_state_tiles(ax, states_data):
    for abbr, x, y, iana_tz, color_key in states_data:
        live_abbr, live_offset = get_live_tz_info(iana_tz, ref_datetime)
        
        observes_dst = check_if_observes_dst(iana_tz, current_year)
        is_no_dst = not observes_dst
        is_split = abbr in auto_split_states
        
        bg_color = TZ_COLORS[color_key]
        edge_color = "#D9534F" if is_no_dst else ("#FF9800" if is_split else "#1F497D")
        
        box = mpatches.FancyBboxPatch((x, y), 12.5, 12.5, boxstyle="round,pad=0.2", 
                                      ec=edge_color, fc=bg_color, lw=3.0 if (is_no_dst or is_split) else 1.8)
        ax.add_patch(box)
        
        label_abbr = f"{abbr}*" if is_split else abbr
        ax.text(x + 6.25, y + 8.4, label_abbr, ha='center', va='center', fontsize=30, fontweight='bold', color='black')
        ax.text(x + 6.25, y + 4.6, f"{live_abbr}\n({live_offset})", ha='center', va='center', fontsize=20, fontweight='bold', color='black')
        
        if is_no_dst:
            ax.text(x + 6.25, y + 1.5, "NO DST", ha='center', va='center', fontsize=12, fontweight='bold', 
                     color='red', bbox=dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor='none'))

def draw_inset_master(ax, x, y, title, iana_tz, color_key, is_no_dst=True):
    live_abbr, live_offset = get_live_tz_info(iana_tz, ref_datetime)
    bg_color = TZ_COLORS[color_key]
    edge_color = "red" if is_no_dst else "#1F497D"
    
    box = mpatches.FancyBboxPatch((x, y), 26, 16, boxstyle="round,pad=0.4", 
                                  ec=edge_color, fc=bg_color, lw=2.5)
    ax.add_patch(box)
    ax.text(x + 13, y + 12.8, title, ha='center', va='center', fontsize=18, fontweight='bold', color='black')
    ax.text(x + 13, y + 8.0, f"{live_abbr} ({live_offset})", ha='center', va='center', fontsize=22, fontweight='bold', color='black')
    
    dst_txt = "NO DST" if is_no_dst else "Observes DST"
    badge_bg = "white" if is_no_dst else "#2E7D32"
    badge_fg = "red" if is_no_dst else "white"
    ax.text(x + 13, y + 3.2, dst_txt, ha='center', va='center', fontsize=13, fontweight='bold',
            color=badge_fg, bbox=dict(boxstyle="round,pad=0.3", facecolor=badge_bg, edgecolor='none'))

states_map_grid = [
    ("WA", 36, 85, "America/Los_Angeles", "PST"), ("ID", 50, 85, "America/Boise", "MST"),
    ("MT", 64, 85, "America/Denver", "MST"), ("ND", 78, 85, "America/North_Dakota/Center", "CST"),
    ("MN", 92, 85, "America/Chicago", "CST"), ("WI", 106, 85, "America/Chicago", "CST"),
    ("MI", 126, 85, "America/Detroit", "EST"), ("NY", 154, 85, "America/New_York", "EST"),
    ("VT", 168, 96, "America/New_York", "EST"), ("NH", 182, 96, "America/New_York", "EST"),
    ("ME", 196, 96, "America/New_York", "EST"), ("OR", 36, 68, "America/Los_Angeles", "PST"),
    ("NV", 50, 68, "America/Los_Angeles", "PST"), ("WY", 64, 68, "America/Denver", "MST"),
    ("SD", 78, 68, "America/Chicago", "CST"), ("IA", 92, 68, "America/Chicago", "CST"),
    ("IL", 106, 68, "America/Chicago", "CST"), ("IN", 120, 68, "America/Indiana/Indianapolis", "EST"),
    ("OH", 134, 68, "America/New_York", "EST"), ("PA", 151, 68, "America/New_York", "EST"),
    ("NJ", 165, 68, "America/New_York", "EST"), ("MA", 179, 80, "America/New_York", "EST"),
    ("CT", 179, 68, "America/New_York", "EST"), ("RI", 193, 74, "America/New_York", "EST"),
    ("CA", 30, 51, "America/Los_Angeles", "PST"), ("UT", 50, 51, "America/Denver", "MST"),
    ("CO", 64, 51, "America/Denver", "MST"), ("NE", 78, 51, "America/Chicago", "CST"),
    ("MO", 92, 51, "America/Chicago", "CST"), ("KY", 112, 51, "America/New_York", "EST"),
    ("WV", 129, 51, "America/New_York", "EST"), ("VA", 146, 51, "America/New_York", "EST"),
    ("MD", 160, 51, "America/New_York", "EST"), ("DE", 174, 51, "America/New_York", "EST"),
    ("AZ", 46, 34, "America/Phoenix", "MST"), ("NM", 60, 34, "America/Denver", "MST"),
    ("KS", 74, 34, "America/Chicago", "CST"), ("OK", 88, 34, "America/Chicago", "CST"),
    ("AR", 102, 34, "America/Chicago", "CST"), ("TN", 116, 34, "America/Chicago", "CST"),
    ("NC", 144, 34, "America/New_York", "EST"), ("SC", 158, 34, "America/New_York", "EST"),
    ("AK", 30, 17, "America/Anchorage", "AKST"), ("HI", 46, 17, "Pacific/Honolulu", "HST"),
    ("TX", 74, 17, "America/Chicago", "CST"), ("LA", 98, 17, "America/Chicago", "CST"),
    ("MS", 112, 17, "America/Chicago", "CST"), ("AL", 126, 17, "America/Chicago", "CST"),
    ("GA", 140, 17, "America/New_York", "EST"), ("FL", 158, 17, "America/New_York", "EST")
]

# ==================================================================
# DOCUMENT 1: 50 U.S. STATES MAP ONLY
# ==================================================================
fig1, ax1 = plt.subplots(figsize=(32, 18))
ax1.axis('off'); ax1.set_xlim(10, 210); ax1.set_ylim(0, 110)

fig1.suptitle(f'Dynamic 50 U.S. States Time Zone Map (Live: {today_str})', 
              fontsize=36, fontweight='bold', y=0.96, color='#1F497D')
ax1.set_title(f'Live local abbreviations & UTC offsets across all 50 U.S. States  |  Source: {sync_status}\n{dst_2026_note}', 
              fontsize=16, fontstyle='italic', pad=15, color='#333333')

render_state_tiles(ax1, states_map_grid)

ax1.text(110, 4, "* Asterisk (*) indicates state has multiple internal time zones.\nArizona (except Navajo Nation) and Hawaii stay on Standard Time year-round.", 
         ha='center', fontsize=13, fontstyle='italic', color='#333333')

plt.savefig('Doc1_50_States_Time_Zone_Map.pdf', format='pdf', bbox_inches='tight')
plt.savefig('Doc1_50_States_Time_Zone_Map.png', dpi=300, bbox_inches='tight')
plt.close(fig1)

# ==================================================================
# DOCUMENT 2: 5 U.S. TERRITORIES ONLY
# ==================================================================
fig2, ax2 = plt.subplots(figsize=(24, 15))
ax2.axis('off'); ax2.set_xlim(0, 120); ax2.set_ylim(0, 95)

fig2.suptitle(f'Dynamic 5 U.S. Territories Time Zone Reference (Live: {today_str})', 
              fontsize=34, fontweight='bold', y=0.95, color='#1F497D')
ax2.set_title(f'Inhabited U.S. Territories Time Zone Offsets (Year-Round Standard Time)  |  Source: {sync_status}', 
              fontsize=16, fontstyle='italic', pad=15, color='#595959')

territories_data = [
    ("American Samoa", "AS", "Pacific/Pago_Pago", "SST", "South Pacific", 15, 62),
    ("Guam", "GU", "Pacific/Guam", "ChST", "North Pacific", 65, 62),
    ("Northern Mariana Islands", "MP", "Pacific/Saipan", "ChST", "North Pacific", 15, 33),
    ("Puerto Rico", "PR", "America/Puerto_Rico", "AST", "Caribbean", 65, 33),
    ("U.S. Virgin Islands", "VI", "America/St_Thomas", "AST", "Caribbean", 40, 4)
]

for title, abbr, iana_tz, color_key, region, x, y in territories_data:
    live_abbr, live_offset = get_live_tz_info(iana_tz, ref_datetime)
    bg_color = TZ_COLORS[color_key]
    
    box = mpatches.FancyBboxPatch((x, y), 38, 22, boxstyle="round,pad=0.5", ec="red", fc=bg_color, lw=3.0)
    ax2.add_patch(box)
    
    ax2.text(x + 19, y + 17.5, f"{title} ({abbr})", ha='center', va='center', fontsize=22, fontweight='bold', color='black')
    ax2.text(x + 19, y + 13.8, f"Region: {region}", ha='center', va='center', fontsize=16, fontstyle='italic', color='#333333')
    ax2.text(x + 19, y + 9.0, f"{live_abbr} ({live_offset})", ha='center', va='center', fontsize=26, fontweight='bold', color='black')
    ax2.text(x + 19, y + 3.8, "NO DST (Standard Time Year-Round)", ha='center', va='center', fontsize=14, fontweight='bold', color='red', bbox=dict(boxstyle="round,pad=0.3", facecolor='white', edgecolor='none'))

plt.savefig('Doc2_5_Territories_Time_Zone_Map.pdf', format='pdf', bbox_inches='tight')
plt.savefig('Doc2_5_Territories_Time_Zone_Map.png', dpi=300, bbox_inches='tight')
plt.close(fig2)

# ==================================================================
# DOCUMENT 3: COMBINED MASTER MAP (50 STATES + 5 TERRITORIES)
# ==================================================================
fig3, ax3 = plt.subplots(figsize=(34, 18))
ax3.axis('off'); ax3.set_xlim(0, 220); ax3.set_ylim(0, 110)

fig3.suptitle(f'Dynamic U.S. States & Territories Time Zone Map (Live: {today_str})', 
              fontsize=38, fontweight='bold', y=0.96, color='#1F497D')
ax3.set_title(f'Live local abbreviations & UTC offsets with uniform state tiles  |  Source: {sync_status}\n{dst_2026_note}', 
              fontsize=18, fontstyle='italic', pad=15, color='#333333')

render_state_tiles(ax3, states_map_grid)

draw_inset_master(ax3, 2, 88, "Guam", "Pacific/Guam", "ChST", is_no_dst=True)
draw_inset_master(ax3, 2, 68, "N. Mariana Islands", "Pacific/Saipan", "ChST", is_no_dst=True)
draw_inset_master(ax3, 2, 48, "American Samoa", "Pacific/Pago_Pago", "SST", is_no_dst=True)
draw_inset_master(ax3, 192, 48, "Puerto Rico", "America/Puerto_Rico", "AST", is_no_dst=True)
draw_inset_master(ax3, 192, 28, "U.S. Virgin Islands", "America/St_Thomas", "AST", is_no_dst=True)

ax3.text(110, 4, "* Asterisk (*) indicates state has multiple internal time zones.\nArizona (except Navajo Nation), Hawaii, and all 5 territories stay on Standard Time year-round.", 
         ha='center', fontsize=13, fontstyle='italic', color='#333333')

plt.savefig('Doc3_Combined_Master_Time_Zone_Map.pdf', format='pdf', bbox_inches='tight')
plt.savefig('Doc3_Combined_Master_Time_Zone_Map.png', dpi=300, bbox_inches='tight')
plt.close(fig3)

# ==================================================================
# DOCUMENT 4: GRANULAR LOCATIONS & SPLIT-ZONE REFERENCE TABLE
# (TIGHTENED VERTICAL SPACING - NO EXTRA SPACES)
# ==================================================================
fig4, ax4 = plt.subplots(figsize=(18, 22))
ax4.axis('off')

# Combined text block with tight line spacing (1.05) to collapse vertical gap
header_text = (
    "Official U.S. Granular Time Zone & Split-Region Reference Table\n"
    f"Source: {sync_status} on {today_str} | Calculated using IANA / Olson Database"
)

ax4.text(
    0.5, 0.985, header_text, 
    ha='center', va='top', transform=ax4.transAxes,
    linespacing=1.05,
    fontdict={'color': '#1F497D', 'size': 18, 'weight': 'bold'}
)

col_labels = ["Location / Region", "ST", "Active", "UTC", "Specific Geographic Details"]
table_data = []

# Process table data with text wrapping
for entry in US_GRANULAR_DATABASE:
    abbr, offset = get_live_tz_info(entry["iana_tz"], ref_datetime)
    wrapped_loc = textwrap.fill(entry["location"], width=32)
    wrapped_details = textwrap.fill(entry["details"], width=48)
    
    table_data.append([
        wrapped_loc,
        entry["state"],
        abbr,
        offset,
        wrapped_details
    ])

# Column width ratios
col_widths = [0.30, 0.05, 0.10, 0.10, 0.45]

# Table top boundary starts at 0.955 (immediately below the title block)
table = ax4.table(
    cellText=table_data, 
    colLabels=col_labels, 
    colWidths=col_widths,
    loc='upper center', 
    cellLoc='left',
    bbox=[0.02, 0.01, 0.96, 0.94]
)

table.auto_set_font_size(False)
table.set_fontsize(10.5)

# Styling header and alternating rows
for (row, col), cell in table.get_celld().items():
    if row == 0:
        cell.set_facecolor('#1F497D')
        cell.get_text().set_color('white')
        cell.get_text().set_weight('bold')
        cell.get_text().set_fontsize(11.5)
        cell.set_height(0.025)
    else:
        cell.get_text().set_color('black')
        if row % 2 == 0:
            cell.set_facecolor('#F4F6F9')
        else:
            cell.set_facecolor('white')

plt.savefig('Doc4_Granular_Time_Zone_Table.pdf', format='pdf', bbox_inches='tight')
plt.savefig('Doc4_Granular_Time_Zone_Table.png', dpi=300, bbox_inches='tight')
plt.close(fig4)

print("All 4 documents generated successfully!")