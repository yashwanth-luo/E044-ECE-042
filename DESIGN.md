# SYSTEM DESIGN DOCUMENT

## Project: Electronic Toll RFID Tag Account Engine

**Team ID:** E044  
**Problem Statement:** ECE-042  
**Language:** Python

## 1. Introduction

The system automates toll collection using RFID tags. It reads vehicle information, calculates toll charges, updates account balances and generates reports.

## 2. System Architecture

The system follows a modular, command-driven architecture.

**Input CSV Files → Data Loading → Event Processing → Toll Calculation → Account Update → Output Reports**

## 3. Input Modules

The system uses five input files:

- `tags.csv` – registered vehicle and RFID tag details.
- `reads.csv` – vehicle crossing information.
- `recharges.csv` – tag recharge transactions.
- `passes.csv` – pass purchase requests.
- `commands.txt` – commands to execute the system operations.

## 4. Main Processing Modules

### A. Tag Management
Loads registered tags and maintains vehicle details, registered class, account balance and tag status.

### B. Event Processing
Reads recharge, pass and vehicle crossing events and processes them in timestamp order.

### C. Toll Calculation
Calculates toll according to vehicle class and applies return-trip rules.

### D. Pass Management
Checks pass eligibility, validity and remaining trips.

### E. Account Management
Updates balances, processes recharges and handles blacklisted tags.

### F. Report Generation
Creates daily collection summaries and monthly tag statements.

## 5. Toll Calculation

| Vehicle Class | Toll |
|---|---:|
| CAR | Rs. 65 |
| LCV | Rs. 105 |
| BUS_TRUCK | Rs. 220 |
| MAV | Rs. 345 |

A second paid crossing within 24 hours receives a 50% discount.

## 6. Important Validations

- Invalid tag IDs.
- Invalid vehicle classes.
- Insufficient tag balance.
- Minimum recharge amount.
- Duplicate vehicle reads.
- Pass eligibility and validity.
- Vehicle-class mismatch.
- Blacklisted tag status.

## 7. Output Design

The system generates five CSV reports:

1. `read_log.csv`
2. `recharge_log.csv`
3. `pass_log.csv`
4. `daily_collection.csv`
5. `statements.csv`

## 8. Testing

The project includes a Python validation script to check selected business rules and output record counts.

## 9. Conclusion

The proposed system provides an automated approach to RFID toll processing, account management and collection reporting. It uses Python and CSV files to process toll plaza transactions.
