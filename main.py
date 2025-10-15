from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
import pandas as pd
import numpy as np
import uvicorn
import os
from datetime import datetime
import hashlib

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
    # 첫 번째 열(피해건수)은 총합이므로 제외하고 세부 피해 유형만 사용
    age_types = df_age.columns[2:].tolist()  # 2번째 열부터 (피해건수 제외)
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

@app.get("/reviews")
async def reviews(request: Request):
    # Excel 파일에서 후기 데이터 읽기
    try:
        data_file = "data/reviews_data_new.xlsx"
        if os.path.exists(data_file):
            df_reviews = pd.read_excel(data_file, sheet_name="후기")
            # NaN 값을 빈 문자열로 변환
            df_reviews = df_reviews.fillna("")
            reviews_data = df_reviews.to_dict('records')
        else:
            # 파일이 없으면 빈 DataFrame 생성하고 파일 생성
            df_reviews = pd.DataFrame(columns=["번호", "작성자", "내용", "작성일시"])
            reviews_data = []
            # 초기 파일 생성
            with pd.ExcelWriter(data_file, engine='openpyxl') as writer:
                df_reviews.to_excel(writer, sheet_name="후기", index=False)
    except Exception as e:
        print(f"Error reading reviews: {e}")
        reviews_data = []
    
    # 최신순으로 정렬 (번호가 큰 것부터)
    reviews_data = sorted(reviews_data, key=lambda x: x.get('번호', 0), reverse=True)
    
    return templates.TemplateResponse("reviews.html", {
        "request": request, 
        "reviews_data": reviews_data
    })

@app.post("/reviews/add")
async def add_review(request: Request, name: str = Form(...), content: str = Form(...), password: str = Form(...)):
    try:
        data_file = "data/reviews_data_new.xlsx"
        
        # 비밀번호 해시 생성
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # 기존 데이터 읽기
        if os.path.exists(data_file):
            df_reviews = pd.read_excel(data_file, sheet_name="후기")
        else:
            df_reviews = pd.DataFrame(columns=["번호", "작성자", "내용", "작성일시", "비밀번호"])
        
        # 새로운 번호 생성
        if len(df_reviews) == 0:
            new_id = 1
        else:
            new_id = df_reviews["번호"].max() + 1
        
        # 새 후기 추가
        new_review = pd.DataFrame([{
            "번호": new_id,
            "작성자": name,
            "내용": content,
            "작성일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "비밀번호": password_hash
        }])
        
        df_reviews = pd.concat([df_reviews, new_review], ignore_index=True)
        
        # Excel 파일에 저장
        with pd.ExcelWriter(data_file, engine='openpyxl') as writer:
            df_reviews.to_excel(writer, sheet_name="후기", index=False)
        
    except Exception as e:
        print(f"Error adding review: {e}")
    
    # 후기 페이지로 리다이렉트
    return RedirectResponse(url="/reviews", status_code=303)


@app.post("/reviews/delete/{review_id}")
async def delete_review(review_id: int, password: str = Form(...)):
    try:
        data_file = "data/reviews_data_new.xlsx"
        
        # 비밀번호 해시 생성
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # 기존 데이터 읽기
        if os.path.exists(data_file):
            df_reviews = pd.read_excel(data_file, sheet_name="후기")
        else:
            return JSONResponse({"success": False, "message": "데이터 파일이 없습니다."}, status_code=404)
        
        # 해당 번호의 후기 찾기
        review = df_reviews[df_reviews["번호"] == review_id]
        
        if len(review) == 0:
            return JSONResponse({"success": False, "message": "해당 후기를 찾을 수 없습니다."}, status_code=404)
        
        # 비밀번호 확인
        if review.iloc[0]["비밀번호"] != password_hash:
            return JSONResponse({"success": False, "message": "비밀번호가 일치하지 않습니다."}, status_code=401)
        
        # 후기 삭제
        df_reviews = df_reviews[df_reviews["번호"] != review_id]
        
        # Excel 파일에 저장
        with pd.ExcelWriter(data_file, engine='openpyxl') as writer:
            df_reviews.to_excel(writer, sheet_name="후기", index=False)
        
        return JSONResponse({"success": True, "message": "후기가 삭제되었습니다."})
        
    except Exception as e:
        print(f"Error deleting review: {e}")
        return JSONResponse({"success": False, "message": f"삭제 중 오류가 발생했습니다: {str(e)}"}, status_code=500)

if __name__ == "__main__":
    # 환경변수에서 포트 가져오기 (cloudtype.io는 기본적으로 8080 사용)
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)