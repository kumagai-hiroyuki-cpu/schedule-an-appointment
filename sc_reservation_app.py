
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# ページ設定
st.set_page_config(
    page_title="スクールカウンセリング予約・管理システム",
    page_icon="🏫",
    layout="wide"
)

# セッション状態の初期化（モックデータ用）
if "reservations" not in st.session_state:
    # サンプルデータ
    st.session_state.reservations = pd.DataFrame([
        {
            "id": 1,
            "date": "2026-11-10",
            "time_slot": "10:00 - 11:00",
            "status": "予約済み",
            "teacher": "山田 太郎",
            "student_info": "1年2組 ○○さん (人間関係の悩み)"
        },
        {
            "id": 2,
            "date": "2026-11-10",
            "time_slot": "13:00 - 14:00",
            "status": "予約済み",
            "teacher": "佐藤 花子",
            "student_info": "2年1組 ××君 (進路の不安)"
        }
    ])

if "slots" not in st.session_state:
    # カウンセラーの勤務可能枠（例）
    st.session_state.slots = [
        {"date": "2026-11-10", "time_slot": "10:00 - 11:00", "available": False},
        {"date": "2026-11-10", "time_slot": "11:00 - 12:00", "available": True},
        {"date": "2026-11-10", "time_slot": "13:00 - 14:00", "available": False},
        {"date": "2026-11-10", "time_slot": "14:00 - 15:00", "available": True},
        {"date": "2026-11-12", "time_slot": "10:00 - 11:00", "available": True},
        {"date": "2026-11-12", "time_slot": "11:00 - 12:00", "available": True},
    ]

# 特定の特権ユーザー（SCおよび指定の教員3名）のシミュレーション
# 実際の学校導入時は Google Workspace のログインメールアドレス等で判定します
SPECIAL_EMAILS = ["sc@school.ed.jp", "teacher1@school.ed.jp", "teacher2@school.ed.jp", "teacher3@school.ed.jp"]

st.title("🏫 スクールカウンセラー（SC）面談予約システム")
st.markdown("---")

# サイドバー：ログイン・権限シミュレーション
st.sidebar.header("🔐 ログイン・権限設定")
user_role = st.sidebar.selectbox(
    "あなたの役割を選択してください",
    ["一般教員（他の先生）", "特定の特権教員（3名のうちの1人）", "スクールカウンセラー (SC)"]
)

# 役割に応じたフラグ
is_privileged = (user_role != "一般教員（他の先生）")
user_name = st.sidebar.text_input("あなたの氏名", value="鈴木 一郎" if not is_privileged else "指定教員A")

st.sidebar.markdown("---")
st.sidebar.info(
    "**【プライバシー保護の仕組み】**
"
    "- **一般の先生方**: 空き時間の確認と予約が可能ですが、他の先生の面談の『誰の相談か』は一切見えません（『予約済み』とだけ表示されます）。
"
    "- **特定の教員3名・SC**: すべての予約の詳細（生徒名や相談内容）を確認・管理できます。"
)

# メインタブの作成
tab1, tab2, tab3 = st.tabs(["📅 空き状況・予約する", "📋 全体スケジュール確認", "⚙️ 管理・枠の追加（SC向け）"])

with tab1:
    st.subheader("📅 カウンセラーの空き状況と予約")
    st.markdown("空いている時間帯を選択して、面談の予約を行うことができます。")
    
    # スロットの一覧表示
    slots_df = pd.DataFrame(st.session_state.slots)
    
    # 予約データのステータスを反映
    display_data = []
    for slot in st.session_state.slots:
        # 該当スロットの予約を探す
        matched_res = st.session_state.reservations[
            (st.session_state.reservations["date"] == slot["date"]) & 
            (st.session_state.reservations["time_slot"] == slot["time_slot"])
        ]
        
        status_text = "🟢 予約可能（空き）" if slot["available"] else "🔴 予約済み"
        
        # 誰の予約かは、特権ユーザーか本人のみ詳細表示、一般には伏せる
        detail = "---"
        if not slot["available"]:
            if not matched_res.empty:
                if is_privileged:
                    detail = f"{matched_res.iloc[0]['teacher']} 先生 (対象: {matched_res.iloc[0]['student_info']})"
                else:
                    detail = "面談が入っています（詳細非公開）"
        
        display_data.append({
            "日付": slot["date"],
            "時間帯": slot["time_slot"],
            "ステータス": status_text,
            "詳細 / 相談者": detail,
            "raw_available": slot["available"]
        })
    
    df_view = pd.DataFrame(display_data)
    st.dataframe(df_view[["日付", "時間帯", "ステータス", "詳細 / 相談者"]], use_container_width=True, hide_index=True)
    
    st.markdown("### 📝 新規予約の申し込み")
    available_slots = [f"{s['date']} ({s['time_slot']})" for s in st.session_state.slots if s["available"]]
    
    if available_slots:
        with st.form("reservation_form"):
            selected_slot = st.selectbox("予約可能な日時を選択", available_slots)
            student_input = st.text_input("相談対象（学年・組・生徒名、および概要）", placeholder="例: 1年2組 山田太郎（学校生活への適応について）")
            submit_btn = st.form_submit_button("この時間で予約を確定する")
            
            if submit_btn:
                if not student_input.strip():
                    st.error("相談対象や概要を入力してください。")
                else:
                    # 日付と時間帯を抽出
                    date_part = selected_slot.split(" ")[0]
                    time_part = selected_slot.split(" ")[1] + " " + selected_slot.split(" ")[2] + " " + selected_slot.split(" ")[3]
                    
                    # スロットを予約済みに更新
                    for s in st.session_state.slots:
                        if s["date"] == date_part and s["time_slot"] == time_part:
                            s["available"] = False
                    
                    # 予約データに追加
                    new_res = pd.DataFrame([{
                        "id": len(st.session_state.reservations) + 1,
                        "date": date_part,
                        "time_slot": time_part,
                        "status": "予約済み",
                        "teacher": user_name,
                        "student_info": student_input
                    }])
                    st.session_state.reservations = pd.concat([st.session_state.reservations, new_res], ignore_index=True)
                    st.success("予約が完了しました！他の先生の画面には「予約済み」としてのみ表示されます。")
                    st.rerun()
    else:
        st.warning("現在、予約可能な空き枠がありません。")

