#!/usr/bin/env python3
import argparse, csv, random
from datetime import date, timedelta
from pathlib import Path

HEADERS = [
    "firstName","lastName","birthDate","birthYear","graduationYear","gender",
    "emails","phoneNumbers","sports","position","height","weight","school","teamName"
]

# Sport-specific positions with weights reflecting typical team distribution
POSITIONS = {
    "Soccer": [
        ("Goalkeeper", 2),
        ("Defender", 4),
        ("Midfielder", 4),
        ("Forward", 3),
    ],
    "Volleyball": [
        ("Setter", 2),
        ("Outside Hitter", 4),
        ("Middle Blocker", 3),
        ("Opposite Hitter", 2),
        ("Libero", 2),
        ("Defensive Specialist", 2),
    ],
}

FIRST_NAMES_M = ["Ethan","Liam","Noah","Mason","Jacob","Aiden","James","Elijah","Benjamin","Lucas",
                 "Alexander","Daniel","Matthew","Henry","Sebastian","Jack","Owen","Samuel","David","Joseph",
                 "Carter","Wyatt","John","Jackson","Luke","Anthony","Isaac","Grayson","Julian","Levi",
                 "Christopher","Joshua","Andrew","Lincoln","Mateo","Ryan","Jaxon","Nathan","Aaron","Isaiah",
                 "Thomas","Charles","Caleb","Josiah","Christian","Hunter","Eli","Jonathan","Connor","Landon",
                 "Adrian","Asher","Cameron","Leo","Theodore","Jeremiah","Hudson","Robert","Easton","Nolan",
                 "Nicholas","Ezra","Colton","Angel","Brayden","Jordan","Dominic","Austin","Ian","Adam",
                 "Elias","Jaxson","Greyson","Jose","Ezekiel","Carson","Evan","Maverick","Bryson","Jace",
                 "Cooper","Xavier","Parker","Roman","Jason","Santiago","Chase","Sawyer","Gavin","Leonardo",
                 "Kayden","Ayden","Jameson","Kevin","Bentley","Zachary","Everett","Axel","Tyler","Micah",
                 "Vincent","Weston","Miles","Wesley","Nathaniel","Harrison","Brandon","Cole","Declan","Luis",
                 "Braxton","Damian","Silas","Tristan","Ryder","Bennett","George","Emmett","Justin","Kai",
                 "Max","Diego","Luca","Ryker","Carlos","Maxwell","Kingston","Ivan","Maddox","Juan",
                 "Ashton","Jayce","Rowan","Kaiden","Giovanni","Eric","Jesus","Calvin","Abel","King",
                 "Camden","Amir","Blake","Alex","Brody","Malachi","Emmanuel","Jonah","Beau","Jude",
                 "Antonio","Alan","Elliott","Elliot","Wayne","Rory","Louis","Gabriel","Victor","Sergio",
                 "Nash","Noel","Felix","Edward","Dean","Lorenzo","Matteo","Maximus","Preston","Oscar",
                 "Karter","Jax","Marcus","Brantley","Legend","Remington","Leon","Zion","Carlos","Tucker",
                 "Finn","Arthur","Milo","Knox","Ricardo","Patrick","Paxton","Brian","Timothy","Abraham",
                 "Richard","Kaden","Andre","Enzo","Zayden","Rafael","Nico","Francis","Cayden","Shane",
                 "River","Kyle","Killian","Andy","Sage","Archer","Javier","Alejandro","Miguel","Griffin",
                 "Hayden","Paul","Jett","Phoenix","Zander","Liam","Brady","Oliver","Braeden","Dallas",
                 "Barrett","Reid","Colt","Beckham","Avery","Jake","Gage","Theo","Jasper","Corbin",
                 "Cruz","Atlas","Rhett","Lane","Sean","Kyrie","Mario","Kash","Bryce","Brooks",
                 "Travis","Graham","Clayton","Simon","Cody","Stephen","Kane","Gunner","Zane","River",
                 "Dawson","Messiah","Kai","Magnus","Brett","Ellis","Emmitt","Porter","Dane","Jaden"]
