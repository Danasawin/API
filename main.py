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

🎯 โปรดจัดทำรายงานข่าวในรูปแบบต่อไปนี้:
1️⃣ พาดหัวข่าวให้น่าสนใจ ดึงดูดความสนใจผู้อ่าน
2️⃣ สรุปเนื้อหาให้ชัดเจน กระชับ เข้าใจง่าย
3️⃣ เพิ่มรายละเอียดที่เกี่ยวข้อง เป็นข้อเท็จจริง
4️⃣ ใช้น้ำเสียงที่เป็นกลาง มืออาชีพ และน่าเชื่อถือ

💡 **ข้อกำหนดในการจัดรูปแบบ**
- ห้ามใช้เครื่องหมาย * หรือ markdown ใดๆ
- ห้ามใช้ตัวหนาหรือเอียง
- ใช้ emoji เพื่อแยกหัวข้อย่อย เช่น 🔍 ✏️ 📢
- จัดบรรทัดใหม่เพื่อความอ่านง่าย
- เหมาะกับการแสดงผลใน LINE ที่รองรับข้อความล้วน (plain text)

ตัวอย่างโครงสร้างที่ต้องการ:

📰 หัวข้อข่าว

✏️ สรุปข่าว  
เนื้อหา...

🔍 รายละเอียด  
หัวข้อย่อย 1  
คำอธิบาย...

🛡️ แนวทางแก้ไข  
รายการ 1  
รายการ 2

📢 ข้อคิดหรือข้อเสนอแนะ
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