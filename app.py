import streamlit as st
import pandas as pd
import os
from datetime import datetime

DATA_FILE = "poker_action_log_v6.csv"
GTO_DB_FILE = "gto_6max_100bb.csv"

# --- ハンド表記を自動で標準化する機能 ---
def normalize_hand(hand_str):
    h = hand_str.upper().replace(" ", "")
    if len(h) < 2: return h
    
    ranks_order = "AKQJT98765432"
    # 最初の2文字（数字部分）を抽出して並べ替え
    r1, r2 = h[0], h[1]
    suffix = h[2:] if len(h) > 2 else ""
    
    if ranks_order.find(r1) > ranks_order.find(r2):
        return r1 + r2 + suffix
    else:
        return r2 + r1 + suffix

# --- 外部CSVからアクションを検索 ---
def get_action_from_csv(hand, position):
    h = normalize_hand(hand)
    p = position.upper()
    
    if os.path.exists(GTO_DB_FILE):
        gto_df = pd.read_csv(GTO_DB_FILE)
        match = gto_df[(gto_df['ハンド'] == h) & (gto_df['ポジション'] == p)]
        if not match.empty:
            return match.iloc[0]['正解アクション']
    return "-"

# データの読み込み
def load_data():
    cols = ["日時", "参加人数", "ハンド", "ポジション", "自分のアクション", "正解アクション", "メモ"]
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=cols)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

st.set_page_config(page_title="Preflop Checker", layout="centered")
st.title("⚡️ プリフロ判定ツール")

# --- メイン入力エリア ---
# 実戦で押しやすいよう、入力を中央に集約
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        player_count = st.radio("テーブル人数", [6, 9], index=0, horizontal=True)
    with col2:
        position = st.selectbox("ポジション", ["UTG", "UTG1", "LJ", "HJ", "CO", "BTN", "SB", "BB"], index=4)

    hand = st.text_input("ハンド (例: 25o, kqs, aa)", placeholder="25o").strip()

# --- 判定結果の表示 ---
if hand:
    correct_action = get_action_from_csv(hand, position)
    
    # 結果をデカデカと表示
    if correct_action == "レイズ":
        st.markdown(f"<h1 style='text-align: center; color: #ff4b4b;'>🔥 レイズ</h1>", unsafe_allow_html=True)
    elif correct_action == "フォールド":
        st.markdown(f"<h1 style='text-align: center; color: #777777;'>❄️ フォールド</h1>", unsafe_allow_html=True)
    elif correct_action == "コール":
        st.markdown(f"<h1 style='text-align: center; color: #4b4bff;'>💎 コール</h1>", unsafe_allow_html=True)
    else:
        st.warning("データにないハンドです。表記を確認してください（例: 52o）")

# --- 記録保存エリア ---
with st.expander("実戦ログとして保存する"):
    my_action = st.selectbox("自分の実際のアクション", ["未選択", "フォールド", "コール", "レイズ", "オールイン"])
    memo = st.text_input("メモ (相手の印象など)")
    if st.button("この判断をログに記録"):
        df = load_data()
        new_data = pd.DataFrame([{
            "日時": datetime.now().strftime("%m/%d %H:%M"),
            "参加人数": player_count,
            "ハンド": normalize_hand(hand),
            "ポジション": position,
            "自分のアクション": my_action,
            "正解アクション": correct_action,
            "メモ": memo
        }])
        df = pd.concat([df, new_data], ignore_index=True)
        save_data(df)
        st.success("ログを保存しました。")

# --- 履歴表示 ---
if st.checkbox("過去のログを表示"):
    df = load_data()
    if not df.empty:
        st.table(df.tail(10))