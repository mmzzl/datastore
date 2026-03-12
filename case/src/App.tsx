import { useState } from 'react'
import './App.css'
import { Strategy } from './types/strategy'
import { allStrategies, defaultStrategies } from './data/mockData'
import StrategyListPage from './pages/StrategyListPage'
import StrategyDetailPage from './pages/StrategyDetailPage'
import StrategyCreatePage from './pages/StrategyCreatePage'
import StrategyComparePage from './pages/StrategyComparePage'
import StockListPage from './pages/StockListPage'
import StockDetailPage from './pages/StockDetailPage'

// 定义路由类型
type Route = 'list' | 'detail' | 'create' | 'compare' | 'stock-list' | 'stock-detail'

function App() {
  const [route, setRoute] = useState<Route>('list')
  const [selectedStrategyId, setSelectedStrategyId] = useState<string>('')
  const [strategies, setStrategies] = useState<Strategy[]>(allStrategies)
  const [compareStrategies, setCompareStrategies] = useState<Strategy[]>(defaultStrategies.slice(0, 3))

  // 切换路由
  const navigate = (newRoute: Route, strategyId?: string) => {
    setRoute(newRoute)
    if (strategyId) {
      setSelectedStrategyId(strategyId)
    }
  }

  // 添加新策略
  const addStrategy = (newStrategy: Strategy) => {
    setStrategies([...strategies, newStrategy])
    navigate('list')
  }

  return (
    <div className="app">
      <header className="header">
        <h1>交易策略平台</h1>
      </header>
      <main className="main">
        <aside className="sidebar">
          <nav>
            <ul className="sidebar-nav">
              <li>
                <a 
                  href="#" 
                  className={route === 'stock-list' ? 'active' : ''}
                  onClick={(e) => {
                    e.preventDefault()
                    navigate('stock-list')
                  }}
                >
                  行情中心
                </a>
              </li>
              <li>
                <a 
                  href="#" 
                  className={route === 'list' ? 'active' : ''}
                  onClick={(e) => {
                    e.preventDefault()
                    navigate('list')
                  }}
                >
                  策略列表
                </a>
              </li>
              <li>
                <a 
                  href="#" 
                  className={route === 'create' ? 'active' : ''}
                  onClick={(e) => {
                    e.preventDefault()
                    navigate('create')
                  }}
                >
                  新增策略
                </a>
              </li>
              <li>
                <a 
                  href="#" 
                  className={route === 'compare' ? 'active' : ''}
                  onClick={(e) => {
                    e.preventDefault()
                    navigate('compare')
                  }}
                >
                  策略比较
                </a>
              </li>
            </ul>
          </nav>
        </aside>
        <section className="content">
          {route === 'stock-list' && (
            <StockListPage 
              onSelectStock={(code) => navigate('stock-detail', code)} 
            />
          )}
          {route === 'stock-detail' && selectedStrategyId && (
            <StockDetailPage 
              stockCode={selectedStrategyId} 
              onBack={() => navigate('stock-list')} 
            />
          )}
          {route === 'list' && (
            <StrategyListPage 
              strategies={strategies} 
              onSelectStrategy={(id) => navigate('detail', id)} 
            />
          )}
          {route === 'detail' && selectedStrategyId && (
            <StrategyDetailPage 
              strategy={strategies.find(s => s.id === selectedStrategyId)!} 
              onBack={() => navigate('list')} 
            />
          )}
          {route === 'create' && (
            <StrategyCreatePage onAddStrategy={addStrategy} />
          )}
          {route === 'compare' && (
            <StrategyComparePage 
              strategies={compareStrategies} 
            />
          )}
        </section>
      </main>
    </div>
  )
}

export default App