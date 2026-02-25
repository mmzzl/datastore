export interface Strategy {
  id: string;
  name: string;
  description: string;
  type: 'default' | 'custom';
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  score: number;
  buyRules: Rule[];
  sellRules: Rule[];
  positionSize: number; // 仓位比例，0-100%
  stopLoss: number; // 止损比例，负数表示亏损百分比
  takeProfit: number; // 止盈比例，正数表示盈利百分比
  backtestResults?: BacktestResult;
}

export interface Rule {
  id: string;
  indicator: Indicator;
  operator: Operator;
  value: number;
  timeframe?: number; // 时间周期，如MA5的5
}

export type Indicator = 
  | 'MA' // 移动平均线
  | 'RSI' // 相对强弱指标
  | 'MACD' // 平滑异同移动平均线
  | 'BB' // 布林带
  | 'VOL' // 成交量
  | 'PRICE' // 价格
  | 'KDJ' // 随机指标
  | 'ADX' // 平均趋向指数
  | 'CCI'; // 顺势指标

export type Operator = '>' | '<' | '>=' | '<=' | '=';

export interface BacktestResult {
  id: string;
  strategyId: string;
  startTime: string;
  endTime: string;
  initialCapital: number;
  finalCapital: number;
  totalReturn: number;
  annualReturn: number;
  maxDrawdown: number;
  sharpeRatio: number;
  sortinoRatio: number;
  winRate: number;
  profitFactor: number;
  tradeCount: number;
  trades: Trade[];
  equityCurve: EquityPoint[];
}

export interface Trade {
  id: string;
  timestamp: string;
  type: 'buy' | 'sell';
  price: number;
  quantity: number;
  amount: number;
  balance: number;
  reason: string;
}

export interface EquityPoint {
  timestamp: string;
  equity: number;
  benchmark: number;
}

export interface StrategyComparison {
  strategies: Strategy[];
  metrics: ComparisonMetric[];
}

export interface ComparisonMetric {
  name: string;
  value: number;
  unit: string;
  isHigherBetter: boolean;
}

export interface StrategyScore {
  strategyId: string;
  totalScore: number;
  metricScores: {
    [key: string]: number;
  };
  rank: number;
}