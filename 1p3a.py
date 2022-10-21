import os
import sys
import re
import random
import urllib.parse
import requests


API_HOST = 'api.1point3acres.com'


def do_checkin(headers: dict) -> str:
    with requests.Session() as session:

        with session.get(url=f'https://{API_HOST}/api/users/checkin', headers=headers) as r:
            emotion = {
                'qdxq': random.choice(r.json()['emotion'])['qdxq'],
                'todaysay': ''.join(chr(random.randint(0x4E00, 0x9FBF)) for _ in range(random.randint(5, 10))),
            }
            print('emotion for today:', emotion)

        with session.post(url=f'https://{API_HOST}/api/users/checkin', headers=headers, json=emotion) as r:
            return r.json()['msg']


def do_daily_questions(headers: dict) -> str:
    def find_answer_id(question: dict) -> int:
        ans = requests.get(url='https://raw.githubusercontent.com/xjasonlyu/1point3acres/main/questions.json')\
            .json()\
            .get(question['qc'])
        for k, v in question.items():
            if not re.match(r'^a\d$', k):
                continue
            if ans == v:
                return int(k[1])
        return 0

    def compose_ans(question: dict) -> dict:
        return {
            'qid': question['id'],
            'answer': find_answer_id(question),
        }

    with requests.Session() as session:

        with session.get(url=f'https://{API_HOST}/api/daily_questions', headers=headers) as r:
            ans = compose_ans(r.json()['question'])
            if not ans['answer']:
                return '未找到匹配答案，请手动答题'
            print('answer for today:', ans)

        with session.post(url=f'https://{API_HOST}/api/daily_questions', headers=headers, json=ans) as r:
            return r.json()['msg']



def push_notification(title: str, content: str) -> None:
    alertURL = os.getenv('ALERT_URL','')
    alertURL = alertURL.replace(r'{{title}}',   urllib.parse.quote(title))
    alertURL = alertURL.replace(r'{{content}}', urllib.parse.quote(content))

    try:
        _ = requests.get(alertURL)
    except Exception as e:
        print(f'failed to notify: {e}')


def main(do):

    try:
        headers = {
            "Host": API_HOST,
            "device-id": os.getenv('DEVICE_ID',''),
            "authorization": os.getenv('AUTH',''),
            "content-type": 'application/json',
            "User-Agent": 'okhttp/3.14.9',
            "Accept-Encoding": 'gzip',
        }
        message_text = do(headers)
    except Exception as e:
        message_text = str(e)

    # log to output
    print('resp: %s' % message_text)

    # telegram notify
    push_notification(f'1Point3Acres {do.__name__}', message_text)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        # do all
        main(do_checkin)
        main(do_daily_questions)
    elif sys.argv[1] in ('1', 'checkin'):
        main(do_checkin)
    elif sys.argv[1] in ('2', 'question'):
        main(do_daily_questions)
    else:
        print("unknown command")
