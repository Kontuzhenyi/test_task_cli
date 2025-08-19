import argparse
from datetime import date
from main import parse_cli_date, extract_record_date

def test_parse_cli_and_extract_date_1():
    assert parse_cli_date("2025-06-22") == date(2025, 6, 22)

def test_parse_cli_and_extract_date_2():
    try:
        parse_cli_date("2025-22-06")
    except argparse.ArgumentTypeError as e:
        assert "Неверный формат --date" in str(e)

def test_parse_cli_and_extract_date_3():
    log = {"@timestamp": "2025-06-22T14:00:21+00:00"}
    assert extract_record_date(log) == date(2025, 6, 22)

def test_parse_cli_and_extract_date_4():
    assert extract_record_date({}) is None