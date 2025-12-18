#!/usr/bin/env python3
import argparse, csv, random, sys
from datetime import datetime, timedelta
from pathlib import Path

# ---- Config: sport-specific metric specs ----
# Center/SD are for adult male baseline; min/max expanded to accommodate all ages/genders
SPORT_METRICS = {
    "Soccer": {
        "FLY10_TIME": {"units": "s", "better": "lower", "center": 1.22, "sd": 0.06, "drift_per_day": -0.0006, "min": 1.00, "max": 1.70, "flyInDistance": 20},
        "VERTICAL_JUMP": {"units": "in", "better": "higher", "center": 23.5, "sd": 2.0, "drift_per_day": +0.008, "min": 12.0, "max": 32.0, "flyInDistance": ""},
        "AGILITY_505": {"units": "s", "better": "lower", "center": 2.55, "sd": 0.07, "drift_per_day": -0.0007, "min": 2.1, "max": 3.5, "flyInDistance": ""},
        "RSI": {"units": "", "better": "higher", "center": 2.4, "sd": 0.25, "drift_per_day": +0.0009, "min": 1.0, "max": 4.5, "flyInDistance": ""},
        "T_TEST": {"units": "s", "better": "lower", "center": 9.8, "sd": 0.4, "drift_per_day": -0.0010, "min": 7.5, "max": 13.5, "flyInDistance": ""},
        "HEIGHT": {"units": "in", "better": "higher", "center": 70, "sd": 3.0, "drift_per_day": 0.0, "min": 60, "max": 80, "flyInDistance": "", "static": True},
        "WEIGHT": {"units": "lbs", "better": "neutral", "center": 160, "sd": 15.0, "drift_per_day": 0.0, "min": 100, "max": 220, "flyInDistance": "", "static": True},
    },
    "Volleyball": {
        "VERTICAL_JUMP": {"units": "in", "better": "higher", "center": 24.0, "sd": 2.5, "drift_per_day": +0.008, "min": 12.0, "max": 36.0, "flyInDistance": ""},
        "APPROACH_JUMP": {"units": "in", "better": "higher", "center": 28.0, "sd": 3.0, "drift_per_day": +0.008, "min": 16.0, "max": 42.0, "flyInDistance": ""},
        "BLOCK_JUMP": {"units": "in", "better": "higher", "center": 24.0, "sd": 2.5, "drift_per_day": +0.008, "min": 12.0, "max": 36.0, "flyInDistance": ""},
        "T_TEST": {"units": "s", "better": "lower", "center": 9.8, "sd": 0.4, "drift_per_day": -0.0010, "min": 7.5, "max": 13.5, "flyInDistance": ""},
        "AGILITY_505": {"units": "s", "better": "lower", "center": 2.55, "sd": 0.07, "drift_per_day": -0.0007, "min": 2.1, "max": 3.5, "flyInDistance": ""},
        "RSI": {"units": "", "better": "higher", "center": 2.4, "sd": 0.25, "drift_per_day": +0.0009, "min": 1.0, "max": 4.5, "flyInDistance": ""},
        "WINGSPAN": {"units": "in", "better": "higher", "center": 72, "sd": 3.5, "drift_per_day": 0.0, "min": 58, "max": 86, "flyInDistance": "", "static": True},
        "STANDING_REACH": {"units": "in", "better": "higher", "center": 93, "sd": 4.0, "drift_per_day": 0.0, "min": 75, "max": 110, "flyInDistance": "", "static": True},
        "HEIGHT": {"units": "in", "better": "higher", "center": 72, "sd": 3.5, "drift_per_day": 0.0, "min": 60, "max": 84, "flyInDistance": "", "static": True},
        "WEIGHT": {"units": "lbs", "better": "neutral", "center": 165, "sd": 18.0, "drift_per_day": 0.0, "min": 100, "max": 240, "flyInDistance": "", "static": True},
        "DASH_10YD": {"units": "s", "better": "lower", "center": 1.7, "sd": 0.08, "drift_per_day": -0.0005, "min": 1.4, "max": 2.2, "flyInDistance": ""},
    },
}

SUPPORTED_SPORTS = list(SPORT_METRICS.keys())

# Age bracket multipliers (baseline = college_plus at 1.00)
AGE_BRACKETS = {
    "middle_school": 0.80,  # ages <14
    "young_hs": 0.88,       # ages 14-15
    "older_hs": 0.95,       # ages 16-17
    "college_plus": 1.00,   # ages 18+
}

# Age boundary constants for bracket determination
AGE_MIDDLE_SCHOOL_MAX = 14
AGE_YOUNG_HS_MAX = 16
AGE_OLDER_HS_MAX = 18
AGE_MIN_VALID = 0
AGE_MAX_VALID = 100

