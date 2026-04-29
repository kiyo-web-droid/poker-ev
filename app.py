import streamlit as st
import pandas as pd
import os
from datetime import datetime

DATA_FILE = "poker_action_log_v7.csv"
GTO_DB_FILE = "gto_6max_100bb.csv"

# --- ハンド表記を「強い順」に正しく修正する機能 ---
def normalize_hand(hand_str):
    h = hand_str.upper().replace(" ", "")
    if len(h) < 2: return h
    
    ranks_order = "AKQJT98765432"
    r1, r2 = h[0], h[1]
    suffix = h[2:] if len(h) > 2 else ""
    
    # ランクの強さを比較（インデックスが小さいほど強い）
    idx1 = ranks_order.find(r1)
    idx2 = ranks_order.find(r2)
    
    if idx1 == -1 or idx2 == -1: return h # ランク外の文字
    
    if idx1 <= idx2:
        # すでに強い順（または同じ）ならそのまま
        return r1 + r2 + suffix
    else:
        # 逆なら入れ替える
        return r2 + r1 + suffix

# --- 外部CSVからアクションを検索 ---
def get_action_from_csv(hand, position):
    h = normalize_hand(hand)
    p = position.upper()
    
    if os.path.exists(GTO_DB_FILE):
        gto_df = pd.read_csv(GTO_DB_FILE)
        # データベース内のハンド名と照合
        match = gto_df[(gto_df['ハンド'] == h) & (gto_df['ポジション'] == p)]
        if not match.empty:
            return match.iloc[0]['正解アクション']
    return "-"

st.set_page_config(page_title="Preflop Checker", layout="centered")
st.title("⚡️ プリフロ判定ツール V7")

# --- メイン入力エリア ---
with st.container():
    # 人数をスライダーに変更（2-9人）
    player_count = st.slider("テーブル人数", 2, 9, 6)
    
    # ポジション選択
    position = st.selectbox("ポジション", ["UTG", "UTG1", "LJ", "HJ", "CO", "BTN", "SB", "BB"], index=4)

    # ハンド入力
    hand = st.text_input("ハンド (例: 25o, kqs, aa)", placeholder="25o").strip()

# --- 判定結果の表示 ---
if hand:
    # 内部でどう判定されているかを表示（デバッグ用）
    normalized = normalize_hand(hand)
    correct_action = get_action_from_csv(hand, position)
    
    st.write(f"判定ハンド: {normalized}")
    
    if correct_action == "レイズ":
        st.markdown(f"<h1 style='text-align: center; color: #ff4b4b;'>🔥 レイズ</h1>", unsafe_allow_html=True)
    elif correct_action == "フォールド":
        st.markdown(f"<h1 style='text-align: center; color: #777777;'>❄️ フォールド</h1>", unsafe_allow_html=True)
    elif correct_action == "コール":
        st.markdown(f"<h1 style='text-align: center; color: #4b4bff;'>💎 コール</h1>", unsafe_allow_html=True)
    else:
        st.warning("データにないハンドです。表に載っていない弱い手の可能性があります。")

# --- 記録保存エリア ---
with st.expander("実戦ログとして保存する"):
    my_action = st.selectbox("自分の実際のアクション", ["未選択", "フォールド", "コール", "レイズ", "オールイン"])
    memo = st.text_input("メモ")
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
        # 念のため保存用関数も定義しておく
        df.to_csv(DATA_FILE, index=False)
        st.success("ログを保存しました。")