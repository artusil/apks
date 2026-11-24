# hubsoc
Социальная сеть на Flask и SQLite. Локальный запуск: `pip install -r requirements.txt`, затем `flask --app app run`.

## Бесплатная публикация на PythonAnywhere
Создайте бесплатный аккаунт, загрузите проект в каталог `hubsoc` и установите зависимости в virtualenv. В разделе Web создайте приложение Manual configuration с той же версией Python и укажите путь к virtualenv. В WSGI-файле используйте:

```python
import os, sys
sys.path.insert(0, os.path.expanduser('~/hubsoc'))
from app import app as application
```
Нажмите Reload. Аккаунты и записи сохраняются в `instance/`; не публикуйте эту папку, регулярно делайте резервные копии.

## Свой сервер на Python

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python host.py
```

Откройте `http://localhost:8000`. Waitress обслуживает приложение Flask и статику; регистрация, лента и лайки работают с локальной SQLite, без GitHub. Адрес и порт можно изменить: `python host.py --host 127.0.0.1 --port 9000`. Также поддерживается переменная `PORT`. Файлы в `docs/` — отдельная версия для GitHub Pages.

Для постоянного доступа нужен постоянно работающий компьютер с доступом из интернета или VPS. Для публикации поставьте перед Waitress HTTPS-прокси (например, Caddy), привязав Waitress к `127.0.0.1`. Домен подключается отдельно через DNS. Храните `instance/` на постоянном диске и делайте резервные копии.