with tab2:
    st.subheader("📋 スケジュール一覧（全教員向けビュー）")
    st.markdown("学校全体でのカウンセリング実施状況（空き・埋まり具合）を確認できます。")
    
    # 一般教員が見る形式のテーブル
    general_view = []
    for slot in st.session_state.slots:
        status = "【空き】予約受付中" if slot["available"] else "【予約済み】面談実施予定"
        general_view.append({
            "日付": slot["date"],
            "時間帯": slot["time_slot"],
            "状況": status
        })
    st.table(pd.DataFrame(general_view))
    
    if is_privileged:
        st.markdown("---")
        st.markdown("### 🔒 【特権ユーザー専用】詳細な面談一覧")
        st.success("あなたには特権権限が付与されているため、以下の詳細を確認できます。")
        st.dataframe(st.session_state.reservations[["date", "time_slot", "teacher", "student_info"]], use_container_width=True)

with tab3:
    st.subheader("⚙️ 管理者・SC向け設定")
    if user_role == "スクールカウンセラー (SC)" or is_privileged:
        st.markdown("#### 新規のカウンセリング可能枠を追加する")
        with st.form("add_slot_form"):
            new_date = st.date_input("実施日付", value=datetime.today() + timedelta(days=1))
            new_time = st.selectbox("時間帯", ["10:00 - 11:00", "11:00 - 12:00", "13:00 - 14:00", "14:00 - 15:00", "15:00 - 16:00"])
            add_btn = st.form_submit_button("空き枠を追加")
            
            if add_btn:
                date_str = new_date.strftime("%Y-%m-%d")
                # 重複チェック
                exists = any(s["date"] == date_str and s["time_slot"] == new_time for s in st.session_state.slots)
                if exists:
                    st.warning("その日時・時間帯の枠はすでに存在します。")
                else:
                    st.session_state.slots.append({"date": date_str, "time_slot": new_time, "available": True})
                    st.success(f"{date_str} {new_time} の枠を追加しました。")
                    st.rerun()
        
        st.markdown("#### 予約のキャンセル・管理")
        if not st.session_state.reservations.empty:
            res_to_cancel = st.selectbox(
                "キャンセル・削除する予約を選択",
                st.session_state.reservations.apply(lambda r: f"ID:{r['id']} | {r['date']} {r['time_slot']} | 担当:{r['teacher']} | 対象:{r['student_info']}", axis=1)
            )
            if st.button("選択した予約をキャンセル（枠を解放）"):
                res_id = int(res_to_cancel.split(" | ")[0].replace("ID:", ""))
                # 該当予約の情報を取得
                target_res = st.session_state.reservations[st.session_state.reservations["id"] == res_id].iloc[0]
                
                # スロットを再度空きにする
                for s in st.session_state.slots:
                    if s["date"] == target_res["date"] and s["time_slot"] == target_res["time_slot"]:
                        s["available"] = True
                
                # 予約リストから削除
                st.session_state.reservations = st.session_state.reservations[st.session_state.reservations["id"] != res_id]
                st.success("予約をキャンセルし、枠を解放しました。")
                st.rerun()
    else:
        st.warning("このタブはスクールカウンセラーおよび特定の特権教員のみアクセスできます。")
