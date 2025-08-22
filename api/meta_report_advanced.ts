/**
 * Vercel Serverless Function for Advanced Meta Ads Reporting
 */

import type { VercelRequest, VercelResponse } from '@vercel/node';

// 타입 정의
interface InsightsData {
  spend: number;
  impressions: number;
  clicks: number;
  conversions: number;
  conversion_value: number;
  roas: number;
  ctr: number;
  cpm: number;
  cpc: number;
  cac: number;
  reach: number;
  frequency: number;
  landing_conversion_rate: number;
}

interface AdsetInsights extends InsightsData {
  adset_name: string;
}

interface AdInsights extends InsightsData {
  ad_name: string;
}

interface WeeklyComparison {
  this_week: InsightsData;
  last_week: InsightsData;
  spend_change: number;
  roas_change: number;
  conversion_change: number;
}

interface Action {
  action_type: string;
  value: string;
}

interface ActionValue {
  action_type: string;
  value: string;
}

interface MetaInsightsResponse {
  spend: string;
  impressions: string;
  clicks: string;
  reach: string;
  frequency: string;
  purchase_roas?: Array<{ value: string }>;
  actions?: Action[];
  action_values?: ActionValue[];
  ctr: string;
  cpm: string;
  cpc?: string;
  adset_name?: string;
  ad_id?: string;
}

interface MetaAd {
  id: string;
  name: string;
  status: string;
}

class MetaAdsManager {
  private accessToken: string;
  private adAccountId: string;
  private baseUrl: string = 'https://graph.facebook.com/v18.0';

  constructor(accessToken: string, adAccountId: string) {
    this.accessToken = accessToken;
    this.adAccountId = adAccountId;
  }

  async getAccountPerformance(datePreset: string = 'today'): Promise<InsightsData | null> {
    const url = `${this.baseUrl}/act_${this.adAccountId}/insights`;
    const params = new URLSearchParams({
      access_token: this.accessToken,
      fields: 'spend,impressions,clicks,conversions,purchase_roas,ctr,cpm,cpc,cpp,frequency,reach,actions,action_values',
      date_preset: datePreset,
      level: 'account'
    });

    try {
      const response = await fetch(`${url}?${params}`);
      if (response.status === 200) {
        const result = await response.json();
        const data = result.data || [];
        if (data.length > 0) {
          return this.parseInsights(data[0]);
        }
      }
      return null;
    } catch (error) {
      console.error(`계정 성과 조회 실패: ${error}`);
      return null;
    }
  }

  async getAdsetPerformance(datePreset: string = 'today', limit: number = 5): Promise<AdsetInsights[]> {
    const url = `${this.baseUrl}/act_${this.adAccountId}/insights`;
    const params = new URLSearchParams({
      access_token: this.accessToken,
      fields: 'adset_name,spend,impressions,clicks,conversions,purchase_roas,ctr,frequency',
      date_preset: datePreset,
      level: 'adset',
      filtering: JSON.stringify([{ field: 'spend', operator: 'GREATER_THAN', value: 0 }]),
      sort: JSON.stringify(['spend_descending']),
      limit: limit.toString()
    });

    try {
      const response = await fetch(`${url}?${params}`);
      if (response.status === 200) {
        const result = await response.json();
        const data = result.data || [];
        return data.slice(0, limit).map((item: MetaInsightsResponse) => this.parseAdsetInsights(item));
      }
      return [];
    } catch (error) {
      console.error(`광고세트 성과 조회 실패: ${error}`);
      return [];
    }
  }

