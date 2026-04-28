import streamlit as st
import pandas as pd
import os
from datetime import datetime

DATA_FILE = "poker_ev_log_v4.csv"

# --- V4: 多次元条件分岐AIエンジン ---
def get_preflop_gto(hand, player_count, position):
    """
    ハンド、参加人数、ポジションの3つの条件から正解を導き出す関数
    """
    h = hand.upper().replace(" ", "")
    
    # 参加人数によるテーブルの分類（7人以上をフルリング、6人以下をショートハンドと定義）
    table_type = "9-max" if player_count >= 7 else "6-max"

    # 多次元データベース（※テスト用のダミーデータ）
    gto_db = {
        "AA": {
            "9-max": {
                "UTG": {"action": "レイズ", "ev": 1.5},
                "BTN": {"action": "レイズ", "ev": 2.8},
                "default": {"action": "レイズ", "ev": 2.0} # その他のポジション用
            },
            "6-max": {
                "UTG": {"action": "レイズ", "ev": 2.1}, # 人数が少ない分、UTGでもEVが高い
                "BTN": {"action": "レイズ", "ev": 3.0},
                "default": {"action": "レイズ", "ev": 2.5}
            }
        },
        "AJO": {
            "9-max": {
                "UTG": {"action": "フォールド", "ev": 0.0}, # フルリングのUTGでは弱すぎるので捨てる
                "BTN": {"action": "レイズ", "ev": 0.3},     # 後ろのポジションなら戦える
                "default": {"action": "フォールド", "ev": 0.0}
            },
            "6-max": {
                "UTG": {"action": "フォールド", "ev": 0.0},
                "BTN": {"action": "レイズ", "ev": 0.5},     # 6人テーブルならBTNでの利益が少し上がる
                "default": {"action": "フォールド", "ev": 0.0}
            }
        },
        "72O": {
            # 72oは人数やポジションに関係なく常にフォールド
            "all": {"action": "フォールド", "ev": 0.0}
        }
    }

    if h not in gto_db:
        return "-", 0.0 # 辞書にないハンドは手動入力にする

    hand_data = gto_db[h]

    # 72oのように全条件共通のハンドの処理
    if "all" in hand_data:
        return hand_data["all"]["action"], hand_data["all"]["ev"]

    # 条件に合わせたデータの抽出
    if table_type in hand_data:
        table_data = hand_data[table_type]
        if position in table_data:
            return table_data[position]["action"], table_data[position]["ev"]
        else:
            return table_data["default"]["action"], table_data["default"]["ev"]

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
st.title("♠️ ポーカー実践・解析ログ V4 (条件分岐エンジン)")

st.header("📝 ハンド記録")
st.info("💡 テスト：「AA」や「AJo」を入力し、人数（6人/9人）やポジション（UTG/BTN）を変えて保存してみてください。")

with st.form("hand_input_form"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        location = st.selectbox("場所", ["KKPoker", "ライブ", "その他"])
        player_count = st.slider("参加人数", 2, 9, 6) # デフォルトを6人に設定
        hand = st.text_input("ハンド (例: AA, AJo, 72o)")
        position = st.selectbox("ポジション", ["UTG", "UTG+1", "MP", "CO", "BTN", "SB", "BB"]) # 順番を実際のプレイ順に整理

    with col2:
        eff_stack = st.number_input("エフェクティブスタック (BB)", min_value=0.0, value=100.0, step=1.0)
        spr = st.number_input("SPR (Stack-to-Pot Ratio)", min_value=0.0, step=0.1)
        my_action = st.selectbox("自分のアクション", ["フォールド", "チェック", "コール", "ベット", "レイズ", "オールイン"])
        correct_action = st.selectbox("正解のアクション (※自動判定時無視)", ["-", "フォールド", "チェック", "コール", "ベット", "レイズ", "オールイン"])

    with col3:
        est_ev = st.number_input("想定EV (BB)", value=0.0, step=0.1)
        true_ev = st.number_input("正解EV (BB) (※自動判定時無視)", value=0.0, step=0.1)
        
    action_detail = st.text_area("アクション詳細 / ボード情報")
    memo = st.text_area("その他メモ")
    
    submit_button = st.form_submit_button("保存して自動判定")

if submit_button:
    # --- V4: 人数とポジションを渡して判定させる ---
    auto_action, auto_ev = get_preflop_gto(hand, player_count, position)
    
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
        st.success(f"🤖 自動判定！ 【{player_count}人テーブル / {position} / {hand}】の正解は「{auto_action} (EV: {auto_ev}BB)」です。")
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