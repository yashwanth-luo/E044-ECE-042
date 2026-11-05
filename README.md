# ECE-042 – Electronic Toll RFID Tag Account Engine for a Single Plaza — Sample Data Pack

Prepared by 10 SECONDS for Team E044.

## Files

| File | What it holds | Row count |
|---|---|---|
| `tags.csv` | Registered RFID tags | 500 |
| `reads.csv` | Plaza reads for October 2026 | 5404 |
| `recharges.csv` | Recharges | 146 |
| `passes.csv` | Monthly pass purchase requests (paid in cash at the plaza office) | 61 |
| `commands.txt` | Commands to process, in file order (comment lines start with #) | 4 commands |

Volumes in this sample are reduced for email delivery; the hidden evaluation set is larger and uses the same schema.

## Column reference

Conventions: dates `YYYY-MM-DD`; timestamps `YYYY-MM-DD HH:MM:SS` (24h, IST, no timezone suffix); money in Rs as plain decimals (no commas, no symbol); percentages as plain numbers (12.5 = 12.5%); booleans `true`/`false`; IDs uppercase with a fixed prefix.

### tags.csv
| column | type | units / format | allowed values | notes |
|---|---|---|---|---|
| tag_id | string | `TAG-nnnn` | unique | |
| vehicle_number | string | | | informational |
| owner_name | string | | | informational |
| registered_class | string | | CAR, LCV, BUS_TRUCK, MAV | single-trip rate 65 / 105 / 220 / 345 |
| opening_balance | decimal | Rs | | balance at 2026-10-01 00:00:00 |
| local_resident | boolean | | true/false | only true + CAR may buy MONTHLY_LOCAL |
| exempt | boolean | | true/false | fare 0, crossing still logged |

### reads.csv
| column | type | units / format | allowed values | notes |
|---|---|---|---|---|
| timestamp | timestamp | YYYY-MM-DD HH:MM:SS | Oct 2026 | sorted ascending |
| tag_id | string | | from tags.csv | |
| lane | string | | L1–L6 | duplicate suppression is per tag per lane within 2 minutes |
| detected_class | string | | CAR, LCV, BUS_TRUCK, MAV | compare with registered_class |

### recharges.csv
| column | type | units / format | allowed values | notes |
|---|---|---|---|---|
| timestamp | timestamp | | | |
| tag_id | string | | from tags.csv | |
| amount | decimal | Rs | | minimum 100; one planted 50.00 |

### passes.csv
| column | type | units / format | allowed values | notes |
|---|---|---|---|---|
| timestamp | timestamp | | | purchase time; pass valid from this moment to month end |
| tag_id | string | | from tags.csv | |
| pass_type | string | | MONTHLY_LOCAL, TRIP_50 | price per rules (330, or 30 × single rate); paid in cash, tag balance unchanged |

## Command file format

One command per line, `COMMAND_NAME|arg1|...`; lines starting with `#` are comments. Commands must be processed in file order.

| command | arguments | meaning |
|---|---|---|
| `LOAD_TAGS` | file | register tags with opening balances |
| `PROCESS_EVENTS` | reads file, recharges file, passes file | merge the three files into one stream ordered by timestamp (ties: PASS, then RECHARGE, then READ) and process every event |
| `PRINT_DAILY_COLLECTION` | from date, to date | one line per day |
| `PRINT_STATEMENTS` | YYYY-MM | per-tag monthly statement |

## Planted scenarios

Every edge case in the brief (EC1…) plus extra traps (TRAP1…). Line numbers count the header as line 1.

- **EC1** – Return crossing exactly 24 hours after the first — TAG-0090 crosses at 08:15:00 on 8 Oct and exactly 24 h later; no other crossing in between → `reads.csv` line 1272 (2026-10-08 08:15:00); `reads.csv` line 1457 (2026-10-09 08:15:00)
- **EC2** – Balance exactly equal to the fare — CAR tag with opening balance 65.00 = fare; first read leaves 0.00 (allowed, LOW_BALANCE); the next read goes negative → BLACKLISTED → `tags.csv` line 207 (TAG-0206)
- **EC3** – Local-resident pass bought mid-month (valid only till month end, full price) — TAG-0236 (local CAR) buys MONTHLY_LOCAL on 15 Oct: full 330, valid 15–31 Oct only → `passes.csv` line 62 (2026-10-15 09:40:00)
- **EC4** – Blacklisted tag recharged to exactly Rs 0 — MAV with 245.00 → first read −100.00 (BLACKLISTED); recharge of 100.00 brings it to exactly 0.00 (not positive, stays blacklisted); a later 500.00 recharge restores it → `tags.csv` line 217 (TAG-0216)
- **EC5** – Mismatch read on an exempt tag — exempt LCV tag with one read detected as BUS_TRUCK — fare stays 0; whether the Rs 100 penalty/re-verification flag applies is not stated: document your choice → `tags.csv` line 219 (TAG-0218)
- **TRAP1** – non-local CAR tag requests MONTHLY_LOCAL → reject → `passes.csv` line 61 (TAG-0254)
- **TRAP2** – BUS_TRUCK with a 50-trip pass crossing more than 50 times → crossings beyond 50 are charged → `tags.csv` line 341 (TAG-0340)
- **TRAP3** – duplicate read +45 s in the same lane (ignore) and a read +120 s in the same lane (boundary of the 2-minute window) → `tags.csv` line 112 (TAG-0111)
- **TRAP4** – registered BUS_TRUCK read as LCV (lower class) → ignored, BUS_TRUCK rate → `tags.csv` line 369 (TAG-0368)
- **TRAP5** – recharge of 50.00 → below the Rs 100 minimum, reject → `recharges.csv` line 18 (2026-10-06 12:30:00)
- **TRAP6** – 40 reads with detected class higher than registered (higher rate + Rs 100 penalty + re-verification flag) — first one at this timestamp → `reads.csv` line 253 (2026-10-02 11:58:45)
- **TRAP7** – 25 planted tags go negative at least once (24 NEG tags that recharge only after going negative, plus EC4); also TAG-0206 (EC2) goes negative — first NEG tag by id → `tags.csv` line 11 (TAG-0010)
- **TRAP8** – events from the three files must be merged by timestamp before processing (PASS, then RECHARGE, then READ on equal timestamps) → `reads.csv` line 1

## What is NOT in this pack

Expected outputs are not provided for this set. Validate your engine with your own test suite against the rules in your brief (BR-01 … BR-nn). A separate hidden input set with the same schema will be used at final evaluation; outputs are compared field-for-field, so follow the column formats above exactly in your own output.

## Output format expected at evaluation

**`read_log.csv`** — one row per read in reads.csv order:
`timestamp, tag_id, lane, registered_class, detected_class, outcome, fare, penalty, balance_after, flags`
- outcome = SINGLE / RETURN / PASS / EXEMPT / CASH_BLACKLISTED / DUPLICATE_IGNORED; flags = semicolon-joined subset of LOW_BALANCE, BLACKLISTED, MISMATCH (blank when none); balance_after unchanged for CASH and DUPLICATE rows.

**`recharge_log.csv`** — `timestamp, tag_id, amount, status, balance_after` (status = OK / REJECTED_MINIMUM).

**`pass_log.csv`** — `timestamp, tag_id, pass_type, status, price, valid_from, valid_to` (status = SOLD / REJECTED; dates YYYY-MM-DD).

**`daily_collection.csv`** — `date, reads, duplicates_ignored, exempt_crossings, pass_crossings, paid_crossings, tag_collection, cash_collection, penalties, total_collection`.

**`statements.csv`** — one row per tag, sorted by tag_id:
`month, tag_id, registered_class, opening_balance, crossings, fare_charged, penalties, cash_paid, recharges, closing_balance, status` (status = ACTIVE / BLACKLISTED / REVERIFY / ACTIVE_PASS).
