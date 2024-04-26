from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


# Create your models here.
class UserData(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_data')
    date_of_birth = models.DateField()
    weight = models.FloatField(validators=[MinValueValidator(10)])  # Вес в кг
    gender = models.CharField(max_length=10)  # Пол
    height = models.IntegerField(validators=[MinValueValidator(10)])  # Рост в см

    active = models.BooleanField(default=False)


class SleepRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sleep_time = models.DateField(auto_now_add=True)
    deep_sleep_duration = models.DecimalField(max_digits=5, decimal_places=2,
                                              validators=[MinValueValidator(0), MaxValueValidator(24)])  # часы
    fast_sleep_duration = models.DecimalField(max_digits=5, decimal_places=2,
                                              validators=[MinValueValidator(0), MaxValueValidator(24)])  # часы
    total_time_bed = models.DecimalField(max_digits=5, decimal_places=2,
                                         validators=[MinValueValidator(0), MaxValueValidator(24)])


class SleepStatistics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sleep_duration = models.FloatField()  # deep_sleep_duration + fast_sleep_duration
    sleep_quality = models.FloatField()   # Это поле генерируется на основании данных пользователя
    health_impact = models.CharField(max_length=255)  # краткая сводка которая основывается на полученных результатах
    date = models.DateField(auto_now_add=True)
    calories_burned = models.FloatField()  # сожженные калории во сне
