from datetime import datetime, timedelta, time
import numpy as np
from django.templatetags.static import static
from django.conf import settings
from sleep_tracking_app.models import SleepRecord, User
from .num_to_str import interpret_chronotype


def calculate_calories_burned(gender: int, weight: float, height: int, age: np.float64,
                              sleep_duration: int) -> float:
    # Расчёт BMR (Basal Metabolic Rate) по формуле Миффлина-Джеора
    bmr = 10 * weight + 6.25 * height - 5 * age / 12 + 5 if gender else 10 * weight + 6.25 * height - 5 * age / 12 - 161

    calories_burned = (bmr * (
            int(sleep_duration) / 60)) / 24  # round((bmr / 24 ) * 0.85 * float(sleep_duration / 60), 1)
    return round(calories_burned, 1)


def evaluate_bedtime(sleep_data: SleepRecord) -> datetime:
    if sleep_data.device_bedtime <= sleep_data.bedtime:
        return sleep_data.device_bedtime
    return sleep_data.bedtime


def evaluate_wake_time(sleep_data: SleepRecord) -> datetime:
    if sleep_data.device_wake_up_time >= sleep_data.wake_up_time:
        return sleep_data.device_wake_up_time
    return sleep_data.wake_up_time


'''def compute_rr_intervals(bpm_list: list | np.ndarray) -> np.ndarray:
    # Переводим bpm в RR-интервалы (мс)
    bpm_array = np.asarray(bpm_list, dtype=np.float64)
    return 60_000.0 / bpm_array


def compute_time_domain(rr_intervals: np.array) -> dict:
    """
    Вычисляет основные временные параметры HRV: SDNN, RMSSD, pNN50
    """
    results = {
        'SDNN': sdnn(rr_intervals)['sdnn'],
        'RMSSD': rmssd(rr_intervals)['rmssd'],
        'pNN50': nn50(rr_intervals)['pnn50']
    }
    return results


def compute_frequency_domain(rr_intervals: np.array) -> dict:
    """
    Вычисляет частотные параметры HRV через метод Уэлча
    Возвращает LF, HF, HF/LF
    """

    # welch_psd принимает последовательность RRI (сек) - переводим из мс в с

    result = welch_psd(rr_intervals / 1000.0, show=False)

    return {
        'POWER': result['fft_abs'],
        'LF/HF': result['fft_ratio']
    }


def compute_nonlinear(rr_intervals):
    """
    Вычисляет нелинейные параметры HRV: SD1, SD2 и асимметрию (по методике Poincare)
    """

    stats = poincare(rr_intervals)
    return {'SD1': stats['sd1'], 'SD2': stats['sd2'], 'SD_ratio': stats['sd_ratio']}'''

"""def compute_hrv_for_record(record: SleepRecord) -> dict:
    # Извлекаем bpm по ночам и дню
    night_bpms = [entry.bpm for entry in record.night_hr_entries.order_by('time')]
    day_bpms = [entry.bpm for entry in record.day_hr_entries.order_by('time')]

    # Вычисляем RRI
    rr_night = compute_rr_intervals(night_bpms)
    rr_day = compute_rr_intervals(day_bpms)

    # Временная область
    td_night = compute_time_domain(rr_night)
    td_day = compute_time_domain(rr_day)

    # Частотная область
    fd_night = compute_frequency_domain(rr_night)
    fd_day = compute_frequency_domain(rr_day)

    # Нелинейная область
    nl_night = compute_nonlinear(rr_night)
    nl_day = compute_nonlinear(rr_day)

    return {
        'time_domain': {'night': td_night, 'day': td_day},
        'frequency_domain': {'night': fd_night, 'day': fd_day},
        'nonlinear': {'night': nl_night, 'day': nl_day}
    }"""


