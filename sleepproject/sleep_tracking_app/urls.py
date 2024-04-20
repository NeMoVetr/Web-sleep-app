from django.urls import path

from .tasks import send_reminder_email
from .views import home, register, add_users_sleep_data, user_update, sleep_statistics_show, \
    profile, sleep_record_update, CustomPasswordResetView, CustomPasswordResetDoneView, CustomPasswordResetConfirmView, \
    CustomPasswordResetCompleteView

urlpatterns = [
    path('send_reminder_email/', send_reminder_email, name='send_reminder_email'),
    path('', home, name='home'),
    path('add-users-sleep-data/', add_users_sleep_data, name='add_users_sleep_data'),
    path('user-update', user_update, name='user_update'),
    path('sleep-record-update/', sleep_record_update, name='sleep_record_update'),
    path('profile/', profile, name='profile'),
    path('sleep-statistics-show/', sleep_statistics_show, name='sleep_statistics_show'),
    path('register/', register, name='register'),

    path('custom-password-reset-confirm/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(),
         name='custom_password_reset_confirm'),
    path('custom-password-reset-done/', CustomPasswordResetDoneView.as_view(), name='custom_password_reset_done'),
    path('custom-password-reset/', CustomPasswordResetView.as_view(), name='custom_password_reset'),
    path('custom-password-complete/', CustomPasswordResetCompleteView.as_view(), name='custom_password_reset_complete'),
]
