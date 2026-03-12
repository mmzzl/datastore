export interface Stock {
  code: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  amount: number;
  open: number;
  high: number;
  low: number;
  close: number;
  prevClose: number;
  turnover: number;
  pe: number;
  pb: number;
  marketCap: number;
  sector: string;
  industry: string;
}

export interface StockKLine {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface StockRealtime {
  code: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  amount: number;
  timestamp: number;
}

export interface Portfolio {
  id: string;
  stocks: PortfolioStock[];
  totalValue: number;
  totalCost: number;
  totalGain: number;
  totalGainPercent: number;
}

export interface PortfolioStock {
  code: string;
  name: string;
  shares: number;
  avgCost: number;
  currentPrice: number;
  marketValue: number;
  gain: number;
  gainPercent: number;
}
