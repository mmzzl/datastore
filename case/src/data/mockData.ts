import { Strategy, BacktestResult, Trade, EquityPoint } from '../types/strategy';

// 生成随机ID的辅助函数
const generateId = (): string => {
  return Math.random().toString(36).substr(2, 9);
};

// 默认交易策略
export const defaultStrategies: Strategy[] = [
  {
    id: '1',
    name: '移动平均线交叉策略',
    description: '短期均线上穿长期均线买入，短期均线下穿长期均线卖出',
    type: 'default',
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
    createdBy: 'system',
    score: 8.5,
    buyRules: [
      {
        id: '1-1',
        indicator: 'MA',
        operator: '>',
        value: 20,
        timeframe: 5
      }
    ],
    sellRules: [
      {
        id: '1-2',
        indicator: 'MA',
        operator: '<',
        value: 20,
        timeframe: 5
      }
    ],
    positionSize: 50,
    stopLoss: -5,
    takeProfit: 10,
    backtestResults: {
      id: 'bt-1',
      strategyId: '1',
      startTime: '2023-01-01T00:00:00Z',
      endTime: '2023-12-31T00:00:00Z',
      initialCapital: 100000,
      finalCapital: 125000,
      totalReturn: 25,
      annualReturn: 25,
      maxDrawdown: -12,
      sharpeRatio: 1.8,
      sortinoRatio: 2.2,
      winRate: 65,
      profitFactor: 1.8,
      tradeCount: 48,
      trades: [
        {
          id: 'trade-1',
          timestamp: '2023-01-15T00:00:00Z',
          type: 'buy',
          price: 100,
          quantity: 500,
          amount: 50000,
          balance: 50000,
          reason: 'MA5 > MA20'
        },
        {
          id: 'trade-2',
          timestamp: '2023-02-20T00:00:00Z',
          type: 'sell',
          price: 112,
          quantity: 500,
          amount: 56000,
          balance: 106000,
          reason: 'MA5 < MA20'
        }
      ],
      equityCurve: [
        { timestamp: '2023-01-01T00:00:00Z', equity: 100000, benchmark: 100000 },
        { timestamp: '2023-06-30T00:00:00Z', equity: 115000, benchmark: 108000 },
        { timestamp: '2023-12-31T00:00:00Z', equity: 125000, benchmark: 112000 }
      ]
    }
  },
  {
    id: '2',
    name: 'RSI超买超卖策略',
    description: 'RSI>70卖出，RSI<30买入',
    type: 'default',
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
    createdBy: 'system',
    score: 7.8,
    buyRules: [
      {
        id: '2-1',
        indicator: 'RSI',
        operator: '<',
        value: 30
      }
    ],
    sellRules: [
      {
        id: '2-2',
        indicator: 'RSI',
        operator: '>',
        value: 70
      }
    ],
    positionSize: 40,
    stopLoss: -6,
    takeProfit: 12,
    backtestResults: {
      id: 'bt-2',
      strategyId: '2',
      startTime: '2023-01-01T00:00:00Z',
      endTime: '2023-12-31T00:00:00Z',
      initialCapital: 100000,
      finalCapital: 118000,
      totalReturn: 18,
      annualReturn: 18,
      maxDrawdown: -15,
      sharpeRatio: 1.5,
      sortinoRatio: 1.8,
      winRate: 60,
      profitFactor: 1.6,
      tradeCount: 62,
      trades: [
        {
          id: 'trade-3',
          timestamp: '2023-02-01T00:00:00Z',
          type: 'buy',
          price: 85,
          quantity: 470,
          amount: 40000,
          balance: 60000,
          reason: 'RSI < 30'
        },
        {
          id: 'trade-4',
          timestamp: '2023-03-15T00:00:00Z',
          type: 'sell',
          price: 95,
          quantity: 470,
          amount: 44650,
          balance: 104650,
          reason: 'RSI > 70'
        }
      ],
      equityCurve: [
        { timestamp: '2023-01-01T00:00:00Z', equity: 100000, benchmark: 100000 },
        { timestamp: '2023-06-30T00:00:00Z', equity: 110000, benchmark: 108000 },
        { timestamp: '2023-12-31T00:00:00Z', equity: 118000, benchmark: 112000 }
      ]
    }
  },
  {
    id: '3',
    name: 'MACD策略',
    description: 'MACD线与信号线金叉买入，死叉卖出',
    type: 'default',
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
    createdBy: 'system',
    score: 8.2,
    buyRules: [
      {
        id: '3-1',
        indicator: 'MACD',
        operator: '>',
        value: 0
      }
    ],
    sellRules: [
      {
        id: '3-2',
        indicator: 'MACD',
        operator: '<',
        value: 0
      }
    ],
    positionSize: 50,
    stopLoss: -5,
    takeProfit: 10,
    backtestResults: {
      id: 'bt-3',
      strategyId: '3',
      startTime: '2023-01-01T00:00:00Z',
      endTime: '2023-12-31T00:00:00Z',
      initialCapital: 100000,
      finalCapital: 122000,
      totalReturn: 22,
      annualReturn: 22,
      maxDrawdown: -10,
      sharpeRatio: 2.0,
      sortinoRatio: 2.4,
      winRate: 68,
      profitFactor: 1.9,
      tradeCount: 42,
      trades: [
        {
          id: 'trade-5',
          timestamp: '2023-01-20T00:00:00Z',
          type: 'buy',
          price: 110,
          quantity: 454,
          amount: 50000,
          balance: 50000,
          reason: 'MACD金叉'
        },
        {
          id: 'trade-6',
          timestamp: '2023-03-10T00:00:00Z',
          type: 'sell',
          price: 120,
          quantity: 454,
          amount: 54500,
          balance: 104500,
          reason: 'MACD死叉'
        }
      ],
      equityCurve: [
        { timestamp: '2023-01-01T00:00:00Z', equity: 100000, benchmark: 100000 },
        { timestamp: '2023-06-30T00:00:00Z', equity: 118000, benchmark: 108000 },
        { timestamp: '2023-12-31T00:00:00Z', equity: 122000, benchmark: 112000 }
      ]
    }
  },
  {
    id: '4',
    name: '布林带策略',
    description: '价格触及下轨买入，触及上轨卖出',
    type: 'default',
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
    createdBy: 'system',
    score: 7.5,
    buyRules: [
      {
        id: '4-1',
        indicator: 'BB',
        operator: '<',
        value: 0
      }
    ],
    sellRules: [
      {
        id: '4-2',
        indicator: 'BB',
        operator: '>',
        value: 100
      }
    ],
    positionSize: 45,
    stopLoss: -7,
    takeProfit: 15,
    backtestResults: {
      id: 'bt-4',
      strategyId: '4',
      startTime: '2023-01-01T00:00:00Z',
      endTime: '2023-12-31T00:00:00Z',
      initialCapital: 100000,
      finalCapital: 115000,
      totalReturn: 15,
      annualReturn: 15,
      maxDrawdown: -18,
      sharpeRatio: 1.3,
      sortinoRatio: 1.6,
      winRate: 58,
      profitFactor: 1.5,
      tradeCount: 55,
      trades: [
        {
          id: 'trade-7',
          timestamp: '2023-02-25T00:00:00Z',
          type: 'buy',
          price: 90,
          quantity: 500,
          amount: 45000,
          balance: 55000,
          reason: '价格触及布林带下轨'
        },
        {
          id: 'trade-8',
          timestamp: '2023-04-05T00:00:00Z',
          type: 'sell',
          price: 102,
          quantity: 500,
          amount: 51000,
          balance: 106000,
          reason: '价格触及布林带上轨'
        }
      ],
      equityCurve: [
        { timestamp: '2023-01-01T00:00:00Z', equity: 100000, benchmark: 100000 },
        { timestamp: '2023-06-30T00:00:00Z', equity: 108000, benchmark: 108000 },
        { timestamp: '2023-12-31T00:00:00Z', equity: 115000, benchmark: 112000 }
      ]
    }
  },
  {
    id: '5',
    name: '成交量突破策略',
    description: '成交量突破前N日均值+X%时买入',
    type: 'default',
    createdAt: '2024-01-01T00:00:00Z',
    updatedAt: '2024-01-01T00:00:00Z',
    createdBy: 'system',
    score: 8.0,
    buyRules: [
      {
        id: '5-1',
        indicator: 'VOL',
        operator: '>',
        value: 1000000
      }
    ],
    sellRules: [
      {
        id: '5-2',
        indicator: 'MA',
        operator: '<',
        value: 10,
        timeframe: 5
      }
    ],
    positionSize: 55,
    stopLoss: -4,
    takeProfit: 8,
    backtestResults: {
      id: 'bt-5',
      strategyId: '5',
      startTime: '2023-01-01T00:00:00Z',
      endTime: '2023-12-31T00:00:00Z',
      initialCapital: 100000,
      finalCapital: 120000,
      totalReturn: 20,
      annualReturn: 20,
      maxDrawdown: -13,
      sharpeRatio: 1.7,
      sortinoRatio: 2.0,
      winRate: 62,
      profitFactor: 1.7,
      tradeCount: 38,
      trades: [
        {
          id: 'trade-9',
          timestamp: '2023-03-01T00:00:00Z',
          type: 'buy',
          price: 120,
          quantity: 458,
          amount: 55000,
          balance: 45000,
          reason: '成交量突破100万'
        },
        {
          id: 'trade-10',
          timestamp: '2023-04-20T00:00:00Z',
          type: 'sell',
          price: 128,
          quantity: 458,
          amount: 58600,
          balance: 103600,
          reason: 'MA5 < MA10'
        }
      ],
      equityCurve: [
        { timestamp: '2023-01-01T00:00:00Z', equity: 100000, benchmark: 100000 },
        { timestamp: '2023-06-30T00:00:00Z', equity: 115000, benchmark: 108000 },
        { timestamp: '2023-12-31T00:00:00Z', equity: 120000, benchmark: 112000 }
      ]
    }
  }
];

// 自定义策略（初始为空）
export const customStrategies: Strategy[] = [];

// 所有策略
export const allStrategies: Strategy[] = [...defaultStrategies, ...customStrategies];