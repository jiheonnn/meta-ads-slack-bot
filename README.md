# 🤖 아임웹 매출 자동 리포트 슬랙봇

완전 자동화된 매출 리포트 시스템 - 토큰 무한 갱신 지원

## ✨ 주요 기능

- 📊 **자동 매출 리포트**: 매일 12시, 23시 59분 슬랙 전송
- 💰 **정확한 매출 계산**: 실제 결제금액 기준 (할인 적용)
- 🔄 **완전 자동 토큰 관리**: 무한 갱신 (수동 작업 불필요)
- 📱 **실시간 알림**: 에러 발생시 즉시 슬랙 알림

## 🚀 빠른 시작

### 1. 최초 토큰 발급 (1회만)
```bash
python3 get_first_token.py
```

### 2. 봇 실행
```bash
python3 sales_bot.py
```

## 📁 파일 구조

```
├── sales_bot.py           # 메인 봇 (리팩토링됨)
├── oauth_token_manager.py # 토큰 관리
├── get_first_token.py     # 최초 인증
├── imweb_tokens.json      # 토큰 저장 (자동 생성)
├── requirements.txt       # 패키지 목록
└── Procfile              # 배포용
```

## ⏰ 자동화 스케줄

- **12:00**: 중간 매출 리포트
- **23:59**: 최종 매출 리포트  
- **월요일 09:00**: 토큰 상태 체크
- **매월 1일 03:00**: 토큰 자동 갱신

## 🔧 환경 설정

### 필요 패키지
```bash
pip install requests schedule
```

### 슬랙 웹훅 URL 설정
`sales_bot.py`에서 웹훅 URL을 자신의 것으로 변경하세요.

## 🚢 클라우드 배포

Railway, Render, Google Cloud 등에 배포하여 24/7 실행 가능

## 🔒 보안

- `imweb_tokens.json` 파일 보안 주의
- 프라이빗 레포지토리 사용 권장
- 환경변수로 민감 정보 관리