def chronotype_assessment(user: User, day: int = None) -> dict:
    """
    Оценка хронотипа пользователя на основе данных о сне за последние N дней.
    """
    try:
        # Находим последнюю запись сна для пользователя
        sleep_data = SleepRecord().get_last_sleep_records(user=user, days=day)
    except SleepRecord.DoesNotExist:
        return {}

    if not sleep_data:
        return {}

    # Разделяем на рабочие дни и выходные (по дате начала сна)
    free_midpoints = []
    all_midpoints = []
    free_durations = []
    all_durations = []

    for record in sleep_data:
        total_bedtime = evaluate_bedtime(record)

        # расчёт midpoint как datetime
        midpoint = total_bedtime + timedelta(minutes=record.duration / 2)

        midpoint_hour = midpoint.hour + midpoint.minute / 60 + midpoint.second / 3600

        all_midpoints.append(midpoint_hour)

        all_durations.append(record.duration / 60)

        # считаем выходные по дню недели bedtime
        if total_bedtime.weekday() >= 5:
            free_midpoints.append(midpoint_hour)
            free_durations.append(record.duration / 60)

    # средние
    free_midpoints_np = np.array(free_midpoints, dtype=np.float64)
    free_durations_np = np.array(free_durations, dtype=np.float64)
    all_durations_np = np.array(all_durations, dtype=np.float64)

    msf = np.mean(free_midpoints_np)  # mid-sleep free
    sd_free = np.mean(free_durations_np)  # sleep duration free
    sd_week = np.mean(all_durations_np)  # sleep duration week

    # скорректированный mid-sleep (MSFsc)
    msf_sc = msf - 0.5 * (sd_free - sd_week)
    msf_sc_hours = int(msf_sc)
    msf_sc_minutes = int((msf_sc % 1) * 60)
    interpret_str = interpret_chronotype(msf_time=time(hour=msf_sc_hours, minute=msf_sc_minutes),
                                         name="sleep_statistic", language="ru")

    key = interpret_str.keys()


    match key:
        case key if 'skylark' in key:
            interpret_str['img'] = 'skylark.png'
        case key if 'pigeon' in key:
            interpret_str['img'] = 'pigeon.png'
        case key if 'owl' in key:
            interpret_str['img'] = 'owl.png'
        case _:
            interpret_str['img'] = None

    return interpret_str


def calculate_cycle_count(sleep_data: SleepRecord) -> int:
    """
    Количество циклов сна в последней записи сна пользователя.
    Цикл считается завершённым, если он длится более 90 минут и содержит как минимум одну фазу глубокого и REM сна.
    1 цикл = 90 минут (минимум) + глубокий сон + REM
    Если цикл не завершён, то он не учитывается.
    """

    # Находим последнюю запись сна для пользователя
    segments = sleep_data.segments.order_by('start_time')
    cycle_count = 0
    current_cycle_duration = 0
    has_deep = False
    has_rem = False
    for i, seg in enumerate(segments):
        duration_min = (seg['end_time'] - seg['start_time']).total_seconds() / 60
        if seg['state'] in [2, 3, 4]:  # Light, Deep, REM
            current_cycle_duration += duration_min
            if seg['state'] == 3:
                has_deep = True
            if seg['state'] == 4:
                has_rem = True
        if seg['state'] == 5 or i == len(segments) - 1:  # Awake or end
            if current_cycle_duration >= 90 and has_deep and has_rem:
                cycle_count += 1
            current_cycle_duration = 0
            has_deep = False
            has_rem = False
    return cycle_count


def time_to_minutes(dt, ref_hour=20):
    """
    Преобразует время в минуты от 00:00, нормализуя относительно заданного референсного часа (по умолчанию 20:00).
    """

    if not dt:
        return None
    # Извлекаем часы и минуты
    hours = dt.hour
    minutes = dt.minute
    # Преобразуем в минуты от 00:00
    total_minutes = hours * 60 + minutes
    # Нормализуем относительно ref_hour (20:00), чтобы учесть переход через полночь
    ref_minutes = ref_hour * 60
    normalized_minutes = (total_minutes - ref_minutes) % 1440  # 1440 минут = 24 часа
    return normalized_minutes


