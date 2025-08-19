import json
import os
import sys
from argparse import ArgumentTypeError
from main import existing_file, main

def test_existing_file_1(tmp_path):
    p = tmp_path / "x.log"
    p.write_text("", encoding="utf-8")
    assert existing_file(str(p)) == str(p)

def test_existing_file_2(tmp_path):
    p = tmp_path / "nope.log"
    try:
        existing_file(str(p))
    except ArgumentTypeError as e:
        assert "не найден" in str(e)

def test_main_1(monkeypatch, tmp_path, capsys):
    logs = [
        {"@timestamp":"2025-06-22T10:00:00+00:00","http_user_agent":"UA-1","response_time":0.1},
        {"@timestamp":"2025-06-22T11:00:00+00:00","http_user_agent":"UA-1","response_time":0.2},
        {"@timestamp":"2025-06-22T12:00:00+00:00","http_user_agent":"UA-2","response_time":1.0},
    ]
    src = tmp_path / "logs.jsonl"
    src.write_text("\n".join(json.dumps(x) for x in logs) + "\n", encoding="utf-8")
    out_csv = tmp_path / "ua.csv"

    monkeypatch.setattr(sys, "argv", ["log_parser.py", "--file", str(src), "--report", str(out_csv), "--report-kind", "useragent"])
    code = main()
    out = capsys.readouterr().out

    assert code == 0
    assert "http_user_agent" in out
    assert "UA-1" in out and "UA-2" in out
    assert out_csv.exists()
    head = out_csv.read_text(encoding="utf-8").splitlines()[0]
    assert head == "http_user_agent,total,avg_response_time"

def test_main_2(tmp_path, monkeypatch, capsys):
    logs = [
        {"@timestamp":"2025-06-22T10:00:00+00:00","http_user_agent":"UA-1","response_time":0.1},
        {"@timestamp":"2025-06-22T11:00:00+00:00","http_user_agent":"UA-1","response_time":0.2},
        {"@timestamp":"2025-06-22T12:00:00+00:00","http_user_agent":"UA-2","response_time":1.0},
    ]
    src = tmp_path / "logs.jsonl"
    src.write_text("\n".join(json.dumps(x) for x in logs) + "\n", encoding="utf-8")
    out_csv = tmp_path / "ua.csv"

    monkeypatch.setattr(sys, "argv", ["log_parser.py", "--file", str(src), "--report", str(out_csv), "--report-kind", "useragent"])
    code = main()
    out = capsys.readouterr().out

    assert code == 0
    assert "http_user_agent" in out
    assert "UA-1" in out and "UA-2" in out
    assert out_csv.exists()
    head = out_csv.read_text(encoding="utf-8").splitlines()[0]
    assert head == "http_user_agent,total,avg_response_time"

def test_main_3(tmp_path, monkeypatch, capsys):
    bad = tmp_path / "bad.jsonl"
    bad.write_text("{not json}\n", encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["log_parser.py", "--file", str(bad)])
    code = main()
    out = capsys.readouterr().out

    assert code == 1
    assert "Нет валидных записей" in out