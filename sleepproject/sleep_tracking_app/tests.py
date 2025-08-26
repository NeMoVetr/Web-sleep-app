from django.test import TestCase

# Create your tests here.
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sleepproject.settings')
django.setup()

from sleep_tracking_app.models import UserData, User, SleepRecord

from sleep_statistic import *


def test_sleep_statistics():
    # Выбираем первого пользователя из базы данных
    user = User.objects.first()
    if not user:
        print("No users found in the database.")
        return
    print(f"Testing for user: {user.username}")

    # Получаем данные пользователя из UserData
    user_data = UserData.objects.get(user=user)
    if not user_data:
        print("No user data found for the user.")
        return

    # Вычисляем возраст в месяцах
    age_months = user_data.get_age_months()

    # 1. Chronotype assessment для последних 7 дней
    msf_sc = chronotype_assessment(user, day=7)
    print(f"Ваш хронотип: {msf_sc}")


    # 2. sleep_regularity для последних 7 дней
    regularity = sleep_regularity(user, day=7)
    print(f"Sleep Regularity: {regularity}")

    # 3. Sleep statistics для последней записи сна
    latest_sleep = SleepRecord.objects.filter(user=user).order_by('-sleep_date_time').first()
    if latest_sleep:
        metrics = calculate_sleep_statistics_metrics(
            sleep_data=latest_sleep,
            age=age_months,
            gender=user_data.gender,
            weight=user_data.weight,
            height=user_data.height
        )
        print("\n--- Sleep Statistics Metrics ---")
        for key, value in metrics.items():
            if isinstance(value, dict):
                print(f"{key}:")
                for k, v in value.items():
                    print(f"  {k}: {v} %")
            else:
                print(f"{key}: {value}")
    else:
        print("No sleep records found for the user.")


if __name__ == '__main__':
    test_sleep_statistics()
