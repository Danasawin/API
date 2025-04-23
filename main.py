from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from openperplex import OpenperplexAsync
import google.generativeai as genai
import asyncio

app = FastAPI()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LINE & Gemini setup
line_bot_api = LineBotApi('YOUR_LINE_CHANNEL_ACCESS_TOKEN')
handler = WebhookHandler('YOUR_LINE_CHANNEL_SECRET')

genai.configure(api_key="YOUR_GOOGLE_API_KEY")
model = genai.GenerativeModel("gemini-2.0-flash")
client = OpenperplexAsync(api_key="YOUR_OPENPERPLEX_API_KEY")

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
    asyncio.create_task(process_message(event))

async def process_message(event: MessageEvent):
    try:
        user_input = event.message.text.strip().lower()

        # Keyword-based auto-news from ThaiRath
        url_map = {
            "เอนเตอร์เทน": "https://www.thairath.co.th/entertain",
            "กีฬา": "https://www.thairath.co.th/sport",
            "เทคโนโลยี": "https://www.thairath.co.th/lifestyle/tech",
            "การเมือง": "https://www.thairath.co.th/news/politic",
            "การเงิน": "https://www.thairath.co.th/money",
            "สุขภาพ": "https://www.thairath.co.th/lifestyle/health-and-beauty",
        }

        if user_input in url_map:
            url = url_map[user_input]
            today = datetime.now().strftime("%d %B %Y")
            query = f"""
ขอข่าวที่เป็นกระแสในหมวด '{user_input}' ประจำวันที่ {today}
จำนวน 3 หัวข้อ แบบละเอียด พร้อมสรุปและข้อมูลเชิงลึก
(โปรดใช้ภาษาที่เข้าใจง่าย และแสดงแหล่งอ้างอิงด้วย)
"""

            response = await client.query_from_url(
                url=url,
                query=query,
                model='gemini-2.0-flash',
                response_language="th"
            )
            result = response.get("llm_response", "ไม่พบข่าวที่ร้องขอ")
        else:
            # Fallback to generative prompt based on free text
            prompt = f"""
คุณคือผู้สื่อข่าวมืออาชีพ

กรุณาจัดทำรายงานข่าวจากหัวข้อต่อไปนี้:
"{event.message.text}"

รูปแบบข่าวที่ต้องการ:
- พาดหัวข่าวที่ชัดเจนและน่าสนใจ
- สรุปเนื้อหาข่าวแบบกระชับ
- รายละเอียดประกอบที่เกี่ยวข้องและเป็นข้อเท็จจริง
- ใช้น้ำเสียงแบบเป็นกลางและมืออาชีพ
"""
            gemini_response = model.generate_content(prompt)
            result = gemini_response.text.strip()

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=result)
        )

    except Exception as e:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"เกิดข้อผิดพลาด: {str(e)}")
        )

# For POST API from your frontend
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
        line_bot_api.push_message(data.user_id, TextSendMessage(text=reply_text))
        return {"status": "ok", "message": "News sent!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
