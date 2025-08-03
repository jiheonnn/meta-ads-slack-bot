import json
from datetime import datetime
from oauth_token_manager import ImwebTokenManager

# 현재 토큰 정보 확인
with open('imweb_tokens.json', 'r') as f:
    tokens = json.load(f)

print('📅 현재 토큰 정보:')
print(f'생성일: {tokens["created_at"]}')

created_time = datetime.fromisoformat(tokens['created_at'])
print(f'생성일 (파싱): {created_time}')

# 토큰 매니저로 갱신 시도
manager = ImwebTokenManager('7241ca65-cfcf-4e24-aa94-12eee45a9f7e', 'cf1e8fc3-5d8b-41fc-823f-79ba9ff17921')

print('\n🔄 Refresh Token으로 갱신 중...')
new_token = manager.refresh_access_token(tokens['refresh_token'])

if new_token:
    print('✅ 갱신 성공!')
    
    # 갱신 후 토큰 정보 확인
    with open('imweb_tokens.json', 'r') as f:
        new_tokens = json.load(f)
    
    print('\n📅 갱신 후 토큰 정보:')
    print(f'새 생성일: {new_tokens["created_at"]}')
    
    new_created_time = datetime.fromisoformat(new_tokens['created_at'])
    print(f'새 생성일 (파싱): {new_created_time}')
    
    # 차이 계산
    time_diff = new_created_time - created_time
    print(f'\n⏰ 시간 차이: {time_diff}')
    
    if new_tokens['refresh_token'] != tokens['refresh_token']:
        print('🆕 새로운 refresh token 발급됨!')
        print('🎉 Rolling refresh token 정책 사용 중 - 자동화 가능할 수 있음!')
        
        # JWT 토큰 만료일 확인해보기
        import base64
        try:
            # refresh token의 payload 디코딩 (JWT)
            refresh_payload = new_tokens['refresh_token'].split('.')[1]
            # padding 추가
            refresh_payload += '=' * (4 - len(refresh_payload) % 4)
            decoded = base64.b64decode(refresh_payload)
            refresh_data = json.loads(decoded)
            
            print(f'\n🔍 새 Refresh Token 정보:')
            print(f'iat (발급시간): {refresh_data.get("iat")}')
            print(f'exp (만료시간): {refresh_data.get("exp")}')
            
            if refresh_data.get('exp'):
                exp_time = datetime.fromtimestamp(refresh_data['exp'])
                iat_time = datetime.fromtimestamp(refresh_data['iat'])
                print(f'발급일: {iat_time}')
                print(f'만료일: {exp_time}')
                print(f'유효기간: {exp_time - iat_time}')
                
        except Exception as e:
            print(f'JWT 디코딩 실패: {e}')
            
    else:
        print('🔄 동일한 refresh token - 만료일 연장 안됨')
        
else:
    print('❌ 갱신 실패')