def sleep_regularity(user: User, day: int = None) -> dict:
    """
    Оценка регулярности сна пользователя на основе стандартного отклонения времени отхода ко сну и пробуждения
    за последние N дней.
    """
    try:
        sleep_data_interval = SleepRecord().get_last_sleep_records(user=user, days=day)
    except SleepRecord.DoesNotExist:
        return {}

    bedtimes = [time_to_minutes(r.bedtime) for r in sleep_data_interval]
    wake_times = [time_to_minutes(r.wake_up_time) for r in sleep_data_interval]

    bedtime_std = round(np.std(bedtimes), 2) if len(bedtimes) >= 2 else 0
    wake_time_std = round(np.std(wake_times), 2) if len(wake_times) >= 2 else 0

    return {
        'bedtime_std': bedtime_std,
        'wake_time_std': wake_time_std
    }

def calculate_sleep_statistics_metrics(sleep_data: SleepRecord, age: np.float64 = None, gender: int = None,
                                     weight: float = None, height: int = None) -> dict:
    """
    Вычисляет основные метрики сна на основе последней записи сна пользователя.
    Возвращает словарь с метриками:
    - latency_minutes: Латентность сна в минутах
    - sleep_efficiency: Эффективность сна в процентах
    - sleep_phases: Процент каждой фазы сна (глубокий, легкий, REM, бодрствование)
    - sleep_fragmentation_index: Индекс фрагментации сна
    - sleep_calories_burned: Сожжённые калории во время сна (на основе BMR)

    Возвращает пустой словарь, если передан None или невалидные данные.
    """
    if not sleep_data or not hasattr(sleep_data, 'segments'):
        return {}

    try:
        total_bedtime = evaluate_bedtime(sleep_data) if hasattr(sleep_data, 'bedtime') else None
        total_wake_time = evaluate_wake_time(sleep_data) if hasattr(sleep_data, 'wake_up_time') else None

        # Латентность сна в минутах
        latency_minutes = 0.0
        if total_bedtime:
            first_segment = sleep_data.segments.order_by('start_time').values_list('start_time', flat=True).first()
            if first_segment:
                latency_delta = first_segment - total_bedtime
                latency_minutes = latency_delta.total_seconds() / 60 if hasattr(latency_delta, 'total_seconds') else 0.0

        # Эффективность сна
        sleep_efficiency = 0.0
        if (total_bedtime and total_wake_time and
            hasattr(total_wake_time, '__sub__') and
            hasattr(total_bedtime, '__sub__')):
            try:
                total_time_in_bed_min = (total_wake_time - total_bedtime).total_seconds() / 60
                if total_time_in_bed_min > 0 and hasattr(sleep_data, 'duration') and sleep_data.duration:
                    sleep_efficiency = min(100.0, max(0.0, sleep_data.duration * 100 / total_time_in_bed_min))
            except (AttributeError, TypeError, ZeroDivisionError):
                pass

        # Процент каждой фазы сна
        sleep_phases = {
            'deep': 0.0,
            'light': 0.0,
            'rem': 0.0,
            'awake': 0.0
        }

        if hasattr(sleep_data, 'duration') and sleep_data.duration:
            total_sleep_time = sleep_data.duration + getattr(sleep_data, 'sleep_awake_duration', 0)
            if total_sleep_time > 0:
                for phase in ['deep', 'light', 'rem', 'awake']:
                    phase_duration = getattr(sleep_data, f'sleep_{phase}_duration', 0)
                    sleep_phases[phase] = min(100.0, max(0.0, (phase_duration / total_sleep_time) * 100))

        # Индекс фрагментации сна
        interpret_fragmentation = 0.0
        if (hasattr(sleep_data, 'awake_count') and sleep_data.awake_count is not None and
            hasattr(sleep_data, 'duration') and sleep_data.duration and sleep_data.duration > 0):
            try:
                interpret_fragmentation = sleep_data.awake_count / (sleep_data.duration / 60)
            except ZeroDivisionError:
                pass

        # Сожжённые калории во время сна (на основе BMR)
        sleep_calories_burned = 0.0
        if all([gender is not None, weight, height, age, hasattr(sleep_data, 'duration')]):
            try:
                sleep_calories_burned = calculate_calories_burned(
                    gender=gender,
                    weight=weight,
                    height=height,
                    age=age,
                    sleep_duration=getattr(sleep_data, 'duration', 0)
                )
            except (TypeError, ValueError):
                pass

        return {
            'latency_minutes': round(latency_minutes, 2) if latency_minutes is not None else 0.0,
            'sleep_efficiency': round(sleep_efficiency, 2) if sleep_efficiency is not None else 0.0,
            'sleep_phases': sleep_phases,
            'sleep_fragmentation_index': round(interpret_fragmentation, 2) if interpret_fragmentation is not None else 0.0,
            'sleep_calories_burned': round(sleep_calories_burned, 2) if sleep_calories_burned is not None else 0.0,
        }

    except Exception:

        return {}

