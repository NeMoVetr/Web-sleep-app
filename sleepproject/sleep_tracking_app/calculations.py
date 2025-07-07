from datetime import datetime

from .models import SleepRecord, SleepStatistics, User, UserData


def calculate_sleep_statistics(user: User, user_data: UserData, update: datetime | None = None) -> None:
    # Получаем данные за выбранную дату, если она была передана
    if update:
        sleep_data = SleepRecord.objects.get(user=user, sleep_time=update)
    else:
        # Пытаемся получить последнюю запись SleepRecord для данного пользователя
        sleep_data = SleepRecord.objects.filter(user=user).latest('sleep_time')

    # Общее время сна за последнюю ночь
    sleep_duration = sleep_data.sleep_deep_duration + sleep_data.sleep_light_duration
    sleep_quality = round((sleep_duration / sleep_data.total_time_bed) * 100, 1)
    date_current = datetime.now()
    age = float((date_current.year - user_data.date_of_birth.year) * 12 + (
            date_current.month - user_data.date_of_birth.month))

    health_impact = f"Рекомендуемое время сна: {evaluate_health_impact(age)} часов для вашего возраста"
    calories_burned = calculate_calories_burned(user_data=user_data, age=age, sleep_duration=sleep_duration / 60)

    # Создаем запись в модели SleepStatistics
    if not update:
        SleepStatistics.objects.create(
            user=user,
            sleep_duration=sleep_duration,
            sleep_quality=sleep_quality,
            health_impact=health_impact,
            calories_burned=calories_burned,
        )
    else:
        statistics_entry = SleepStatistics.objects.get(user=user, date=update)
        statistics_entry.sleep_duration = sleep_duration
        statistics_entry.sleep_quality = sleep_quality
        statistics_entry.health_impact = health_impact
        statistics_entry.calories_burned = calories_burned
        statistics_entry.save()


def evaluate_health_impact(age: float) -> str:
    match age:
        case age if 0 <= age <= 3:
            return '14-17'
        case age if 4 <= age <= 11:
            return '12-15'
        case age if 12 <= age <= 2 * 12:
            return '11-14'
        case age if 3 * 12 <= age <= 5 * 12:
            return '10-13'
        case age if 6 * 12 <= age <= 13 * 12:
            return '9-11'
        case age if 14 * 12 <= age <= 17 * 12:
            return '8-10'
        case age if 18 * 12 <= age <= 25 * 12:
            return '7-9'
        case age if 26 * 12 <= age <= 64 * 12:
            return '7-9'
        case age if age >= 65 * 12:
            return '7-8'


def calculate_calories_burned(user_data: UserData, age: float, sleep_duration: float) -> float:
    gender = user_data.gender
    weight = user_data.weight
    height = user_data.height
    if gender == 1:
        BMR = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age // 12)
    else:
        BMR = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age // 12)
    calories_burned = round(BMR / 24 * 0.85 * float(sleep_duration), 1)
    return round(calories_burned, 1)


def plot_sleep_histograms(sleep_statistics: SleepStatistics | list[SleepStatistics]) -> dict:
    if isinstance(sleep_statistics, SleepStatistics):
        dates = [sleep_statistics.date.strftime("%Y-%m-%d")]
        sleep_duration_set = [sleep_statistics.sleep_duration]
    else:
        dates = [record.date.strftime("%Y-%m-%d") for record in sleep_statistics]
        sleep_duration_set = [record.sleep_duration for record in sleep_statistics]

    data = {
        'dates': dates,
        'sleep_duration': sleep_duration_set,
    }

    return data


def plot_sleep_duration_sleep_quality(sleep_statistics: list[SleepStatistics]) -> dict:
    sleep_duration = [record.sleep_duration for record in sleep_statistics]
    sleep_quality = [record.sleep_quality for record in sleep_statistics]
    dates = [record.date.strftime("%Y-%m-%d") for record in sleep_statistics]

    data = {
        'sleep_duration': sleep_duration,
        'sleep_quality': sleep_quality,
        'dates': dates
    }

    return data


def plot_sleep_quality(sleep_statistics: SleepStatistics | list[SleepStatistics]) -> dict:
    if isinstance(sleep_statistics, SleepStatistics):
        dates = [sleep_statistics.date.strftime("%Y-%m-%d")]
        sleep_quality_set = [sleep_statistics.sleep_quality]
    else:
        dates = [statistics.date.strftime("%Y-%m-%d") for statistics in sleep_statistics]
        sleep_quality_set = [statistics.sleep_quality for statistics in sleep_statistics]

    data = {
        'dates': dates,
        'sleep_quality': sleep_quality_set
    }

    return data


def plot_sleep_deep_fast(sleep_records: SleepRecord | list[SleepRecord]) -> dict:
    if isinstance(sleep_records, SleepRecord):
        fast = float(sleep_records.sleep_light_duration) / 60 if sleep_records.sleep_light_duration else 0
        deep = float(sleep_records.sleep_deep_duration) / 60 if sleep_records.sleep_deep_duration else 0
        dates = sleep_records.sleep_date_time.strftime("%Y-%m-%d")
    else:
        fast = [float(record.sleep_light_duration) / 60 for record in sleep_records if record.sleep_light_duration]
        deep = [float(record.sleep_deep_duration) / 60 for record in sleep_records if record.sleep_deep_duration]
        dates = [record.sleep_date_time.strftime("%Y-%m-%d") for record in sleep_records]

    data = {
        'fast_sleep_duration': fast,
        'deep_sleep_duration': deep,
        'dates': dates
    }
    return data
