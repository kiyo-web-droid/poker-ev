import streamlit as st
import pandas as pd
import os
from datetime import datetime

# データ保存用のローカルファイル
DATA_FILE = "poker_ev_log_v2.csv"

# データの読み込み
def load_data():
    cols = ["日時", "場所", "参加人数", "ハンド", "ポジション", "エフェクティブスタック(BB)", "SPR", 
            "アクション詳細", "自分のアクション", "正解のアクション", "想定EV(BB)", "正解EV(BB)", "メモ"]
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # 既存のCSVに新しい列がない場合の対応
        for col in cols:
            if col not in df.columns:
                df[col] = ""
        return df
    else:
        return pd.DataFrame(columns=cols)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

st.set_page_config(layout="wide") # 画面を広く使う
st.title("♠️ ポーカー実践・解析ログ V2")

# --- 入力フォーム ---
st.header("📝 ハンド記録（詳細版）")
with st.form("hand_input_form"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        location = st.selectbox("場所", ["KKPoker", "ライブ", "その他"])
        player_count = st.slider("参加人数", 2, 9, 9)
        hand = st.text_input("ハンド (例: AsKs)")
        position = st.selectbox("ポジション", ["SB", "BB", "UTG", "UTG+1", "MP", "CO", "BTN"])

    with col2:
        eff_stack = st.number_input("エフェクティブスタック (BB)", min_value=0.0, step=1.0)
        spr = st.number_input("SPR (Stack-to-Pot Ratio)", min_value=0.0, step=0.1)
        my_action = st.selectbox("自分のアクション", ["フォールド", "チェック", "コール", "ベット", "レイズ", "オールイン"])
        correct_action = st.selectbox("正解のアクション（解析後）", ["-", "フォールド", "チェック", "コール", "ベット", "レイズ", "オールイン"])

    with col3:
        est_ev = st.number_input("想定EV (BB)", value=0.0, step=0.1)
        true_ev = st.number_input("正解EV (BB)", value=0.0, step=0.1)
        
    action_detail = st.text_area("アクション詳細 (例: BTNから3BBオープン、自分BBでコール...等)")
    memo = st.text_area("その他メモ (相手の癖、その時の心理状態など)")
    
    submit_button = st.form_submit_button("このハンドを保存する")

if submit_button:
    df = load_data()
    new_data = pd.DataFrame([{
        "日時": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "場所": location,
        "参加人数": player_count,
        "ハンド": hand,
        "ポジション": position,
        "エフェクティブスタック(BB)": eff_stack,
        "SPR": spr,
        "アクション詳細": action_detail,
        "自分のアクション": my_action,
        "正解のアクション": correct_action,
        "想定EV(BB)": est_ev,
        "正解EV(BB)": true_ev,
        "メモ": memo
    }])
    df = pd.concat([df, new_data], ignore_index=True)
    save_data(df)
    st.success("ハンドを記録しました！")

# --- データの表示 ---
st.header("📊 過去のハンド履歴")
df = load_data()

if not df.empty:
    # ズレの可視化
    df['EV誤差'] = df['正解EV(BB)'] - df['想定EV(BB)']
    st.write("表のセルを直接編集して、後から「正解」を書き込めます。")
    edited_df = st.data_editor(df, num_rows="dynamic")
    
    if not df.equals(edited_df):
        save_data(edited_df)
        st.rerun()

    # 分析表示
    st.subheader("💡 傾向分析")
    c1, c2 = st.columns(2)
    with c1:
        avg_err = edited_df['EV誤差'].mean()
        st.metric("平均EV誤差", f"{avg_err:.2f} BB")
    with c2:
        # 正解率（アクションが一致しているか）
        correct_count = (edited_df['自分のアクション'] == edited_df['正解のアクション']).sum()
        total_reviewed = (edited_df['正解のアクション'] != "-").sum()
        if total_reviewed > 0:
            accuracy = (correct_count / total_reviewed) * 100
            st.metric("アクション正解率", f"{accuracy:.1f} %")
else:
    st.info("まだ記録がありません。")