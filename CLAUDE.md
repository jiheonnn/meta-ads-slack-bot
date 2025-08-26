# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Meta 광고 성과를 Slack으로 자동 리포팅하는 Vercel Serverless Function 프로젝트입니다. TypeScript로 작성되었으며, 크론잡을 통해 하루 2번 자동 실행됩니다.

## Commands

### Development
```bash
# 로컬 테스트 실행 (Meta API 호출 및 Slack 전송 테스트)
npm test

# Vercel 개발 서버 실행
npm run dev

# 프로덕션 배포
npm run deploy
```

### 환경변수 필수 설정
로컬 테스트를 위해 `.env` 파일에 다음 변수가 필요합니다:
- `SLACK_WEBHOOK_URL`: Slack Incoming Webhook URL
- `META_ACCESS_TOKEN`: Meta API 액세스 토큰  
- `META_AD_ACCOUNT_ID`: Meta 광고 계정 ID (act_ 제외)

## Architecture

### Core Structure
- **Serverless Function**: `/api/meta_report_advanced.ts`가 메인 엔드포인트로, Vercel의 서버리스 함수로 동작
- **Cron Jobs**: `vercel.json`에 정의된 2개의 크론잡 (UTC 3:00, 14:59 = KST 12:00, 23:59)
- **API Integration**: Meta Graph API v18.0을 사용하여 광고 데이터 수집, Slack Webhook으로 메시지 전송

### Key Components

#### MetaAdsManager Class (`api/meta_report_advanced.ts`)
- Meta API와의 모든 통신을 담당하는 핵심 클래스
- 계정 전체 성과, 광고세트별 성과, 광고별 성과 데이터 수집
- 주간 비교 분석 및 인사이트 생성 기능 포함

#### SlackReporter Class (`api/meta_report_advanced.ts`)  
- Slack 메시지 포맷팅 및 전송 담당
- Block Kit을 사용한 구조화된 메시지 생성
- 이모지 활용한 시각적 인디케이터 제공

### Data Flow
1. Vercel 크론잡 또는 수동 호출로 함수 트리거
2. MetaAdsManager가 Meta API에서 광고 데이터 수집
3. 데이터 분석 및 인사이트 생성
4. SlackReporter가 포맷팅하여 Slack 전송

### Important Notes
- **타입 안정성**: TypeScript의 엄격한 타입 체크 활성화 (`strict: true`)
- **에러 처리**: 각 API 호출마다 try-catch로 에러 처리, 실패 시 null 반환
- **데이터 파싱**: Meta API 응답의 문자열 값들을 숫자로 변환하는 로직 포함
- **광고 필터링**: 활성 상태(`ACTIVE`)인 광고만 수집