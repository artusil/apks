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
