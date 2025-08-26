import * as dotenv from 'dotenv';
import * as path from 'path';

// Load environment variables
dotenv.config({ path: path.join(__dirname, '..', '.env') });

async function testSlackWebhook() {
  const webhookUrl = process.env.SLACK_WEBHOOK_URL;
  
  if (!webhookUrl) {
    console.error('❌ SLACK_WEBHOOK_URL이 설정되지 않았습니다.');
    return;
  }

  console.log('🔍 Slack Webhook URL 테스트 중...');
  console.log(`URL: ${webhookUrl.substring(0, 50)}...`);

  const testMessage = {
    blocks: [
      {
        type: "header",
        text: {
          type: "plain_text",
          text: "🧪 Webhook 테스트",
          emoji: true
        }
      },
      {
        type: "section",
        text: {
          type: "mrkdwn",
          text: `테스트 시간: ${new Date().toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' })}`
        }
      }
    ]
  };

  try {
    const response = await fetch(webhookUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(testMessage)
    });

    console.log(`📡 응답 상태: ${response.status} ${response.statusText}`);
    
    const responseText = await response.text();
    console.log(`📝 응답 내용: ${responseText}`);

    if (response.status === 200) {
      console.log('✅ Slack Webhook이 정상적으로 작동합니다!');
    } else if (response.status === 403) {
      console.error('❌ 403 Forbidden - Webhook URL이 잘못되었거나 만료되었습니다.');
    } else {
      console.error(`❌ 예상치 못한 응답: ${response.status}`);
    }
  } catch (error) {
    console.error('❌ 요청 실패:', error);
  }
}

testSlackWebhook();