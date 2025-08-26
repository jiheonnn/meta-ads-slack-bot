import * as dotenv from 'dotenv';
import * as path from 'path';

// Load environment variables
dotenv.config({ path: path.join(__dirname, '..', '.env') });

/**
 * Test script for Ad Alert System
 */
async function testAdAlert() {
  console.log('🚨 광고 경고 알람 시스템 테스트');
  console.log('==================================================\n');

  // Check environment variables
  console.log('📋 환경변수 확인:');
  const slackWebhookUrl = process.env.SLACK_WEBHOOK_URL;
  const metaAccessToken = process.env.META_ACCESS_TOKEN;
  const metaAdAccountId = process.env.META_AD_ACCOUNT_ID;

  if (!slackWebhookUrl) {
    console.error('❌ SLACK_WEBHOOK_URL이 설정되지 않았습니다.');
    return;
  }
  console.log('✅ SLACK_WEBHOOK_URL: 설정됨');

  if (!metaAccessToken) {
    console.error('❌ META_ACCESS_TOKEN이 설정되지 않았습니다.');
    return;
  }
  console.log('✅ META_ACCESS_TOKEN: 설정됨');

  if (!metaAdAccountId) {
    console.error('❌ META_AD_ACCOUNT_ID가 설정되지 않았습니다.');
    return;
  }
  console.log(`✅ META_AD_ACCOUNT_ID: ${metaAdAccountId}\n`);

  // Test the handler directly
  console.log('📊 광고 경고 알람 핸들러 실행 중...\n');

  try {
    // Import and execute the handler
    const handler = require('../api/ad_alert').default;
    
    // Mock request and response objects
    const mockReq: any = {
      method: 'GET',
      headers: {},
      query: {},
      body: null
    };

    const mockRes: any = {
      status: (code: number) => {
        console.log(`Response Status: ${code}`);
        return {
          json: (data: any) => {
            console.log('Response Body:', JSON.stringify(data, null, 2));
            return data;
          }
        };
      }
    };

    // Execute the handler
    await handler(mockReq, mockRes);

    console.log('\n✅ 테스트 완료! 슬랙 메시지를 확인하세요.');
    console.log('   - 전체 요약 메시지');
    console.log('   - 문제가 있는 광고별 개별 경고 메시지');

  } catch (error) {
    console.error('\n❌ 테스트 실패:', error);
    if (error instanceof Error) {
      console.error('Error details:', error.message);
      console.error('Stack trace:', error.stack);
    }
  }
}

// Quick test for date range
function testDateRange() {
  console.log('\n📅 날짜 범위 테스트:');
  const today = new Date();
  const fourDaysAgo = new Date(today);
  fourDaysAgo.setDate(today.getDate() - 3);

  console.log(`Today: ${today.toISOString().split('T')[0]}`);
  console.log(`4 days ago: ${fourDaysAgo.toISOString().split('T')[0]}`);
  console.log('이 기간의 일별 데이터를 수집합니다.\n');
}

// Test alert level calculation
function testAlertLevels() {
  console.log('\n🎯 경고 레벨 기준:');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('🟡 레벨 1 (주의):');
  console.log('   - CTR 2일 연속 하락');
  console.log('   - CPC 2일 연속 상승');
  console.log('   - CAC 2일 연속 상승');
  console.log('   - ROAS < 2.0');
  
  console.log('\n🟠 레벨 2 (위험):');
  console.log('   - CTR 3일 연속 하락');
  console.log('   - CPC 3일 연속 상승');
  console.log('   - ROAS < 1.5');
  
  console.log('\n🔴 레벨 3 (긴급):');
  console.log('   - CTR·CPC·CAC 모두 3일 연속 악화');
  console.log('   - AND ROAS ≤ 1.2');
  console.log('   - 두 조건 모두 충족 시에만 긴급');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
}

// Main execution
async function main() {
  testDateRange();
  testAlertLevels();
  await testAdAlert();
}

main().catch(console.error);