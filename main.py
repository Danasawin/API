from fastapi import FastAPI, Request, HTTPException
from linebot import AsyncLineBotApi
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.webhook import WebhookParser
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from openperplex import OpenperplexAsync
from httpx import AsyncClient as AsyncHTTPClient
import re

def clean_and_add_emojis(text: str) -> str:
    # Remove asterisks
    text = text.replace("*", "")

    # Add emojis for sections
    text = re.sub(r"(ข่าวที่ \d+)", r"📰 \1", text)
    text = re.sub(r"(หัวข้อ:)", r"🗞️ \1", text)
    text = re.sub(r"(สรุป:)", r"🧠 \1", text)
    text = re.sub(r"(แหล่งข่าว:)", r"📌 \1", text)

    return text

# Inside your generate_news function after getting the response


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
line_bot_api = AsyncLineBotApi('YOUR_LINE_ACCESS_TOKEN', async_http_client)
parser = WebhookParser('YOUR_LINE_CHANNEL_SECRET')
client = OpenperplexAsync(api_key="YOUR_OPENPERPLEX_API_KEY")

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
            "รายวัน": "https://www.thairath.co.th/home",
            "เอนเตอร์เทน": "https://www.thairath.co.th/entertain",
            "กีฬา": "https://www.thairath.co.th/sport",
            "เทคโนโลยี": "https://www.thairath.co.th/lifestyle/tech",
            "การเมือง": "https://www.thairath.co.th/news/politic",
            "การเงิน": "https://www.thairath.co.th/money",
            "สุขภาพ": "https://www.thairath.co.th/lifestyle/health-and-beauty",
        }

        if user_input in url_map:
            # ส่งข้อความแจ้งว่ากำลังโหลดก่อน
        


            url = url_map[user_input]
            today = datetime.now().strftime("%d %B %Y")
            query = f"""
ขอข่าวที่เป็นกระแสในหมวด '{user_input}' ประจำวันที่ {today}
จำนวน 3 หัวข้อ แบบละเอียด พร้อมสรุปและข้อมูลเชิงลึก หากไม่พบให้เอาข่าวอะไรมาก็ได้จาก url
(โปรดใช้ภาษาที่เข้าใจง่าย และแสดงแหล่งอ้างอิงด้วย)
"""
            response = await client.query_from_url(
                url=url,
                query=query,
                model="gemini-2.0-flash",
                response_language="th"
            )
            result = response.get("llm_response", "ไม่พบข่าวที่ร้องขอ")
            result = clean_and_add_emojis(result)

            # ส่งข่าวจริงทีหลัง
            await line_bot_api.push_message(
                event.source.user_id,
                TextSendMessage(text=result)
            )

        else:
            # ตอบกลับทันทีถ้าไม่มีหมวดหมู่ที่ถูกต้อง
            await line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="กรุณาพิมพ์ชื่อหมวดข่าว เช่น กีฬา, การเมือง, สุขภาพ เป็นต้น")
            )

    except Exception as e:
        await line_bot_api.push_message(
            event.source.user_id,
            TextSendMessage(text=f"เกิดข้อผิดพลาด: {str(e)}")
        )


class NewsRequest(BaseModel):
    user_id: str
    category: str
    source: str  
    language: str   



@app.post("/generate-news")
async def generate_news(data: NewsRequest):
    today_date = datetime.now().strftime("%d %B %Y")

    # Normalize source name and category
    source = data.source.lower()
    category = data.category.strip()
    language = data.language.strip()

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

      # Get the category URL
    source_categories = category_map.get(source)
    if not source_categories:
        raise HTTPException(status_code=400, detail="ไม่พบแหล่งข่าวที่กำหนด")

    category_url = source_categories.get(category)
    if not category_url:
        raise HTTPException(status_code=400, detail="ไม่พบหมวดหมู่ข่าวที่กำหนด")
    

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
            response_language=language
        )

        result = response.get("llm_response", "ไม่พบข้อมูลจากแหล่งข่าวที่กำหนด")
        result = clean_and_add_emojis(result)

        await line_bot_api.push_message(
            data.user_id,
            TextSendMessage(text=result)
        )
        return {"status": "ok", "message": "News sent!"}

    except Exception as e:
        await line_bot_api.push_message(
            data.user_id,
            TextSendMessage(text=f"❌ เกิดข้อผิดพลาด: {str(e)}")
        )
        raise HTTPException(status_code=500, detail=str(e))