'''def calculate_sleep_statistics_metrics(sleep_data: SleepRecord, age: np.float64, gender: int, weight: float,
                                       height: int) -> dict:
    """
    Вычисляет основные метрики сна на основе последней записи сна пользователя.
    Возвращает словарь с метриками:
    - latency_minutes: Латентность сна в минутах
    - sleep_efficiency: Эффективность сна в процентах
    - sleep_phases: Процент каждой фазы сна (глубокий, легкий, REM, бодрствование)
    - sleep_fragmentation_index: Индекс фрагментации сна
    - sleep_calories_burned: Сожжённые калории во время сна (на основе BMR)
    """

    total_bedtime = evaluate_bedtime(sleep_data)
    total_wake_time = evaluate_wake_time(sleep_data)

    # Латентность сна в минутах
    latency_delta = sleep_data.segments.order_by('start_time').values_list('start_time',
                                                                           flat=True).first() - total_bedtime
    latency_minutes = latency_delta.total_seconds() / 60 if latency_delta else 0

    # Эффективность сна
    total_time_in_bed_min = (total_wake_time - total_bedtime).total_seconds() / 60
    sleep_efficiency = sleep_data.duration * 100 / total_time_in_bed_min if total_time_in_bed_min else 0

    # Процент каждой фазы сна
    sleep_phases = {
        'deep': sleep_data.sleep_deep_duration / (
                sleep_data.duration + sleep_data.sleep_awake_duration) * 100 if sleep_data.duration else 0,
        'light': sleep_data.sleep_light_duration / (
                sleep_data.duration + sleep_data.sleep_awake_duration) * 100 if sleep_data.duration else 0,
        'rem': sleep_data.sleep_rem_duration / (
                sleep_data.duration + sleep_data.sleep_awake_duration) * 100 if sleep_data.duration else 0,
        'awake': sleep_data.sleep_awake_duration / (
                sleep_data.duration + sleep_data.sleep_awake_duration) * 100 if sleep_data.duration else 0,
    }

    # Индекс фрагментации сна
    interpret_fragmentation = (sleep_data.awake_count / (sleep_data.duration / 60)) if sleep_data.duration else 0

    # Сожжённые калории во время сна (на основе BMR)
    sleep_calories_burned = calculate_calories_burned(gender=gender, weight=weight, height=height, age=age,
                                                      sleep_duration=sleep_data.duration)

    return {
        'latency_minutes': latency_minutes,
        'sleep_efficiency': sleep_efficiency,
        'sleep_phases': sleep_phases,
        'sleep_fragmentation_index': interpret_fragmentation,
        'sleep_calories_burned': sleep_calories_burned,
    }'''


def avg_sleep_duration(items: list):
    """
    Средняя продолжительность сна за последние N дней.
    items: список объектов SleepStatistics
    """

    durations = [s.duration for s in items if s.duration]
    if durations:
        return round(np.mean(durations) / 60, 2)
    return 0