# Gender-specific adjustments per metric (multiplier applied to baseline)
# Based on typical performance differences between male/female athletes
GENDER_ADJUSTMENTS = {
    "FLY10_TIME": {"Male": 1.00, "Female": 1.08},      # Females ~8% slower (times are inverted)
    "VERTICAL_JUMP": {"Male": 1.00, "Female": 0.75},   # Females ~25% lower jump
    "AGILITY_505": {"Male": 1.00, "Female": 1.05},     # Females ~5% slower
    "RSI": {"Male": 1.00, "Female": 0.85},             # Females ~15% lower RSI
    "T_TEST": {"Male": 1.00, "Female": 1.08},          # Females ~8% slower
    "HEIGHT": {"Male": 1.00, "Female": 0.93},          # Females ~7% shorter
    "WEIGHT": {"Male": 1.00, "Female": 0.82},          # Females ~18% lighter
    "APPROACH_JUMP": {"Male": 1.00, "Female": 0.75},   # Females ~25% lower jump
    "BLOCK_JUMP": {"Male": 1.00, "Female": 0.75},      # Females ~25% lower jump
    "WINGSPAN": {"Male": 1.00, "Female": 0.93},        # Females ~7% shorter wingspan
    "STANDING_REACH": {"Male": 1.00, "Female": 0.93},  # Females ~7% shorter reach
    "DASH_10YD": {"Male": 1.00, "Female": 1.08},       # Females ~8% slower
}

# Performance level multipliers (applied to baseline after age/gender adjustments)
PERFORMANCE_LEVELS = {
    "elite": 1.15,        # Top-tier athletes, 15% above baseline
    "varsity": 1.00,      # Baseline performance level
    "jv": 0.90,           # Junior varsity, 10% below baseline
    "recreational": 0.75, # Casual/beginner level, 25% below baseline
}

def resolve_performance_multiplier(performance_level=None, performance_multiplier=None):
    """Resolve the performance multiplier from level or custom value."""
    if performance_multiplier is not None:
        return performance_multiplier
    elif performance_level is not None:
        return PERFORMANCE_LEVELS.get(performance_level, 1.0)
    else:
        return 1.0  # Default to varsity level (no adjustment)

def get_sport_metrics(sport):
    """Return metrics dict for sport or raise error if unsupported."""
    if sport not in SPORT_METRICS:
        raise ValueError(f"Unsupported sport: '{sport}'. Supported sports: {SUPPORTED_SPORTS}")
    return SPORT_METRICS[sport]

def parse_args():
    p = argparse.ArgumentParser(description="Generate sport-specific testing measurements from a roster.")
    p.add_argument("--roster", required=True, help="Path to roster CSV")
    p.add_argument("--out", required=True, help="Output measurements CSV")
    p.add_argument("--trials", type=int, default=3, help="Trials per metric per date (default 3)")
    p.add_argument("--dates", nargs="*", help="Test dates YYYY-MM-DD. If omitted, generates random dates.")
    p.add_argument("--num_random_dates", type=int, default=1, help="If no --dates, how many random dates to make")
    p.add_argument("--random_date_start", default="2025-01-01", help="Start of random date window YYYY-MM-DD")
    p.add_argument("--random_date_end", default="2025-12-31", help="End of random date window YYYY-MM-DD")
    p.add_argument("--performance_level", choices=["elite", "varsity", "jv", "recreational"], help="Predefined performance level")
    p.add_argument("--performance_multiplier", type=float, help="Custom performance multiplier (overrides --performance_level)")
    p.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    return p.parse_args()

def read_roster(path):
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        rows = [row for row in r]
    # Expected headers from your spec:
    # firstName,lastName,birthDate,birthYear,graduationYear,gender,emails,phoneNumbers,sports,height,weight,school,teamName
    return rows

def rand_dates(n, start_str, end_str):
    start = datetime.strptime(start_str, "%Y-%m-%d").date()
    end = datetime.strptime(end_str, "%Y-%m-%d").date()
    span = (end - start).days
    max_possible = span + 1  # inclusive range
    if n > max_possible:
        print(f"Warning: Requested {n} dates but only {max_possible} possible in range. Using {max_possible}.", file=sys.stderr)
        n = max_possible
    ds = set()
    while len(ds) < n:
        ds.add(start + timedelta(days=random.randint(0, span)))
    return sorted(ds)

def age_on(birth_date_str, on_date):
    # birth_date as YYYY-MM-DD
    try:
        bd = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
    except Exception:
        return ""  # missing or malformed
    years = on_date.year - bd.year - ((on_date.month, on_date.day) < (bd.month, bd.day))
    return years

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def get_age_bracket(age):
    """Map age to performance bracket with validation."""
    if age is None or age == "":
        return "college_plus"  # default if age unknown

    # Type conversion with error handling
    try:
        age = int(float(age))  # Handle both "18" and "18.5"
    except (ValueError, TypeError):
        return "college_plus"  # default for invalid values

    # Sanity check for unrealistic ages
    if age < AGE_MIN_VALID or age > AGE_MAX_VALID:
        return "college_plus"  # default to adult baseline

    if age < AGE_MIDDLE_SCHOOL_MAX:
        return "middle_school"
    elif age < AGE_YOUNG_HS_MAX:
        return "young_hs"
    elif age < AGE_OLDER_HS_MAX:
        return "older_hs"
    else:
        return "college_plus"

