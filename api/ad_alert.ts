/**
 * Vercel Serverless Function for Ad Performance Alert System
 * Monitors ad performance and sends alerts when metrics deteriorate
 */

import type { VercelRequest, VercelResponse } from '@vercel/node';

// Type definitions
interface DailyAdData {
  date: string;
  ad_id: string;
  ad_name: string;
  spend: number;
  impressions: number;
  clicks: number;
  conversions: number;
  conversion_value: number;
  ctr: number;
  cpc: number;
  cac: number;
  roas: number;
  thumbnail_url?: string;
}

interface AdTrendAnalysis {
  ad_id: string;
  ad_name: string;
  ctr_declining_days: number;
  cpc_increasing_days: number;
  cac_increasing_days: number;
  latest_roas: number;
  alert_level: AlertLevel;
  thumbnail_url?: string;
  metrics_summary: {
    ctr_change: number[];  // Percentage changes for last 3 days
    cpc_change: number[];
    cac_change: number[];
  };
}

enum AlertLevel {
  NORMAL = 0,
  CAUTION = 1,    // Level 1 - 주의
  WARNING = 2,    // Level 2 - 위험  
  CRITICAL = 3    // Level 3 - 긴급
}

class AdAlertManager {
  private accessToken: string;
  private adAccountId: string;
  private slackWebhookUrl: string;
  private baseUrl: string = 'https://graph.facebook.com/v18.0';

  constructor(accessToken: string, adAccountId: string, slackWebhookUrl: string) {
    this.accessToken = accessToken;
    this.adAccountId = adAccountId;
    this.slackWebhookUrl = slackWebhookUrl;
  }

  /**
   * Get ad creative thumbnails for a list of ad IDs
   */
  async getAdCreativeThumbnails(adIds: string[]): Promise<Map<string, string>> {
    const thumbnailMap = new Map<string, string>();
    
    for (const adId of adIds) {
      try {
        // Get ad creative info
        const url = `${this.baseUrl}/${adId}`;
        const params = new URLSearchParams({
          access_token: this.accessToken,
          fields: 'creative{thumbnail_url,image_url,object_story_spec}'
        });

        const response = await fetch(`${url}?${params}`);
        if (response.status === 200) {
          const result = await response.json();
          
          // Try to get thumbnail URL from various sources
          let thumbnailUrl = null;
          
          if (result.creative) {
            // Direct thumbnail_url
            if (result.creative.thumbnail_url) {
              thumbnailUrl = result.creative.thumbnail_url;
            }
            // Or image_url
            else if (result.creative.image_url) {
              thumbnailUrl = result.creative.image_url;
            }
            // Or from object_story_spec
            else if (result.creative.object_story_spec?.link_data?.image_hash) {
              // If we have image hash, we need to construct the URL
              const imageHash = result.creative.object_story_spec.link_data.image_hash;
              thumbnailUrl = `https://scontent.xx.fbcdn.net/v/t45.1600-4/${imageHash}`;
            }
            else if (result.creative.object_story_spec?.video_data?.image_url) {
              thumbnailUrl = result.creative.object_story_spec.video_data.image_url;
            }
          }
          
          if (thumbnailUrl) {
            thumbnailMap.set(adId, thumbnailUrl);
          }
        }
      } catch (error) {
        console.error(`Error fetching creative for ad ${adId}:`, error);
      }
    }
    
    return thumbnailMap;
  }

