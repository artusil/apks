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

### Отдельное окно приложения (Windows)
Распакуйте папку `hubsoc` целиком и откройте `hubsoc_desktop.py` или выполните `py hubsoc_desktop.py`. Скрипт сам создаёт `.venv`, при необходимости устанавливает `requirements-desktop.txt` и открывает ленту в окне WebView2. Нужны Python 3.11+, Microsoft Edge WebView2 Runtime и интернет при первой установке. Сервер доступен только на этом компьютере; при закрытии окна он останавливается. База, клипы и профиль окна хранятся в `instance/`. EXE не собирается. `Start-hubsoc.bat` по-прежнему запускает обычную браузерную версию.
