# Vercel로 FindShare 배포하기

Vercel을 사용하면 간단하게 FindShare를 웹에 배포할 수 있습니다.

---

## Vercel이란?

- ✅ Next.js, Python, Node.js 지원
- ✅ GitHub 자동 배포 (git push = 자동 배포)
- ✅ 무료 tier 제공 (넉넉함)
- ✅ 공개 URL 자동 생성
- ✅ 배포 시간 빠름 (2-3분)

---

## 단계별 배포 가이드

### 1단계: Vercel 계정 생성

1. [vercel.com](https://vercel.com) 접속
2. **"Sign Up"** 클릭
3. GitHub 계정으로 가입 (추천) 또는 이메일

### 2단계: GitHub에 푸시

현재 코드를 GitHub 레포에 푸시해야 합니다.

```bash
# 현재 branch 확인
git status

# 모든 변경 스테이지
git add .

# 커밋
git commit -m "feat: Vercel 배포 설정 추가"

# push
git push origin claude/sharehouse-listing-finder-YYsZh
```

또는 새 main branch에 푸시:
```bash
git checkout -b main
git push -u origin main
```

### 3단계: Vercel에서 배포

1. [vercel.com/dashboard](https://vercel.com/dashboard)에 로그인
2. **"Add New..."** → **"Project"**
3. **"Import Git Repository"** 선택
4. `aabbeyroad/findshare` 레포 검색 및 선택
5. **"Import"** 클릭

### 4단계: 프로젝트 설정

Vercel이 자동으로 설정을 감지하므로:
- **Framework**: Python 자동 감지
- **Python Version**: 3.11 (자동)
- **Build Command**: 자동 설정됨
- **Install Command**: 자동 설정됨

특별히 변경할 것 없음. **"Deploy"** 버튼 클릭!

### 5단계: 배포 완료!

Vercel이 자동으로:
1. Python 환경 세팅
2. Playwright 브라우저 설치
3. 앱 빌드 및 배포
4. **공개 URL** 생성

배포 완료 후 URL 형식:
```
https://findshare-[hash].vercel.app
```

---

## 배포 후 확인

### 1. 앱이 정상 동작하는지 확인

배포된 URL로 접속:
```
https://your-project.vercel.app
```

### 2. 검색 테스트

1. 검색 폼 입력
2. "양도 매물 검색" 버튼 클릭
3. 결과 확인

### 3. API 문서 확인 (선택)

```
https://your-project.vercel.app/docs
```

---

## 자동 배포 설정 (선택)

GitHub에 푸시하면 자동으로 배포됩니다:

```bash
# 로컬에서 수정
# ... 코드 변경 ...

# git에 푸시
git add .
git commit -m "fix: 버그 수정"
git push origin main

# ✅ Vercel에 자동으로 배포됨!
```

---

## 배포 로그 확인

배포 중에 문제가 있으면:

1. Vercel 대시보드 → 프로젝트 선택
2. **"Deployments"** 탭
3. 최신 배포 클릭
4. **"Logs"** 확인

주로 보이는 로그:
- Python 패키지 설치
- Playwright 브라우저 설치 (첫 배포 시 약 2-3분)
- 앱 시작

---

## 커스텀 도메인 연결 (선택)

본인의 도메인을 사용하려면:

1. Vercel 프로젝트 → **Settings**
2. **"Domains"** 탭
3. 도메인 입력
4. DNS 설정 가이드 따라 하기

예: `findshare.mycompany.com`으로 접근 가능

---

## 환경 변수 설정 (선택)

나중에 민감한 정보를 사용하려면:

1. Vercel 프로젝트 → **Settings**
2. **"Environment Variables"**
3. 변수 추가
4. 재배포

---

## 성능 최적화

### 첫 번째 요청 시간

- **콜드 스타트**: 처음 요청 시 3-5초 (Vercel 특성)
- **이후 요청**: 빠름 (0.5초 이내)

이는 정상입니다. Vercel Serverless의 특성입니다.

### 메모리 사용

Playwright는 약 200-300MB 메모리 사용.
Vercel 기본 제한: 1024MB → 충분합니다.

---

## 문제 해결

### "Playwright 설치 실패"

배포 로그에서 확인 가능. 보통 자동으로 해결됨.

재배포:
```
Vercel 대시보드 → Deployments → 최신 배포의 "..." → Redeploy
```

### "API 응답 없음"

1. 브라우저 개발자도구 (F12) 열기
2. **Network** 탭 확인
3. `/api/search` 요청 상태 확인

### "정적 파일 안 보임"

`public/` 폴더가 배포되었는지 확인:
1. Vercel 프로젝트 → **Files**
2. `public/index.html` 존재 확인

---

## 배포 후 추가 기능 개발

배포된 상태에서도 계속 개발 가능:

```bash
# 로컬에서 새 기능 추가
# ... 코드 작성 ...

# 테스트
python app.py

# 배포
git add .
git commit -m "feat: 새로운 기능"
git push origin main

# ✅ 자동 배포!
```

---

## V2 기능 추가 로드맵

- [ ] 이메일 알림 (SendGrid)
- [ ] Google Sheets 연동
- [ ] 직방, 다방 스크래퍼 추가
- [ ] 검색 조건 저장 기능
- [ ] 가격 이력 추적

---

## 지원

문제가 있으면:

- **Vercel 문서**: https://vercel.com/docs
- **Python 배포 가이드**: https://vercel.com/docs/functions/serverless-functions/runtimes/python

Happy deploying! 🚀