FIRST_NAMES_F = ["Mia","Ava","Sophia","Isabella","Charlotte","Amelia","Evelyn","Abigail","Emily","Elizabeth",
                 "Sofia","Avery","Ella","Scarlett","Grace","Chloe","Victoria","Riley","Nora","Lily",
                 "Zoey","Mila","Hazel","Leah","Penelope","Aria","Norah","Layla","Margaret","Ellie",
                 "Madison","Delilah","Isla","Adalyn","Grayson","Brielle","Eliana","Nova","Morgan","Sydney",
                 "Maya","Leilani","Ariana","Elena","Cora","Ayla","Eloise","Anna","Caroline","Genesis",
                 "Aaliyah","Kennedy","Kinsley","Allison","Gabriella","Adeline","Skylar","Mary","Nevaeh","Alice",
                 "Luna","Everly","Mackenzie","Claire","Madelyn","Natalie","Naomi","Eva","Ruby","Serenity",
                 "Autumn","Adelyn","Hailey","Gianna","Valentina","Eliza","Ashley","Camila","Josephine","Maria",
                 "Iris","Eleanor","Sarah","Natalia","Isabelle","Willow","Piper","Aurora","Lucy","Samantha",
                 "Paisley","Raelynn","Stella","Violet","Savannah","Brooklyn","Lillian","Juniper","Zoe","Emilia",
                 "Hannah","Julia","Melody","Jasmine","Josephine","Ivy","Faith","Alexandra","Kylie","Audrey",
                 "Catherine","Clare","Kimberly","Brooklynn","Sophie","Aubrey","Olive","Cecilia","Gabrielle","Lydia",
                 "Adriana","Josie","Parker","Madeline","Ryleigh","Liliana","Brynlee","Andrea","Keira","Juliana",
                 "Nicole","Hadley","Arya","Dakota","Harmony","Lyla","Peyton","Phoebe","Athena","Reese",
                 "Carmen","Paige","Daniela","Ariel","Angela","Payton","Emma","Jocelyn","Kaitlyn","Nevaeh",
                 "Diana","Rosalie","Hope","Georgia","Mya","Jordyn","Jenna","Rachel","Molly","Kate",
                 "Kayla","Destiny","Amy","Kalani","Finley","Ximena","Fernanda","Summer","Stephanie","Mckenzie",
                 "Paola","Daisy","Miranda","Rowan","London","Kyla","Esther","Eden","Anastasia","Kamila",
                 "Tessa","Francesca","Lilly","Alicia","Sabrina","Alayna","Elise","Gracie","Emery","Michelle",
                 "Lila","Makayla","Alexa","Gia","Vanessa","Nyla","Ember","Sage","Mckenna","Annie",
                 "Presley","Amara","Alayah","Amira","Charlee","Lucia","Amina","Alana","Madeleine","Jacqueline",
                 "Alaina","Miriam","Rebecca","Adelynn","Catalina","Fiona","Sloane","June","Camille","Angelina",
                 "Lola","Maggie","Gemma","Valeria","Heidi","Adelaide","Vera","Alina","Vivian","Talia",
                 "Haisley","Jessica","Khloe","Sydney","Ophelia","Daphne","Mallory","Celia","Remi","Raegan",
                 "Kali","Teagan","Rose","Juliette","Callie","Kiara","Allie","Haven","Oakley","Fatima"]
LAST_NAMES = ["Martinez","Johnson","Garcia","Hernandez","Lopez","Rodriguez","Perez","Sanchez","Ramirez","Torres",
              "Flores","Rivera","Gonzalez","Morales","Diaz","Castillo","Gomez","Santos","Reyes","Nguyen","Patel","Kim",
              "Smith","Brown","Davis","Miller","Wilson","Moore","Taylor","Anderson","Thomas","Jackson",
              "White","Harris","Martin","Thompson","Young","Allen","King","Wright","Scott","Torres",
              "Adams","Baker","Gonzalez","Nelson","Carter","Mitchell","Perez","Roberts","Turner","Phillips",
              "Campbell","Parker","Evans","Edwards","Collins","Stewart","Sanchez","Morris","Rogers","Reed",
              "Cook","Morgan","Bell","Murphy","Bailey","Rivera","Cooper","Richardson","Cox","Howard",
              "Ward","Torres","Peterson","Gray","Ramirez","James","Watson","Brooks","Kelly","Sanders",
              "Price","Bennett","Wood","Barnes","Ross","Henderson","Coleman","Jenkins","Perry","Powell",
              "Long","Patterson","Hughes","Flores","Washington","Butler","Simmons","Foster","Gonzales","Bryant",
              "Alexander","Russell","Griffin","Diaz","Hayes","Myers","Ford","Hamilton","Graham","Sullivan",
              "Wallace","Woods","Cole","West","Jordan","Owens","Reynolds","Fisher","Ellis","Harrison",
              "Gibson","Mcdonald","Cruz","Marshall","Ortiz","Gomez","Murray","Freeman","Wells","Webb",
              "Simpson","Stevens","Tucker","Porter","Hunter","Hicks","Crawford","Henry","Boyd","Mason",
              "Morales","Kennedy","Warren","Dixon","Ramos","Reyes","Burns","Gordon","Shaw","Holmes",
              "Rice","Robertson","Hunt","Black","Daniels","Palmer","Mills","Nichols","Grant","Knight",
              "Ferguson","Rose","Stone","Hawkins","Dunn","Perkins","Hudson","Spencer","Gardner","Stephens",
              "Payne","Pierce","Berry","Matthews","Arnold","Wagner","Willis","Ray","Watkins","Olson",
              "Carroll","Duncan","Snyder","Hart","Cunningham","Bradley","Lane","Andrews","Ruiz","Harper",
              "Fox","Riley","Armstrong","Carpenter","Weaver","Greene","Lawrence","Elliott","Chavez","Sims",
              "Austin","Peters","Kelley","Franklin","Lawson","Fields","Gutierrez","Ryan","Schmidt","Carr",
              "Vasquez","Castillo","Wheeler","Chapman","Oliver","Montgomery","Richards","Williamson","Johnston","Banks",
              "Meyer","Bishop","Mccoy","Howell","Alvarez","Morrison","Hansen","Fernandez","Garza","Harvey",
              "Little","Burton","Stanley","Nguyen","George","Jacobs","Reid","Kim","Fuller","Lynch",
              "Dean","Gilbert","Garrett","Romero","Welch","Larson","Frazier","Burke","Hanson","Day",
              "Mendoza","Moreno","Bowman","Medina","Fowler","Brewer","Hoffman","Carlson","Silva","Pearson",
              "Holland","Douglas","Fleming","Jensen","Vargas","Byrd","Davidson","Hopkins","May","Terry",
              "Herrera","Wade","Soto","Walters","Curtis","Neal","Caldwell","Lowe","Jennings","Barnett",
              "Graves","Jimenez","Horton","Shelton","Barrett","Obrien","Castro","Sutton","Gregory","Mckinney",
              "Lucas","Miles","Craig","Rodriquez","Chambers","Holt","Lambert","Fletcher","Watts","Bates"]
