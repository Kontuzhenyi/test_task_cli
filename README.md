# Log Parser

Скрипт для анализа JSON-логов и построения отчётов по `url`, `useragent` или `browser`.

## Возможности

- Поддержка нескольких входных файлов с логами.
- Фильтрация по дате (`--date YYYY-MM-DD`).
- Построение отчётов:
  - по `url`
  - по `useragent`
  - по определению браузера из поля `User-Agent`.
- Вывод отчёта в консоль в виде таблицы.
- Сохранение отчёта в CSV.

## Примеры запуска

Анализ логов по URL:
python main.py --file example1.log example2.log --report report.csv --report-kind url

Фильтрация по дате:
python main.py --file example1.log --report report.csv --report-kind useragent --date 2025-06-22
