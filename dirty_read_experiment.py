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

ORIGINAL_PRICE = 19.99
UPDATED_PRICE = 29.99

writer_updated = threading.Event()
reader_attempting = threading.Event()
reader_finished = threading.Event()

writer_error = []
start_time = time.monotonic()


def log(message):
    elapsed = time.monotonic() - start_time
    print(f"[{elapsed:6.2f}s] {message}", flush=True)


def get_price():
    """Read current price of Action DVD using a separate connection."""
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            SELECT price
            FROM inventory_test
            WHERE item_id = 1
        """)

        result = cursor.fetchone()

        if result is None:
            raise RuntimeError("Item with item_id = 1 was not found.")

        return float(result[0])

    finally:
        cursor.close()
        connection.close()


def transaction_1_writer():
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
            UPDATE inventory_test
            SET price = %s
            WHERE item_id = 1
        """, (UPDATED_PRICE,))

        if cursor.rowcount != 1:
            raise RuntimeError("Expected to update exactly one row.")

        log(
            f"T1: Updated price of item_id=1 from {ORIGINAL_PRICE} "
            f"to {UPDATED_PRICE} (uncommitted)."
        )

        writer_updated.set()

        if CURRENT_ISOLATION_LEVEL == "SERIALIZABLE":
            if not reader_attempting.wait(timeout=15):
                raise TimeoutError("T2 did not attempt to read.")

            log("T1: T2 is attempting to read. Waiting briefly.")
            time.sleep(1.5)

        else:
            if not reader_finished.wait(timeout=15):
                raise TimeoutError("T2 did not finish reading.")

        connection.rollback()
        log("T1: ROLLBACK executed. Price restored to 19.99.")

    except Exception as error:
        writer_error.append(str(error))
        if connection is not None:
            connection.rollback()
        log(f"T1 ERROR: {error}")

    finally:
        writer_updated.set()
        reader_finished.set()

        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


def transaction_2_reader():
    connection = None
    cursor = None

    try:
        if not writer_updated.wait(timeout=15):
            raise TimeoutError("T1 did not finish its update.")

        if writer_error:
            raise RuntimeError("T1 failed: " + writer_error[0])

        connection = get_connection()
        cursor = connection.cursor()

        connection.start_transaction(
            isolation_level=CURRENT_ISOLATION_LEVEL
        )

        log("T2: Transaction started.")

        if CURRENT_ISOLATION_LEVEL == "SERIALIZABLE":
            reader_attempting.set()

        cursor.execute("""
            SELECT price
            FROM inventory_test
            WHERE item_id = 1
        """)

        result = cursor.fetchone()

        if result is None:
            raise RuntimeError("Item with item_id = 1 was not found.")

        price = float(result[0])

        log(f"T2: Read price = {price}")

        if price == UPDATED_PRICE:
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
        reader_finished.set()

        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    for level in ISOLATION_LEVELS:
        CURRENT_ISOLATION_LEVEL = level

        writer_updated.clear()
        reader_attempting.clear()
        reader_finished.clear()
        writer_error.clear()
        start_time = time.monotonic()

        print(f"\n==================================================")
        print(f"=== DIRTY READ EXPERIMENT: {CURRENT_ISOLATION_LEVEL} ===")
        print(f"==================================================\n")

        initial_price = get_price()
        log(f"Initial price = {initial_price}")

        if abs(initial_price - ORIGINAL_PRICE) > 0.01:
            print(
                f"\nEXPERIMENT STOPPED: Expected price is {ORIGINAL_PRICE}. "
                "Reset the test data before running again.\n"
            )
            break

        thread_1 = threading.Thread(target=transaction_1_writer)
        thread_2 = threading.Thread(target=transaction_2_reader)

        thread_1.start()
        thread_2.start()

        thread_1.join()
        thread_2.join()

        final_price = get_price()
        print(f"\nFinal price = {final_price}")

        if abs(final_price - ORIGINAL_PRICE) <= 0.01:
            print("DATABASE CHECK: Price restored successfully.")
        else:
            print("DATABASE CHECK: Price does not match original.")

    print("\n=== ALL ISOLATION LEVEL EXPERIMENTS FINISHED ===\n")