  async getAdPerformance(datePreset: string = 'today', limit: number = 15): Promise<AdInsights[]> {
    // 먼저 광고 ID와 이름 가져오기
    const adsUrl = `${this.baseUrl}/act_${this.adAccountId}/ads`;
    const adsParams = new URLSearchParams({
      access_token: this.accessToken,
      fields: 'id,name,status',
      filtering: JSON.stringify([{ field: 'effective_status', operator: 'IN', value: ['ACTIVE', 'PAUSED'] }]),
      limit: '50'
    });

    try {
      // 광고 메타데이터 가져오기
      const adsResponse = await fetch(`${adsUrl}?${adsParams}`);
      if (adsResponse.status !== 200) {
        return [];
      }

      const adsResult = await adsResponse.json();
      const adsData: MetaAd[] = adsResult.data || [];
      const adNames: { [key: string]: string } = {};
      adsData.forEach(ad => {
        adNames[ad.id] = ad.name;
      });

      // 인사이트 데이터 가져오기
      const insightsUrl = `${this.baseUrl}/act_${this.adAccountId}/insights`;
      const insightsParams = new URLSearchParams({
        access_token: this.accessToken,
        fields: 'ad_id,spend,impressions,clicks,conversions,purchase_roas,ctr,actions',
        date_preset: datePreset,
        level: 'ad',
        filtering: JSON.stringify([{ field: 'spend', operator: 'GREATER_THAN', value: 0 }]),
        sort: JSON.stringify(['spend_descending']),
        limit: limit.toString()
      });

      const response = await fetch(`${insightsUrl}?${insightsParams}`);
      if (response.status === 200) {
        const result = await response.json();
        const data = result.data || [];
        const results: AdInsights[] = [];
        
        for (const item of data.slice(0, limit)) {
          const parsed = this.parseAdInsights(item);
          const adId = item.ad_id || '';
          parsed.ad_name = adNames[adId] || `광고 ID: ${adId}`;
          results.push(parsed);
        }
        
        return results;
      }
      return [];
    } catch (error) {
      console.error(`개별 광고 성과 조회 실패: ${error}`);
      return [];
    }
  }

  async getWeeklyComparison(): Promise<WeeklyComparison | null> {
    const thisWeek = await this.getAccountPerformance('this_week');
    const lastWeek = await this.getAccountPerformance('last_week');

    if (thisWeek && lastWeek) {
      return {
        this_week: thisWeek,
        last_week: lastWeek,
        spend_change: lastWeek.spend > 0 
          ? ((thisWeek.spend - lastWeek.spend) / lastWeek.spend * 100) 
          : 0,
        roas_change: thisWeek.roas - lastWeek.roas,
        conversion_change: lastWeek.conversions > 0 
          ? ((thisWeek.conversions - lastWeek.conversions) / lastWeek.conversions * 100) 
          : 0
      };
    }
    return null;
  }

  private parseInsights(insights: MetaInsightsResponse): InsightsData {
    const spend = parseFloat(insights.spend || '0');
    const impressions = parseInt(insights.impressions || '0');
    const clicks = parseInt(insights.clicks || '0');
    const reach = parseInt(insights.reach || '0');
    const frequency = parseFloat(insights.frequency || '0');

    // ROAS 처리
    const roasData = insights.purchase_roas || [];
    const roas = roasData.length > 0 ? parseFloat(roasData[0].value || '0') : 0;

    // 전환 데이터 처리
    let conversions = 0;
    let conversionValue = 0;
    const actions = insights.actions || [];
    const actionValues = insights.action_values || [];

    for (const action of actions) {
      if (action.action_type === 'purchase') {
        conversions = parseInt(action.value || '0');
        break;
      }
    }

    for (const value of actionValues) {
      if (value.action_type === 'purchase') {
        conversionValue = parseFloat(value.value || '0');
        break;
      }
    }

    const ctr = parseFloat(insights.ctr || '0');
    const cpm = parseFloat(insights.cpm || '0');
    const cpc = insights.cpc 
      ? parseFloat(insights.cpc) 
      : (clicks > 0 ? spend / clicks : 0);
    const cac = conversions > 0 ? spend / conversions : 0;

    // 랜딩페이지 전환율 계산 (클릭 대비 구매)
    const landingConversionRate = clicks > 0 ? (conversions / clicks * 100) : 0;

    return {
      spend,
      impressions,
      clicks,
      conversions,
      conversion_value: conversionValue,
      roas,
      ctr,
      cpm,
      cpc,
      cac,
      reach,
      frequency,
      landing_conversion_rate: landingConversionRate
    };
  }

