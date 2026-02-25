import { Strategy } from '../types/strategy'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface StrategyComparePageProps {
  strategies: Strategy[]
}

const StrategyComparePage = ({ strategies }: StrategyComparePageProps) => {
  // 格式化日期
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString()
  }

  // 格式化数字
  const formatNumber = (num: number, decimals: number = 2) => {
    return num.toFixed(decimals)
  }

  // 计算策略综合评分
  const calculateScore = (strategy: Strategy) => {
    if (!strategy.backtestResults) return 0
    
    const { totalReturn, annualReturn, maxDrawdown, sharpeRatio, winRate } = strategy.backtestResults
    
    // 评分算法：综合考虑收益率、风险和稳定性
    // 权重分配：总收益率(25%)、年化收益率(25%)、最大回撤(20%)、夏普比率(20%)、胜率(10%)
    const score = 
      (totalReturn / 50 * 25) + // 假设50%为满分
      (annualReturn / 50 * 25) +
      ((Math.abs(maxDrawdown) / 30) * 20) + // 假设最大回撤-30%为满分
      (sharpeRatio / 3 * 20) + // 假设夏普比率3为满分
      (winRate / 100 * 10)
    
    return Math.min(10, Math.max(0, score))
  }

  // 生成对比数据
  const generateComparisonData = () => {
    return strategies.map(strategy => {
      const score = calculateScore(strategy)
      const results = strategy.backtestResults
      
      return {
        name: strategy.name,
        score: score.toFixed(1),
        totalReturn: results ? `${formatNumber(results.totalReturn)}%` : '-',
        annualReturn: results ? `${formatNumber(results.annualReturn)}%` : '-',
        maxDrawdown: results ? `${formatNumber(results.maxDrawdown)}%` : '-',
        sharpeRatio: results ? formatNumber(results.sharpeRatio) : '-',
        winRate: results ? `${formatNumber(results.winRate)}%` : '-',
        tradeCount: results ? results.tradeCount : '-',
        equityCurve: results ? results.equityCurve : []
      }
    })
  }

  // 合并所有策略的净值曲线数据
  const generateCombinedEquityData = () => {
    // 获取所有策略的净值曲线
    const equityCurves = strategies.map(s => s.backtestResults?.equityCurve || [])
    
    // 如果没有回测数据，返回空数组
    if (equityCurves.length === 0 || equityCurves[0].length === 0) {
      return []
    }
    
    // 使用第一个策略的时间点作为基准
    const baseCurve = equityCurves[0]
    
    // 合并数据
    return baseCurve.map((point, index) => {
      const combinedPoint: any = { timestamp: point.timestamp }
      
      // 为每个策略添加净值数据
      strategies.forEach((strategy, strategyIndex) => {
        const curve = equityCurves[strategyIndex]
        if (curve && curve[index]) {
          combinedPoint[strategy.name] = curve[index].equity
        }
      })
      
      return combinedPoint
    })
  }

  const comparisonData = generateComparisonData()
  const combinedEquityData = generateCombinedEquityData()

  return (
    <div>
      <h2 className="page-title">策略比较与评分</h2>
      
      {/* 评分排名 */}
      <div className="detail-section">
        <h2>策略评分排名</h2>
        
        <div className="strategy-grid">
          {comparisonData
            .sort((a, b) => parseFloat(b.score) - parseFloat(a.score))
            .map((data, index) => (
              <div key={data.name} className="strategy-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <h3 style={{ fontSize: '1.1rem' }}>{index + 1}. {data.name}</h3>
                  <div className="strategy-score" style={{ fontSize: '1.25rem', padding: '0.5rem 1rem' }}>
                    {data.score}
                  </div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.9rem', marginTop: '1rem' }}>
                  <div>
                    <span style={{ color: '#7f8c8d' }}>总收益率:</span> {data.totalReturn}
                  </div>
                  <div>
                    <span style={{ color: '#7f8c8d' }}>年化收益率:</span> {data.annualReturn}
                  </div>
                  <div>
                    <span style={{ color: '#7f8c8d' }}>最大回撤:</span> {data.maxDrawdown}
                  </div>
                  <div>
                    <span style={{ color: '#7f8c8d' }}>夏普比率:</span> {data.sharpeRatio}
                  </div>
                </div>
              </div>
            ))
          }
        </div>
      </div>

      {/* 指标对比表格 */}
      <div className="detail-section">
        <h2>指标对比详情</h2>
        
        <div className="table-container">
          <table className="compare-table">
            <thead>
              <tr>
                <th>策略名称</th>
                <th>综合评分</th>
                <th>总收益率</th>
                <th>年化收益率</th>
                <th>最大回撤</th>
                <th>夏普比率</th>
                <th>胜率</th>
                <th>交易次数</th>
              </tr>
            </thead>
            <tbody>
              {comparisonData.map((data) => (
                <tr key={data.name}>
                  <td>{data.name}</td>
                  <td>{data.score}</td>
                  <td>{data.totalReturn}</td>
                  <td>{data.annualReturn}</td>
                  <td>{data.maxDrawdown}</td>
                  <td>{data.sharpeRatio}</td>
                  <td>{data.winRate}</td>
                  <td>{data.tradeCount}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 净值曲线对比 */}
      {combinedEquityData.length > 0 && (
        <div className="detail-section">
          <h2>净值曲线对比</h2>
          
          <div className="chart-container" style={{ height: '500px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={combinedEquityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" tickFormatter={formatDate} />
                <YAxis />
                <Tooltip formatter={(value) => [`${formatNumber(Number(value))}`, '净值']} />
                <Legend />
                
                {/* 为每个策略添加一条线 */}
                {strategies.map((strategy, index) => (
                  <Line 
                    key={strategy.id}
                    type="monotone" 
                    dataKey={strategy.name} 
                    stroke={['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6'][index % 5]} 
                    strokeWidth={2} 
                    dot={false}
                    activeDot={{ r: 6 }}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* 策略详情概览 */}
      <div className="detail-section">
        <h2>策略详情概览</h2>
        
        {strategies.map((strategy) => (
          <div key={strategy.id} style={{ marginBottom: '2rem', padding: '1.5rem', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3>{strategy.name}</h3>
              <div className="strategy-score">{calculateScore(strategy).toFixed(1)}</div>
            </div>
            
            <p style={{ marginBottom: '1rem', color: '#666', fontSize: '0.95rem' }}>{strategy.description}</p>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
              <div>
                <h4 style={{ marginBottom: '0.75rem', fontSize: '1rem', color: '#2c3e50' }}>买入规则</h4>
                {strategy.buyRules.map((rule) => (
                  <div key={rule.id} style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: '#2c3e50' }}>
                    {rule.indicator} {rule.operator} {rule.value}{rule.timeframe ? ` (${rule.timeframe}周期)` : ''}
                  </div>
                ))}
              </div>
              
              <div>
                <h4 style={{ marginBottom: '0.75rem', fontSize: '1rem', color: '#2c3e50' }}>卖出规则</h4>
                {strategy.sellRules.map((rule) => (
                  <div key={rule.id} style={{ marginBottom: '0.5rem', fontSize: '0.9rem', color: '#2c3e50' }}>
                    {rule.indicator} {rule.operator} {rule.value}{rule.timeframe ? ` (${rule.timeframe}周期)` : ''}
                  </div>
                ))}
              </div>
            </div>
            
            <div style={{ display: 'flex', gap: '2rem', fontSize: '0.9rem', color: '#7f8c8d' }}>
              <div>仓位比例: {strategy.positionSize}%</div>
              <div>止损: {strategy.stopLoss}%</div>
              <div>止盈: {strategy.takeProfit}%</div>
              <div>类型: {strategy.type === 'default' ? '默认策略' : '自定义策略'}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default StrategyComparePage