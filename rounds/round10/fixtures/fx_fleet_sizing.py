#!/usr/bin/env python3
"""Step 2+3 fleet sizing arithmetic (read-only; reads
only published data: data/step1/pilot_read.json and
data/step1/l3/jobs_report.json, plus this package's
settings_fleet.json).

Registered inputs (claude-reply-26cc773 sec.3):
  Delta_plan = 0.14, derived there as the pilot's L3
  one-sided 95% lower bound 0.195 x Stage 3's observed
  Delta-to-gain ratio 0.73 = 0.14235, registered
  rounded to 0.14.
  Variance per pair ~ (1 - p0) x q - Delta^2 with
  p0 = 0.01 (the pilot's zero-fire share: 791 jobs
  over 99 of its 100 games, verified below from the
  published jobs report + pilot read) and q = 0.324
  (Stage 3's paired dispersion input, as registered
  in the reply -- cited, not re-derived).
  n = var x ((z_a + z_b) / Delta)^2, z_b = 0.8416
  (80% power). Two-sided z_a = 1.96: n = 120.61 ->
  121 pairs; the layout takes whole seeds x both
  seats -> 61 seeds = 122 pairs REGISTERED. One-sided
  z_a = 1.645: n = 95.0 -> ~95 pairs (96 even). The
  registered 122 is the conservative figure; achieved
  power at 122 pairs (two-sided) ~= 0.805.
  GAME_TIMEOUT = ceil(3 x pilot max wall) = 8031 s.
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
R10 = os.path.dirname(HERE)
SETTINGS = json.load(open(os.path.join(
    R10, "code", "step2", "settings_fleet.json")))
PILOT_READ = json.load(open(os.path.join(
    R10, "data", "step1", "pilot_read.json")))
JOBS_REPORT = json.load(open(os.path.join(
    R10, "data", "step1", "l3", "jobs_report.json")))

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))


def phi(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


sz = SETTINGS["sizing"]
DELTA = float(sz["delta_plan"])
P0 = float(sz["p0"])
Q = float(sz["q"])
ZB = float(sz["z_power_80"])

# ---- p0 from the published pilot artifacts ----
games_with_jobs = int(JOBS_REPORT["games_with_jobs"])
pilot_games = int(PILOT_READ["games_population"])
p0_meas = 1.0 - games_with_jobs / pilot_games
check("pilot zero-fire share from published artifacts "
      "is 1/100 = 0.01", pilot_games == 100
      and games_with_jobs == 99 and abs(p0_meas - P0) < 1e-12,
      "games %d, with jobs %d" % (pilot_games, games_with_jobs))

# ---- Delta_plan derivation ----
derived = 0.195 * 0.73
check("Delta_plan derivation 0.195 x 0.73 = 0.14235, "
      "registered as 0.14", abs(derived - 0.14235) < 1e-9
      and abs(derived - DELTA) <= 0.0025,
      "derived %.5f" % derived)

# ---- variance + both conventions ----
var = (1.0 - P0) * Q - DELTA ** 2
check("variance per pair = 0.99 x 0.324 - 0.0196 = "
      "0.30116", abs(var - 0.30116) < 1e-9
      and abs(var - float(sz["variance_per_pair"])) < 1e-12,
      "var %.8f" % var)
n_two = var * ((1.96 + ZB) / DELTA) ** 2
check("two-sided n = 120.61 -> ceil 121",
      abs(n_two - 120.61) < 0.05 and math.ceil(n_two) == 121,
      "n_two %.4f" % n_two)
n_one = var * ((1.645 + ZB) / DELTA) ** 2
check("one-sided n = 95.0 -> ~95 pairs (96 even)",
      abs(n_one - 95.0) < 0.1, "n_one %.4f" % n_one)
check("registered n = 122 pairs = 61 seeds x both "
      "seats (the conservative, two-sided figure)",
      int(sz["n_pairs_registered"]) == 122
      and int(SETTINGS["games"]["pairs"]) == 122
      and math.ceil(n_two) <= 122 and n_one < 122)
power = phi(DELTA / math.sqrt(var / 122) - 1.96)
check("achieved power at 122 pairs (two-sided) >= 0.80",
      power >= 0.80, "power %.4f" % power)

# ---- the Delta = 0.10 cross-check ----
var10 = (1.0 - P0) * Q - 0.10 ** 2
n10 = var10 * ((1.96 + ZB) / 0.10) ** 2
check("Delta = 0.10 cross-check: n = 243.9 -> 244 pairs "
      "(the reply's 'about 246'; rounding in the z-sum)",
      abs(n10 - 243.9) < 0.5 and abs(math.ceil(n10) - 246) <= 3,
      "n10 %.4f" % n10)

# ---- co-read minimum ----
check("teacher arm 122 games >= the registered Step 2 "
      "minimum of 72", int(SETTINGS["games"]["teacher_games"])
      >= int(SETTINGS["coread"]["minimum_teacher_games"]) == 72)

# ---- GAME_TIMEOUT from the pilot's realized walls ----
max_wall = float(PILOT_READ["wall_s"]["max"])
check("pilot max wall from the published read is "
      "2676.8 s", abs(max_wall - 2676.8) < 0.05,
      "max %.2f" % max_wall)
check("GAME_TIMEOUT = ceil(3 x 2676.8) = 8031 in "
      "settings (both arms)", math.ceil(3 * max_wall) == 8031
      and int(SETTINGS["games"]["timeout_s"]) == 8031)

if __name__ == "__main__":
    bad = 0
    for name, ok, detail in RESULTS:
        print("%s: %s%s" % ("PASS" if ok else "FAIL", name,
                            (" -- " + detail) if detail and not ok
                            else ""))
        bad += 0 if ok else 1
    raise SystemExit(1 if bad else 0)
