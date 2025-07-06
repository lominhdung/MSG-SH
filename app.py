from flask import Flask, request, jsonify
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
import os

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

bolt_app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)
handler = SlackRequestHandler(bolt_app)

flask_app = Flask(__name__)

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.get_json()
    # Kiểm tra nếu là yêu cầu xác minh từ Slack
    if data.get("type") == "url_verification":
        return jsonify({"challenge": data.get("challenge")})
    # Nếu không thì chuyển cho handler xử lý các sự kiện khác
    return handler.handle(request)

@flask_app.route("/")
def home():
    return "Bot GPT kiểm tra bệnh án đang hoạt động!"

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
