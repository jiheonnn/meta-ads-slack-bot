"""
통합 리포트 테스트 스크립트
매출 + Meta 광고 성과 통합 리포트를 슬랙에 전송해서 테스트
"""

from sales_bot import SalesBot

def test_combined_report():
    """통합 리포트 테스트"""
    
    SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"
    META_ACCESS_TOKEN = "EAAKUZAdQJpPgBPEc9KSGZAFtP2P9DUTrAZCDT68KKqwxFmHVZAZCQlLepisdV9aWbN6fHft0b3oO1NoEqZBCoFr5fSQVuGNGwETNQ3Xukys6q3SUZC8aOj2u2CypBnsHRQJGec28N2omBz9vSRqh25qxfB5JcCaXaPZAZAudrd9QrU2pgQ7ihKlEsy7cbHHrbeQ9wxoE7XpjX50y3dNxHaNkbc7R89aZCDC3fAInbZCeWctkNWybgwAxFiJ"
    META_AD_ACCOUNT_ID = "360590366471346"
    
    print("🧪 통합 리포트 테스트 시작...")
    print("=" * 50)
    
    try:
        # SalesBot 인스턴스 생성
        sales_bot = SalesBot(SLACK_WEBHOOK_URL, META_ACCESS_TOKEN, META_AD_ACCOUNT_ID)
        
        # 테스트 리포트 전송
        print("📊 테스트 리포트 생성 및 전송 중...")
        sales_bot.send_sales_report("테스트")
        
        print("✅ 테스트 완료! 슬랙을 확인해보세요.")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        print("\n가능한 원인:")
        print("1. Meta 액세스 토큰이 만료되었거나 잘못됨")
        print("2. 아임웹 토큰이 없거나 만료됨")
        print("3. 슬랙 웹훅 URL이 잘못됨")
        print("4. 필요한 패키지가 설치되지 않음")

if __name__ == "__main__":
    test_combined_report()