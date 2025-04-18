from fastapi import FastAPI, Request, Response, HTTPException
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
import base64
import hashlib
import hmac
from linebot import LineBotApi, WebhookHandler
app = FastAPI()

line_bot_api = LineBotApi('UmJLwtX2GPLFyATOW8wF7t1vxlbwifazDxVlz0VnFZFGlJykK/1LusDXRDWIFBkK8ZtPrdjWray3Nwh1tY6z/D3+Rq4Q9JLjjtdNZ62bII+OJ4CMMaEFZzXBe32MLa9kutOYFRvmzq/cz3sNurzCDAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('1c6f587d59c7c2767657fc02a2b3649b')

@app.get('/hello')
def hello_word():
    return {"hello" : "world"}

@app.post("/message")
async def hello_word(request: Request):
    # Step 1: Read the incoming request body
    body = await request.body()
    
    # Step 2: Log the raw body for debugging purposes
    print("Request body:", body)
    
    # Step 3: Extract the signature and verify it
    signature = request.headers.get('X-Line-Signature')
    if not signature:
        raise HTTPException(status_code=400, detail="X-Line-Signature header missing")

    # Step 4: Verify the signature
    hash = hmac.new(
        '1c6f587d59c7c2767657fc02a2b3649b'.encode('utf-8'),
        body,
        hashlib.sha256
    ).digest()
    
    if signature != base64.b64encode(hash).decode():
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Step 5: Process the event using the handler
    handler.handle(body)
    return {"message": "success"}

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