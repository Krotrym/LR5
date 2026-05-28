# ЛР5 Django: ветеринарная клиника

Вариант: 30, ветеринарная клиника. Дополнительное задание про многозадачность не реализовывалось.

## Локальный запуск

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py runserver
```

Сайт откроется по адресу http://127.0.0.1:8000/.
На Windows можно также запустить `.\runserver.ps1`.

Демо-пользователи:

- администратор: `admin` / `admin12345`
- клиенты: `client1` ... `client10` / `client12345`
- врачи-сотрудники: `doctor1` ... `doctor10` / `client12345`

## Docker

```powershell
docker compose up --build
```

Контейнер выполнит миграции, наполнит демоданными и поднимет сервер на http://127.0.0.1:8000/.

## Render

Проект подготовлен для Render: есть `build.sh`, `render.yaml`, Gunicorn, WhiteNoise и поддержка `DATABASE_URL` для PostgreSQL.

Быстрый вариант:

1. Залить папку `LR5` в GitHub-репозиторий.
2. В Render открыть Blueprints и выбрать этот репозиторий.
3. Render прочитает `render.yaml`, создаст Web Service и PostgreSQL.
4. После сборки сайт будет доступен по адресу вида `https://vetclinic-lr5.onrender.com`.

Ручной вариант:

- Build Command: `bash build.sh`
- Start Command: `gunicorn vetclinic_site.wsgi:application`
- Environment:
  - `DJANGO_DEBUG=0`
  - `DJANGO_SECRET_KEY` сгенерировать в Render
  - `DATABASE_URL` взять из Render PostgreSQL

## PythonAnywhere

Если Render просит карту, можно использовать PythonAnywhere Free. Для него есть облегченный файл зависимостей `requirements-pythonanywhere.txt`.

```bash
git clone https://github.com/USERNAME/REPOSITORY.git
cd REPOSITORY
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-pythonanywhere.txt
python manage.py migrate
python manage.py seed_demo
python manage.py collectstatic --noinput
```

В разделе Web на PythonAnywhere:

- Source code: путь к папке проекта
- Working directory: путь к папке проекта
- WSGI configuration file: указать `vetclinic_site.settings` и `application`
- Static files: URL `/static/`, directory `.../staticfiles`

## Что есть

- обязательные страницы: главная, о компании, новости, словарь, контакты, политика, вакансии, отзывы, промокоды;
- регистрация, авторизация, личный кабинет клиента;
- CRUD услуг через function-based views на страницах сайта;
- фронтовые поиск, фильтрация и сортировка услуг;
- серверная и клиентская валидация даты рождения;
- валидация моделей, связи OneToOne, ForeignKey, ManyToMany;
- внешние API: GitHub API и Open-Meteo Air Quality API;
- текущая таймзона, UTC/локальная дата сохранения, текстовый календарь;
- статистика и PNG-диаграмма, построенная Python/Pillow;
- демоданные: по 10 записей в основных таблицах предметной области.