  /**
   * Get daily performance data for all ads over the last 4 days
   */
  async getDailyAdPerformance(): Promise<Map<string, DailyAdData[]> | null> {
    const today = new Date();
    const fourDaysAgo = new Date(today);
    fourDaysAgo.setDate(today.getDate() - 3);

    const since = fourDaysAgo.toISOString().split('T')[0];
    const until = today.toISOString().split('T')[0];

    const url = `${this.baseUrl}/act_${this.adAccountId}/insights`;
    const params = new URLSearchParams({
      access_token: this.accessToken,
      fields: 'ad_id,ad_name,spend,impressions,clicks,conversions,purchase_roas,ctr,cpc,cpp,actions,action_values',
      level: 'ad',
      time_increment: '1', // Daily breakdown
      time_range: JSON.stringify({ since, until }),
      filtering: JSON.stringify([{ field: 'ad.effective_status', operator: 'IN', value: ['ACTIVE'] }])
    });

    try {
      const response = await fetch(`${url}?${params}`);
      if (response.status === 200) {
        const result = await response.json();
        const data = result.data || [];
        
        // Group data by ad_id
        const adDataMap = new Map<string, DailyAdData[]>();
        
        for (const dayData of data) {
          const parsed = this.parseDailyInsights(dayData);
          if (parsed) {
            const adId = parsed.ad_id;
            if (!adDataMap.has(adId)) {
              adDataMap.set(adId, []);
            }
            adDataMap.get(adId)!.push(parsed);
          }
        }

        // Sort each ad's data by date
        for (const [adId, adData] of adDataMap) {
          adData.sort((a, b) => a.date.localeCompare(b.date));
        }

        return adDataMap;
      }
      return null;
    } catch (error) {
      console.error('Error fetching daily ad performance:', error);
      return null;
    }
  }

  /**
   * Parse daily insights data
   */
  private parseDailyInsights(data: any): DailyAdData | null {
    try {
      const spend = parseFloat(data.spend || '0');
      const impressions = parseInt(data.impressions || '0');
      const clicks = parseInt(data.clicks || '0');
      
      // Extract conversions
      let conversions = 0;
      let conversion_value = 0;
      
      if (data.actions) {
        const purchaseAction = data.actions.find((a: any) => 
          a.action_type === 'purchase' || a.action_type === 'omni_purchase'
        );
        if (purchaseAction) {
          conversions = parseInt(purchaseAction.value || '0');
        }
      }

      if (data.action_values) {
        const purchaseValue = data.action_values.find((a: any) => 
          a.action_type === 'purchase' || a.action_type === 'omni_purchase'
        );
        if (purchaseValue) {
          conversion_value = parseFloat(purchaseValue.value || '0');
        }
      }

      const ctr = parseFloat(data.ctr || '0');
      const cpc = parseFloat(data.cpc || '0');
      const cac = conversions > 0 ? spend / conversions : 0;
      const roas = spend > 0 ? conversion_value / spend : 0;

      return {
        date: data.date_start,
        ad_id: data.ad_id,
        ad_name: data.ad_name || `Ad ${data.ad_id}`,
        spend,
        impressions,
        clicks,
        conversions,
        conversion_value,
        ctr,
        cpc,
        cac,
        roas
      };
    } catch (error) {
      console.error('Error parsing daily insights:', error);
      return null;
    }
  }

  /**
   * Analyze trends for each ad
   */
  async analyzeAdTrends(adDataMap: Map<string, DailyAdData[]>): Promise<AdTrendAnalysis[]> {
    const analyses: AdTrendAnalysis[] = [];
    
    // Get thumbnails for all ads
    const adIds = Array.from(adDataMap.keys());
    const thumbnailMap = await this.getAdCreativeThumbnails(adIds);

    for (const [adId, adData] of adDataMap) {
      if (adData.length < 2) continue; // Need at least 2 days of data

      const analysis: AdTrendAnalysis = {
        ad_id: adId,
        ad_name: adData[adData.length - 1].ad_name,
        ctr_declining_days: 0,
        cpc_increasing_days: 0,
        cac_increasing_days: 0,
        latest_roas: adData[adData.length - 1].roas,
        alert_level: AlertLevel.NORMAL,
        thumbnail_url: thumbnailMap.get(adId),
        metrics_summary: {
          ctr_change: [],
          cpc_change: [],
          cac_change: []
        }
      };

      // Analyze last 3 transitions (if we have 4 days of data)
      for (let i = Math.max(1, adData.length - 3); i < adData.length; i++) {
        const prev = adData[i - 1];
        const curr = adData[i];

        // CTR analysis
        if (prev.ctr > 0) {
          const ctrChange = ((curr.ctr - prev.ctr) / prev.ctr) * 100;
          analysis.metrics_summary.ctr_change.push(ctrChange);
          if (ctrChange < 0) {
            analysis.ctr_declining_days++;
          } else {
            analysis.ctr_declining_days = 0; // Reset if improved
          }
        }

        // CPC analysis
        if (prev.cpc > 0) {
          const cpcChange = ((curr.cpc - prev.cpc) / prev.cpc) * 100;
          analysis.metrics_summary.cpc_change.push(cpcChange);
          if (cpcChange > 0) {
            analysis.cpc_increasing_days++;
          } else {
            analysis.cpc_increasing_days = 0; // Reset if improved
          }
        }

        // CAC analysis
        if (prev.cac > 0) {
          const cacChange = ((curr.cac - prev.cac) / prev.cac) * 100;
          analysis.metrics_summary.cac_change.push(cacChange);
          if (cacChange > 0) {
            analysis.cac_increasing_days++;
          } else {
            analysis.cac_increasing_days = 0; // Reset if improved
          }
        }
      }

      // Determine alert level
      analysis.alert_level = this.calculateAlertLevel(analysis);
      analyses.push(analysis);
    }

    return analyses;
  }