def get_adjustment_factor(age, gender, metric, metric_spec, performance_multiplier=1.0):
    """Calculate combined age + gender + performance adjustment factor for a metric."""
    # Get age bracket multiplier
    bracket = get_age_bracket(age)
    age_mult = AGE_BRACKETS[bracket]

    # Get gender multiplier - explicit fallback to Male baseline
    # Use .get() to prevent KeyError if metric is added without gender adjustments
    metric_adjustments = GENDER_ADJUSTMENTS.get(metric, {"Male": 1.00, "Female": 1.00})
    if gender not in ["Male", "Female"]:
        gender_mult = 1.00  # Default to Male baseline for unexpected/missing values
    else:
        gender_mult = metric_adjustments.get(gender, 1.00)

    # For "better is lower" metrics (times), adjustments work differently
    # Lower performance = higher times, so we multiply by the inverse relationship
    if metric_spec["better"] == "lower":
        # Age: younger athletes are slower (higher times), so inverse age_mult
        # Gender: if female mult > 1.0 (slower), apply directly
        # Performance: higher multiplier means better performance (lower times), so inverse
        # Safeguard against division by zero (though current constants are all > 0)
        combined = (1.0 / age_mult if age_mult != 0 else 1.0) * gender_mult * (1.0 / performance_multiplier if performance_multiplier != 0 else 1.0)
    else:
        # For "better is higher" metrics (jumps, RSI), multiply directly
        combined = age_mult * gender_mult * performance_multiplier

    return combined

def athlete_baseline_offsets(roster_rows):
    """Give each athlete a stable baseline offset per metric so their data is consistent across dates."""
    offsets = {}
    for a in roster_rows:
        key = (a.get("firstName","").strip(), a.get("lastName","").strip(), a.get("teamName","").strip())
        sport = a.get("sports", "").strip()
        metrics = get_sport_metrics(sport)
        per_metric = {}
        for m, spec in metrics.items():
            # Small per-athlete bias
            per_metric[m] = random.gauss(0.0, spec["sd"] * 0.5)
        offsets[key] = per_metric
    return offsets

def gen_value(spec, base_offset, day_index, jitter_sd, age=None, gender=None, metric=None, performance_multiplier=1.0):
    # Apply age and gender adjustments to center baseline
    center = spec["center"]
    # Explicitly check for None and empty string to handle all edge cases
    if age is not None and age != "" and gender and metric:
        adjustment = get_adjustment_factor(age, gender, metric, spec, performance_multiplier)
        center = center * adjustment

    # Trend over time: drift_per_day * day_index, plus trial noise
    trend = spec["drift_per_day"] * day_index
    v = random.gauss(center + base_offset + trend, jitter_sd)
    return clamp(v, spec["min"], spec["max"])

def main():
    args = parse_args()
    random.seed(args.seed)

    roster = read_roster(args.roster)
    if not roster:
        print("No roster rows found.", file=sys.stderr)
        sys.exit(1)

    # Resolve performance multiplier
    performance_multiplier = resolve_performance_multiplier(args.performance_level, args.performance_multiplier)

    # Resolve dates
    if args.dates and len(args.dates) > 0:
        dates = [datetime.strptime(d, "%Y-%m-%d").date() for d in args.dates]
    else:
        dates = rand_dates(args.num_random_dates, args.random_date_start, args.random_date_end)

    # Stable athlete-specific baselines
    base = athlete_baseline_offsets(roster)

    out_fields = ["firstName","lastName","gender","teamName","date","age","metric","trial","value","units","flyInDistance","notes"]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=out_fields)
        w.writeheader()

        for a in roster:
            key = (a.get("firstName","").strip(), a.get("lastName","").strip(), a.get("teamName","").strip())
            per_metric_offset = base[key]
            gender = a.get("gender","")
            team = a.get("teamName","")
            birthDate = a.get("birthDate","")
            sport = a.get("sports", "").strip()

            if not sport:
                print(f"Warning: No sport specified for {key[0]} {key[1]}. Skipping.", file=sys.stderr)
                continue

            metrics = get_sport_metrics(sport)

            for di, d in enumerate(sorted(dates)):
                age = age_on(birthDate, d)

                for metric, spec in metrics.items():
                    # Static metrics (HEIGHT, WEIGHT, etc.) only need 1 trial
                    num_trials = 1 if spec.get("static", False) else args.trials
                    for trial in range(num_trials):
                        # Slightly higher within-session jitter than between-date drift
                        jitter_sd = spec["sd"] * 0.5
                        val = gen_value(spec, per_metric_offset[metric], di, jitter_sd, age, gender, metric, performance_multiplier)

                        row = {
                            "firstName": key[0],
                            "lastName": key[1],
                            "gender": gender,
                            "teamName": team,
                            "date": d.isoformat(),
                            "age": age,
                            "metric": metric,
                            "trial": trial + 1,
                            "value": round(val, 3),
                            "units": spec["units"],
                            "flyInDistance": spec["flyInDistance"],
                            "notes": "Auto-generated",
                        }
                        w.writerow(row)

    print(f"Wrote measurements: {args.out}")
    print(f"Dates used: {', '.join([d.isoformat() for d in dates])}")

if __name__ == "__main__":
    main()

