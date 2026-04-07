# AM Data Generators

Python scripts for generating realistic athlete roster and performance measurement data.

## Scripts

### `generate_roster.py`

Generates a CSV file with athlete roster data including names, birth dates, demographics, and team information.

**Usage:**
```bash
./generate_roster.py --out roster.csv --num 25 --gender Male --age_group high_school --team_name "Varsity Soccer"
```

**Options:**
- `--out` (required): Output CSV file path
- `--num` (required): Number of athletes to generate
- `--gender`: Gender for all athletes (Male/Female/Not Specified)
- `--sport`: Sport name (default: Soccer)
- `--age_group`: Age group (middle_school/high_school/college/pro)
- `--birth_year_min/max`: Override age group with specific birth year range
- `--team_name`: Custom team name (auto-generated if omitted)
- `--seed`: Random seed for reproducibility (default: 42)

**Output fields:**
firstName, lastName, birthDate, birthYear, graduationYear, gender, emails, phoneNumbers, sports, height, weight, school, teamName

### `generate_measurements.py`

Generates performance testing measurements from a roster CSV. Creates realistic values that account for age, gender, and include drift over time.

**Usage:**
```bash
./generate_measurements.py --roster roster.csv --out measurements.csv --trials 3 --dates 2025-03-15 2025-06-20
```

**Options:**
- `--roster` (required): Path to roster CSV file
- `--out` (required): Output measurements CSV file path
- `--trials`: Number of trials per metric per date (default: 3)
- `--dates`: Test dates in YYYY-MM-DD format (space-separated)
- `--num_random_dates`: Generate N random dates if --dates not specified (default: 1)
- `--random_date_start/end`: Date range for random generation (default: 2025-01-01 to 2025-12-31)
- `--seed`: Random seed (default: 42)

**Metrics generated:**
- FLY10_TIME: 10-yard sprint time (seconds)
- VERTICAL_JUMP: Vertical jump height (inches)
- AGILITY_505: 505 agility test time (seconds)
- RSI: Reactive Strength Index
- T_TEST: T-test agility time (seconds)

**Output fields:**
firstName, lastName, gender, teamName, date, age, metric, value, units, flyInDistance, notes

### `generate_dashr.py`

Generates Dashr timing gate CSV files from a roster. Output matches the real Dashr export format (54 columns) and is compatible with the AthleteMetrics Device Import parser.

**Usage:**
```bash
./generate_dashr.py --roster roster.csv --out dashr_export.csv --dates 2025-03-15 2025-06-20
```

**Options:**
- `--roster` (required): Path to roster CSV file
- `--out` (required): Output Dashr CSV file path
- `--dates` (required): Session dates in YYYY-MM-DD format (space-separated)
- `--drills`: Drill types to generate (default: dash flying 505). Choices: dash, flying, 505, proagility
- `--trials`: Attempts per athlete per drill (default: 3)
- `--dash-distance`: Final distance for dash drills in yards (default: 30). Choices: 10, 20, 30, 40
- `--performance-level`: Performance level (default: varsity). Choices: elite, varsity, jv, recreational
- `--seed`: Random seed (default: 42)

**Drill types:**
- `dash`: Timed sprint with split times (5yd, 10yd, 20yd splits for a 30yd dash)
- `flying`: 10-yard fly time with 20-yard approach
- `505`: 505 agility test with left and right directions
- `proagility`: Pro Agility / 5-10-5 test with left and right directions

## Example Workflow

```bash
# Generate a roster of 30 high school athletes
./generate_roster.py --out data/roster.csv --num 30 --age_group high_school

# Generate measurements for two test dates
./generate_measurements.py --roster data/roster.csv --out data/measurements.csv --trials 3 --dates 2025-02-01 2025-05-01
```

### Device Import Testing

```bash
# Generate a Dashr CSV for testing the Device Import feature
./generate_dashr.py --roster data/roster.csv --out data/dashr_export.csv \
  --dates 2025-03-15 2025-06-20 --drills dash flying 505 --trials 3

# Use the output in AthleteMetrics: Data Entry > Device Import tab > Upload Device File
```

## Requirements

Python 3.x (no external dependencies required)
