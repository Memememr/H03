
import threading
import time

from test_env import get_connection


# ============================================================
# CONFIGURATION
# Change this value in each of the four scripts.
# ============================================================

ISOLATION_LEVEL = "READ UNCOMMITTED"

ORIGINAL_QUANTITY = 10
UPDATED_QUANTITY = 50

writer_updated = threading.Event()
reader_attempting = threading.Event()
reader_finished = threading.Event()

writer_error = []

start_time = time.monotonic()


def log(message):
    elapsed = time.monotonic() - start_time
    print(f"[{elapsed:6.2f}s] {message}", flush=True)


def get_quantity():
    """Read the current quantity using a separate connection."""

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT quantity
            FROM inventory_test
            WHERE item_id = 1
        """)

        result = cursor.fetchone()

        if result is None:
            raise RuntimeError("Item with item_id = 1 was not found.")

        return result[0]

    finally:
        cursor.close()
        connection.close()


# ============================================================
# TRANSACTION 1 - WRITER
# Updates the quantity but does not commit.
# ============================================================

def transaction_1_writer():

    connection = None
    cursor = None

    try:
        connection = get_connection()
        cursor = connection.cursor()

        connection.start_transaction(
            isolation_level=ISOLATION_LEVEL
        )

        log("T1: Transaction started.")

        cursor.execute("""
            UPDATE inventory_test
            SET quantity = %s
            WHERE item_id = 1
        """, (UPDATED_QUANTITY,))

        if cursor.rowcount != 1:
            raise RuntimeError("Expected to update exactly one row.")

        log(
            f"T1: Updated quantity from {ORIGINAL_QUANTITY} "
            f"to {UPDATED_QUANTITY} (uncommitted)."
        )

        # Allow Transaction 2 to begin reading.
        writer_updated.set()

        if ISOLATION_LEVEL == "SERIALIZABLE":

            # Wait until T2 attempts its SELECT.
            if not reader_attempting.wait(timeout=15):
                raise TimeoutError("T2 did not attempt to read.")

            log("T1: T2 is attempting to read. Waiting briefly.")

            # Give T2 time to reach the database and encounter the lock.
            time.sleep(1.5)

        else:

            # Keep the update uncommitted until T2 finishes reading.
            if not reader_finished.wait(timeout=15):
                raise TimeoutError("T2 did not finish reading.")

        connection.rollback()

        log("T1: ROLLBACK executed. Quantity restored to 10.")

    except Exception as error:

        writer_error.append(str(error))

        if connection is not None:
            connection.rollback()

        log(f"T1 ERROR: {error}")

    finally:

        # Make sure T2 does not wait forever if T1 encounters an error.
        writer_updated.set()
        reader_finished.set()

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# TRANSACTION 2 - READER
# Attempts to read T1's uncommitted update.
# ============================================================

def transaction_2_reader():

    connection = None
    cursor = None

    try:

        # Wait until T1 has updated the quantity.
        if not writer_updated.wait(timeout=15):
            raise TimeoutError("T1 did not finish its update.")

        if writer_error:
            raise RuntimeError("T1 failed: " + writer_error[0])

        connection = get_connection()
        cursor = connection.cursor()

        connection.start_transaction(
            isolation_level=ISOLATION_LEVEL
        )

        log("T2: Transaction started.")

        if ISOLATION_LEVEL == "SERIALIZABLE":
            reader_attempting.set()

        cursor.execute("""
            SELECT quantity
            FROM inventory_test
            WHERE item_id = 1
        """)

        result = cursor.fetchone()

        if result is None:
            raise RuntimeError("Item with item_id = 1 was not found.")

        quantity = result[0]

        log(f"T2: Read quantity = {quantity}")

        if quantity == UPDATED_QUANTITY:
            log("RESULT: DIRTY READ DETECTED!")

        else:
            log("RESULT: Dirty read not detected.")

        connection.commit()

        log("T2: COMMIT executed.")

    except Exception as error:

        if connection is not None:
            connection.rollback()

        log(f"T2 ERROR: {error}")

    finally:

        # Tell T1 that T2 has finished.
        reader_finished.set()

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# RUN THE EXPERIMENT
# ============================================================

if __name__ == "__main__":

    print(f"\n=== DIRTY READ: {ISOLATION_LEVEL} ===\n")

    # Check that the experiment starts with the expected value.
    initial_quantity = get_quantity()

    log(f"Initial quantity = {initial_quantity}")

    if initial_quantity != ORIGINAL_QUANTITY:
        print(
            "\nEXPERIMENT STOPPED: Expected quantity is 10. "
            "Reset the test data before running again.\n"
        )

    else:

        thread_1 = threading.Thread(target=transaction_1_writer)
        thread_2 = threading.Thread(target=transaction_2_reader)

        thread_1.start()
        thread_2.start()

        thread_1.join()
        thread_2.join()

        # Verify that T1's rollback restored the original quantity.
        final_quantity = get_quantity()

        print(f"\nFinal quantity = {final_quantity}")

        if final_quantity == ORIGINAL_QUANTITY:
            print("DATABASE CHECK: Quantity restored successfully.")
        else:
            print("DATABASE CHECK: Quantity does not match the original.")

    print("\n=== EXPERIMENT FINISHED ===\n")
