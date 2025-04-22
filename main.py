from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from linebot.models import TextSendMessage
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
    user_message = event.message.text

    # Example: extract news settings from message
    prompt = f"""
คุณคือผู้สื่อข่าวมืออาชีพ 📰

กรุณาจัดทำรายงานข่าวจากหัวข้อต่อไปนี้:
🗂️ หัวข้อ: "{user_message}"

กรุณาจัดทำรายงานข่าวตามรูปแบบด้านล่างนี้ โดยใช้ภาษาที่เหมาะสมกับการสื่อสารผ่าน LINE (ไม่ใช้ Markdown หรือ HTML):

📌 โครงสร้างที่ต้องการ:

🧲 พาดหัวข่าว:
- เขียนให้ชัดเจน ดึงดูดความสนใจ

📝 สรุปข่าว:
- อธิบายเนื้อหาอย่างกระชับ เข้าใจง่าย

🔍 รายละเอียดเพิ่มเติม:
- ข้อมูลประกอบที่เป็นข้อเท็จจริง และเกี่ยวข้องกับหัวข้อ

🤝 น้ำเสียง:
- ใช้ภาษาที่เป็นกลาง มืออาชีพ อ่านง่ายสำหรับผู้อ่านทั่วไป

📢 จุดประสงค์:
- ทำให้ผู้อ่านเข้าใจข่าวสารได้รวดเร็วและครบถ้วน โดยไม่ใช้รูปแบบ Markdown
"""



    response = model.generate_content(prompt)
    reply_text = response.text.strip()

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )



class NewsRequest(BaseModel):
    user_id: str
    category: str
    voice: str
    news_type: str

@app.post("/generate-news")
async def generate_news(data: NewsRequest):
    prompt = f"""
🧑‍💼 คุณคือผู้สื่อข่าวมืออาชีพ

🗂️ หัวข้อข่าว: "{data.category}"  
🎙️ น้ำเสียงที่ต้องการ: {data.voice}  
📝 รูปแบบการรายงาน: {data.news_type}

โปรดจัดทำรายงานข่าวในรูปแบบที่เหมาะสมกับการส่งผ่าน LINE โดยใช้การจัดรูปแบบด้วยอีโมจิและสัญลักษณ์ เพื่อให้อ่านง่าย:

📰 หัวข้อข่าว: (ใช้พาดหัวข่าวที่น่าสนใจ)

✏️ สรุป:
- สรุปเนื้อหาสั้น ๆ กระชับ ชัดเจน

🔍 รายละเอียด:
- ข้อเท็จจริงที่เกี่ยวข้อง
- เพิ่มข้อมูลเชิงลึกที่น่าสนใจ

🎯 น้ำเสียงที่ใช้: {data.voice}

❗ โปรดเขียนในภาษาที่เข้าใจง่ายสำหรับผู้อ่านทั่วไป และไม่ต้องใส่ Markdown หรือ HTML
"""


    try:
        response = model.generate_content(prompt)
        reply_text = response.text.strip()

        # Push message to the user
        line_bot_api.push_message(data.user_id, TextSendMessage(text=reply_text))
        return {"status": "ok", "message": "News sent!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))