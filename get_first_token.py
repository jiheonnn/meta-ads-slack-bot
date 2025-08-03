"""
최초 OAuth 토큰 발급받기
1회만 실행하면 됨
"""

import webbrowser
from urllib.parse import urlencode
from datetime import datetime
from oauth_token_manager import ImwebTokenManager

# 설정
CLIENT_ID = '7241ca65-cfcf-4e24-aa94-12eee45a9f7e'
CLIENT_SECRET = 'cf1e8fc3-5d8b-41fc-823f-79ba9ff17921'
REDIRECT_URI = 'https://petebaek0712000.imweb.me/'  # 임시로 메인 도메인 사용
SITE_CODE = 'S202407313af6560dd5f06'

print("=== 아임웹 OAuth 최초 인증 ===\n")

# 1단계: 인증 URL 생성
params = {
    'responseType': 'code',
    'clientId': CLIENT_ID,
    'redirectUri': REDIRECT_URI,
    'scope': 'site-info:write order:read',  # 필수 권한 + 주문 조회 권한
    'siteCode': SITE_CODE,
    'state': f'random_state_{int(datetime.now().timestamp() * 1000)}'
}

auth_url = f'https://openapi.imweb.me/oauth2/authorize?{urlencode(params)}'

print("1. 아래 URL을 브라우저에서 열어주세요:")
print(auth_url)
print("\n2. 아임웹에 로그인하고 권한을 승인하세요.")
print("\n3. 리다이렉트된 URL에서 code 파라미터를 복사하세요.")
print(f"   예: {REDIRECT_URI}?code=XXXXX&state=...")

# 브라우저 자동 열기
webbrowser.open(auth_url)

# 2단계: 인증 코드 입력 받기
print("\n" + "="*50)
code = input("인증 코드(code)를 입력하세요: ").strip()

if code:
    # 3단계: 토큰 발급
    manager = ImwebTokenManager(CLIENT_ID, CLIENT_SECRET)
    access_token = manager.get_token_from_code(code, REDIRECT_URI)
    
    if access_token:
        print("\n✅ 토큰 발급 성공!")
        print("토큰이 'imweb_tokens.json' 파일에 저장되었습니다.")
        print("\n이제부터 자동으로 주문 정보를 조회할 수 있습니다.")
        
        # 테스트 API 호출
        print("\n테스트: 주문 목록 조회 중...")
        orders = manager.api_call('/orders')
        if orders:
            print(f"✅ 성공! 주문 {len(orders.get('data', {}).get('orders', []))}개 확인")
        else:
            print("❌ 주문 조회 실패")
    else:
        print("\n❌ 토큰 발급 실패")
else:
    print("\n취소되었습니다.")