  /**
   * Calculate alert level based on metrics
   */
  private calculateAlertLevel(analysis: AdTrendAnalysis): AlertLevel {
    const { ctr_declining_days, cpc_increasing_days, cac_increasing_days, latest_roas } = analysis;

    // Level 3 - Critical: 3 days of deterioration AND ROAS ≤ 1.2
    if (ctr_declining_days >= 3 && cpc_increasing_days >= 3 && cac_increasing_days >= 3 && latest_roas <= 1.2) {
      return AlertLevel.CRITICAL;
    }

    // Level 2 - Warning
    if (ctr_declining_days >= 3 && cpc_increasing_days >= 3 && latest_roas < 1.5) {
      return AlertLevel.WARNING;
    }

    // Level 1 - Caution
    if (ctr_declining_days >= 2 || cpc_increasing_days >= 2 || cac_increasing_days >= 2 || latest_roas < 2.0) {
      return AlertLevel.CAUTION;
    }

    return AlertLevel.NORMAL;
  }

  /**
   * Send individual Slack alerts for ads with issues
   */
  async sendIndividualAlerts(analyses: AdTrendAnalysis[]): Promise<void> {
    // First, send summary message
    const alertCounts = {
      caution: analyses.filter(a => a.alert_level === AlertLevel.CAUTION).length,
      warning: analyses.filter(a => a.alert_level === AlertLevel.WARNING).length,
      critical: analyses.filter(a => a.alert_level === AlertLevel.CRITICAL).length
    };

    const summaryMessage = {
      blocks: [
        {
          type: "header",
          text: {
            type: "plain_text",
            text: "📊 광고 성과 모니터링",
            emoji: true
          }
        },
        {
          type: "section",
          text: {
            type: "mrkdwn",
            text: `*${new Date().toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' })}*\n` +
                  `총 ${analyses.length}개 광고 분석 완료\n` +
                  `━━━━━━━━━━━━━━━━━━━━\n` +
                  `🟡 주의: ${alertCounts.caution}개\n` +
                  `🟠 위험: ${alertCounts.warning}개\n` +
                  `🔴 긴급: ${alertCounts.critical}개`
          }
        }
      ]
    };

    await this.sendSlackMessage(summaryMessage);

    // Send individual alerts with 2-second delay between messages
    const alertedAds = analyses.filter(a => a.alert_level > AlertLevel.NORMAL);
    
    for (const analysis of alertedAds) {
      await new Promise(resolve => setTimeout(resolve, 2000)); // 2 second delay
      await this.sendAdAlert(analysis);
    }
  }

