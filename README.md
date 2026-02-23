# FindShare — 쉐어하우스 양도 통합 검색

여러 사이트의 쉐어하우스 양도 게시글을 한 번에 검색하는 도구입니다.

**지원 사이트**: 당근마켓, 피터팬의 좋은방 구하기, 네이버 카페

---

## 🚀 온라인으로 배포하기

이미 완성된 앱입니다! 다양한 방법으로 무료 배포 가능합니다.

### 1️⃣ **Vercel로 배포 (가장 간단)**

**[VERCEL_DEPLOYMENT.md](./VERCEL_DEPLOYMENT.md)** 참고

```bash
# 1. GitHub에 푸시
git push origin main

# 2. Vercel에서 import (GitHub 연동)
# 3. 자동 배포 완료! (2-3분)
```

✨ **Vercel의 장점:**
- GitHub과 자동 연동 (push = 자동 배포)
- 무료 tier 넉넉함
- 빠른 배포 속도

---

### 2️⃣ **Railway.app 배포**

**[DEPLOYMENT.md](./DEPLOYMENT.md)** 참고 (상세 가이드 포함)

- Railway (Docker 기반, 무료 크레딧)
- Render.com (무료 옵션)
- 로컬 네트워크 공유

---

## 시작하기

### 1. Python 설치 확인 (3.10 이상 필요)
```bash
python --version
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. Playwright 브라우저 설치 (최초 1회만)
```bash
playwright install chromium
```
> Chromium 브라우저를 약 150MB 다운로드합니다. 당근마켓, 피터팬 같은 JS 기반 사이트를 사용하기 위해 필요합니다.

### 4. 앱 실행
```bash
python app.py
```

### 5. 브라우저에서 열기
```
http://localhost:8000
```

---

## 사용 방법

1. **키워드** 입력: "쉐어하우스 양도" (기본값) 또는 "쉐어하우스 인수", "공유주택 양도" 등
2. **지역** 선택: 전국 또는 원하는 지역
3. **최대 금액** 설정 (선택사항)
4. **사이트** 선택: 당근마켓, 피터팬
5. **검색하기** 클릭

---

## 프로젝트 구조

```
findshare/
├── app.py                  # 메인 서버 (FastAPI)
├── scrapers/
│   ├── base.py             # 공통 기반 클래스
│   ├── daangn.py           # 당근마켓 스크래퍼
│   └── peterpanz.py        # 피터팬 스크래퍼
├── static/
│   └── index.html          # 프론트엔드 UI
├── requirements.txt
└── README.md
```

---

## 새 사이트 추가하는 방법

1. `scrapers/` 폴더에 새 파일 생성 (예: `zigbang.py`)
2. `BaseScraper`를 상속받아 `search()` 메서드 구현
3. `app.py`의 `SCRAPERS` 딕셔너리에 추가
4. `static/index.html`의 사이트 체크박스에 추가

```python
# scrapers/zigbang.py 예시
from .base import BaseScraper, Listing

class ZigbangScraper(BaseScraper):
    async def search(self, keyword, location="", max_price=None):
        # 여기에 스크래핑 로직 작성
        return []
```

---

## 스크래퍼 셀렉터 업데이트 방법

사이트가 업데이트되어 스크래핑이 안 될 경우:

1. 브라우저에서 해당 사이트 접속
2. 개발자도구 열기 (F12)
3. Elements 탭에서 원하는 요소 확인
4. 해당 스크래퍼 파일의 셀렉터 수정

---

## 환경변수 (선택사항)

`.env` 파일을 만들어 설정 가능:
```
PORT=8000          # 서버 포트 (기본값: 8000)
```

---

## 버전 2에서 추가할 것들

- **알림 기능**: 새 양도 매물 발견 시 이메일/카카오톡 알림
- **검색 저장**: 자주 쓰는 검색 조건 저장
- **더 많은 사이트**: 직방, 네이버 카페, 부동산 커뮤니티 등
- **Google Sheets 연동**: 결과를 스프레드시트로 자동 저장
- **중복 제거**: 여러 사이트에 같은 게시글이 있을 경우 합치기
- **가격 이력**: 게시글 가격 변동 추적
