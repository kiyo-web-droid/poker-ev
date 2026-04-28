import streamlit as st
import pandas as pd
import os
from datetime import datetime

# データ保存用のローカルファイル
DATA_FILE = "poker_ev_log_v3.csv"

# --- プリフロップ簡易AIエンジン（第1段階プロトタイプ） ---
def get_preflop_gto(hand):
    """
    ハンドを入力すると、簡易的な正解アクションとEVを返す関数。
    ※大文字小文字の違いや、s(スーテッド)、o(オフスーツ)を自動補正します。
    """
    # 入力された文字を大文字にして空白を消す（表記揺れ対策）
    h = hand.upper().replace(" ", "")
    
    # 簡易辞書（本来はここに1326通りの全表が入ります）
    gto_chart = {
        "AA": {"action": "レイズ", "ev": 2.5},
        "KK": {"action": "レイズ", "ev": 1.8},
        "QQ": {"action": "レイズ", "ev": 1.2},
        "AKS": {"action": "レイズ", "ev": 0.8}, # s = スーテッド
        "AKO": {"action": "レイズ", "ev": 0.5}, # o = オフスーツ
        "72O": {"action": "フォールド", "ev": 0.0},
        "83O": {"action": "フォールド", "ev": 0.0},
    }
    
    if h in gto_chart:
        return gto_chart[h]["action"], gto_chart[h]["ev"]
    else:
        return "-", 0.0 # 辞書にないハンドは手動入力用にする

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
st.title("♠️ ポーカー実践・解析ログ V3 (自動判定テスト版)")

# --- 入力フォーム ---
st.header("📝 ハンド記録")
st.info("💡 テスト機能：「AA」や「72o」など特定のハンドを入力して保存すると、正解EVが自動入力されます。")

with st.form("hand_input_form"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        location = st.selectbox("場所", ["KKPoker", "ライブ", "その他"])
        player_count = st.slider("参加人数", 2, 9, 9)
        hand = st.text_input("ハンド (例: AA, AKs, 72o)")
        position = st.selectbox("ポジション", ["SB", "BB", "UTG", "UTG+1", "MP", "CO", "BTN"])

    with col2:
        eff_stack = st.number_input("エフェクティブスタック (BB)", min_value=0.0, step=1.0)
        spr = st.number_input("SPR (Stack-to-Pot Ratio)", min_value=0.0, step=0.1)
        my_action = st.selectbox("自分のアクション", ["フォールド", "チェック", "コール", "ベット", "レイズ", "オールイン"])
        correct_action = st.selectbox("正解のアクション (※自動判定される場合は無視されます)", ["-", "フォールド", "チェック", "コール", "ベット", "レイズ", "オールイン"])

    with col3:
        est_ev = st.number_input("想定EV (BB)", value=0.0, step=0.1)
        true_ev = st.number_input("正解EV (BB) (※自動判定される場合は無視されます)", value=0.0, step=0.1)
        
    action_detail = st.text_area("アクション詳細 / ボード情報")
    memo = st.text_area("その他メモ")
    
    submit_button = st.form_submit_button("保存して自動判定")

if submit_button:
    # --- 自動判定ロジック ---
    auto_action, auto_ev = get_preflop_gto(hand)
    
    # 辞書にハンドがあった場合は自動判定の値を優先、なければ手動入力の値を採用
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
        st.success(f"🤖 自動判定発動！ ハンド【{hand}】の正解アクションは「{auto_action}」、正解EVは「{auto_ev}BB」として記録しました。")
    else:
        st.success("記録を保存しました。")

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