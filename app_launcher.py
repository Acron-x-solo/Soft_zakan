import sys
import os
import json
import urllib.request
import zipfile
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QListWidget, QHBoxLayout, QMessageBox, QLineEdit, QLabel, QDialog, QInputDialog, QProgressDialog
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from PIL import Image

APP_LIST_FILE = 'apps.json'
BACKGROUND_IMAGE = 'background.jpg'  # Имя файла для фоновой картинки
ARCHIVES_FILE = 'archives.json'
APP_LIST_URL = 'https://www.dropbox.com/scl/fi/wpzwn6gixwn6z21ryl12r/apps.json?rlkey=czenqd5zpy4vfwn4c21w79bqf&st=z7fx4xok&dl=1'  # Укажите свой URL
ARCHIVES_URL = 'https://www.dropbox.com/scl/fi/kf91ljvcl2e9fq02vf4j1/archives.json?rlkey=ajqy1knl9bhemhsutzois4iva&st=ijqwj7go&dl=1'  # Укажите свой URL

class AdminPanel(QDialog):
    def __init__(self, apps, add_callback, delete_callback, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Админ-панель (требуется пароль)')
        self.setMinimumSize(420, 350)
        self.setModal(True)
        self.setStyleSheet(parent.dark_stylesheet() if parent else "")
        self.apps = apps
        self.add_callback = add_callback
        self.delete_callback = delete_callback
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.label = QLabel('Введите пароль:')
        layout.addWidget(self.label)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)
        self.check_btn = QPushButton('Проверить пароль')
        self.check_btn.clicked.connect(self.check_password)
        layout.addWidget(self.check_btn)
        # Кнопка обновления списков
        self.update_btn = QPushButton('Обновить списки с сервера')
        self.update_btn.clicked.connect(self.update_lists_from_server)
        layout.addWidget(self.update_btn)
        # Панель управления
        self.panel_widget = QWidget()
        self.panel_layout = QVBoxLayout()
        self.panel_layout.setContentsMargins(0, 0, 0, 0)
        self.panel_layout.setSpacing(10)
        self.panel_widget.setLayout(self.panel_layout)
        self.panel_widget.setVisible(False)
        self.apps_list = QListWidget()
        self.apps_list.setMinimumHeight(100)
        self.apps_list.setSizePolicy(self.apps_list.sizePolicy().horizontalPolicy(), 7)
        self.update_list()
        self.panel_layout.addWidget(QLabel('Приложения:'))
        self.panel_layout.addWidget(self.apps_list, stretch=1)
        btns = QHBoxLayout()
        btns.setSpacing(10)
        self.add_btn = QPushButton('Добавить приложение')
        self.add_btn.clicked.connect(self.add_app)
        btns.addWidget(self.add_btn)
        self.add_url_btn = QPushButton('Добавить по ссылке')
        self.add_url_btn.clicked.connect(self.add_by_url)
        btns.addWidget(self.add_url_btn)
        self.install_zip_btn = QPushButton('Установить из архива')
        self.install_zip_btn.clicked.connect(self.install_from_zip)
        btns.addWidget(self.install_zip_btn)
        self.unpack_zip_btn = QPushButton('Распаковать архив')
        self.unpack_zip_btn.clicked.connect(self.unpack_zip)
        btns.addWidget(self.unpack_zip_btn)
        self.del_btn = QPushButton('Удалить выбранное')
        self.del_btn.clicked.connect(self.delete_selected)
        btns.addWidget(self.del_btn)
        self.panel_layout.addLayout(btns)
        # Раздел для ссылок на архивы
        self.panel_layout.addWidget(QLabel('Ссылки на архивы:'))
        self.archives_list = QListWidget()
        self.update_archives_list()
        self.panel_layout.addWidget(self.archives_list)
        arch_btns = QHBoxLayout()
        self.add_arch_btn = QPushButton('Добавить ссылку на архив')
        self.add_arch_btn.clicked.connect(self.add_archive_link)
        arch_btns.addWidget(self.add_arch_btn)
        self.del_arch_btn = QPushButton('Удалить ссылку')
        self.del_arch_btn.clicked.connect(self.delete_archive_link)
        arch_btns.addWidget(self.del_arch_btn)
        self.panel_layout.addLayout(arch_btns)
        layout.addWidget(self.panel_widget, stretch=1)
        self.setLayout(layout)

    def check_password(self):
        if self.password_input.text() == '1111':
            self.panel_widget.setVisible(True)
            self.label.setText('Админ-панель')
            self.password_input.hide()
            self.check_btn.hide()
        else:
            QMessageBox.warning(self, 'Ошибка', 'Неверный пароль!')

    def add_app(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Выберите приложение', '', 'Программы (*.exe *.py)')
        if file_path:
            self.add_callback(file_path)
            self.update_list()

    def add_by_url(self):
        url, ok = QInputDialog.getText(self, 'Добавить по ссылке', 'Введите ссылку на exe-файл:')
        if ok and url:
            try:
                local_name = os.path.basename(url.split('?')[0])
                local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), local_name)
                urllib.request.urlretrieve(url, local_path)
                self.add_callback(local_path)
                QMessageBox.information(self, 'Успех', f'Файл скачан и добавлен: {local_name}')
                self.update_list()
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Не удалось скачать файл:\n{e}')

    def delete_selected(self):
        selected = self.apps_list.currentRow()
        if selected >= 0:
            self.delete_callback(selected)
            self.update_list()

    def update_list(self):
        self.apps_list.clear()
        for app in self.apps:
            self.apps_list.addItem(app)

    def install_from_zip(self):
        zip_path, _ = QFileDialog.getOpenFileName(self, 'Выберите архив', '', 'Архивы (*.zip)')
        if zip_path:
            try:
                base_dir = os.path.splitext(os.path.basename(zip_path))[0]
                extract_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), base_dir)
                os.makedirs(extract_path, exist_ok=True)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
                # Поиск первого exe-файла
                exe_path = None
                for root, dirs, files in os.walk(extract_path):
                    for file in files:
                        if file.lower().endswith('.exe'):
                            exe_path = os.path.join(root, file)
                            break
                    if exe_path:
                        break
                if exe_path:
                    self.add_callback(exe_path)
                    QMessageBox.information(self, 'Успех', f'Архив распакован и приложение добавлено: {exe_path}')
                else:
                    QMessageBox.warning(self, 'Внимание', 'Архив распакован, но exe-файл не найден.')
                self.update_list()
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Не удалось распаковать архив:\n{e}')

    def unpack_zip(self):
        zip_path, _ = QFileDialog.getOpenFileName(self, 'Выберите архив', '', 'Архивы (*.zip)')
        if zip_path:
            try:
                base_dir = os.path.splitext(os.path.basename(zip_path))[0]
                extract_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), base_dir)
                os.makedirs(extract_path, exist_ok=True)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
                QMessageBox.information(self, 'Успех', f'Архив распакован в папку: {extract_path}')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Не удалось распаковать архив:\n{e}')

    def update_archives_list(self):
        self.archives_list.clear()
        archives = AppLauncher.load_archives()
        for item in archives:
            self.archives_list.addItem(item['name'])

    def add_archive_link(self):
        url, ok2 = QInputDialog.getText(self, 'Добавить ссылку на архив', 'Введите ссылку на zip-архив:')
        if not (ok2 and url):
            return
        default_name = os.path.splitext(os.path.basename(url.split('?')[0]))[0]
        name, ok1 = QInputDialog.getText(self, 'Название архива', f'Введите название архива:', text=default_name)
        if not (ok1 and name):
            return
        try:
            archives = AppLauncher.load_archives()
            if not any(a['url'] == url for a in archives):
                archives.append({'name': name, 'url': url})
                AppLauncher.save_archives(archives)
            self.update_archives_list()
        except Exception as e:
            print(f'Ошибка при добавлении архива: {e}')
            QMessageBox.critical(self, 'Ошибка', f'Не удалось сохранить архив:\n{e}')

    def delete_archive_link(self):
        row = self.archives_list.currentRow()
        if row >= 0:
            archives = AppLauncher.load_archives()
            del archives[row]
            AppLauncher.save_archives(archives)
            self.update_archives_list()

    def update_lists_from_server(self):
        import urllib.request
        try:
            if APP_LIST_URL:
                urllib.request.urlretrieve(APP_LIST_URL, APP_LIST_FILE)
            if ARCHIVES_URL:
                urllib.request.urlretrieve(ARCHIVES_URL, ARCHIVES_FILE)
            QMessageBox.information(self, 'Успех', 'Списки успешно обновлены!')
            self.update_list()
            self.update_archives_list()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось обновить списки:\n{e}')

class AppLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Soft')
        self.setGeometry(100, 100, 500, 400)
        self.setStyleSheet(self.dark_stylesheet())
        AppLauncher.update_lists_from_server()
        self.apps = []
        self.load_apps()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.update_list()
        layout.addWidget(self.list_widget)
        btn_layout = QHBoxLayout()
        self.admin_btn = QPushButton('Админ-панель')
        self.admin_btn.clicked.connect(self.open_admin_panel)
        btn_layout.addWidget(self.admin_btn)
        self.run_btn = QPushButton('Запустить выбранное')
        self.run_btn.clicked.connect(self.run_selected)
        btn_layout.addWidget(self.run_btn)
        self.install_from_archive_btn = QPushButton('Установить приложение из архива')
        self.install_from_archive_btn.clicked.connect(self.install_from_archive_link)
        btn_layout.addWidget(self.install_from_archive_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def dark_stylesheet(self):
        return f"""
            QWidget {{
                background-color: #181818;
                color: #f0f0f0;
                font-size: 16px;
            }}
            QPushButton {{
                background-color: #232323;
                color: #f0f0f0;
                border: 1px solid #333;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: #333333;
            }}
            QListWidget {{
                background-image: url('{BACKGROUND_IMAGE}');
                background-repeat: no-repeat;
                background-position: center;
                background-attachment: fixed;
                background-size: contain;
                color: #f0f0f0;
                border: 1px solid #333;
                font-size: 16px;
            }}
        """

    def open_admin_panel(self):
        self.admin_panel = AdminPanel(self.apps, self.add_app, self.delete_app, parent=self)
        self.admin_panel.exec_()

    def add_app(self, file_path):
        if file_path not in self.apps:
            self.apps.append(file_path)
            self.save_apps()
            self.update_list()
        else:
            QMessageBox.information(self, 'Информация', 'Это приложение уже добавлено.')

    def delete_app(self, index):
        if 0 <= index < len(self.apps):
            del self.apps[index]
            self.save_apps()
            self.update_list()

    def run_selected(self):
        selected = self.list_widget.currentRow()
        if selected >= 0:
            app_path = self.apps[selected]
            try:
                if app_path.lower().endswith('.py'):
                    subprocess.Popen([sys.executable, app_path], shell=True)
                else:
                    os.startfile(app_path)
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Не удалось запустить приложение:\n{e}')
        else:
            QMessageBox.information(self, 'Информация', 'Выберите приложение для запуска.')

    def update_list(self):
        self.list_widget.clear()
        for app in self.apps:
            self.list_widget.addItem(app)

    def load_apps(self):
        if os.path.exists(APP_LIST_FILE):
            try:
                with open(APP_LIST_FILE, 'r', encoding='utf-8') as f:
                    self.apps = json.load(f)
            except Exception:
                self.apps = []
        if not self.apps:
            # Добавляем примеры приложений
            notepad = r'C:\Windows\System32\notepad.exe'
            calc = r'C:\Windows\System32\calc.exe'
            examples = [notepad, calc]
            for ex in examples:
                if os.path.exists(ex):
                    self.apps.append(ex)
            self.save_apps()

    def save_apps(self):
        with open(APP_LIST_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.apps, f, ensure_ascii=False, indent=2)

    def install_from_archive_link(self):
        archives = AppLauncher.load_archives()
        if not archives:
            QMessageBox.information(self, 'Нет архивов', 'Нет доступных архивов для установки.')
            return
        from PyQt5.QtWidgets import QInputDialog
        names = [a['name'] for a in archives]
        name, ok = QInputDialog.getItem(self, 'Установка из архива', 'Выберите архив для установки:', names, 0, False)
        if ok and name:
            archive = next((a for a in archives if a['name'] == name), None)
            if not archive:
                QMessageBox.warning(self, 'Ошибка', 'Архив не найден.')
                return
            url = archive['url']
            try:
                local_name = os.path.basename(url.split('?')[0])
                local_zip = os.path.join(os.path.dirname(os.path.abspath(__file__)), local_name)
                # Прогресс-бар для скачивания
                progress = QProgressDialog('Скачивание архива...', 'Отмена', 0, 100, self)
                progress.setWindowTitle('Установка архива')
                progress.setWindowModality(Qt.WindowModal)
                progress.setValue(0)
                canceled = False
                def reporthook(blocknum, blocksize, totalsize):
                    nonlocal canceled
                    if totalsize > 0:
                        percent = int(blocknum * blocksize * 100 / totalsize)
                        progress.setValue(min(percent, 100))
                        QApplication.processEvents()
                        if progress.wasCanceled():
                            canceled = True
                            raise Exception('Скачивание отменено пользователем.')
                try:
                    urllib.request.urlretrieve(url, local_zip, reporthook)
                except Exception as e:
                    if canceled or progress.wasCanceled():
                        if os.path.exists(local_zip):
                            os.remove(local_zip)
                        QMessageBox.information(self, 'Отмена', 'Скачивание архива отменено.')
                        return
                    else:
                        raise
                progress.setValue(100)
                if not os.path.exists(local_zip):
                    raise Exception('Файл не был скачан.')
                if not zipfile.is_zipfile(local_zip):
                    raise Exception('Скачанный файл не является zip-архивом.')
                # Прогресс-бар для распаковки
                with zipfile.ZipFile(local_zip, 'r') as zip_ref:
                    filelist = zip_ref.namelist()
                    extract_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.path.splitext(local_name)[0])
                    os.makedirs(extract_path, exist_ok=True)
                    progress2 = QProgressDialog('Распаковка архива...', 'Отмена', 0, len(filelist), self)
                    progress2.setWindowTitle('Распаковка архива')
                    progress2.setWindowModality(Qt.WindowModal)
                    canceled_unpack = False
                    for i, file in enumerate(filelist):
                        if progress2.wasCanceled():
                            canceled_unpack = True
                            break
                        zip_ref.extract(file, extract_path)
                        progress2.setValue(i + 1)
                        QApplication.processEvents()
                    progress2.setValue(len(filelist))
                    if canceled_unpack:
                        # Удаляем распакованные файлы
                        import shutil
                        shutil.rmtree(extract_path, ignore_errors=True)
                        QMessageBox.information(self, 'Отмена', 'Распаковка архива отменена.')
                        return
                exe_path = None
                for root, dirs, files in os.walk(extract_path):
                    for file in files:
                        if file.lower().endswith('.exe'):
                            exe_path = os.path.join(root, file)
                            break
                    if exe_path:
                        break
                if exe_path:
                    self.add_app(exe_path)
                    QMessageBox.information(self, 'Успех', f'Архив установлен и приложение добавлено: {exe_path}')
                else:
                    QMessageBox.warning(self, 'Внимание', 'Архив распакован, но exe-файл не найден.')
                archives = [a for a in archives if a['name'] != name]
                AppLauncher.save_archives(archives)
            except Exception as e:
                import traceback
                print(traceback.format_exc())
                QMessageBox.critical(self, 'Ошибка', f'Не удалось установить архив:\n{e}')

    @staticmethod
    def load_archives():
        if os.path.exists(ARCHIVES_FILE):
            try:
                with open(ARCHIVES_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Миграция старого формата (список ссылок)
                    if data and isinstance(data[0], str):
                        data = [{'name': f'Архив {i+1}', 'url': url} for i, url in enumerate(data)]
                        AppLauncher.save_archives(data)
                    return data
            except Exception:
                return []
        return []

    @staticmethod
    def save_archives(archives):
        try:
            with open(ARCHIVES_FILE, 'w', encoding='utf-8') as f:
                json.dump(archives, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f'Ошибка при сохранении {ARCHIVES_FILE}: {e}')

    @staticmethod
    def update_lists_from_server():
        import urllib.request
        try:
            if APP_LIST_URL:
                urllib.request.urlretrieve(APP_LIST_URL, APP_LIST_FILE)
            if ARCHIVES_URL:
                urllib.request.urlretrieve(ARCHIVES_URL, ARCHIVES_FILE)
        except Exception as e:
            print(f'Не удалось обновить списки при запуске: {e}')

def resize_background_image():
    try:
        if os.path.exists(BACKGROUND_IMAGE):
            img = Image.open(BACKGROUND_IMAGE)
            max_width = 800
            if img.width > max_width:
                ratio = max_width / img.width
                new_size = (max_width, int(img.height * ratio))
                # Используем Resampling.LANCZOS для новых версий Pillow
                try:
                    resample = Image.Resampling.LANCZOS
                except AttributeError:
                    resample = Image.LANCZOS
                img = img.resize(new_size, resample)
                img.save(BACKGROUND_IMAGE)
    except Exception as e:
        print(f'Ошибка при уменьшении фонового изображения: {e}')

def main():
    resize_background_image()
    app = QApplication(sys.argv)
    launcher = AppLauncher()
    launcher.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 