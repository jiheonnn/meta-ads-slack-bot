# Meta Ads Slack Reporter

Meta(Facebook) 광고 성과를 Slack으로 자동 리포팅하는 Vercel Serverless Function입니다.

## 🚀 주요 기능

- **자동 리포팅**: 매일 정해진 시간에 광고 성과 자동 전송
- **종합 분석**: 계정 전체 성과, 소재별 성과, 주간 비교 제공
- **인사이트 생성**: ROAS, CTR, 빈도 기반 자동 인사이트
- **TypeScript 기반**: 타입 안정성과 더 나은 개발 경험

## 📅 스케줄

크론잡으로 다음 시간에 자동 실행됩니다:
- 매일 오전 3시 (UTC) = 한국시간 정오 12시
- 매일 오후 2시 59분 (UTC) = 한국시간 오후 11시 59분

## 🛠 설치 및 설정

### 1. 의존성 설치

```bash
npm install
```

### 2. 환경변수 설정

`.env` 파일을 생성하고 다음 변수를 설정하세요:

```env
SLACK_WEBHOOK_URL=your_slack_webhook_url
META_ACCESS_TOKEN=your_meta_access_token
META_AD_ACCOUNT_ID=your_ad_account_id
```

- **SLACK_WEBHOOK_URL**: Slack Incoming Webhook URL
- **META_ACCESS_TOKEN**: Meta API 액세스 토큰
- **META_AD_ACCOUNT_ID**: Meta 광고 계정 ID (act_ 제외)

### 3. 로컬 테스트

```bash
npm test
```

## 📦 Vercel 배포

### 1. Vercel CLI 설치

```bash
npm i -g vercel
```

### 2. 프로젝트 연결 및 배포

```bash
vercel
```

### 3. 환경변수 설정

Vercel 대시보드에서 프로젝트 설정 > Environment Variables에서 다음 변수 추가:
- `SLACK_WEBHOOK_URL`
- `META_ACCESS_TOKEN`
- `META_AD_ACCOUNT_ID`

### 4. 프로덕션 배포

```bash
vercel --prod
```

## 📂 프로젝트 구조

```
slackbot/
├── api/
│   └── meta_report_advanced.ts    # 메인 서버리스 함수
├── test/
│   └── test_meta_report.ts        # 로컬 테스트 스크립트
├── types/
│   └── environment.d.ts           # 환경변수 타입 정의
├── vercel.json                    # Vercel 설정 및 크론잡
├── package.json                   # 프로젝트 설정
├── tsconfig.json                  # TypeScript 설정
└── .env.example                   # 환경변수 예시
```

## 🔄 Python에서 TypeScript로 마이그레이션

이 프로젝트는 원래 Python으로 작성되었으나 다음 이유로 TypeScript로 전환되었습니다:

1. **Vercel 호환성**: TypeScript/Node.js가 Vercel의 1급 시민
2. **안정성**: 더 성숙한 런타임과 풍부한 문서
3. **타입 안정성**: TypeScript의 정적 타입 시스템
4. **성능**: 더 빠른 콜드 스타트와 실행 속도

## 📊 리포트 내용

### 전체 성과
- 광고비, ROAS, 전환수, 전환 매출
- 도달, 빈도, CTR, CPM, CPC, CAC
- 랜딩페이지 전환율

### 주간 비교
- 이번 주 vs 지난 주 성과 비교
- 광고비, ROAS, 전환 변화율

### 소재별 성과
- 상위 15개 광고 소재의 개별 성과
- 소재명, 광고비, ROAS, CTR

### 자동 인사이트
- ROAS 기반 최적화 제안
- CTR 기반 크리에이티브 개선 제안
- 광고 피로도 경고

## 🐛 문제 해결

### 크론잡이 실행되지 않는 경우

1. Vercel 대시보드에서 Functions 탭 확인
2. 환경변수가 모두 설정되었는지 확인
3. Vercel 로그 확인: `vercel logs`

### Meta API 오류

1. 액세스 토큰이 유효한지 확인
2. 광고 계정 ID가 올바른지 확인
3. Meta API 권한 확인

### Slack 메시지가 오지 않는 경우

1. Webhook URL이 올바른지 확인
2. Slack 워크스페이스의 Webhook 설정 확인

## 📝 라이선스

ISC