import streamlit as st
import pandas as pd
import os
from datetime import datetime

# データ保存用のローカルファイル
DATA_FILE = "poker_ev_log.csv"

# データの読み込み
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["日時", "場所", "ハンド", "ポジション", "SPR", "想定EV(BB)", "正解EV(BB)", "メモ"])

# データの保存
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

st.title("♠️ ポーカー期待値（EV）特化ログ")
st.write("収支ではなく、自分の「判断の精度」を記録し、GTOとのズレを修正するためのツールです。")

# --- 入力フォーム ---
st.header("📝 新しいハンドを記録")
with st.form("hand_input_form"):
    col1, col2 = st.columns(2)
    with col1:
        location = st.selectbox("場所", ["KKPoker", "ライブ", "その他"])
        hand = st.text_input("ハンド (例: AhKd)")
        position = st.selectbox("ポジション", ["SB", "BB", "UTG", "MP", "CO", "BTN"])
    with col2:
        spr = st.number_input("SPR (Stack-to-Pot Ratio)", min_value=0.0, step=0.1)
        est_ev = st.number_input("プレイ中の想定EV (BB)", value=0.0, step=0.1)
        true_ev = st.number_input("復習時の正解EV (BB) ※後で入力可", value=0.0, step=0.1)

    memo = st.text_area("メモ (相手の傾向、ベットサイズの意図など)")
    submit_button = st.form_submit_button("記録を追加")

if submit_button:
    df = load_data()
    new_data = pd.DataFrame([{
        "日時": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "場所": location,
        "ハンド": hand,
        "ポジション": position,
        "SPR": spr,
        "想定EV(BB)": est_ev,
        "正解EV(BB)": true_ev,
        "メモ": memo
    }])
    df = pd.concat([df, new_data], ignore_index=True)
    save_data(df)
    st.success("記録を保存しました！下部の表に反映されます。")

# --- データの表示と分析 ---
st.header("📊 過去の判断ログ")
df = load_data()

if not df.empty:
    # EVのズレ（誤差）を計算
    df['EV誤差(正解-想定)'] = df['正解EV(BB)'] - df['想定EV(BB)']
    
    # データの編集と表示
    st.write("※セルをダブルクリックして「正解EV」などを後から編集できます。")
    edited_df = st.data_editor(df, num_rows="dynamic")
    
    # 変更があったらCSVを上書き保存
    if not df.equals(edited_df):
        save_data(edited_df)
        st.rerun()

    # 簡単な分析サマリー
    st.subheader("💡 分析サマリー")
    avg_error = edited_df['EV誤差(正解-想定)'].mean()
    st.metric(label="平均EV誤差", value=f"{avg_error:.2f} BB")
    st.caption("※プラスが大きい場合は自分の見積もりが悲観的すぎ、マイナスが大きい場合は楽観的すぎる（ブラフ過多など）傾向があります。")

else:
    st.info("まだ記録がありません。上のフォームから入力してください。")