  private parseAdsetInsights(insights: MetaInsightsResponse): AdsetInsights {
    const base = this.parseInsights(insights);
    return {
      ...base,
      adset_name: insights.adset_name || 'Unknown'
    };
  }

  private parseAdInsights(insights: MetaInsightsResponse): AdInsights {
    const base = this.parseInsights(insights);
    return {
      ...base,
      ad_name: '' // ad_name은 별도로 처리됨
    };
  }

  formatComprehensiveReport(
    accountPerf: InsightsData | null,
    ads: AdInsights[],
    weeklyComp: WeeklyComparison | null
  ): string {
    // 한국 시간으로 변환 (UTC+9)
    const koreaTime = new Date();
    koreaTime.setHours(koreaTime.getHours() + 9);
    const year = koreaTime.getFullYear();
    const month = String(koreaTime.getMonth() + 1).padStart(2, '0');
    const day = String(koreaTime.getDate()).padStart(2, '0');
    const today = `${year}-${month}-${day}`;
    
    let message = `📊 *${today} Meta 광고 종합 리포트*\n\n`;

    // 1. 계정 전체 성과
    if (accountPerf) {
      message += "📈 *전체 성과*\n";
      message += `• 광고비: ${accountPerf.spend.toLocaleString('ko-KR', { maximumFractionDigits: 0 })}원\n`;
      message += `• ROAS: ${accountPerf.roas.toFixed(2)}배\n`;
      message += `• 전환수: ${accountPerf.conversions}건\n`;
      message += `• 전환 매출: ${accountPerf.conversion_value.toLocaleString('ko-KR', { maximumFractionDigits: 0 })}원\n`;
      message += `• 도달: ${accountPerf.reach.toLocaleString('ko-KR')}명 (빈도: ${accountPerf.frequency.toFixed(1)})\n`;
      message += `• CTR: ${accountPerf.ctr.toFixed(2)}% | CPM: ${accountPerf.cpm.toLocaleString('ko-KR', { maximumFractionDigits: 0 })}원\n`;
      message += `• CPC: ${accountPerf.cpc.toLocaleString('ko-KR', { maximumFractionDigits: 0 })}원 | CAC: ${accountPerf.cac.toLocaleString('ko-KR', { maximumFractionDigits: 0 })}원\n`;
      message += `• 랜딩 전환율: ${accountPerf.landing_conversion_rate.toFixed(2)}%\n\n`;
    }

    // 2. 주간 비교
    if (weeklyComp) {
      message += "📅 *주간 비교*\n";
      const spendEmoji = weeklyComp.spend_change > 0 ? "📈" : "📉";
      const roasEmoji = weeklyComp.roas_change > 0 ? "📈" : "📉";
      const convEmoji = weeklyComp.conversion_change > 0 ? "📈" : "📉";

      message += `• 광고비: ${spendEmoji} ${weeklyComp.spend_change >= 0 ? '+' : ''}${weeklyComp.spend_change.toFixed(1)}%\n`;
      message += `• ROAS: ${roasEmoji} ${weeklyComp.roas_change >= 0 ? '+' : ''}${weeklyComp.roas_change.toFixed(2)}\n`;
      message += `• 전환: ${convEmoji} ${weeklyComp.conversion_change >= 0 ? '+' : ''}${weeklyComp.conversion_change.toFixed(1)}%\n\n`;
    }

    // 3. 소재별 성과
    if (ads.length > 0) {
      message += "🎨 *소재별 성과*\n";
      ads.forEach((ad, index) => {
        const name = ad.ad_name.length > 25 
          ? ad.ad_name.substring(0, 25) 
          : ad.ad_name;
        // 간결한 한 줄 포맷
        const num = (index + 1).toString().padStart(2, ' ');
        const nameFormatted = name.padEnd(25, ' ');
        const spendK = (ad.spend / 1000).toFixed(0);
        message += `${num}. ${nameFormatted} | ${spendK}k원 | ROAS:${ad.roas.toFixed(1)} | CTR:${ad.ctr.toFixed(1)}%\n`;
      });
      message += "\n";
    }

    // 4. 인사이트 및 추천
    message += this.generateInsights(accountPerf, ads);

    return message;
  }

