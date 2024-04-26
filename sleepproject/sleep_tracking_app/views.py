import json
from datetime import datetime

import pandas as pd
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetConfirmView, PasswordResetCompleteView, PasswordResetView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView

from .calculations import calculate_sleep_statistics, plot_sleep_histograms, plot_sleep_duration_sleep_quality, \
    plot_sleep_quality, plot_sleep_deep_fast
from .forms import SleepRecordForm, UserRegistrationForm, UserDataForm, UserInfoUpdateForm, UpdateSleepRecordForm
from .models import SleepRecord, SleepStatistics, UserData


# Create your views here.
def home(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'home.html')


def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        user_data_form = UserDataForm(request.POST)
        if user_form.is_valid() and user_data_form.is_valid():
            user = user_form.save()
            user_data = user_data_form.save(commit=False)
            user_data.user = user
            user_data.save()
            return redirect('home')
    else:
        user_form = UserRegistrationForm()
        user_data_form = UserDataForm()
    return render(request, 'registration/register.html', {'user_form': user_form, 'user_data_form': user_data_form})


@login_required
def add_users_sleep_data(request):
    user = request.user

    today = datetime.now().date()

    sleep_data_exists = SleepRecord.objects.filter(user=user, sleep_time=today).exists()

    if request.method == 'POST':
        form = SleepRecordForm(request.POST)
        if form.is_valid():
            deep_sleep_duration = form.cleaned_data['deep_sleep_duration']
            fast_sleep_duration = form.cleaned_data['fast_sleep_duration']
            total_time_bed = form.cleaned_data['total_time_bed']
            if (deep_sleep_duration + fast_sleep_duration) <= total_time_bed:
                sleep_data = form.save(commit=False)
                sleep_data.user = user
                sleep_data.save()
                return redirect('sleep_statistics_show')
            else:
                messages.warning(request,
                                 'Сумма глубокого и быстрого сна должна быть меньше или равна общему времени в кровати.')
                return redirect('add_users_sleep_data')
    else:
        form = SleepRecordForm()
        sleep_data = None

    return render(request, 'add_users_sleep_data.html',
                  {'form': form, 'sleep_data': sleep_data, 'sleep_data_exists': sleep_data_exists})


@login_required
def user_update(request):
    user = request.user
    try:
        user_data = UserData.objects.get(user=user)
    except UserData.DoesNotExist:
        user_data = None

    if request.method == 'POST':
        form = UserInfoUpdateForm(request.POST, instance=user)
        user_data_form = UserDataForm(request.POST, instance=user_data)

        if form.is_valid() and user_data_form.is_valid():
            user = form.save()
            user_data = user_data_form.save(commit=False)
            user_data.user = user
            user_data.save()
            return redirect('profile')
    else:
        form = UserInfoUpdateForm(instance=user)
        user_data_form = UserDataForm(instance=user_data) if user_data else None

    context = {
        'form': form,
        'user_data_form': user_data_form,
    }
    return render(request, 'update_user.html', context)


@login_required
def profile(request):
    user = request.user
    user_data = UserData.objects.get(user=user)
    context = {
        'user': user,
        'user_data': user_data,
    }
    return render(request, 'web/profile.html', context)


@login_required
def sleep_record_update(request):
    user = request.user
    user_data = UserData.objects.get(user=user)
    if request.method == 'POST':
        form = UpdateSleepRecordForm(user, request.POST)
        if form.is_valid():
            selected_date = form.cleaned_data['data_sleep']
            deep_sleep_duration = form.cleaned_data['deep_sleep_duration']
            fast_sleep_duration = form.cleaned_data['fast_sleep_duration']
            total_time_bed = form.cleaned_data['total_time_bed']
            if (deep_sleep_duration + fast_sleep_duration) <= total_time_bed:
                sleep_record = SleepRecord.objects.filter(user=user, sleep_time=selected_date).first()
                form = UpdateSleepRecordForm(user, request.POST, instance=sleep_record)
                if form.is_valid():
                    form.save()
                    calculate_sleep_statistics(user=user, user_data=user_data, update=selected_date)
                    return redirect('sleep_statistics_show')
            else:
                messages.warning(request,
                                 'Сумма глубокого и быстрого сна должна быть меньше или равна общему времени в кровати.')
                return redirect('sleep_record_update')
    else:
        form = UpdateSleepRecordForm(user)

    return render(request, 'update_sleep_record.html', {'form': form})


