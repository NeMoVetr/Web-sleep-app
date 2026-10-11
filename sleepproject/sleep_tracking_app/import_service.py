"""Persist parsed sleep data independently of Celery and source format."""

from django.contrib.auth.models import User
from django.db import transaction

from .models import SleepRecord, SleepSegment, NightHeartRateEntry, SleepStatistics, UserData
from .sleep_import import SleepDataParser, ProgressCallback, ignore_progress
from .sleep_statistic import calculate_sleep_statistics_metrics


class SleepImportService:
    def __init__(self, parser: SleepDataParser):
        self.parser = parser

    def import_records(self, user_id: int, source, *, progress: ProgressCallback = ignore_progress) -> dict:
        user = User.objects.get(pk=user_id)
        user_data = UserData.objects.get(user=user)
        sleep_data = self.parser.parse(source, progress=progress)

        if sleep_data is None:
            return {"status": "error", "message": "Invalid CSV file"}

        meta, items, night_hr = sleep_data.records, sleep_data.segments, sleep_data.heart_rates
        total = len(meta)
        processed = 0

        # Получаем данные пользователя
        age = user_data.get_age_months()
        gender = user_data.gender
        weight = user_data.weight
        height = user_data.height

        with transaction.atomic():
            # Создаём или обновляем базовые записи сна и собираем их в словарь
            record_map = {}
            for sleep_time, meta_row in meta.iterrows():
                record, _ = SleepRecord.objects.update_or_create(
                    user=user,
                    sleep_date_time=sleep_time,
                    defaults={
                        'sleep_rem_duration': meta_row.get('sleep_rem_duration'),
                        'has_rem': meta_row.get('has_rem'),
                        'min_hr': meta_row.get('min_hr'),
                        'device_bedtime': meta_row.get('device_bedtime'),
                        'sleep_deep_duration': meta_row.get('sleep_deep_duration'),
                        'wake_up_time': meta_row.get('wake_up_time'),
                        'bedtime': meta_row.get('bedtime'),
                        'awake_count': meta_row.get('awake_count'),
                        'duration': meta_row.get('duration'),
                        'max_hr': meta_row.get('max_hr'),
                        'sleep_awake_duration': meta_row.get('sleep_awake_duration'),
                        'avg_hr': meta_row.get('avg_hr'),
                        'sleep_light_duration': meta_row.get('sleep_light_duration'),
                        'device_wake_up_time': meta_row.get('device_wake_up_time'),
                    }
                )
                record_map[sleep_time] = record

                processed += 1

                progress(processed, total, f'Обработано: {processed}/{total}')

            # Удаляем старые дочерние объекты разом
            SleepSegment.objects.filter(record__in=record_map.values()).delete()
            NightHeartRateEntry.objects.filter(record__in=record_map.values()).delete()
            dates = {record.sleep_date_time.date() for record in record_map.values()}
            SleepStatistics.objects.filter(user=user, date__in=dates).delete()

            # Подготавливаем объекты для bulk_create
            segments_to_create = []
            night_hr_to_create = []


            # --- подготавливаем сегменты сна ---
            for idx, seg in items.iterrows():
                record = record_map.get(idx)
                if record is None:
                    continue
                segments_to_create.append(
                    SleepSegment(
                        record=record,
                        start_time=seg['start_time'],
                        end_time=seg['end_time'],
                        state=seg['state']
                    )
                )

            # --- подготавливаем пульс ---
            for record in record_map.values():
                # ночной пульс
                night_mask = (night_hr.index >= record.device_bedtime) & (
                        night_hr.index <= record.device_wake_up_time)
                night_df = night_hr[night_mask]
                night_hr_to_create.extend([
                    NightHeartRateEntry(record=record, time=idx, bpm=row['bpm'])
                    for idx, row in night_df.iterrows()
                ])

            # bulk insert
            SleepSegment.objects.bulk_create(segments_to_create, batch_size=1000)
            NightHeartRateEntry.objects.bulk_create(night_hr_to_create, batch_size=1000)

            # --- подготавливаем статистику сна ---
            sleep_statistic_to_create = []
            for record in record_map.values():
                record.refresh_from_db()
                stats = calculate_sleep_statistics_metrics(record, age, gender, weight, height)

                sleep_statistic_to_create.append(
                    SleepStatistics(
                        user=user,
                        date=record.sleep_date_time.date(),
                        latency_minutes=stats['latency_minutes'],
                        sleep_efficiency=stats['sleep_efficiency'],
                        sleep_phases=stats['sleep_phases'],
                        sleep_fragmentation_index=stats['sleep_fragmentation_index'],
                        sleep_calories_burned=stats['sleep_calories_burned']
                    )
                )

            # bulk insert
            SleepStatistics.objects.bulk_create(sleep_statistic_to_create, batch_size=1000)

        # transaction.atomic откатит изменения автоматически

        return {"status": "completed", "imported": processed}