  private generateInsights(accountPerf: InsightsData | null, ads: AdInsights[]): string {
    let insights = "💡 *인사이트*\n";

    if (!accountPerf) {
      return insights + "• 데이터 없음\n";
    }

    // ROAS 기반 인사이트
    if (accountPerf.roas < 1.0) {
      insights += "⚠️ ROAS가 1.0 미만입니다. 광고 최적화가 시급합니다.\n";
    } else if (accountPerf.roas < 1.5) {
      insights += "📊 ROAS 개선이 필요합니다. 타겟팅 재검토를 권장합니다.\n";
    } else if (accountPerf.roas > 3.0) {
      insights += "🎉 우수한 ROAS! 예산 증액을 고려해보세요.\n";
    }

    // CTR 기반 인사이트
    if (accountPerf.ctr < 1.0) {
      insights += "• 낮은 CTR - 광고 크리에이티브 개선 필요\n";
    } else if (accountPerf.ctr > 2.0) {
      insights += "• 높은 CTR - 광고가 타겟에게 잘 어필하고 있습니다\n";
    }

    // 빈도 기반 인사이트
    if (accountPerf.frequency > 3.0) {
      insights += "• 광고 피로도 주의 - 새로운 크리에이티브 추가 권장\n";
    }

    // 소재 다양성
    if (ads.length > 10) {
      insights += "• 활성 소재가 많습니다. 저성과 소재 정리를 고려해보세요.\n";
    }

    return insights;
  }
}

async function sendToSlack(webhookUrl: string, message: string): Promise<boolean> {
  const payload = {
    text: message,
    username: "메타 광고 분석봇",
    icon_emoji: ":chart_with_upwards_trend:"
  };

  try {
    const response = await fetch(webhookUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    });
    return response.status === 200;
  } catch (error) {
    console.error('Slack 전송 실패:', error);
    return false;
  }
}

// Vercel serverless function handler
export default async function handler(req: VercelRequest, res: VercelResponse) {
  // 크론잡에서 호출되는 GET 또는 POST 요청 처리
  if (req.method !== 'GET' && req.method !== 'POST') {
    res.setHeader('Allow', ['GET', 'POST']);
    return res.status(405).json({ error: `Method ${req.method} not allowed` });
  }

  // 환경 변수에서 설정 읽기
  const SLACK_WEBHOOK_URL = process.env.SLACK_WEBHOOK_URL;
  const META_ACCESS_TOKEN = process.env.META_ACCESS_TOKEN;
  const META_AD_ACCOUNT_ID = process.env.META_AD_ACCOUNT_ID;

  if (!SLACK_WEBHOOK_URL || !META_ACCESS_TOKEN || !META_AD_ACCOUNT_ID) {
    return res.status(500).json({ error: 'Missing required environment variables' });
  }

  try {
    // Meta 광고 매니저 초기화
    const manager = new MetaAdsManager(META_ACCESS_TOKEN, META_AD_ACCOUNT_ID);

    // 데이터 수집
    const [accountPerf, ads, weeklyComp] = await Promise.all([
      manager.getAccountPerformance(),
      manager.getAdPerformance(),
      manager.getWeeklyComparison()
    ]);

    // 리포트 생성
    const message = manager.formatComprehensiveReport(
      accountPerf,
      ads,
      weeklyComp
    );

    // 슬랙으로 전송
    const slackSuccess = await sendToSlack(SLACK_WEBHOOK_URL, message);
    
    if (slackSuccess) {
      return res.status(200).json({
        success: true,
        message: 'Comprehensive report sent successfully'
      });
    } else {
      return res.status(500).json({
        success: false,
        message: 'Failed to send slack message'
      });
    }
  } catch (error) {
    const errorMessage = `❌ 광고 리포트 생성 실패: ${error}`;
    await sendToSlack(SLACK_WEBHOOK_URL!, errorMessage);
    
    return res.status(500).json({
      success: false,
      error: String(error)
    });
  }
}