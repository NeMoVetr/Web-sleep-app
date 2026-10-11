from typing import List

from celery import shared_task
import os

from celery_progress.backend import ProgressRecorder
from django.contrib.auth.models import User

from sleepproject.celery import app  # Фоновая задача

from django.core.mail import send_mass_mail

from .import_service import SleepImportService
from .sleep_import import CurrentCsvSleepParser
from .models import SleepRecord, SleepStatistics, UserData


from .service_factory import create_recommendation_engine

@shared_task(bind=True, name='import_sleep_records_task')
def import_sleep_records(self, user_id: int, csv_path: str):
    progress_recorder = ProgressRecorder(self)
    service = SleepImportService(CurrentCsvSleepParser())
    try:
        return service.import_records(
            user_id, csv_path, progress=progress_recorder.set_progress,
        )
    finally:
        if os.path.exists(csv_path):
            os.remove(csv_path)

@shared_task
def sleep_recommended(user_data_id: int, sleep_record_id: List[int], sleep_statistics_id:List[int]):
    user_data = UserData.objects.get(id=user_data_id)
    # Забираем записи сна и статистику одним запросом
    sleep_records_qs = SleepRecord.objects.only(
        'id', 'duration', 'sleep_rem_duration',
        'sleep_deep_duration', 'sleep_light_duration',
    ).filter(id__in=sleep_record_id, user=user_data.user)

    sleep_statistics_qs = SleepStatistics.objects.only(
        'id', 'sleep_efficiency', 'sleep_fragmentation_index',
        'latency_minutes', 'sleep_calories_burned', 'recommended',
    ).filter(id__in=sleep_statistics_id, user=user_data.user)

    sleep_records_map = {r.id: r for r in sleep_records_qs}
    sleep_statistics_map = {s.id: s for s in sleep_statistics_qs}

    # Сохраняем порядок такой же, как в списках id
    sleep_records_list = [sleep_records_map[i] for i in sleep_record_id if i in sleep_records_map]
    sleep_statistics_list = [sleep_statistics_map[i] for i in sleep_statistics_id if i in sleep_statistics_map]

    if not sleep_records_list or not sleep_statistics_list:
        return "Недостаточно данных для анализа сна."

    result = create_recommendation_engine().recommend(
        user_data, sleep_statistics_list, sleep_records_list,
    )
    if not result.text:
        return "Ошибка генерации рекомендаций."

    latest_stat = sleep_statistics_list[0]
    latest_stat.recommended = result.text
    latest_stat.save(update_fields=['recommended'])
    return latest_stat.recommended

@app.task
def send_reminder_email():
    # Получаем все активные напоминания, которые должны быть отправлены
    user = User.objects.filter(user_data__active=True)
    reminder_text = 'Уважаемый пользователь,\n\nМы надеемся, что наш сервис помогает вам лучше понять своё состояние сна. Чтобы обеспечить максимальную эффективность и точность данных, мы хотели бы напомнить вам о важности регулярного обновления информации в приложении.\nПожалуйста, не забывайте вносить данные о вашем сне ежедневно. Это поможет нам предоставить вам наиболее точные и полезные аналитические данные о вашем сне, что, в свою очередь, поможет вам лучше понять его влияние на ваше здоровье.\n\nМы ценим ваше участие в нашем проекте.\n\nС уважением,\nКоманда GoodSleepPro.'
    emails = list(user.values_list('email', flat=True))

    messages = [(
        'Напоминание о ежедневном заполнении данных о отслеживания качества сна',
        reminder_text,
        'goodsleeppro@yandex.ru',
        emails,
    )]

    # Отправляем все письма в одном запросе
    send_mass_mail(messages, fail_silently=False)
