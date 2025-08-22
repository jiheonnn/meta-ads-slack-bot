declare global {
  namespace NodeJS {
    interface ProcessEnv {
      SLACK_WEBHOOK_URL: string;
      META_ACCESS_TOKEN: string;
      META_AD_ACCOUNT_ID: string;
      NODE_ENV?: 'development' | 'production' | 'test';
    }
  }
}

export {};