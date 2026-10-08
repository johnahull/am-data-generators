"""Regression tests for the generators. Stdlib only: python3 -m unittest discover -s tests -v"""
import csv
import subprocess
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATES = ["2025-03-15", "2025-06-20"]

# Metric codes AthleteMetrics accepts for the codes these generators emit. Update when the app changes
# (AM-FEAT-016 split AGILITY_505 by protocol; AM-FEAT-015 added the MQ_* scores).
APP_METRIC_CODES = {
    "FLY10_TIME", "VERTICAL_JUMP", "APPROACH_JUMP", "BLOCK_JUMP", "RSI", "T_TEST",
    "HEIGHT_IN", "WEIGHT_LBS", "WINGSPAN", "STANDING_REACH", "DASH_10YD",
    "AGILITY_505_YD", "AGILITY_505_YD_L", "AGILITY_505_YD_R",
    "MQ_LIN_ACCEL", "MQ_MAX_VELO", "MQ_DECEL", "MQ_SHUFFLE", "MQ_LATRUN", "MQ_HIPTURN",
    "MQ_BACKPEDAL", "MQ_JUMP",
    "MQ_TRANS_DECEL_CUT", "MQ_TRANS_GAS_BRAKE", "MQ_TRANS_BACKPEDAL_TURN", "MQ_TRANS_LAT_LINEAR",
}
RETIRED_CODES = {"AGILITY_505", "AGILITY_505_L", "AGILITY_505_R", "AGILITY_505_LSI"}
MQ_PATTERNS = {"MQ_LIN_ACCEL", "MQ_MAX_VELO", "MQ_DECEL", "MQ_SHUFFLE",
               "MQ_LATRUN", "MQ_HIPTURN", "MQ_BACKPEDAL", "MQ_JUMP"}
MQ_TRANSITIONS = {"MQ_TRANS_DECEL_CUT", "MQ_TRANS_GAS_BRAKE", "MQ_TRANS_BACKPEDAL_TURN", "MQ_TRANS_LAT_LINEAR"}


def run(script, *args):
    subprocess.run([sys.executable, str(ROOT / script), *args], check=True, capture_output=True, text=True)


class GeneratorOutputTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        tmp = Path(cls._tmp.name)
        cls.measurements = {}
        cls.dashr = []
        for sport in ("Soccer", "Volleyball"):
            roster = tmp / f"{sport}-roster.csv"
            out = tmp / f"{sport}-measurements.csv"
            run("generate_roster.py", "--out", str(roster), "--num", "10", "--sport", sport,
                "--age_group", "high_school", "--team_name", f"{sport} Test")
            run("generate_measurements.py", "--roster", str(roster), "--out", str(out), "--dates", *DATES)
            with open(out, newline="", encoding="utf-8") as f:
                cls.measurements[sport] = list(csv.DictReader(f))
            if sport == "Volleyball":
                dashr = tmp / "dashr.csv"
                run("generate_dashr.py", "--roster", str(roster), "--out", str(dashr),
                    "--dates", DATES[0], "--drills", "dash", "flying", "505", "proagility")
                with open(dashr, newline="", encoding="utf-8") as f:
                    cls.dashr = list(csv.DictReader(f))

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def by_athlete_date(self, sport):
        grouped = defaultdict(lambda: defaultdict(list))
        for r in self.measurements[sport]:
            grouped[(r["firstName"], r["lastName"], r["date"])][r["metric"]].append(float(r["value"]))
        return grouped

    def test_only_codes_the_app_accepts(self):
        for sport, rows in self.measurements.items():
            emitted = {r["metric"] for r in rows}
            self.assertFalse(emitted & RETIRED_CODES, f"{sport} emits retired codes")
            self.assertLessEqual(emitted, APP_METRIC_CODES, f"{sport} emits unknown codes")

    def test_mq_scores_are_whole_numbers_0_to_3_one_trial(self):
        for sport, rows in self.measurements.items():
            mq = [r for r in rows if r["metric"].startswith("MQ_")]
            self.assertTrue(mq)
            for r in mq:
                self.assertIn(r["value"], {"0", "1", "2", "3"})
                self.assertEqual(r["units"], "score")
                self.assertEqual(r["trial"], "1")

    def test_all_mq_codes_present_on_every_date(self):
        # MQI_TOTAL needs all 8 patterns, MQ_TRANSITION_TOTAL all 4 transitions, on the same date.
        for sport in self.measurements:
            for key, metrics in self.by_athlete_date(sport).items():
                self.assertLessEqual(MQ_PATTERNS | MQ_TRANSITIONS, set(metrics), f"{sport} {key}")

    def test_cod_deficit_inputs_present_and_in_range(self):
        for sport in self.measurements:
            for key, metrics in self.by_athlete_date(sport).items():
                for code in ("AGILITY_505_YD_L", "AGILITY_505_YD_R", "DASH_10YD"):
                    self.assertIn(code, metrics, f"{sport} {key} missing {code}")
                deficit = min(metrics["AGILITY_505_YD_L"][0], metrics["AGILITY_505_YD_R"][0]) - metrics["DASH_10YD"][0]
                self.assertGreaterEqual(deficit, 0, f"{sport} {key}")
                self.assertLessEqual(deficit, 2.0, f"{sport} {key}")

    def test_dashr_rows_are_yard_protocol(self):
        self.assertTrue(self.dashr)
        self.assertEqual({r["Units"] for r in self.dashr}, {"Imperial"})
        agility = [r for r in self.dashr if r["Type"] == "505 Agility Test"]
        self.assertTrue(agility)
        self.assertEqual({r["Direction"] for r in agility}, {"L", "R"})
        # Parser accepts 1.3-4.6 s for the yard 5-0-5
        for r in agility:
            self.assertTrue(1.3 <= float(r["Final Time"]) <= 4.6, r["Final Time"])


if __name__ == "__main__":
    unittest.main()
