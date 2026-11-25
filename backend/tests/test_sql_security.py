import pytest
from app.services.sql_service import SQLService


def test_sql_validator_allows_valid_select():
    sql = "SELECT region, SUM(revenue) AS total_revenue FROM sales_data GROUP BY region ORDER BY total_revenue DESC"
    is_valid, final_sql = SQLService.validate_sql(sql, allowed_table="sales_data", allowed_columns=["region", "revenue"])
    assert is_valid is True
    assert "LIMIT" in final_sql
    assert "SELECT" in final_sql


def test_sql_validator_rejects_drop_table():
    sql = "DROP TABLE sales_data"
    is_valid, err = SQLService.validate_sql(sql, allowed_table="sales_data", allowed_columns=["revenue"])
    assert is_valid is False
    assert "Disallowed statement type" in err or "Prohibited" in err


def test_sql_validator_rejects_delete():
    sql = "DELETE FROM sales_data WHERE revenue < 100"
    is_valid, err = SQLService.validate_sql(sql, allowed_table="sales_data", allowed_columns=["revenue"])
    assert is_valid is False


def test_sql_validator_rejects_multiple_statements():
    sql = "SELECT * FROM sales_data; DROP TABLE sales_data;"
    is_valid, err = SQLService.validate_sql(sql, allowed_table="sales_data", allowed_columns=["revenue"])
    assert is_valid is False
    assert "Multiple SQL statements" in err


def test_sql_validator_rejects_dml_and_ddl():
    attacks = [
        "INSERT INTO sales_data (revenue) VALUES (999999)",
        "UPDATE sales_data SET revenue = 0",
        "CREATE TABLE backdoor (id INT)",
        "ALTER TABLE sales_data ADD COLUMN hack TEXT",
        "PRAGMA table_info(sales_data)",
        "ATTACH DATABASE 'evil.db' AS evil"
    ]
    for attack in attacks:
        is_valid, err = SQLService.validate_sql(attack, allowed_table="sales_data", allowed_columns=["revenue"])
        assert is_valid is False, f"Expected attack to be rejected: {attack}"


def test_sql_validator_rejects_subquery_on_disallowed_tables():
    sql = "SELECT revenue FROM (SELECT * FROM users) AS u"
    is_valid, err = SQLService.validate_sql(sql, allowed_table="sales_data", allowed_columns=["revenue"])
    assert is_valid is False
    assert "Unauthorized table access" in err
