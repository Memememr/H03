import threading
import time
from test_env import get_connection

ISOLATION_LEVELS = [
    "READ UNCOMMITTED",
    "READ COMMITTED",
    "REPEATABLE READ",
    "SERIALIZABLE"
]

CURRENT_ISOLATION_LEVEL = "READ UNCOMMITTED"

first_read_done = threading.Event()
writer_finished = threading.Event()

writer_error = []
start_time = time.monotonic()


def log(message):
    elapsed = time.monotonic() - start_time
    print(f"[{elapsed:6.2f}s] {message}", flush=True)


def get_row_count():
    """Read total count of rows in inventory_test using a separate connection."""
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM inventory_test")
        return cursor.fetchone()[0]
    finally:
        cursor.close()
        connection.close()


def cleanup_inserted_row():
    """Remove item_id = 6 so the table is reset for the next run."""
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("DELETE FROM inventory_test WHERE item_id = 6")
        connection.commit()
    except Exception as error:
        log(f"CLEANUP ERROR: {error}")
    finally:
        cursor.close()
        connection.close()


def transaction_1_reader():
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        connection.start_transaction(
            isolation_level=CURRENT_ISOLATION_LEVEL
        )

        log("T1: Transaction started.")

        cursor.execute("SELECT * FROM inventory_test")
        first_rows = cursor.fetchall()
        log(f"T1: 1st Read count = {len(first_rows)} rows")

        first_read_done.set()

        if not writer_finished.wait(timeout=15):
            raise TimeoutError("T2 did not finish writing.")

        cursor.execute("SELECT * FROM inventory_test")
        second_rows = cursor.fetchall()
        log(f"T1: 2nd Read count = {len(second_rows)} rows")

        if len(second_rows) > len(first_rows):
            log("RESULT: PHANTOM READ DETECTED!")
        else:
            log("RESULT: Phantom read not detected.")

        connection.commit()
        log("T1: COMMIT executed.")

    except Exception as error:
        if connection is not None:
            connection.rollback()
        log(f"T1 ERROR: {error}")

    finally:
        first_read_done.set()
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


def transaction_2_writer():
    connection = None
    cursor = None

    try:
        if not first_read_done.wait(timeout=15):
            raise TimeoutError("T1 did not finish its first read.")

        connection = get_connection()
        cursor = connection.cursor()

        connection.start_transaction(
            isolation_level=CURRENT_ISOLATION_LEVEL
        )

        log("T2: Transaction started.")

        cursor.execute("""
            INSERT INTO inventory_test (item_id, item_name, quantity, price)
            VALUES (%s, %s, %s, %s)
        """, (6, 'DVD Romance Movie', 67, 9.99))

        log("T2: Inserted 'DVD Romance Movie', quantity=67, price=9.99.")

        connection.commit()
        log("T2: COMMIT executed.")

    except Exception as error:
        writer_error.append(str(error))
        if connection is not None:
            connection.rollback()
        log(f"T2 ERROR: {error}")

    finally:
        writer_finished.set()
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    for level in ISOLATION_LEVELS:
        CURRENT_ISOLATION_LEVEL = level

        first_read_done.clear()
        writer_finished.clear()
        writer_error.clear()
        start_time = time.monotonic()

        cleanup_inserted_row()

        print(f"\n==================================================")
        print(f"=== PHANTOM READ EXPERIMENT: {CURRENT_ISOLATION_LEVEL} ===")
        print(f"==================================================\n")

        initial_count = get_row_count()
        log(f"Initial row count = {initial_count}")

        thread_1 = threading.Thread(target=transaction_1_reader)
        thread_2 = threading.Thread(target=transaction_2_writer)

        thread_1.start()
        thread_2.start()

        thread_1.join()
        thread_2.join()

        final_count = get_row_count()
        print(f"\nFinal row count = {final_count}")

    cleanup_inserted_row()
    print("\n=== ALL ISOLATION LEVEL EXPERIMENTS FINISHED ===\n")