@login_required
def sleep_statistics_show(request):
    user = request.user

    user_data = UserData.objects.get(user=user)

    sleep_statistics_set = SleepStatistics.objects.filter(user=user)
    sleep_record_set = SleepRecord.objects.filter(user=user)

    if not sleep_record_set.exists() and not sleep_statistics_set.exists():
        context = {'html_table_sleep_statistics': None, 'html_table_sleep_record': None}
        return render(request, 'sleep_statistics_show.html', context)

    today = datetime.now().date()

    if not sleep_statistics_set.filter(date=today).exists() and sleep_record_set.filter(sleep_time=today).exists():
        calculate_sleep_statistics(user=user, user_data=user_data)

    data_sleep_statistics = {
        'Дата': [sleep_statistic.date for sleep_statistic in sleep_statistics_set],
        'Продолжительность сна (часы)': [sleep_statistic.sleep_duration for sleep_statistic in sleep_statistics_set],
        'Качество сна (%)': [sleep_statistic.sleep_quality for sleep_statistic in sleep_statistics_set],
        'Сожженные калории во время сна (кк)': [sleep_statistic.calories_burned for sleep_statistic in
                                                sleep_statistics_set],
    }
    recommended_sleep = sleep_statistics_set.latest('date').health_impact

    data_sleep_record = {
        'Дата': [record.sleep_time for record in sleep_record_set],

        'Продолжительность глубокого сна (часы)': [sleep_record.deep_sleep_duration for sleep_record in
                                                   sleep_record_set],
        'Продолжительность лёгкого сна (часы)': [sleep_record.fast_sleep_duration for sleep_record in sleep_record_set],
    }

    df_sleep_statistics = pd.DataFrame(data_sleep_statistics)
    df_sleep_statistics = pd.concat([df_sleep_statistics.tail(10)])
    html_table_sleep_statistics = df_sleep_statistics.to_html(
        classes=["table-bordered", "table-striped", "table-hover"], index=False)

    df_sleep_record = pd.DataFrame(data_sleep_record)
    df_sleep_record = pd.concat([df_sleep_record.tail(10)])

    html_table_sleep_record = df_sleep_record.to_html(classes=["table-bordered", "table-striped", "table-hover"],
                                                      index=False)
    context = {
        'html_table_sleep_statistics': html_table_sleep_statistics,
        'html_table_sleep_record': html_table_sleep_record,
    }

    # Построение графика
    graph_phase = plot_sleep_histograms(sleep_statistics_set)
    graph_duration_quality = plot_sleep_duration_sleep_quality(sleep_statistics_set)
    graph_sleep_deep_fast = plot_sleep_deep_fast(sleep_record_set)
    graph_quality = plot_sleep_quality(sleep_statistics_set)

    context2 = {
        'graph_phase': json.dumps(graph_phase),
        'graph_duration_quality': json.dumps(graph_duration_quality),
        'graph_sleep_deep_fast': json.dumps(graph_sleep_deep_fast),
        'graph_quality': json.dumps(graph_quality),
    }

    return render(request, 'sleep_statistics_show.html', locals())


class CustomPasswordResetView(PasswordResetView):
    template_name = 'system/user_password_reset.html'
    email_template_name = 'system/password_reset_email.html'
    success_url = reverse_lazy('custom_password_reset_done')


class CustomPasswordResetDoneView(TemplateView):
    template_name = 'system/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'system/password_reset_confirm.html'
    success_url = reverse_lazy('custom_password_reset_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'system/password_reset_complete.html'

# taskkill /F /IM celery.exe
