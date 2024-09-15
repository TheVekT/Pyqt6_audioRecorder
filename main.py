import sys
import json
import shutil
from datetime import datetime, timedelta
import numpy as np
import wave
import os
from datetime import datetime
from designe import Ui_MainWindow 
from mini import Ui_MiniWindow
from PyQt6 import QtGui, QtCore
from PyQt6.QtCore import QIODevice, QBuffer, QTimer, Qt, QPropertyAnimation, QRect, QEasingCurve, QRectF
from PyQt6.QtMultimedia import QMediaDevices, QAudioSource, QAudioFormat
from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox, QPushButton, QSlider, QLabel, QComboBox, QGraphicsOpacityEffect, QFileDialog
from PyQt6.QtGui import QIcon, QPainter, QColor, QPainterPath

class MiniWindow(QMainWindow):
    def __init__(self):
        super(MiniWindow, self).__init__()
        self.ui = Ui_MiniWindow()
        self.ui.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint |
                    QtCore.Qt.WindowType.WindowMinimizeButtonHint |
                    QtCore.Qt.WindowType.WindowSystemMenuHint |
                    QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        icon = QIcon(":/icons/icon.png")  # Specify the path to your icon
        self.setWindowIcon(icon)
        self.setWindowTitle("Диктофон")
        self.ui.label.mousePressEvent = self.label_mouse_press_event
        self.ui.label.mouseMoveEvent = self.label_mouse_move_event
        self.ui.label.mouseReleaseEvent = self.label_mouse_release_event
        self.ui.rec_timer_2.hide()
    def label_mouse_press_event(self, event):
        """Запоминаем начальные позиции при нажатии на метку."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.mouse_start_position = event.globalPosition().toPoint()
            self.window_start_position = self.frameGeometry().topLeft()

    def label_mouse_move_event(self, event):
        """Перемещаем окно при перемещении мыши."""
        if self.is_dragging:
            delta = event.globalPosition().toPoint() - self.mouse_start_position
            self.move(self.window_start_position + delta)

    def label_mouse_release_event(self, event):
        """Прекращаем перетаскивание при отпускании кнопки."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Устанавливаем цвет фона окна
        painter.setBrush(QColor(255, 255, 255))  # Белый фон, если необходимо
        painter.setPen(QtCore.Qt.PenStyle.NoPen)

        # Рисуем скругленный прямоугольник
        rect = self.rect()
        radius = 20
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), radius, radius)
        painter.drawPath(path)

        # Если хотите рисовать что-то поверх скругленного прямоугольника, например, фон
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOver)
        painter.setBrush(self.palette().window())
        painter.drawPath(path)

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.records_dir = './records'
        if not os.path.exists(self.records_dir):
            os.makedirs(self.records_dir)
        self.load_settings()
        self.setWindowTitle("Диктофон")
                # Убрать стандартную панель сверху и закруглить окно
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint |
                    QtCore.Qt.WindowType.WindowMinimizeButtonHint |
                    QtCore.Qt.WindowType.WindowSystemMenuHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(620, 315)  # Ширина и высота в пикселях
        self.is_recording = False
        icon = QIcon(":/icons/icon.png")  # Specify the path to your icon
        self.setWindowIcon(icon)

        # Переменные для хранения состояния перетаскивания окна
        self.is_dragging = False
        self.mouse_start_position = None
        self.window_start_position = None
        self.setup_animations()
        # Подключаем mouse-ивенты для метки
        self.ui.label_8.mousePressEvent = self.label_mouse_press_event
        self.ui.label_8.mouseMoveEvent = self.label_mouse_move_event
        self.ui.label_8.mouseReleaseEvent = self.label_mouse_release_event
        # Подключаем кнопки сворачивания и закрытия к методам
        self.ui.minimize.clicked.connect(self.minimize_window)
        self.ui.close.clicked.connect(self.close_window)

        self.mini_window = MiniWindow()
        self.mini_window.ui.full_scr.clicked.connect(self.restore_main_window)
        self.mini_window.ui.rec_pause.clicked.connect(self.pause_recording)
        self.mini_window.ui.rec_start.clicked.connect(self.start_recording)


        

        
        # Устанавливаем диапазон значений для первого слайдера
        self.ui.horizontalSlider.setMinimum(1)
        self.ui.horizontalSlider.setMaximum(7)
        self.ui.horizontalSlider.setTickInterval(1)
        self.ui.horizontalSlider.setSingleStep(1)
        
        # Подключаем сигнал изменения значения первого слайдера к слоту update_label_5
        self.ui.horizontalSlider.valueChanged.connect(self.update_label_5)
        
        # Обновляем метку при запуске, чтобы отображать текущее значение первого слайдера
        self.update_label_5(self.ui.horizontalSlider.value())

        # Устанавливаем диапазон значений для второго слайдера (от 0 до 20, шаг - 1)
        self.ui.horizontalSlider_2.setMinimum(0)
        self.ui.horizontalSlider_2.setMaximum(20)
        self.ui.horizontalSlider_2.setTickInterval(1)
        self.ui.horizontalSlider_2.setSingleStep(1)
        

        # Подключаем сигнал изменения значения второго слайдера к слоту update_label_4
        self.ui.horizontalSlider_2.valueChanged.connect(self.update_label_4)

        # Обновляем метку при запуске, чтобы отображать текущее значение второго слайдера
        self.update_label_4(self.ui.horizontalSlider_2.value())
        # Подключаем сигнал нажатия на кнопку к общему обработчику
        self.populate_microphones()


        self.recording_timer = QTimer()
        self.recording_timer.timeout.connect(self.update_timer_display)
        self.start_time = None
        self.elapsed_time = 0  # Время записи в секундах

                # Подключаем сигнал нажатия на кнопку к методам
                        # Подключаем кнопки паузы и продолжения
        self.ui.rec_pause.clicked.connect(self.pause_recording)
        self.ui.rec_continue.clicked.connect(self.resume_recording)
        self.ui.rec_start.clicked.connect(self.start_recording)
        self.ui.rec_stop.clicked.connect(self.stop_recording)
        # Подключаем кнопку выбора папки
        self.ui.pushButton.clicked.connect(self.choose_folder)
        self.ui.pushButton.setToolTip("Вибір папки збереження.")


        self.audio_source = None
        self.audio_file = None
        self.audio_buffer = None
        self.audio_data = bytearray()
        self.original_opacity_effects = {}
                # Новый флаг для отслеживания состояния паузы
        self.is_paused = False
        self.audio_data_paused = bytearray()



        self.segment_timer = QTimer()
        self.segment_timer.timeout.connect(self.check_recording_time)
        self.current_segment_start = None
        self.segment_duration = None

        # Инициализация таймера для мониторинга уровня звука
        self.sound_timer = QTimer()
        self.sound_timer.setInterval(100)  # Интервал проверки (в миллисекундах)
        self.sound_timer.timeout.connect(self.monitor_sound)
        self.sound_timer.start()
                # Подключаем событие изменения выбора в comboBox
        self.ui.comboBox.currentIndexChanged.connect(self.update_microphone)
        self.update_microphone()  # Устанавливаем аудио устройство по умолчанию


        
    def get_selected_interval(self):
        """Возвращает интервал времени в секундах на основе выбранной кнопки."""
        button = self.ui.buttonGroup.checkedButton()
        if button == self.ui.pushButton_4:
            return 10 * 60 # 10 минут
        elif button == self.ui.pushButton_5:
            return 30 * 60  # 30 минут
        elif button == self.ui.pushButton_6:
            return 60 * 60  # 60 минут
        elif button == self.ui.pushButton_7:
            return 120 * 60  # 120 минут
        return None
    def update_microphone(self):
        """Обновляет аудиоустройство на основе выбранного в comboBox."""
        selected_device_description = self.ui.comboBox.currentText()
        input_devices = QMediaDevices.audioInputs()
        selected_device = None

        for device in input_devices:
            if device.description() == selected_device_description:
                selected_device = device
                break

        if selected_device:
            format = QAudioFormat()
            format.setSampleRate(22050)
            format.setChannelCount(1)
            format.setSampleFormat(QAudioFormat.SampleFormat.Int16)

            self.audio_source_timer = QAudioSource(selected_device, format)
            self.audio_buffer_timer = self.audio_source_timer.start()
            
            if not self.audio_buffer_timer.isOpen():
                self.audio_buffer = None
        else:
            print("Выбранное устройство не найдено")

    def monitor_sound(self):
        """Мониторинг уровня звука и изменение иконки микрофона."""
        
        if self.audio_source_timer and self.audio_buffer_timer:
            
            data = self.audio_buffer_timer.readAll()

            if not data:
                print("No data available")
                return

            # Преобразование аудио данных в массив numpy для анализа уровня звука
            audio_array = np.frombuffer(data, dtype=np.int16)

            # Определяем средний уровень звука
            volume_level = np.abs(audio_array).mean()
            

            # Пороговое значение, чтобы определить, есть ли звук (регулируйте его)
            slider_value = self.ui.horizontalSlider_2.value() 
            
            threshold = 300 - slider_value * 10
            if volume_level > threshold:
                # Если звук превышает порог, делаем иконку зеленой
                self.ui.micro.setPixmap(QtGui.QPixmap(":/icons/micro_green.png"))
            else:
                # Если звука нет, возвращаем обычную иконку
                self.ui.micro.setPixmap(QtGui.QPixmap(":/icons/micro.png"))
        else:
            # Если аудио устройство не инициализировано, возвращаем обычную иконку
            self.ui.micro.setPixmap(QtGui.QPixmap(":/icons/micro.png"))




    def update_label_5(self, value):
        # Обновляем текст метки label_5 с сохранением стилей
        self.ui.label_5.setText(
            f'<html><head/><body><p align="center">'
            f'<span style="font-size:14pt; font-weight:600;">{value} Дн</span>'
            f'</p></body></html>'
        )

    def update_label_4(self, value):
        # Переводим значение слайдера в проценты (каждый шаг равен 5%)
        percentage = value * 5
        # Обновляем текст метки label_4 с сохранением стилей
        self.ui.label_4.setText(
            f'<html><head/><body><p align="center">'
            f'<span style="font-size:12pt; font-weight:600;">{percentage}%</span>'
            f'</p></body></html>'
        )
        

    def populate_microphones(self):
        # Получаем список всех доступных аудиоустройств ввода
        input_devices = QMediaDevices.audioInputs()

        # Очищаем comboBox перед заполнением
        self.ui.comboBox.clear()

        # Проверяем, есть ли доступные устройства ввода
        if not input_devices:
            self.ui.comboBox.addItem("Немає доступних пристроїв")
        else:
            # Добавляем доступные устройства ввода в comboBox
            for device in input_devices:
                self.ui.comboBox.addItem(device.description())

    def amplify_audio(self, data, gain):
        """
        Метод для усиления аудиоданных.
        data: исходные данные аудио (байтовый формат)
        gain: коэффициент усиления (например, 1.5 для 150%)
        """
        # Конвертируем байты в numpy массив для работы с числами
        audio_data = np.frombuffer(data, dtype=np.int16)
        
        # Применяем коэффициент усиления
        amplified_data = audio_data * gain

        # Убедимся, что значения не выходят за пределы диапазона int16
        amplified_data = np.clip(amplified_data, -32768, 32767)

        # Возвращаем данные в байтовом формате
        return amplified_data.astype(np.int16).tobytes()

    def start_recording(self):
        self.clean_old_records()
        if self.is_paused:
            # Если на паузе, продолжаем запись
            self.resume_recording()
        else:
            
            self.block_groupbox_elements(True)
            self.start_timer()

            selected_device_description = self.ui.comboBox.currentText()
            input_devices = QMediaDevices.audioInputs()
            selected_device = None
            for device in input_devices:
                if device.description() == selected_device_description:
                    selected_device = device
                    break

            if selected_device is None:
                QMessageBox.critical(self, "Помилка", "Вибраний пристрій не знайдено")
                self.ui.rec_start.setChecked(False)
                return

            format = QAudioFormat()
            format.setSampleRate(22050)
            format.setChannelCount(1)
            format.setSampleFormat(QAudioFormat.SampleFormat.Int16)

            self.audio_source = QAudioSource(selected_device, format)
            self.audio_buffer = QBuffer()
            self.audio_buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            self.is_recording = True
            self.start_time = datetime.now()
            date_folder = self.start_time.strftime("%d-%m-%Y")
            self.date_folder_path = os.path.join(self.records_dir, date_folder)
            if not os.path.exists(self.date_folder_path):
                os.makedirs(self.date_folder_path)

            self.file_name = self.start_time.strftime("%H-%M-%S") + ".wav"
            self.file_path = os.path.join(self.date_folder_path, self.file_name)

            slider_value = self.ui.horizontalSlider_2.value() * 10 / 100.0
            self.gain = 1 + slider_value

            self.audio_data = bytearray()
            self.audio_source.start(self.audio_buffer)
                        # Устанавливаем интервал сегмента
            self.segment_duration = self.get_selected_interval()
            self.current_segment_start = datetime.now()

            if self.segment_duration:
                self.segment_timer.start(1000)  # Проверяем каждую секунду
            self.ui.rec_pause.setCheckable(True)
            self.mini_window.ui.rec_pause.setCheckable(True)
            self.ui.rec_start.setChecked(True)
            self.mini_window.ui.rec_start.setChecked(True)
            self.animate_button(self.ui.rec_start, False)
            self.ui.rec_start.setEnabled(False)
            self.mini_window.ui.rec_start.setEnabled(False)
            


    def pause_recording(self):
        """Приостановка записи."""
        if self.audio_source and self.is_recording == True:
            self.is_paused = True
            self.audio_source.stop()
            if self.audio_buffer:
                self.audio_data.extend(self.audio_buffer.data())
                self.audio_buffer.close()
                self.audio_buffer = None
                self.recording_timer.stop()
                self.ui.rec_pause.setChecked(True)
                self.mini_window.ui.rec_pause.setChecked(True)
                self.animate_button(self.ui.rec_pause, False)
                self.mini_window.ui.rec_pause.setEnabled(False)
                self.ui.rec_pause.setEnabled(False)
                

    def resume_recording(self):
        """Возобновление записи."""
        if self.is_paused:
            self.is_paused = False
            self.audio_buffer = QBuffer()
            self.audio_buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            self.audio_source.start(self.audio_buffer)
            self.recording_timer.start()
            self.ui.rec_pause.setChecked(False)
            self.mini_window.ui.rec_pause.setChecked(False)
            self.mini_window.ui.rec_pause.setEnabled(True)
            self.ui.rec_pause.setEnabled(True)

    def stop_recording(self):
        if self.audio_source:
            self.audio_source.stop()
            self.audio_source = None

            if self.audio_buffer:
                self.audio_data.extend(self.audio_buffer.data())
                self.audio_buffer.close()
                self.audio_buffer = None

            # Сохраняем запись
            amplified_audio_data = self.amplify_audio(self.audio_data, self.gain)
            with wave.open(self.file_path, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(22050)
                wav_file.writeframes(amplified_audio_data)
            self.is_recording = False
            self.is_paused = False
            self.audio_data = bytearray()
            self.segment_timer.stop()
            self.ui.rec_pause.setCheckable(False)
            self.mini_window.ui.rec_pause.setCheckable(False)
            self.ui.rec_pause.setChecked(False)
            self.ui.rec_pause.setEnabled(True)
            self.ui.rec_start.setChecked(False)
            self.mini_window.ui.rec_start.setChecked(False)

            self.stop_timer()
            self.ui.rec_start.setEnabled(True)
            self.mini_window.ui.rec_pause.setEnabled(True)
            self.mini_window.ui.rec_start.setEnabled(True)
            self.block_groupbox_elements(False)



    def save_audio_data(self):
        # Получаем данные из буфера
        audio_data = self.audio_buffer.data()

        # Применяем усиление к аудиоданным
        amplified_audio_data = self.amplify_audio(audio_data, self.gain)

        # Указываем путь к файлу для записи
        file_path = os.path.join(self.records_dir, self.file_name)

        # Записываем данные в файл WAV
        with wave.open(file_path, 'wb') as wav_file:
            wav_file.setnchannels(1)         # Моно
            wav_file.setsampwidth(2)         # 2 байта для Int16
            wav_file.setframerate(22050)     # Уменьшенная частота дискретизации
            wav_file.writeframes(amplified_audio_data)
    def check_recording_time(self):
        if self.segment_duration:
            elapsed_time = (datetime.now() - self.current_segment_start).total_seconds()
            if elapsed_time >= self.segment_duration:
                self.stop_recording()
                self.start_recording()  # Начинаем новую запись
    def clean_old_records(self):
    # Получаем количество дней из положения слайдера
        days_to_keep = self.ui.horizontalSlider.value()
        
        # Получаем текущую дату
        today = datetime.now()

        # Проходим по всем папкам в основной папке для записей
        for folder_name in os.listdir(self.records_dir):
            folder_path = os.path.join(self.records_dir, folder_name)
            
            # Проверяем, является ли это папкой и соответствует ли она формату даты
            if os.path.isdir(folder_path):
                try:
                    folder_date = datetime.strptime(folder_name, "%d-%m-%Y")
                except ValueError:
                    continue  # Если формат неверный, пропускаем папку
                
                # Вычисляем разницу в днях между текущей датой и датой папки
                days_diff = (today - folder_date).days

                # Если папка старше указанного количества дней, удаляем её
                if days_diff > days_to_keep:
                    shutil.rmtree(folder_path)
                    print(f"Удалена папка: {folder_path}")
    def start_timer(self):
        """Запускает таймер и показывает элемент."""
        self.start_time = 0  # Устанавливаем начальное время
        self.elapsed_time = 0
        self.ui.rec_timer.show()  # Показываем QLabel
        self.mini_window.ui.rec_timer_2.show()
        self.recording_timer.start(1000)  # Запускаем таймер с интервалом 1 секунда
        self.ui.rec_timer.setText(f"<html><head/><body><p align=\"right\"><span style=\" font-size:11pt; font-weight:600;\">0:00:00</span></p></body></html>")

    def stop_timer(self):
        """Останавливает таймер, сбрасывает время и прячет элемент."""
        self.recording_timer.stop()  # Останавливаем таймер
        self.start_time = None
        self.elapsed_time = 0  # Сбрасываем время
        self.ui.rec_timer.hide()  # Прячем QLabel
        self.mini_window.ui.rec_timer_2.hide()

    def update_timer_display(self):
        """Обновляет отображение времени записи."""
        self.elapsed_time += 1
        
        # Преобразование секунд в часы, минуты и секунды
        hours = self.elapsed_time // 3600
        minutes = (self.elapsed_time % 3600) // 60
        seconds = self.elapsed_time % 60
        self.ui.rec_timer.setText(f"<html><head/><body><p align=\"right\"><span style=\" font-size:11pt; font-weight:600;\">{hours}:{minutes:02}:{seconds:02}</span></p></body></html>")
        self.mini_window.ui.rec_timer_2.setText(f"<html><head/><body><p align=\"center\"><span style=\" font-size:10pt; font-weight:600;\">{hours}:{minutes:02}:{seconds:02}</span></p></body></html>")

    def choose_folder(self):
        """Открывает диалог выбора папки и сохраняет выбранный путь."""
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения записей", self.records_dir)
        if folder:
            self.records_dir = folder
            # Обновляем настройки
            self.save_settings()
    def get_checked_button_text(self):
        checked_button = self.ui.buttonGroup.checkedButton()
        return checked_button.text() if checked_button else None
    def set_checked_button_by_text(self, text):
        for button in self.ui.buttonGroup.buttons():
            if button.text() == text:
                button.setChecked(True)
                break
    def reset_settings(self):
        """Сбрасывает настройки к значениям по умолчанию."""
        self.ui.horizontalSlider.setValue(1)
        self.ui.horizontalSlider_2.setValue(0)
        self.records_dir = './records'
        self.ui.buttonGroup.setExclusive(False)  # Чтобы не проверять кнопку по умолчанию
        self.ui.pushButton_4.setChecked(True)  # Установим кнопку по умолчанию (например, 10 минут)
        self.ui.buttonGroup.setExclusive(True)
        self.save_settings()

    def save_settings(self):
        settings = {
            'slider1_value': self.ui.horizontalSlider.value(),
            'slider2_value': self.ui.horizontalSlider_2.value(),
            'records_dir': self.records_dir,  # Сохраняем путь к папке
            'files_cut': self.ui.buttonGroup.checkedButton().objectName() if self.ui.buttonGroup.checkedButton() else None
        }
        
        with open('settings.json', 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)

    def load_settings(self):
        try:
            with open('settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # Устанавливаем значения для слайдеров
            if 'slider1_value' in settings:
                self.ui.horizontalSlider.setValue(settings['slider1_value'])
            if 'slider2_value' in settings:
                self.ui.horizontalSlider_2.setValue(settings['slider2_value'])
            if 'records_dir' in settings:
                self.records_dir = settings['records_dir']  # Загружаем путь к папке
            if 'files_cut' in settings:
                # Если в настройках указана кнопка, то устанавливаем её
                checked_button = settings.get('files_cut')
                if checked_button:
                    for button in self.ui.buttonGroup.buttons():
                        if button.objectName() == checked_button:
                            button.setChecked(True)
                            break
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Ошибка при загрузке настроек: {e}. Используем значения по умолчанию.")
            self.reset_settings()
    def block_groupbox_elements(self, block):
        """
        Блокирует или разблокирует все элементы внутри groupBox и изменяет их прозрачность.
        :param block: True для блокировки, False для разблокировки
        """
        if block:
            # Сохранение исходных эффектов прозрачности и установка полупрозрачности
            for element in self.ui.groupBox.findChildren((QPushButton, QSlider, QLabel, QComboBox)):
                if element.isEnabled():
                    effect = QGraphicsOpacityEffect()
                    effect.setOpacity(0.5)
                    element.setGraphicsEffect(effect)
                    self.original_opacity_effects[element] = effect
                    element.setEnabled(False)
        else:
            # Восстановление исходных эффектов прозрачности и разблокировка
            for element, effect in self.original_opacity_effects.items():
                element.setGraphicsEffect(None)  # Удаление эффекта прозрачности
                element.setEnabled(True)
            self.original_opacity_effects.clear()  # Очистка словаря
    def label_mouse_press_event(self, event):
        """Запоминаем начальные позиции при нажатии на метку."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.mouse_start_position = event.globalPosition().toPoint()
            self.window_start_position = self.frameGeometry().topLeft()

    def label_mouse_move_event(self, event):
        """Перемещаем окно при перемещении мыши."""
        if self.is_dragging:
            delta = event.globalPosition().toPoint() - self.mouse_start_position
            self.move(self.window_start_position + delta)

    def label_mouse_release_event(self, event):
        """Прекращаем перетаскивание при отпускании кнопки."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False
    def setup_animations(self):
        # Словарь для хранения анимаций и их состояний
        self.animations = {}
        self.original_rects = {}
        
        # Список кнопок, для которых нужно добавить анимацию
        buttons = [self.ui.rec_start, self.ui.rec_stop, self.ui.rec_pause, 
               self.ui.rec_continue, self.ui.pushButton_4, self.ui.pushButton_5, 
               self.ui.pushButton_6, self.ui.pushButton_7]
        # Настройка анимации для каждой кнопки
        for button in buttons:
            button.installEventFilter(self)
            self.original_rects[button] = button.geometry()
            animation = QtCore.QPropertyAnimation(button, b"geometry")
            animation.setDuration(200)  # Длительность анимации в миллисекундах
            animation.setEasingCurve(QtCore.QEasingCurve.Type.InOutQuad)
            self.animations[button] = animation
    
    def eventFilter(self, obj, event):
        if obj in self.animations:
            if event.type() == QtCore.QEvent.Type.Enter:
                self.animate_button(obj, increase=True)
            elif event.type() == QtCore.QEvent.Type.Leave:
                self.animate_button(obj, increase=False)
        return super(MainWindow, self).eventFilter(obj, event)
    
    def animate_button(self, button, increase):
        animation = self.animations[button]
        if self.is_button_blocked(button) is None:
            return  # Не применять анимацию, если кнопка заблокирована
        # Получаем начальные и конечные размеры для анимации
        start_rect = button.geometry()
        if increase:
            end_rect = start_rect.adjusted(-3, -3, 3, 3)  # Увеличиваем размеры
        else:
            end_rect = self.original_rects[button]  # Возвращаем к исходным размерам
        
        # Если анимация уже была запущена, останавливаем ее
        if animation.state() == QtCore.QAbstractAnimation.State.Running:
            animation.stop()
        
        animation.setStartValue(start_rect)
        animation.setEndValue(end_rect)
        animation.start()
    def is_button_blocked(self, button):
        """
        Проверяет, заблокирована ли кнопка.
        :param button: QPushButton
        :return: True если кнопка заблокирована, иначе False
        """
        if button.isEnabled():
            return True
        else:
            return None
    def minimize_window(self):
        self.hide()  # Скрываем текущее окно
        self.mini_window.show()  # Показываем окно MiniWindow
    def restore_main_window(self):
        """Метод для восстановления главного окна."""
        self.show()  # Показываем главное окно
        self.mini_window.hide()  # Скрываем окно MiniWindow
    def close_window(self):
        self.close()
    def closeEvent(self, event):
        # Сохранение настроек при закрытии приложения
        self.save_settings()
        event.accept()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Устанавливаем цвет фона окна
        painter.setBrush(QColor(255, 255, 255))  # Белый фон, если необходимо
        painter.setPen(QtCore.Qt.PenStyle.NoPen)

        # Рисуем скругленный прямоугольник
        rect = self.rect()
        radius = 20
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), radius, radius)
        painter.drawPath(path)

        # Если хотите рисовать что-то поверх скругленного прямоугольника, например, фон
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOver)
        painter.setBrush(self.palette().window())
        painter.drawPath(path)
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
