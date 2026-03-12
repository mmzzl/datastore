import { Stock, StockKLine, Portfolio } from '../types/stock';

export const stockList: Stock[] = [
  {
    code: '000001',
    name: '平安银行',
    price: 12.85,
    change: 0.23,
    changePercent: 1.82,
    volume: 45678900,
    amount: 584236000,
    open: 12.60,
    high: 12.95,
    low: 12.55,
    close: 12.62,
    prevClose: 12.62,
    turnover: 2.35,
    pe: 6.82,
    pb: 0.65,
    marketCap: 248600000000,
    sector: '金融',
    industry: '银行'
  },
  {
    code: '000002',
    name: '万科A',
    price: 8.92,
    change: -0.15,
    changePercent: -1.65,
    volume: 32456700,
    amount: 289234000,
    open: 9.05,
    high: 9.12,
    low: 8.85,
    close: 9.07,
    prevClose: 9.07,
    turnover: 1.89,
    pe: 8.45,
    pb: 0.72,
    marketCap: 103500000000,
    sector: '房地产',
    industry: '房地产开发'
  },
  {
    code: '600519',
    name: '贵州茅台',
    price: 1685.50,
    change: 25.30,
    changePercent: 1.52,
    volume: 2345670,
    amount: 3948231000,
    open: 1660.00,
    high: 1692.00,
    low: 1655.00,
    close: 1660.20,
    prevClose: 1660.20,
    turnover: 0.85,
    pe: 32.15,
    pb: 8.92,
    marketCap: 2116000000000,
    sector: '食品饮料',
    industry: '白酒'
  },
  {
    code: '600036',
    name: '招商银行',
    price: 35.82,
    change: 0.45,
    changePercent: 1.27,
    volume: 28765400,
    amount: 1023456000,
    open: 35.40,
    high: 36.10,
    low: 35.25,
    close: 35.37,
    prevClose: 35.37,
    turnover: 1.45,
    pe: 7.23,
    pb: 1.15,
    marketCap: 897800000000,
    sector: '金融',
    industry: '银行'
  },
  {
    code: '000858',
    name: '五粮液',
    price: 142.30,
    change: -2.15,
    changePercent: -1.49,
    volume: 8923400,
    amount: 1267890000,
    open: 144.50,
    high: 145.20,
    low: 141.80,
    close: 144.45,
    prevClose: 144.45,
    turnover: 1.68,
    pe: 18.92,
    pb: 4.85,
    marketCap: 552300000000,
    sector: '食品饮料',
    industry: '白酒'
  },
  {
    code: '601318',
    name: '中国平安',
    price: 48.25,
    change: 0.78,
    changePercent: 1.64,
    volume: 45678900,
    amount: 2194567000,
    open: 47.50,
    high: 48.65,
    low: 47.35,
    close: 47.47,
    prevClose: 47.47,
    turnover: 2.15,
    pe: 9.85,
    pb: 1.22,
    marketCap: 883200000000,
    sector: '金融',
    industry: '保险'
  },
  {
    code: '000333',
    name: '美的集团',
    price: 58.90,
    change: 1.25,
    changePercent: 2.17,
    volume: 19876500,
    amount: 1169234000,
    open: 57.65,
    high: 59.20,
    low: 57.50,
    close: 57.65,
    prevClose: 57.65,
    turnover: 1.92,
    pe: 12.45,
    pb: 3.25,
    marketCap: 413500000000,
    sector: '家用电器',
    industry: '家电'
  },
  {
    code: '600900',
    name: '长江电力',
    price: 23.45,
    change: -0.08,
    changePercent: -0.34,
    volume: 12345600,
    amount: 289456000,
    open: 23.55,
    high: 23.68,
    low: 23.32,
    close: 23.53,
    prevClose: 23.53,
    turnover: 0.65,
    pe: 18.25,
    pb: 2.35,
    marketCap: 536700000000,
    sector: '公用事业',
    industry: '电力'
  }
];

const generateKLineData = (basePrice: number, days: number): StockKLine[] => {
  const data: StockKLine[] = [];
  let currentPrice = basePrice * 0.85;
  const startDate = new Date('2024-01-01');

  for (let i = 0; i < days; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);
    
    const change = (Math.random() - 0.48) * currentPrice * 0.04;
    const open = currentPrice;
    const close = currentPrice + change;
    const high = Math.max(open, close) + Math.random() * currentPrice * 0.02;
    const low = Math.min(open, close) - Math.random() * currentPrice * 0.02;
    const volume = Math.floor(1000000 + Math.random() * 5000000);

    data.push({
      date: date.toISOString().split('T')[0],
      open: Number(open.toFixed(2)),
      high: Number(high.toFixed(2)),
      low: Number(low.toFixed(2)),
      close: Number(close.toFixed(2)),
      volume
    });

    currentPrice = close;
  }

  return data;
};

export const stockKLineData: Record<string, StockKLine[]> = {
  '000001': generateKLineData(12.62, 120),
  '000002': generateKLineData(9.07, 120),
  '600519': generateKLineData(1660.20, 120),
  '600036': generateKLineData(35.37, 120),
  '000858': generateKLineData(144.45, 120),
  '601318': generateKLineData(47.47, 120),
  '000333': generateKLineData(57.65, 120),
  '600900': generateKLineData(23.53, 120)
};

export const defaultPortfolio: Portfolio = {
  id: '1',
  stocks: [
    {
      code: '600519',
      name: '贵州茅台',
      shares: 100,
      avgCost: 1450.00,
      currentPrice: 1685.50,
      marketValue: 168550,
      gain: 23550,
      gainPercent: 16.24
    },
    {
      code: '000001',
      name: '平安银行',
      shares: 1000,
      avgCost: 11.50,
      currentPrice: 12.85,
      marketValue: 12850,
      gain: 1350,
      gainPercent: 11.74
    },
    {
      code: '600036',
      name: '招商银行',
      shares: 500,
      avgCost: 32.00,
      currentPrice: 35.82,
      marketValue: 17910,
      gain: 1910,
      gainPercent: 11.94
    }
  ],
  totalValue: 199310,
  totalCost: 177500,
  totalGain: 21810,
  totalGainPercent: 12.29
};

export const getStockByCode = (code: string): Stock | undefined => {
  return stockList.find(s => s.code === code);
};

export const getStockKLine = (code: string): StockKLine[] => {
  return stockKLineData[code] || [];
};
