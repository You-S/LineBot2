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

app = Flask(__name__)

line_bot_api = LineBotApi('FJGm2w50XY4NIb9bKTro/iq6T9dsjiHsawT3xzcwYqVdxhS9m/d3kEkrNXWrPB5Xq1miYvnJ3RN1/LXLcvF6Lro9+GbAMUa4lhp8Lr06ouTvH1NtFAX9DQC8e+t6AabKg0X5iE9ttaCyLBQ4sSlhmAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('523f0657d22c322bba73ac17817f366c')


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
    app.run()