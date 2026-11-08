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
reader_finished = threading.Event()

writer_error = []
start_time = time.monotonic()


def log(message):
    elapsed = time.monotonic() - start_time
    print(f"[{elapsed:6.2f}s] {message}", flush=True)


def get_row_count():
    """Read total count of rows using a separate connection."""
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM inventory_test")
        return cursor.fetchone()[0]
    finally:
        cursor.close()
        connection.close()


def cleanup_inserted_row():
    """Remove item_id = 6 to reset table state."""
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


# ============================================================
# TRANSACTION 1 - READER (Classic Table Lock)
# ============================================================

def transaction_1_reader():
    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        connection.start_transaction(isolation_level=CURRENT_ISOLATION_LEVEL)
        log("T1: Transaction started.")

        # CLASSIC TABLE LOCK: Lock the entire table for reading
        cursor.execute("LOCK TABLES inventory_test READ")
        log("T1: LOCK TABLES inventory_test READ executed.")

        cursor.execute("SELECT * FROM inventory_test")
        first_rows = cursor.fetchall()
        log(f"T1: 1st Read count = {len(first_rows)} rows")

        # Allow T2 to attempt its INSERT
        first_read_done.set()

        # Simulate holding the table lock while T2 tries to insert
        time.sleep(2.0)

        cursor.execute("SELECT * FROM inventory_test")
        second_rows = cursor.fetchall()
        log(f"T1: 2nd Read count = {len(second_rows)} rows")

        if len(second_rows) > len(first_rows):
            log("RESULT: PHANTOM READ DETECTED!")
        else:
            log("RESULT: Phantom read prevented via Table Lock.")

        # RELEASE CLASSIC TABLE LOCK
        cursor.execute("UNLOCK TABLES")
        log("T1: UNLOCK TABLES executed.")

        connection.commit()
        log("T1: COMMIT executed.")

    except Exception as error:
        if connection is not None:
            # Always ensure locks are released on error
            try:
                cursor.execute("UNLOCK TABLES")
            except Exception:
                pass
            connection.rollback()
        log(f"T1 ERROR: {error}")

    finally:
        first_read_done.set()
        reader_finished.set()
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


# ============================================================
# TRANSACTION 2 - WRITER
# ============================================================

def transaction_2_writer():
    connection = None
    cursor = None

    try:
        if not first_read_done.wait(timeout=15):
            raise TimeoutError("T1 did not finish its first read.")

        connection = get_connection()
        cursor = connection.cursor()

        connection.start_transaction(isolation_level=CURRENT_ISOLATION_LEVEL)
        log("T2: Transaction started. Attempting INSERT...")

        # This INSERT will BLOCK until T1 runs UNLOCK TABLES
        cursor.execute("""
            INSERT INTO inventory_test (item_id, item_name, quantity, price)
            VALUES (%s, %s, %s, %s)
        """, (6, 'DVD Romance Movie', 67, 9.99))

        log("T2: INSERT successful (Unblocked by T1's UNLOCK TABLES).")

        connection.commit()
        log("T2: COMMIT executed.")

    except Exception as error:
        writer_error.append(str(error))
        if connection is not None:
            connection.rollback()
        log(f"T2 ERROR: {error}")

    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


# ============================================================
# RUN THE EXPERIMENT ACROSS ALL 4 ISOLATION LEVELS
# ============================================================

if __name__ == "__main__":
    for level in ISOLATION_LEVELS:
        CURRENT_ISOLATION_LEVEL = level

        first_read_done.clear()
        reader_finished.clear()
        writer_error.clear()
        start_time = time.monotonic()

        cleanup_inserted_row()

        print(f"\n==================================================")
        print(f"=== LOCKING EXPERIMENT PHANTOM READ: {CURRENT_ISOLATION_LEVEL} ===")
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
    print("\n=== ALL LOCKING EXPERIMENTS ON PHANTOM READ FINISHED ===\n")