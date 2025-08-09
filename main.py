from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import pandas as pd
import numpy as np
import uvicorn
import os

app = FastAPI()

# fly.io에서는 자동으로 HTTPS를 처리하므로 별도 미들웨어 불필요

# 정적 파일 디렉토리 설정
static_dir = "static"
templates_dir = "templates"

# Static 파일 마운트 (더 구체적인 설정)
app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")
templates = Jinja2Templates(directory=templates_dir)

@app.get("/")
async def home(request: Request):
    # (이전과 동일하게)
    AGE_LABELS = ["10대", "20대", "30대", "40대", "50대", "60대 이상"]
    AGE_VALUES = [120, 450, 390, 260, 150, 45]
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "age_labels": AGE_LABELS,
            "age_values": AGE_VALUES,
        }
    )

@app.get("/news")
async def news(request: Request):
    # Excel 파일에서 뉴스 데이터 읽기
    try:
        data_file = "data/news_data.xlsx"
        df_news = pd.read_excel(data_file, sheet_name="뉴스")
        news_data = df_news.to_dict('records')
    except:
        news_data = []
    
    return templates.TemplateResponse("news.html", {"request": request, "news_data": news_data})

@app.get("/cases")
async def cases(request: Request):
    # Excel 파일에서 판례 데이터 읽기
    try:
        data_file = "data/cases_data.xlsx"
        df_cases = pd.read_excel(data_file, sheet_name="판례")
        cases_data = df_cases.to_dict('records')
    except:
        cases_data = []
    
    return templates.TemplateResponse("cases.html", {"request": request, "cases_data": cases_data})

@app.get("/resources")
async def resources(request: Request):
    return templates.TemplateResponse("resources.html", {"request": request})

@app.get("/debug")
async def debug():
    """디버깅용: 파일 경로 확인"""
    import os
    css_content = ""
    try:
        with open("static/css/style.css", "r", encoding="utf-8") as f:
            content = f.read()
            css_content = content[:200] + "..." if len(content) > 200 else content
    except:
        css_content = "파일을 읽을 수 없음"
    
    return {
        "current_dir": os.getcwd(),
        "static_exists": os.path.exists("static"),
        "static_files": os.listdir("static") if os.path.exists("static") else [],
        "static_css_files": os.listdir("static/css") if os.path.exists("static/css") else [],
        "static_css_exists": os.path.exists("static/css/style.css"),
        "css_file_size": os.path.getsize("static/css/style.css") if os.path.exists("static/css/style.css") else 0,
        "css_preview": css_content,
        "templates_exists": os.path.exists("templates"),
        "data_exists": os.path.exists("data"),
        "static_dir_used": static_dir,
        "templates_dir_used": templates_dir
    }

@app.get("/about")
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/statistics")
async def statistics(request: Request):
    # 연령대별 피해유형 데이터
    try:
        age_file = "data/한국여성인권진흥원_디지털성범죄피해자지원센터 연령대별 세부 피해 유형 현황_20231231.csv"
        df_age = pd.read_csv(age_file, encoding="cp949")
    except:
        # 데이터 파일이 없을 경우 기본값
        df_age = pd.DataFrame({"연령대": ["10대", "20대", "30대"], "촬영형": [10, 20, 15], "유포형": [5, 15, 10]})
    
    # 지원현황 데이터
    try:
        support_file = "data/한국여성인권진흥원_디지털성범죄피해자지원센터 지원현황_20241231.csv"
        df_support = pd.read_csv(support_file, encoding="cp949")
    except:
        # 데이터 파일이 없을 경우 기본값
        df_support = pd.DataFrame({"연도": [2022, 2023, 2024], "상담": [100, 150, 200], "법률지원": [50, 80, 120]})

    # 연령대별 피해유형 그래프용 데이터
    age_labels = df_age.iloc[:,0].tolist()
    age_types = df_age.columns[1:].tolist()
    age_type_values = [df_age[type].tolist() for type in age_types]

    # 연도별 지원현황 그래프용 데이터
    year_labels = df_support.iloc[1:,0].tolist()
    support_types = df_support.columns[1:].tolist()
    support_type_values = [df_support[type].iloc[1:].astype(int).tolist() for type in support_types]
    return templates.TemplateResponse(
        "statistics.html",
        {
            "request": request,
            "age_labels": age_labels,
            "age_types": age_types,
            "age_type_values": age_type_values,
            "year_labels": year_labels,
            "support_types": support_types,
            "support_type_values": support_type_values,
        }
    )

if __name__ == "__main__":
    # 환경변수에서 포트 가져오기 (cloudtype.io는 기본적으로 8080 사용)
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)