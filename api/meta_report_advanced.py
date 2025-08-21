"""
Vercel Serverless Function for Advanced Meta Ads Reporting
"""

import os
import json
import requests
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler


class MetaAdsManager:
    def __init__(self, access_token, ad_account_id):
        self.access_token = access_token
        self.ad_account_id = ad_account_id
        self.base_url = "https://graph.facebook.com/v18.0"
    
    def get_account_performance(self, date_preset='today'):
        """계정 전체 성과 조회"""
        url = f"{self.base_url}/act_{self.ad_account_id}/insights"
        params = {
            'access_token': self.access_token,
            'fields': 'spend,impressions,clicks,conversions,purchase_roas,ctr,cpm,cpc,cpp,frequency,reach,actions,action_values',
            'date_preset': date_preset,
            'level': 'account'
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json().get('data', [])
                if data:
                    return self._parse_insights(data[0])
            return None
        except Exception as e:
            print(f"계정 성과 조회 실패: {str(e)}")
            return None
    
    
    def get_adset_performance(self, date_preset='today', limit=5):
        """광고세트별 성과 조회 (상위 5개)"""
        url = f"{self.base_url}/act_{self.ad_account_id}/insights"
        params = {
            'access_token': self.access_token,
            'fields': 'adset_name,spend,impressions,clicks,conversions,purchase_roas,ctr,frequency',
            'date_preset': date_preset,
            'level': 'adset',
            'filtering': json.dumps([{'field': 'spend', 'operator': 'GREATER_THAN', 'value': 0}]),
            'sort': json.dumps(['spend_descending']),
            'limit': limit
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json().get('data', [])
                return [self._parse_adset_insights(item) for item in data[:limit]]
            return []
        except Exception as e:
            print(f"광고세트 성과 조회 실패: {str(e)}")
            return []
    
    def get_ad_performance(self, date_preset='today', limit=15):
        """개별 광고별 성과 조회 (상위 15개)"""
        # 먼저 광고 ID와 이름 가져오기
        ads_url = f"{self.base_url}/act_{self.ad_account_id}/ads"
        ads_params = {
            'access_token': self.access_token,
            'fields': 'id,name,status',
            'filtering': json.dumps([{'field': 'effective_status', 'operator': 'IN', 'value': ['ACTIVE', 'PAUSED']}]),
            'limit': 50
        }
        
        try:
            # 광고 메타데이터 가져오기
            ads_response = requests.get(ads_url, params=ads_params)
            if ads_response.status_code != 200:
                return []
            
            ads_data = ads_response.json().get('data', [])
            ad_names = {ad['id']: ad['name'] for ad in ads_data}
            
            # 인사이트 데이터 가져오기
            insights_url = f"{self.base_url}/act_{self.ad_account_id}/insights"
            insights_params = {
                'access_token': self.access_token,
                'fields': 'ad_id,spend,impressions,clicks,conversions,purchase_roas,ctr,actions',
                'date_preset': date_preset,
                'level': 'ad',
                'filtering': json.dumps([{'field': 'spend', 'operator': 'GREATER_THAN', 'value': 0}]),
                'sort': json.dumps(['spend_descending']),
                'limit': limit
            }
            
            response = requests.get(insights_url, params=insights_params)
            if response.status_code == 200:
                data = response.json().get('data', [])
                results = []
                for item in data[:limit]:
                    parsed = self._parse_ad_insights(item)
                    # ad_id로 이름 매칭
                    ad_id = item.get('ad_id', '')
                    parsed['ad_name'] = ad_names.get(ad_id, f"광고 ID: {ad_id}")
                    results.append(parsed)
                return results
            return []
        except Exception as e:
            print(f"개별 광고 성과 조회 실패: {str(e)}")
            return []
    
    def get_weekly_comparison(self):
        """주간 성과 비교"""
        this_week = self.get_account_performance('this_week')
        last_week = self.get_account_performance('last_week')
        
        if this_week and last_week:
            return {
                'this_week': this_week,
                'last_week': last_week,
                'spend_change': ((this_week['spend'] - last_week['spend']) / last_week['spend'] * 100) if last_week['spend'] > 0 else 0,
                'roas_change': this_week['roas'] - last_week['roas'],
                'conversion_change': ((this_week['conversions'] - last_week['conversions']) / last_week['conversions'] * 100) if last_week['conversions'] > 0 else 0
            }
        return None
    
    def _parse_insights(self, insights):
        """인사이트 데이터 파싱"""
        spend = float(insights.get('spend', 0))  # 이미 KRW
        impressions = int(insights.get('impressions', 0))
        clicks = int(insights.get('clicks', 0))
        reach = int(insights.get('reach', 0))
        frequency = float(insights.get('frequency', 0))
        
        # ROAS 처리
        roas_data = insights.get('purchase_roas', [])
        roas = float(roas_data[0].get('value', 0)) if roas_data else 0
        
        # 전환 데이터 처리
        conversions = 0
        conversion_value = 0
        actions = insights.get('actions', [])
        action_values = insights.get('action_values', [])
        
        for action in actions:
            if action.get('action_type') == 'purchase':
                conversions = int(action.get('value', 0))
                break
        
        for value in action_values:
            if value.get('action_type') == 'purchase':
                conversion_value = float(value.get('value', 0))  # 이미 KRW
                break
        
        ctr = float(insights.get('ctr', 0))
        cpm = float(insights.get('cpm', 0))  # 이미 KRW
        cpc = float(insights.get('cpc', 0)) if 'cpc' in insights else (spend / clicks if clicks > 0 else 0)
        cac = spend / conversions if conversions > 0 else 0  # Customer Acquisition Cost
        
        # 랜딩페이지 전환율 계산 (클릭 대비 구매)
        landing_conversion_rate = (conversions / clicks * 100) if clicks > 0 else 0
        
        return {
            'spend': spend,
            'impressions': impressions,
            'clicks': clicks,
            'conversions': conversions,
            'conversion_value': conversion_value,
            'roas': roas,
            'ctr': ctr,
            'cpm': cpm,
            'cpc': cpc,
            'cac': cac,
            'reach': reach,
            'frequency': frequency,
            'landing_conversion_rate': landing_conversion_rate
        }
    
    
    def _parse_adset_insights(self, insights):
        """광고세트 인사이트 파싱"""
        base = self._parse_insights(insights)
        base['adset_name'] = insights.get('adset_name', 'Unknown')
        return base
    
    def _parse_ad_insights(self, insights):
        """광고 인사이트 파싱"""
        base = self._parse_insights(insights)
        # ad_name은 별도로 처리됨
        return base
    
    def format_comprehensive_report(self, account_perf, ads, weekly_comp):
        """종합 리포트 포맷팅"""
        today = datetime.now().strftime('%Y-%m-%d')
        message = f"📊 *{today} Meta 광고 종합 리포트*\n\n"
        
        # 1. 계정 전체 성과
        if account_perf:
            message += "📈 *전체 성과*\n"
            message += f"• 광고비: {account_perf['spend']:,.0f}원\n"
            message += f"• ROAS: {account_perf['roas']:.2f}배\n"
            message += f"• 전환수: {account_perf['conversions']}건\n"
            message += f"• 전환 매출: {account_perf['conversion_value']:,.0f}원\n"
            message += f"• 도달: {account_perf['reach']:,}명 (빈도: {account_perf['frequency']:.1f})\n"
            message += f"• CTR: {account_perf['ctr']:.2f}% | CPM: {account_perf['cpm']:,.0f}원\n"
            message += f"• CPC: {account_perf['cpc']:,.0f}원 | CAC: {account_perf['cac']:,.0f}원\n"
            message += f"• 랜딩 전환율: {account_perf['landing_conversion_rate']:.2f}%\n\n"
        
        # 2. 주간 비교
        if weekly_comp:
            message += "📅 *주간 비교*\n"
            spend_emoji = "📈" if weekly_comp['spend_change'] > 0 else "📉"
            roas_emoji = "📈" if weekly_comp['roas_change'] > 0 else "📉"
            conv_emoji = "📈" if weekly_comp['conversion_change'] > 0 else "📉"
            
            message += f"• 광고비: {spend_emoji} {weekly_comp['spend_change']:+.1f}%\n"
            message += f"• ROAS: {roas_emoji} {weekly_comp['roas_change']:+.2f}\n"
            message += f"• 전환: {conv_emoji} {weekly_comp['conversion_change']:+.1f}%\n\n"
        
        # 3. 소재별 성과
        if ads:
            message += "🎨 *소재별 성과*\n"
            for i, ad in enumerate(ads, 1):
                name = ad['ad_name'][:25] if len(ad['ad_name']) > 25 else ad['ad_name']
                # 간결한 한 줄 포맷
                message += f"{i:2d}. {name:25s} | {ad['spend']/1000:.0f}k원 | ROAS:{ad['roas']:.1f} | CTR:{ad['ctr']:.1f}%\n"
            message += "\n"
        
        
        # 4. 인사이트 및 추천
        message += self._generate_insights(account_perf, ads)
        
        return message
    
    def _generate_insights(self, account_perf, ads):
        """자동 인사이트 생성"""
        insights = "💡 *인사이트*\n"
        
        if not account_perf:
            return insights + "• 데이터 없음\n"
        
        # ROAS 기반 인사이트
        if account_perf['roas'] < 1.0:
            insights += "⚠️ ROAS가 1.0 미만입니다. 광고 최적화가 시급합니다.\n"
        elif account_perf['roas'] < 1.5:
            insights += "📊 ROAS 개선이 필요합니다. 타겟팅 재검토를 권장합니다.\n"
        elif account_perf['roas'] > 3.0:
            insights += "🎉 우수한 ROAS! 예산 증액을 고려해보세요.\n"
        
        # CTR 기반 인사이트
        if account_perf['ctr'] < 1.0:
            insights += "• 낮은 CTR - 광고 크리에이티브 개선 필요\n"
        elif account_perf['ctr'] > 2.0:
            insights += "• 높은 CTR - 광고가 타겟에게 잘 어필하고 있습니다\n"
        
        # 빈도 기반 인사이트
        if account_perf['frequency'] > 3.0:
            insights += "• 광고 피로도 주의 - 새로운 크리에이티브 추가 권장\n"
        
        # 소재 다양성
        if ads and len(ads) > 10:
            insights += "• 활성 소재가 많습니다. 저성과 소재 정리를 고려해보세요.\n"
        
        return insights


def send_to_slack(webhook_url, message):
    """슬랙으로 메시지 전송"""
    payload = {
        "text": message,
        "username": "메타 광고 분석봇",
        "icon_emoji": ":chart_with_upwards_trend:"
    }
    
    response = requests.post(webhook_url, json=payload)
    return response.status_code == 200


from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler"""
    
    def do_GET(self):
        """크론잡에서 호출되는 GET 요청 처리"""
        # 환경 변수에서 설정 읽기
        SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')
        META_ACCESS_TOKEN = os.environ.get('META_ACCESS_TOKEN')
        META_AD_ACCOUNT_ID = os.environ.get('META_AD_ACCOUNT_ID')
        
        if not all([SLACK_WEBHOOK_URL, META_ACCESS_TOKEN, META_AD_ACCOUNT_ID]):
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Missing required environment variables'}).encode())
            return
        
        try:
            # Meta 광고 매니저 초기화
            manager = MetaAdsManager(META_ACCESS_TOKEN, META_AD_ACCOUNT_ID)
            
            # 데이터 수집
            account_perf = manager.get_account_performance()
            ads = manager.get_ad_performance()
            weekly_comp = manager.get_weekly_comparison()
            
            # 리포트 생성
            message = manager.format_comprehensive_report(
                account_perf, ads, weekly_comp
            )
            
            # 슬랙으로 전송
            if send_to_slack(SLACK_WEBHOOK_URL, message):
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': True,
                    'message': 'Comprehensive report sent successfully'
                }).encode())
            else:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': 'Failed to send slack message'
                }).encode())
                
        except Exception as e:
            error_message = f"❌ 광고 리포트 생성 실패: {str(e)}"
            send_to_slack(SLACK_WEBHOOK_URL, error_message)
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'error': str(e)
            }).encode())