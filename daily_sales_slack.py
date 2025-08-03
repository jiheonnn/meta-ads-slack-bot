"""
매일 오후 11시 59분에 오늘의 총 매출을 슬랙으로 전송
"""

import requests
import json
from datetime import datetime, timezone, timedelta
import schedule
import time
from oauth_token_manager import ImwebTokenManager

class DailySalesSlackBot:
    def __init__(self, slack_webhook_url):
        self.slack_webhook_url = slack_webhook_url
        # 토큰 매니저 초기화 (자동 갱신 기능 포함)
        self.token_manager = ImwebTokenManager(
            client_id='7241ca65-cfcf-4e24-aa94-12eee45a9f7e',
            client_secret='cf1e8fc3-5d8b-41fc-823f-79ba9ff17921'
        )
    
    def get_today_orders(self):
        """오늘의 주문 정보 조회 (토큰 자동 갱신, 모든 페이지)"""
        # 한국 시간 기준으로 오늘 날짜 설정
        kst = timezone(timedelta(hours=9))
        today_kst = datetime.now(kst)
        start_of_day = today_kst.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = today_kst.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        print(f"🕐 조회 시간: {start_of_day.strftime('%Y-%m-%d %H:%M:%S')} ~ {end_of_day.strftime('%Y-%m-%d %H:%M:%S')} (KST)")
        
        # 토큰 매니저를 통한 API 호출 (자동 갱신)
        token = self.token_manager.get_valid_token()
        if not token:
            raise Exception("유효한 토큰을 가져올 수 없습니다. 인증을 다시 진행해주세요.")
        
        headers = {'Authorization': f'Bearer {token}'}
        all_orders = []
        page = 1
        
        while True:
            params = {
                'page': page,
                'limit': 100,  # API 최대 제한
                'startWtime': start_of_day.isoformat().replace('+00:00', 'Z'),
                'endWtime': end_of_day.isoformat().replace('+00:00', 'Z')
            }
            
            response = requests.get('https://openapi.imweb.me/orders', headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                orders = data.get('data', {}).get('list', [])
                total_count = data.get('data', {}).get('totalCount', 0)
                
                if not orders:  # 더 이상 주문이 없으면 종료
                    break
                    
                all_orders.extend(orders)
                print(f"📄 페이지 {page} 조회: {len(orders)}개 주문 (전체: {total_count}개)")
                
                # 모든 주문을 가져왔으면 종료
                if len(all_orders) >= total_count:
                    break
                    
                page += 1
            else:
                raise Exception(f"주문 조회 실패: {response.status_code} - {response.text}")
        
        print(f"✅ 총 {len(all_orders)}개 주문 조회 완료")
        return all_orders
    
    def calculate_daily_sales(self):
        """오늘의 총 매출 계산 (실제 결제금액 기준)"""
        orders = self.get_today_orders()
        total_sales = 0
        total_orders = 0
        target_products = ['다이어트의 정석', '벌크업의 정석']
        product_sales = {}
        
        for order in orders:
            # 결제 완료된 주문만 계산
            payment_status = None
            paid_price = 0
            if order.get('payments'):
                payment_info = order['payments'][0]
                payment_status = payment_info.get('paymentStatus')
                paid_price = payment_info.get('paidPrice', 0)
            
            if payment_status not in ['PAYMENT_COMPLETE', 'PARTIAL_REFUND_COMPLETE']:
                continue
            
            # 대상 상품이 있는지 확인
            order_has_target_product = False
            target_product_name = None
            total_quantity = 0
            
            for section in order.get('sections', []):
                for item in section.get('sectionItems', []):
                    prod_info = item.get('productInfo', {})
                    prod_name = prod_info.get('prodName', '')
                    quantity = item.get('qty', 0)
                    
                    # 대상 상품인지 확인
                    for target in target_products:
                        if target in prod_name:
                            order_has_target_product = True
                            target_product_name = target
                            total_quantity += quantity
                            break
                    
                    if order_has_target_product:
                        break
                        
                if order_has_target_product:
                    break
            
            # 대상 상품이 있으면 실제 결제금액을 매출로 계산
            if order_has_target_product and paid_price > 0:
                total_sales += paid_price
                total_orders += 1
                
                # 상품별 매출 집계 (실제 결제금액 기준)
                if target_product_name not in product_sales:
                    product_sales[target_product_name] = {'sales': 0, 'quantity': 0}
                product_sales[target_product_name]['sales'] += paid_price
                product_sales[target_product_name]['quantity'] += total_quantity
        
        return {
            'total_sales': total_sales,
            'total_orders': total_orders,
            'product_sales': product_sales,
            'date': datetime.now().strftime('%Y-%m-%d')
        }
    
    def format_slack_message(self, sales_data):
        """슬랙 메시지 포맷팅"""
        date = sales_data['date']
        total_sales = f"{sales_data['total_sales']:,}"
        total_orders = sales_data['total_orders']
        
        message = f"""
📊 *{date} 일일 매출 리포트*

💰 *총 매출*: {total_sales}원
📦 *총 주문*: {total_orders}건
"""
        
        if sales_data['product_sales']:
            message += "\n📈 *상품별 매출*:\n"
            for product, data in sales_data['product_sales'].items():
                sales = f"{data['sales']:,}"
                quantity = data['quantity']
                message += f"   • {product}: {sales}원 ({quantity}개)\n"
        
        # 평균 주문 금액
        if total_orders > 0:
            avg_order = sales_data['total_sales'] / total_orders
            message += f"\n📊 *평균 주문 금액*: {avg_order:,.0f}원"
        
        return message.strip()
    
    def send_to_slack(self, message):
        """슬랙으로 메시지 전송"""
        payload = {
            "text": message,
            "username": "매출봇",
            "icon_emoji": ":moneybag:"
        }
        
        response = requests.post(self.slack_webhook_url, json=payload)
        
        if response.status_code == 200:
            print(f"✅ 슬랙 전송 성공: {datetime.now()}")
        else:
            print(f"❌ 슬랙 전송 실패: {response.status_code}")
    
    def send_daily_report(self):
        """일일 매출 리포트 전송"""
        try:
            print(f"📊 일일 매출 리포트 생성 중... {datetime.now()}")
            
            sales_data = self.calculate_daily_sales()
            message = self.format_slack_message(sales_data)
            self.send_to_slack(message)
            
        except Exception as e:
            error_message = f"❌ 매출 리포트 생성 실패: {str(e)}"
            print(error_message)
            
            # 토큰 관련 에러인지 확인
            if "토큰" in str(e) or "인증" in str(e) or "401" in str(e):
                error_message += "\n\n🔑 토큰이 만료되었습니다. 관리자가 다시 인증해주세요."
                error_message += "\n1. python3 get_first_token.py 실행"
                error_message += "\n2. 브라우저에서 인증 진행"
                error_message += "\n3. 코드 입력"
            
            # 에러도 슬랙으로 전송
            self.send_to_slack(error_message)
    
    def check_token_status(self):
        """토큰 상태 확인 및 알림"""
        tokens = self.token_manager.load_tokens()
        if not tokens:
            self.send_to_slack("⚠️ 토큰이 없습니다. 인증이 필요합니다.")
            return False
        
        try:
            created_at = datetime.fromisoformat(tokens['created_at'])
            now = datetime.now()
            
            # refresh token 만료 7일 전 알림 (90일 - 83일)
            refresh_expires = created_at + timedelta(days=83)
            if now > refresh_expires:
                warning_msg = f"🚨 토큰 만료 임박!\n리프레시 토큰이 {(created_at + timedelta(days=90)).strftime('%Y-%m-%d')}에 만료됩니다.\n관리자가 재인증을 진행해주세요."
                self.send_to_slack(warning_msg)
                return False
            
            return True
        except:
            return False
    
    def auto_refresh_token(self):
        """토큰 자동 갱신 (완전 자동화)"""
        try:
            print(f"🔄 자동 토큰 갱신 시작... {datetime.now()}")
            
            tokens = self.token_manager.load_tokens()
            if not tokens or not tokens.get('refresh_token'):
                error_msg = "❌ 자동 갱신 실패: 토큰이 없습니다."
                print(error_msg)
                self.send_to_slack(error_msg)
                return False
            
            # refresh token으로 갱신
            new_token = self.token_manager.refresh_access_token(tokens['refresh_token'])
            
            if new_token:
                success_msg = f"✅ 토큰 자동 갱신 성공! {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n새로운 토큰으로 90일간 사용 가능합니다."
                print(success_msg)
                self.send_to_slack(success_msg)
                return True
            else:
                error_msg = f"❌ 토큰 자동 갱신 실패! {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n관리자가 수동으로 토큰을 재발급해주세요."
                print(error_msg)
                self.send_to_slack(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"❌ 토큰 자동 갱신 중 오류 발생: {str(e)}"
            print(error_msg)
            self.send_to_slack(error_msg)
            return False

def main():
    # 슬랙 웹훅 URL 설정 (여기에 실제 웹훅 URL을 입력하세요)
    SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"
    
    # 매출봇 인스턴스 생성
    sales_bot = DailySalesSlackBot(SLACK_WEBHOOK_URL)
    
    # 시작시 토큰 상태 확인
    print("🔍 토큰 상태 확인 중...")
    if not sales_bot.check_token_status():
        print("❌ 토큰 문제가 있습니다. 슬랙 알림을 확인하세요.")
    
    # 매일 오후 11:59에 실행 예약
    schedule.every().day.at("23:59").do(sales_bot.send_daily_report)
    
    # 주간 토큰 상태 체크 (매주 월요일 오전 9시)
    schedule.every().monday.at("09:00").do(sales_bot.check_token_status)
    
    # 월간 refresh token 자동 갱신 (매월 1일 오전 3시)
    schedule.every().month.do(sales_bot.auto_refresh_token).at("03:00")
    
    print("🤖 매출봇이 시작되었습니다!")
    print("⏰ 매일 오후 11시 59분에 매출 리포트를 전송합니다.")
    print("🔍 매주 월요일 오전 9시에 토큰 상태를 체크합니다.")
    print("🔄 매월 1일 오전 3시에 토큰을 자동 갱신합니다.")
    print("🎉 완전 자동화! 더 이상 수동 토큰 갱신 불필요!")
    print("🛑 중지하려면 Ctrl+C를 누르세요.")
    
    # 테스트용: 지금 즉시 실행
    print("\n🧪 테스트용으로 지금 매출 리포트를 전송합니다...")
    sales_bot.send_daily_report()
    
    # 스케줄 실행
    while True:
        schedule.run_pending()
        time.sleep(60)  # 1분마다 체크

if __name__ == "__main__":
    main()