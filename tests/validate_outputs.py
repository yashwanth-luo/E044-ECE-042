
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"


def read_csv(name):
    with (OUT / name).open(
        newline="", encoding="utf-8-sig"
    ) as file:
        return list(csv.DictReader(file))


reads = read_csv("read_log.csv")
recharges = read_csv("recharge_log.csv")
passes = read_csv("pass_log.csv")
daily = read_csv("daily_collection.csv")
statements = read_csv("statements.csv")

checks = []


def check(label, condition):
    if not condition:
        raise AssertionError(f"FAILED: {label}")

    checks.append(label)


exact_return = [
    r for r in reads
    if r["tag_id"] == "TAG-0090"
    and r["timestamp"] in {
        "2026-10-08 08:15:00",
        "2026-10-09 08:15:00"
    }
]

check(
    "Exact 24-hour return is half fare",
    len(exact_return) == 2
    and exact_return[1]["outcome"] == "RETURN"
    and exact_return[1]["fare"] == "32.50"
)

check(
    "Duplicate read after 45 seconds is ignored",
    any(
        r["tag_id"] == "TAG-0111"
        and r["timestamp"] == "2026-10-03 22:10:47"
        and r["outcome"] == "DUPLICATE_IGNORED"
        for r in reads
    )
)

trip_tag = [
    r for r in reads if r["tag_id"] == "TAG-0340"
]

check(
    "50-trip pass stops after 50 free crossings",
    sum(r["outcome"] == "PASS" for r in trip_tag) == 50
    and sum(
        r["outcome"] in ("SINGLE", "RETURN")
        for r in trip_tag
    ) == 8
)

check(
    "Rs.50 recharge is rejected",
    any(
        r["amount"] == "50.00"
        and r["status"] == "REJECTED_MINIMUM"
        for r in recharges
    )
)

check(
    "Non-local CAR monthly pass is rejected",
    any(
        r["tag_id"] == "TAG-0254"
        and r["status"] == "REJECTED"
        for r in passes
    )
)

check(
    "Higher-class mismatch penalty applies during a pass",
    any(
        r["outcome"] == "PASS"
        and r["penalty"] == "100.00"
        and "MISMATCH" in r["flags"]
        for r in reads
    )
)

check(
    "Lower detected class does not reduce BUS_TRUCK fare",
    any(
        r["tag_id"] == "TAG-0368"
        and r["detected_class"] == "LCV"
        and r["fare"] == "110.00"
        and r["penalty"] == "0.00"
        for r in reads
    )
)

check(
    "Exempt mismatch remains zero-fare",
    any(
        r["tag_id"] == "TAG-0218"
        and r["detected_class"] == "BUS_TRUCK"
        and r["outcome"] == "EXEMPT"
        and r["fare"] == "0.00"
        for r in reads
    )
)

check(
    "All output row counts match the sample",
    len(reads) == 5404
    and len(recharges) == 146
    and len(passes) == 61
    and len(daily) == 31
    and len(statements) == 500
)

print(f"PASS: {len(checks)} validation checks")

for label in checks:
    print("[OK]", label)
