import sys
print(sys.version)
print(sys.path)
import librosa
import os
import random
import tkinter as tk
from pathlib import Path
from tkinter import filedialog
import matplotlib.pyplot as plt
import numpy as np
import sounddevice as sd
import soundfile as sf
from pydub import AudioSegment
from pedalboard import Pedalboard, HighpassFilter, LowpassFilter, Reverb, Delay, LowShelfFilter, HighShelfFilter
from tkinter import Toplevel, Text, Button, Scrollbar
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mutagen.easyid3 import EasyID3
from PIL import Image, ImageTk
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage
from Track_slider import TrackSlider
from Slider_effects import Slider_effects
import mutagen
from mutagen.id3 import ID3, TIT2, TPE1, TRCK, TALB, TCON, TENC, COMM, TCOM, TDRC, TPE2, TPOS, TPUB, TCOP, TSRC, TEXT, TOLY, TOPE, WXXX, APIC, USLT
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

OUTPUT_PATH = Path(__file__).parent
ASSETS_PATH = OUTPUT_PATH / Path(r"C:\Users\user\Desktop\kursach\build\assets\frame0")
def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)

is_randomize_active = True
global reverb_damping_level
delay_mix_level = 0  # Начальное значение mix для Delay
delay_feedback_level = 0  # Начальное значение feedback для Delay
# Глобальные переменные для EQ
is_low_cut_active = False
is_high_cut_active = False
is_boost_500hz_active = False
is_boost_4500hz_active = False
is_boost_200hz_active = False
is_boost_1500hz_active = False
pan_width_level = 0  # Начальное значение width
pan_speed_level = 0  # Начальное значение speed
# Глобальные переменные для panman
is_wiper_effect_active = False
is_bursty_effect_active = False
# Глобальные переменные для Delay
is_delay_quarter_active = False
is_delay_eighth_active = False
# Глобальные переменные
is_reverb_room_active = False
is_reverb_plate_active = False
loaded_track = None
is_playing = False  # Переменная для отслеживания состояния воспроизведения
current_time = 0  # Текущее время воспроизведения в секундах
samplerate = None  # Инициализируем samplerate как None
slider_moving = False
current_file_path = None
loaded_track = None
track_duration = 0
samplerate = 0
update_task_id = None  # Идентификатор задачи для обновления времени
original_samplerate = 0
current_sample = 0  # Текущая позиция (сэмпл) в треке
speed_changed = False  # Флаг изменения скорости
# Глобальные переменные
loaded_track_original = None  # Оригинальные данные трека
loaded_track_mod = None  # Модифицированные данные трека
start_time = None
track_duration = 0  # Длительность трека в миллисекундах
current_time = 0  # Текущее время воспроизведения в миллисекундах
elapsed_time = 0  # Добавьте эту строку в начало вашего скрипта
# Инициализация переменной slider_update_task_id в начале скрипта
slider_update_task_id = None
# Глобальные переменные для уровня громкости
volume_level = 1.0  # Начальный уровень громкости
bpm = 120  # Начальное значение BPM
reverb_mix_level = 0
reverb_damping_level = 0  # Начальное значение damping
# Переменная для отслеживания текущего изображения
is_stop_image = True

window = Tk()
window.geometry("1300x700")
window.title("DE_Studio")
window.configure(bg="#585050")

# Функция для открытия всплывающего окна
def open_instruction_window():
    instruction_window = Toplevel(window)
    instruction_window.title("INSTRUCTION")
    instruction_window.geometry("800x200")  # Устанавливаем размер окна

    descriptions = [
        "Reverb:\nMIX - баланс между исходным и обработанным сигналом.\nDECAY - длительность эффекта.\nPLATE - плавный звук, ROOM - естественное эхо.",
        "Delay:\nMIX - баланс между исходным и задержанным сигналом.\nFEEDBACK - количество повторений эха.\n1/4 - четвертные ноты, 1/8 - восьмые ноты.",
        "PANMAN:\nWIDTH - амплитуда панорамирования.\nSPEED - скорость панорамирования.\nWiper - плавное, BURSTY - отрывистое.",
        "EQUALIZER:\nLow Cut (100Hz) - убирает низкие частоты.\nHigh Cut (5kHz) - уменьшает высокие частоты.\nBell Filters на 200, 500, 1500, 4500Гц."
    ]

    for desc in descriptions:
        frame = tk.Frame(instruction_window, borderwidth=1, relief='solid')
        frame.pack(side='left', expand=True, fill='both')

        text_field = Text(frame, height=10, width=20, font=('Arial', 12), wrap='word')
        text_field.pack(side='left', fill='both', expand=True)
        text_field.insert('1.0', desc)
        text_field.config(state='disabled')  # Делаем текстовое поле доступным только для чтения

def safe_cancel(task_id):
    if task_id is not None:
        window.after_cancel(task_id)


# Вычисляем BPM
def estimate_bpm(file_path):
    y, sr = librosa.load(file_path)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    return tempo

def save_id3_tags(file_path, track_title=None, track_artist=None):
    audio = MP3(file_path, ID3=ID3)  # Создаем объект MP3
    try:
        audio.add_tags()  # Добавляем ID3 тег, если его нет
    except mutagen.id3.error:
        pass  # ID3 тег уже существует
    if track_title is not None:
        audio.tags.add(TIT2(encoding=3, text=track_title))
    if track_artist is not None:
        audio.tags.add(TPE1(encoding=3, text=track_artist))
    audio.save()  # Сохраняем теги в файле

