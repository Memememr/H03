import threading
import time

from test_env import get_connection


# ============================================================
# DIRTY READ - READ UNCOMMITTED
# ============================================================

ISOLATION_LEVEL = "READ UNCOMMITTED"

writer_updated = threading.Event()
reader_finished = threading.Event()

start_time = time.monotonic()


def log(message):
    elapsed = time.monotonic() - start_time
    print(f"[{elapsed:6.2f}s] {message}", flush=True)


def transaction_1_writer():
    """Updates the quantity without committing."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        connection.isolation_level = ISOLATION_LEVEL
        connection.start_transaction()

        log("T1: Transaction started.")

        cursor.execute("""
            UPDATE inventory_test
            SET quantity = 50
            WHERE item_id = 1
        """)

        log("T1: Updated quantity from 10 to 50 (uncommitted).")

        # Tell T2 that the update is ready to be read.
        writer_updated.set()

        # Keep the uncommitted change until T2 reads it.
        reader_finished.wait()

        connection.rollback()
        log("T1: ROLLBACK executed. Quantity restored to 10.")

    except Exception as error:
        connection.rollback()
        log(f"T1 ERROR: {error}")

    finally:
        cursor.close()
        connection.close()


def transaction_2_reader():
    """Attempts to read T1's uncommitted update."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        connection.isolation_level = ISOLATION_LEVEL

        # Wait until T1 has performed its UPDATE.
        writer_updated.wait()

        connection.start_transaction()
        log("T2: Transaction started.")

        cursor.execute("""
            SELECT quantity
            FROM inventory_test
            WHERE item_id = 1
        """)

        result = cursor.fetchone()

        log(f"T2: Read quantity = {result[0]}")

        if result[0] == 50:
            log("RESULT: DIRTY READ DETECTED!")
        else:
            log("RESULT: Dirty read not detected.")

        connection.commit()
        log("T2: COMMIT executed.")

    except Exception as error:
        connection.rollback()
        log(f"T2 ERROR: {error}")

    finally:
        reader_finished.set()
        cursor.close()
        connection.close()


# ============================================================
# RUN CONCURRENT TRANSACTIONS
# ============================================================

if __name__ == "__main__":

    print("\n=== DIRTY READ: READ UNCOMMITTED ===\n")

    thread_1 = threading.Thread(target=transaction_1_writer)
    thread_2 = threading.Thread(target=transaction_2_reader)

    thread_1.start()
    thread_2.start()

    thread_1.join()
    thread_2.join()

    print("\n=== EXPERIMENT FINISHED ===\n")
