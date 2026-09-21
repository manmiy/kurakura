# kurakuraimport heapq
import streamlit as st

# ---------------------------------------------------------
# シミュレーションコアロジック（イベント駆動型）
# ---------------------------------------------------------
def run_builder_simulation(tasks, num_builders):
    """
    tasks: [{"name": 施設名, "duration": 所要時間(日), "count": 個数}, ...]
    num_builders: 大工の人数
    
    各タスクを個別の施設として展開し、大工の空き時間に割り当てる
    """
    if not tasks or num_builders <= 0:
        return 0, []

    # タスクを展開（個数分だけリスト化）
    # 優先度として「所要時間が長いもの」から順に割り当てる（クリティカルパスの最大化）
    expanded_tasks = []
    for t in tasks:
        for _ in range(t["count"]):
            expanded_tasks.append((t["name"], t["duration"]))
            
    # 時間の長い順にソート（効率的なスケジューリング）
    expanded_tasks.sort(key=lambda x: x[1], reverse=True)

    # 最小ヒープで大工の空き時間を管理 (空く時間, 大工ID)
    builders = [(0.0, i + 1) for i in range(num_builders)]
    heapq.heapify(builders)

    schedule_log = []

    for facility_name, duration in expanded_tasks:
        # 最も早く空く大工を取り出す
        free_time, builder_id = heapq.heappop(builders)
        
        start_time = free_time
        finish_time = start_time + duration
        
        schedule_log.append({
            "builder": builder_id,
            "name": facility_name,
            "duration": duration,
            "start": start_time,
            "finish": finish_time
        })
        
        # 作業完了後の時間を戻す
        heapq.heappush(builders, (finish_time, builder_id))

    # 全作業の中で最も遅い完了時間がトータル日数
    total_days = max(b[0] for b in builders)
    return total_days, schedule_log


# ---------------------------------------------------------
# UI構築 (Streamlit)
# ---------------------------------------------------------
st.set_page_config(page_title="クラクラ大工シミュレーター", layout="wide")
st.title("🛡️ クラクラ アップグレード完了日数シミュレーター")

# セッション状態の初期化（入力フォームの動的追加・削除用）
if "facility_rows" not in st.session_state:
    st.session_state.facility_rows = [
        {"name": "大砲", "count": 5, "duration": 7.0},
        {"name": "アーチャータワー", "count": 6, "duration": 8.5},
        {"name": "クラン城", "count": 1, "duration": 12.0},
    ]

# 1. 基本設定
st.header("1. 基本設定")
num_builders = st.number_input("稼働できる大工の人数", min_value=1, max_value=6, value=5, step=1)

st.markdown("---")

# 2. 施設データ入力エリア
st.header("2. 施設データの入力")
st.caption("同じ名前・時間の施設は「数」でまとめて入力できます。")

# 一括削除・行追加の操作ボタン
col_btn1, col_btn2 = st.columns([1, 5])
with col_btn1:
    if st.button("➕ 施設行を追加"):
        st.session_state.facility_rows.append({"name": "", "count": 1, "duration": 1.0})
        st.rerun()

# 各行の入力フォームを出力
updated_rows = []
for idx, row in enumerate(st.session_state.facility_rows):
    c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
    
    with c1:
        name = st.text_input(f"施設名 #{idx+1}", value=row["name"], key=f"name_{idx}")
    with c2:
        count = st.number_input(f"数 #{idx+1}", min_value=1, value=int(row["count"]), step=1, key=f"count_{idx}")
    with c3:
        duration = st.number_input(f"時間 (日数) #{idx+1}", min_value=0.1, value=float(row["duration"]), step=0.5, key=f"dur_{idx}")
    with c4:
        st.write("") # 高さ調整
        st.write("")
        if st.button("削除", key=f"del_{idx}"):
            st.session_state.facility_rows.pop(idx)
            st.rerun()
            
    updated_rows.append({"name": name, "count": count, "duration": duration})

st.session_state.facility_rows = updated_rows

st.markdown("---")

# 3. 計算実行処理
if st.button("🚀 計算を実行する", type="primary", use_container_width=True):
    # 有効なデータのみ抽出
    valid_tasks = [r for r in st.session_state.facility_rows if r["name"].strip() != ""]
    
    if not valid_tasks:
        st.warning("施設名が入力されている行がありません。")
    else:
        total_days, log = run_builder_simulation(valid_tasks, num_builders)
        
        # 答えの表示
        st.subheader("🎉 計算結果")
        
        # 単純合計時間（1人で作業した場合）と効率の比較
        sum_work_days = sum(t["duration"] * t["count"] for t in valid_tasks)
        ideal_days = sum_work_days / num_builders
        
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric("必要トータル日数", f"{total_days:.2f} 日")
        col_res2.metric("総労働時間（延べ日数）", f"{sum_work_days:.1f} 日分")
        col_res3.metric("理論上の最短（単純割）", f"{ideal_days:.2f} 日")
        
        # 内訳のログ（折りたたみ）
        with st.expander("詳細な割り当てスケジュールを確認する"):
            # 大工ごとにグループ化して表示
            for b_id in range(1, num_builders + 1):
                st.write(f"**🔨 大工 #{b_id} のスケジュール**")
                b_tasks = [l for l in log if l["builder"] == b_id]
                for task in b_tasks:
                    st.text(f"  • [{task['start']:.1f}日目 〜 {task['finish']:.1f}日目] {task['name']} ({task['duration']}日)")