def save_as():
    global loaded_track_mod, original_samplerate, current_file_path, speeds, current_speed_index
    if loaded_track_mod is None:
        print("Нет загруженного трека для сохранения.")
        return

    track_name = entry_1.get()
    default_filename = f"{track_name}_evkiDB.mp3" if track_name else "Новый_трек_evkiDB.mp3"

    file_path = filedialog.asksaveasfilename(initialfile=default_filename, defaultextension=".mp3", filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")])
    if not file_path:
        return
    # Применяем все настройки к треку
    apply_effects()  # Применяем все настройки к треку
    current_speed = speeds[current_speed_index]
    if current_speed != 1:  # Изменяем скорость только если она отличается от 1
        # Если трек стерео, обрабатываем каждый канал отдельно
        if loaded_track_mod.ndim == 2:
            left_channel = librosa.effects.time_stretch(loaded_track_mod[:, 0].astype(np.float32), rate=current_speed)
            right_channel = librosa.effects.time_stretch(loaded_track_mod[:, 1].astype(np.float32), rate=current_speed)
            track_to_save = np.stack([left_channel, right_channel], axis=1)
        else:
            # Для моно трека обрабатываем как один канал
            track_to_save = librosa.effects.time_stretch(loaded_track_mod.astype(np.float32), rate=current_speed)
    else:
        track_to_save = loaded_track_mod
    try:
        sf.write(file_path, track_to_save, original_samplerate)
        save_id3_tags(file_path)
        print(f"Файл успешно сохранен как {file_path}")
    except Exception as e:
        print(f"Ошибка при сохранении файла: {e}")


def open_audio_file():
    global loaded_track, track_duration, current_time, samplerate, original_samplerate, loaded_track_original, \
        loaded_track_mod, current_speed_index, speeds, is_playing, volume_level, button_5, button_3, bpm, current_file_path

    file_path = filedialog.askopenfilename(filetypes=[("Audio files", "*.mp3 *.wav")])
    if file_path:
        current_file_path = file_path
        reset_parameters()  # Сброс параметров перед загрузкой нового трека
        if is_playing:
            sd.stop()
            is_playing = False

        current_time = 0
        if track_slider:
            track_slider.set_position(0)

        current_speed_index = 0
        volume_level = 1.0

        track_title = 'Неизвестный трек'  # Значение по умолчанию
        track_artist = 'Неизвестный исполнитель'  # Значение по умолчанию

        try:
            # Пытаемся загрузить теги, если это MP3-файл
            audio = EasyID3(file_path)
            track_title = audio.get('title', [track_title])[0]
            track_artist = audio.get('artist', [track_artist])[0]
        except Exception as e:
            # Если возникает ошибка, предполагаем что тегов нет
            print(f"Ошибка при чтении ID3 тегов: {e}, используем значения по умолчанию.")

        # Пытаемся загрузить аудиофайл
        try:
            data, samplerate = sf.read(file_path)
            original_samplerate = samplerate
            loaded_track_original = data
            loaded_track_mod = np.copy(data)
            apply_volume()

            speed = speeds[current_speed_index]
            track_duration = len(data) * 1000 / samplerate * speed

            duration_minutes = track_duration // 60000
            duration_seconds = (track_duration % 60000) // 1000
            entry_3.delete(0, tk.END)
            entry_3.insert(0, f"00:00:000 / {int(duration_minutes):02d}:{int(duration_seconds):02d}")
            plot_audio(file_path)

            button_5.config(image=stop_image)
            button_5.image = stop_image
            button_3.config(text="1X")

            bpm = estimate_bpm(file_path)  # Обновляем bpm на основе файла
            print(f"Estimated BPM: {bpm}")

            entry_1.delete(0, tk.END)
            entry_1.insert(0, track_title)
            entry_2.delete(0, tk.END)
            entry_2.insert(0, track_artist)

        except Exception as e:
            print(f"Ошибка при загрузке аудиофайла: {e}")
            return

    else:
        print("Файл не был выбран.")


def stop_playback():
    global is_playing, update_task_id, current_time, elapsed_time, track_slider
    # Останавливаем воспроизведение
    sd.stop()
    # Обновляем переменные состояния
    is_playing = False
    # Отменяем задачу обновления времени
    if update_task_id is not None:
        window.after_cancel(update_task_id)
        update_task_id = None
    # Сбрасываем текущее время и прошедшее время
    current_time = 0
    elapsed_time = 0
    # Обновляем позицию слайдера
    update_slider_position()
    print(f"Воспроизведение остановлено, положение слайдера: {current_time}")

def start_playback():
    global is_playing, current_time, samplerate, loaded_track_mod, original_samplerate

    if loaded_track_mod is not None:
        sd.stop()
        is_playing = True
        current_speed = speeds[current_speed_index]
        adjusted_samplerate = int(original_samplerate * current_speed)
        sd.play(loaded_track_mod, adjusted_samplerate)


def update_time():
    global current_time, elapsed_time, is_playing, update_task_id, track_duration
    if is_playing and window.winfo_exists():
        elapsed_time += 100  # Увеличиваем прошедшее время на 100 мс
        current_time += 100  # Увеличиваем текущее время на 100 мс
        if current_time >= track_duration:
            current_time = 0
            elapsed_time = 0
            start_playback()
        update_slider_position()  # Обновляем положение слайдера
        update_timer(current_time, track_duration)  # Обновляем таймер
        update_task_id = window.after(100, update_time)  # Планируем следующее обновление

def update_entry_metadata(title, artist):
    entry_1.config(state='normal')
    entry_1.delete(0, tk.END)
    entry_1.insert(0, title)
    entry_1.config(state='readonly')
    entry_2.config(state='normal')
    entry_2.delete(0, tk.END)
    entry_2.insert(0, artist)
    entry_2.config(state='readonly')

def update_timer(current_time_ms, total_time_ms):
    current_minutes = int(current_time_ms // 60000)
    current_seconds = int((current_time_ms % 60000) // 1000)
    current_milliseconds = int(current_time_ms % 1000)
    total_minutes = int(total_time_ms // 60000)
    total_seconds = int((total_time_ms % 60000) // 1000)
    timer_text = f"{current_minutes:02}:{current_seconds:02}:{current_milliseconds:03} / {total_minutes:02}:{total_seconds:02}"
    entry_3.delete(0, tk.END)
    entry_3.insert(0, timer_text)


def plot_audio(file_path):
    global loaded_track, track_duration, duration_minutes, duration_seconds, samplerate
    data, samplerate = sf.read(file_path)
    loaded_track = data
    track_duration = len(data) * 1000 / samplerate  # Длительность в миллисекундах
    duration_minutes = track_duration // 60000
    duration_seconds = (track_duration % 60000) // 1000

    current_time = 0
    entry_3.delete(0, tk.END)
    entry_3.insert(0, f"00:00:000 / {int(duration_minutes):02d}:{int(duration_seconds):02d}")

    # Чтение аудиофайла
    data, samplerate = sf.read(file_path)
    left_channel = data[:, 0]  # Левый канал
    right_channel = data[:, 1]  # Правый канал

    # Визуализация аудиофайла
    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor('none')  # Прозрачный фон фигуры
    ax.patch.set_facecolor('none')  # Прозрачный фон области графика

    ax.plot(left_channel, color='yellow')  # Цвет для левого канала
    ax.plot(right_channel, color='black')  # Цвет для правого канала
    ax.axis('off')  # Отключение осей

    # Встроить график в Tkinter окно
    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.get_tk_widget().config(bg='#C3C3C3')  # Установка цвета фона канваса
    canvas_widget = canvas.get_tk_widget()

    # Размещение в определенном месте (x, y, width, height)
    canvas_widget.place(x=0, y=165, width=1300, height=126)
    canvas.draw()
def apply_volume():
    global loaded_track_mod, volume_level, current_time, samplerate, current_speed_index, speeds, is_playing
    if loaded_track_original is not None:
        loaded_track_mod = np.copy(loaded_track_original) * volume_level
        apply_effects()  # Обновляем эффекты после изменения громкости
        if is_playing:
            sd.stop()
            adjusted_samplerate = int(original_samplerate * speeds[current_speed_index])
            start_sample = int(current_time * adjusted_samplerate / 1000)
            sd.play(loaded_track_mod[start_sample:], adjusted_samplerate)
def increase_volume(event=None):
    global volume_level
    volume_level = min(volume_level + 0.1, 1.0)
    volume_level = round(volume_level, 2)  # Округляем до двух знаков после запятой
    apply_volume()  # Применяем измененный уровень громкости
    print("Увеличиваем громкость:", volume_level)
def decrease_volume(event=None):
    global volume_level
    volume_level = max(volume_level - 0.1, 0.0)
    volume_level = round(volume_level, 2)  # Округляем
    apply_volume()  # Применяем измененный уровень громкости
    print("Уменьшаем громкость:", volume_level)
# Объединение обработчиков событий клавиатуры
def handle_volume_change(event, change):
    focused_widget = window.focus_get()
    if focused_widget in [entry_1, entry_2, entry_3]:
        return  # Не меняем громкость, если фокус на одном из полей ввода
    if change == "increase":
        increase_volume()
    elif change == "decrease":
        decrease_volume()
    apply_volume()


# Цвета для текста и фона кнопок по умолчанию
default_text_color = "white"  # Цвет текста по умолчанию
default_button_color = "#B8B818"  # Цвет фона кнопок по умолчанию
# Активные цвета для текста и фона кнопок
active_text_color = "black"  # Цвет текста для активной кнопки
active_button_color = "white"  # Цвет фона для активной кнопки


def toggle_button_color(button, is_active):
    if is_active:
        button.config(bg=active_button_color, fg=active_text_color)
    else:
        button.config(bg=default_button_color, fg=default_text_color)
def change_speed():
    global current_speed_index, speeds, track_duration, original_samplerate, loaded_track_mod, current_time, is_playing
    old_speed = speeds[current_speed_index]
    current_speed_index = (current_speed_index + 1) % len(speeds)
    new_speed = speeds[current_speed_index]
    # Выводим информацию для отладки
    print(f"Изменение скорости с {old_speed}X на {new_speed}X")
    # Обновляем текст скорости
    new_speed_float = float(new_speed)  # Преобразуем значение в число с плавающей точкой
    if new_speed_float.is_integer():
        speed_text = f"{int(new_speed_float)}X"  # Для целых чисел
    else:
        speed_text = f"{new_speed_float:.2f}"  # Для дробных чисел
        speed_text = speed_text.rstrip('0').rstrip('.') + 'X'  # Убираем лишние нули и точку
    button_3.config(text=speed_text)

    if loaded_track_mod is not None:
        time_ratio = current_time / track_duration
        track_duration = len(loaded_track_mod) * 1000 / (original_samplerate * new_speed)
        current_time = time_ratio * track_duration
        # Выводим обновленное время
        print(f"Обновленное текущее время: {current_time} мс")
        if is_playing:
            sd.stop()
            adjusted_samplerate = int(original_samplerate * new_speed)
            start_sample = int(current_time * adjusted_samplerate / 1000)
            sd.play(loaded_track_mod[start_sample:], adjusted_samplerate)

def start_slider_move(event):
    global slider_moving, track_duration, track_slider
    if track_duration <= 0:
        return  # Добавлена проверка на нулевую длительность
    slider_moving = True
    click_position = max(0, min(event.x, track_slider.length - TrackSlider.SLIDER_SIZE))
    track_slider.set_position(click_position)

def stop_slider_move(event):
    global slider_moving, current_time, track_duration, loaded_track_mod, original_samplerate, speeds, current_speed_index, is_playing
    if track_duration <= 0:
        return  # Добавлена проверка на нулевую длительность
    slider_moving = False
    if track_duration > 0:
        click_position = max(0, min(event.x, track_slider.length - TrackSlider.SLIDER_SIZE))
        slider_position_ratio = click_position / (track_slider.length - TrackSlider.SLIDER_SIZE)
        current_time = slider_position_ratio * track_duration

        if is_playing:
            sd.stop()
            current_speed = speeds[current_speed_index]
            adjusted_samplerate = int(original_samplerate * current_speed)
            start_sample = int(current_time * adjusted_samplerate / 1000)
            sd.play(loaded_track_mod[start_sample:], adjusted_samplerate, blocking=False)

        update_slider_position()
        update_timer(current_time, track_duration)

def update_slider_position():
    global current_time, track_duration, track_slider, slider_moving
    if not slider_moving and track_duration > 0:
        slider_position = (current_time / track_duration) * (track_slider.length - TrackSlider.SLIDER_SIZE)
        slider_position = min(slider_position, track_slider.length - TrackSlider.SLIDER_SIZE)
        track_slider.set_position(slider_position)

def apply_effects():
    global loaded_track_mod, is_wiper_effect_active, is_bursty_effect_active, \
        samplerate, is_playing, current_time, is_delay_quarter_active, \
        is_delay_eighth_active, bpm, is_low_cut_active, is_high_cut_active, \
        is_boost_500hz_active, is_boost_4500hz_active, is_boost_200hz_active, \
        is_boost_1500hz_active, pan_width_level, pan_speed_level, original_samplerate
    # Сохраняем текущее состояние воспроизведения и позицию
    was_playing = is_playing
    sd.stop()  # Остановка воспроизведения для применения эффектов
    if loaded_track_original is None:
        return
    # Копия оригинального трека для дальнейшей обработки
    loaded_track_mod = np.copy(loaded_track_original).astype('float32') * volume_level
    # Создаем педалборд для эквалайзера
    eq_board = Pedalboard([])
    # Применяем усиления для выбранных частот
    if is_boost_500hz_active:
        eq_board.append(LowShelfFilter(cutoff_frequency_hz=500, gain_db=3.0))  # Усиление на 3 dB для 500Hz
    if is_boost_4500hz_active:
        eq_board.append(HighShelfFilter(cutoff_frequency_hz=4500, gain_db=3.0))  # Усиление на 3 dB для 4500Hz

    if is_boost_200hz_active:
        eq_board.append(LowShelfFilter(cutoff_frequency_hz=200, gain_db=3.0))  # Усиление на 3 dB для 200Hz

    if is_boost_1500hz_active:
        eq_board.append(HighShelfFilter(cutoff_frequency_hz=1500, gain_db=3.0))  # Усиление на 3 dB для 1500Hz

    loaded_track_mod = eq_board(loaded_track_mod, samplerate)
    reverb_track = np.copy(loaded_track_mod)
    # Обработка реверберации
    if is_reverb_room_active or is_reverb_plate_active:
        reverb_params = {
            'room_size': 1, 'damping': reverb_damping_level, 'wet_level': reverb_mix_level, 'dry_level': 0.8,
            'width': 0.8, 'freeze_mode': 0.0
        } if is_reverb_room_active else {
            'room_size': 1, 'damping': reverb_damping_level, 'wet_level': reverb_mix_level, 'dry_level': 0.2,
            'width': 0.3, 'freeze_mode': 0.1
        }
        reverb_effect = Reverb(**reverb_params)
        reverb_track = reverb_effect(reverb_track, samplerate)

        # Копия для реверберации
        reverb_track = np.copy(loaded_track_mod)

        # Применение реверберации к копии
        reverb_track = reverb_effect(reverb_track, samplerate)

        # Фильтры для реверберации
        reverb_board = Pedalboard([HighpassFilter(cutoff_frequency_hz=500), LowpassFilter(cutoff_frequency_hz=3000)])
        reverb_track = reverb_board(reverb_track, samplerate)

        # Смешивание реверберированной копии с оригинальным треком
        loaded_track_mod += reverb_track * reverb_mix_level  # Коэффициент смешивания может быть настроен

    current_speed = speeds[current_speed_index]
    if is_delay_quarter_active or is_delay_eighth_active:
        base_delay_time = (60 / bpm)  # Основное время задержки в секундах
        delay_time = base_delay_time * (0.25 if is_delay_quarter_active else 0.125) / current_speed
        delay_effect = Delay(delay_seconds=delay_time, feedback=delay_feedback_level, mix=delay_mix_level)
        loaded_track_mod = delay_effect(loaded_track_mod, samplerate)

    # Проверяем, не равен ли pan_speed_level нулю
    if pan_speed_level == 0:
        pan_speed_level = 0.01  # Устанавливаем минимальное значение

    # Аналогично для pan_width_level
    if pan_width_level == 0:
        pan_width_level = 0.01  # Устанавливаем минимальное значение

    # Логика панорамирования для WIPER
    if is_wiper_effect_active:
        # Рассчитываем количество сэмплов в зависимости от BPM и скорости панорамирования
        pan_samples = int(samplerate * (60 / bpm) * pan_speed_level * 5)
        # Создаем массив панорамирования от -width до +width
        pan = np.sin(np.linspace(0, 2 * np.pi, pan_samples)) * pan_width_level
        # Повторяем массив, чтобы он соответствовал длине трека
        pan = np.tile(pan, int(np.ceil(len(loaded_track_mod) / pan_samples)))[:len(loaded_track_mod)]
        # Применяем панорамирование к левому и правому каналам
        left_channel = loaded_track_mod[:, 0] * (1 - pan)
        right_channel = loaded_track_mod[:, 1] * (1 + pan)
        loaded_track_mod = np.vstack((left_channel, right_channel)).T

    # Логика панорамирования для BURSTY
    if is_bursty_effect_active:
        # Рассчитываем количество сэмплов в зависимости от BPM и скорости панорамирования
        pan_samples = int(samplerate * (60 / bpm) * pan_speed_level * 5)
        # Создаем массив панорамирования от -width до +width с резкими переходами
        pan = np.sin(np.linspace(0, 2 * np.pi, pan_samples))
        pan = np.clip(pan, -pan_width_level, pan_width_level)
        # Повторяем массив, чтобы он соответствовал длине трека
        pan = np.tile(pan, int(np.ceil(len(loaded_track_mod) / pan_samples)))[:len(loaded_track_mod)]
        # Применяем панорамирование к левому и правому каналам
        left_channel = loaded_track_mod[:, 0] * (1 - pan)
        right_channel = loaded_track_mod[:, 1] * (1 + pan)
        loaded_track_mod = np.vstack((left_channel, right_channel)).T

    # Код для low-cut фильтра
    if is_low_cut_active:
        board = Pedalboard([HighpassFilter(cutoff_frequency_hz=100)])  # Устанавливаем cutoff на 100 Гц
        loaded_track_mod = board(loaded_track_mod, samplerate)

    # Код для high-cut фильтра
    if is_high_cut_active:
        board = Pedalboard([LowpassFilter(cutoff_frequency_hz=5000)])  # Устанавливаем cutoff на 5000 Гц
        loaded_track_mod = board(loaded_track_mod, samplerate)

        # Возобновляем воспроизведение с правильной позиции, если трек был воспроизведен
    if was_playing:
        adjusted_samplerate = int(original_samplerate * speeds[current_speed_index])
        start_sample = int(current_time * adjusted_samplerate / 1000)
        sd.play(loaded_track_mod[start_sample:], adjusted_samplerate, blocking=False)
        is_playing = True


# Функция для обновления уровня реверберации из слайдера
def update_reverb_level(position):
    global reverb_mix_level
    # Нормализуем позицию слайдера в диапазон от 0 до 1
    reverb_mix_level = position / (reverb_slider.length - TrackSlider.SLIDER_SIZE)
    reverb_mix_level = min(max(reverb_mix_level, 0), 1)  # Ограничиваем уровень от 0 до 1
    print(f"Уровень реверберации установлен на: {reverb_mix_level:.2f}")
    apply_effects()  # Переприменяем эффекты с новым уровнем реверберации

def update_damping_level(position):    # Функция для обновления уровня damping из слайдера
    global reverb_damping_level
    # Нормализуем позицию слайдера в диапазон от 0 до 1
    reverb_damping_level = position / (damping_slider.length - TrackSlider.SLIDER_SIZE)
    reverb_damping_level = min(max(reverb_damping_level, 0), 1)  # Ограничиваем уровень от 0 до 1
    print(f"Уровень damping установлен на: {reverb_damping_level:.2f}")
    apply_effects()  # Переприменяем эффекты с новым уровнем damping
def update_delay_mix_level(position):
    global delay_mix_level
    # Нормализуем позицию слайдера в диапазон от 0 до 1
    delay_mix_level = position / (delay_mix_slider.length - TrackSlider.SLIDER_SIZE)
    delay_mix_level = min(max(delay_mix_level, 0), 1)  # Ограничиваем уровень от 0 до 1
    print(f"Уровень mix для Delay установлен на: {delay_mix_level:.2f}")
    apply_effects()  # Переприменяем эффекты с новым уровнем mix для Delay

def update_delay_feedback_level(position):   # Функция для обновления уровня feedback Delay из слайдера
    global delay_feedback_level
    # Нормализуем позицию слайдера в диапазон от 0 до 1
    delay_feedback_level = position / (delay_feedback_slider.length - TrackSlider.SLIDER_SIZE)
    delay_feedback_level = min(max(delay_feedback_level, 0), 1)  # Ограничиваем уровень от 0 до 1
    print(f"Уровень feedback для Delay установлен на: {delay_feedback_level:.2f}")
    apply_effects()  # Переприменяем эффекты с новым уровнем feedback для Delay


def update_pan_width_level(position):
    global pan_width_level
    pan_width_level = position / (pan_width_slider.length - TrackSlider.SLIDER_SIZE)
    pan_width_level = min(max(pan_width_level, 0), 1)
    print(f"Уровень width для Pan установлен на: {pan_width_level:.2f}")
    apply_effects()

def update_pan_speed_level(position):   # Функция для обновления уровня speed Pan из слайдера
    global pan_speed_level
    pan_speed_level = position / (pan_speed_slider.length - TrackSlider.SLIDER_SIZE)
    pan_speed_level = min(max(pan_speed_level, 0.03), 1)
    print(f"Уровень speed для Pan установлен на: {pan_speed_level:.2f}")
    apply_effects()

def reverb_ROOM():
    global is_reverb_room_active, is_reverb_plate_active
    is_reverb_room_active = not is_reverb_room_active
    is_reverb_plate_active = False
    toggle_button_color(room_button, is_reverb_room_active)
    toggle_button_color(plate_button, False)
    apply_effects()
def reverb_PLATE():
    global is_reverb_room_active, is_reverb_plate_active
    is_reverb_plate_active = not is_reverb_plate_active
    is_reverb_room_active = False
    toggle_button_color(plate_button, is_reverb_plate_active)
    toggle_button_color(room_button, False)
    apply_effects()


def change_delay_to_quarter():
    global is_delay_quarter_active, is_delay_eighth_active
    is_delay_quarter_active = not is_delay_quarter_active
    is_delay_eighth_active = False
    toggle_button_color(one_four_button, is_delay_quarter_active)
    toggle_button_color(one_eight_button, False)
    apply_effects()
def change_delay_to_eighth():
    global is_delay_quarter_active, is_delay_eighth_active
    is_delay_eighth_active = not is_delay_eighth_active
    is_delay_quarter_active = False
    toggle_button_color(one_eight_button, is_delay_eighth_active)
    toggle_button_color(one_four_button, False)
    apply_effects()
def activate_wiper_effect():
    global is_wiper_effect_active, is_bursty_effect_active
    if is_bursty_effect_active:
        is_bursty_effect_active = False
        toggle_button_color(bursty_button, False)
    is_wiper_effect_active = not is_wiper_effect_active
    toggle_button_color(wiper_button, is_wiper_effect_active)
    apply_effects()
    print("Эффект панорамирования WIPER " + ("активирован" if is_wiper_effect_active else "деактивирован"))

def activate_bursty_effect():
    global is_wiper_effect_active, is_bursty_effect_active
    if is_wiper_effect_active:
        is_wiper_effect_active = False
        toggle_button_color(wiper_button, False)
    is_bursty_effect_active = not is_bursty_effect_active
    toggle_button_color(bursty_button, is_bursty_effect_active)
    apply_effects()
    print("Эффект панорамирования BURSTY " + ("активирован" if is_bursty_effect_active else "деактивирован"))
def cut_100hz():
    global is_low_cut_active
    is_low_cut_active = not is_low_cut_active  # Переключение состояния
    toggle_button_color(one_hundred__button, is_low_cut_active)  # Обновление цвета кнопки
    apply_effects()  # Применение изменений
    print("Low-cut на 100Hz " + ("активирован" if is_low_cut_active else "деактивирован"))

def cut_5000hz():
    global is_high_cut_active
    is_high_cut_active = not is_high_cut_active  # Переключение состояния
    toggle_button_color(hundred_hundred_button, is_high_cut_active)  # Обновление цвета кнопки
    apply_effects()  # Применение изменений
    print("High-cut на 5000Hz " + ("активирован" if is_high_cut_active else "деактивирован"))
def boost_200hz():
    global is_boost_200hz_active
    is_boost_200hz_active = not is_boost_200hz_active
    toggle_button_color(two_hundred_button, is_boost_200hz_active)
    print("Частота 200Hz " + ("усилена" if is_boost_200hz_active else "не усилена"))
    apply_effects()
def boost_500hz():
    global is_boost_500hz_active
    is_boost_500hz_active = not is_boost_500hz_active
    toggle_button_color(five_hundred_button, is_boost_500hz_active)
    print("Частота 500Hz " + ("усилена" if is_boost_500hz_active else "не усилена"))
    apply_effects()

def boost_1500hz():
    global is_boost_1500hz_active
    is_boost_1500hz_active = not is_boost_1500hz_active
    toggle_button_color(one_five_hudred_button, is_boost_1500hz_active)
    print("Частота 1500Hz " + ("усилена" if is_boost_1500hz_active else "не усилена"))
    apply_effects()
def boost_4500hz():
    global is_boost_4500hz_active
    is_boost_4500hz_active = not is_boost_4500hz_active
    toggle_button_color(four_five_hundred_button, is_boost_4500hz_active)
    print("Частота 4500Hz " + ("усилена" if is_boost_4500hz_active else "не усилена"))
    apply_effects()

canvas = Canvas(
    window,
    bg="#585050",
    height=700,
    width=1300,
    bd=0,
    highlightthickness=0,
    relief="ridge"
)

canvas.place(x=0, y=0)
image_image_1 = PhotoImage(file=relative_to_assets("image_1.png"))  # image_1.png это фон и некоторые элелементы по типу шапки программы, столбиков снизу...
image_1 = canvas.create_image(650.0000171661377, 350.0, image=image_image_1)

entry_image_1 = PhotoImage(file=relative_to_assets("entry_1.png"))  # entry_1.png это пустая серая полоса где при загрузке музыки будет отображаться название трека
entry_bg_1 = canvas.create_image(230.0, 134.5, image=entry_image_1)

entry_image_3 = PhotoImage(file=relative_to_assets("entry_3.png"))  # entry_3.png это пустая серая полоса где при загрузке музыки будет длительность трека
entry_bg_3 = canvas.create_image(1193.0, 134.5, image=entry_image_3)

entry_image_2 = PhotoImage(file=relative_to_assets("entry_2.png"))  # entry_2.png это пустая серая полоса где при загрузке музыки будет отображаться испольнителя трека
entry_bg_2 = canvas.create_image(733.5, 134.5, image=entry_image_2)

entry_1 = Entry(bd=0, bg="#C3C3C3", fg="#000716", highlightthickness=0)
entry_1.place(x=59.0, y=114.0, width=342.0, height=45.0)

entry_2 = Entry(bd=0, bg="#C3C3C3", fg="#000716", highlightthickness=0)
entry_2.place(x=638.0, y=114.0, width=191.0, height=45.0)

entry_3 = Entry(bd=0, bg="#C3C3C3", fg="#000716", highlightthickness=0)
entry_3.place(x=1138.0, y=114.0, width=110.0, height=45.0)

entry_1.takefocus = False
entry_2.takefocus = False
entry_3.takefocus = False

button_1 = Button(window, text="SAVE AS", font=('Arial', 16), borderwidth=0, highlightthickness=0, relief="flat", bg="#d9d9d9")
button_1.place(x=123.0, y=3.0, width=85.0, height=30.0)

speeds = [1, 1.1, 1.25, 1.5, 0.75, 0.9]
current_speed_index = 0

button_3 = Button(window, text="1X", font=('Arial', 16), borderwidth=0, highlightthickness=0, command=change_speed, relief="flat", bg="#C3C3C3")
button_3.place(x=358.0, y=43.0, width=98.0, height=51.0)

button_4 = Button(window, text="OPEN", font=('Arial', 16), borderwidth=0, highlightthickness=0, command=open_audio_file, relief="flat", bg="#d9d9d9")
button_4.place(x=38.0, y=3.0, width=79.0, height=30.0)

# Функция для переключения воспроизведения
def toggle_play():
    global is_playing, update_task_id, loaded_track_mod, original_samplerate, speeds, current_speed_index, current_time

    if is_playing:
        sd.stop()
        is_playing = False
        button_5.config(image=stop_image)
        if update_task_id is not None:
            window.after_cancel(update_task_id)
            update_task_id = None
    else:
        if loaded_track_mod is not None:
            current_speed = speeds[current_speed_index]
            adjusted_samplerate = int(original_samplerate * current_speed)
            start_sample = int(current_time * adjusted_samplerate / 1000)
            sd.play(loaded_track_mod[start_sample:], adjusted_samplerate, blocking=False)
            is_playing = True
            button_5.config(image=cont_image)
            update_time()
    print(f"Воспроизведение {'возобновлено' if is_playing else 'остановлено'}, текущее время: {current_time} мс")

    # Привязываем функцию к кнопке
    button_5.config(command=toggle_play)


# Загружаем изображения
stop_image = PhotoImage(file=r"C:\Users\user\Desktop\kursach\build\assets\frame0\stop.png")
cont_image = PhotoImage(file=r"C:\Users\user\Desktop\kursach\build\assets\frame0\cont.png")

# Создаем кнопку с изначальным изображением stop
button_5 = tk.Button(window, image=stop_image, command=toggle_play)
button_5.image = stop_image  # Сохраняем ссылку на изображение
button_5.pack()  # Размещаем кнопку в окне
# Размещение кнопки на окне
button_5.place(x=294.0, y=42.0, width=48.0, height=48.0)
# Определение информации о кнопках в виде списка кортежей.
# Каждый кортеж содержит текст кнопки, функцию обратного вызова, координаты X и Y, ширину и высоту.
buttons_info = [
    ("PLATE", reverb_PLATE, 6.0, 590.0, 113.0, 56.0),
    ("ROOM", reverb_ROOM, 127.0, 590.0, 113.0, 56.0),
    ("1/4", change_delay_to_quarter, 267.0, 590.0, 113.0, 56.0),
    ("1/8", change_delay_to_eighth, 388.0, 590.0, 116.0, 56.0),
    ("WIPER", activate_wiper_effect, 798.0, 590.0, 113.0, 56.0),
    ("BURSTY", activate_bursty_effect, 919.0, 590.0, 113.0, 56.0),
    ("500Hz", boost_500hz, 1062.0, 582.0, 113.0, 56.0),
    ("4500Hz", boost_4500hz, 1183.0, 582.0, 113.0, 56.0),
    ("200Hz", boost_200hz, 1062.0, 516.0, 113.0, 56.0),
    ("1500Hz", boost_1500hz, 1183.0, 516.0, 113.0, 56.0),
    ("100Hz", cut_100hz, 1062.0, 434.0, 113.0, 56.0),
    ("5000Hz", cut_5000hz, 1183.0, 434.0, 113.0, 56.0)
]

button_references = {
    "PLATE": None,
    "ROOM": None,
    "1/4": None,
    "1/8": None,
    "WIPER": None,
    "BURSTY": None,
    "500Hz": None,
    "4500Hz": None,
    "200Hz": None,
    "1500Hz": None,
    "100Hz": None,
    "5000Hz": None
}

# Цикл, проходящий по списку buttons_info.
# Для каждого элемента списка создается кнопка с соответствующими параметрами.
for text, command, x, y, width, height in buttons_info:
    # Создание кнопки с заданными параметрами: текстом, командой, цветом и т.д.
    button = Button(window, text=text, command=command, bg=default_button_color, fg=default_text_color, font=('Arial', 17, 'bold'))
    # Размещение кнопки на окне в заданных координатах с указанными размерами.
    button.place(x=x, y=y, width=width, height=height)
    if text == "PLATE":
        plate_button = button
    if text == "ROOM":
        room_button = button
    if text == "1/4":
        one_four_button = button
    if text == "1/8":
        one_eight_button = button
    if text == "WIPER":
        wiper_button = button
    if text == "BURSTY":
        bursty_button = button
    if text == "500Hz":
        five_hundred_button = button
    if text == "4500Hz":
        four_five_hundred_button = button
    if text == "200Hz":
        two_hundred_button = button
    if text == "1500Hz":
        one_five_hudred_button = button
    if text == "100Hz":
        one_hundred__button = button
    if text == "5000Hz":
        hundred_hundred_button = button

# Кнопка рандома
button_image_20 = PhotoImage(file=relative_to_assets("button_20.png"))
button_20 = Button(window, image=button_image_20, borderwidth=0, highlightthickness=0, command=lambda: print("button_20 clicked"), relief="flat")
button_20.place(x=541.0, y=438.0, width=217.0, height=221.0)


def randomize_parameters():
    global is_randomize_active
    if is_randomize_active:
        set_random_parameters()
    else:
        reset_parameters()
    is_randomize_active = not is_randomize_active


def set_random_parameters():
    global reverb_mix_level, reverb_damping_level, delay_mix_level, delay_feedback_level, pan_width_level, pan_speed_level
    global is_low_cut_active, is_high_cut_active, is_boost_500hz_active, is_boost_4500hz_active, is_boost_200hz_active, is_boost_1500hz_active
    global is_wiper_effect_active, is_bursty_effect_active, is_delay_quarter_active, is_delay_eighth_active, is_reverb_room_active, is_reverb_plate_active

    # Установка случайных значений с учетом ограничений
    reverb_mix_level = random.uniform(0, 0.6)  # Ограничение до 0.7
    reverb_damping_level = random.uniform(0, 0.8)
    delay_mix_level = random.uniform(0, 1)
    delay_feedback_level = random.uniform(0, 0.7)  # Ограничение до 0.7
    pan_width_level = random.uniform(0, 1)
    pan_speed_level = random.uniform(0, 1)  # Минимальное значение 0.03

    # Случайные значения для активации эффектов
    is_low_cut_active = random.choice([True, False])
    is_high_cut_active = random.choice([True, False])
    is_boost_500hz_active = random.choice([True, False])
    is_boost_4500hz_active = random.choice([True, False])
    is_boost_200hz_active = random.choice([True, False])
    is_boost_1500hz_active = random.choice([True, False])

    # Выбор только одного из эффектов реверберации
    if random.choice([True, False]):
        is_reverb_room_active = True
        is_reverb_plate_active = False
    else:
        is_reverb_room_active = False
        is_reverb_plate_active = True

    # Выбор только одного из эффектов задержки
    if random.choice([True, False]):
        is_delay_quarter_active = True
        is_delay_eighth_active = False
    else:
        is_delay_quarter_active = False
        is_delay_eighth_active = True

    # Выбор только одного из эффектов панорамирования
    if random.choice([True, False]):
        is_wiper_effect_active = True
        is_bursty_effect_active = False
    else:
        is_wiper_effect_active = False
        is_bursty_effect_active = True

    # Случайное включение/отключение реверберации
    is_reverb_room_active = random.choice([True, False])
    is_reverb_plate_active = random.choice([True, False]) if not is_reverb_room_active else False

    # Случайное включение/отключение дилэя
    is_delay_quarter_active = random.choice([True, False])
    is_delay_eighth_active = random.choice([True, False]) if not is_delay_quarter_active else False

    # Случайное включение/отключение панорамирования
    is_wiper_effect_active = random.choice([True, False])
    is_bursty_effect_active = random.choice([True, False]) if not is_wiper_effect_active else False

    # Применение новых значений
    apply_effects()  # Применение новых значений перед обновлением интерфейса
    update_all_sliders_and_buttons()  # Обновление интерфейса

    # Вывод отладочной информации
    print_debug_info()


def update_all_sliders_and_buttons():
    # Обновление слайдеров
    reverb_slider.set_position(int(reverb_mix_level * 214))
    damping_slider.set_position(int(reverb_damping_level * 214))
    delay_mix_slider.set_position(int(delay_mix_level * 214))
    delay_feedback_slider.set_position(int(delay_feedback_level * 214))
    pan_width_slider.set_position(int(pan_width_level * 214))
    pan_speed_slider.set_position(int(pan_speed_level * 214))

    # Обновление цветов кнопок
    update_button_colors()
def update_button_colors():
    toggle_button_color(one_hundred__button, is_low_cut_active)
    toggle_button_color(hundred_hundred_button, is_high_cut_active)
    toggle_button_color(five_hundred_button, is_boost_500hz_active)
    toggle_button_color(four_five_hundred_button, is_boost_4500hz_active)
    toggle_button_color(two_hundred_button, is_boost_200hz_active)
    toggle_button_color(one_five_hudred_button, is_boost_1500hz_active)
    toggle_button_color(plate_button, is_reverb_plate_active)
    toggle_button_color(room_button, is_reverb_room_active)
    toggle_button_color(one_four_button, is_delay_quarter_active)
    toggle_button_color(one_eight_button, is_delay_eighth_active)
    toggle_button_color(wiper_button, is_wiper_effect_active)
    toggle_button_color(bursty_button, is_bursty_effect_active)
def print_debug_info():
    print("Randomized Parameters:")
    print(f"Reverb Mix Level: {reverb_mix_level}")
    print(f"Reverb Damping Level: {reverb_damping_level}")
    print(f"Delay Mix Level: {delay_mix_level}")
    print(f"Delay Feedback Level: {delay_feedback_level}")
    print(f"Pan Width Level: {pan_width_level}")
    print(f"Pan Speed Level: {pan_speed_level}")
    print(f"Low Cut: {'Active' if is_low_cut_active else 'Inactive'}")
    print(f"High Cut: {'Active' if is_high_cut_active else 'Inactive'}")
    print(f"500Hz Boost: {'Active' if is_boost_500hz_active else 'Inactive'}")
    print(f"4500Hz Boost: {'Active' if is_boost_4500hz_active else 'Inactive'}")
    print(f"200Hz Boost: {'Active' if is_boost_200hz_active else 'Inactive'}")
    print(f"1500Hz Boost: {'Active' if is_boost_1500hz_active else 'Inactive'}")
    print(f"Reverb: {'Room' if is_reverb_room_active else 'Plate'}")
    print(f"Delay: {'1/4' if is_delay_quarter_active else '1/8'}")
    print(f"Pan: {'Wiper' if is_wiper_effect_active else 'Bursty'}")


def reset_parameters():
    # Сброс всех параметров и эффектов
    global reverb_mix_level, reverb_damping_level, delay_mix_level, delay_feedback_level, pan_width_level, pan_speed_level
    global is_low_cut_active, is_high_cut_active, is_boost_500hz_active, is_boost_4500hz_active, is_boost_200hz_active, is_boost_1500hz_active
    global is_wiper_effect_active, is_bursty_effect_active, is_delay_quarter_active, is_delay_eighth_active, is_reverb_room_active, is_reverb_plate_active

    # Установка всех параметров в их начальные значения
    reverb_mix_level = 0
    reverb_damping_level = 0
    delay_mix_level = 0
    delay_feedback_level = 0
    pan_width_level = 0
    pan_speed_level = 0
    is_low_cut_active = False
    is_high_cut_active = False
    is_boost_500hz_active = False
    is_boost_4500hz_active = False
    is_boost_200hz_active = False
    is_boost_1500hz_active = False
    is_wiper_effect_active = False
    is_bursty_effect_active = False
    is_delay_quarter_active = False
    is_delay_eighth_active = False
    is_reverb_room_active = False
    is_reverb_plate_active = False

    apply_effects()  # Применение новых значений перед обновлением интерфейса
    update_all_sliders_and_buttons()  # Обновление интерфейса

    print("All parameters have been reset.")


# Связываем функцию randomize_parameters с кнопкой button_20
button_20.config(command=randomize_parameters)

images_info = [
    ("image_2.png", 73.0, 330.0),  # наклоненный текст REVERB
    ("image_3.png", 121.0, 371.0),  # жирный текст MIX
    ("image_4.png", 127.0, 459.0),  # жирный текст DECAY
    ("image_5.png", 395.0, 459.0),  # жирный текст FEEDBACK
    ("image_6.png", 924.0, 371.0),  # жирный текст WIDTH
    ("image_7.png", 123.0, 561.0),  # жирный текст MODE
    ("image_8.png", 390.0, 561.0),  # жирный текст MODE
    ("image_9.png", 386.0, 368.0),  # жирный текст MIX
    ("image_10.png", 144.0, 73.0),  # наклоненный текст Prod by DB, evkidey
    ("image_11.png", 925.0, 459.0),  # жирный текст SPEED
    ("image_12.png", 1117.0, 409.0),  # жирный текст LOW_CUT
    ("image_13.png", 1180.0, 503.0),  # жирный текст Bells
    ("image_14.png", 1237.0, 409.0),  # жирный текст High Cut
    ("image_15.png", 340.0, 333.0),  # наклоненный текст DELAY
    ("image_16.png", 910.0, 333.0),  # наклоненный текст PANMAN
    ("image_17.png", 1169.0, 333.0),  # наклоненный текст EQUALIZER
    ("image_18.png", 922.0, 561.0),  # жирный текст MODE
    ("image_19.png", 650.0, 396.0)
]

images = []  # Список для сохранения объектов PhotoImage и предотвращения их удаления сборщиком мусора
for image_file, x, y in images_info:
    image = PhotoImage(file=relative_to_assets(image_file))
    images.append(image)  # Сохраняем ссылку на объект PhotoImage
    canvas.create_image(x, y, image=image)

button_4.config(command=open_audio_file)
window.resizable(False, False)

# Создание текстовых кнопок с плюсом и минусом
button_plus = Button(window, text="+", font=('Arial', 16, 'bold'), command=increase_volume, borderwidth=0, highlightthickness=0, relief="flat")
button_plus.place(x=823.0, y=50.0, width=41.0, height=33.0)
button_minus = Button(window, text="-", font=('Arial', 16, 'bold'), command=decrease_volume, borderwidth=0, highlightthickness=0, relief="flat")
button_minus.place(x=865.0, y=50.0, width=44.0, height=33.3)
def handle_volume_change(event, change):
    if change == "increase":
        increase_volume()
    elif change == "decrease":
        decrease_volume()
    apply_volume()

window.bind('<Control-plus>', lambda event: handle_volume_change(event, "increase"))  # Используйте Ctrl + для увеличения громкости
window.bind('<Control-minus>', lambda event: handle_volume_change(event, "decrease"))  # Используйте Ctrl - для уменьшения громкости

track_slider = TrackSlider(window, 320)
track_slider.place(x=472, y=60)
track_slider.bind('<ButtonPress-1>', start_slider_move)
track_slider.bind('<ButtonRelease-1>', stop_slider_move)

# Создание и размещение слайдера реверберации
reverb_slider = Slider_effects(window, length=214)
reverb_slider.place(x=19, y=406)  # Укажите подходящие координаты для размещения
reverb_slider.bind('<ButtonRelease-1>', lambda event: update_reverb_level(reverb_slider.get_position()))
reverb_slider.set_position(int(reverb_mix_level * 100))

# Создание и размещение слайдера дапинга
damping_slider = Slider_effects(window, length=214)
damping_slider.place(x=19, y=495)  # Укажите подходящие координаты для размещения
# Прикрепите событие перемещения слайдера к функции update_damping_level
damping_slider.bind('<ButtonRelease-1>', lambda event: update_damping_level(damping_slider.get_position()))

delay_mix_slider = Slider_effects(window, length=214)
delay_mix_slider.place(x=281, y=406)  # Укажите подходящие координаты для размещения
delay_mix_slider.bind('<ButtonRelease-1>', lambda event: update_delay_mix_level(delay_mix_slider.get_position()))
delay_mix_slider.set_position(int(delay_mix_level * 214))

# Создание и размещение слайдера feedback для Delay
delay_feedback_slider = Slider_effects(window, length=214)
delay_feedback_slider.place(x=281, y=495)  # Укажите подходящие координаты для размещения
delay_feedback_slider.bind('<ButtonRelease-1>', lambda event: update_delay_feedback_level(delay_feedback_slider.get_position()))
delay_feedback_slider.set_position(int(delay_feedback_level * 214))

# Создание и размещение слайдера width для Pan
pan_width_slider = Slider_effects(window, length=214)
pan_width_slider.place(x=806, y=406)  # Укажите подходящие координаты для размещения
pan_width_slider.bind('<ButtonRelease-1>', lambda event: update_pan_width_level(pan_width_slider.get_position()))
pan_width_slider.set_position(int(pan_width_level * 214))

# Создание и размещение слайдера speed для Pan
pan_speed_slider = Slider_effects(window, length=214)
pan_speed_slider.place(x=806, y=495)  # Укажите подходящие координаты для размещения
pan_speed_slider.bind('<ButtonRelease-1>', lambda event: update_pan_speed_level(pan_speed_slider.get_position()))
pan_speed_slider.set_position(int(pan_speed_level * 214))

# Создаем кнопку "ИНСТРУКЦИЯ" и связываем ее с функцией open_instruction_window
button_instruction = Button(window, text="INSTRUCTION", font=('Trykker', 16), borderwidth=0, highlightthickness=0, command=open_instruction_window,
                            relief="flat", bg="#d9d9d9")
button_instruction.place(x=220, y=3, width=150, height=30)

for entry in [entry_1, entry_2, entry_3]:
    entry.bind("<Key>", lambda e: "break")

button_1.config(command=save_as)

window.bind('<space>', lambda event: toggle_play())
def on_closing():
    safe_cancel(update_task_id)
    window.destroy()

window.protocol("WM_DELETE_WINDOW", on_closing)
image = Image.open("C:/Users/user/Desktop/kursach/build/icon.ico")
icon = ImageTk.PhotoImage(image)
window.iconphoto(True, icon)
window.mainloop()
