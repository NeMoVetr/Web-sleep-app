from django.urls import path

from .tasks import send_reminder_email, import_sleep_records
from .views import home, register, add_users_sleep_data, user_update, sleep_statistics_show, \
    profile, sleep_record_update, CustomPasswordResetView, CustomPasswordResetDoneView, CustomPasswordResetConfirmView, \
    CustomPasswordResetCompleteView, sleep_records_from_csv, custom_logout

urlpatterns = [
    path('send_reminder_email/', send_reminder_email, name='send_reminder_email'),

    #path("celery-progress/", import_sleep_records, name="import_sleep_records"),

    path('', home, name='home'),
    path('add-users-sleep-data/', add_users_sleep_data, name='add_users_sleep_data'),
    path('user-update', user_update, name='user_update'),
    path('sleep-record-update/', sleep_record_update, name='sleep_record_update'),
    path('sleep-records-from-csv/', sleep_records_from_csv, name='sleep_records_from_csv'),
    path('profile/', profile, name='profile'),
    path('sleep-statistics-show/', sleep_statistics_show, name='sleep_statistics_show'),
    path('register/', register, name='register'),
    path('logout/', custom_logout, name='custom_logout'),

    path('custom-password-reset-confirm/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(),
         name='custom_password_reset_confirm'),
    path('custom-password-reset-done/', CustomPasswordResetDoneView.as_view(), name='custom_password_reset_done'),
    path('custom-password-reset/', CustomPasswordResetView.as_view(), name='custom_password_reset'),
    path('custom-password-complete/', CustomPasswordResetCompleteView.as_view(), name='custom_password_reset_complete'),
]
