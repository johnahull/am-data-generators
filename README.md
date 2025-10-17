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

## Example Workflow

```bash
# Generate a roster of 30 high school athletes
./generate_roster.py --out data/roster.csv --num 30 --age_group high_school

# Generate measurements for two test dates
./generate_measurements.py --roster data/roster.csv --out data/measurements.csv --trials 3 --dates 2025-02-01 2025-05-01
```

## Requirements

Python 3.x (no external dependencies required)
