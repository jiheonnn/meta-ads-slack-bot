"""
아임웹 매출 자동 리포트 슬랙봇
- 매일 12시, 23시 59분 매출 리포트 자동 전송
- 토큰 완전 자동 관리 (무한 갱신)
- 실제 결제금액 기준 정확한 매출 계산
"""

import requests
import json
from datetime import datetime, timezone, timedelta
import schedule
import time
from oauth_token_manager import ImwebTokenManager
from meta_ads_manager import MetaAdsManager


class SalesBot:
    def __init__(self, slack_webhook_url, meta_access_token=None, meta_ad_account_id=None):
        self.slack_webhook_url = slack_webhook_url
        self.token_manager = ImwebTokenManager(
            client_id='7241ca65-cfcf-4e24-aa94-12eee45a9f7e',
            client_secret='cf1e8fc3-5d8b-41fc-823f-79ba9ff17921'
        )
        self.target_products = ['다이어트의 정석', '벌크업의 정석']
        
        # 목표 설정
        self.daily_sales_target = 600000  # 일일 매출 목표 60만원
        self.roas_warning_threshold = 1.3  # ROAS 경고 기준 1.3
        
        # Meta 광고 매니저 초기화
        if meta_access_token and meta_ad_account_id:
            self.meta_ads_manager = MetaAdsManager(meta_access_token, meta_ad_account_id)
        else:
            self.meta_ads_manager = None
    
    def get_today_orders(self):
        """오늘의 모든 주문 조회 (페이지네이션 처리)"""
        # 한국 시간 기준으로 오늘 날짜 설정
        kst = timezone(timedelta(hours=9))
        today_kst = datetime.now(kst)
        start_of_day = today_kst.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = today_kst.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        print(f"🕐 조회 시간: {start_of_day.strftime('%Y-%m-%d %H:%M:%S')} ~ {end_of_day.strftime('%Y-%m-%d %H:%M:%S')} (KST)")
        
        token = self.token_manager.get_valid_token()
        if not token:
            raise Exception("유효한 토큰을 가져올 수 없습니다.")
        
        headers = {'Authorization': f'Bearer {token}'}
        all_orders = []
        page = 1
        
        while True:
            params = {
                'page': page,
                'limit': 100,
                'startWtime': start_of_day.isoformat().replace('+00:00', 'Z'),
                'endWtime': end_of_day.isoformat().replace('+00:00', 'Z')
            }
            
            response = requests.get('https://openapi.imweb.me/orders', headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                orders = data.get('data', {}).get('list', [])
                
                if not orders:
                    break
                    
                all_orders.extend(orders)
                
                if len(all_orders) >= data.get('data', {}).get('totalCount', 0):
                    break
                    
                page += 1
            else:
                raise Exception(f"주문 조회 실패: {response.status_code}")
        
        return all_orders
    
    def calculate_sales(self):
        """매출 계산 (실제 결제금액 기준)"""
        orders = self.get_today_orders()
        total_sales = 0
        total_orders = 0
        product_sales = {}
        
        for order in orders:
            # 결제 완료된 주문만 처리
            if not order.get('payments'):
                continue
                
            payment_info = order['payments'][0]
            payment_status = payment_info.get('paymentStatus')
            paid_price = payment_info.get('paidPrice', 0)
            
            if payment_status not in ['PAYMENT_COMPLETE', 'PARTIAL_REFUND_COMPLETE'] or paid_price <= 0:
                continue
            
            # 대상 상품 확인
            target_product = self._find_target_product(order)
            if target_product:
                total_sales += paid_price
                total_orders += 1
                
                if target_product not in product_sales:
                    product_sales[target_product] = {'sales': 0, 'quantity': 0}
                
                product_sales[target_product]['sales'] += paid_price
                product_sales[target_product]['quantity'] += self._get_order_quantity(order)
        
        return {
            'total_sales': total_sales,
            'total_orders': total_orders,
            'product_sales': product_sales,
            'date': datetime.now().strftime('%Y-%m-%d')
        }
    
    def _find_target_product(self, order):
        """주문에서 대상 상품 찾기"""
        for section in order.get('sections', []):
            for item in section.get('sectionItems', []):
                prod_name = item.get('productInfo', {}).get('prodName', '')
                for target in self.target_products:
                    if target in prod_name:
                        return target
        return None
    
    def _get_order_quantity(self, order):
        """주문의 총 수량 계산"""
        total_qty = 0
        for section in order.get('sections', []):
            for item in section.get('sectionItems', []):
                total_qty += item.get('qty', 0)
        return total_qty
    
    def format_message(self, sales_data, report_time="일일"):
        """슬랙 메시지 포맷팅"""
        date = sales_data['date']
        total_sales = f"{sales_data['total_sales']:,}"
        total_orders = sales_data['total_orders']
        
        message = f"📊 *{date} {report_time} 매출 리포트*\n\n"
        message += f"💰 *총 매출*: {total_sales}원\n"
        message += f"📦 *총 주문*: {total_orders}건\n"
        
        if sales_data['product_sales']:
            message += "\n📈 *상품별 매출*:\n"
            for product, data in sales_data['product_sales'].items():
                sales = f"{data['sales']:,}"
                quantity = data['quantity']
                message += f"   • {product}: {sales}원 ({quantity}개)\n"
        
        if total_orders > 0:
            avg_order = sales_data['total_sales'] / total_orders
            message += f"\n📊 *평균 주문 금액*: {avg_order:,.0f}원"
        
        return message.strip()
    
    def generate_alert_messages(self, sales_data, meta_performance):
        """목표 달성 축하 및 ROAS 경고 메시지 생성"""
        alert_messages = []
        
        # 매출 목표 달성 확인
        total_sales = sales_data['total_sales']
        if total_sales >= self.daily_sales_target:
            achievement_rate = (total_sales / self.daily_sales_target) * 100
            alert_messages.append(
                f"\n🎉 *축하합니다!* 🎉\n"
                f"일일 매출 목표 달성! ({achievement_rate:.1f}%)\n"
                f"목표: {self.daily_sales_target:,}원 → 달성: {total_sales:,}원"
            )
        
        # ROAS 경고 확인 (Meta 광고 데이터가 있는 경우)
        if meta_performance and meta_performance['roas'] > 0:
            roas = meta_performance['roas']
            if roas < self.roas_warning_threshold:
                alert_messages.append(
                    f"\n⚠️ *ROAS 주의* ⚠️\n"
                    f"광고 효율이 기준치 이하입니다.\n"
                    f"현재 ROAS: {roas:.2f}배 (기준: {self.roas_warning_threshold}배)\n"
                    f"광고 최적화를 검토해보세요."
                )
            elif roas >= 2.0:  # 높은 ROAS일 때 축하
                alert_messages.append(
                    f"\n🚀 *우수한 광고 성과!* 🚀\n"
                    f"ROAS: {roas:.2f}배 - 광고가 효율적으로 운영되고 있습니다!"
                )
        
        return "".join(alert_messages) if alert_messages else ""
    
    def send_to_slack(self, message):
        """슬랙으로 메시지 전송"""
        payload = {
            "text": message,
            "username": "매출봇",
            "icon_emoji": ":moneybag:"
        }
        
        response = requests.post(self.slack_webhook_url, json=payload)
        return response.status_code == 200
    
    def send_sales_report(self, report_time="일일"):
        """매출 리포트 전송 (Meta 광고 성과 포함)"""
        try:
            print(f"📊 {report_time} 리포트 생성 중... {datetime.now()}")
            
            # 매출 데이터 조회
            sales_data = self.calculate_sales()
            sales_message = self.format_message(sales_data, report_time)
            
            # Meta 광고 성과 조회 (설정된 경우)
            meta_message = ""
            meta_performance = None
            if self.meta_ads_manager:
                try:
                    print("📱 Meta 광고 성과 조회 중...")
                    meta_performance = self.meta_ads_manager.get_today_performance()
                    meta_message = "\n\n" + self.meta_ads_manager.format_performance_message(meta_performance)
                except Exception as meta_error:
                    print(f"⚠️ Meta 광고 성과 조회 실패: {str(meta_error)}")
                    meta_message = "\n\n⚠️ Meta 광고 성과 조회 실패"
            
            # 알림 메시지 생성 (목표 달성, ROAS 경고)
            alert_message = self.generate_alert_messages(sales_data, meta_performance)
            
            # 통합 메시지 생성
            combined_message = sales_message + meta_message + alert_message
            
            if self.send_to_slack(combined_message):
                print(f"✅ {report_time} 리포트 전송 성공")
            else:
                print(f"❌ {report_time} 리포트 전송 실패")
                
        except Exception as e:
            error_message = f"❌ {report_time} 리포트 생성 실패: {str(e)}"
            print(error_message)
            
            if "토큰" in str(e) or "인증" in str(e) or "401" in str(e):
                error_message += "\n\n🔑 토큰이 만료되었습니다. 시스템에서 자동 갱신을 시도합니다."
            
            self.send_to_slack(error_message)
    
    def auto_refresh_token(self):
        """토큰 자동 갱신"""
        try:
            print(f"🔄 토큰 자동 갱신 시작... {datetime.now()}")
            
            tokens = self.token_manager.load_tokens()
            if not tokens or not tokens.get('refresh_token'):
                error_msg = "❌ 토큰 자동 갱신 실패: 토큰이 없습니다."
                print(error_msg)
                self.send_to_slack(error_msg)
                return False
            
            new_token = self.token_manager.refresh_access_token(tokens['refresh_token'])
            
            if new_token:
                success_msg = f"✅ 토큰 자동 갱신 성공! {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n새로운 토큰으로 90일간 사용 가능합니다."
                print(success_msg)
                self.send_to_slack(success_msg)
                return True
            else:
                error_msg = f"❌ 토큰 자동 갱신 실패! 수동 재발급이 필요합니다."
                print(error_msg)
                self.send_to_slack(error_msg)
                return False
                
        except Exception as e:
            error_msg = f"❌ 토큰 자동 갱신 중 오류: {str(e)}"
            print(error_msg)
            self.send_to_slack(error_msg)
            return False
    
    def check_token_status(self):
        """토큰 상태 확인"""
        tokens = self.token_manager.load_tokens()
        if not tokens:
            self.send_to_slack("⚠️ 토큰이 없습니다. 인증이 필요합니다.")
            return False
        
        try:
            created_at = datetime.fromisoformat(tokens['created_at'])
            now = datetime.now()
            refresh_expires = created_at + timedelta(days=83)
            
            if now > refresh_expires:
                warning_msg = f"🚨 토큰 만료 임박!\n리프레시 토큰이 {(created_at + timedelta(days=90)).strftime('%Y-%m-%d')}에 만료됩니다."
                self.send_to_slack(warning_msg)
                return False
            
            return True
        except:
            return False


def main():
    SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/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"
    
    # Meta 광고 설정
    META_ACCESS_TOKEN = "EAAKUZAdQJpPgBPEc9KSGZAFtP2P9DUTrAZCDT68KKqwxFmHVZAZCQlLepisdV9aWbN6fHft0b3oO1NoEqZBCoFr5fSQVuGNGwETNQ3Xukys6q3SUZC8aOj2u2CypBnsHRQJGec28N2omBz9vSRqh25qxfB5JcCaXaPZAZAudrd9QrU2pgQ7ihKlEsy7cbHHrbeQ9wxoE7XpjX50y3dNxHaNkbc7R89aZCDC3fAInbZCeWctkNWybgwAxFiJ"
    META_AD_ACCOUNT_ID = "360590366471346"  # Meta 광고 계정 ID
    
    sales_bot = SalesBot(SLACK_WEBHOOK_URL, META_ACCESS_TOKEN, META_AD_ACCOUNT_ID)
    
    # 시작시 토큰 상태 확인
    print("🔍 토큰 상태 확인 중...")
    sales_bot.check_token_status()
    
    # 스케줄 설정
    schedule.every().day.at("12:00").do(lambda: sales_bot.send_sales_report("중간"))
    schedule.every().day.at("23:59").do(lambda: sales_bot.send_sales_report("최종"))
    schedule.every().monday.at("09:00").do(sales_bot.check_token_status)
    schedule.every(30).days.at("03:00").do(sales_bot.auto_refresh_token)  # 30일마다
    
    print("🤖 매출봇 시작!")
    print("⏰ 매일 12:00, 23:59에 매출 리포트 전송")
    print("🔄 30일마다 03:00에 토큰 자동 갱신")
    print("🎉 완전 자동화 시스템 가동 중!")
    print("🛑 중지: Ctrl+C")
    
    # 시작 알림
    print("\n📊 매출봇 준비 완료! 스케줄에 따라 자동 실행됩니다.")
    
    # 메인 루프
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()