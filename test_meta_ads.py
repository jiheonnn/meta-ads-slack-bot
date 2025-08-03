"""
Meta 광고 API 연동 테스트 스크립트
광고 계정 ID를 찾고 API 연결을 테스트합니다.
"""

from meta_ads_manager import MetaAdsManager
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.user import User

def test_meta_connection():
    """Meta API 연결 테스트 및 광고 계정 ID 찾기"""
    
    ACCESS_TOKEN = "EAAKUZAdQJpPgBPEc9KSGZAFtP2P9DUTrAZCDT68KKqwxFmHVZAZCQlLepisdV9aWbN6fHft0b3oO1NoEqZBCoFr5fSQVuGNGwETNQ3Xukys6q3SUZC8aOj2u2CypBnsHRQJGec28N2omBz9vSRqh25qxfB5JcCaXaPZAZAudrd9QrU2pgQ7ihKlEsy7cbHHrbeQ9wxoE7XpjX50y3dNxHaNkbc7R89aZCDC3fAInbZCeWctkNWybgwAxFiJ"
    
    try:
        # Facebook API 초기화
        FacebookAdsApi.init(access_token=ACCESS_TOKEN)
        print("✅ Meta API 연결 성공!")
        
        # 현재 사용자의 광고 계정 목록 조회
        me = User(fbid='me')
        ad_accounts = me.get_ad_accounts()
        
        print(f"\n📋 사용 가능한 광고 계정 목록:")
        for account in ad_accounts:
            account_id = account['id'].replace('act_', '')
            account_name = account.get('name', 'Unknown')
            print(f"   • 계정 ID: {account_id}")
            print(f"     계정 이름: {account_name}")
            print(f"     계정 상태: {account.get('account_status', 'Unknown')}")
            print()
        
        if ad_accounts:
            # 첫 번째 계정으로 테스트
            first_account_id = ad_accounts[0]['id'].replace('act_', '')
            print(f"🧪 첫 번째 계정({first_account_id})으로 성과 데이터 테스트...")
            
            # MetaAdsManager로 테스트
            manager = MetaAdsManager(ACCESS_TOKEN, first_account_id)
            performance = manager.get_today_performance()
            message = manager.format_performance_message(performance)
            
            print("📊 오늘의 광고 성과:")
            print(message)
            
            print(f"\n✅ 테스트 완료! 광고 계정 ID: {first_account_id}")
            print(f"이 ID를 sales_bot.py의 META_AD_ACCOUNT_ID에 입력하세요.")
            
        else:
            print("❌ 사용 가능한 광고 계정이 없습니다.")
            
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        print("\n가능한 원인:")
        print("1. 액세스 토큰이 만료되었거나 잘못됨")
        print("2. 마케팅 API 권한이 없음")
        print("3. 광고 계정에 대한 접근 권한이 없음")
        
if __name__ == "__main__":
    test_meta_connection()