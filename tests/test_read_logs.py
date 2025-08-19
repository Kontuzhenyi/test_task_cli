import json
from datetime import date
from main import read_logs

def _write_lines(p, lines):
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")

def test_read_logs_1(tmp_path):
    """
    read_logs принимает несколько путей, читает оба файла и
    возвращает объединённый список валидных записей в порядке чтения.
    """
    ex1 = tmp_path / "ex1.log"
    _write_lines(ex1, [
        json.dumps({"@timestamp":"2025-06-22T10:00:00+00:00","url":"/a","response_time":0.1}),
        "",  # пустая
        "{not json}",  # битая
        json.dumps({"@timestamp":"2025-06-22T11:00:00+00:00","url":"/b","response_time":"0.2"}),
        json.dumps({"@timestamp":"2025-06-23T00:00:00+00:00","url":"/a","response_time":0.3}),  # другая дата
    ])

    ex2 = tmp_path / "ex2.log"
    _write_lines(ex2, [
        json.dumps({"@timestamp":"2025-06-22T12:00:00+00:00","http_user_agent":"UA-X","response_time":1.0}),
        json.dumps({"@timestamp":"2025-06-23T12:00:00+00:00","http_user_agent":"UA-Y","response_time":2.0}),
    ])

    recs_url = read_logs([str(ex1), str(ex2)], filter_date=date(2025,6,22), group_field="url")
    assert recs_url == [
        {"group": "/a", "response_time": 0.1},
        {"group": "/b", "response_time": 0.2},
    ]

    recs_ua = read_logs([str(ex1), str(ex2)], filter_date=date(2025,6,22), group_field="http_user_agent")
    assert recs_ua == [
        {"group": "UA-X", "response_time": 1.0},
    ]

def test_read_logs_2(tmp_path):
    p = tmp_path / "logs.log"
    _write_lines(p, [
        json.dumps({"@timestamp":"2025-06-22T10:00:00+00:00","url":"/ok","response_time":0.1}),
        json.dumps({"@timestamp":"2025-06-22T10:00:00+00:00","url":"/no_time"}),        # нет response_time
        json.dumps({"@timestamp":"2025-06-22T10:00:00+00:00","response_time":0.2}),     # нет поля группировки
        json.dumps({"@timestamp":"2025-06-22T10:00:00+00:00","url":"/bad","response_time":"xx"}), # не число
    ])
    recs = read_logs([str(p)], filter_date=None, group_field="url")
    assert recs == [{"group": "/ok", "response_time": 0.1}]