  /**
   * Send individual ad alert
   */
  private async sendAdAlert(analysis: AdTrendAnalysis): Promise<void> {
    const levelEmoji = {
      [AlertLevel.CAUTION]: '🟡',
      [AlertLevel.WARNING]: '🟠',
      [AlertLevel.CRITICAL]: '🔴'
    };

    const levelText = {
      [AlertLevel.CAUTION]: '주의',
      [AlertLevel.WARNING]: '위험',
      [AlertLevel.CRITICAL]: '긴급'
    };

    const ctrChanges = analysis.metrics_summary.ctr_change.map(c => `${c.toFixed(1)}%`).join(' → ');
    const cpcChanges = analysis.metrics_summary.cpc_change.map(c => `${c > 0 ? '+' : ''}${c.toFixed(1)}%`).join(' → ');
    const cacChanges = analysis.metrics_summary.cac_change.map(c => `${c > 0 ? '+' : ''}${c.toFixed(1)}%`).join(' → ');

    const blocks: any[] = [];
    
    // If we have a thumbnail, add an image block first
    if (analysis.thumbnail_url) {
      blocks.push({
        type: "image",
        image_url: analysis.thumbnail_url,
        alt_text: analysis.ad_name
      });
    }
    
    // Add the main content block
    blocks.push({
      type: "section",
      text: {
        type: "mrkdwn",
        text: `${levelEmoji[analysis.alert_level]} *${levelText[analysis.alert_level]}: ${analysis.ad_name}*\n` +
              `━━━━━━━━━━━━━━━━━━━━\n` +
              `• CTR: ${analysis.ctr_declining_days}일 연속 하락 (${ctrChanges})\n` +
              `• CPC: ${analysis.cpc_increasing_days}일 연속 상승 (${cpcChanges})\n` +
              `• CAC: ${analysis.cac_increasing_days}일 연속 상승 (${cacChanges})\n` +
              `• ROAS: ${analysis.latest_roas.toFixed(2)} ${analysis.latest_roas <= 1.2 ? '⚠️' : ''}\n` +
              `━━━━━━━━━━━━━━━━━━━━\n` +
              `→ ${this.getRecommendation(analysis.alert_level)}`
      }
    });
    
    // If we have a thumbnail and want it as an accessory, use this format instead:
    // blocks.push({
    //   type: "section",
    //   text: { ... },
    //   accessory: {
    //     type: "image",
    //     image_url: analysis.thumbnail_url,
    //     alt_text: analysis.ad_name
    //   }
    // });

    const message = { blocks };

    await this.sendSlackMessage(message);
  }

  /**
   * Get recommendation based on alert level
   */
  private getRecommendation(level: AlertLevel): string {
    switch (level) {
      case AlertLevel.CRITICAL:
        return '즉시 검토 필요! 광고 중단 고려';
      case AlertLevel.WARNING:
        return '크리에이티브 교체 검토';
      case AlertLevel.CAUTION:
        return '모니터링 강화 필요';
      default:
        return '정상 운영 중';
    }
  }

  /**
   * Send message to Slack
   */
  private async sendSlackMessage(message: any): Promise<void> {
    try {
      await fetch(this.slackWebhookUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(message)
      });
    } catch (error) {
      console.error('Error sending Slack message:', error);
    }
  }
}

// Main handler function
export default async function handler(req: VercelRequest, res: VercelResponse) {
  // Get environment variables
  const slackWebhookUrl = process.env.SLACK_WEBHOOK_URL;
  const metaAccessToken = process.env.META_ACCESS_TOKEN;
  const metaAdAccountId = process.env.META_AD_ACCOUNT_ID;

  // Validate environment variables
  if (!slackWebhookUrl || !metaAccessToken || !metaAdAccountId) {
    return res.status(500).json({
      error: 'Missing required environment variables',
      required: ['SLACK_WEBHOOK_URL', 'META_ACCESS_TOKEN', 'META_AD_ACCOUNT_ID']
    });
  }

  try {
    const alertManager = new AdAlertManager(metaAccessToken, metaAdAccountId, slackWebhookUrl);

    // Get daily performance data
    const adDataMap = await alertManager.getDailyAdPerformance();
    if (!adDataMap || adDataMap.size === 0) {
      return res.status(200).json({
        success: true,
        message: 'No active ads found or unable to fetch data'
      });
    }

    // Analyze trends (now async because it fetches thumbnails)
    const analyses = await alertManager.analyzeAdTrends(adDataMap);

    // Send alerts
    await alertManager.sendIndividualAlerts(analyses);

    return res.status(200).json({
      success: true,
      message: `Analyzed ${analyses.length} ads, sent alerts for ${analyses.filter(a => a.alert_level > 0).length} ads`
    });

  } catch (error) {
    console.error('Error in ad alert handler:', error);
    return res.status(500).json({
      error: 'Internal server error',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
}