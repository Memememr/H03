-- ============================================================
-- M1: Schema + Seed Data
-- Database: isolation_lab
-- Table: inventory_test
-- Engine: InnoDB (REQUIRED — MyISAM does not support transactions)
-- ============================================================
-- HOW TO USE:
--   Run this whole file in MySQL Workbench to set up the database.
--   Run it again anytime to RESET the data back to the seed state.
--   The DROP TABLE line means any previous experiments are wiped.
-- ============================================================

CREATE DATABASE IF NOT EXISTS isolation_lab;
USE isolation_lab;

-- Reset: drop old table so experiments always start fresh
DROP TABLE IF EXISTS inventory_test;

-- ------------------------------------------------------------
-- Table: inventory_test (simplified version of Sakila's inventory)
-- 4 columns — matches the assignment requirement of 4-5 columns
-- ------------------------------------------------------------
CREATE TABLE inventory_test (
    item_id    INT PRIMARY KEY,          -- unique item identifier
    item_name  VARCHAR(50),              -- readable name
    quantity   INT,                      -- the column experiments update most
    price      DECIMAL(10,2)             -- second column for variety
) ENGINE=InnoDB;

-- ------------------------------------------------------------
-- Seed data: 5 rows
-- WHY 5 ROWS:
--   - Phantom read experiments need multiple rows so WHERE clauses
--     actually filter something (e.g. WHERE quantity < 15)
--   - Quantity values (10, 5, 20, 3, 15) are spread out so
--     experiments can target "low stock" or "high stock" easily
--   - Not too many rows — keeps SELECT * output short for screenshots
--     and makes interleaving tables easy to read
-- ------------------------------------------------------------
INSERT INTO inventory_test (item_id, item_name, quantity, price) VALUES
(1, 'DVD Action Movie', 10, 19.99),
(2, 'DVD Comedy Movie',  5, 14.99),
(3, 'DVD Documentary',  20, 24.99),
(4, 'DVD Horror Movie',  3, 17.99),
(5, 'DVD Sci-Fi Movie', 15, 22.99);

-- ------------------------------------------------------------
-- Verify setup (should show 5 rows and Engine = InnoDB)
-- ------------------------------------------------------------
SELECT * FROM inventory_test;
SHOW TABLE STATUS FROM isolation_lab LIKE 'inventory_test';