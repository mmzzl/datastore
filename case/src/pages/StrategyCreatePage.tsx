import { useState } from 'react'
import { Strategy, Rule, Indicator, Operator } from '../types/strategy'

interface StrategyCreatePageProps {
  onAddStrategy: (strategy: Strategy) => void
}

const StrategyCreatePage = ({ onAddStrategy }: StrategyCreatePageProps) => {
  // 生成随机ID
  const generateId = (): string => {
    return Math.random().toString(36).substr(2, 9)
  }

  // 策略基本信息
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [positionSize, setPositionSize] = useState(50)
  const [stopLoss, setStopLoss] = useState(-5)
  const [takeProfit, setTakeProfit] = useState(10)

  // 买入规则
  const [buyRules, setBuyRules] = useState<Rule[]>([
    {
      id: generateId(),
      indicator: 'MA',
      operator: '>',
      value: 20,
      timeframe: 5
    }
  ])

  // 卖出规则
  const [sellRules, setSellRules] = useState<Rule[]>([
    {
      id: generateId(),
      indicator: 'MA',
      operator: '<',
      value: 20,
      timeframe: 5
    }
  ])

  // 指标选项
  const indicators: { value: Indicator; label: string }[] = [
    { value: 'MA', label: '移动平均线(MA)' },
    { value: 'RSI', label: '相对强弱指标(RSI)' },
    { value: 'MACD', label: '平滑异同移动平均线(MACD)' },
    { value: 'BB', label: '布林带(BB)' },
    { value: 'VOL', label: '成交量(VOL)' },
    { value: 'PRICE', label: '价格(PRICE)' },
    { value: 'KDJ', label: '随机指标(KDJ)' },
    { value: 'ADX', label: '平均趋向指数(ADX)' },
    { value: 'CCI', label: '顺势指标(CCI)' }
  ]

  // 运算符选项
  const operators: Operator[] = ['>', '<', '>=', '<=', '=']

  // 添加买入规则
  const addBuyRule = () => {
    setBuyRules([
      ...buyRules,
      {
        id: generateId(),
        indicator: 'MA',
        operator: '>',
        value: 0,
        timeframe: 5
      }
    ])
  }

  // 删除买入规则
  const removeBuyRule = (ruleId: string) => {
    if (buyRules.length > 1) {
      setBuyRules(buyRules.filter(rule => rule.id !== ruleId))
    }
  }

  // 更新买入规则
  const updateBuyRule = (ruleId: string, field: keyof Rule, value: any) => {
    setBuyRules(buyRules.map(rule => 
      rule.id === ruleId ? { ...rule, [field]: value } : rule
    ))
  }

  // 添加卖出规则
  const addSellRule = () => {
    setSellRules([
      ...sellRules,
      {
        id: generateId(),
        indicator: 'MA',
        operator: '<',
        value: 0,
        timeframe: 5
      }
    ])
  }

  // 删除卖出规则
  const removeSellRule = (ruleId: string) => {
    if (sellRules.length > 1) {
      setSellRules(sellRules.filter(rule => rule.id !== ruleId))
    }
  }

  // 更新卖出规则
  const updateSellRule = (ruleId: string, field: keyof Rule, value: any) => {
    setSellRules(sellRules.map(rule => 
      rule.id === ruleId ? { ...rule, [field]: value } : rule
    ))
  }

  // 提交表单
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    // 创建新策略
    const newStrategy: Strategy = {
      id: generateId(),
      name,
      description,
      type: 'custom',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      createdBy: 'user',
      score: 0, // 初始评分
      buyRules,
      sellRules,
      positionSize,
      stopLoss,
      takeProfit
    }

    onAddStrategy(newStrategy)
  }

  return (
    <div>
      <h2 className="page-title">创建交易策略</h2>
      
      <form onSubmit={handleSubmit} className="detail-section">
        {/* 基本信息 */}
        <div className="form-group">
          <label htmlFor="name">策略名称</label>
          <input
            type="text"
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="description">策略描述</label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
            rows={4}
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label htmlFor="positionSize">仓位比例 (%)</label>
            <input
              type="number"
              id="positionSize"
              min="1"
              max="100"
              value={positionSize}
              onChange={(e) => setPositionSize(Number(e.target.value))}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="stopLoss">止损比例 (%)</label>
            <input
              type="number"
              id="stopLoss"
              min="-100"
              max="0"
              step="0.5"
              value={stopLoss}
              onChange={(e) => setStopLoss(Number(e.target.value))}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="takeProfit">止盈比例 (%)</label>
            <input
              type="number"
              id="takeProfit"
              min="0"
              max="100"
              step="0.5"
              value={takeProfit}
              onChange={(e) => setTakeProfit(Number(e.target.value))}
              required
            />
          </div>
        </div>

        <hr style={{ margin: '2rem 0', borderColor: '#e0e0e0' }} />

        {/* 买入规则 */}
        <h3 style={{ marginBottom: '1.5rem', color: '#2c3e50' }}>买入规则</h3>
        {buyRules.map((rule, index) => (
          <div key={rule.id} style={{ marginBottom: '1.5rem', padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
              <div style={{ width: '200px' }}>
                <label>指标</label>
                <select
                  value={rule.indicator}
                  onChange={(e) => updateBuyRule(rule.id, 'indicator', e.target.value as Indicator)}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
                >
                  {indicators.map(ind => (
                    <option key={ind.value} value={ind.value}>{ind.label}</option>
                  ))}
                </select>
              </div>

              <div style={{ width: '100px' }}>
                <label>运算符</label>
                <select
                  value={rule.operator}
                  onChange={(e) => updateBuyRule(rule.id, 'operator', e.target.value as Operator)}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
                >
                  {operators.map(op => (
                    <option key={op} value={op}>{op}</option>
                  ))}
                </select>
              </div>

              <div style={{ width: '120px' }}>
                <label>数值</label>
                <input
                  type="number"
                  value={rule.value}
                  onChange={(e) => updateBuyRule(rule.id, 'value', Number(e.target.value))}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
                  step="any"
                  required
                />
              </div>

              {(rule.indicator === 'MA' || rule.indicator === 'BB') && (
                <div style={{ width: '120px' }}>
                  <label>时间周期</label>
                  <input
                    type="number"
                    value={rule.timeframe || 5}
                    onChange={(e) => updateBuyRule(rule.id, 'timeframe', Number(e.target.value))}
                    style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
                    min="1"
                    required
                  />
                </div>
              )}

              <div style={{ display: 'flex', alignItems: 'flex-end', paddingBottom: '0.5rem' }}>
                <button
                  type="button"
                  className="btn btn-danger btn-small"
                  onClick={() => removeBuyRule(rule.id)}
                  disabled={buyRules.length <= 1}
                >
                  删除
                </button>
              </div>
            </div>
          </div>
        ))}

        <button
          type="button"
          className="btn btn-secondary"
          onClick={addBuyRule}
          style={{ marginBottom: '2rem' }}
        >
          添加买入规则
        </button>

        <hr style={{ margin: '2rem 0', borderColor: '#e0e0e0' }} />

        {/* 卖出规则 */}
        <h3 style={{ marginBottom: '1.5rem', color: '#2c3e50' }}>卖出规则</h3>
        {sellRules.map((rule, index) => (
          <div key={rule.id} style={{ marginBottom: '1.5rem', padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
              <div style={{ width: '200px' }}>
                <label>指标</label>
                <select
                  value={rule.indicator}
                  onChange={(e) => updateSellRule(rule.id, 'indicator', e.target.value as Indicator)}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
                >
                  {indicators.map(ind => (
                    <option key={ind.value} value={ind.value}>{ind.label}</option>
                  ))}
                </select>
              </div>

              <div style={{ width: '100px' }}>
                <label>运算符</label>
                <select
                  value={rule.operator}
                  onChange={(e) => updateSellRule(rule.id, 'operator', e.target.value as Operator)}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
                >
                  {operators.map(op => (
                    <option key={op} value={op}>{op}</option>
                  ))}
                </select>
              </div>

              <div style={{ width: '120px' }}>
                <label>数值</label>
                <input
                  type="number"
                  value={rule.value}
                  onChange={(e) => updateSellRule(rule.id, 'value', Number(e.target.value))}
                  style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
                  step="any"
                  required
                />
              </div>

              {(rule.indicator === 'MA' || rule.indicator === 'BB') && (
                <div style={{ width: '120px' }}>
                  <label>时间周期</label>
                  <input
                    type="number"
                    value={rule.timeframe || 5}
                    onChange={(e) => updateSellRule(rule.id, 'timeframe', Number(e.target.value))}
                    style={{ width: '100%', padding: '0.5rem', marginTop: '0.25rem' }}
                    min="1"
                    required
                  />
                </div>
              )}

              <div style={{ display: 'flex', alignItems: 'flex-end', paddingBottom: '0.5rem' }}>
                <button
                  type="button"
                  className="btn btn-danger btn-small"
                  onClick={() => removeSellRule(rule.id)}
                  disabled={sellRules.length <= 1}
                >
                  删除
                </button>
              </div>
            </div>
          </div>
        ))}

        <button
          type="button"
          className="btn btn-secondary"
          onClick={addSellRule}
          style={{ marginBottom: '2rem' }}
        >
          添加卖出规则
        </button>

        {/* 提交按钮 */}
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', marginTop: '2rem' }}>
          <button type="button" className="btn btn-secondary">
            重置
          </button>
          <button type="submit" className="btn btn-primary">
            创建策略
          </button>
        </div>
      </form>
    </div>
  )
}

export default StrategyCreatePage