# E044-ECE-042: Electronic Toll RFID Tag Account Engine

## 1. Project Overview

This project is an Electronic Toll RFID Tag Account Engine for a Single Plaza.

It processes vehicle RFID reads, calculates toll charges, manages tag balances, handles recharges and monthly passes, and generates collection reports.

**Team ID:** E044  
**Problem Statement:** ECE-042  
**Programming Language:** Python 3.10+  
**Interface:** Command-line / CSV based

## 2. Project Objectives

- Register and manage RFID tags.
- Calculate toll charges based on vehicle class.
- Apply return-trip discounts.
- Process monthly and 50-trip passes.
- Handle recharges and low balances.
- Identify blacklisted tags.
- Detect vehicle-class mismatches.
- Ignore duplicate reads.
- Generate daily collection and monthly statements.

## 3. Technology Used

- Python
- CSV files for input and output
- VS Code
- Git and GitHub for version control

## 4. Project Folder Structure

```text
E044-ECE-042/
│
├── data/
│   ├── tags.csv
│   ├── reads.csv
│   ├── recharges.csv
│   ├── passes.csv
│   └── commands.txt
│
├── src/
│   └── main.py
│
├── tests/
│   └── validate_outputs.py
│
├── output/
│   ├── read_log.csv
│   ├── recharge_log.csv
│   ├── pass_log.csv
│   ├── daily_collection.csv
│   └── statements.csv
│
└── README.md
```

## 5. Toll Rates

| Vehicle Class | Toll Rate |
|---|---:|
| CAR | Rs. 65 |
| LCV | Rs. 105 |
| BUS_TRUCK | Rs. 220 |
| MAV | Rs. 345 |

## 6. Main Business Rules

1. A second crossing within 24 hours receives a 50% return-trip discount.
2. A monthly local pass costs Rs. 330 for eligible local CAR tags.
3. A 50-trip pass costs 30 times the single-trip rate.
4. The minimum recharge amount is Rs. 100.
5. Tags with negative balances are blacklisted.
6. Blacklisted tags pay double the normal toll in cash.
7. Higher detected vehicle classes attract a Rs. 100 penalty and re-verification.
8. Lower detected classes do not reduce the registered-class toll.
9. Duplicate reads within two minutes in the same lane are ignored.
10. Exempt tags are not charged toll fees.

## 7. How to Run the Project

Open the project folder in VS Code.

Run the following command in the terminal:

```powershell
python src/main.py
```

The program reads the commands from `data/commands.txt`, processes the input CSV files and generates output reports in the `output` folder.

## 8. Output Files

| Output File | Description |
|---|---|
| read_log.csv | Details of vehicle reads and toll charges |
| recharge_log.csv | Recharge transactions |
| pass_log.csv | Pass purchase records |
| daily_collection.csv | Daily toll collection summary |
| statements.csv | Monthly tag account statements |

## 9. Run Validation Tests

Run:

```powershell
python tests/validate_outputs.py
```

The validation script checks selected business rules and verifies output record counts.

## 10. Conclusion

The project demonstrates how an RFID-based electronic toll system can automate toll collection, manage tag accounts, process vehicle crossings and generate financial reports using Python and CSV files.
