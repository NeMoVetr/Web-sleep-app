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


class Reminder(models.Model):
    user = models.ForeignKey(UserData, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    reminder_text = models.TextField(
        'Уважаемый пользователь,\n\nМы надеемся, что наш сервис помогает вам лучше понять своё состояние сна. Чтобы обеспечить максимальную эффективность и точность данных, мы хотели бы напомнить вам о важности регулярного обновления информации в приложении.\n\nПожалуйста, не забывайте вносить данные о вашем сне ежедневно. Это поможет нам предоставить вам наиболее точные и полезные аналитические данные о вашем сне, что, в свою очередь, поможет вам лучше понять его влияние на ваше здоровье.\n\nМы ценим ваше участие в нашем проекте.\n\nС уважением,\nКоманда GoodSleepPro.')


class SleepStatistics(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sleep_duration = models.FloatField()  # deep_sleep_duration + fast_sleep_duration
    sleep_quality = models.FloatField()   # Это поле генерируется на основании данных пользователя
    health_impact = models.CharField(max_length=255)  # краткая сводка которая основывается на полученных результатах
    date = models.DateField(auto_now_add=True)
    calories_burned = models.FloatField()  # сожженные калории во сне
