from fastapi import FastAPI, Request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai
app = FastAPI()

# LINE credentials
line_bot_api = LineBotApi('eKkMgEbccG7xaNbNrk2V3vMSkvRT2i8rQCbQpMknar4t2k8Vy7bH3oaqAxmjmoCz0EtEVoJAdQWInsrg4Cm/06qBd8kyhmNhb9dAQkqKNYlxsJi6bdy0nEQ8NYkrKnCB8/8ZGH09ny3INKSxt0s2mQdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('de8adfeffdaf6b8490df64b19079c6b6')

genai.configure(api_key="AIzaSyAGtp85h9udWVfkffHB5Kmuja3sivhP-Os")
model = genai.GenerativeModel('gemini-2.0-flash')

@app.get("/hello")
def hello_world():
    return {"hello": "world"}


@app.post("/message")
async def message(request: Request):
    signature = request.headers.get("X-Line-Signature")
    if not signature:
        return {"error": "X-Line-Signature header missing"}

    body = await request.body()
    print("Request body:", body.decode("utf-8"))

    try:
        handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        return {"error": "Invalid signature"}
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return {"error": "Internal server error"}

    return {"message": "OK"}


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.mode != "active":
        print("Standby mode: cannot reply to message.")
        return

    user_message = event.message.text

    if user_message == "สวัสดี":
        send_message(event, "สวัสดีชาวโลก")
    else:
        try:
            # Send user's message to Gemini and get response
            response = model.generate_content(user_message)
            gemini_reply = response.text
        except Exception as e:
            print(f"Gemini error: {e}")
            gemini_reply = "ขออภัย เกิดข้อผิดพลาดในการประมวลผลข้อมูล"

        send_message(event, gemini_reply)

def send_message(event, message):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=message)
    )
