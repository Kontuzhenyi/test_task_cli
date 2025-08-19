import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from datetime import date, datetime
from statistics import mean
from typing import Iterable, List, Dict, TypedDict, Optional, Callable, Any

from tabulate import tabulate

# Два класса ниже это подсказки для создания словарей
class RawLog(TypedDict): # Сырой лог
    group: str
    response_time: float

class ReportRow(TypedDict):
    group: str
    total: int
    avg_response_time: float

def existing_file(path: str) -> str:
    """
    Проверяет существование файла.
    """
    if not os.path.isfile(path):
        raise argparse.ArgumentTypeError(f"Файл '{path}' не найден")
    return path

def parse_cli_date(s: str) -> date:
    """
    Проверяет дату из параметра.
    """
    try:
        return date.fromisoformat(s)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"Неверный формат --date: '{s}'. Ожидается YYYY-MM-DD, напр. 2025-06-22")

def parse_args() -> argparse.Namespace:
    """
    Разбирает аргументы командной строки.
    --file: один или несколько путей к логам
    --report: путь к результирующему CSV-отчёту.
    --date: дата по которой будут отсортировываться записи.
    --report-kind: тип отчета.
    """
    parser = argparse.ArgumentParser(description="Скрипт для обработки log-файлов")
    parser.add_argument(
        "--file",
        type=existing_file,
        required=True,
        nargs="+",
        help="Имена файлов логов (по одной JSON-записи на строку)"
    )
    parser.add_argument(
        "--report",
        type=str,
        default="report.csv",
        help="Название файла для сохранения отчёта (по умолчанию report.csv)"
    )
    parser.add_argument(
        "--date",
        type=parse_cli_date,
        default=None,
        help="Фильтр по дате (формат YYYY-MM-DD), берутся только записи за указанный день",
    )
    parser.add_argument(
        "--report-kind",
        choices=["url", "useragent", "browser"],
        default="url",
        help="Тип отчёта: url, useragent или browser (по умолчанию url)"
    )
    return parser.parse_args()

def extract_record_date(log: Dict[str, Any]) -> Optional[date]: 
    """
    Достаёт дату из поля '@timestamp' в формате ISO 8601:
    'YYYY-MM-DDTHH:MM:SS+00:00'
    Если поле отсутствует или формат некорректный — вернёт None.
    """
    ts = log.get("@timestamp")
    if not ts:
        return None

    try:
        dt = datetime.fromisoformat(str(ts))
        return dt.date()
    except ValueError:
        return None
    
def detect_browser(user_agent: str, log: Dict[str, Any]) -> str:
    ua = user_agent.lower()
    
    if "edg/" in ua or "edge" in ua:
        return "Edge"
    if "opr/" in ua or "opera" in ua:
        return "Opera"
    if "chrome" in ua and "edg/" not in ua and "edge" not in ua and "opr/" not in ua:
        return "Chrome"
    if "firefox" in ua or "fxios" in ua:
        return "Firefox"
    if "safari" in ua and "chrome" not in ua:
        return "Safari"
    return "Other"

def read_logs(filepaths: Iterable[str], filter_date: Optional[date] = None, group_field: str = "url",
               transform: Optional[Callable[[str, Dict[str, Any]], str]] = None,) -> List[RawLog]:
    """
    Читает JSON-строки из файлов и возвращает список валидных записей.
    Пропускает пустые строки и некорректный JSON.
    Учитываются записи, содержащие ключи 'url' или 'http_user_agent',  и 'response_time'.
    """
    records: List[RawLog] = []
    for filepath in filepaths:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    log: Dict = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"Ошибка парсинга строки в {filepath}: {line}")
                    print("Причина: ", e)
                    continue

                if group_field in log and "response_time" in log:
                    if filter_date is not None:
                        rec_date = extract_record_date(log)
                        if rec_date != filter_date:
                            continue
                    try:
                        rt = float(log["response_time"])
                    except (TypeError, ValueError):
                        continue
                    raw_value = str(log[group_field])
                    value = transform(raw_value, log) if transform else raw_value
                    records.append(
                        RawLog(
                            group=value,
                            response_time=rt,
                        )
                    )
    return records

def build_report(records: Iterable[RawLog]) -> List[ReportRow]:
    """
    Группирует записи по указанному полю (url или useragent), считает total и среднее время ответа.
    Возвращает список строк отчёта, отсортированный по total (убывание).
    """
    by_field: Dict[str, List[float]] = defaultdict(list)
    for rec in records:
        key = rec["group"]
        if key is None:
            continue
        by_field[key].append(rec["response_time"])

    rows: List[ReportRow] = []
    for key, times in by_field.items():
        if not times:
            continue
        avg = mean(times)
        rows.append(
            ReportRow(
                group=key,
                total=len(times),
                avg_response_time=round(avg, 3),
            )
        )

    rows.sort(key=lambda r: (r["total"], r["avg_response_time"]), reverse=True)
    return rows

def save_report_csv(rows: Iterable[ReportRow], path: str, group_field: str = "url") -> None:
    """
    Сохраняет отчёт в CSV.
    """
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=[group_field, "total", "avg_response_time"]
        )
        writer.writeheader()
        writer.writerows(
            {
                group_field: row["group"],
                "total": row["total"],
                "avg_response_time": row["avg_response_time"],
            }
            for row in rows
        )

def main() -> int:
    """
    Точка входа: читает логи, строит отчёт, печатает таблицу и сохраняет CSV.
    """
    args = parse_args()
    
    field_map = {
        "url":       ("url", None),
        "useragent": ("http_user_agent", None),
        "browser": ("http_user_agent", detect_browser),
    }

    group_field, transform = field_map[args.report_kind]
    filter_date = args.date

    records = read_logs(args.file, filter_date, group_field, transform=transform)
    if not records:
        print("Нет валидных записей в логах.")
        return 1 
    report_rows = build_report(records)

    header_map = {
        "group": (
            "url" if args.report_kind == "url"
            else "http_user_agent" if args.report_kind == "useragent"
            else "browser"
        ),
        "total": "total",
        "avg_response_time": "avg_response_time",
    }
    print(tabulate(report_rows, headers=header_map, tablefmt="simple"))    

    save_report_csv(report_rows, args.report, group_field)
    print(f"\nОтчёт сохранён в: {args.report}")
    return 0

if __name__ == "__main__":
    sys.exit(main())