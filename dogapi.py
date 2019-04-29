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
        sessionStorage[user_id] = {}
        res['response']['text'] = 'Привет! Это игра-угадайка! В ней Вам нужно по картинке угадать породу собаки!' \
            ' Для некоторых она может показаться скучной, но знатоки, наверное, оценят. Хотите ли Вы сыграть?'
        rollback(user_id)
        return
    if sessionStorage[user_id]['ask']:
        for disagree in disagree_list:
            if disagree in user_answer:
                res['response']['end_session'] = True
                break
        for agree in agree_list:
            if agree in user_answer:
                sessionStorage[user_id]['ask'] = False
                break
        if res['response']['end_session']:
            res['response']['text'] = 'Ну, как говорится, на нет и суда нет!'
            return
    if sessionStorage[user_id]['run']:
        if 'сдаюсь' in user_answer:
            res['response']['text'] = 'Как же так? Это - {}. Хотите еще?'.format(sessionStorage[user_id]['correct'])
            rollback(user_id)
            return
        elif sessionStorage[user_id]['correct'].lower() in user_answer:
            rollback(user_id)
            res['response']['text'] = 'А Вы умны! Хотите еще?'
            return
        else:
            res['response']['text'] = 'Вы не правы! Сдаётесь?'
            res['response']['buttons'] = [{'title': 'Сдаюсь!', 'hide': True}]
            return
    if res['response']['end_session']:
        res['response']['text'] = 'Ну, как говорится, на нет и суда нет!'
        return
    if not sessionStorage[user_id]['ask']:
        choose_dog(user_id, res)
        return
    res['response']['text'] = 'Используйте словечки попроще, молодой человек!'


def choose_dog(user_id, res):
    dogs_list = eval(requests.get('https://dog.ceo/api/breed/hound/images').text)['message']
    dog = random.choice(dogs_list)
    params = {
            "key": "trnsl.1.1.20190414T112030Z.8a0d166f1b7aa090.7f11eb566d7db267d90914cf4a747455ccd6c4cd",
            "text": dog.split('/')[4],
            "lang": "ru",
            "format": 'plain'
        }
    sessionStorage[user_id]['correct'] = requests.get("https://translate.yandex.net/api/v1.5/tr.json/translate", params=params).json()['text'][0]
    sessionStorage[user_id]['run'] = True
    url = 'https://dialogs.yandex.net/api/v1/skills/93adceb8-c5bd-4195-8232-e0f17d410cb4/images'
    headers = {"Content-Type": "application/json",
               "Authorization": "OAuth AQAAAAArjWblAAT7o-lEl6h0I0Scq1-e2HViM3w"}
    image = requests.post(url, headers=headers, data=json.dumps({"url": dog}))
    json_data = json.loads(image.text)
    res['response']['card'] = {}
    res['response']['card']['type'] = 'BigImage'
    res['response']['card']['title'] = 'Тогда угадайте-ка тогда вот эту породу, многоуважаемый знаток!'
    res['response']['card']['image_id'] = json_data['image']['id']
    res['response']['text'] = 'Ну, давайте!'


def rollback(user_id):
    sessionStorage[user_id]['ask'] = True
    sessionStorage[user_id]['correct'] = False
    sessionStorage[user_id]['run'] = False


if __name__ == '__main__':
    app.run()
