"""
OAuth 토큰을 받아서 저장하고 자동으로 갱신하며 사용하는 시스템
"""

import requests
import json
import time
from datetime import datetime, timedelta

class ImwebTokenManager:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_file = 'imweb_tokens.json'
        self.base_url = 'https://openapi.imweb.me'
        
    def save_tokens(self, access_token, refresh_token):
        """토큰을 파일에 저장"""
        tokens = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'created_at': datetime.now().isoformat()
        }
        with open(self.token_file, 'w') as f:
            json.dump(tokens, f)
            
    def load_tokens(self):
        """저장된 토큰 불러오기"""
        try:
            with open(self.token_file, 'r') as f:
                return json.load(f)
        except:
            return None
            
    def get_token_from_code(self, code, redirect_uri):
        """최초 인증 코드로 토큰 발급"""
        data = {
            'grantType': 'authorization_code',
            'clientId': self.client_id,
            'clientSecret': self.client_secret,
            'redirectUri': redirect_uri,
            'code': code
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.post(
            f'{self.base_url}/oauth2/token',
            data=data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()['data']
            self.save_tokens(result['accessToken'], result['refreshToken'])
            return result['accessToken']
        else:
            print(f"토큰 발급 실패: {response.json()}")
            return None
            
    def refresh_access_token(self, refresh_token):
        """Refresh Token으로 Access Token 갱신"""
        data = {
            'grantType': 'refresh_token',
            'clientId': self.client_id,
            'clientSecret': self.client_secret,
            'refreshToken': refresh_token
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        response = requests.post(
            f'{self.base_url}/oauth2/token',
            data=data,
            headers=headers
        )
        
        if response.status_code == 200:
            result = response.json()['data']
            self.save_tokens(result['accessToken'], result['refreshToken'])
            return result['accessToken']
        else:
            print(f"토큰 갱신 실패: {response.json()}")
            return None
            
    def get_valid_token(self):
        """유효한 액세스 토큰 반환 (필요시 자동 갱신)"""
        tokens = self.load_tokens()
        
        if not tokens:
            print("저장된 토큰이 없습니다. 먼저 인증을 진행하세요.")
            return None
            
        # 토큰이 2시간 이내면 갱신 (아임웹 액세스 토큰 유효기간: 2시간)
        created_at = datetime.fromisoformat(tokens['created_at'])
        if datetime.now() - created_at > timedelta(hours=1.5):
            print("토큰 갱신 중...")
            return self.refresh_access_token(tokens['refresh_token'])
        
        return tokens['access_token']
        
    def api_call(self, endpoint, method='GET', data=None):
        """API 호출 (토큰 자동 관리)"""
        token = self.get_valid_token()
        
        if not token:
            return None
            
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        url = f'{self.base_url}{endpoint}'
        
        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 401:  # 토큰 만료
            print("토큰 만료, 갱신 시도...")
            tokens = self.load_tokens()
            new_token = self.refresh_access_token(tokens['refresh_token'])
            
            if new_token:
                headers['Authorization'] = f'Bearer {new_token}'
                if method == 'GET':
                    response = requests.get(url, headers=headers)
                elif method == 'POST':
                    response = requests.post(url, headers=headers, json=data)
        
        return response.json() if response.status_code == 200 else None


# 사용 예시
if __name__ == "__main__":
    CLIENT_ID = '7241ca65-cfcf-4e24-aa94-12eee45a9f7e'
    CLIENT_SECRET = 'cf1e8fc3-5d8b-41fc-823f-79ba9ff17921'
    
    manager = ImwebTokenManager(CLIENT_ID, CLIENT_SECRET)
    
    # 1. 최초 1회: 브라우저에서 받은 code로 토큰 발급
    # code = "브라우저에서_받은_인증_코드"
    # manager.get_token_from_code(code, 'https://athlogic.app/auth/callback')
    
    # 2. 그 이후: 자동으로 주문 조회 (토큰 자동 갱신)
    orders = manager.api_call('/orders')
    if orders:
        print(f"주문 {len(orders.get('data', {}).get('orders', []))}개 조회 성공!")
    
    # 3. 5분마다 자동 실행 가능
    while True:
        orders = manager.api_call('/orders')
        # 주문 처리 로직...
        time.sleep(300)  # 5분 대기