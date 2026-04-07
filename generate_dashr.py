#!/usr/bin/env python3
"""Generate synthetic Dashr timing gate CSV files from an athlete roster.

Produces CSV files that match the real Dashr export format (54 columns),
compatible with the AthleteMetrics Device Import parser.
"""
import argparse, csv, random, sys
from datetime import datetime, timedelta
from pathlib import Path

# ---- Dashr CSV header (exact 54-column order) ----
DASHR_HEADER = [
    "Date","First Name","Middle Name","Last Name","Type","Lane ID","Units",
    "Start Distance","Split Time 1","Split Distance 1","Split Speed 1",
    "Start Time 2","Split Distance 2","Split Speed 2",
    "Start Time 3","Split Distance 3","Split Speed 3",
    "Start Time 4","Split Distance 4","Split Speed 4",
    "Start Time 5","Split Distance 5","Split Speed 5",
    "Start Time 6","Split Distance 6","Split Speed 6",
    "Final Time","Final Distance","Final Speed",
    "Jump Distance","Reaction Time","Direction","Weight","Reps","1 RM",
    "Lap Time 1","Lap Time 2","Lap Time 3","Lap Time 4","Lap Time 5",
    "Lap Time 6","Lap Time 7","Lap Time 8","Lap Time 9",
    "RAST Time 1","RAST Time 2","RAST Time 3","RAST Time 4","RAST Time 5","RAST Time 6",
    "Average RSI","Max RSI","RSI",
    "Speed Ratio","Symmetry Score","MultiPlanar Plyometric Index","Custom Event Results",
]

# ---- Drill baselines (adult male varsity, in seconds) ----
DRILL_SPECS = {
    "dash": {
        "type": "Dash",
        "distances": {10: 1.65, 20: 2.95, 30: 4.20, 40: 4.80},
        "sd": 0.08,
        "split_distances": {10: [5], 20: [5, 10], 30: [5, 10, 20], 40: [5, 10, 20, 30]},
    },
    "flying": {
        "type": "Flying",
        "center": 1.25,
        "sd": 0.06,
        "final_distance": 10,
        "start_distance": 20,
    },
    "505": {
        "type": "505 Agility Test",
        "center": 2.50,
        "sd": 0.12,
        "directions": ["L", "R"],
    },
    "proagility": {
        "type": "Pro Agility",
        "center": 4.80,
        "sd": 0.15,
        "directions": ["L", "R"],
    },
}

# Gender adjustments (multiplier on time — >1.0 means slower)
GENDER_TIME_MULT = {"Male": 1.00, "Female": 1.08}

# Age bracket multipliers (inverse for time: younger = slower)
AGE_BRACKETS = {
    "middle_school": 1.25,   # ages <14, ~25% slower
    "young_hs": 1.14,        # ages 14-15
    "older_hs": 1.05,        # ages 16-17
    "college_plus": 1.00,    # ages 18+
}

PERFORMANCE_LEVELS = {
    "elite": 0.92,        # 8% faster than baseline
    "varsity": 1.00,
    "jv": 1.10,           # 10% slower
    "recreational": 1.25, # 25% slower
}


def parse_args():
    p = argparse.ArgumentParser(description="Generate Dashr-format CSV from a roster.")
    p.add_argument("--roster", required=True, help="Path to roster CSV (from generate_roster.py)")
    p.add_argument("--out", required=True, help="Output Dashr CSV path")
    p.add_argument("--dates", nargs="+", required=True, help="Session dates (YYYY-MM-DD)")
    p.add_argument("--drills", nargs="+", default=["dash", "flying", "505"],
                    choices=list(DRILL_SPECS.keys()),
                    help="Drill types to generate (default: dash flying 505)")
    p.add_argument("--trials", type=int, default=3, help="Attempts per athlete per drill (default: 3)")
    p.add_argument("--dash-distance", type=int, default=30, choices=[10, 20, 30, 40],
                    help="Final distance for dash drills in yards (default: 30)")
    p.add_argument("--performance-level", default="varsity",
                    choices=list(PERFORMANCE_LEVELS.keys()),
                    help="Performance level (default: varsity)")
    p.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    return p.parse_args()


