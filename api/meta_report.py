"""
Vercel Serverless Function for Meta Ads Reporting
"""

import os
import json
import requests
from datetime import datetime
from http.server import BaseHTTPRequestHandler


class MetaAdsManager:
    def __init__(self, access_token, ad_account_id):
        self.access_token = access_token
        self.ad_account_id = ad_account_id
        self.base_url = "https://graph.facebook.com/v18.0"
    
    def get_today_performance(self):
        """오늘의 광고 성과 조회"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        url = f"{self.base_url}/act_{self.ad_account_id}/insights"
        params = {
            'access_token': self.access_token,
            'fields': 'spend,impressions,clicks,conversions,purchase_roas,ctr,cpm,cost_per_conversion',
            'time_range': json.dumps({'since': today, 'until': today}),
            'level': 'account'
        }
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json().get('data', [])
                if data:
                    insights = data[0]
                    
                    spend = float(insights.get('spend', 0))
                    impressions = int(insights.get('impressions', 0))
                    clicks = int(insights.get('clicks', 0))
                    
                    roas_data = insights.get('purchase_roas', [])
                    roas = float(roas_data[0].get('value', 0)) if roas_data else 0
                    
                    conversions_data = insights.get('conversions', [])
                    conversions = int(conversions_data[0].get('value', 0)) if conversions_data else 0
                    
                    ctr = float(insights.get('ctr', 0))
                    cpm = float(insights.get('cpm', 0))
                    
                    cost_per_conversion_data = insights.get('cost_per_conversion', [])
                    cost_per_conversion = float(cost_per_conversion_data[0].get('value', 0)) if cost_per_conversion_data else 0
                    
                    spend_krw = spend * 1300
                    cpm_krw = cpm * 1300
                    cpc_krw = (cost_per_conversion * 1300) if cost_per_conversion > 0 else 0
                    
                    return {
                        'date': today,
                        'spend': spend_krw,
                        'impressions': impressions,
                        'clicks': clicks,
                        'conversions': conversions,
                        'roas': roas,
                        'ctr': ctr,
                        'cpm': cpm_krw,
                        'cpc': cpc_krw
                    }
                else:
                    return self._empty_performance(today)
            else:
                raise Exception(f"API 요청 실패: {response.status_code}")
        except Exception as e:
            print(f"광고 성과 조회 실패: {str(e)}")
            return self._empty_performance(today)
    
    def _empty_performance(self, date):
        """빈 성과 데이터 반환"""
        return {
            'date': date,
            'spend': 0,
            'impressions': 0,
            'clicks': 0,
            'conversions': 0,
            'roas': 0,
            'ctr': 0,
            'cpm': 0,
            'cpc': 0
        }
    
    def format_performance_message(self, performance):
        """성과 메시지 포맷팅"""
        spend = f"{performance['spend']:,.0f}"
        impressions = f"{performance['impressions']:,}"
        clicks = f"{performance['clicks']:,}"
        conversions = performance['conversions']
        roas = performance['roas']
        ctr = performance['ctr']
        cpm = f"{performance['cpm']:,.0f}"
        cpc = f"{performance['cpc']:,.0f}" if performance['cpc'] > 0 else "N/A"
        
        message = f"📱 *Meta 광고 성과*\n"
        message += f"   • 광고비: {spend}원\n"
        message += f"   • 노출수: {impressions}회\n"
        message += f"   • 클릭수: {clicks}회\n"
        message += f"   • 전환수: {conversions}건\n"
        message += f"   • ROAS: {roas:.2f}배\n"
        message += f"   • CTR: {ctr:.2f}%\n"
        message += f"   • CPM: {cpm}원\n"
        message += f"   • CPC: {cpc}원"
        
        return message


def send_to_slack(webhook_url, message):
    """슬랙으로 메시지 전송"""
    payload = {
        "text": message,
        "username": "메타 광고봇",
        "icon_emoji": ":chart_with_upwards_trend:"
    }
    
    response = requests.post(webhook_url, json=payload)
    return response.status_code == 200


def handler(request, response):
    """Vercel serverless function handler"""
    
    # 환경 변수에서 설정 읽기
    SLACK_WEBHOOK_URL = os.environ.get('SLACK_WEBHOOK_URL')
    META_ACCESS_TOKEN = os.environ.get('META_ACCESS_TOKEN')
    META_AD_ACCOUNT_ID = os.environ.get('META_AD_ACCOUNT_ID')
    
    if not all([SLACK_WEBHOOK_URL, META_ACCESS_TOKEN, META_AD_ACCOUNT_ID]):
        return response.status(500).json({
            'error': 'Missing required environment variables'
        })
    
    try:
        # Meta 광고 매니저 초기화
        meta_ads_manager = MetaAdsManager(META_ACCESS_TOKEN, META_AD_ACCOUNT_ID)
        
        # 광고 성과 조회
        performance = meta_ads_manager.get_today_performance()
        
        # 현재 시간 확인 (KST)
        current_hour = datetime.now().hour
        report_time = "중간" if current_hour < 20 else "최종"
        
        # 메시지 생성
        message = f"📊 *{performance['date']} {report_time} 메타 광고 리포트*\n\n"
        message += meta_ads_manager.format_performance_message(performance)
        
        # ROAS 알림 추가
        if performance['roas'] > 0:
            if performance['roas'] < 1.3:
                message += f"\n\n⚠️ *ROAS 주의*\n광고 효율이 낮습니다. (현재: {performance['roas']:.2f}배)"
            elif performance['roas'] >= 2.0:
                message += f"\n\n🚀 *우수한 광고 성과!*\nROAS: {performance['roas']:.2f}배"
        
        # 슬랙으로 전송
        if send_to_slack(SLACK_WEBHOOK_URL, message):
            return response.status(200).json({
                'success': True,
                'message': f'{report_time} report sent successfully'
            })
        else:
            return response.status(500).json({
                'success': False,
                'message': 'Failed to send slack message'
            })
            
    except Exception as e:
        error_message = f"❌ 광고 리포트 생성 실패: {str(e)}"
        send_to_slack(SLACK_WEBHOOK_URL, error_message)
        
        return response.status(500).json({
            'success': False,
            'error': str(e)
        })