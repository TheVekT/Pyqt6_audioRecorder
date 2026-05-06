import sys
import json
import os
import wave
from datetime import datetime, timedelta
from shutil import rmtree

import numpy as np
from PyQt6.QtCore import (
    QIODevice, QBuffer, QTimer, Qt, QPropertyAnimation,
    QEasingCurve, QRectF, QEvent, QAbstractAnimation
)
from PyQt6.QtMultimedia import QMediaDevices, QAudioSource, QAudioFormat
from PyQt6.QtWidgets import (
    QMainWindow, QApplication, QMessageBox, QPushButton,
    QSlider, QLabel, QComboBox, QGraphicsOpacityEffect, QFileDialog
)
from PyQt6.QtGui import (
    QIcon, QPainter, QColor, QPainterPath, QFontDatabase,
    QMouseEvent, QPixmap
)

from designe import Ui_MainWindow
from mini import Ui_MiniWindow


class MiniWindow(QMainWindow):
    def __init__(self):
        super(MiniWindow, self).__init__()
        self.ui = Ui_MiniWindow()
        self.ui.setupUi(self)
        self.is_dragging = False
        self.mouse_start_position = None
        self.window_start_position = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowSystemMenuHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        icon = QIcon(":/icons/icon.png")
        self.setWindowIcon(icon)
        self.setWindowTitle("Диктофон")

        self.ui.label.mousePressEvent = self.label_mouse_press_event
        self.ui.label.mouseMoveEvent = self.label_mouse_move_event
        self.ui.label.mouseReleaseEvent = self.label_mouse_release_event
        self.ui.rec_timer_2.hide()
        self.font_id = QFontDatabase.addApplicationFont(":/icons/Oswald-VariableFont_wght.ttf")

    def label_mouse_press_event(self, event: QMouseEvent):
        """Store initial positions when pressing the label."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.mouse_start_position = event.globalPosition().toPoint()
            self.window_start_position = self.frameGeometry().topLeft()

    def label_mouse_move_event(self, event: QMouseEvent):
        """Move window during mouse movement."""
        if self.is_dragging:
            delta = event.globalPosition().toPoint() - self.mouse_start_position
            self.move(self.window_start_position + delta)

    def label_mouse_release_event(self, event: QMouseEvent):
        """Stop dragging when the button is released."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(Qt.PenStyle.NoPen)

        rect = self.rect()
        radius = 20
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), radius, radius)
        painter.drawPath(path)

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

        self.ui.pushButton.setToolTip("Вибір папки збереження.")
        self.load_settings()
        self.setWindowTitle("Диктофон")

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowSystemMenuHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(620, 315)
        self.is_recording = False
        icon = QIcon(":/icons/icon.png")
        self.setWindowIcon(icon)

        self.is_dragging = False
        self.mouse_start_position = None
        self.window_start_position = None
        self.setup_animations()

        self.ui.label_8.mousePressEvent = self.label_mouse_press_event
        self.ui.label_8.mouseMoveEvent = self.label_mouse_move_event
        self.ui.label_8.mouseReleaseEvent = self.label_mouse_release_event

        self.ui.minimize.clicked.connect(self.minimize_window)
        self.ui.close.clicked.connect(self.close_window)

        self.mini_window = MiniWindow()
        self.mini_window.ui.full_scr.clicked.connect(self.restore_main_window)
        self.mini_window.ui.rec_pause.clicked.connect(self.pause_recording)
        self.mini_window.ui.rec_start.clicked.connect(self.start_recording)

        self.ui.horizontalSlider.setMinimum(1)
        self.ui.horizontalSlider.setMaximum(7)
        self.ui.horizontalSlider.setTickInterval(1)
        self.ui.horizontalSlider.setSingleStep(1)
        self.ui.horizontalSlider.valueChanged.connect(self.update_label_5)
        self.update_label_5(self.ui.horizontalSlider.value())

        self.ui.horizontalSlider_2.setMinimum(0)
        self.ui.horizontalSlider_2.setMaximum(20)
        self.ui.horizontalSlider_2.setTickInterval(1)
        self.ui.horizontalSlider_2.setSingleStep(1)
        self.ui.horizontalSlider_2.valueChanged.connect(self.update_label_4)
        self.update_label_4(self.ui.horizontalSlider_2.value())

        self.populate_microphones()

        self.recording_timer = QTimer()
        self.recording_timer.timeout.connect(self.update_timer_display)
        self.start_time = None
        self.elapsed_time = 0

        self.ui.rec_pause.clicked.connect(self.pause_recording)
        self.ui.rec_continue.clicked.connect(self.resume_recording)
        self.ui.rec_start.clicked.connect(self.start_recording)
        self.ui.rec_stop.clicked.connect(self.stop_recording)
        self.ui.pushButton.clicked.connect(self.choose_folder)

        self.audio_source = None
        self.audio_source_timer = None
        self.audio_file = None
        self.audio_buffer = None
        self.audio_buffer_timer = None
        self.audio_data = bytearray()
        self.original_opacity_effects = {}
        self.is_paused = False
        self.audio_data_paused = bytearray()

        self.split_timer = None
        self.sound_timer = QTimer()
        self.sound_timer.setInterval(100)
        self.sound_timer.timeout.connect(self.monitor_sound)
        self.sound_timer.start()

        self.ui.comboBox.currentIndexChanged.connect(self.update_microphone)
        self.update_microphone()

    def get_selected_interval(self):
        """Return time interval in seconds based on the selected button."""
        button = self.ui.buttonGroup.checkedButton()
        if button == self.ui.pushButton_4:
            return 10 * 60
        elif button == self.ui.pushButton_5:
            return 30 * 60
        elif button == self.ui.pushButton_6:
            return 60 * 60
        elif button == self.ui.pushButton_7:
            return 120 * 60
        return None

    def update_microphone(self):
        """Update audio device based on comboBox selection."""
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

            if not selected_device.isFormatSupported(format):
                format = selected_device.preferredFormat()
                format.setSampleFormat(QAudioFormat.SampleFormat.Int16)

            self.audio_source_timer = QAudioSource(selected_device, format)
            self.audio_buffer_timer = self.audio_source_timer.start()

            if self.audio_buffer_timer is None:
                print("Failed to start audio source timer for monitoring")
            elif not self.audio_buffer_timer.isOpen():
                self.audio_buffer_timer = None
        else:
            self.audio_source_timer = None
            self.audio_buffer_timer = None

    def monitor_sound(self):
        """Monitor sound level and update microphone icon."""
        if self.audio_source_timer and self.audio_buffer_timer:
            data = self.audio_buffer_timer.readAll()
            if not data:
                return

            audio_array = np.frombuffer(data, dtype=np.int16)
            volume_level = np.abs(audio_array).mean()

            slider_value = self.ui.horizontalSlider_2.value()
            threshold = 150 - slider_value * 6
            if volume_level > threshold:
                self.ui.micro.setPixmap(QPixmap(":/icons/micro_green.png"))
            else:
                self.ui.micro.setPixmap(QPixmap(":/icons/micro.png"))
        else:
            self.ui.micro.setPixmap(QPixmap(":/icons/micro.png"))

    def get_next_split_time(self, now: datetime) -> datetime:
        """Calculate the nearest 'round' time point for the selected pattern."""
        interval = self.get_selected_interval()
        if interval is None:
            return now + timedelta(hours=1)
        
        pattern = interval / 60
        dt = now.replace(second=0, microsecond=0)

        if pattern == 10:
            minute = dt.minute
            slot_10 = (minute // 10) + 1
            next_m = slot_10 * 10
            if next_m >= 60:
                return dt.replace(minute=0) + timedelta(hours=1)
            return dt.replace(minute=next_m)

        elif pattern == 30:
            if dt.minute < 30:
                return dt.replace(minute=30)
            return dt.replace(minute=0) + timedelta(hours=1)

        elif pattern == 60:
            return dt.replace(minute=0) + timedelta(hours=1)

        elif pattern == 120:
            dt = dt.replace(minute=0)
            if dt.hour % 2 != 0:
                dt = dt + timedelta(hours=1)
            return dt + timedelta(hours=2)

        return dt + timedelta(hours=1)

    def schedule_next_split(self):
        if self.split_timer is not None:
            self.split_timer.stop()

        now = datetime.now()
        next_dt = self.get_next_split_time(now)
        print(f'Scheduled split time: {next_dt}')
        delta = (next_dt - now).total_seconds()
        ms = max(int(delta * 1000), 0)

        self.split_timer = QTimer(self)
        self.split_timer.setSingleShot(True)

        def split_record():
            if self.is_recording and not self.is_paused:
                self.stop_recording()
                self.start_recording()
            elif self.is_paused:
                self.schedule_next_split()

        self.split_timer.timeout.connect(split_record)
        self.split_timer.start(ms)

    def update_label_5(self, value):
        self.ui.label_5.setText(
            f'<html><head/><body><p align="center">'
            f'<span style="font-size:14pt; font-weight:600;">{value} Дн</span>'
            f'</p></body></html>'
        )

    def update_label_4(self, value):
        percentage = value * 5
        self.ui.label_4.setText(
            f'<html><head/><body><p align="center">'
            f'<span style="font-size:12pt; font-weight:600;">{percentage}%</span>'
            f'</p></body></html>'
        )

    def populate_microphones(self):
        input_devices = QMediaDevices.audioInputs()
        self.ui.comboBox.clear()

        if not input_devices:
            self.ui.comboBox.addItem("Немає доступних пристроїв")
        else:
            for device in input_devices:
                self.ui.comboBox.addItem(device.description())

    def amplify_audio(self, data, gain):
        """Method to amplify audio data. gain: amplification factor."""
        audio_data = np.frombuffer(data, dtype=np.int16)
        amplified_data = audio_data * gain
        amplified_data = np.clip(amplified_data, -32768, 32767)
        return amplified_data.astype(np.int16).tobytes()

    def start_recording(self):
        self.clean_old_records()
        if self.is_paused:
            self.resume_recording()
        else:
            self.block_groupbox_elements(True)
            self.start_timer()

            selected_device_description = self.ui.comboBox.currentText()
            input_devices = QMediaDevices.audioInputs()
            selected_device = None

            if not os.path.exists(self.records_dir):
                os.makedirs(self.records_dir)

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

            self.file_name = f"{self.start_time.strftime('%H-%M-%S')}.wav"
            self.file_path = os.path.join(self.date_folder_path, self.file_name)

            slider_value = self.ui.horizontalSlider_2.value() * 10 / 100.0
            self.gain = (1 + slider_value * 2) * 1.2

            self.audio_data = bytearray()
            self.audio_source.start(self.audio_buffer)
            self.ui.rec_pause.setCheckable(True)
            self.mini_window.ui.rec_pause.setCheckable(True)
            self.ui.rec_start.setChecked(True)
            self.mini_window.ui.rec_start.setChecked(True)
            self.animate_button(self.ui.rec_start, False)
            self.ui.rec_start.setEnabled(False)
            self.mini_window.ui.rec_start.setEnabled(False)

    def pause_recording(self):
        """Pause recording."""
        if self.audio_source and self.is_recording:
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
        """Resume recording."""
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

            amplified_audio_data = self.amplify_audio(self.audio_data, self.gain)
            with wave.open(self.file_path, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(22050)
                wav_file.writeframes(amplified_audio_data)

            self.is_recording = False
            self.is_paused = False
            self.audio_data = bytearray()
            self.ui.rec_pause.setCheckable(False)
            self.mini_window.ui.rec_pause.setCheckable(False)
            self.ui.rec_pause.setChecked(False)
            self.ui.rec_pause.setEnabled(True)
            self.ui.rec_start.setChecked(False)
            self.mini_window.ui.rec_start.setChecked(False)

            if self.split_timer:
                self.split_timer.stop()
            self.stop_timer()
            self.ui.rec_start.setEnabled(True)
            self.mini_window.ui.rec_pause.setEnabled(True)
            self.mini_window.ui.rec_start.setEnabled(True)
            self.block_groupbox_elements(False)
            if not os.path.exists(self.records_dir):
                os.makedirs(self.records_dir)

    def save_audio_data(self):
        if not os.path.exists(self.records_dir):
            os.makedirs(self.records_dir)
        audio_data = self.audio_buffer.data()
        amplified_audio_data = self.amplify_audio(audio_data, self.gain)
        file_path = os.path.join(self.records_dir, self.file_name)

        with wave.open(file_path, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(22050)
            wav_file.writeframes(amplified_audio_data)

    def clean_old_records(self):
        if not os.path.exists(self.records_dir):
            os.makedirs(self.records_dir)

        days_to_keep = self.ui.horizontalSlider.value()
        today = datetime.now()

        for folder_name in os.listdir(self.records_dir):
            folder_path = os.path.join(self.records_dir, folder_name)
            if os.path.isdir(folder_path):
                try:
                    folder_date = datetime.strptime(folder_name, "%d-%m-%Y")
                except ValueError:
                    continue

                days_diff = (today - folder_date).days
                if days_diff > days_to_keep:
                    rmtree(folder_path)
                    print(f"Deleted folder: {folder_path}")

    def start_timer(self):
        """Start timer and show the element."""
        self.start_time = 0
        self.elapsed_time = 0
        self.ui.rec_timer.show()
        self.mini_window.ui.rec_timer_2.show()
        self.recording_timer.start(1000)
        self.ui.rec_timer.setText(
            "<html><head/><body><p align=\"right\">"
            "<span style=\" font-size:11pt; font-weight:600;\">0:00:00</span></p></body></html>"
        )

    def stop_timer(self):
        """Stop timer, reset time, and hide the element."""
        self.recording_timer.stop()
        self.start_time = None
        self.elapsed_time = 0
        self.ui.rec_timer.hide()
        self.mini_window.ui.rec_timer_2.hide()

    def update_timer_display(self):
        """Update recording time display."""
        self.elapsed_time += 1
        if self.elapsed_time == 60:
            self.schedule_next_split()

        hours = self.elapsed_time // 3600
        minutes = (self.elapsed_time % 3600) // 60
        seconds = self.elapsed_time % 60
        self.ui.rec_timer.setText(
            f"<html><head/><body><p align=\"right\"><span style=\" font-size:11pt; font-weight:600;\">"
            f"{hours}:{minutes:02}:{seconds:02}</span></p></body></html>"
        )
        self.mini_window.ui.rec_timer_2.setText(
            f"<html><head/><body><p align=\"center\"><span style=\" font-size:10pt; font-weight:600;\">"
            f"{hours}:{minutes:02}:{seconds:02}</span></p></body></html>"
        )

    def choose_folder(self):
        """Open folder selection dialog and save the selected path."""
        folder = QFileDialog.getExistingDirectory(self, "Виберіть папку для збереження записів.", self.records_dir)
        if folder:
            self.records_dir = folder
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
        """Reset settings to default."""
        self.ui.horizontalSlider.setValue(1)
        self.ui.horizontalSlider_2.setValue(0)
        self.records_dir = './records'
        self.ui.buttonGroup.setExclusive(False)
        self.ui.pushButton_4.setChecked(True)
        self.ui.buttonGroup.setExclusive(True)
        self.save_settings()

    def save_settings(self):
        settings = {
            'slider1_value': self.ui.horizontalSlider.value(),
            'slider2_value': self.ui.horizontalSlider_2.value(),
            'records_dir': self.records_dir,
            'files_cut': self.ui.buttonGroup.checkedButton().objectName() if self.ui.buttonGroup.checkedButton() else None
        }
        with open('settings.json', 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=4)

    def load_settings(self):
        try:
            with open('settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)

            if 'slider1_value' in settings:
                self.ui.horizontalSlider.setValue(settings['slider1_value'])
            if 'slider2_value' in settings:
                self.ui.horizontalSlider_2.setValue(settings['slider2_value'])
            if 'records_dir' in settings:
                self.records_dir = settings['records_dir']
                path = os.path.normpath(os.path.join(os.getcwd(), self.records_dir))
                self.ui.pushButton.setToolTip(f"{path}")
            if 'files_cut' in settings:
                checked_button = settings.get('files_cut')
                if checked_button:
                    for button in self.ui.buttonGroup.buttons():
                        if button.objectName() == checked_button:
                            button.setChecked(True)
                            break
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading settings: {e}. Using defaults.")
            self.reset_settings()

    def block_groupbox_elements(self, block):
        """Block or unblock elements inside groupBox and change opacity."""
        if block:
            for element in self.ui.groupBox.findChildren((QPushButton, QSlider, QLabel, QComboBox)):
                if element.isEnabled():
                    effect = QGraphicsOpacityEffect()
                    effect.setOpacity(0.5)
                    element.setGraphicsEffect(effect)
                    self.original_opacity_effects[element] = effect
                    element.setEnabled(False)
        else:
            for element, effect in self.original_opacity_effects.items():
                element.setGraphicsEffect(None)
                element.setEnabled(True)
            self.original_opacity_effects.clear()

    def label_mouse_press_event(self, event):
        """Store initial positions on label press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.mouse_start_position = event.globalPosition().toPoint()
            self.window_start_position = self.frameGeometry().topLeft()

    def label_mouse_move_event(self, event):
        """Move window on mouse move."""
        if self.is_dragging:
            delta = event.globalPosition().toPoint() - self.mouse_start_position
            self.move(self.window_start_position + delta)

    def label_mouse_release_event(self, event):
        """Stop dragging on button release."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False

    def setup_animations(self):
        self.animations = {}
        self.original_rects = {}
        buttons = [
            self.ui.rec_start, self.ui.rec_stop, self.ui.rec_pause,
            self.ui.rec_continue, self.ui.pushButton_4, self.ui.pushButton_5,
            self.ui.pushButton_6, self.ui.pushButton_7
        ]
        for button in buttons:
            button.installEventFilter(self)
            self.original_rects[button] = button.geometry()
            animation = QPropertyAnimation(button, b"geometry")
            animation.setDuration(200)
            animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
            self.animations[button] = animation

    def eventFilter(self, obj, event):
        if obj in self.animations:
            if event.type() == QEvent.Type.Enter:
                self.animate_button(obj, increase=True)
            elif event.type() == QEvent.Type.Leave:
                self.animate_button(obj, increase=False)
        return super(MainWindow, self).eventFilter(obj, event)

    def animate_button(self, button, increase):
        animation = self.animations[button]
        if self.is_button_blocked(button) is None:
            return

        start_rect = button.geometry()
        if increase:
            end_rect = start_rect.adjusted(-3, -3, 3, 3)
        else:
            end_rect = self.original_rects[button]

        if animation.state() == QAbstractAnimation.State.Running:
            animation.stop()

        animation.setStartValue(start_rect)
        animation.setEndValue(end_rect)
        animation.start()

    def is_button_blocked(self, button):
        """Check if the button is blocked."""
        if button.isEnabled():
            return True
        return None

    def minimize_window(self):
        self.hide()
        self.mini_window.show()

    def restore_main_window(self):
        """Restore main window."""
        self.show()
        self.mini_window.hide()

    def close_window(self):
        self.close()

    def closeEvent(self, event):
        self.save_settings()
        if self.is_recording:
            self.stop_recording()
        event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(Qt.PenStyle.NoPen)

        rect = self.rect()
        radius = 20
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), radius, radius)
        painter.drawPath(path)

        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOver)
        painter.setBrush(self.palette().window())
        painter.drawPath(path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
