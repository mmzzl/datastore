import { Strategy } from '../types/strategy'

interface StrategyListPageProps {
  strategies: Strategy[]
  onSelectStrategy: (id: string) => void
}

const StrategyListPage = ({ strategies, onSelectStrategy }: StrategyListPageProps) => {
  return (
    <div>
      <h2 className="page-title">交易策略列表</h2>
      
      <div className="strategy-grid">
        {strategies.map((strategy) => (
          <div key={strategy.id} className="strategy-card">
            <h3>{strategy.name}</h3>
            <p>{strategy.description}</p>
            <div className="strategy-meta">
              <span>类型: {strategy.type === 'default' ? '默认策略' : '自定义策略'}</span>
              <div className="strategy-score">{strategy.score.toFixed(1)}</div>
            </div>
            <div className="strategy-actions">
              <button 
                className="btn btn-primary btn-small"
                onClick={() => onSelectStrategy(strategy.id)}
              >
                详情
              </button>
              <button className="btn btn-secondary btn-small">
                回测
              </button>
              <button className="btn btn-success btn-small">
                比较
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default StrategyListPage