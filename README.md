# 아임웹 주문 정보 조회 시스템

## 🎯 목적
athlogic.kr (아임웹 쇼핑몰)에서 "다이어트의 정석", "벌크업의 정석" 상품을 구매한 고객 정보를 자동으로 조회하는 시스템

## 📋 작동 방식
1. 아임웹 OAuth 2.0을 사용하여 인증
2. 주문 API를 통해 구매자 정보 조회
3. CSV 파일로 구매자 목록 저장

## 🔧 필요 조건
- Python 3.6+
- 아임웹 개발자센터 앱 등록
- OAuth 앱 정보:
  - Client ID: `7241ca65-cfcf-4e24-aa94-12eee45a9f7e`
  - Client Secret: `cf1e8fc3-5d8b-41fc-823f-79ba9ff17921`
  - Site Code: `S202407313af6560dd5f06`

## 📦 필요 패키지 설치
```bash
pip3 install requests schedule
```

## 🚀 사용 방법

### 1단계: 최초 인증 (1회만 필요)
```bash
python3 get_first_token.py
```
- 브라우저에서 아임웹 로그인
- 권한 승인
- 리다이렉트된 URL의 `code=XXXXX` 값 복사
- 터미널에 붙여넣기

### 2단계: 주문 조회
```bash
python3 get_orders_oauth_correct.py
```
- 최근 7일간의 주문 조회
- "다이어트의 정석", "벌크업의 정석" 구매자 필터링
- CSV 파일로 저장 옵션

## 📁 파일 설명
- `get_first_token.py`: OAuth 인증 코드를 받아 토큰 발급
- `oauth_token_manager.py`: 토큰 관리 및 자동 갱신
- `get_orders_oauth_correct.py`: 주문 조회 및 구매자 정보 추출
- `imweb_tokens.json`: 발급받은 토큰 저장 (자동 생성)

## ⚠️ 주의사항
1. **아임웹 개발자센터 설정 필요**:
   - 앱과 사이트 연동 (테스트 사이트로 등록)
   - OAuth 권한 설정: `site-info:write order:read`
   - Redirect URI: `https://petebaek0712000.imweb.me/`

2. **토큰 만료**:
   - Access Token: 2시간
   - Refresh Token: 90일
   - 자동 갱신되지만, 90일마다 재인증 필요

## 🔍 문제 해결

### "연동되지 않은 사이트" 오류
→ 아임웹 개발자센터에서 앱-사이트 연동 필요

### "Invalid redirect uri" 오류
→ 개발자센터의 Redirect URI 설정 확인

### 주문이 조회되지 않음
→ 날짜 범위 확인, 상품명 확인

## 📊 출력 예시
```
🎯 구매자 발견!
   이름: 홍길동
   전화번호: 010-1234-5678
   상품: 다이어트의 정석 x 1개
   주문일: 2025-07-22T10:30:00.000Z
   주문상태: PAYMENT_COMPLETE
```

## 🔐 보안
- `imweb_tokens.json` 파일은 절대 공유하지 마세요
- Client Secret은 안전하게 보관하세요