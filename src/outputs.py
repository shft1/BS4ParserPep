import csv
import datetime as dt
import logging
from dataclasses import dataclass
from typing import Any, List

from prettytable import PrettyTable

from constants import BASE_DIR, DATETIME_FORMAT, ENCODING


def control_output(results, cli_args):
    output_object = Output(results, cli_args, cli_args.output)
    if output_object.output_args == 'file':
        file_output(results, cli_args)
    elif output_object.output_args == 'pretty':
        pretty_output(results)
    else:
        default_output(results)


@dataclass
class Output:
    results: List
    cli_args: Any
    output_args: str | None


def default_output(results):
    for row in results:
        print(*row)


def pretty_output(results):
    table = PrettyTable()
    table.field_names = results[0]
    table.align = 'l'
    table.add_rows(results[1:])
    print(table)


def file_output(results, cli_args):
    results_dir = BASE_DIR / 'results'
    results_dir.mkdir(exist_ok=True)
    parser_mode = cli_args.mode
    now = dt.datetime.now()
    now_formatted = now.strftime(DATETIME_FORMAT)
    file_name = f'{parser_mode}_{now_formatted}.csv'
    file_path = results_dir / file_name
    with open(file_path, 'w', encoding=ENCODING) as csv_file:
        if parser_mode == 'pep':
            table = PrettyTable(results[0])
            table.add_rows(results[1:])
            csv_file.write(table.get_string())
        else:
            writer = csv.writer(csv_file, dialect='unix')
            writer.writerows(results)
    logging.info(f'Файл с результатами был сохранён: {file_path}')
