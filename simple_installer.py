import os
import sys
import urllib.request
import zipfile
import shutil
from pathlib import Path

try:
    import winshell
    from win32com.client import Dispatch
except ImportError:
    print('Установите pywin32 и winshell: pip install pywin32 winshell')
    sys.exit(1)

# --- НАСТРОЙКИ ---
DOWNLOAD_URL = 'https://www.dropbox.com/scl/fi/qm0lddxxk4agxuq5yg7s8/app_launcher.exe?rlkey=g7dq6dnuqn0ftm35a3pxi1lj0&st=kcjcrk02&dl=1'  # Замените на вашу ссылку
FOLDER = r'C:\Soft'

# --- СКАЧИВАНИЕ ---
def download_file(url, dest):
    print(f'Скачивание {url} ...')
    urllib.request.urlretrieve(url, dest)
    print(f'Скачано: {dest}')

# --- РАСПАКОВКА ---
def extract_zip(zip_path, extract_to):
    print(f'Распаковка {zip_path} ...')
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print(f'Распаковано в: {extract_to}')

# --- ЯРЛЫК ---
def create_shortcut(target, shortcut_path, icon=None):
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    shortcut.Targetpath = target
    shortcut.WorkingDirectory = os.path.dirname(target)
    if icon:
        shortcut.IconLocation = icon
    shortcut.save()
    print(f'Ярлык создан: {shortcut_path}')

# --- ОСНОВНОЙ СЦЕНАРИЙ ---
def main():
    os.makedirs(FOLDER, exist_ok=True)
    filename = os.path.basename(DOWNLOAD_URL.split('?')[0])
    dest_path = os.path.join(FOLDER, filename)
    download_file(DOWNLOAD_URL, dest_path)

    exe_path = dest_path
    if zipfile.is_zipfile(dest_path):
        extract_zip(dest_path, FOLDER)
        # Ищем первый exe в папке
        exe_path = None
        for root, dirs, files in os.walk(FOLDER):
            for file in files:
                if file.lower().endswith('.exe'):
                    exe_path = os.path.join(root, file)
                    break
            if exe_path:
                break
        if not exe_path:
            print('Не найден exe-файл после распаковки!')
            sys.exit(1)
        os.remove(dest_path)  # удаляем zip

    # Создаём ярлык на рабочем столе
    desktop = winshell.desktop()
    shortcut_path = os.path.join(desktop, 'Soft.lnk')
    create_shortcut(exe_path, shortcut_path)
    print('Установка завершена!')

if __name__ == '__main__':
    main() 