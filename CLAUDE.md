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
- Outputs CSV with fields: firstName, lastName, birthDate, birthYear, graduationYear, gender, emails, phoneNumbers, sports, height, weight, school, teamName
- Uses hardcoded realistic name lists and school names for Austin area

### Measurement Generation (`generate_measurements.py`)
- Creates performance test data based on roster input
- Implements 5 standard athletic metrics: FLY10_TIME, VERTICAL_JUMP, AGILITY_505, RSI, T_TEST
- Features realistic age/gender adjustments and performance drift over time
- Supports multiple trial runs per athlete per test date

## Data Flow

The typical workflow is sequential:
1. Generate roster with `generate_roster.py`
2. Use roster CSV as input to `generate_measurements.py` to create measurement data

## Key Configuration

### Metric Specifications (`generate_measurements.py:8-14`)
Each metric has baseline stats (center, standard deviation), acceptable ranges, and drift coefficients for realistic progression over time.

### Age and Gender Adjustments (`generate_measurements.py:16-38`)
Performance multipliers based on demographic factors to ensure realistic data distribution.

## Common Commands

### Generate roster data:
```bash
./generate_roster.py --out roster.csv --num 25 --gender Male --age_group high_school --team_name "Varsity Soccer"
```

### Generate measurement data:
```bash
./generate_measurements.py --roster roster.csv --out measurements.csv --trials 3 --dates 2025-03-15 2025-06-20
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