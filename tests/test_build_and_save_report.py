import csv
from main import build_report, save_report_csv

def test_build_and_save_report_1():
    records = [
        {"group": "/a", "response_time": 0.1},
        {"group": "/a", "response_time": 0.4},
        {"group": "/b", "response_time": 1.0},
        {"group": "/a", "response_time": 0.2},
        {"group": "/b", "response_time": 2.0},
    ]
    report = build_report(records)
    
    assert [r["group"] for r in report] == ["/a", "/b"]
    assert report[0]["total"] == 3 and report[0]["avg_response_time"] == 0.233
    assert report[1]["total"] == 2 and report[1]["avg_response_time"] == 1.5

def test_build_and_save_report_2(tmp_path):
    rows = [
        {"group": "/a", "total": 3, "avg_response_time": 0.233},
        {"group": "/b", "total": 2, "avg_response_time": 1.5},
    ]
    out = tmp_path / "r.csv"

    # как url
    save_report_csv(rows, str(out), group_field="url")
    with out.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        got = list(reader)
    assert reader.fieldnames == ["url", "total", "avg_response_time"]
    # DictReader читает строки как строки — приводим типы для сравнения
    got = [{"url": r["url"], "total": int(r["total"]), "avg_response_time": float(r["avg_response_time"])} for r in got]
    assert got == [
        {"url": "/a", "total": 3, "avg_response_time": 0.233},
        {"url": "/b", "total": 2, "avg_response_time": 1.5},
    ]

    # как http_user_agent
    save_report_csv(rows, str(out), group_field="http_user_agent")
    with out.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == ["http_user_agent", "total", "avg_response_time"]