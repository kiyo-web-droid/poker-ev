import streamlit as st
import pandas as pd
import os
from datetime import datetime

DATA_FILE = "poker_ev_log_v5.csv"
GTO_DB_FILE = "gto_6max_100bb.csv" # 外部の正解データファイル

# --- V5: 外部CSV（本物のデータベース）から正解を検索するエンジン ---
def get_gto_from_csv(hand, position):
    h = hand.upper().replace(" ", "")
    p = position.upper()
    
    # GTOのCSVファイルが存在するか確認
    if os.path.exists(GTO_DB_FILE):
        gto_df = pd.read_csv(GTO_DB_FILE)
        
        # ハンドとポジションが完全に一致する行を探す
        match = gto_df[(gto_df['ハンド'] == h) & (gto_df['ポジション'] == p)]
        
        if not match.empty:
            # 見つかった場合は、アクションとEVを返す
            action = match.iloc[0]['正解アクション']
            ev = match.iloc[0]['正解EV(BB)']
            return action, float(ev)
            
    # ファイルがない、またはハンドが登録されていない場合は手動入力へ
    return "-", 0.0

# データの読み込み
def load_data():
    cols = ["日時", "場所", "参加人数", "ハンド", "ポジション", "エフェクティブスタック(BB)", "SPR", 
            "アクション詳細", "自分のアクション", "正解のアクション", "想定EV(BB)", "正解EV(BB)", "メモ"]
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        for col in cols:
            if col not in df.columns:
                df[col] = ""
        return df
    else:
        return pd.DataFrame(columns=cols)

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

st.set_page_config(layout="wide")
st.title("♠️ ポーカー実践・解析ログ V5 (外部DB連動版)")

st.header("📝 ハンド記録")
st.info(f"💡 外部データ【{GTO_DB_FILE}】と連動中。AKs、AKoなどを入力してみてください。")

with st.form("hand_input_form"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        location = st.selectbox("場所", ["KKPoker", "ライブ", "その他"])
        player_count = st.slider("参加人数", 2, 9, 6)
        hand = st.text_input("ハンド (例: AKs, AKo, AJo)")
        position = st.selectbox("ポジション", ["UTG", "UTG+1", "MP", "CO", "BTN", "SB", "BB"])

    with col2:
        eff_stack = st.number_input("エフェクティブスタック (BB)", min_value=0.0, value=100.0, step=1.0)
        spr = st.number_input("SPR (Stack-to-Pot Ratio)", min_value=0.0, step=0.1)
        my_action = st.selectbox("自分のアクション", ["フォールド", "チェック", "コール", "ベット", "レイズ", "オールイン"])
        correct_action = st.selectbox("正解のアクション (自動判定時は無視)", ["-", "フォールド", "チェック", "コール", "ベット", "レイズ", "オールイン"])

    with col3:
        est_ev = st.number_input("想定EV (BB)", value=0.0, step=0.1)
        true_ev = st.number_input("正解EV (BB) (自動判定時は無視)", value=0.0, step=0.1)
        
    action_detail = st.text_area("アクション詳細 / ボード情報")
    memo = st.text_area("その他メモ")
    
    submit_button = st.form_submit_button("保存して外部DBと照合")

if submit_button:
    # 外部CSVデータを参照して判定
    auto_action, auto_ev = get_gto_from_csv(hand, position)
    
    final_correct_action = auto_action if auto_action != "-" else correct_action
    final_true_ev = auto_ev if auto_action != "-" else true_ev

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
        "正解のアクション": final_correct_action,
        "想定EV(BB)": est_ev,
        "正解EV(BB)": final_true_ev,
        "メモ": memo
    }])
    df = pd.concat([df, new_data], ignore_index=True)
    save_data(df)
    
    if auto_action != "-":
        st.success(f"✅ DB照合完了！ 【{position} / {hand}】の正解は「{auto_action} (EV: {auto_ev}BB)」です。")
    else:
        st.success("記録を保存しました。（DBにないハンドのため手動入力として処理）")

# --- データの表示 ---
st.header("📊 過去のハンド履歴")
df = load_data()

if not df.empty:
    df['EV誤差'] = df['正解EV(BB)'] - df['想定EV(BB)']
    edited_df = st.data_editor(df, num_rows="dynamic")
    
    if not df.equals(edited_df):
        save_data(edited_df)
        st.rerun()

    st.subheader("💡 傾向分析")
    c1, c2 = st.columns(2)
    with c1:
        avg_err = edited_df['EV誤差'].mean()
        st.metric("平均EV誤差", f"{avg_err:.2f} BB")
    with c2:
        correct_count = (edited_df['自分のアクション'] == edited_df['正解のアクション']).sum()
        total_reviewed = (edited_df['正解のアクション'] != "-").sum()
        if total_reviewed > 0:
            accuracy = (correct_count / total_reviewed) * 100
            st.metric("アクション正解率", f"{accuracy:.1f} %")