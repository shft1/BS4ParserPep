# BS4ParserPep - парсер PEP

---

### Описание:
Парсер выполняет сбор информации об стандартах PEP, отображая результаты парсинга в нескольких форматах на выбор.

---

### Список поддерживаемых сайтов:
- https://peps.python.org/

---

### Стек Технологий
- Python 3.9
- BeautifulSoup4
- requests

---

### Инструкция по запуску:
**Клонируйте репозиторий:**
```
git clone git@github.com:shft1/BS4ParserPep.git
```

**Установите и активируйте виртуальное окружение:**
для MacOS:
```
python3 -m venv venv
```

для Windows:
```
python -m venv venv
source venv/bin/activate
source venv/Scripts/activate
```

**Установите зависимости из файла `requirements.txt`:**
```
pip install -r requirements.txt
```

**Перейдите в папку `src` и запустите скрипт с позиционным аргументом `pep`:**  
```
python main.py pep
```

---

### Примечание

- Результат парсинга сохранится в папку `results` с именем файла, начинающегося на `pep..`
- Логгирования сохраняется в папку `logs`

---

### Автор:

[Алексей Малков](https://github.com/shft1)
