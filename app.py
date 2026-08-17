import os

from dotenv import load_dotenv
from flask import Flask, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    ButtonsTemplate,
    CarouselColumn,
    CarouselTemplate,
    DatetimePickerTemplateAction,
    LocationAction,
    LocationMessage,
    MessageEvent,
    PostbackEvent,
    QuickReply,
    QuickReplyButton,
    TemplateSendMessage,
    TextMessage,
    TextSendMessage,
    URIAction,
)

import session
from walkerplus import scrape_walkerplus

load_dotenv(override=True)

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ["ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["CHANNEL_SECRET"])


@app.route("/")
def index():
    return "You call index()"


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


def _get_user_id(event) -> str | None:
    if event.source.type == "user":
        return event.source.user_id
    return None


def _build_carousel_message(events: list[dict[str, str]]) -> TemplateSendMessage:
    columns = [
        CarouselColumn(
            thumbnail_image_url=event["image_url"],
            title=event["title"][:40],
            text="詳細を見る",
            actions=[URIAction(label="詳細", uri=event["link_url"])],
        )
        for event in events
    ]
    return TemplateSendMessage(
        alt_text="イベント検索結果",
        template=CarouselTemplate(columns=columns),
    )


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text == "イベント検索":
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(
                alt_text="日付を選択してください",
                template=ButtonsTemplate(
                    title="イベント検索",
                    text="開催日を選んでください",
                    actions=[
                        DatetimePickerTemplateAction(
                            label="日付を選ぶ",
                            data="action=event_search&step=date",
                            mode="date",
                        )
                    ],
                ),
            ),
        )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=event.message.text),
        )


@handler.add(MessageEvent, message=LocationMessage)
def handle_location(event):
    user_id = _get_user_id(event)
    if not user_id:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ユーザー情報を取得できませんでした。"),
        )
        return

    date_str = session.get_selected_date(user_id)
    if not date_str:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="先に「イベント検索」から日付を選択してください。"
            ),
        )
        return

    try:
        events = scrape_walkerplus(
            event.message.latitude,
            event.message.longitude,
            date_str,
        )
    except Exception:
        app.logger.exception("Failed to scrape WalkerPlus")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text="イベント情報の取得に失敗しました。しばらくしてから再度お試しください。"
            ),
        )
        return
    finally:
        session.clear_selected_date(user_id)

    if not events:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(
                text=f"{date_str} の周辺ではイベントが見つかりませんでした。"
            ),
        )
        return

    line_bot_api.reply_message(
        event.reply_token,
        _build_carousel_message(events),
    )


@handler.add(PostbackEvent)
def handle_postback(event):
    if "action=event_search" not in event.postback.data:
        return

    selected_date = event.postback.params.get("date", "")
    user_id = _get_user_id(event)
    if user_id and selected_date:
        session.save_selected_date(user_id, selected_date)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(
            text=f"{selected_date} を選択しました。現在地を送ってください。",
            quick_reply=QuickReply(
                items=[
                    QuickReplyButton(
                        action=LocationAction(label="現在地を送る"),
                    )
                ]
            ),
        ),
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
