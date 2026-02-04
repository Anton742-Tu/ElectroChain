# ElectroChain

Система управления сетью продаж электроники с иерархической структурой.

## Описание

Веб-приложение с API-интерфейсом и админ-панелью для управления сетью по продаже электроники.
Иерархическая структура состоит из трех уровней:
- Завод (уровень 0)
- Розничная сеть
- Индивидуальный предприниматель

## Установка

1. Клонировать репозиторий:
```bash
git clone <git@github.com:Anton742-Tu/ElectroChain.git>
cd electrochain
```
2. Создать виртуальное окружение:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate     # Windows
```
3. Установить зависимости:

```bash
pip install -r requirements-dev.txt
```
4. Применить миграции:

```bash
python manage.py migrate
```
5. Создать суперпользователя:

```bash
python manage.py createsuperuser
```
6. Запустить сервер:

```bash
python manage.py runserver
```
## Использование
Админ-панель: http://localhost:8000/admin/

API: http://localhost:8000/api/

## Разработка
### Форматирование кода
```bash
black .
isort .
flake8 .
```
## Тестирование
```bash
python manage.py test
```
## Структура проекта
