# FindShare 배포 가이드

웹으로 접근 가능하게 온라인 배포하는 방법입니다.

---

## 방법 1: Railway.app (추천 - 가장 간단)

**Railway는:**
- ✅ 무료 $5/월 크레딧 제공
- ✅ Docker 자동 지원
- ✅ 환경 변수 관리 UI 제공
- ✅ GitHub 자동 배포 가능
- ✅ 배포 후 공개 URL 받음

### 1단계: 준비

```bash
# 1. Railway 계정 생성 (GitHub 연동 가능)
# https://railway.app

# 2. 이 레포를 GitHub에 푸시 (아직 안 했다면)
git push origin claude/sharehouse-listing-finder-YYsZh
```

### 2단계: Railway.app에서 배포

1. [railway.app](https://railway.app) 접속
2. **"New Project"** 클릭
3. **"Deploy from GitHub"** 선택
4. 이 레포 선택 (`aabbeyroad/findshare`)
5. **"Deploy"** 클릭

### 3단계: 환경 변수 설정 (선택사항)

Railway 프로젝트 → Variables 탭:
```
PORT=8000
```

### 4단계: 배포 완료!

Railway가 자동으로:
1. Dockerfile 인식
2. Playwright 브라우저 설치
3. 앱 빌드 및 실행
4. 공개 URL 생성 (예: `findshare-prod.up.railway.app`)

배포 후 이 URL로 접근 가능합니다!

---

## 방법 2: Render.com (무료, 간단)

1. [render.com](https://render.com) 접속
2. **"New +"** → **"Web Service"**
3. GitHub 연동 후 레포 선택
4. 설정:
   - **Name**: `findshare` (또는 원하는 이름)
   - **Environment**: Docker
   - **Build Command**: 비워두기 (자동)
   - **Start Command**: 비워두기 (Dockerfile 사용)
   - **Plan**: Free
5. **"Create Web Service"** 클릭

약 5-10분 후 배포됨. 공개 URL을 받습니다.

---

## 방법 3: Heroku (유료)

Heroku는 2022년부터 무료 tier가 폐지되어 $7/월 이상 필요합니다.
따라서 Railway 또는 Render를 추천합니다.

---

## 방법 4: 로컬 네트워크 공유 (같은 WiFi)

온라인 배포 없이 같은 WiFi에서만 접근하려면:

### 1단계: 로컬 IP 확인

**Linux/Mac:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

**Windows (PowerShell):**
```powershell
ipconfig
```
→ IPv4 주소 확인 (예: `192.168.1.100`)

### 2단계: 앱 실행

```bash
python app.py
```

### 3단계: 다른 기기에서 접근

같은 WiFi의 다른 컴퓨터/스마트폰에서:
```
http://YOUR_IP:8000
```

예: `http://192.168.1.100:8000`

---

## 배포 후 주의사항

### Playwright 브라우저 다운로드

- Railway/Render에서 자동으로 설치됨
- 첫 배포 시 약 5-10분 소요 가능 (브라우저 다운로드)
- 로그에서 진행 상황 확인 가능

### 성능

- 첫 요청은 "콜드 스타트" (3-5초) 가능
- 이후 요청은 빠름

### 비용

- **Railway**: 무료 $5/월 크레딧 (충분함)
- **Render**: Free plan 있음 (30분 유휴 시 잠자기)

---

## 배포 문제 해결

### "Playwright 브라우저 설치 실패"

Dockerfile의 시스템 패키지 설치 부분 확인.
필요한 라이브러리가 모두 포함되어 있습니다.

### "포트 바인딩 오류"

Railway/Render에서 자동으로 포트 할당.
`PORT` 환경 변수가 올바르게 설정되었는지 확인.

### "메모리 부족"

Playwright 브라우저는 약 100-200MB 메모리 사용.
Railway 무료 tier는 512MB 제공 (충분함).

---

## 커스텀 도메인 연결 (선택사항)

Railway/Render 프로젝트에서:
1. **Settings** → **Custom Domain**
2. 자신의 도메인 입력
3. DNS 레코드 설정 (가이드 제공)

예를 들어 `findshare.yourcompany.com`으로 접근 가능하게 할 수 있습니다.

---

## 배포 후 모니터링

### Railway

- 프로젝트 → **Deployments** 탭에서 실시간 로그 확인
- **Metrics** 탭에서 CPU, 메모리 사용량 모니터링

### Render

- 프로젝트 페이지에서 **Logs** 확인
- **Metrics** 탭에서 성능 모니터링

---

## 다음 단계

배포 후 V2 기능 추가:
- 이메일 알림 (SendGrid)
- Google Sheets 연동
- 더 많은 사이트 추가 (직방, 다방 등)
