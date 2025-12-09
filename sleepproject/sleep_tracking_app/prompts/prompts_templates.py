from typing import List

from sleep_tracking_app.models import UserData, SleepStatistics, SleepRecord


def create_sleep_analysis_prompt(
        user_data: UserData,
        sleep_statistics_list: List[SleepStatistics],
        sleep_records_list: List[SleepRecord]) -> str:
    """
    Создает промпт для анализа сна на основе данных пользователя
    и нескольких последних ночей сна.

    ВАЖНО:
    - Первый элемент списков считается ПОСЛЕДНЕЙ ночью (самая свежая запись).
    - Второй элемент — ПРЕДЫДУЩЕЙ ночью.
    """

    # Базовые параметры пользователя
    user_info = f"""Демографические данные:
        - Возраст в месяцах: {user_data.get_age_months()}
        - Пол: {user_data.get_gender()}
        - Вес: {user_data.weight} кг
        - Рост: {user_data.height} см
    """

    nights_blocks = []

    for idx, (sleep_statistics, sleep_record) in enumerate(
            zip(sleep_statistics_list, sleep_records_list), start=1):
        # Определяем заголовок для ночи
        if idx == 1:
            night_label = "Последняя ночь (самая свежая запись)"
        elif idx == 2:
            night_label = "Предыдущая ночь (за день до последней)"
        else:
            night_label = f"Более ранняя ночь номер {idx}"

        # Попробуем взять дату, если она есть в модели SleepStatistics
        date_str = ""
        date_value = getattr(sleep_statistics, "date", None)
        if date_value:
            date_str = f"\n- Дата: {date_value}"

        sleep_info = f"""{night_label}:{date_str}
            - Продолжительность сна: {sleep_record.duration} минут
            - Глубокий сон: {sleep_record.sleep_deep_duration} минут
            - Легкий сон: {sleep_record.sleep_light_duration} минут
            - Эффективность сна: {sleep_statistics.sleep_efficiency}%
            - Индекс фрагментации сна: {sleep_statistics.sleep_fragmentation_index}
            - Время засыпания: {sleep_statistics.latency_minutes} минут
            - Калории, сожжённые во сне: {sleep_statistics.sleep_calories_burned} ккал
        """

        # Добавляем REM-сон если есть данные
        if getattr(sleep_record, "sleep_rem_duration", None):
            if sleep_record.sleep_rem_duration > 0:
                sleep_info += f"\n- REM-сон: {sleep_record.sleep_rem_duration} минут"

        # Добавляем пульс если есть данные
        if getattr(sleep_record, "avg_hr", None):
            sleep_info += f"\n- Средний пульс: {sleep_record.avg_hr} уд/мин"
        if getattr(sleep_record, "min_hr", None):
            sleep_info += f"\n- Минимальный пульс: {sleep_record.min_hr} уд/мин"
        if getattr(sleep_record, "max_hr", None):
            sleep_info += f"\n- Максимальный пульс: {sleep_record.max_hr} уд/мин"
        if getattr(sleep_record, "awake_count", None):
            sleep_info += f"\n- Количество пробуждений: {sleep_record.awake_count}"

        nights_blocks.append(sleep_info)

    nights_info = "\n\n".join(nights_blocks) if nights_blocks else "Нет данных по ночам сна."

    prompt = f"""
        {user_info}
        
        Мои параметры сна за последние ночи:
        
        {nights_info}
        
        Внимательно проанализируй мои записи сна. Чётко учитывай, что первая описанная ночь — это ПОСЛЕДНЯЯ ночь (самая свежая запись),
        вторая — ПРЕДЫДУЩАЯ ночь. Сравни показатели между последней и предпредыдущей ночью, опиши тенденции и изменения.
        Дай конкретные советы, как улучшить мой сон, с опорой в первую очередь на последнюю ночь, но с учётом динамики по сравнению с предыдущей.
    """

    return prompt


def get_system_prompt() -> str:
    """
    Возвращает системный промпт для модели
    """
    return """Ты — эксперт по сну (сомнолог), 
            твоя задача дать краткую рекомендацию пользователю на основе показателей, которые он прислал. 
            Твой ответ должен в развёрнутых предложениях, чтобы пользователь понял, что ты эксперт который может донести свою мысль простыми словами.
            Примечание: запрещено использовать язык разметки Markdown."""
