from django import forms
from django.contrib.auth.forms import UserCreationForm
from datetime import date
from .models import SleepRecord, UserData, User



class UserDataForm(forms.ModelForm):
    GENDER_CHOICES = (
        (1, 'Мужской'),
        (0, 'Женский'),
    )
    date_of_birth = forms.DateField(required=True, label='Дата рождения',
                                    widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date', 'max': date.today().isoformat(),}), input_formats=['%Y-%m-%d', '%d.%m.%Y'])
    weight = forms.IntegerField(min_value=10, required=True, label='Вес',
                                widget=forms.TextInput(attrs={'placeholder': 'Введите ваш вес (кг)'}))
    gender = forms.TypedChoiceField(label='Пол', coerce=int, choices=GENDER_CHOICES)
    height = forms.IntegerField(min_value=10, required=True, label='Рост',
                                widget=forms.TextInput(attrs={'placeholder': 'Введите ваш рост (см)'}))
    active = forms.BooleanField(label='Подписаться на рассылку', required=False)

    class Meta:
        model = UserData
        fields = ['date_of_birth', 'weight', 'gender', 'height', 'active']


class UserRegistrationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['password1'].help_text = 'Ваш пароль должен содержать не менее 8 символов.'
        self.fields['password2'].help_text = 'Введите тот же пароль, что и раньше, для подтверждения.'

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        labels = {
            'username': 'Никнейм',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'password1': 'Пароль',
            'password2': 'Повторите пароль',
        }
        help_texts = {
            'username': 'Требуемый. не более 150 символов. Только буквы, цифры и @/./+/-/_.',
        }


class UserInfoUpdateForm(forms.ModelForm):
    username = forms.CharField(label='Ник', max_length=150)
    first_name = forms.CharField(label='Имя', max_length=150)
    last_name = forms.CharField(label='Фамилия', max_length=150)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        labels = {
            'username': 'Ник',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
        }


class SleepRecordForm(forms.ModelForm):
    sleep_deep_duration = forms.IntegerField(label='Общая продолжительность глубокой фазы сна:',
                                             widget=forms.TextInput(attrs={'placeholder': 'Введите число в минутах'}))
    sleep_light_duration = forms.IntegerField(label='Общая продолжительность лёгкой фазы сна:',
                                              widget=forms.TextInput(attrs={'placeholder': 'Введите число в минутах'}))
    total_time_bed = forms.IntegerField(label='Общее время, проведённое в кровати:',
                                        widget=forms.TextInput(attrs={'placeholder': 'Введите число в минутах'}))

    class Meta:
        model = SleepRecord
        fields = ['sleep_deep_duration', 'sleep_light_duration', 'total_time_bed']
        labels = {
            'sleep_deep_duration': 'Продолжительность глубокой фазы сна:',
            'sleep_light_duration': 'Продолжительность лёгкой фазы сна:',
            'total_time_bed': 'Общее время, проведённое в кровати:',
        }


class UpdateSleepRecordForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super(UpdateSleepRecordForm, self).__init__(*args, **kwargs)
        # Filter the queryset based on the user input
        self.fields['data_sleep'].queryset = SleepRecord.objects.filter(user=user).values_list('sleep_date_time',
                                                                                               flat=True).distinct()

    data_sleep = forms.ModelChoiceField(
        queryset=SleepRecord.objects.values_list('sleep_date_time', flat=True).distinct(),
        label='Дата:', to_field_name='sleep_time')
    sleep_deep_duration = forms.IntegerField(label='Общая продолжительность глубокой фазы сна:',
                                             widget=forms.TextInput(attrs={'placeholder': 'Введите число в минутах'}))
    sleep_light_duration = forms.IntegerField(label='Общая продолжительность лёгкой фазы сна:',
                                              widget=forms.TextInput(attrs={'placeholder': 'Введите число в минутах'}))
    total_time_bed = forms.IntegerField(label='Общее время, проведённое в кровати:',
                                        widget=forms.TextInput(attrs={'placeholder': 'Введите число в минутах'}))

    class Meta:
        model = SleepRecord
        fields = ['data_sleep', 'sleep_deep_duration', 'sleep_light_duration', 'total_time_bed']
        labels = {
            'sleep_deep_duration': 'Продолжительность глубокой фазы сна:',
            'sleep_light_duration': 'Продолжительность лёгкой фазы сна:',
            'total_time_bed': 'Общее время, проведённое в кровати:',
        }


class CSVImportForm(forms.Form):
    csv_file = forms.FileField(label='Выберите CSV-файл', widget=forms.ClearableFileInput(
        attrs={'class': 'dropzone','id': 'csv-dropzone', 'accept': '.csv'}))
