import requests
from config import api_key


def geolocators(latitude, longitude):
    url = f"https://geocode-maps.yandex.ru/1.x/?apikey={api_key}&geocode={longitude},{latitude}&format=json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        address = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty'][
            'GeocoderMetaData']['text']
        return address
    else:
        return f'Не удалось расшифровать адрес по координатам {latitude, longitude}'
