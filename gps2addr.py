#!/usr/bin/env python3
"""
gps2addr — Convert GPS coordinates (DMS or decimal) to a human-readable address.

Usage:
  python gps2addr.py "26 deg 12' 14.76\", 28 deg 2' 50.28\""
  python gps2addr.py "48 deg 51' 30\" N, 2 deg 17' 40\" E"
  python gps2addr.py --lat 26.204100 --lon 28.047300
  python gps2addr.py --lat 26.204100 --lon 28.047300 --lat-ref S --lon-ref E
  exiftool -p "$GPSLatitude, $GPSLongitude" photo.jpg | python gps2addr.py
"""

import sys
import re
import argparse
import urllib.request
import urllib.parse
import json
import concurrent.futures


# ══════════════════════════════════════════════════════════════════════════════
#  ANSI COLOR PALETTE
# ══════════════════════════════════════════════════════════════════════════════

class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    WHITE   = "\033[97m"
    CYAN    = "\033[96m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    RED     = "\033[91m"
    MAGENTA = "\033[95m"
    BLUE    = "\033[94m"
    GRAY    = "\033[90m"

    @classmethod
    def disable(cls):
        for attr in list(vars(cls)):
            if not attr.startswith("_") and attr != "disable":
                setattr(cls, attr, "")


# ══════════════════════════════════════════════════════════════════════════════
#  BANNER
# ══════════════════════════════════════════════════════════════════════════════

def print_banner():
    print(f"""
{C.CYAN}{C.BOLD}  ██████╗ ██████╗ ███████╗██████╗  █████╗ ██████╗ ██████╗
 ██╔════╝ ██╔══██╗██╔════╝╚════██╗██╔══██╗██╔══██╗██╔══██╗
 ██║  ███╗██████╔╝███████╗ █████╔╝███████║██║  ██║██║  ██║
 ██║   ██║██╔═══╝ ╚════██║██╔═══╝ ██╔══██║██║  ██║██║  ██║
 ╚██████╔╝██║     ███████║███████╗██║  ██║██████╔╝██████╔╝
  ╚═════╝ ╚═╝     ╚══════╝╚══════╝╚═╝  ╚═╝╚═════╝ ╚═════╝ {C.RESET}
{C.GRAY}  GPS Coordinates → Human Address  ·  Powered by OpenStreetMap / Nominatim{C.RESET}
""")

SEP  = f"{C.GRAY}  {'─' * 62}{C.RESET}"
SEP2 = f"{C.GRAY}  {'═' * 62}{C.RESET}"


# ══════════════════════════════════════════════════════════════════════════════
#  DMS PARSING
# ══════════════════════════════════════════════════════════════════════════════

DMS_RE = re.compile(
    r"(?P<deg>-?\d+(?:\.\d+)?)\s*deg\s*"
    r"(?P<min>\d+(?:\.\d+)?)['′]\s*"
    r'(?P<sec>\d+(?:\.\d+)?)["\u2033]?\s*'
    r"(?P<hemi>[NSEWnsew])?",
)


def dms_to_decimal(deg, min_, sec, hemi=""):
    v = float(deg) + float(min_) / 60 + float(sec) / 3600
    if hemi.upper() in ("S", "W"):
        v = -v
    return round(v, 8)


def parse_dms(raw: str):
    matches = DMS_RE.findall(raw)
    if len(matches) < 2:
        raise ValueError(
            f"Could not find two DMS coordinates in: {raw!r}\n"
            "Expected: 26 deg 12' 14.76\", 28 deg 2' 50.28\""
        )
    results, refs = [], []
    for deg, min_, sec, hemi in matches:
        results.append(dms_to_decimal(deg, min_, sec, hemi))
        refs.append(hemi.upper())
    lat, lon = results[0], results[1]
    if not (-90 <= lat <= 90):
        raise ValueError(f"Invalid latitude value: {lat}")
    if not (-180 <= lon <= 180):
        raise ValueError(f"Invalid longitude value: {lon}")
    return lat, lon, refs[0] in ("N","S"), refs[1] in ("E","W")


# ══════════════════════════════════════════════════════════════════════════════
#  REVERSE GEOCODING
# ══════════════════════════════════════════════════════════════════════════════

NOMINATIM = "https://nominatim.openstreetmap.org/reverse"
UA        = "gps2addr-cli/2.0 (personal script)"


def geocode(lat, lon, lang="en"):
    qs = urllib.parse.urlencode(
        {"lat": lat, "lon": lon, "format": "jsonv2",
         "addressdetails": 1, "accept-language": lang, "zoom": 18}
    )
    req = urllib.request.Request(f"{NOMINATIM}?{qs}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode())


def extract(data):
    a = data.get("address", {})
    num  = a.get("house_number", "")
    road = a.get("road") or a.get("pedestrian") or a.get("footway") or a.get("path") or ""
    return {
        "street":        f"{num} {road}".strip() if num else road,
        "neighbourhood": a.get("neighbourhood") or a.get("suburb") or a.get("quarter") or "",
        "postcode":      a.get("postcode", ""),
        "city":          a.get("city") or a.get("town") or a.get("municipality") or a.get("village") or "",
        "region":        a.get("state") or a.get("state_district") or a.get("county") or "",
        "country":       a.get("country", ""),
        "cc":            a.get("country_code", "").upper(),
        "display":       data.get("display_name", ""),
        "type":          (data.get("type") or data.get("category") or "").replace("_", " ").title(),
        "found":         bool(data.get("display_name")),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  DISPLAY
# ══════════════════════════════════════════════════════════════════════════════

def _row(label, value, color=C.WHITE):
    if not value:
        return
    print(f"  {C.GRAY}{label:<16}{C.RESET}{color}{value}{C.RESET}")


def print_result(info):
    if not info["found"]:
        print(f"  {C.DIM}✘  No address — likely ocean or unmapped territory.{C.RESET}")
        return
    _row("Type",          info["type"],  C.CYAN)
    _row("Street",        info["street"])
    _row("Neighbourhood", info["neighbourhood"])
    city_str = f"{info['postcode']} {info['city']}".strip()
    _row("City",          city_str)
    _row("Region",        info["region"])
    country_str = f"{info['country']} ({info['cc']})" if info["cc"] else info["country"]
    _row("Country",       country_str,  C.GREEN)
    if info["display"]:
        print()
        parts = info["display"].split(", ")
        buf, first = [], True
        for p in parts:
            candidate = ", ".join(buf + [p])
            if len(candidate) > 56 and buf:
                arrow = "→ " if first else "  "
                print(f"  {C.DIM}{arrow}{', '.join(buf)},{C.RESET}")
                buf, first = [p], False
            else:
                buf.append(p)
        if buf:
            arrow = "→ " if first else "  "
            print(f"  {C.DIM}{arrow}{', '.join(buf)}{C.RESET}")


QUADS = {
    "NE": ("North", "East",  +1, +1, C.CYAN),
    "NW": ("North", "West",  +1, -1, C.BLUE),
    "SE": ("South", "East",  -1, +1, C.YELLOW),
    "SW": ("South", "West",  -1, -1, C.MAGENTA),
}


def print_ambiguous(abs_lat, abs_lon, lang):
    print(f"\n{C.YELLOW}{C.BOLD}  ⚠   AMBIGUOUS COORDINATES — N/S and E/W references are missing{C.RESET}")
    print(f"{C.YELLOW}  The EXIF metadata does not specify hemisphere (North/South, East/West).{C.RESET}")
    print(f"{C.YELLOW}  All four possible locations are shown below.{C.RESET}")
    print(f"{C.YELLOW}  Use your photo's context (landscape, language, climate) to identify{C.RESET}")
    print(f"{C.YELLOW}  the correct one, then re-run with --lat-ref and --lon-ref.{C.RESET}")
    print()
    print(f"  {C.GRAY}Absolute coordinates parsed: {abs_lat}°  ·  {abs_lon}°{C.RESET}")
    print(SEP2)

    def fetch(key):
        ns, ew, slat, slon, _ = QUADS[key]
        lt, ln = abs_lat * slat, abs_lon * slon
        try:
            info = extract(geocode(lt, ln, lang))
        except Exception as e:
            info = {"found": False, "error": str(e)}
        return key, lt, ln, info

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        for key, lt, ln, info in ex.map(lambda k: fetch(k), QUADS):
            results[key] = (lt, ln, info)

    for key in ["NE", "NW", "SE", "SW"]:
        lt, ln, info = results[key]
        ns, ew, _, _, color = QUADS[key]
        mark = f"{C.GREEN}✔{C.RESET}" if info["found"] else f"{C.RED}✘{C.RESET}"
        print()
        print(
            f"  {color}{C.BOLD}┌─[ {key} ]  {ns} / {ew} {C.RESET}"
            f"  {mark}  "
            f"{C.GRAY}{lt:+.6f}°,  {ln:+.6f}°{C.RESET}"
        )
        print(f"  {C.GRAY}│{C.RESET}")
        # indent result lines under the box
        old_print = __builtins__.__dict__.get("print") if hasattr(__builtins__, "__dict__") else None

        # Capture output with a simple prefix trick
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            print_result(info)
        for line in buf.getvalue().splitlines():
            print(f"  {C.GRAY}│{C.RESET}{line}")

        print(f"  {color}└{'─' * 58}{C.RESET}")

    print()
    print(f"  {C.DIM}Tip: re-run with {C.WHITE}--lat-ref N|S  --lon-ref E|W{C.RESET}{C.DIM} to lock in a hemisphere.{C.RESET}")
    print()


def print_single(lat, lon, lang):
    print(f"\n{SEP2}")
    print(f"  {C.GRAY}Coordinates   {C.WHITE}{C.BOLD}{lat:+.6f}°   {lon:+.6f}°{C.RESET}")
    print(f"  {C.GRAY}Querying Nominatim…{C.RESET}")
    print(SEP)
    try:
        info = extract(geocode(lat, lon, lang))
    except Exception as e:
        print(f"\n  {C.RED}Network error: {e}{C.RESET}\n")
        sys.exit(2)
    print()
    if info["found"]:
        print(f"  {C.GREEN}{C.BOLD}✔  Address found{C.RESET}\n")
    else:
        print(f"  {C.RED}✘  No address found for these coordinates.{C.RESET}\n")
    print_result(info)
    print()
    print(SEP2)
    print()


# ══════════════════════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════════════════════

def build_parser():
    p = argparse.ArgumentParser(
        prog="gps2addr",
        description="Convert GPS DMS coordinates to a postal address.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python gps2addr.py "26 deg 12' 14.76\\", 28 deg 2' 50.28\\""
  python gps2addr.py "48 deg 51' 30\\" N, 2 deg 17' 40\\" E"
  python gps2addr.py --lat 26.2041 --lon 28.0473 --lat-ref S --lon-ref E
  exiftool -p "$GPSLatitude, $GPSLongitude" photo.jpg | python gps2addr.py
        """,
    )
    p.add_argument("coords",    nargs="?", help="DMS coordinate string")
    p.add_argument("--lat",     type=float)
    p.add_argument("--lon",     type=float)
    p.add_argument("--lat-ref", choices=["N","S","n","s"], help="Force N or S hemisphere")
    p.add_argument("--lon-ref", choices=["E","W","e","w"], help="Force E or W hemisphere")
    p.add_argument("--lang",    default="en", help="Language for results (default: en)")
    p.add_argument("--json",    dest="as_json", action="store_true", help="Print raw JSON")
    p.add_argument("--no-color", action="store_true", help="Disable colors")
    return p


def main():
    parser = build_parser()
    args   = parser.parse_args()

    if args.no_color or not sys.stdout.isatty():
        C.disable()

    print_banner()

    lat_has_ref = lon_has_ref = False

    try:
        if args.lat is not None and args.lon is not None:
            lat, lon = args.lat, args.lon
            lat_has_ref = args.lat_ref is not None
            lon_has_ref = args.lon_ref is not None
        else:
            raw = args.coords
            if raw is None:
                if not sys.stdin.isatty():
                    raw = sys.stdin.read().strip()
                else:
                    parser.print_help()
                    sys.exit(1)
            lat, lon, lat_has_ref, lon_has_ref = parse_dms(raw)
    except ValueError as e:
        print(f"  {C.RED}[ERROR]{C.RESET} {e}\n")
        sys.exit(1)

    # Apply explicit hemisphere flags
    if args.lat_ref:
        lat = -abs(lat) if args.lat_ref.upper() == "S" else +abs(lat)
        lat_has_ref = True
    if args.lon_ref:
        lon = -abs(lon) if args.lon_ref.upper() == "W" else +abs(lon)
        lon_has_ref = True

    ambiguous = not lat_has_ref or not lon_has_ref

    if ambiguous:
        print_ambiguous(abs(lat), abs(lon), args.lang)
        return

    if args.as_json:
        print(json.dumps(geocode(lat, lon, args.lang), ensure_ascii=False, indent=2))
        return

    print_single(lat, lon, args.lang)


if __name__ == "__main__":
    main()
