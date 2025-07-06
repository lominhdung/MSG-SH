import os
import openai
import fitz  # PyMuPDF
from flask import Flask, request, Response
from slack_sdk import WebClient
from slack_sdk.signature import SignatureVerifier
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
verifier = SignatureVerifier(os.getenv("SLACK_SIGNING_SECRET"))
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_text_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def analyze_medical_errors(content):
    prompt = f"""
    Bạn là một chuyên gia kiểm tra hồ sơ bệnh án theo quy định của Bộ Y tế.
    Hãy đọc nội dung sau và liệt kê các lỗi sai sót có thể dẫn đến xuất toán BHYT hoặc vi phạm quy định hồ sơ bệnh án:

    Nội dung hồ sơ:
    {content}

    Trả về danh sách lỗi cụ thể (nếu có), lý do, trích dẫn Thông tư liên quan.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response['choices'][0]['message']['content']

@app.route("/slack/events", methods=["POST"])
def slack_events():
    if not verifier.is_valid_request(request.get_data(), request.headers):
        return Response(status=403)

    payload = request.json

    # Xử lý nếu bot bị mention hoặc file được chia sẻ
    if "event" in payload:
        event = payload["event"]

        if event.get("type") == "app_mention":
            user = event["user"]
            channel = event["channel"]
            text = event.get("text", "")

            result = analyze_medical_errors(text)
            client.chat_postMessage(channel=channel, text=f"<@{user}> 📋 Kết quả phân tích:\n{result}")

        elif event.get("type") == "message" and "files" in event:
            for f in event["files"]:
                file_info = client.files_info(file=f["id"])["file"]
                file_url = file_info["url_private_download"]
                headers = {"Authorization": f"Bearer {os.getenv('SLACK_BOT_TOKEN')}"}
                file_data = requests.get(file_url, headers=headers)

                with open("temp.pdf", "wb") as out:
                    out.write(file_data.content)

                content = extract_text_from_pdf("temp.pdf")
                result = analyze_medical_errors(content)
                client.chat_postMessage(channel=event["channel"], text=f"📄 Phân tích file:\n{result}")

    return Response("OK", status=200)
