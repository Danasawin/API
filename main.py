from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from linebot.models import TextSendMessage
from datetime import datetime
from openperplex import OpenPerplex
import json

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# LINE credentials
line_bot_api = LineBotApi('eKkMgEbccG7xaNbNrk2V3vMSkvRT2i8rQCbQpMknar4t2k8Vy7bH3oaqAxmjmoCz0EtEVoJAdQWInsrg4Cm/06qBd8kyhmNhb9dAQkqKNYlxsJi6bdy0nEQ8NYkrKnCB8/8ZGH09ny3INKSxt0s2mQdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('de8adfeffdaf6b8490df64b19079c6b6')

genai.configure(api_key="AIzaSyCIzdW0XY_OBuCJtJ3pgI-nph04tn3-LeM")
model = genai.GenerativeModel("gemini-2.0-flash")


# OpenPerplex API client
client = OpenPerplex(api_key="TezyZ85m68dC0XDMpq_DxKIuXyIFVc_IUvramJ1NKtw")

@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature")
    if signature is None:
        raise HTTPException(status_code=400, detail="Missing X-Line-Signature header")

    body = await request.body()

    try:
        handler.handle(body.decode(), signature)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error handling message: {str(e)}")

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    import asyncio

    async def respond():
        try:
            # Extract text from user message
            user_input = event.message.text.strip().lower()

            # Keyword-to-URL mapping
            url_map = {
                "เอนเตอร์เทน": "https://www.thairath.co.th/entertain",
                "กีฬา": "https://www.thairath.co.th/sport",
                "เทคโนโลยี": "https://www.thairath.co.th/lifestyle/tech",
                "การเมือง": "https://www.thairath.co.th/news/politic",
                "การเงิน": "https://www.thairath.co.th/money",
                "สุขภาพ": "https://www.thairath.co.th/lifestyle/health-and-beauty",

            }

            # Default to homepage if not matched
            matched_url = url_map.get(user_input, "https://www.thairath.co.th")

            today = datetime.now().strftime("%d %B %Y")
            query = f"""
ขอข่าวที่เป็นกระแสในหมวด '{user_input}' ประจำวันที่ {today}
จำนวน 3 หัวข้อ แบบละเอียด พร้อมสรุปและข้อมูลเชิงลึก
(โปรดใช้ภาษาที่เข้าใจง่าย และแสดงแหล่งอ้างอิงด้วย)
"""

            response = await client.query_from_url(
                url=matched_url,
                query=query,
                model='gemini-2.0-flash',
                response_language="th",
            )

            news = response.get('llm_response', 'ไม่พบข่าวที่ร้องขอ')

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=news)
            )

        except Exception as e:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"เกิดข้อผิดพลาด: {str(e)}")
            )

    asyncio.run(respond(event))



class NewsRequest(BaseModel):
    user_id: str
    category: str
    voice: str
    news_type: str

@app.post("/generate-news")
async def generate_news(data: NewsRequest):
    today_date = datetime.now().strftime("%d %B %Y")
    prompt = f"""
🧑‍💼 คุณคือผู้สื่อข่าวมืออาชีพ

🗂️ หัวข้อข่าว: "{data.category}"  
🎙️ น้ำเสียงที่ต้องการ: {data.voice}  
📝 รูปแบบการรายงาน: {data.news_type}
📅 **กรุณาจัดทำข่าวเฉพาะในวันนี้ ({today_date}) เท่านั้น**

โปรดจัดทำรายงานข่าวในรูปแบบที่เหมาะสมกับการส่งผ่าน LINE โดยใช้การจัดรูปแบบด้วยอีโมจิและสัญลักษณ์ เพื่อให้อ่านง่าย:

📰 หัวข้อข่าว: (ใช้พาดหัวข่าวที่น่าสนใจ)

✏️ สรุป:
- สรุปเนื้อหาสั้น ๆ กระชับ ชัดเจน

🔍 รายละเอียด:
- ข้อเท็จจริงที่เกี่ยวข้อง
- เพิ่มข้อมูลเชิงลึกที่น่าสนใจ

🎯 น้ำเสียงที่ใช้: {data.voice}

❗ โปรดเขียนในภาษาที่เข้าใจง่ายสำหรับผู้อ่านทั่วไป และไม่ต้องใส่ Markdown หรือ HTML
📰 แหล่งที่มา: [ชื่อแหล่งที่มา เช่น เว็บไซต์ข่าว X]
"""


    try:
        response = model.generate_content(prompt)
        reply_text = response.text.strip()

        # Push message to the user
        line_bot_api.push_message(data.user_id, TextSendMessage(text=reply_text))
        return {"status": "ok", "message": "News sent!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))