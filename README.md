# Meta Ads Slack Reporter

메타(Facebook) 광고 성과를 슬랙으로 자동 리포팅하는 서버리스 함수입니다.

## 기능

- 매일 12시, 23시 59분에 광고 성과 자동 리포트
- ROAS 모니터링 및 알림
- 광고비, 노출, 클릭, 전환 등 주요 지표 추적

## 배포 방법

### 1. Vercel에 배포

1. 이 저장소를 Fork 또는 Clone
2. [Vercel](https://vercel.com)에 로그인
3. 새 프로젝트 생성 후 이 저장소 연결
4. 환경 변수 설정:
   - `SLACK_WEBHOOK_URL`: 슬랙 웹훅 URL
   - `META_ACCESS_TOKEN`: 메타 액세스 토큰
   - `META_AD_ACCOUNT_ID`: 메타 광고 계정 ID
5. 배포

### 2. 환경 변수 설정

`.env.example` 파일을 참고하여 필요한 환경 변수를 설정하세요.

## 스케줄 설정

`vercel.json` 파일의 crons 섹션에서 리포트 시간을 조정할 수 있습니다.
- 현재 설정: 매일 12:00 (KST), 23:59 (KST)

## 라이선스

MIT