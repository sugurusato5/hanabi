"""ユーザーごとのイベント検索セッションを一時保存する。"""

from __future__ import annotations

# user_id -> 選択された日付 ("YYYY-MM-DD")
user_selected_dates: dict[str, str] = {}


def save_selected_date(user_id: str, date_str: str) -> None:
    user_selected_dates[user_id] = date_str


def get_selected_date(user_id: str) -> str | None:
    return user_selected_dates.get(user_id)


def clear_selected_date(user_id: str) -> None:
    user_selected_dates.pop(user_id, None)
