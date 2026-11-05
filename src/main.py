import csv
from pathlib import Path
from datetime import datetime, timedelta
import calendar
from collections import defaultdict
from decimal import Decimal, InvalidOperation

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
RATES = {"CAR": Decimal("65"), "LCV": Decimal("105"),
         "BUS_TRUCK": Decimal("220"), "MAV": Decimal("345")}
CLASS_ORDER = ["CAR", "LCV", "BUS_TRUCK", "MAV"]
DT_FORMAT = "%Y-%m-%d %H:%M:%S"


def money(value):
    return Decimal(str(value)).quantize(Decimal("0.01"))


def parse_time(value):
    return datetime.strptime(value.strip(), DT_FORMAT)


def read_csv(filename):
    with open(filename, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(filename, headers, rows):
    OUTPUT_DIR.mkdir(exist_ok=True)
    with open(OUTPUT_DIR / filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def load_tags(filename=DATA_DIR / "tags.csv"):
    tags = {}
    for row in read_csv(filename):
        tag_id = row["tag_id"].strip()
        vehicle_class = row["registered_class"].strip()
        if vehicle_class not in RATES:
            raise ValueError(f"Unknown vehicle class for {tag_id}: {vehicle_class}")
        if tag_id in tags:
            raise ValueError(f"Duplicate tag ID: {tag_id}")
        balance = money(row["opening_balance"])
        tags[tag_id] = {
            **row,
            "tag_id": tag_id,
            "registered_class": vehicle_class,
            "opening_balance": balance,
            "balance": balance,
            "local_resident": row["local_resident"].strip().lower() == "true",
            "exempt": row["exempt"].strip().lower() == "true",
            "blacklisted": False,
            "reverify": False,
            "crossings": 0,
            "fare_charged": Decimal("0.00"),
            "penalties": Decimal("0.00"),
            "cash_paid": Decimal("0.00"),
            "recharges": Decimal("0.00"),
        }
    return tags


def class_rate(vehicle_class):
    return RATES[vehicle_class]


def pass_purchase(tag, pass_type, when):
    last_day = calendar.monthrange(when.year, when.month)[1]
    valid_to = when.replace(day=last_day, hour=23, minute=59, second=59)
    if pass_type == "MONTHLY_LOCAL":
        if tag["registered_class"] != "CAR" or not tag["local_resident"]:
            return None
        price = Decimal("330.00")
        trips = None
    elif pass_type == "TRIP_50":
        price = class_rate(tag["registered_class"]) * 30
        trips = 50
    else:
        return None
    return {"type": pass_type, "valid_from": when, "valid_to": valid_to,
            "remaining": trips, "price": price}


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    commands_file = DATA_DIR / "commands.txt"
    if not commands_file.exists():
        raise FileNotFoundError("Missing data/commands.txt")

    tags = {}
    passes = defaultdict(list)
    crossing_times = defaultdict(list)
    last_read_by_lane = {}
    daily = defaultdict(lambda: {
        "reads": 0, "duplicates_ignored": 0, "exempt_crossings": 0,
        "pass_crossings": 0, "paid_crossings": 0,
        "tag_collection": Decimal("0.00"), "cash_collection": Decimal("0.00"),
        "penalties": Decimal("0.00")
    })
    read_logs = []
    recharge_logs = []
    pass_logs = []
    read_results = {}

    commands = []
    with open(commands_file, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                commands.append(line.split("|"))

    for command in commands:
        name = command[0].strip()
        if name == "LOAD_TAGS":
            path = DATA_DIR / command[1].strip()
            tags = load_tags(path)
            print(f"Loaded {len(tags)} tags.")
        elif name == "PROCESS_EVENTS":
            if not tags:
                raise RuntimeError("Run LOAD_TAGS before PROCESS_EVENTS.")
            reads = read_csv(DATA_DIR / command[1].strip())
            recharges = read_csv(DATA_DIR / command[2].strip())
            purchases = read_csv(DATA_DIR / command[3].strip())

            events = []
            for index, row in enumerate(reads):
                events.append((parse_time(row["timestamp"]), 2, index, "READ", row))
            for index, row in enumerate(recharges):
                events.append((parse_time(row["timestamp"]), 1, index, "RECHARGE", row))
            for index, row in enumerate(purchases):
                events.append((parse_time(row["timestamp"]), 0, index, "PASS", row))
            events.sort(key=lambda e: (e[0], e[1], e[2]))

            for when, priority, index, event_type, row in events:
                tag_id = row["tag_id"].strip()
                tag = tags.get(tag_id)
                if tag is None:
                    if event_type == "READ":
                        read_results[index] = {
                            "timestamp": row["timestamp"], "tag_id": tag_id,
                            "lane": row["lane"], "registered_class": "",
                            "detected_class": row["detected_class"], "outcome": "DUPLICATE_IGNORED",
                            "fare": "0.00", "penalty": "0.00", "balance_after": "0.00",
                            "flags": "UNKNOWN_TAG"
                        }
                    continue

                day = when.strftime("%Y-%m-%d")
                d = daily[day]

                if event_type == "PASS":
                    pass_type = row["pass_type"].strip()
                    new_pass = pass_purchase(tag, pass_type, when)
                    if new_pass:
                        passes[tag_id].append(new_pass)
                        status, price = "SOLD", new_pass["price"]
                        d["cash_collection"] += price
                    else:
                        status, price = "REJECTED", Decimal("0.00")
                    last_day = calendar.monthrange(when.year, when.month)[1]
                    valid_to = when.replace(day=last_day, hour=23, minute=59, second=59)
                    pass_logs.append({
                        "timestamp": row["timestamp"], "tag_id": tag_id,
                        "pass_type": pass_type, "status": status,
                        "price": f"{price:.2f}",
                        "valid_from": when.strftime("%Y-%m-%d") if status == "SOLD" else "",
                        "valid_to": valid_to.strftime("%Y-%m-%d") if status == "SOLD" else ""
                    })

                elif event_type == "RECHARGE":
                    amount = money(row["amount"])
                    if amount < 100:
                        status = "REJECTED_MINIMUM"
                    else:
                        status = "OK"
                        tag["balance"] += amount
                        tag["recharges"] += amount
                        if tag["balance"] > 0:
                            tag["blacklisted"] = False
                    recharge_logs.append({
                        "timestamp": row["timestamp"], "tag_id": tag_id,
                        "amount": f"{amount:.2f}", "status": status,
                        "balance_after": f'{tag["balance"]:.2f}'
                    })

                else:  # READ
                    d["reads"] += 1
                    lane_key = (tag_id, row["lane"].strip())
                    previous = last_read_by_lane.get(lane_key)
                    duplicate = previous is not None and timedelta(0) <= when - previous < timedelta(minutes=2)
                    if duplicate:
                        d["duplicates_ignored"] += 1
                        result = {
                            "timestamp": row["timestamp"], "tag_id": tag_id,
                            "lane": row["lane"], "registered_class": tag["registered_class"],
                            "detected_class": row["detected_class"], "outcome": "DUPLICATE_IGNORED",
                            "fare": "0.00", "penalty": "0.00",
                            "balance_after": f'{tag["balance"]:.2f}', "flags": ""
                        }
                        read_results[index] = result
                        continue
                    last_read_by_lane[lane_key] = when

                    flags = []
                    fare = Decimal("0.00")
                    penalty = Decimal("0.00")
                    outcome = "SINGLE"
                    detected = row["detected_class"].strip()
                    registered = tag["registered_class"]

                    if tag["exempt"]:
                        outcome = "EXEMPT"
                        d["exempt_crossings"] += 1
                    elif tag["blacklisted"]:
                        outcome = "CASH_BLACKLISTED"
                        fare = class_rate(registered) * 2
                        tag["cash_paid"] += fare
                        d["cash_collection"] += fare
                        flags.append("BLACKLISTED")
                        d["paid_crossings"] += 1
                    else:
                        # A mismatch to a higher class uses that class rate plus Rs.100.
                        effective_class = registered
                        if detected in CLASS_ORDER and CLASS_ORDER.index(detected) > CLASS_ORDER.index(registered):
                            effective_class = detected
                            penalty = Decimal("100.00")
                            tag["reverify"] = True
                            flags.append("MISMATCH")
                        # Lower detected class is ignored.
                        active = None
                        for p in reversed(passes[tag_id]):
                            if p["valid_from"] <= when <= p["valid_to"]:
                                if p["type"] == "MONTHLY_LOCAL" or p["remaining"] > 0:
                                    active = p
                                    break
                        if active:
                            if active["type"] == "TRIP_50":
                                active["remaining"] -= 1
                            outcome = "PASS"
                            d["pass_crossings"] += 1
                        else:
                            history = crossing_times[tag_id]
                            while history and when - history[0] > timedelta(hours=24):
                                history.pop(0)
                            if len(history) == 1:
                                fare = class_rate(effective_class) / 2
                                outcome = "RETURN"
                            else:
                                fare = class_rate(effective_class)
                                outcome = "SINGLE"
                            history.append(when)
                            tag["balance"] -= fare + penalty
                            tag["fare_charged"] += fare
                            tag["penalties"] += penalty
                            d["tag_collection"] += fare
                            d["penalties"] += penalty
                            d["paid_crossings"] += 1
                            if tag["balance"] < 0:
                                tag["blacklisted"] = True
                                flags.append("BLACKLISTED")
                            if tag["balance"] < 2 * class_rate(registered):
                                flags.append("LOW_BALANCE")

                    tag["crossings"] += 1
                    if tag["exempt"]:
                        pass
                    read_results[index] = {
                        "timestamp": row["timestamp"], "tag_id": tag_id,
                        "lane": row["lane"], "registered_class": registered,
                        "detected_class": detected, "outcome": outcome,
                        "fare": f"{fare:.2f}", "penalty": f"{penalty:.2f}",
                        "balance_after": f'{tag["balance"]:.2f}',
                        "flags": ";".join(flags)
                    }

            # Preserve original reads.csv order in read_log.csv.
            read_logs = [read_results[i] for i in range(len(reads))]
            write_csv("read_log.csv",
                ["timestamp", "tag_id", "lane", "registered_class", "detected_class",
                 "outcome", "fare", "penalty", "balance_after", "flags"], read_logs)
            write_csv("recharge_log.csv",
                ["timestamp", "tag_id", "amount", "status", "balance_after"], recharge_logs)
            write_csv("pass_log.csv",
                ["timestamp", "tag_id", "pass_type", "status", "price", "valid_from", "valid_to"], pass_logs)
            print(f"Processed {len(reads)} reads, {len(recharges)} recharges and {len(purchases)} pass requests.")

        elif name == "PRINT_DAILY_COLLECTION":
            start = datetime.strptime(command[1], "%Y-%m-%d").date()
            end = datetime.strptime(command[2], "%Y-%m-%d").date()
            rows = []
            current = start
            while current <= end:
                key = current.isoformat()
                x = daily[key]
                total = x["tag_collection"] + x["cash_collection"] + x["penalties"]
                rows.append({
                    "date": key, "reads": x["reads"],
                    "duplicates_ignored": x["duplicates_ignored"],
                    "exempt_crossings": x["exempt_crossings"],
                    "pass_crossings": x["pass_crossings"],
                    "paid_crossings": x["paid_crossings"],
                    "tag_collection": f'{x["tag_collection"]:.2f}',
                    "cash_collection": f'{x["cash_collection"]:.2f}',
                    "penalties": f'{x["penalties"]:.2f}',
                    "total_collection": f'{total:.2f}'
                })
                current += timedelta(days=1)
            write_csv("daily_collection.csv",
                ["date", "reads", "duplicates_ignored", "exempt_crossings", "pass_crossings",
                 "paid_crossings", "tag_collection", "cash_collection", "penalties",
                 "total_collection"], rows)
            print(f"Created daily_collection.csv ({len(rows)} days).")

        elif name == "PRINT_STATEMENTS":
            month = command[1].strip()
            rows = []
            for tag_id in sorted(tags):
                tag = tags[tag_id]
                # This sample command requests October 2026; balances are the final
                # balances after all events in the processed month.
                has_pass = any(p["valid_from"].strftime("%Y-%m") == month and
                               p["valid_to"] >= p["valid_from"] for p in passes[tag_id])
                if tag["blacklisted"]:
                    status = "BLACKLISTED"
                elif tag["reverify"]:
                    status = "REVERIFY"
                elif has_pass:
                    status = "ACTIVE_PASS"
                else:
                    status = "ACTIVE"
                rows.append({
                    "month": month, "tag_id": tag_id,
                    "registered_class": tag["registered_class"],
                    "opening_balance": f'{tag["opening_balance"]:.2f}',
                    "crossings": tag["crossings"],
                    "fare_charged": f'{tag["fare_charged"]:.2f}',
                    "penalties": f'{tag["penalties"]:.2f}',
                    "cash_paid": f'{tag["cash_paid"]:.2f}',
                    "recharges": f'{tag["recharges"]:.2f}',
                    "closing_balance": f'{tag["balance"]:.2f}',
                    "status": status
                })
            write_csv("statements.csv",
                ["month", "tag_id", "registered_class", "opening_balance", "crossings",
                 "fare_charged", "penalties", "cash_paid", "recharges",
                 "closing_balance", "status"], rows)
            print(f"Created statements.csv ({len(rows)} tags).")
        else:
            raise ValueError(f"Unknown command: {name}")

    print("\nAll requested processing commands completed.")
    print("Output files are in:", OUTPUT_DIR)


if __name__ == "__main__":
    main()
