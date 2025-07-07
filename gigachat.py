import requests
from dotenv import load_dotenv, find_dotenv
import os
import json
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv(find_dotenv())


def get_access_token() -> str:
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

    payload = {
        'scope': 'GIGACHAT_API_PERS'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'RqUID': 'b38759ba-e5a6-4385-b920-bb41913576be',
        'Authorization': f'Basic N2JmODVkYWMtZTRiZi00YjE5LTgzMGItMGIwNThjNjRiOTdhOmJhNjAxNjhmLTdmMjQtNDdhZC05NDIwLWQ0YWE4N2I3Yzk2Yg=='
    }

    response = requests.request("POST", url, headers=headers, data=payload, verify=False)
    return response.json()["access_token"]


def get_answer():
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    access_token = get_access_token()

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    body = {
        "model": "GigaChat",
        "messages": [
            {"role": "system",
             "content": "Ты — эксперт по сну (сомнолог), твоя задача дать краткую рекомендацию пользователю на основе показателей, которые он прислал."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "top_p": 0.9,
        "n": 1,
        "stream": False
    }

    response = requests.request("POST", url, headers=headers, data=json.dumps(body), verify=False)
    response.raise_for_status()  # Проверка на ошибки HTTP

    return response.json()["choices"][0]["message"]["content"]


# Пример данных пользователя
prompt = (
    'Мне 21 лет, мужчина, вес 65 кг, рост 182 см. Мои показатели: "sleep_rem_duration":0,"version":2,"timezone":12,"has_rem":false,"items":[{"end_time":1750727640,"start_time":1750725900,"state":3},{"end_time":1750727940,"start_time":1750727640,"state":2},{"end_time":1750728600,"start_time":1750727940,"state":3},{"end_time":1750729500,"start_time":1750728600,"state":2},{"end_time":1750731120,"start_time":1750729500,"state":3},{"end_time":1750732140,"start_time":1750731120,"state":2},{"end_time":1750733760,"start_time":1750732140,"state":3},{"end_time":1750734000,"start_time":1750733760,"state":2},{"end_time":1750735860,"start_time":1750734000,"state":5},{"end_time":1750738380,"start_time":1750735860,"state":3},{"end_time":1750738800,"start_time":1750738380,"state":2},{"end_time":1750739880,"start_time":1750738800,"state":3},{"end_time":1750740360,"start_time":1750739880,"state":2},{"end_time":1750743360,"start_time":1750740360,"state":3},{"end_time":1750743900,"start_time":1750743360,"state":2},{"end_time":1750745340,"start_time":1750743900,"state":3},{"end_time":1750746120,"start_time":1750745340,"state":2},{"end_time":1750747080,"start_time":1750746120,"state":5},{"end_time":1750747440,"start_time":1750747080,"state":2},{"end_time":1750752060,"start_time":1750747440,"state":3}],"min_hr":47,"device_bedtime":1750725900,"sleep_deep_duration":84,"wake_up_time":1750752060,"bedtime":1750725900,"awake_count":2,"duration":389,"max_hr":95,"sleep_awake_duration":47,"avg_hr":60,"has_stage":true,"sleep_light_duration":305,"device_wake_up_time":1750752060'
)


answer = get_answer()
print("Ответ GigaChat:\n", answer)
