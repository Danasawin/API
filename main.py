from fastapi import FastAPI, Request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai

app = FastAPI()

# LINE credentials
line_bot_api = LineBotApi('eKkMgEbccG7xaNbNrk2V3vMSkvRT2i8rQCbQpMknar4t2k8Vy7bH3oaqAxmjmoCz0EtEVoJAdQWInsrg4Cm/06qBd8kyhmNhb9dAQkqKNYlxsJi6bdy0nEQ8NYkrKnCB8/8ZGH09ny3INKSxt0s2mQdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('de8adfeffdaf6b8490df64b19079c6b6')

genai.configure(api_key="AIzaSyCIzdW0XY_OBuCJtJ3pgI-nph04tn3-LeM")
model = genai.GenerativeModel("gemini-2.0-flash")

@app.post("/callback")
async def callback(request: Request):
    body = await request.body()
    signature = request.headers["X-Line-Signature"]
    handler.handle(body.decode(), signature)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    # Example: extract news settings from message
    prompt = f"""
    You are a news reporter. Respond to this request:
    "{user_message}"

    Format your answer with:
    - Appropriate news content
    - Requested tone and style
    """

    response = model.generate_content(prompt)
    reply_text = response.text.strip()

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )