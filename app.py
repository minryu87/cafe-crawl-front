import gradio as gr
import pandas as pd
import requests
import plotly.express as px

ele_api = "https://cafecrawl-cicd-u45006.vm.elestio.app"

# 검색 이력 불러오기
def fetch_search_logs():
    r = requests.get(f"{ele_api}/search-logs/")
    if r.status_code == 200:
        logs = r.json().get("logs", [])
        # (id, summary) 튜플 리스트로 변환
        return [(f"{log['search_query']} | {log['period']} | {log['requested_at'][:16]}", log['id']) for log in logs]
    return []

# 분석 결과 불러오기
def fetch_analysis_result(search_log_id):
    r = requests.get(f"{ele_api}/analysis-result/", params={"search_log_id": search_log_id})
    if r.status_code == 200:
        return pd.DataFrame(r.json().get("data", []))
    return pd.DataFrame()

def show_analysis(search_log_id, relevance_only, selected_user):
    df = fetch_analysis_result(search_log_id)
    if df.empty:
        return "데이터 없음", None, "<div>데이터 없음</div>", gr.update(choices=[], value=None), "<div>데이터 없음</div>"
    # 관련도 1만 보기 필터
    if relevance_only:
        filtered = df[df['is_relevant'] == 1]
    else:
        filtered = df
    # 요약/그래프/테이블
    user_counts = filtered['user_name'].value_counts().reset_index()
    user_counts.columns = ['카페명', 'count']
    top_users = user_counts.head(3)
    summary = f"가장 많은 게시글이 수집된 카페는 {top_users.iloc[0]['카페명']}로, {top_users.iloc[0]['count']}개 수집되었습니다." if len(top_users) > 0 else "데이터 없음"
    if len(top_users) > 1:
        summary += f" 2위는 {top_users.iloc[1]['카페명']}로, {top_users.iloc[1]['count']}개,"
    if len(top_users) > 2:
        summary += f" 3위는 {top_users.iloc[2]['카페명']}로, {top_users.iloc[2]['count']}개 입니다."
    fig = None
    if not user_counts.empty:
        fig = px.bar(user_counts.head(10), x='카페명', y='count', title='카페별 게시글 수(상위 10)', labels={'카페명':'카페명','count':'개수'})
    user_list = user_counts['카페명'].tolist()
    selected_user_val = selected_user if selected_user in user_list else (user_list[0] if user_list else None)
    user_df = filtered[filtered['user_name'] == selected_user_val] if selected_user_val else pd.DataFrame()
    def make_html_table(df, max_height=400):
        if df.empty:
            return "<div>데이터 없음</div>"
        df = df.copy().reset_index(drop=True)
        df.insert(0, '순번', df.index + 1)
        col_order = ['순번', 'user_name', 'title', 'date', 'summary', 'is_relevant', 'reason', 'link']
        for col in col_order:
            if col not in df.columns:
                df[col] = ''
        html = f'<div style="max-height:{max_height}px;overflow-y:auto;">'
        html += '<table border="1" style="font-size:13px; border-collapse:collapse; width:100%; table-layout:fixed; word-break:break-all;">'
        html += '<tr>'
        for col in ['순번', '카페명', 'title', 'date', 'summary', 'is_relevant', 'reason', '원문보기']:
            html += f'<th>{col}</th>'
        html += '</tr>'
        for _, row in df.iterrows():
            html += '<tr>'
            for col, disp in zip(['순번', 'user_name', 'title', 'date', 'summary', 'is_relevant', 'reason'], ['순번', '카페명', 'title', 'date', 'summary', 'is_relevant', 'reason']):
                html += f'<td>{row[col]}</td>'
            link = row['link']
            if pd.notnull(link) and link:
                html += f'<td><a href="{link}" target="_blank">link</a></td>'
            else:
                html += '<td></td>'
            html += '</tr>'
        html += '</table></div>'
        return html
    html_table = make_html_table(filtered, max_height=400)
    user_html = make_html_table(user_df, max_height=300)
    return summary, fig, html_table, gr.update(choices=user_list, value=selected_user_val), user_html

def update_user_html(search_log_id, relevance_only, selected_user):
    df = fetch_analysis_result(search_log_id)
    if df.empty:
        return "<div>데이터 없음</div>"
    filtered = df[df['is_relevant'] == 1] if relevance_only else df
    user_df = filtered[filtered['user_name'] == selected_user] if selected_user else pd.DataFrame()
    def make_html_table(df, max_height=300):
        if df.empty:
            return "<div>데이터 없음</div>"
        df = df.copy().reset_index(drop=True)
        df.insert(0, '순번', df.index + 1)
        col_order = ['순번', 'user_name', 'title', 'date', 'summary', 'is_relevant', 'reason', 'link']
        for col in col_order:
            if col not in df.columns:
                df[col] = ''
        html = f'<div style="max-height:{max_height}px;overflow-y:auto;">'
        html += '<table border="1" style="font-size:13px; border-collapse:collapse; width:100%; table-layout:fixed; word-break:break-all;">'
        html += '<tr>'
        for col in ['순번', '카페명', 'title', 'date', 'summary', 'is_relevant', 'reason', '원문보기']:
            html += f'<th>{col}</th>'
        html += '</tr>'
        for _, row in df.iterrows():
            html += '<tr>'
            for col, disp in zip(['순번', 'user_name', 'title', 'date', 'summary', 'is_relevant', 'reason'], ['순번', '카페명', 'title', 'date', 'summary', 'is_relevant', 'reason']):
                html += f'<td>{row[col]}</td>'
            link = row['link']
            if pd.notnull(link) and link:
                html += f'<td><a href="{link}" target="_blank">link</a></td>'
            else:
                html += '<td></td>'
            html += '</tr>'
        html += '</table></div>'
        return html
    return make_html_table(user_df, max_height=300)

with gr.Blocks() as demo:
    gr.Markdown("""
    # 네이버 카페 크롤링 분석 서비스 (Hugging Face Front)
    - 좌측에서 검색 이력 선택 → 분석/시각화
    """)
    with gr.Row():
        with gr.Column(scale=1):
            search_logs = gr.Dropdown(label="검색 이력 선택", choices=fetch_search_logs(), interactive=True)
            relevance_only = gr.Checkbox(label="관련도 1(관련)만 보기", value=True)
        with gr.Column(scale=4):
            out1 = gr.Textbox(label="요약")
            out2 = gr.Plot(label="카페별 게시글 수(상위 10)")
            out3 = gr.HTML(label="전체 결과")
            user_list = gr.Dropdown(label="카페명 선택", choices=[], interactive=True)
            out4 = gr.HTML(label="선택 카페 리스트")

    def on_search_log_change(search_log_id, relevance_only):
        return show_analysis(search_log_id, relevance_only, None)

    search_logs.change(
        on_search_log_change,
        inputs=[search_logs, relevance_only],
        outputs=[out1, out2, out3, user_list, out4]
    )

    user_list.change(
        update_user_html,
        inputs=[search_logs, relevance_only, user_list],
        outputs=out4
    )

demo.launch()
