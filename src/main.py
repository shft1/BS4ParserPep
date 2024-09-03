import datetime as dt
import logging
import re
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from prettytable import PrettyTable
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import (BASE_DIR, DATETIME_FORMAT, EXPECTED_STATUS,
                       MAIN_DOC_URL, PEP_DOC_URL)
from outputs import control_output
from utils import find_tag, get_response


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return

    soup = BeautifulSoup(response.text, features='lxml')
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all(
        'li', attrs={'class': 'toctree-l1'}
    )

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    for section in tqdm(sections_by_python,
                        desc='Парсинг статей об обновлениях Python'):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        if response is None:
            return

        soup = BeautifulSoup(response.text, features='lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        results.append(
            (version_link, h1.text, dl_text)
        )
    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return

    soup = BeautifulSoup(response.text, 'lxml')
    sidebar = find_tag(soup, tag=None, attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')
    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise Exception('Ничего не нашлось')

    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is None:
            version, status = a_tag.text, ''
        else:
            version, status = text_match.groups()
        results.append(
            (link, version, status)
        )
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, downloads_url)
    if response is None:
        return

    soup = BeautifulSoup(response.text, 'lxml')
    table_tag = find_tag(soup, 'table', {'class': 'docutils'})
    pdf_a4_tag = find_tag(
        table_tag, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')})
    pdf_a_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a_link)

    filename = archive_url.split('/')[-1]
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename
    response = get_response(session, archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


def pep(session):
    response = get_response(session, PEP_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    num_index = find_tag(soup, 'section', {'id': 'numerical-index'})
    tbody = find_tag(num_index, 'tbody')
    peps_rows = tbody.find_all('tr')
    count_pep = len(peps_rows)
    for pep_row in peps_rows:
        status_in_table = find_tag(pep_row, 'abbr').text[1:]
        url_tag = find_tag(pep_row, 'a', {'class': 'pep reference internal'})
        pep_url = urljoin(PEP_DOC_URL, url_tag['href'])
        response = get_response(session, pep_url)
        soup = BeautifulSoup(response.text, features='lxml')
        status_tag = soup.find(text='Status').parent
        status = status_tag.next_sibling.next_sibling.text
        expected_status = EXPECTED_STATUS[status_in_table]
        if status not in expected_status:
            logging.warning(
                f'Несовпадающие статусы:\n'
                f'{pep_url}\n'
                f'Статус в карточке: {status}\n'
                f'Ожидаемые статусы: {expected_status}'
            )
            continue
        ROWS_IN_TABLE[status] += 1
    ROWS_IN_TABLE['Total'] = count_pep
    rows = list(ROWS_IN_TABLE.items())
    table = PrettyTable(rows[0])
    table.add_rows(rows[1:])
    results = table.get_string()

    results_dir = BASE_DIR / 'results'
    results_dir.mkdir(exist_ok=True)
    now = dt.datetime.now()
    now_formatted = now.strftime(DATETIME_FORMAT)
    file_name = f'pep_{now_formatted}.csv'
    file_path = results_dir / file_name
    with open(file_path, 'w', encoding='utf-8') as csv_file:
        csv_file.write(results)


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep,
}


ROWS_IN_TABLE = {
    'Статус': 'Количество',
    'Accepted': 0,
    'Active': 0,
    'Draft': 0,
    'Deferred': 0,
    'Final': 0,
    'Provisional': 0,
    'Rejected': 0,
    'Superseded': 0,
    'Withdrawn': 0,
    'Total': 0,
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')

    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки {args}')

    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode
    result = MODE_TO_FUNCTION[parser_mode](session)

    if result is not None:
        control_output(result, args)
    logging.info('Парсер завершил работу.')


if __name__ == '__main__':
    main()
