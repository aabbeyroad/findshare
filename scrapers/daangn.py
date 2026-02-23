"""
daangn.py — 당근마켓 스크래퍼

왜 Playwright를 사용하나?
  당근마켓은 React로 만들어진 사이트입니다.
  일반 HTTP 요청(requests, httpx)으로는 빈 HTML만 받게 되고
  실제 게시글 데이터는 JavaScript가 실행된 후에 나타납니다.
  Playwright는 실제 브라우저처럼 JS를 실행해서 완전한 페이지를 가져옵니다.

검색 URL 형태:
  https://www.daangn.com/search/{검색어}#tab=flea_market
"""

import logging
import asyncio
from typing import Optional, List
from urllib.parse import quote

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from .base import BaseScraper, Listing

logger = logging.getLogger(__name__)


class DaangnScraper(BaseScraper):
    """당근마켓 중고거래 게시글 스크래퍼"""

    BASE_URL = "https://www.daangn.com"
    SOURCE_NAME = "당근마켓"
    MAX_RESULTS = 20  # 한 번 검색에 가져올 최대 게시글 수

    async def search(
        self,
        keyword: str,
        location: str = "",
        max_price: Optional[int] = None,
    ) -> List[Listing]:
        """
        당근마켓에서 키워드로 게시글을 검색합니다.

        당근마켓은 지역 기반 플랫폼이라 특정 지역을 URL로 필터링하기 어렵습니다.
        대신 검색어에 지역명을 포함시켜 검색합니다.
        (예: "쉐어하우스 양도 마포구")
        """
        # 검색어 구성: 키워드 + 지역
        search_query = f"{keyword} {location}".strip() if location else keyword
        encoded_query = quote(search_query)

        # 중고거래 탭으로 바로 이동
        url = f"{self.BASE_URL}/search/{encoded_query}#tab=flea_market"
        logger.info(f"[당근마켓] 검색 시작: {search_query}")

        listings: List[Listing] = []

        try:
            async with async_playwright() as playwright:
                # headless=True: 실제 브라우저 창을 띄우지 않고 백그라운드에서 실행
                browser = await playwright.chromium.launch(headless=True)
                context = await browser.new_context(
                    # 한국어 환경 설정 (봇으로 감지될 가능성 줄이기)
                    locale="ko-KR",
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                )

                page = await context.new_page()

                try:
                    # 페이지 로드 (networkidle: 네트워크 요청이 멈출 때까지 대기)
                    await page.goto(url, wait_until="networkidle", timeout=30_000)

                    # 검색 결과가 나타날 때까지 최대 10초 대기
                    # 당근마켓 셀렉터는 사이트 업데이트로 변경될 수 있습니다
                    # 변경됐다면 브라우저 개발자도구 > Elements에서 확인하세요
                    try:
                        await page.wait_for_selector(
                            "article, [data-testid*='article'], .flea-market-article-item",
                            timeout=10_000,
                        )
                    except PlaywrightTimeout:
                        logger.warning("[당근마켓] 검색 결과 없음 또는 로딩 실패")
                        return []

                    # 모든 article 요소 가져오기
                    articles = await page.query_selector_all("article")
                    logger.info(f"[당근마켓] {len(articles)}개 항목 발견")

                    for article in articles[: self.MAX_RESULTS]:
                        try:
                            listing = await self._parse_article(article, location)
                            if listing:
                                # 가격 필터 적용
                                if max_price and listing.price:
                                    price_num = self.extract_price_number(listing.price)
                                    if price_num and price_num > max_price:
                                        continue
                                listings.append(listing)
                        except Exception as e:
                            logger.debug(f"[당근마켓] 항목 파싱 오류: {e}")
                            continue

                finally:
                    await browser.close()

        except Exception as e:
            logger.error(f"[당근마켓] 스크래핑 실패: {e}")
            raise

        logger.info(f"[당근마켓] {len(listings)}개 결과 반환")
        return listings

    async def _parse_article(self, article, fallback_location: str) -> Optional[Listing]:
        """
        article 엘리먼트에서 매물 정보를 추출합니다.

        당근마켓 HTML 구조:
          <article>
            <a href="/articles/...">
              <img src="...">
              <strong>제목</strong>
              <span>지역 · 시간</span>
              <span>가격</span>
            </a>
          </article>

        ⚠️ 이 셀렉터들은 당근마켓 업데이트로 변경될 수 있습니다.
           변경 시 브라우저 개발자도구에서 실제 클래스명을 확인하고 수정하세요.
        """
        # 링크 추출
        link_el = await article.query_selector("a[href]")
        if not link_el:
            return None

        href = await link_el.get_attribute("href")
        if not href:
            return None

        # 상대 경로를 절대 경로로 변환
        full_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href

        # 제목 추출 (strong 또는 h3 태그 우선)
        title_el = await article.query_selector("strong, h3, [class*='title']")
        title = (await title_el.inner_text()).strip() if title_el else None
        if not title:
            return None

        # 가격 추출
        price_el = await article.query_selector("[class*='price'], [class*='Price']")
        price = (await price_el.inner_text()).strip() if price_el else None

        # 지역/시간 정보 추출 (보통 "마포구 · 3시간 전" 형태)
        location_el = await article.query_selector(
            "[class*='location'], [class*='region'], [class*='area']"
        )
        raw_location = (
            (await location_el.inner_text()).strip() if location_el else fallback_location
        )
        # "마포구 · 3시간 전" → "마포구" 만 추출
        location_clean = raw_location.split("·")[0].strip() if raw_location else fallback_location

        # 썸네일 이미지
        img_el = await article.query_selector("img")
        image_url = await img_el.get_attribute("src") if img_el else None

        return Listing(
            title=title,
            url=full_url,
            source=self.SOURCE_NAME,
            price=price,
            location=location_clean,
            image_url=image_url,
        )
