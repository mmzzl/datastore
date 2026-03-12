import { useState } from 'react';
import { Stock } from '../types/stock';
import { stockList } from '../data/stockData';

interface StockListPageProps {
  onSelectStock: (code: string) => void;
}

const formatNumber = (num: number): string => {
  if (num >= 100000000) {
    return (num / 100000000).toFixed(2) + '亿';
  }
  if (num >= 10000) {
    return (num / 10000).toFixed(2) + '万';
  }
  return num.toString();
};

const formatPrice = (price: number): string => {
  return price.toFixed(2);
};

const StockListPage: React.FC<StockListPageProps> = ({ onSelectStock }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<'name' | 'changePercent' | 'volume'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  const filteredStocks = stockList
    .filter(stock => 
      stock.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      stock.code.includes(searchTerm)
    )
    .sort((a, b) => {
      let comparison = 0;
      switch (sortField) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'changePercent':
          comparison = a.changePercent - b.changePercent;
          break;
        case 'volume':
          comparison = a.volume - b.volume;
          break;
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });

  const handleSort = (field: 'name' | 'changePercent' | 'volume') => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  return (
    <div className="stock-list-page">
      <div className="stock-list-header">
        <h2>行情中心</h2>
        <div className="stock-search">
          <input
            type="text"
            placeholder="搜索股票代码/名称..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="stock-search-input"
          />
        </div>
      </div>

      <div className="stock-summary">
        <div className="summary-card">
          <span className="summary-label">上证指数</span>
          <span className="summary-value">3,456.78</span>
          <span className="summary-change positive">+12.34 +0.36%</span>
        </div>
        <div className="summary-card">
          <span className="summary-label">深证成指</span>
          <span className="summary-value">11,234.56</span>
          <span className="summary-change negative">-45.67 -0.41%</span>
        </div>
        <div className="summary-card">
          <span className="summary-label">创业板指</span>
          <span className="summary-value">2,345.89</span>
          <span className="summary-change positive">+23.45 +1.01%</span>
        </div>
      </div>

      <div className="stock-table-container">
        <table className="stock-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('name')} className="sortable">
                股票名称 {sortField === 'name' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th>代码</th>
              <th className="text-right">现价</th>
              <th onClick={() => handleSort('changePercent')} className="sortable text-right">
               涨跌幅 {sortField === 'changePercent' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th className="text-right">涨跌</th>
              <th onClick={() => handleSort('volume')} className="sortable text-right">
               成交量 {sortField === 'volume' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th className="text-right">成交额</th>
              <th className="text-right">振幅</th>
              <th className="text-right">换手率</th>
            </tr>
          </thead>
          <tbody>
            {filteredStocks.map(stock => (
              <tr 
                key={stock.code} 
                onClick={() => onSelectStock(stock.code)}
                className="stock-row"
              >
                <td className="stock-name">
                  <span className="name">{stock.name}</span>
                  <span className="industry">{stock.industry}</span>
                </td>
                <td className="stock-code">{stock.code}</td>
                <td className="text-right price">{formatPrice(stock.price)}</td>
                <td className={`text-right change ${stock.changePercent >= 0 ? 'positive' : 'negative'}`}>
                  <span className="change-tag">{stock.changePercent >= 0 ? '涨' : '跌'}</span>
                  {stock.changePercent >= 0 ? '+' : ''}{stock.changePercent.toFixed(2)}%
                </td>
                <td className={`text-right ${stock.change >= 0 ? 'positive' : 'negative'}`}>
                  {stock.change >= 0 ? '+' : ''}{stock.change.toFixed(2)}
                </td>
                <td className="text-right">{formatNumber(stock.volume)}</td>
                <td className="text-right">{formatNumber(stock.amount)}</td>
                <td className="text-right">{((stock.high - stock.low) / stock.low * 100).toFixed(2)}%</td>
                <td className="text-right">{stock.turnover.toFixed(2)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default StockListPage;
