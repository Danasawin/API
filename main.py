from fastapi import FastAPI, Request, Response
from typing import Optional
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = FastAPI()

line_bot_api = LineBotApi('UmJLwtX2GPLFyATOW8wF7t1vxlbwifazDxVlz0VnFZFGlJykK/1LusDXRDWIFBkK8ZtPrdjWray3Nwh1tY6z/D3+Rq4Q9JLjjtdNZ62bII+OJ4CMMaEFZzXBe32MLa9kutOYFRvmzq/cz3sNurzCDAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('1c6f587d59c7c2767657fc02a2b3649b')

@app.get('/hello')
def hello_word():
    return {"hello" : "world"}

@app.post('/message')
async def hello_word(request: Request):
    signature = request.headers['X-Line-Signature']
    body = await request.body()
    
    try:
      handler.handle(body.decode('UTF-8'), signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
        if event.message.text == 'สวัสดี' : 
            sendMessage(event,"สวัสดีชาวโลก")
        else:
            echo(event)
    
def echo(event):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=event.message.text))
        
def sendMessage(event,message):
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=message))