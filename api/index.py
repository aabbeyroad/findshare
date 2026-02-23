"""
app.py — FindShare 메인 애플리케이션

왜 FastAPI를 선택했나?
  - 빠르고 현대적인 Python 웹 프레임워크
  - async/await 지원: 여러 사이트를 동시에 스크래핑할 수 있습니다
    (순차 실행: 5초 × 2사이트 = 10초 → 동시 실행: 약 5초)
  - 자동으로 API 문서 생성 (/docs 에서 확인 가능)

실행 방법:
  python app.py
  또는
  uvicorn app:app --reload  (개발 시 자동 재시작)
"""

import asyncio
import logging
import os
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from scrapers import DaangnScraper, PeterpanzScraper, NaverCafeScraper

# 로그 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# FastAPI 앱 초기화
# ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="FindShare API",
    description="쉐어하우스 양도 게시글 통합 검색 서비스",
    version="1.0.0",
)

# CORS 설정: 다른 도메인에서 API를 호출할 수 있게 허용
# (나중에 배포 시 특정 도메인만 허용하도록 변경 가능)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 제공 (HTML, CSS, JS)
# Vercel에서는 public/ 폴더 사용
import os
static_dir = os.path.join(os.path.dirname(__file__), "..", "public")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ──────────────────────────────────────────────────────────────
# 사용 가능한 스크래퍼 등록
# 새 사이트를 추가할 때는 여기에 추가하면 됩니다
# ──────────────────────────────────────────────────────────────
SCRAPERS = {
    "daangn": DaangnScraper,
    "peterpanz": PeterpanzScraper,
    "naver_cafe": NaverCafeScraper,
}

SCRAPER_NAMES = {
    "daangn": "당근마켓",
    "naver_cafe": "네이버 카페",
    "peterpanz": "피터팬",
}


# ──────────────────────────────────────────────────────────────
# 요청/응답 데이터 모델
# ──────────────────────────────────────────────────────────────
class SearchRequest(BaseModel):
    """검색 요청 파라미터"""

    keyword: str = Field(
        default="쉐어하우스 양도",
        description="검색 키워드",
        examples=["쉐어하우스 양도", "쉐어하우스 인수", "공유주택 양도"],
    )
    location: str = Field(
        default="",
        description="지역 필터 (비우면 전국 검색)",
        examples=["서울", "마포구", "서울 강남구"],
    )
    max_price: Optional[int] = Field(
        default=None,
        description="최대 가격 (원 단위). 예: 30000000 = 3천만원",
        examples=[30_000_000, 50_000_000, 100_000_000],
    )
    sites: List[str] = Field(
        default=["daangn", "peterpanz"],
        description="검색할 사이트 목록",
    )


class ListingResponse(BaseModel):
    """개별 매물 응답"""
    title: str
    url: str
    source: str
    price: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    posted_at: Optional[str] = None


class ScraperError(BaseModel):
    """스크래퍼 오류 정보"""
    source: str
    error: str


class SearchResponse(BaseModel):
    """검색 결과 응답"""
    listings: List[ListingResponse]
    total: int
    errors: List[ScraperError] = []
    search_info: dict = {}


# ──────────────────────────────────────────────────────────────
# API 엔드포인트
# ──────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def serve_frontend():
    """메인 페이지 (HTML 프론트엔드 제공)"""
    public_dir = os.path.join(os.path.dirname(__file__), "..", "public")
    index_path = os.path.join(public_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    # Fallback: static 폴더에서 찾기
    return FileResponse("static/index.html")


@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    쉐어하우스 양도 게시글 통합 검색

    여러 사이트를 동시에(asyncio.gather) 검색해서 결과를 합칩니다.
    한 사이트가 실패해도 다른 사이트 결과는 정상 반환됩니다.
    """
    logger.info(
        f"검색 요청: keyword='{request.keyword}', location='{request.location}', "
        f"max_price={request.max_price}, sites={request.sites}"
    )

    # 요청한 사이트 중 유효한 것만 필터링
    valid_sites = [s for s in request.sites if s in SCRAPERS]
    if not valid_sites:
        raise HTTPException(status_code=400, detail="유효한 사이트를 하나 이상 선택해주세요.")

    # 각 사이트의 스크래퍼 인스턴스 생성
    scraper_instances = [(site_id, SCRAPERS[site_id]()) for site_id in valid_sites]

    # 모든 스크래퍼를 동시에 실행 (asyncio.gather)
    # return_exceptions=True: 일부 실패해도 나머지 결과 반환
    tasks = [
        scraper.search(
            keyword=request.keyword,
            location=request.location,
            max_price=request.max_price,
        )
        for _, scraper in scraper_instances
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 결과 취합
    all_listings = []
    errors = []

    for (site_id, _), result in zip(scraper_instances, results):
        if isinstance(result, Exception):
            logger.error(f"[{SCRAPER_NAMES[site_id]}] 실패: {result}")
            errors.append(
                ScraperError(
                    source=SCRAPER_NAMES[site_id],
                    error=str(result),
                )
            )
        else:
            logger.info(f"[{SCRAPER_NAMES[site_id]}] {len(result)}개 결과")
            all_listings.extend([ListingResponse(**l.to_dict()) for l in result])

    logger.info(f"총 {len(all_listings)}개 결과 반환 (오류: {len(errors)}건)")

    return SearchResponse(
        listings=all_listings,
        total=len(all_listings),
        errors=errors,
        search_info={
            "keyword": request.keyword,
            "location": request.location,
            "sites_searched": [SCRAPER_NAMES[s] for s in valid_sites],
        },
    )


@app.get("/api/health")
async def health_check():
    """서비스 상태 확인"""
    return {
        "status": "ok",
        "service": "FindShare",
        "version": "1.0.0",
        "available_sites": list(SCRAPER_NAMES.values()),
    }


@app.get("/api/sites")
async def get_available_sites():
    """검색 가능한 사이트 목록 조회"""
    return {
        "sites": [
            {"id": site_id, "name": name}
            for site_id, name in SCRAPER_NAMES.items()
        ]
    }


# ──────────────────────────────────────────────────────────────
# 앱 실행
# ──────────────────────────────────────────────────────────────
# Vercel: app 객체를 자동으로 감지합니다. 아래 코드는 로컬 테스트용입니다.
# 배포 시에는 Vercel이 관리하므로 아래 코드는 실행되지 않습니다.
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"\n🏠 FindShare 서버 시작")
    print(f"   브라우저에서 열기: http://localhost:{port}")
    print(f"   API 문서:          http://localhost:{port}/docs")
    print(f"   종료: Ctrl+C\n")

    uvicorn.run(
        "api.index:app",  # Vercel 배포 시 경로
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info",
    )
