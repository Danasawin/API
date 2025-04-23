from fastapi import FastAPI, Request, HTTPException
from linebot import AsyncLineBotApi
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.webhook import WebhookParser
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import google.generativeai as genai
import os
from dotenv import load_dotenv
from openperplex import OpenperplexAsync
from aiohttp import ClientSession
from linebot.exceptions import LineBotApiError

# Load environment variables
load_dotenv()

async def create_line_bot_api():
    session = ClientSession()
    line_bot_api = AsyncLineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"), async_http_client=session)
    return line_bot_api
# Initialize FastAPI app
app = FastAPI()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LINE & OpenPerplex setup
line_bot_api = AsyncLineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
parser = WebhookParser(os.getenv("LINE_CHANNEL_SECRET"))

# Gemini setup
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

# OpenPerplex setup
client = OpenperplexAsync(api_key=os.getenv("OPENPERPLEX_API_KEY"))

@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing X-Line-Signature header")

    body = await request.body()
    body_text = body.decode("utf-8")

    try:
        events = parser.parse(body_text, signature)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Parse error: {str(e)}")

    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
            await handle_keyword_news(event)

    return "OK"

async def handle_keyword_news(event: MessageEvent):
    try:
        user_input = event.message.text.strip().lower()

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
            # Query the OpenPerplex API
            response = await client.query_from_url(
                url=url,
                query=query,
                model="gemini-2.0-flash",
                response_language="th"
            )
            result = response.get("llm_response", "ไม่พบข่าวที่ร้องขอ")
        else:
            result = "กรุณาพิมพ์ชื่อหมวดข่าว เช่น กีฬา, การเมือง, สุขภาพ เป็นต้น"

        # Send reply back to the user on LINE
        await line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=result)
        )

    except Exception as e:
        await line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"เกิดข้อผิดพลาด: {str(e)}")
        )

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
        # Requesting Gemini to generate content
        response = model.generate_content(prompt)
        reply_text = response.text.strip()
        
        # Sending generated news to the user on LINE
        await line_bot_api.push_message(data.user_id, TextSendMessage(text=reply_text))
        return {"status": "ok", "message": "News sent!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating news: {str(e)}")
