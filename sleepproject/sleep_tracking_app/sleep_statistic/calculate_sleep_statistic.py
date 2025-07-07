from django.utils import timezone

from datetime import datetime, timedelta
import numpy as np
from pyhrv.time_domain import sdnn, rmssd, nn50
from pyhrv.frequency_domain import welch_psd
from pyhrv.nonlinear import poincare
from sleep_tracking_app.models import SleepRecord, User

date_current = timezone.now()


def calculate_calories_burned(gender: int, weight: float, height: int, age: float,
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


def compute_rr_intervals(bpm_list: list | np.ndarray) -> np.ndarray:
    # Переводим bpm в RR-интервалы (мс) с использованием векторизированных операций NumPy
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
    f, psd = welch_psd(rr_intervals / 1000.0)

    # LF: 0.04–0.15 Hz, HF: 0.15–0.4 Hz
    lf_band = (0.04, 0.15)
    hf_band = (0.15, 0.4)
    lf_power = np.sum(psd[(f >= lf_band[0]) & (f < lf_band[1])])
    hf_power = np.sum(psd[(f >= hf_band[0]) & (f < hf_band[1])])
    return {'LF': lf_power, 'HF': hf_power, 'HF/LF': hf_power / max(lf_power, 1)}


def compute_nonlinear(rr_intervals):
    """
    Вычисляет нелинейные параметры HRV: SD1, SD2 и асимметрию (по методике Poincare)
    """

    stats = poincare(rr_intervals)
    return {'SD1': stats['sd1'], 'SD2': stats['sd2'], 'SD_ratio': stats['sd_ratio']}


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


def chronotype_assessment(user: User, day: int = 7) -> float:
    """
    Оценка хронотипа пользователя на основе данных о сне за последние N дней.
    """

    sleep_data = SleepRecord.objects.filter(user=user, sleep_time__gte=date_current - timedelta(days=day))

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

    # 3. средние
    free_midpoints_np = np.array(free_midpoints, dtype=np.float64)
    free_durations_np = np.array(free_durations, dtype=np.float64)
    all_durations_np = np.array(all_durations, dtype=np.float64)

    msf = np.mean(free_midpoints_np)  # mid-sleep free
    sd_free = np.mean(free_durations_np)  # sleep duration free
    sd_week = np.mean(all_durations_np)  # sleep duration week

    # 4. скорректированный mid-sleep (MSFsc)
    msf_sc = msf - 0.5 * (sd_free - sd_week)

    return msf_sc


def calculate_recovery_index(user: User, age: float, gender: int, day: int = 60) -> float:
    """
    Оценка индекса восстановления на основе данных о сне за последние N дней
    """
    sleep_data = SleepRecord.objects.filter(user=user, sleep_time__gte=date_current - timedelta(days=day))

    aggregated_night_bpms = []
    for rec in sleep_data:
        night_bpms = [entry.bpm for entry in
                      rec.night_hr_entries.order_by('time')]  # нужна ли группировка по дате и времени?
        aggregated_night_bpms.extend(night_bpms)

    # 3. HRV для «ночной» части — из текущей записи
    night_bpms_current = [e.bpm for e in sleep_data.latest('sleep_time').night_hr_entries.order_by('time')]
    rr_night_current = compute_rr_intervals(night_bpms_current)
    td_night = compute_time_domain(rr_night_current)
    fd_night = compute_frequency_domain(rr_night_current)
    nl_night = compute_nonlinear(rr_night_current)

    # 4. HRV для агрегированных ночных 60-дневных замеров
    rr_aggregated = compute_rr_intervals(aggregated_night_bpms)
    td_agg = compute_time_domain(rr_aggregated)

    # 5. Коэффициенты по полу и возрасту
    # gender = user.user_data.gender
    k_gender = 1.0 if gender else 1.12

    k_age = 1 + (40 - age / 12) / 100

    # 6. Формируем Recovery Index
    rmssd_ratio = (td_night['RMSSD'] / td_agg['RMSSD']) * 40
    hf_lf = fd_night['HF/LF'] * 30
    sd_ratio = nl_night['SD_ratio'] * 20
    sdnn_ratio = (td_night['SDNN'] / td_agg['SDNN']) * 10

    recovery_index = (
            k_age * k_gender * rmssd_ratio +
            hf_lf +
            sd_ratio +
            k_age * sdnn_ratio
    )

    return recovery_index


def calculate_sleep_statistics_metrics(sleep_data: SleepRecord, age: float, gender: int, weight: float,
                                       height: int) -> dict:
    total_bedtime = evaluate_bedtime(sleep_data)
    total_wake_time = evaluate_wake_time(sleep_data)

    # age = float((date_current.year - user_data.date_of_birth.year) * 12 + (
    #        date_current.month - user_data.date_of_birth.month))

    # Латентность сна в минутах
    latency_delta = sleep_data.segments.start_time.first() - total_bedtime
    latency_minutes = latency_delta.total_seconds() / 60 if latency_delta else 0

    # Эффективность сна
    total_time_in_bed_min = (total_wake_time - total_bedtime).total_seconds() / 60
    sleep_efficiency = sleep_data.duration * 100 / total_time_in_bed_min if total_time_in_bed_min else 0

    # Процент каждой фазы сна
    sleep_phases = {
        'deep': sleep_data.sleep_deep_duration / sleep_data.duration * 100 if sleep_data.duration else 0,
        'light': sleep_data.sleep_light_duration / sleep_data.duration * 100 if sleep_data.duration else 0,
        'rem': sleep_data.sleep_rem_duration / sleep_data.duration * 100 if sleep_data.duration else 0,
        'awake': sleep_data.sleep_awake_duration / sleep_data.duration * 100 if sleep_data.duration else 0,
    }

    # Индекс фрагментации сна
    sleep_fragmentation_index = (sleep_data.awake_count / (sleep_data.duration / 60)) if sleep_data.duration else 0

    # Сожжённые калории во время сна (на основе BMR)
    sleep_calories_burned = calculate_calories_burned(gender=gender, weight=weight, height=height, age=age,
                                                      sleep_duration=sleep_data.duration)

    return {
        'latency_minutes': latency_minutes,
        'sleep_efficiency': sleep_efficiency,
        'sleep_phases': sleep_phases,
        'sleep_fragmentation_index': sleep_fragmentation_index,
        'sleep_calories_burned': sleep_calories_burned,
    }


def main():
    pass


if __name__ == "__main__":
    main()
