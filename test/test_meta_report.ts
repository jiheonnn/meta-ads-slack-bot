/**
 * 테스트 스크립트 - TypeScript 버전
 */

import * as dotenv from 'dotenv';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

// .env 파일 로드 (있는 경우)
dotenv.config();

// 테스트 환경 변수 (하드코딩된 값 또는 환경변수에서 가져오기)
const SLACK_WEBHOOK_URL = process.env.SLACK_WEBHOOK_URL || "https://hooks.slack.com/services/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";
const META_ACCESS_TOKEN = process.env.META_ACCESS_TOKEN || "EAAKUZAdQJpPgBPIgmlSwOP35imYOYzJGY9PVBAowJZA55r5MWSvpaHmQxwJNYboVJ3f00VBlZAlVO3JhhLQ8AXkgoTt9S6MVZCPXHa9mzaXF9G8dnbmJSl7sQzb97gmiDZA8LsZBuQYnH1WDd64Qwvclm5zcZAelHLZCiuNtAWI7URjpC07p9l7oLCMs1ZB8GKr8QdZCYDY7y9h7EZBMUFq0tsZA";
const META_AD_ACCOUNT_ID = process.env.META_AD_ACCOUNT_ID || "360590366471346";

// 환경변수 설정
process.env.SLACK_WEBHOOK_URL = SLACK_WEBHOOK_URL;
process.env.META_ACCESS_TOKEN = META_ACCESS_TOKEN;
process.env.META_AD_ACCOUNT_ID = META_AD_ACCOUNT_ID;

// handler 함수 import
import handler from '../api/meta_report_advanced';

// 모의 Request와 Response 객체 생성
class MockRequest {
  method: string = 'GET';
  query: any = {};
  cookies: any = {};
  body: any = null;
  env: any = {};
}

class MockResponse {
  statusCode: number = 200;
  headers: { [key: string]: string } = {};
  body: any = null;

  status(code: number) {
    this.statusCode = code;
    return this;
  }

  json(data: any) {
    this.headers['Content-Type'] = 'application/json';
    this.body = data;
    console.log(`Response Status: ${this.statusCode}`);
    console.log('Response Body:', JSON.stringify(data, null, 2));
    return this;
  }
}

async function main() {
  console.log("🚀 Meta 광고 리포트 테스트 - TypeScript 버전");
  console.log("=" .repeat(50));
  
  // 환경변수 확인
  console.log("\n📋 환경변수 확인:");
  console.log(`✅ SLACK_WEBHOOK_URL: ${SLACK_WEBHOOK_URL ? '설정됨' : '❌ 없음'}`);
  console.log(`✅ META_ACCESS_TOKEN: ${META_ACCESS_TOKEN ? '설정됨' : '❌ 없음'}`);
  console.log(`✅ META_AD_ACCOUNT_ID: ${META_AD_ACCOUNT_ID ? '설정됨' : '❌ 없음'}`);
  
  try {
    // 모의 요청/응답 객체 생성
    const req = new MockRequest() as any;
    const res = new MockResponse() as any;
    
    console.log("\n📊 핸들러 실행 중...");
    
    // handler 함수 실행
    await handler(req, res);
    
    // 결과 확인
    if (res.statusCode === 200) {
      console.log("\n✅ 테스트 성공! 슬랙을 확인하세요.");
    } else {
      console.log(`\n❌ 테스트 실패: Status ${res.statusCode}`);
    }
  } catch (error) {
    console.error("\n❌ 테스트 중 오류 발생:", error);
  }
}

// 스크립트 실행
main().catch(console.error);