import os
import sys
import shutil
import subprocess

FILES_TO_INCLUDE = [
    'background.jpg',
    'archives.json',
    'apps.json',
]
SCRIPT = 'app_launcher.py'
EXE_NAME = 'app_launcher.exe'

# Проверка наличия файлов
missing = [f for f in FILES_TO_INCLUDE + [SCRIPT] if not os.path.exists(f)]
if missing:
    print('Не найдены файлы:', ', '.join(missing))
    sys.exit(1)

# Формируем параметры для PyInstaller
add_data = []
for f in FILES_TO_INCLUDE:
    add_data.extend(['--add-data', f'{f};.'])

cmd = [
    sys.executable, '-m', 'PyInstaller',
    '--onefile', '--noconsole',
    *add_data,
    '--name', EXE_NAME.replace('.exe', ''),
    SCRIPT
]

print('Собираю exe-файл...')
res = subprocess.run(cmd)
if res.returncode != 0:
    print('Ошибка сборки!')
    sys.exit(1)

# Копируем нужные файлы в dist (на всякий случай)
dist_dir = os.path.join('dist')
for f in FILES_TO_INCLUDE:
    shutil.copy2(f, dist_dir)

print(f'Готово! Файл dist/{EXE_NAME} создан.') 