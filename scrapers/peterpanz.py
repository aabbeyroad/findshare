"""
peterpanz.py — 피터팬의 좋은방 구하기 스크래퍼

왜 Playwright로 전환했나?
  처음에는 httpx(일반 HTTP 요청)로 시도했지만 피터팬이 봇 차단(403 Forbidden)을 합니다.
  Playwright는 실제 Chrome 브라우저처럼 동작하기 때문에 봇 감지를 우회할 수 있습니다.

검색 URL 형태:
  https://www.peterpanz.com/find-home?keyword=쉐어하우스+양도
"""

import logging
import asyncio
from typing import Optional, List
from urllib.parse import urlencode

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from .base import BaseScraper, Listing

logger = logging.getLogger(__name__)


class PeterpanzScraper(BaseScraper):
    """피터팬의 좋은방 구하기 스크래퍼 (Playwright 기반)"""

    BASE_URL = "https://www.peterpanz.com"
    SOURCE_NAME = "피터팬"
    MAX_RESULTS = 20

    async def search(
        self,
        keyword: str,
        location: str = "",
        max_price: Optional[int] = None,
    ) -> List[Listing]:
        """
        피터팬에서 쉐어하우스 양도 게시글을 검색합니다.
        """
        search_keyword = f"{keyword} {location}".strip() if location else keyword
        params = {"keyword": search_keyword}
        url = f"{self.BASE_URL}/find-home?{urlencode(params)}"

        logger.info(f"[피터팬] 검색 시작: {search_keyword}")
        listings: List[Listing] = []

        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                context = await browser.new_context(
                    locale="ko-KR",
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                )

                page = await context.new_page()

                try:
                    await page.goto(url, wait_until="networkidle", timeout=30_000)

                    # 매물 목록이 나타날 때까지 대기
                    # 피터팬 셀렉터: 실제 구조에 맞게 여러 후보 시도
                    result_loaded = False
                    for selector in [
                        "li[class*='item']",
                        "div[class*='item']",
                        "article",
                        ".room-list",
                        "[class*='list']",
                    ]:
                        try:
                            await page.wait_for_selector(selector, timeout=5_000)
                            result_loaded = True
                            logger.debug(f"[피터팬] 셀렉터 '{selector}' 발견")
                            break
                        except PlaywrightTimeout:
                            continue

                    if not result_loaded:
                        logger.warning("[피터팬] 검색 결과 없음 또는 로딩 실패")
                        return []

                    # 페이지 내용 전체 가져오기
                    # 링크가 있는 항목 위주로 추출
                    items = await page.query_selector_all("a[href*='/rooms/'], a[href*='/find-home/']")

                    if not items:
                        # 더 넓은 범위로 시도
                        items = await page.query_selector_all("li a, article a")

                    logger.info(f"[피터팬] {len(items)}개 항목 발견")

                    seen_urls = set()  # 중복 제거

                    for item in items[: self.MAX_RESULTS]:
                        try:
                            listing = await self._parse_item(item, location)
                            if listing and listing.url not in seen_urls:
                                # 가격 필터
                                if max_price and listing.price:
                                    price_num = self.extract_price_number(listing.price)
                                    if price_num and price_num > max_price:
                                        continue
                                seen_urls.add(listing.url)
                                listings.append(listing)
                        except Exception as e:
                            logger.debug(f"[피터팬] 항목 파싱 오류: {e}")
                            continue

                finally:
                    await browser.close()

        except Exception as e:
            logger.error(f"[피터팬] 스크래핑 실패: {e}")
            raise

        logger.info(f"[피터팬] {len(listings)}개 결과 반환")
        return listings

    async def _parse_item(self, element, fallback_location: str) -> Optional[Listing]:
        """
        링크 엘리먼트에서 매물 정보를 추출합니다.

        피터팬 카드 구조 (예상):
          <a href="/rooms/12345">
            <img src="...">
            <p class="title">제목</p>
            <p class="price">월세 50/50</p>
            <p class="location">마포구</p>
          </a>
        """
        # URL
        href = await element.get_attribute("href")
        if not href:
            return None

        full_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href

        # 제목: 가장 긴 텍스트가 보통 제목
        title_el = await element.query_selector(
            "[class*='title'], h2, h3, strong, p"
        )
        title = None
        if title_el:
            title = (await title_el.inner_text()).strip()

        # 제목이 없거나 너무 짧으면 전체 텍스트에서 첫 줄 사용
        if not title or len(title) < 4:
            full_text = (await element.inner_text()).strip()
            if full_text:
                lines = [l.strip() for l in full_text.split("\n") if l.strip()]
                title = lines[0] if lines else None

        if not title:
            return None

        # 가격
        price_el = await element.query_selector("[class*='price'], [class*='Price']")
        price = (await price_el.inner_text()).strip() if price_el else None

        # 지역
        location_el = await element.query_selector(
            "[class*='location'], [class*='address'], [class*='area'], [class*='region']"
        )
        location = (
            (await location_el.inner_text()).strip()
            if location_el
            else fallback_location
        )

        # 이미지
        img_el = await element.query_selector("img")
        image_url = await img_el.get_attribute("src") if img_el else None

        return Listing(
            title=title,
            url=full_url,
            source=self.SOURCE_NAME,
            price=price,
            location=location,
            image_url=image_url,
        )
