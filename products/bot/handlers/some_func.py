# Выгрузка json(patterns)
import json
import os


def json_loader(key: str = None) -> [dict, list]:
    try:
        current_path = os.path.abspath(os.getcwd())
        json_file_path = os.path.join(current_path, '.json')
        with open(json_file_path, 'r', encoding='utf-8') as file:
            templates = json.load(file)
            if key:
                return templates[key].values()
            else:
                return templates
    except Exception as e:
        print(Exception, e)


def get_image(input_file):
    try:
        with open(input_file, 'rb') as photo:
            return photo.read()
    except Exception as e:
        print(Exception, e)
