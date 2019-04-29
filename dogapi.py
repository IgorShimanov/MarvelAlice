import requests
import random
import json
from flask import request, Flask
from dbase import agree_list, disagree_list


app = Flask(__name__)


sessionStorage = {}


@app.route('/post', methods=['POST'])
def main():
    response = {
        'session': request.json['session'],
        'version': request.json['version'],
        'response': {
            'end_session': False
        }
    }

    handle_dialog(request.json, response)

    return json.dumps(response)


def handle_dialog(req, res):
    user_id = req['session']['user_id']
    user_answer = req['request']['original_utterance'].lower()
    if req['session']['new']:
        res['response']['text'] = 'Привет! Это игра-угадайка! В ней Вам нужно по картинке угадать породу собаки!' \
            ' Для некоторых она может показаться скучной, но знатоки, наверное, оценят. Хотите ли Вы сыграть?'
        rollback(user_answer)
        return
    if sessionStorage[user_id]['ask']:
        for disagree in disagree_list:
            if disagree in user_answer:
                res['response']['end_session'] = True
                break
        for agree in agree_list:
            if agree in user_answer:
                sessionStorage[user_id]['ask'] = False
                res['response']['end_session'] = False
                break
        if res['response']['end_session']:
            res['response']['text'] = 'Ну, как говорится, на нет и суда нет!'
            return
    if not sessionStorage[user_id]['ask']:
        choose_dog(user_id, res)
        return
    if res['response']['end_session']:
        res['response']['text'] = 'Ну, как говорится, на нет и суда нет!'
        return
    if sessionStorage[user_id]['run']:
        if 'сдаюсь' in user_answer:
            rollback(user_answer)
            res['response']['text'] = 'Как же так? Это - {}. Хотите еще?'.format(sessionStorage[user_id]['correct'])
            return
        elif user_answer == sessionStorage[user_id]['correct']:
            rollback(user_answer)
            res['response']['text'] = 'А Вы умны! Хотите еще?'
            return
        else:
            res['response']['text'] = 'Вы не правы! Сдаётесь?'
            res['response']['buttons'] = [{'title': 'Сдаюсь!', 'hide': True}]
            return


def choose_dog(user_id, res):
    dogs_list = eval(requests.get('https://dog.ceo/api/breed/hound/images').text)['message']
    dog = random.choice(dogs_list)
    sessionStorage[user_id]['correct'] = dog.split('/')[4]
    sessionStorage[user_id]['run'] = True
    res['response']['card'] = {}
    res['response']['card']['type'] = 'BigImage'
    url = 'https://dialogs.yandex.net/api/v1/skills/7a429ccd-662e-464e-a30e-b529594302b9/images'
    headers = {"Content-Type": "application/json",
               "Authorization": "OAuth AQAAAAAa43A_AAT7owWbfTkp80EDhFzcpgs_AHs"}
    data = {"url": dog}
    image = requests.post(url, headers=headers, data=json.dumps(data))
    json_data = json.loads(image.text)
    res['response']['card']['title'] = 'Тогда угадайте-ка тогда вот эту породу, многоуважаемый знаток!'
    res['response']['card']['image_id'] = json_data['image']['id']


def rollback(user_id):
    sessionStorage[user_id]['ask'] = True
    sessionStorage[user_id]['correct'] = False
    sessionStorage[user_id]['run'] = False


if __name__ == '__main__':
    app.run()
