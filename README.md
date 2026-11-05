# Database Isolation Levels — Hands-On Activity

A Python and MySQL project exploring how database isolation levels and locking mechanisms affect concurrent transactions, data consistency, and transaction performance.

## Overview

This project investigates how different database isolation levels maintain transaction integrity when multiple transactions access and modify the same data simultaneously.

The experiments focus on three common concurrency problems:

1. **Dirty Read** – A transaction reads changes made by another transaction that have not yet been committed.
2. **Non-Repeatable Read** – A transaction reads the same row twice but gets different values because another transaction modified and committed the row in between.
3. **Phantom Read** – A transaction runs the same query twice but gets a different number of rows because another transaction inserted or deleted matching records.

The project also explores how locking mechanisms can prevent concurrency problems and how they affect transaction performance.

## Project Objectives

- Demonstrate the three common read anomalies using concurrent transactions.
- Compare the behavior of four database isolation levels.
- Identify which concurrency problems are prevented or allowed by each isolation level.
- Experiment with row-level and explicit table locking mechanisms.
- Observe the effects of isolation levels and locks on transaction execution and performance.
- Understand the trade-offs between data consistency and transaction concurrency.

## Experiments

### 1. Baseline Experiments

The baseline experiments consist of 12 cases:

| Read Anomaly | READ UNCOMMITTED | READ COMMITTED | REPEATABLE READ | SERIALIZABLE |
|---|---|---|---|---|
| Dirty Read | DR-01 | DR-02 | DR-03 | DR-04 |
| Non-Repeatable Read | NR-01 | NR-02 | NR-03 | NR-04 |
| Phantom Read | PR-01 | PR-02 | PR-03 | PR-04 |

Each experiment uses two concurrent transactions to demonstrate how the selected isolation level handles a specific read anomaly.

### 2. Locking Experiments

At least four additional experiments investigate how locking mechanisms affect concurrent transactions.

Each experiment corresponds to one of the four isolation levels.

The experiments may use:
- Row-level locking, such as `SELECT ... FOR UPDATE`.
- Explicit table locking, such as `LOCK TABLES`.

The objective is to observe how locks prevent conflicting operations and how they affect waiting time, execution time, and concurrency.

## Project Structure

```text
H03/
│
├── dirty_read_experiment.py
├── non_repeatable_read_experiment.py
├── phantom_read_experiment.py
├── locking_experiment.py
│
├── test_env.py
├── schema.sql
├── requirements.txt
├── README.md
└── .gitignore
```

Each experiment script uses a configurable isolation level. Instead of maintaining four separate scripts for the same read anomaly, users can change the isolation-level setting and rerun the experiment.

The locking experiments are handled separately because they investigate additional locking behavior.

## Prerequisites

Before running the experiments, make sure you have:

- Python 3.10 or later
- MySQL Server 8.0 or later
- MySQL Workbench (recommended)
- Visual Studio Code or another Python editor

The database table must use the **InnoDB storage engine**, since InnoDB supports transactions and row-level locking.

## Installation and Setup

### 1. Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd H03
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
venv\Scripts\activate
```

### 3. Install the required package

```bash
python -m pip install -r requirements.txt
```

### 4. Set up the database

Open MySQL Workbench and execute the contents of `schema.sql`.

This creates the `isolation_lab` database and the `inventory_test` table.

The table is based on a simplified inventory scenario with four columns:

| Column | Data Type | Description |
|---|---|---|
| item_id | INT | Unique identifier for each item |
| item_name | VARCHAR(50) | Name of the item |
| quantity | INT | Available item quantity |
| price | DECIMAL(10,2) | Item price |

**Important:** The schema script drops and recreates the `inventory_test` table. Only execute it when you intend to reset the experiment data.

### 5. Configure the database connection

Open `test_env.py` and configure your local MySQL credentials.

```python
import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_MYSQL_PASSWORD",
    "database": "isolation_lab"
}

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)
```

Replace `YOUR_MYSQL_PASSWORD` with your own MySQL password.

Do not commit your actual database password to the repository. Keep the shared version configured with placeholder credentials.

## Running the Experiments

### 1. Choose an isolation level

Open the Python script for the experiment you want to run.

Find its isolation-level configuration:

```python
ISOLATION_LEVEL = "READ UNCOMMITTED"
```

Change the value to one of the following:

| Isolation Level | Configuration |
|---|---|
| READ UNCOMMITTED | `"READ UNCOMMITTED"` |
| READ COMMITTED | `"READ COMMITTED"` |
| REPEATABLE READ | `"REPEATABLE READ"` |
| SERIALIZABLE | `"SERIALIZABLE"` |

### 2. Run the experiment

Make sure your terminal is inside the project root folder.

For example, to run the Dirty Read experiment:

```powershell
python dirty_read_experiment.py
```

To run the other experiments:

```powershell
python non_repeatable_read_experiment.py
```

```powershell
python phantom_read_experiment.py
```

```powershell
python locking_experiment.py
```

### 3. Repeat using other isolation levels

Change the `ISOLATION_LEVEL` configuration and execute the same script again.

There is no need to create separate scripts for each isolation level.

**Note:** Run experiments one at a time to avoid interference between test transactions.

## Understanding the Results

For each experiment, observe:

- The operations performed by Transaction 1 and Transaction 2.
- The order in which the transactions execute.
- The values read or modified by each transaction.
- Whether a read anomaly occurs.
- Whether a transaction has to wait for another transaction.
- The final state of the database.
- The execution time and any noticeable waiting caused by locks.

The expected behavior should be compared with the actual terminal output. Do not assume that an experiment produced the expected result without running and verifying it.

## Locking and Performance

The locking experiments investigate how database locks help maintain data consistency.

Consider the following when analyzing the results:

- **Row-level locks:** Restrict access to specific rows while a transaction holds the lock.
- **Table locks:** Restrict access at the table level, potentially affecting more transactions.
- **Waiting time:** Measures how long a transaction waits for another transaction to release a lock.
- **Concurrency:** Examines how many transactions can proceed simultaneously.
- **Performance:** Considers the execution time and overhead introduced by locking.

The goal is to understand the trade-off between preventing conflicting operations and allowing transactions to execute concurrently.


## Technologies Used

- Python
- MySQL 8.0
- InnoDB Storage Engine
- MySQL Connector/Python
- Python Threading

## References

- [MySQL 8.0 Reference Manual — InnoDB Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.0/en/innodb-transaction-isolation-levels.html)
- [MySQL 8.0 Reference Manual — InnoDB Locking](https://dev.mysql.com/doc/refman/8.0/en/innodb-locking.html)
- [MySQL 8.0 Reference Manual — LOCK TABLES](https://dev.mysql.com/doc/refman/8.0/en/lock-tables.html)
- [MySQL Connector/Python Documentation](https://dev.mysql.com/doc/connector-python/en/)

---