"""
OAuth 토큰으로 주문 정보 조회 (문서 기반 수정 버전)
"""

import requests
import json
from datetime import datetime, timedelta, timezone

# 저장된 토큰 불러오기
try:
    with open('imweb_tokens.json', 'r') as f:
        tokens = json.load(f)
        access_token = tokens['access_token']
except:
    print("토큰 파일을 찾을 수 없습니다.")
    exit()

print("=== OAuth로 주문 정보 조회 (수정 버전) ===\n")

headers = {
    'Authorization': f'Bearer {access_token}'
}

# 날짜 설정 (UTC ISO8601 형식)
end_date = datetime.now(timezone.utc)
start_date = end_date - timedelta(days=7)  # 최근 7일

params = {
    'page': 1,
    'limit': 100,
    'startWtime': start_date.isoformat().replace('+00:00', 'Z'),  # UTC ISO8601
    'endWtime': end_date.isoformat().replace('+00:00', 'Z')
}

print(f"검색 기간: {params['startWtime']} ~ {params['endWtime']}")

response = requests.get('https://openapi.imweb.me/orders', headers=headers, params=params)

if response.status_code == 200:
    data = response.json()
    orders = data.get('data', {}).get('list', [])
    total_count = data.get('data', {}).get('totalCount', 0)
    
    print(f"✅ 주문 조회 성공! 검색된 주문: {len(orders)}개 (전체: {total_count}개)\n")
    
    # 대상 상품
    TARGET_PRODUCTS = ['다이어트의 정석', '벌크업의 정석']
    buyers = []
    
    for order in orders:
        order_no = order.get('orderNo')
        
        # 주문 상태 확인 (결제 관련 상태)
        payment_status = None
        if order.get('payments'):
            payment_status = order['payments'][0].get('paymentStatus')
        
        # 결제 완료된 주문만
        if payment_status not in ['PAYMENT_COMPLETE', 'PARTIAL_REFUND_COMPLETE']:
            continue
        
        # sections 내의 sectionItems 확인
        for section in order.get('sections', []):
            # 주문 섹션 상태 확인
            section_status = section.get('orderSectionStatus')
            
            for item in section.get('sectionItems', []):
                prod_info = item.get('productInfo', {})
                prod_name = prod_info.get('prodName', '')
                
                # 대상 상품 확인
                for target in TARGET_PRODUCTS:
                    if target in prod_name:
                        buyer_info = {
                            'order_no': order_no,
                            'buyer_name': order.get('ordererName'),
                            'buyer_phone': order.get('ordererCall'),
                            'buyer_email': order.get('ordererEmail'),
                            'order_date': order.get('wtime'),
                            'product_name': prod_name,
                            'quantity': item.get('qty'),
                            'price': prod_info.get('itemPrice'),
                            'order_status': section_status,
                            'payment_status': payment_status
                        }
                        buyers.append(buyer_info)
                        
                        print(f"🎯 구매자 발견!")
                        print(f"   이름: {buyer_info['buyer_name']}")
                        print(f"   전화번호: {buyer_info['buyer_phone']}")
                        print(f"   상품: {buyer_info['product_name']} x {buyer_info['quantity']}개")
                        print(f"   주문일: {buyer_info['order_date']}")
                        print(f"   주문상태: {buyer_info['order_status']}")
                        print(f"   결제상태: {buyer_info['payment_status']}\n")
                        break
    
    print(f"\n총 {len(buyers)}명의 구매자를 찾았습니다.")
    
    if buyers:
        # CSV 저장
        save = input("\nCSV 파일로 저장하시겠습니까? (y/n): ")
        if save.lower() == 'y':
            import csv
            filename = f"buyers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=buyers[0].keys())
                writer.writeheader()
                writer.writerows(buyers)
            
            print(f"✅ {filename} 파일로 저장되었습니다.")
    
else:
    print(f"❌ 오류 발생: {response.status_code}")
    print(response.json())