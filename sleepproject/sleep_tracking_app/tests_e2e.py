from datetime import date
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import json


class E2ETests(TestCase):
    def test_register_login_add_sleep_and_view_statistics(self):
        """
        E2E тест: регистрация нового пользователя, логин, добавление записи сна и просмотр страницы статистики.
        """
        username = 'e2euser'
        password = 'E2E-pass-123'
        # регистрация (POST на view 'register')
        reg_url = reverse('register')
        dob = date.today().isoformat()
        data = {
            'username': username,
            'first_name': 'E2E',
            'last_name': 'User',
            'email': 'e2e@example.test',
            'password1': password,
            'password2': password,
            'date_of_birth': dob,
            'weight': '70',
            'gender': '1',
            'height': '175',
            'active': '',
        }
        resp = self.client.post(reg_url, data)
        # ожидаем редирект на home
        self.assertIn(resp.status_code, (302, 301))

        # логинимся через client
        logged = self.client.login(username=username, password=password)
        self.assertTrue(logged)

        # загружаем CSV-файл через view 'sleep_records_from_csv'
        csv_url = reverse('sleep_records_from_csv')

        # Собираем минимально валидный CSV по формату Key,Time,Value
        # Value для сна — JSON с version=2, has_stage=True, items и метаданными
        device_bedtime = 1700000000
        device_wake = device_bedtime + 8 * 3600
        sleep_json = {
            'version': 2,
            'has_stage': True,
            'device_bedtime': device_bedtime,
            'device_wake_up_time': device_wake,
            'sleep_deep_duration': 120,
            'sleep_light_duration': 300,
            'sleep_rem_duration': 30,
            'awake_count': 1,
            'items': [
                {'start_time': device_bedtime, 'end_time': device_bedtime + 1800, 'state': 2},
                {'start_time': device_bedtime + 1800, 'end_time': device_bedtime + 5400, 'state': 3},
                {'start_time': device_bedtime + 5400, 'end_time': device_bedtime + 6000, 'state': 4},
            ]
        }

        heart_json = {'time': device_bedtime + 1000, 'bpm': 60}

        rows = [
            ['sleep', str(device_bedtime), json.dumps(sleep_json)],
            ['heart_rate', str(device_bedtime + 1000), json.dumps(heart_json)],
        ]

        csv_lines = ['Key,Time,Value'] + [','.join([r[0], r[1], '"' + r[2].replace('"', '""') + '"']) for r in rows]
        csv_content = '\n'.join(csv_lines).encode('utf-8')

        uploaded = SimpleUploadedFile('data.csv', csv_content, content_type='text/csv')
        resp2 = self.client.post(csv_url, {'csv_file': uploaded}, format='multipart')
        self.assertEqual(resp2.status_code, 200)
        data = resp2.json()
        self.assertIn('task_id', data)

        # получаем страницу статистики
        stats_url = reverse('sleep_statistics_show')
        resp3 = self.client.get(stats_url)
        self.assertEqual(resp3.status_code, 200)
        # проверяем, что шаблон с метриками отрендерен — либо через context, либо по содержимому HTML
        if resp3.context is not None:
            self.assertTrue('metric' in resp3.context or 'plot_data' in resp3.context)
        else:
            content = resp3.content.decode('utf-8')
            # проверяем наличие ключевых фраз из шаблона
            self.assertTrue(
                'Мы советуем' in content or 'Столько вы спали' in content or 'Статистика сна' in content
            )
