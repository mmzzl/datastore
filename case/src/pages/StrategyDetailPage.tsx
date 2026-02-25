import { Strategy } from '../types/strategy'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface StrategyDetailPageProps {
  strategy: Strategy
  onBack: () => void
}

const StrategyDetailPage = ({ strategy, onBack }: StrategyDetailPageProps) => {
  // 格式化日期
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString()
  }

  // 格式化数字
  const formatNumber = (num: number, decimals: number = 2) => {
    return num.toFixed(decimals)
  }

  return (
    <div>
      <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <button className="btn btn-secondary" onClick={onBack}>
          返回列表
        </button>
        <h2 className="page-title">{strategy.name}</h2>
        <div className="strategy-score">{strategy.score.toFixed(1)}</div>
      </div>

      {/* 策略基本信息 */}
      <div className="detail-section">
        <h2>基本信息</h2>
        <div className="detail-grid">
          <div>
            <div className="detail-item">
              <div className="detail-label">策略描述</div>
              <div className="detail-value">{strategy.description}</div>
            </div>
            <div className="detail-item">
              <div className="detail-label">策略类型</div>
              <div className="detail-value">{strategy.type === 'default' ? '默认策略' : '自定义策略'}</div>
            </div>
            <div className="detail-item">
              <div className="detail-label">创建时间</div>
              <div className="detail-value">{formatDate(strategy.createdAt)}</div>
            </div>
            <div className="detail-item">
              <div className="detail-label">创建者</div>
              <div className="detail-value">{strategy.createdBy}</div>
            </div>
          </div>
          <div>
            <div className="detail-item">
              <div className="detail-label">仓位比例</div>
              <div className="detail-value">{strategy.positionSize}%</div>
            </div>
            <div className="detail-item">
              <div className="detail-label">止损比例</div>
              <div className="detail-value">{strategy.stopLoss}%</div>
            </div>
            <div className="detail-item">
              <div className="detail-label">止盈比例</div>
              <div className="detail-value">{strategy.takeProfit}%</div>
            </div>
            <div className="detail-item">
              <div className="detail-label">最近更新</div>
              <div className="detail-value">{formatDate(strategy.updatedAt)}</div>
            </div>
          </div>
        </div>
      </div>

      {/* 交易规则 */}
      <div className="detail-section">
        <h2>交易规则</h2>
        
        <div className="rule-section">
          <h3>买入规则</h3>
          {strategy.buyRules.map((rule) => (
            <div key={rule.id} className="rule-item">
              <div className="rule-text">
                {rule.indicator} {rule.operator} {rule.value}{rule.timeframe ? ` (${rule.timeframe}周期)` : ''}
              </div>
            </div>
          ))}
        </div>
        
        <div className="rule-section">
          <h3>卖出规则</h3>
          {strategy.sellRules.map((rule) => (
            <div key={rule.id} className="rule-item">
              <div className="rule-text">
                {rule.indicator} {rule.operator} {rule.value}{rule.timeframe ? ` (${rule.timeframe}周期)` : ''}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 回测结果 */}
      {strategy.backtestResults && (
        <>
          <div className="detail-section">
            <h2>回测结果概览</h2>
            <div className="backtest-results">
              <div className="backtest-metric">
                <div className="backtest-metric-label">总收益率</div>
                <div className="backtest-metric-value positive">{formatNumber(strategy.backtestResults.totalReturn)}%</div>
              </div>
              <div className="backtest-metric">
                <div className="backtest-metric-label">年化收益率</div>
                <div className="backtest-metric-value positive">{formatNumber(strategy.backtestResults.annualReturn)}%</div>
              </div>
              <div className="backtest-metric">
                <div className="backtest-metric-label">最大回撤</div>
                <div className="backtest-metric-value negative">{formatNumber(strategy.backtestResults.maxDrawdown)}%</div>
              </div>
              <div className="backtest-metric">
                <div className="backtest-metric-label">夏普比率</div>
                <div className="backtest-metric-value">{formatNumber(strategy.backtestResults.sharpeRatio)}</div>
              </div>
              <div className="backtest-metric">
                <div className="backtest-metric-label">胜率</div>
                <div className="backtest-metric-value">{formatNumber(strategy.backtestResults.winRate)}%</div>
              </div>
              <div className="backtest-metric">
                <div className="backtest-metric-label">交易次数</div>
                <div className="backtest-metric-value">{strategy.backtestResults.tradeCount}</div>
              </div>
            </div>
          </div>

          {/* 净值曲线 */}
          <div className="detail-section">
            <h2>净值曲线</h2>
            <div className="chart-container" style={{ height: '400px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={strategy.backtestResults.equityCurve}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" tickFormatter={formatDate} />
                  <YAxis />
                  <Tooltip formatter={(value) => [`${formatNumber(Number(value))}`, '净值']} />
                  <Legend />
                  <Line type="monotone" dataKey="equity" stroke="#3498db" name="策略净值" strokeWidth={2} />
                  <Line type="monotone" dataKey="benchmark" stroke="#e74c3c" name="基准净值" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 交易记录 */}
          <div className="detail-section">
            <h2>交易记录</h2>
            <div className="table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>时间</th>
                    <th>类型</th>
                    <th>价格</th>
                    <th>数量</th>
                    <th>金额</th>
                    <th>余额</th>
                    <th>原因</th>
                  </tr>
                </thead>
                <tbody>
                  {strategy.backtestResults.trades.slice(0, 10).map((trade) => (
                    <tr key={trade.id}>
                      <td>{formatDate(trade.timestamp)}</td>
                      <td>{trade.type === 'buy' ? '买入' : '卖出'}</td>
                      <td>{formatNumber(trade.price)}</td>
                      <td>{trade.quantity}</td>
                      <td>{formatNumber(trade.amount)}</td>
                      <td>{formatNumber(trade.balance)}</td>
                      <td>{trade.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default StrategyDetailPage