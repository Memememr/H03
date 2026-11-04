# Database Isolation Levels — Hands-On Activity

A Python and MySQL project that demonstrates how different database transaction isolation levels affect concurrency problems, particularly **Dirty Reads**.

This project uses Python threading to simulate two concurrent database transactions: a writer and a reader. By changing the transaction isolation level, we can observe how MySQL handles uncommitted changes and prevents read anomalies.

## Project Overview

The experiments use a simplified inventory database based on the Sakila database concept.

**Database:** `isolation_lab`

**Table:** `inventory_test`

**Storage Engine:** InnoDB

**Technologies:**
- Python
- MySQL 8.0+
- InnoDB Storage Engine
- mysql-connector-python
- Python Threading

## Prerequisites

Before running the experiments, make sure you have:

- Python 3.10 or later
- MySQL Server 8.0 or later
- MySQL Workbench (recommended)
- Git

## 1. Clone the Repository

Clone the repository to your local machine:

```bash
git clone <repository-url>
```

## 2. Set Up a Virtual Environment (Recommended)

Create a Python virtual environment:

```bash
python -m venv venv
```

Activate it.

**Windows:**

```bash
venv\Scripts\activate
```

**macOS / Linux:**

```bash
source venv/bin/activate
```

## 3. Install Dependencies

Install the required Python packages:

```bash
python -m pip install -r requirements.txt
```

## 4. Set Up the Database

1. Open MySQL Workbench.
2. Open the `schema.sql` file.
3. Execute the entire SQL script.
4. Verify that the `isolation_lab` database was created.
5. Check that the `inventory_test` table contains five records.
6. Confirm that the table uses the InnoDB storage engine.

The database schema is automatically created by executing `schema.sql`.

**Important:** You only need to execute `schema.sql` during the initial setup. Running it again drops and recreates `inventory_test`, resetting all records to their original seed values.

## 5. Configure Database Credentials

Open `test_env.py` and configure your local MySQL credentials.

Example:

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_MYSQL_PASSWORD",
    "database": "isolation_lab"
}
```

Replace `YOUR_MYSQL_PASSWORD` with your own MySQL password.

**Note:** Each group member must configure their own local database credentials. Do not upload personal database passwords to GitHub.

## 6. Run the Experiments

Run the Python scripts from the project's root directory.

## Dirty Read Experiment

Each experiment uses two independent MySQL database connections.

**Transaction 1 — Writer**
- Starts a transaction.
- Updates the inventory quantity from `10` to `50`.
- Leaves the update uncommitted.
- Rolls back the transaction.

**Transaction 2 — Reader**
- Starts a concurrent transaction.
- Attempts to read the updated inventory quantity.
- Displays the value returned by MySQL.

The results demonstrate how each isolation level handles uncommitted changes.

## Important Notes

- Make sure MySQL Server is running before executing the scripts.
- Each transaction must use its own database connection.
- Run the experiments individually.
- Execute the SQL setup script before running the experiments for the first time.
- Do not execute `schema.sql` while an experiment is running.
- The scripts use Python threading events to coordinate transaction execution.
- Actual execution timestamps may vary depending on system performance and transaction scheduling.

## References

- [MySQL 8.0 Reference Manual](https://dev.mysql.com/doc/refman/8.0/en/)
- [InnoDB Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.0/en/innodb-transaction-isolation-levels.html)
- [Python Threading Documentation](https://docs.python.org/3/library/threading.html)
