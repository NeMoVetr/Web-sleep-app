from django.contrib import admin


from .models import SleepRecord, Reminder, SleepStatistics, UserData


# Register your models here.
class UserDataAdmin(admin.ModelAdmin):
    search_fields = ['user_name', 'weight', 'gender', 'height', 'active']

    def user_name(self, obj):
        return obj.user.username


class SleepRecordAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'sleep_time', 'deep_sleep_duration', 'fast_sleep_duration']
    list_filter = ['user']
    search_fields = ['user', 'sleep_time', 'deep_sleep_duration', 'fast_sleep_duration']

    def user_name(self, obj):
        return obj.user.username


class ReminderAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'date', 'active_mailing']
    list_filter = ['user', 'date']
    search_fields = ['user', 'date', 'reminder_text']

    def user_name(self, obj):
        return obj.user.username

    def active_mailing(self, obj):
        return obj.user.active


class SleepStatisticsAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'sleep_duration', 'sleep_quality', 'health_impact', 'date', 'calories_burned']
    list_filter = ['user', 'sleep_duration', 'sleep_quality']
    search_fields = ['user', 'sleep_duration', 'sleep_quality']

    def delete_model(self, request, obj):
        # Удаляем все записи SleepStatistics, связанные с удаляемым пользователем
        SleepStatistics.objects.filter(user=obj.user).delete()

    def user_name(self, obj):
        return obj.user.username


admin.site.register(UserData, UserDataAdmin)
admin.site.register(SleepRecord, SleepRecordAdmin)
admin.site.register(Reminder, ReminderAdmin)
admin.site.register(SleepStatistics, SleepStatisticsAdmin)
