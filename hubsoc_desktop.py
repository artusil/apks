"""Запуск hubsoc в отдельном окне Windows. Исходники остаются отдельными файлами."""
import os
from pathlib import Path
import subprocess
import sys
import threading
import venv

ROOT = Path(__file__).resolve().parent
ENV = ROOT / '.venv'


def prepare():
    files = ('app.py', 'requirements.txt', 'requirements-desktop.txt',
             'static/clips.js', 'templates/index.html')
    if not all((ROOT / f).is_file() for f in files):
        raise RuntimeError('Сначала извлеките ZIP целиком. Запускайте скрипт из папки hubsoc.')
    python = ENV / 'Scripts' / 'python.exe'
    if not python.exists():
        print('Создаём окружение для hubsoc…', flush=True)
        venv.create(ENV, with_pip=True)
    check = subprocess.run([python, '-c', 'import flask, waitress, webview'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if check.returncode:
        print('Устанавливаем компоненты. При первом запуске нужен интернет…', flush=True)
        subprocess.run([python, '-m', 'pip', 'install', '-r', 'requirements-desktop.txt'],
                       cwd=ROOT, check=True)
    return python


def run_window():
    from waitress import create_server
    import webview
    from app import app

    server = create_server(app, host='127.0.0.1', port=0,
                           max_request_body_size=app.config['MAX_CONTENT_LENGTH'])
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    try:
        webview.create_window('hubsoc', f'http://127.0.0.1:{server.effective_port}/',
                              width=1100, height=760, min_size=(360, 480))
        webview.start(gui='edgechromium', private_mode=False,
                      storage_path=str(Path(app.instance_path) / 'webview'))
    finally:
        server.close()


def main():
    if os.name != 'nt':
        raise RuntimeError('Это окно для Windows. На другой ОС запустите host.py.')
    if sys.argv[1:] == ['--window']:
        run_window()
        return 0
    return subprocess.call([prepare(), str(Path(__file__).resolve()), '--window'], cwd=ROOT)


if __name__ == '__main__':
    try:
        status = main()
        if status:
            raise RuntimeError(f'Процесс окна завершился с кодом {status}.')
    except Exception as exc:
        import ctypes
        message = (f'Не удалось открыть hubsoc.\n\n{exc}\n\n'
                   'Нужны Python 3.11+ и Microsoft Edge WebView2 Runtime. '
                   'Для запуска в браузере используйте Start-hubsoc.bat.')
        if os.name == 'nt':
            ctypes.windll.user32.MessageBoxW(None, message, 'hubsoc', 0x10)
        else:
            print(message, file=sys.stderr)
        sys.exit(1)