def read_roster(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def get_age_bracket(age):
    if age is None or age == "":
        return "college_plus"
    try:
        age = int(float(age))
    except (ValueError, TypeError):
        return "college_plus"
    if age < 14:
        return "middle_school"
    elif age < 16:
        return "young_hs"
    elif age < 18:
        return "older_hs"
    return "college_plus"


def age_on(birth_date_str, on_date):
    try:
        bd = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
    except Exception:
        return None
    return on_date.year - bd.year - ((on_date.month, on_date.day) < (bd.month, bd.day))


def time_multiplier(gender, age, perf_level):
    """Combined multiplier for time-based drills (>1.0 = slower)."""
    g = GENDER_TIME_MULT.get(gender, 1.00)
    a = AGE_BRACKETS[get_age_bracket(age)]
    p = PERFORMANCE_LEVELS.get(perf_level, 1.00)
    return g * a * p


def fmt_time(t):
    """Format time to 6 decimal places like real Dashr output."""
    return f"{t:.6f}"


def fmt_dist(d):
    """Format distance to 6 decimal places."""
    return f"{d:.6f}"


def fmt_speed(distance_yd, time_s):
    """Compute speed in MPH and format as 'XX.XX (MPH)'."""
    if time_s <= 0:
        return ""
    # yards/s → mph: multiply by 3600/3/1760 = 0.681818...
    # Actually: 1 yard = 3 feet, 1 mile = 5280 feet, 1 hour = 3600s
    # speed_mph = (distance_yd * 3 / 5280) / (time_s / 3600)
    speed_mph = (distance_yd / time_s) * (3600.0 * 3.0 / 5280.0)
    return f"{speed_mph:.2f} (MPH)"


def gen_split_times(final_time, final_dist, split_distances):
    """Generate realistic cumulative split times using acceleration curve.

    Uses power law: time at distance d = (d/D)^0.85 * T
    This models the acceleration phase where early splits are slower per yard.
    """
    splits = []
    for sd in split_distances:
        ratio = sd / final_dist
        split_time = (ratio ** 0.85) * final_time
        # Add tiny jitter to each split
        split_time += random.gauss(0, 0.01)
        split_time = max(0.1, split_time)
        splits.append((sd, split_time))
    return splits


def empty_row():
    """Create a row dict with all 54 columns empty."""
    return {h: "" for h in DASHR_HEADER}


def gen_dash_row(athlete, date_str, final_dist, split_dists, base_time, sd, mult):
    """Generate a single Dash row with splits."""
    final_time = max(0.5, random.gauss(base_time * mult, sd * mult))
    splits = gen_split_times(final_time, final_dist, split_dists)

    row = empty_row()
    row["Date"] = date_str
    row["First Name"] = athlete.get("firstName", "").strip()
    row["Middle Name"] = ""
    row["Last Name"] = athlete.get("lastName", "").strip()
    row["Type"] = "Dash"
    row["Units"] = "Imperial"
    row["Final Time"] = fmt_time(final_time)
    row["Final Distance"] = fmt_dist(final_dist)
    row["Final Speed"] = fmt_speed(final_dist, final_time)

    # Fill split columns
    for i, (sd, st) in enumerate(splits):
        if i == 0:
            row["Split Time 1"] = fmt_time(st)
            row["Split Distance 1"] = fmt_dist(sd)
            row["Split Speed 1"] = fmt_speed(sd, st)
        else:
            n = i + 1
            row[f"Start Time {n}"] = fmt_time(st)
            row[f"Split Distance {n}"] = fmt_dist(sd)
            row[f"Split Speed {n}"] = fmt_speed(sd, st)

    return row


def gen_flying_row(athlete, date_str, base_time, sd, mult):
    """Generate a single Flying row."""
    final_time = max(0.5, random.gauss(base_time * mult, sd * mult))

    row = empty_row()
    row["Date"] = date_str
    row["First Name"] = athlete.get("firstName", "").strip()
    row["Middle Name"] = ""
    row["Last Name"] = athlete.get("lastName", "").strip()
    row["Type"] = "Flying"
    row["Units"] = "Imperial"
    row["Start Distance"] = fmt_dist(20.0)
    row["Final Time"] = fmt_time(final_time)
    row["Final Distance"] = fmt_dist(10.0)
    row["Final Speed"] = fmt_speed(10.0, final_time)

    return row


def gen_agility_row(athlete, date_str, drill_type, direction, base_time, sd, mult):
    """Generate a single agility test row (505 or Pro Agility)."""
    final_time = max(0.5, random.gauss(base_time * mult, sd * mult))

    row = empty_row()
    row["Date"] = date_str
    row["First Name"] = athlete.get("firstName", "").strip()
    row["Middle Name"] = ""
    row["Last Name"] = athlete.get("lastName", "").strip()
    row["Type"] = drill_type
    row["Units"] = "Imperial"
    row["Final Time"] = fmt_time(final_time)
    row["Direction"] = direction

    return row


def main():
    args = parse_args()
    random.seed(args.seed)

    roster = read_roster(args.roster)
    if not roster:
        print("No roster rows found.", file=sys.stderr)
        sys.exit(1)

    dates = [datetime.strptime(d, "%Y-%m-%d").date() for d in args.dates]
    perf_level = args.performance_level

    rows = []

    for session_date in sorted(dates):
        # Shuffle athlete order per session (like real testing days)
        session_roster = list(roster)
        random.shuffle(session_roster)

        for athlete in session_roster:
            gender = athlete.get("gender", "Male")
            birth_date = athlete.get("birthDate", "")
            age = age_on(birth_date, session_date)
            mult = time_multiplier(gender, age, perf_level)

            # Assign a random time-of-day for this athlete's block
            base_hour = random.randint(9, 15)
            base_minute = random.randint(0, 59)

            for drill_name in args.drills:
                spec = DRILL_SPECS[drill_name]

                for trial in range(args.trials):
                    # Increment timestamp by ~2 min per trial
                    trial_minute = base_minute + trial * 2
                    trial_hour = base_hour + trial_minute // 60
                    trial_minute = trial_minute % 60
                    trial_second = random.randint(0, 59)
                    timestamp = f"{session_date.strftime('%m/%d/%Y')} {trial_hour:02d}:{trial_minute:02d}:{trial_second:02d}"

                    if drill_name == "dash":
                        dist = args.dash_distance
                        base_time = spec["distances"][dist]
                        split_dists = spec["split_distances"][dist]
                        row = gen_dash_row(athlete, timestamp, dist, split_dists, base_time, spec["sd"], mult)
                        rows.append(row)

                    elif drill_name == "flying":
                        row = gen_flying_row(athlete, timestamp, spec["center"], spec["sd"], mult)
                        rows.append(row)

                    elif drill_name in ("505", "proagility"):
                        # Generate one row per direction per trial
                        for direction in spec["directions"]:
                            row = gen_agility_row(
                                athlete, timestamp, spec["type"], direction,
                                spec["center"], spec["sd"], mult,
                            )
                            rows.append(row)

                # Advance base time for next drill type
                base_minute += args.trials * 3

    # Write output
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=DASHR_HEADER)
        w.writeheader()
        for row in rows:
            w.writerow(row)

    print(f"Wrote {len(rows)} rows to {args.out}")
    print(f"Sessions: {', '.join(d.isoformat() for d in sorted(dates))}")
    print(f"Athletes: {len(roster)}")
    print(f"Drills: {', '.join(args.drills)}")


if __name__ == "__main__":
    main()
