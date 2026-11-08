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

INITIAL_QUANTITY = 20
UPDATED_QUANTITY = 10

first_read_done = threading.Event()
writer_finished = threading.Event()

writer_error = []
start_time = time.monotonic()


def log(message):
    elapsed = time.monotonic() - start_time
    print(f"[{elapsed:6.2f}s] {message}", flush=True)


def get_quantity():
    """Read current quantity using a separate connection."""
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT quantity
            FROM inventory_test
            WHERE item_id = 3
        """)
        result = cursor.fetchone()
        if result is None:
            raise RuntimeError("Item with item_id = 3 was not found.")
        return result[0]
    finally:
        cursor.close()
        connection.close()


def reset_quantity():
    """Reset quantity of item_id = 3 back to INITIAL_QUANTITY between iterations."""
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute("UPDATE inventory_test SET quantity = %s WHERE item_id = 3", (INITIAL_QUANTITY,))
        connection.commit()
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

        cursor.execute("""
            SELECT quantity
            FROM inventory_test
            WHERE item_id = 3
        """)
        first_read = cursor.fetchone()[0]
        log(f"T1: 1st Read quantity = {first_read}")

        first_read_done.set()

        if not writer_finished.wait(timeout=15):
            raise TimeoutError("T2 did not finish writing.")

        cursor.execute("""
            SELECT quantity
            FROM inventory_test
            WHERE item_id = 3
        """)
        second_read = cursor.fetchone()[0]
        log(f"T1: 2nd Read quantity = {second_read}")

        if first_read != second_read:
            log("RESULT: NON-REPEATABLE READ DETECTED!")
        else:
            log("RESULT: Non-repeatable read not detected.")

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
            UPDATE inventory_test
            SET quantity = %s
            WHERE item_id = 3
        """, (UPDATED_QUANTITY,))

        log(f"T2: Updated quantity of item_id=3 to {UPDATED_QUANTITY}.")

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

        reset_quantity()

        print(f"\n==================================================")
        print(f"=== NON-REPEATABLE READ EXPERIMENT: {CURRENT_ISOLATION_LEVEL} ===")
        print(f"==================================================\n")

        initial_quantity = get_quantity()
        log(f"Initial quantity = {initial_quantity}")

        thread_1 = threading.Thread(target=transaction_1_reader)
        thread_2 = threading.Thread(target=transaction_2_writer)

        thread_1.start()
        thread_2.start()

        thread_1.join()
        thread_2.join()

        final_quantity = get_quantity()
        print(f"\nFinal quantity = {final_quantity}")

    reset_quantity()
    print("\n=== ALL ISOLATION LEVEL EXPERIMENTS FINISHED ===\n")