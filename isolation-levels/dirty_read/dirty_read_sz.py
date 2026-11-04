
import threading
import time

from test_env import get_connection


# ============================================================
# DIRTY READ - SERIALIZABLE
# ============================================================

ISOLATION_LEVEL = "SERIALIZABLE"

writer_updated = threading.Event()
reader_attempting = threading.Event()

start_time = time.monotonic()


def log(message):
    elapsed = time.monotonic() - start_time
    print(f"[{elapsed:6.2f}s] {message}", flush=True)


def transaction_1_writer():

    connection = get_connection()
    cursor = connection.cursor()

    try:
        connection.start_transaction(
            isolation_level=ISOLATION_LEVEL
        )

        log("T1: Transaction started.")

        cursor.execute("""
            UPDATE inventory_test
            SET quantity = 50
            WHERE item_id = 1
        """)

        log("T1: Updated quantity from 10 to 50 (uncommitted).")

        writer_updated.set()

        # Wait until T2 is about to perform its SELECT.
        reader_attempting.wait()

        log("T1: Holding the row lock for 2 seconds.")
        time.sleep(2)

        connection.rollback()

        log("T1: ROLLBACK executed. Quantity restored to 10.")
        log("T1: Exclusive row lock released.")

    except Exception as error:
        connection.rollback()
        log(f"T1 ERROR: {error}")

    finally:
        cursor.close()
        connection.close()


def transaction_2_reader():

    connection = get_connection()
    cursor = connection.cursor()

    try:
        writer_updated.wait()

        connection.start_transaction(
            isolation_level=ISOLATION_LEVEL
        )

        log("T2: Transaction started.")

        reader_attempting.set()

        log("T2: Attempting SELECT. Waiting for T1's lock...")

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
            log("RESULT: Dirty read prevented.")

        connection.commit()
        log("T2: COMMIT executed.")

    except Exception as error:
        connection.rollback()
        log(f"T2 ERROR: {error}")

    finally:
        cursor.close()
        connection.close()


# ============================================================
# RUN CONCURRENT TRANSACTIONS
# ============================================================

if __name__ == "__main__":

    print("\n=== DIRTY READ: SERIALIZABLE ===\n")

    thread_1 = threading.Thread(target=transaction_1_writer)
    thread_2 = threading.Thread(target=transaction_2_reader)

    thread_1.start()
    thread_2.start()

    thread_1.join()
    thread_2.join()

    print("\n=== EXPERIMENT FINISHED ===\n")
