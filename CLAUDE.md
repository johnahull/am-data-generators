# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based athlete data generation tool that creates realistic roster and performance measurement data for sports teams. The project consists of two main scripts that work together in a pipeline.

## Architecture

The codebase follows a simple two-script architecture:

1. **`generate_roster.py`** - Creates athlete roster data with demographics, team info, and contact details
2. **`generate_measurements.py`** - Generates performance test measurements from roster data

Both scripts are self-contained Python files with no external dependencies beyond the Python standard library.

## Key Components

### Roster Generation (`generate_roster.py`)
- Generates realistic athlete profiles with configurable demographics
- Supports age groups: middle_school, high_school, college, pro
- Birth years constrained to 2007 and later
- Outputs CSV with fields: firstName, lastName, birthDate, birthYear, graduationYear, gender, emails, phoneNumbers, sports, height, weight, school, teamName
- Uses hardcoded realistic name lists and generic school names

### Measurement Generation (`generate_measurements.py`)
- Creates sport-specific performance test data based on roster input
- Supports Soccer and Volleyball with distinct metric sets
- Features realistic age/gender adjustments and performance drift over time
- Supports multiple trial runs per athlete per test date (static metrics like HEIGHT/WEIGHT get 1 trial)
- Performance levels: elite, varsity, jv, recreational

## Data Flow

The typical workflow is sequential:
1. Generate roster with `generate_roster.py`
2. Use roster CSV as input to `generate_measurements.py` to create measurement data

## Key Configuration

### Sport-Specific Metrics (`generate_measurements.py:8-31`)

**Soccer** (7 metrics):
- FLY10_TIME, VERTICAL_JUMP, AGILITY_505, RSI, T_TEST, HEIGHT, WEIGHT

**Volleyball** (11 metrics):
- VERTICAL_JUMP, APPROACH_JUMP, BLOCK_JUMP, T_TEST, AGILITY_505, RSI
- WINGSPAN, STANDING_REACH, HEIGHT, WEIGHT, DASH_10YD

Each metric has baseline stats (center, standard deviation), acceptable ranges, and drift coefficients. Static metrics (HEIGHT, WEIGHT, WINGSPAN, STANDING_REACH) have `"static": True` and generate only 1 trial.

### Age and Gender Adjustments (`generate_measurements.py:35-65`)
Performance multipliers based on demographic factors to ensure realistic data distribution.

## Common Commands

### Generate roster data:
```bash
./generate_roster.py --out roster.csv --num 25 --gender Male --age_group high_school --sport Soccer --team_name "Varsity Soccer"
```

### Generate measurement data:
```bash
./generate_measurements.py --roster roster.csv --out measurements.csv --trials 3 --dates 2025-03-15 2025-06-20
```

### Generate with performance level:
```bash
./generate_measurements.py --roster roster.csv --out measurements.csv --trials 3 --performance_level jv --dates 2025-03-15
```

## Testing and Validation

No formal test suite exists. Validation is done by:
1. Running scripts with sample parameters
2. Inspecting output CSV files for realistic data ranges
3. Verifying data relationships (e.g., age-appropriate performance values)

## Data Characteristics

- All generated data is synthetic and realistic but not based on real individuals
- Performance metrics account for age, gender, and temporal progression
- Random seed support (default: 42) ensures reproducible datasets
- CSV output format compatible with standard data analysis tools