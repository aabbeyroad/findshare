"""
naver_cafe.py — 네이버 카페 통합 검색 스크래퍼

왜 네이버 통합 카페 검색을 사용하나?
  네이버 카페는 개별 카페마다 로그인 요구 / 봇 차단이 강합니다.
  대신 네이버 '카페글 검색' (search.naver.com?where=article)은
  로그인 없이도 여러 카페의 게시글 목록과 링크를 함께 보여줍니다.

  → 피터팬 카페, 자취방 구하기 카페, 쉐어하우스 관련 카페 등
    여러 커뮤니티를 한 번에 커버할 수 있습니다.

검색 URL 형태:
  https://search.naver.com/search.naver
    ?where=article          ← 카페글 검색
    &query=쉐어하우스+양도
    &sm=tab_opt
    &nso=so:dd,p:all,a:all  ← 최신순 정렬

특정 카페만 검색하려면:
  TARGET_CAFES 리스트에 카페 ID를 추가하면 됩니다.
  현재는 모든 카페를 대상으로 검색합니다.
"""

import logging
from typing import Optional, List
from urllib.parse import urlencode, quote

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from .base import BaseScraper, Listing

logger = logging.getLogger(__name__)


class NaverCafeScraper(BaseScraper):
    """
    네이버 카페 통합 검색 스크래퍼

    아래 카페들의 게시글을 포함해서 검색합니다:
    - 피터팬의 좋은방 구하기 (cafe.naver.com/peterpan)
    - 자취생활 (cafe.naver.com/zimmer)
    - 그 외 쉐어하우스/부동산 관련 카페
    """

    SEARCH_URL = "https://search.naver.com/search.naver"
    SOURCE_NAME = "네이버 카페"
    MAX_RESULTS = 20

    # 특정 카페만 검색하고 싶다면 카페 ID를 여기에 추가하세요.
    # 비워두면 네이버 전체 카페를 검색합니다.
    # 예: ["peterpan", "zimmer"]
    TARGET_CAFES: List[str] = []

    async def search(
        self,
        keyword: str,
        location: str = "",
        max_price: Optional[int] = None,
    ) -> List[Listing]:
        """
        네이버 카페 통합 검색으로 게시글을 찾습니다.

        Args:
            keyword:   검색 키워드 (예: "쉐어하우스 양도")
            location:  지역 필터 — 키워드에 포함시켜 검색
            max_price: 가격 필터 (카페 검색은 가격 추출이 어려워 소프트 필터)
        """
        search_query = f"{keyword} {location}".strip() if location else keyword
        logger.info(f"[네이버 카페] 검색 시작: {search_query}")

        # 최신순 정렬로 카페글 검색 URL 구성
        params = {
            "where": "article",          # 카페글 탭
            "query": search_query,
            "sm": "tab_opt",
            "nso": "so:dd,p:all,a:all",  # 최신순(dd), 전체 기간(all)
        }
        url = f"{self.SEARCH_URL}?{urlencode(params, quote_via=quote)}"

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
                    # 네이버는 viewport 크기도 체크하는 경우가 있음
                    viewport={"width": 1280, "height": 800},
                )

                page = await context.new_page()

                try:
                    await page.goto(url, wait_until="networkidle", timeout=30_000)

                    # 검색 결과 로딩 대기
                    # 네이버 카페 검색 결과 컨테이너 셀렉터
                    result_loaded = False
                    for selector in [
                        ".cafe_area",            # 카페 검색 결과 영역
                        ".lst_total",            # 전체 목록
                        ".total_area",           # 통합 결과 영역
                        "ul.lst_type",           # 목록 타입
                        "[class*='cafe']",       # 카페 관련 요소
                        "li[id*='a_']",          # 개별 결과 항목
                    ]:
                        try:
                            await page.wait_for_selector(selector, timeout=5_000)
                            result_loaded = True
                            logger.debug(f"[네이버 카페] 셀렉터 '{selector}' 발견")
                            break
                        except PlaywrightTimeout:
                            continue

                    if not result_loaded:
                        logger.warning("[네이버 카페] 검색 결과를 찾지 못했습니다")
                        return []

                    # 결과 항목 추출
                    # 네이버 검색 결과의 링크는 대부분 .api_txt_lines 클래스
                    items = await page.query_selector_all(
                        "li[id*='a_cafe'], li.bx, .total_wrap, .cafe_lst li"
                    )

                    # 대체 셀렉터: 카페 링크 포함된 항목들
                    if not items:
                        items = await page.query_selector_all(
                            "li:has(a[href*='cafe.naver.com'])"
                        )

                    logger.info(f"[네이버 카페] {len(items)}개 항목 발견")

                    seen_urls: set = set()

                    for item in items[: self.MAX_RESULTS * 2]:  # 중복 제거 여유분
                        try:
                            listing = await self._parse_item(item, fallback_location=location)
                            if not listing:
                                continue

                            # 이미 추가한 URL 건너뜀
                            if listing.url in seen_urls:
                                continue

                            # 특정 카페만 필터링 (TARGET_CAFES가 설정된 경우)
                            if self.TARGET_CAFES:
                                if not any(
                                    cafe_id in listing.url
                                    for cafe_id in self.TARGET_CAFES
                                ):
                                    continue

                            seen_urls.add(listing.url)
                            listings.append(listing)

                            if len(listings) >= self.MAX_RESULTS:
                                break

                        except Exception as e:
                            logger.debug(f"[네이버 카페] 항목 파싱 오류: {e}")
                            continue

                finally:
                    await browser.close()

        except Exception as e:
            logger.error(f"[네이버 카페] 스크래핑 실패: {e}")
            raise

        logger.info(f"[네이버 카페] {len(listings)}개 결과 반환")
        return listings

    async def _parse_item(self, item, fallback_location: str) -> Optional[Listing]:
        """
        네이버 카페 검색 결과 항목을 파싱합니다.

        네이버 카페 검색 결과 HTML 구조 (2024년 기준):
          <li id="a_cafe_1" class="bx">
            <div class="total_wrap">
              <a class="api_txt_lines" href="https://cafe.naver.com/...">
                제목 텍스트
              </a>
              <div class="total_dsc_wrap">
                <span class="dsc">게시글 내용 일부...</span>
              </div>
              <div class="source_box">
                <a class="cafe_name">카페 이름</a>
                <span class="date">2시간 전</span>
              </div>
            </div>
          </li>

        ⚠️ 네이버는 자주 HTML 구조를 변경합니다.
           검색이 안 된다면 개발자도구에서 실제 구조를 확인하고 수정하세요.
        """
        # ── 제목 및 링크 추출 ──
        # 네이버 카페 결과의 주요 링크 클래스
        title_link = None
        for selector in [
            "a.api_txt_lines",
            "a[href*='cafe.naver.com']",
            "a.link_tit",
            "strong a",
            "h3 a",
            "a.title",
        ]:
            title_link = await item.query_selector(selector)
            if title_link:
                break

        if not title_link:
            return None

        href = await title_link.get_attribute("href")
        if not href or "cafe.naver.com" not in href:
            return None

        title_raw = await title_link.inner_text()
        title = title_raw.strip()
        if not title or len(title) < 3:
            return None

        # ── 카페명 추출 ──
        cafe_name = None
        for selector in [
            ".cafe_name",
            ".source_cafe",
            "a[href*='cafe.naver.com/'][class*='name']",
            ".sub_txt",
            ".source_box a",
        ]:
            cafe_el = await item.query_selector(selector)
            if cafe_el:
                cafe_name = (await cafe_el.inner_text()).strip()
                break

        # ── 게시 날짜 추출 ──
        posted_at = None
        for selector in [".date", ".time", "span.txt_num", ".sub_time"]:
            date_el = await item.query_selector(selector)
            if date_el:
                posted_at = (await date_el.inner_text()).strip()
                break

        # ── 본문 요약 추출 ──
        description = None
        for selector in [".dsc", ".total_dsc", ".desc", ".api_txt_lines + *"]:
            desc_el = await item.query_selector(selector)
            if desc_el:
                description = (await desc_el.inner_text()).strip()
                if description:
                    break

        # ── 출처 표시: "네이버 카페 > 카페명" 형태 ──
        source_label = f"네이버 카페"
        if cafe_name:
            source_label = f"네이버 카페 › {cafe_name}"

        return Listing(
            title=title,
            url=href,
            source=source_label,
            location=fallback_location or None,
            description=description,
            posted_at=posted_at,
        )
