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
        "HEIGHT_IN": {"units": "in", "better": "higher", "center": 69, "sd": 2.5, "drift_per_day": 0.0, "min": 58, "max": 78, "flyInDistance": "", "static": True},
        "WEIGHT_LBS": {"units": "lbs", "better": "neutral", "center": 155, "sd": 12.0, "drift_per_day": 0.0, "min": 95, "max": 200, "flyInDistance": "", "static": True},
    },
    "Volleyball": {
        "VERTICAL_JUMP": {"units": "in", "better": "higher", "center": 24.0, "sd": 2.5, "drift_per_day": +0.008, "min": 12.0, "max": 36.0, "flyInDistance": ""},
        "APPROACH_JUMP": {"units": "in", "better": "higher", "center": 28.0, "sd": 3.0, "drift_per_day": +0.008, "min": 16.0, "max": 42.0, "flyInDistance": ""},
        "BLOCK_JUMP": {"units": "in", "better": "higher", "center": 24.0, "sd": 2.5, "drift_per_day": +0.008, "min": 12.0, "max": 36.0, "flyInDistance": ""},
        "T_TEST": {"units": "s", "better": "lower", "center": 9.8, "sd": 0.4, "drift_per_day": -0.0010, "min": 7.5, "max": 13.5, "flyInDistance": ""},
        "AGILITY_505": {"units": "s", "better": "lower", "center": 2.55, "sd": 0.07, "drift_per_day": -0.0007, "min": 2.1, "max": 3.5, "flyInDistance": ""},
        "RSI": {"units": "", "better": "higher", "center": 2.4, "sd": 0.25, "drift_per_day": +0.0009, "min": 1.0, "max": 4.5, "flyInDistance": ""},
        "WINGSPAN": {"units": "in", "better": "higher", "center": 76, "sd": 3.5, "drift_per_day": 0.0, "min": 60, "max": 90, "flyInDistance": "", "static": True},
        "STANDING_REACH": {"units": "in", "better": "higher", "center": 96, "sd": 4.0, "drift_per_day": 0.0, "min": 78, "max": 115, "flyInDistance": "", "static": True},
        "HEIGHT_IN": {"units": "in", "better": "higher", "center": 74, "sd": 3.0, "drift_per_day": 0.0, "min": 60, "max": 84, "flyInDistance": "", "static": True},
        "WEIGHT_LBS": {"units": "lbs", "better": "neutral", "center": 170, "sd": 15.0, "drift_per_day": 0.0, "min": 105, "max": 240, "flyInDistance": "", "static": True},
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
    "HEIGHT_IN": {"Male": 1.00, "Female": 0.93},        # Females ~7% shorter
    "WEIGHT_LBS": {"Male": 1.00, "Female": 0.82},      # Females ~18% lighter
    "APPROACH_JUMP": {"Male": 1.00, "Female": 0.75},   # Females ~25% lower jump
    "BLOCK_JUMP": {"Male": 1.00, "Female": 0.75},      # Females ~25% lower jump
    "WINGSPAN": {"Male": 1.00, "Female": 0.93},        # Females ~7% shorter wingspan
    "STANDING_REACH": {"Male": 1.00, "Female": 0.93},  # Females ~7% shorter reach
    "DASH_10YD": {"Male": 1.00, "Female": 1.08},       # Females ~8% slower
}

# Anthropometric growth curves by age and gender (percentage of adult measurements)
# Based on CDC 50th percentile growth data
ANTHROPOMETRIC_GROWTH = {
    "HEIGHT_IN": {
        "Male":   {11: 0.82, 12: 0.85, 13: 0.89, 14: 0.93, 15: 0.97, 16: 0.99, 17: 1.00, 18: 1.00},
        "Female": {11: 0.88, 12: 0.92, 13: 0.96, 14: 0.97, 15: 0.98, 16: 1.00, 17: 1.00, 18: 1.00},
    },
    "WEIGHT_LBS": {
        "Male":   {11: 0.53, 12: 0.60, 13: 0.68, 14: 0.76, 15: 0.84, 16: 0.91, 17: 0.96, 18: 1.00},
        "Female": {11: 0.65, 12: 0.73, 13: 0.81, 14: 0.84, 15: 0.92, 16: 0.94, 17: 0.96, 18: 1.00},
    },
}

