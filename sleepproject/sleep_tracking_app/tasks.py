from sleepproject.celery import app  # Фоновая задача
from django.contrib.auth.models import User
from django.core.mail import send_mass_mail


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

