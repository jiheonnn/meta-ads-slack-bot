"""
Meta 광고 성과 데이터를 가져오는 매니저 클래스
Facebook Marketing API를 사용하여 광고 성과 지표를 조회
"""

import json
from datetime import datetime, timezone, timedelta
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights


class MetaAdsManager:
    def __init__(self, access_token, ad_account_id):
        self.access_token = access_token
        self.ad_account_id = ad_account_id
        self.api = FacebookAdsApi.init(access_token=access_token)
        
    def get_today_performance(self):
        """오늘의 광고 성과 데이터 조회"""
        try:
            # 한국 시간 기준으로 오늘 날짜 설정
            kst = timezone(timedelta(hours=9))
            today_kst = datetime.now(kst)
            today_str = today_kst.strftime('%Y-%m-%d')
            
            print(f"🔍 Meta 광고 성과 조회 중... ({today_str})")
            
            # 광고 계정 객체 생성
            ad_account = AdAccount(f'act_{self.ad_account_id}')
            
            # 조회할 지표 설정
            fields = [
                AdsInsights.Field.spend,           # 지출 금액
                AdsInsights.Field.impressions,     # 노출 수
                AdsInsights.Field.clicks,          # 클릭 수
                AdsInsights.Field.ctr,             # CTR
                AdsInsights.Field.cpc,             # CPC
                AdsInsights.Field.cpm,             # CPM
                AdsInsights.Field.actions,         # 전환 수 (구매 등)
                AdsInsights.Field.action_values,   # 전환 가치 (ROAS 계산용)
            ]
            
            # 조회 파라미터 설정
            params = {
                'time_range': {
                    'since': today_str,
                    'until': today_str
                },
                'level': 'account',
                'date_preset': 'today'
            }
            
            # 인사이트 데이터 조회
            insights = ad_account.get_insights(fields=fields, params=params)
            
            if not insights:
                return self._get_empty_data(today_str)
            
            insight = insights[0]
            
            # 전환 데이터 처리
            conversions = 0
            conversion_value = 0
            
            if 'actions' in insight:
                for action in insight['actions']:
                    if action['action_type'] == 'purchase':
                        conversions = int(action['value'])
                        break
            
            if 'action_values' in insight:
                for action_value in insight['action_values']:
                    if action_value['action_type'] == 'purchase':
                        conversion_value = float(action_value['value'])
                        break
            
            # ROAS 계산
            spend = float(insight.get('spend', 0))
            roas = (conversion_value / spend) if spend > 0 else 0
            
            return {
                'date': today_str,
                'spend': spend,
                'impressions': int(insight.get('impressions', 0)),
                'clicks': int(insight.get('clicks', 0)),
                'ctr': float(insight.get('ctr', 0)),
                'cpc': float(insight.get('cpc', 0)),
                'cpm': float(insight.get('cpm', 0)),
                'conversions': conversions,
                'conversion_value': conversion_value,
                'roas': roas
            }
            
        except Exception as e:
            print(f"❌ Meta 광고 성과 조회 실패: {str(e)}")
            return self._get_empty_data(today_str)
    
    def _get_empty_data(self, date_str):
        """데이터가 없을 때 기본값 반환"""
        return {
            'date': date_str,
            'spend': 0,
            'impressions': 0,
            'clicks': 0,
            'ctr': 0,
            'cpc': 0,
            'cpm': 0,
            'conversions': 0,
            'conversion_value': 0,
            'roas': 0
        }
    
    def format_performance_message(self, performance_data):
        """Meta 광고 성과 메시지 포맷팅"""
        date = performance_data['date']
        spend = f"{performance_data['spend']:,.0f}"
        impressions = f"{performance_data['impressions']:,}"
        clicks = f"{performance_data['clicks']:,}"
        ctr = f"{performance_data['ctr']:.2f}"
        cpc = f"{performance_data['cpc']:,.0f}"
        cpm = f"{performance_data['cpm']:,.0f}"
        conversions = performance_data['conversions']
        roas = f"{performance_data['roas']:.2f}"
        
        message = f"📱 *{date} Meta 광고 성과*\n\n"
        message += f"💰 *지출 금액*: {spend}원\n"
        message += f"👁️ *노출 수*: {impressions}회\n"
        message += f"👆 *클릭 수*: {clicks}회\n"
        message += f"📊 *CTR*: {ctr}%\n"
        message += f"💵 *CPC*: {cpc}원\n"
        message += f"📈 *CPM*: {cpm}원\n"
        message += f"🛒 *전환 수*: {conversions}건\n"
        message += f"🎯 *ROAS*: {roas}배\n"
        
        return message.strip()


# 사용 예시
if __name__ == "__main__":
    # 테스트용 (실제 토큰과 계정 ID 필요)
    ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
    AD_ACCOUNT_ID = "YOUR_AD_ACCOUNT_ID"
    
    manager = MetaAdsManager(ACCESS_TOKEN, AD_ACCOUNT_ID)
    performance = manager.get_today_performance()
    message = manager.format_performance_message(performance)
    print(message)