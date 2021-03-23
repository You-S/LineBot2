from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
import os

app = Flask(__name__)

#環境変数取得
YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

@app.route("/")
def test():
    return "OK"

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    carName = event.message.text
    result = '\n'.join(check(carName))
    if result == '':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text='見つかりませんでした'))
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=result))

def check(carName):
    import requests
    from bs4 import BeautifulSoup
    import re

    url = 'https://cp.toyota.jp/rentacar/?padid=ag270_fr_sptop_onewayma'
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')

    bookList = []
    cont_count = 1
    carLists = soup.find('ul', attrs={'id': 'service-items-shop-type-start'})
    carLists = carLists.find_all('li', attrs={'class': 'service-item'})
    for carList in carLists:
        if carList.find('div', attrs={'class': 'show-entry-end'}) is None:
            search = re.compile('^' + carName)
            al = carList.find(text=search)
            if al is not None:
                carList1 = carList.find_all('p')
                carList2 = carList.find('div', attrs={'class': 'service-item__reserve-tel'})
                content2 = carList2.text.replace('\n', '').replace(' ', '').replace('\u3000', ' ')
                car = []
                for content in carList1:
                    content = content.text.replace('\n', '').replace(' ', '').replace('\u3000', ' ')
                    if content != '':
                        car.append(content)
                car.append(content2)
                sList = ''
                for i in range(0,12,2):
                    info = car[i]
                    cont = car[i+1]
                    sList = sList + info + ':' + cont + '\n'
                sList = '\n' + str(cont_count) + '件目\n' + sList
                cont_count += 1
                bookList.append(sList)
    return bookList    
    
if __name__ == "__main__":
    port = int(os.getenv("PORT"))
    app.run(host="0.0.0.0", port=port)