SCHOOLS = ["Lincoln High School","Jefferson High School","Roosevelt High School","Washington High School","Franklin High School","Madison High School","Kennedy High School","Central High School","Riverside High School","Northview High School"]
EMAIL_DOMAINS = ["email.com","school.edu","mail.com","inbox.com"]

def parse_args():
    p = argparse.ArgumentParser(description="Generate a roster CSV.")
    p.add_argument("--out", required=True, help="Output CSV path")
    p.add_argument("--num", type=int, required=True, help="Number of players")
    p.add_argument("--gender", choices=["Male","Female","Not Specified"], help="Gender for all players")
    p.add_argument("--sport", default=None, help="Sport name (default: Soccer)")
    p.add_argument("--age_group", choices=["middle_school","high_school","college","pro"], help="Age group (if omitted, randomly chosen)")
    p.add_argument("--birth_year_min", type=int, help="Min birth year (inclusive, overrides age_group)")
    p.add_argument("--birth_year_max", type=int, help="Max birth year (inclusive, overrides age_group)")
    p.add_argument("--team_name", default=None, help="Team name; if omitted, auto-generated")
    p.add_argument("--school", default=None, help="School name; if omitted, randomly chosen")
    p.add_argument("--exclude_last_names", nargs="*", help="Last names to exclude from generation")
    p.add_argument("--height_adjust", type=int, default=0, help="Height adjustment in inches (e.g., +2 for taller, -2 for shorter)")
    p.add_argument("--seed", type=int, default=42, help="Random seed")
    return p.parse_args()

def get_birth_years_for_age_group(age_group: str, current_year: int = 2025):
    """Return (min_birth_year, max_birth_year) for the given age group."""
    age_ranges = {
        "middle_school": (11, 14),  # ages 11-14
        "high_school": (14, 18),    # ages 14-18
        "college": (18, 22),        # ages 18-22
        "pro": (22, 35),            # ages 22-35
    }
    min_age, max_age = age_ranges[age_group]
    # birth_year = current_year - age
    min_birth_year = max(2007, current_year - max_age)  # Ensure 2007 or later
    max_birth_year = max(2007, current_year - min_age)
    return (min_birth_year, max_birth_year)

def rng_date_in_year(year: int) -> date:
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

def grad_year_from_birth(birth_year: int) -> int:
    # Typical US graduation ~ spring of year they turn 18
    return birth_year + 18

# Sport-specific height ranges (inches) by gender
HEIGHT_RANGES = {
    "Volleyball": {
        "Female": (66, 75),  # 5'6" to 6'3" for elite female volleyball
        "Male": (72, 82),    # 6'0" to 6'10" for elite male volleyball
    },
    "Soccer": {
        "Female": (62, 70),  # 5'2" to 5'10" for female soccer
        "Male": (66, 76),    # 5'6" to 6'4" for male soccer
    },
}

