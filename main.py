from fastapi import FastAPI, Request, HTTPException
from linebot import AsyncLineBotApi
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.webhook import WebhookParser
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from openperplex import OpenperplexAsync
from httpx import AsyncClient as AsyncHTTPClient
import google.generativeai as genai

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
async_http_client = AsyncHTTPClient()
line_bot_api = AsyncLineBotApi('eKkMgEbccG7xaNbNrk2V3vMSkvRT2i8rQCbQpMknar4t2k8Vy7bH3oaqAxmjmoCz0EtEVoJAdQWInsrg4Cm/06qBd8kyhmNhb9dAQkqKNYlxsJi6bdy0nEQ8NYkrKnCB8/8ZGH09ny3INKSxt0s2mQdB04t89/1O/w1cDnyilFU=', async_http_client)
parser = WebhookParser('de8adfeffdaf6b8490df64b19079c6b6')

# Gemini still used only for /generate-news
genai.configure(api_key="AIzaSyCIzdW0XY_OBuCJtJ3pgI-nph04tn3-LeM")
model = genai.GenerativeModel("gemini-2.0-flash")

client = OpenperplexAsync(api_key="TezyZ85m68dC0XDMpq_DxKIuXyIFVc_IUvramJ1NKtw")

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
            "รายวัน": "https://www.thairath.co.th",
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
                model="gemini-2.0-flash",
                response_language="th"
            )
            result = response.get("llm_response", "ไม่พบข่าวที่ร้องขอ")
        else:
            result = "กรุณาพิมพ์ชื่อหมวดข่าว เช่น กีฬา, การเมือง, สุขภาพ เป็นต้น"

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
    source_name: str  # Default news source
    language: str   # Default language



@app.post("/generate-news")
async def generate_news(data: NewsRequest):
    today_date = datetime.now().strftime("%d %B %Y")

    # Normalize source name and category
    source = data.source_name.lower()
    category = data.category.strip()
    print(source, category)
    # Source & category URL map
    source_map = {
        "thairath": "https://www.thairath.co.th",
        "sanook": "https://www.sanook.com/",
        "dailynews": "https://www.dailynews.co.th/"
    }

    category_map = {
        "thairath": {
         "รายวัน": "https://www.thairath.co.th",
            "เอนเตอร์เทน": "https://www.thairath.co.th/entertain",
            "กีฬา": "https://www.thairath.co.th/sport",
            "เทคโนโลยี": "https://www.thairath.co.th/lifestyle/tech",
            "การเมือง": "https://www.thairath.co.th/news/politic",
            "การเงิน": "https://www.thairath.co.th/money",
            "สุขภาพ": "https://www.thairath.co.th/lifestyle/health-and-beauty",
            "อาญากรรม": "https://www.thairath.co.th/news/crime",
            "ดูดวง": "https://www.thairath.co.th/horoscope",
            "ท่องเที่ยว": "https://www.thairath.co.th/lifestyle/travel",
             "หวย": "https://www.thairath.co.th/lifestyle/travel",



        },
        "sanook": {
           "เอนเตอร์เทน": "https://www.sanook.com/news/entertain/",
            "กีฬา": "https://www.sanook.com/sport/t",
            "เทคโนโลยี": "https://www.sanook.com/it/",
            "การเมือง": "https://www.sanook.com/news/politic/ ",
            "การเงิน": "https://www.sanook.com/money/ ",
            "สุขภาพ": "https://www.sanook.com/health/",
            "อาญากรรม": "https://www.dailynews.co.th/crime/",
            "ดูดวง": "https://www.sanook.com/horoscope/ ",
            "ท่องเที่ยว": "https://www.sanook.com/travel/",
             "หวย": "https://news.sanook.com/lotto/ ",

        },
        "dailynews": {
             "เอนเตอร์เทน": "https://www.dailynews.co.th/news/news_group/entertainment/",
            "กีฬา": "https://www.dailynews.co.th/sport/",
            "เทคโนโลยี": "https://www.dailynews.co.th/technology/",
            "การเมือง": "https://www.dailynews.co.th/politics/",
            "การเงิน": "https://www.dailynews.co.th/economic/",
            "สุขภาพ": "https://www.dailynews.co.th/article/articles_group/lifestyle/health/",
            "อาญากรรม": "https://www.dailynews.co.th/crime/",
            "ดูดวง": "https://www.dailynews.co.th/horoscope/",
            "ท่องเที่ยว": "https://www.dailynews.co.th/news/news_group/lifestyle/travel-hotel/",
             "หวย": "https://www.dailynews.co.th/lotto/",

        }
    }

    # Get proper URL based on source/category (fallbacks if missing)
    source_urls = category_map.get(source, category_map[source])
    category_url = source_urls.get(category, source_urls[category])

    query = f"""
ขอข่าวที่เป็นกระแสในหมวด '{category}' ประจำวันที่ {today_date}
จำนวน 3 หัวข้อ แบบละเอียด พร้อมสรุปและข้อมูลเชิงลึก
(โปรดใช้ภาษาที่เข้าใจง่าย และบอกแหล่งข่าวด้วย)
"""

    try:
        response = await client.query_from_url(
            url=category_url,
            query=query,
            model="gemini-2.0-flash",
            response_language=data.language
        )

        result = response.get("llm_response", "ไม่พบข้อมูลจากแหล่งข่าวที่กำหนด")

        await line_bot_api.push_message(
            data.user_id,
            TextSendMessage(text=result)
        )
        return {"status": "ok", "message": "News sent!"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
