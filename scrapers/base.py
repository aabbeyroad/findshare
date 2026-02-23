"""
base.py — 모든 스크래퍼의 공통 기반

왜 이 구조를 선택했나?
  - 모든 사이트 스크래퍼가 동일한 형태(Listing)로 데이터를 반환하게 해서
    나중에 사이트가 추가되어도 메인 앱 코드를 고칠 필요가 없습니다.
  - 추상 클래스(BaseScraper)를 상속받아 각 사이트별로 search() 메서드만 구현하면 됩니다.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from abc import ABC, abstractmethod
import re


@dataclass
class Listing:
    """
    표준화된 매물 정보

    어느 사이트에서 왔든 같은 구조로 저장합니다.
    이렇게 하면 프론트엔드에서 사이트를 구분하지 않고 동일하게 처리할 수 있어요.
    """
    title: str            # 게시글 제목
    url: str              # 원문 링크
    source: str           # 출처 사이트명 (예: "당근마켓", "피터팬")
    price: Optional[str] = None          # 가격 (문자열, 예: "2,000만원")
    location: Optional[str] = None       # 지역 (예: "서울 마포구")
    description: Optional[str] = None    # 게시글 본문 요약
    image_url: Optional[str] = None      # 썸네일 이미지 URL
    posted_at: Optional[str] = None      # 게시 일시

    def to_dict(self) -> dict:
        """JSON 직렬화용 딕셔너리 변환"""
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "price": self.price,
            "location": self.location,
            "description": self.description,
            "image_url": self.image_url,
            "posted_at": self.posted_at,
        }


class BaseScraper(ABC):
    """
    모든 사이트 스크래퍼의 추상 기반 클래스

    새 사이트를 추가하려면:
    1. 이 클래스를 상속받는 새 파일을 scrapers/ 폴더에 만들기
    2. search() 메서드를 구현하기
    3. app.py의 SCRAPERS 딕셔너리에 추가하기
    """

    @abstractmethod
    async def search(
        self,
        keyword: str,
        location: str = "",
        max_price: Optional[int] = None,
    ) -> List[Listing]:
        """
        주어진 조건으로 매물을 검색합니다.

        Args:
            keyword:   검색 키워드 (예: "쉐어하우스 양도")
            location:  지역 필터 (예: "서울 마포구")
            max_price: 최대 가격 (원 단위, 예: 30_000_000)

        Returns:
            Listing 객체 리스트
        """
        pass

    @staticmethod
    def extract_price_number(price_str: str) -> Optional[int]:
        """
        가격 문자열에서 정수값을 추출합니다.
        예: "2,000만원" → 20_000_000
            "보증금 500 / 월세 50" → 500 (첫 번째 숫자만)
        """
        if not price_str:
            return None

        # 쉼표 제거 후 숫자 추출
        clean = price_str.replace(",", "")
        numbers = re.findall(r"\d+", clean)

        if not numbers:
            return None

        num = int(numbers[0])

        # 단위 처리
        if "억" in price_str:
            return num * 100_000_000
        if "만" in price_str:
            return num * 10_000

        return num
