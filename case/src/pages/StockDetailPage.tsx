import { useState, useMemo } from 'react';
import { ComposedChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { Stock, StockKLine } from '../types/stock';
import { getStockByCode, getStockKLine } from '../data/stockData';

interface StockDetailPageProps {
  stockCode: string;
  onBack: () => void;
}

type TimeRange = '1M' | '3M' | '6M' | '1Y';

const CustomCandlestick: React.FC<any> = (props: any) => {
  const { x, y, width, height, payload } = props;
  if (!payload) return null;

  const isUp = payload.close >= payload.open;
  const fill = isUp ? '#22C55E' : '#EF4444';
  const stroke = fill;

  const priceScale = props.priceScale;
  const candleWidth = width * 0.6;

  const yHigh = priceScale(payload.high);
  const yLow = priceScale(payload.low);
  const yOpen = priceScale(payload.open);
  const yClose = priceScale(payload.close);

  return (
    <g>
      <line
        x1={x + width / 2}
        y1={yHigh}
        x2={x + width / 2}
        y2={yLow}
        stroke={stroke}
        strokeWidth={1}
      />
      <rect
        x={x + (width - candleWidth) / 2}
        y={y + Math.min(yOpen, yClose) - y}
        width={candleWidth}
        height={Math.max(Math.abs(yOpen - yClose), 1)}
        fill={isUp ? 'transparent' : fill}
        stroke={stroke}
        strokeWidth={1}
      />
    </g>
  );
};

const StockDetailPage: React.FC<StockDetailPageProps> = ({ stockCode, onBack }) => {
  const [timeRange, setTimeRange] = useState<TimeRange>('3M');
  
  const stock = getStockByCode(stockCode);
  const kLineData = getStockKLine(stockCode);

  const filteredData = useMemo(() => {
    const now = new Date();
    let daysBack = 90;
    switch (timeRange) {
      case '1M': daysBack = 30; break;
      case '3M': daysBack = 90; break;
      case '6M': daysBack = 180; break;
      case '1Y': daysBack = 365; break;
    }
    const cutoff = new Date(now.getTime() - daysBack * 24 * 60 * 60 * 1000);
    return kLineData.filter(d => new Date(d.date) >= cutoff);
  }, [kLineData, timeRange]);

  const { minPrice, maxPrice, chartData } = useMemo(() => {
    const prices = filteredData.flatMap(d => [d.high, d.low]);
    const min = Math.min(...prices) * 0.98;
    const max = Math.max(...prices) * 1.02;
    return {
      minPrice: min,
      maxPrice: max,
      chartData: filteredData.map(d => ({
        ...d,
        volumeHeight: (d.volume / 1000000) * 20
      }))
    };
  }, [filteredData]);

  const priceRange = maxPrice - minPrice;

  if (!stock) {
    return (
      <div className="stock-detail-page">
        <div className="error-message">股票不存在</div>
        <button onClick={onBack} className="back-button">返回</button>
      </div>
    );
  }

  return (
    <div className="stock-detail-page">
      <div className="stock-detail-header">
        <button onClick={onBack} className="back-button">
          ← 返回
        </button>
      </div>

      <div className="stock-info-card">
        <div className="stock-title">
          <h1>{stock.name}</h1>
          <span className="stock-code">{stock.code}</span>
        </div>
        <div className="stock-price">
          <span className="price">{stock.price.toFixed(2)}</span>
          <span className={`change ${stock.change >= 0 ? 'positive' : 'negative'}`}>
            {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)} 
            ({stock.changePercent >= 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%)
          </span>
        </div>
        <div className="stock-tags">
          <span className="tag sector">{stock.sector}</span>
          <span className="tag industry">{stock.industry}</span>
        </div>
      </div>

      <div className="stock-ohlc">
        <div className="ohlc-item">
          <span className="label">开盘</span>
          <span className="value">{stock.open.toFixed(2)}</span>
        </div>
        <div className="ohlc-item">
          <span className="label">最高</span>
          <span className="value high">{stock.high.toFixed(2)}</span>
        </div>
        <div className="ohlc-item">
          <span className="label">最低</span>
          <span className="value low">{stock.low.toFixed(2)}</span>
        </div>
        <div className="ohlc-item">
          <span className="label">昨收</span>
          <span className="value">{stock.prevClose.toFixed(2)}</span>
        </div>
        <div className="ohlc-item">
          <span className="label">成交量</span>
          <span className="value">{(stock.volume / 1000000).toFixed(2)}万</span>
        </div>
        <div className="ohlc-item">
          <span className="label">成交额</span>
          <span className="value">{(stock.amount / 100000000).toFixed(2)}亿</span>
        </div>
      </div>

      <div className="kline-section">
        <div className="kline-header">
          <h3>行情走势</h3>
          <div className="time-range-selector">
            {(['1M', '3M', '6M', '1Y'] as TimeRange[]).map(range => (
              <button
                key={range}
                className={timeRange === range ? 'active' : ''}
                onClick={() => setTimeRange(range)}
              >
                {range}
              </button>
            ))}
          </div>
        </div>
        <div className="kline-chart">
          <ResponsiveContainer width="100%" height={350}>
            <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis 
                dataKey="date" 
                stroke="#94A3B8" 
                tick={{ fill: '#94A3B8', fontSize: 10 }}
                tickFormatter={(value) => value.slice(5)}
                interval="preserveStartEnd"
              />
              <YAxis 
                domain={[minPrice, maxPrice]}
                stroke="#94A3B8"
                tick={{ fill: '#94A3B8', fontSize: 10 }}
                tickFormatter={(value) => value.toFixed(2)}
                orientation="right"
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#0E1223', 
                  border: '1px solid #334155',
                  borderRadius: '8px'
                }}
                labelStyle={{ color: '#F8FAFC' }}
                formatter={(value: number, name: string) => {
                  if (name === 'volume') return [(value / 10000).toFixed(2) + '万', '成交量'];
                  return [value.toFixed(2), name];
                }}
              />
              <Bar 
                dataKey="volumeHeight" 
                fill="#334155" 
                opacity={0.4}
                yAxisId="volume"
              />
              <YAxis 
                yAxisId="volume" 
                domain={[0, (dataMax: number) => dataMax * 5]} 
                hide 
              />
              {filteredData.map((entry, index) => (
                <ReferenceLine 
                  key={index}
                  segment={[
                    { x: entry.date, y: entry.open },
                    { x: entry.date, y: entry.close }
                  ]}
                  stroke={entry.close >= entry.open ? '#22C55E' : '#EF4444'}
                  strokeWidth={Math.max((chartData[0]?.volumeHeight || 10) / 20, 2)}
                />
              ))}
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="stock-metrics">
        <h3>财务指标</h3>
        <div className="metrics-grid">
          <div className="metric-item">
            <span className="label">市盈率(PE)</span>
            <span className="value">{stock.pe.toFixed(2)}</span>
          </div>
          <div className="metric-item">
            <span className="label">市净率(PB)</span>
            <span className="value">{stock.pb.toFixed(2)}</span>
          </div>
          <div className="metric-item">
            <span className="label">换手率</span>
            <span className="value">{stock.turnover.toFixed(2)}%</span>
          </div>
          <div className="metric-item">
            <span className="label">总市值</span>
            <span className="value">{(stock.marketCap / 100000000).toFixed(2)}亿</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StockDetailPage;