# Position-based adjustments for anthropometric metrics
# HEIGHT_IN adjustment is additive (inches), WEIGHT_LBS adjustment is multiplicative
POSITION_ADJUSTMENTS = {
    "Soccer": {
        "Goalkeeper": {"HEIGHT_IN": +4, "WEIGHT_LBS": 1.08},
        "Defender": {"HEIGHT_IN": +1, "WEIGHT_LBS": 1.03},
        "Midfielder": {"HEIGHT_IN": 0, "WEIGHT_LBS": 1.00},
        "Forward": {"HEIGHT_IN": 0, "WEIGHT_LBS": 0.98},
    },
    "Volleyball": {
        "Setter": {"HEIGHT_IN": -2, "WEIGHT_LBS": 0.95},
        "Outside Hitter": {"HEIGHT_IN": +1, "WEIGHT_LBS": 1.00},
        "Middle Blocker": {"HEIGHT_IN": +4, "WEIGHT_LBS": 1.05},
        "Opposite Hitter": {"HEIGHT_IN": +2, "WEIGHT_LBS": 1.03},
        "Libero": {"HEIGHT_IN": -4, "WEIGHT_LBS": 0.90},
        "Defensive Specialist": {"HEIGHT_IN": -2, "WEIGHT_LBS": 0.95},
    },
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

def get_anthropometric_growth_factor(age, gender, metric):
    """Get age-based growth factor for anthropometric metrics (HEIGHT, WEIGHT, WINGSPAN, STANDING_REACH)."""
    if age is None or age == "":
        return 1.0

    try:
        age = int(float(age))
    except (ValueError, TypeError):
        return 1.0

    # Cap age range
    if age < 11:
        age = 11
    elif age > 18:
        age = 18

    # Default to Male if gender unknown
    if gender not in ["Male", "Female"]:
        gender = "Male"

    # Use HEIGHT_IN growth curve for WINGSPAN and STANDING_REACH
    if metric in ["WINGSPAN", "STANDING_REACH"]:
        metric = "HEIGHT_IN"

    # Get growth table for this metric
    if metric not in ANTHROPOMETRIC_GROWTH:
        return 1.0

    growth_table = ANTHROPOMETRIC_GROWTH[metric].get(gender, {})
    return growth_table.get(age, 1.0)

def get_position_adjustment(sport, position, metric):
    """Get position-based adjustment for anthropometric metrics.

    Returns dict with 'additive' (for HEIGHT_IN-like metrics) and 'multiplicative' (for WEIGHT_LBS).
    """
    if not sport or not position:
        return {"additive": 0, "multiplicative": 1.0}

    pos_adjustments = POSITION_ADJUSTMENTS.get(sport, {}).get(position, {})

    if metric in ["HEIGHT_IN", "WINGSPAN", "STANDING_REACH"]:
        return {"additive": pos_adjustments.get("HEIGHT_IN", 0), "multiplicative": 1.0}
    elif metric == "WEIGHT_LBS":
        return {"additive": 0, "multiplicative": pos_adjustments.get("WEIGHT_LBS", 1.0)}

    return {"additive": 0, "multiplicative": 1.0}

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

# Anthropometric ratio constants for correlating HEIGHT, WINGSPAN, and STANDING_REACH
# Ape index (wingspan/height) typically ~1.0 for average, athletes often slightly higher
WINGSPAN_HEIGHT_RATIO = {"mean": 1.02, "sd": 0.02}  # Wingspan is typically ~102% of height
# Standing reach is typically ~130% of height (arm raised overhead)
STANDING_REACH_HEIGHT_RATIO = {"mean": 1.30, "sd": 0.02}

def compute_static_values(roster_rows, performance_multiplier=1.0):
    """Compute static metric values (HEIGHT, WEIGHT, etc.) once per athlete for consistency across dates.

    HEIGHT, WINGSPAN, and STANDING_REACH are correlated: WINGSPAN and STANDING_REACH
    are derived from HEIGHT using anthropometric ratios with small individual variation.
    """
    static_values = {}
    for a in roster_rows:
        key = (a.get("firstName","").strip(), a.get("lastName","").strip(), a.get("teamName","").strip())
        sport = a.get("sports", "").strip()
        gender = a.get("gender", "")
        position = a.get("position", "").strip()

        metrics = get_sport_metrics(sport)
        athlete_static = {}

        # First, compute HEIGHT_IN as the base anthropometric measurement
        if "HEIGHT_IN" in metrics:
            spec = metrics["HEIGHT_IN"]
            center = spec["center"]

            # Apply gender adjustment
            gender_mult = GENDER_ADJUSTMENTS.get("HEIGHT_IN", {}).get(gender, 1.0)
            center = center * gender_mult

            # Apply position adjustments
            pos_adj = get_position_adjustment(sport, position, "HEIGHT_IN")
            center = center + pos_adj["additive"]

            # Add small per-athlete variation
            athlete_variation = random.gauss(0.0, spec["sd"] * 0.3)
            height_value = clamp(center + athlete_variation, spec["min"], spec["max"])
            athlete_static["HEIGHT_IN"] = height_value
        else:
            height_value = None

        # Compute WINGSPAN derived from HEIGHT with individual ratio variation
        if "WINGSPAN" in metrics and height_value is not None:
            spec = metrics["WINGSPAN"]
            # Each athlete gets their own ape index (wingspan/height ratio)
            athlete_ratio = random.gauss(WINGSPAN_HEIGHT_RATIO["mean"], WINGSPAN_HEIGHT_RATIO["sd"])
            wingspan_value = height_value * athlete_ratio
            wingspan_value = clamp(wingspan_value, spec["min"], spec["max"])
            athlete_static["WINGSPAN"] = wingspan_value

        # Compute STANDING_REACH derived from HEIGHT with individual ratio variation
        if "STANDING_REACH" in metrics and height_value is not None:
            spec = metrics["STANDING_REACH"]
            # Each athlete gets their own standing reach ratio
            athlete_ratio = random.gauss(STANDING_REACH_HEIGHT_RATIO["mean"], STANDING_REACH_HEIGHT_RATIO["sd"])
            reach_value = height_value * athlete_ratio
            reach_value = clamp(reach_value, spec["min"], spec["max"])
            athlete_static["STANDING_REACH"] = reach_value

        # Compute other static metrics (WEIGHT_LBS, etc.) independently
        for metric, spec in metrics.items():
            if not spec.get("static", False):
                continue
            # Skip metrics we already computed
            if metric in ["HEIGHT_IN", "WINGSPAN", "STANDING_REACH"]:
                continue

            center = spec["center"]

            # Apply gender adjustment
            gender_mult = GENDER_ADJUSTMENTS.get(metric, {}).get(gender, 1.0)
            center = center * gender_mult

            # Apply position adjustments
            pos_adj = get_position_adjustment(sport, position, metric)
            center = center + pos_adj["additive"]
            center = center * pos_adj["multiplicative"]

            # Add small per-athlete variation
            athlete_variation = random.gauss(0.0, spec["sd"] * 0.3)
            value = clamp(center + athlete_variation, spec["min"], spec["max"])
            athlete_static[metric] = value

        static_values[key] = athlete_static

    return static_values

def gen_value(spec, base_offset, day_index, jitter_sd, age=None, gender=None, metric=None,
              performance_multiplier=1.0, sport=None, position=None):
    center = spec["center"]
    is_static = spec.get("static", False)

    if age is not None and age != "" and gender and metric:
        if is_static:
            # Use anthropometric growth curves for static metrics (HEIGHT, WEIGHT, etc.)
            # Apply gender adjustment first
            gender_mult = GENDER_ADJUSTMENTS.get(metric, {}).get(gender, 1.0)
            center = center * gender_mult

            # Apply age-based growth factor
            growth_factor = get_anthropometric_growth_factor(age, gender, metric)
            center = center * growth_factor

            # Apply position adjustments
            pos_adj = get_position_adjustment(sport, position, metric)
            center = center + pos_adj["additive"]
            center = center * pos_adj["multiplicative"]
        else:
            # Use performance-based adjustments for non-static metrics
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

    # Pre-compute static metric values (HEIGHT, WEIGHT, etc.) once per athlete
    static_vals = compute_static_values(roster, performance_multiplier)

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
            position = a.get("position", "").strip()

            if not sport:
                print(f"Warning: No sport specified for {key[0]} {key[1]}. Skipping.", file=sys.stderr)
                continue

            metrics = get_sport_metrics(sport)

            for di, d in enumerate(sorted(dates)):
                age = age_on(birthDate, d)

                # Sort metrics so static (anthropometric) come first
                sorted_metrics = sorted(metrics.items(), key=lambda x: (not x[1].get("static", False), x[0]))
                for metric, spec in sorted_metrics:
                    is_static = spec.get("static", False)
                    # Static metrics (HEIGHT, WEIGHT, etc.) only need 1 trial
                    num_trials = 1 if is_static else args.trials
                    for trial in range(num_trials):
                        if is_static:
                            # Use pre-computed static value (consistent across all dates)
                            val = static_vals[key][metric]
                        else:
                            # Generate dynamic value with jitter
                            jitter_sd = spec["sd"] * 0.5
                            val = gen_value(spec, per_metric_offset[metric], di, jitter_sd, age, gender, metric,
                                           performance_multiplier, sport, position)

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