def height_inches(gender: str, sport: str = None, height_adjust: int = 0) -> int:
    """Generate height based on sport and gender, with optional adjustment."""
    if sport and sport in HEIGHT_RANGES:
        ranges = HEIGHT_RANGES[sport]
        if gender in ranges:
            lo, hi = ranges[gender]
            lo += height_adjust
            hi += height_adjust
            return random.randint(lo, hi)
    # Default fallback
    if gender == "Female":
        lo, hi = 60, 70
    elif gender == "Male":
        lo, hi = 64, 74
    else:
        lo, hi = 62, 72
    lo += height_adjust
    hi += height_adjust
    return random.randint(lo, hi)

def weight_pounds(ht_in: int, gender: str) -> int:
    """Generate weight using BMI formula."""
    # BMI ~ N(21, 2) for females, N(22, 2) for males
    bmi = random.gauss(21 if gender != "Male" else 22, 2)
    # Correct BMI formula: weight(kg) = BMI * height(m)^2
    ht_meters = ht_in * 0.0254
    wt_kg = bmi * (ht_meters ** 2)
    wt_lbs = wt_kg * 2.205
    # Clamp to reasonable athletic ranges
    if gender == "Female":
        wt_lbs = max(110, min(200, wt_lbs))
    else:
        wt_lbs = max(130, min(250, wt_lbs))
    return int(round(wt_lbs))

def phone():
    return f"555-555-{random.randint(1000,9999)}"

def email(first: str, last: str):
    tag = random.randint(10,99)
    dom = random.choice(EMAIL_DOMAINS)
    return f"{first.lower()}.{last.lower()}{tag}@{dom}"

def pick_first_name(gender: str):
    if gender == "Female":
        return random.choice(FIRST_NAMES_F)
    if gender == "Male":
        return random.choice(FIRST_NAMES_M)
    # mixed
    return random.choice(FIRST_NAMES_M + FIRST_NAMES_F)

def pick_position(sport: str) -> str:
    """Pick a position for the given sport using weighted random selection."""
    if sport not in POSITIONS:
        return ""
    positions, weights = zip(*POSITIONS[sport])
    return random.choices(positions, weights=weights, k=1)[0]

def main():
    args = parse_args()
    random.seed(args.seed)

    gender = args.gender if args.gender else random.choice(["Male","Female"])
    sport = args.sport if args.sport else "Soccer"

    # Determine birth years
    if args.birth_year_min and args.birth_year_max:
        # Explicit birth years override everything
        by_min, by_max = args.birth_year_min, args.birth_year_max
        age_group = None
    elif args.age_group:
        # Use specified age group
        age_group = args.age_group
        by_min, by_max = get_birth_years_for_age_group(age_group)
    else:
        # Random age group
        age_group = random.choice(["middle_school", "high_school", "college", "pro"])
        by_min, by_max = get_birth_years_for_age_group(age_group)

    if by_min > by_max:
        by_min, by_max = by_max, by_min

    # Auto team name if needed
    if args.team_name:
        team = args.team_name
    else:
        cohort = random.randint(by_min, by_max)
        suffix = "B" if gender == "Male" else ("G" if gender == "Female" else "X")
        team = f"{sport} {cohort}{suffix} Squad"

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    used_names = set()
    
    # Filter out excluded last names
    available_last_names = LAST_NAMES
    if args.exclude_last_names:
        available_last_names = [name for name in LAST_NAMES if name not in args.exclude_last_names]
        if not available_last_names:
            raise ValueError("All last names have been excluded. Cannot generate roster.")
    
    for i in range(args.num):
        # Ensure some name variety
        for _ in range(100):
            fn = pick_first_name(gender)
            ln = random.choice(available_last_names)
            key = (fn, ln)
            if key not in used_names:
                used_names.add(key)
                break

        by = random.randint(by_min, by_max)
        bd = rng_date_in_year(by)
        gy = grad_year_from_birth(by)

        ht = height_inches(gender, sport, args.height_adjust)
        wt = weight_pounds(ht, gender)

        school = args.school if args.school else random.choice(SCHOOLS)
        emails = email(fn, ln)
        phones = phone()

        rows.append({
            "firstName": fn,
            "lastName": ln,
            "birthDate": bd.isoformat(),
            "birthYear": by,
            "graduationYear": gy,
            "gender": gender,
            "emails": emails,
            "phoneNumbers": phones,
            "sports": sport,
            "position": pick_position(sport),
            "height": ht,
            "weight": wt,
            "school": school,
            "teamName": team
        })

    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=HEADERS)
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote roster: {out_path}")
    print(f"Team: {team} | Players: {len(rows)} | Gender: {gender} | Sport: {sport}")
    age_group_msg = f" | Age group: {age_group}" if age_group else ""
    print(f"Birth years: {by_min}–{by_max}{age_group_msg}")

if __name__ == "__main__":
    main()

