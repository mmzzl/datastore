import pytest
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

# 直接导入brain模块，避免导入pandas等依赖
sys.path.insert(0, os.path.join(project_root, "case", "apps", "api"))

from app.monitor.brain.models import BrainDecision, UnhookStrategy
from app.monitor.brain.analyzer import BrainAnalyzer
from app.monitor.brain.unhook import UnhookEngine
from app.monitor.brain.backtest import BacktestEngine

class TestBrainModels:
    """测试Brain模型"""
    
    def test_brain_decision_creation(self):
        """测试Brain决策模型创建"""
        decision = BrainDecision(
            code="sh.600000",
            action="buy",
            confidence=0.85,
            target_price=10.5,
            entry_price=10.0,
            stop_loss=9.5
        )
        assert decision.code == "sh.600000"
        assert decision.action == "buy"
        assert decision.confidence == 0.85
        assert decision.target_price == 10.5
    
    def test_unhook_strategy_creation(self):
        """测试解套策略模型创建"""
        strategy = UnhookStrategy(
            code="sh.600000",
            current_price=8.0,
            cost_price=10.0,
            suggestion="补仓摊平",
            details={"action": "buy", "price": 8.5, "percent": 0.5}
        )
        assert strategy.code == "sh.600000"
        assert strategy.suggestion == "补仓摊平"
        assert strategy.current_price == 8.0
        assert strategy.cost_price == 10.0

class TestBrainAnalyzer:
    """测试Brain分析器"""
    
    def test_brain_analysis(self):
        """测试Brain分析功能"""
        analyzer = BrainAnalyzer()
        
        # 模拟技术数据
        technical_data = {
            "rsi": 30.0,
            "macd": {"macd": -0.1, "signal": -0.05, "histogram": -0.05},
            "kdj": {"k": 20.0, "d": 30.0, "j": 10.0},
            "bollinger": {"upper": 11.0, "middle": 10.0, "lower": 9.0},
            "close": [10.0, 10.1, 10.2]
        }
        
        decision = analyzer.analyze("sh.600000", technical_data, 10.0)
        
        assert isinstance(decision, BrainDecision)
        assert decision.code == "sh.600000"
        assert decision.action in ["buy", "sell", "hold"]
        assert 0 <= decision.confidence <= 1
        assert decision.target_price > 0
        assert decision.entry_price > 0
        assert decision.stop_loss > 0

class TestUnhookEngine:
    """测试解套引擎"""
    
    def test_unhook_strategy_calculation(self):
        """测试解套策略计算"""
        engine = UnhookEngine()
        
        # 测试不同亏损程度的策略
        # 亏损率计算: (cost - current) / cost
        test_cases = [
            (9.8, 10.0, "持有观察"),      # 2%亏损 < 5%
            (9.0, 10.0, "高抛低吸做T"),   # 10%亏损 < 15%
            (8.0, 10.0, "补仓摊平"),      # 20%亏损 < 30%
            (6.0, 10.0, "分析基本面，考虑换股"),  # 40%亏损 < 50%
            (4.0, 10.0, "长期持有等待解套"),   # 60%亏损 >= 50% (默认市场环境 normal)
        ]
        
        for current, cost, expected_suggestion in test_cases:
            strategy = engine.calculate_strategy("sh.600000", current, cost)
            assert strategy.suggestion == expected_suggestion
    
    def test_recovery_probability(self):
        """测试解套概率计算"""
        engine = UnhookEngine()
        
        result = engine.get_recovery_probability("sh.600000", 8.0, 10.0)
        
        assert "probability" in result
        assert "timeframe" in result
        assert "loss_rate" in result
        assert 0 <= result["probability"] <= 1

class TestBacktestEngine:
    """测试回测引擎"""
    
    def test_backtest_buy_and_hold(self):
        """测试买入持有策略回测"""
        engine = BacktestEngine(initial_capital=100000)
        
        # 模拟历史数据
        data = [
            {"date": "2023-01-01", "close": 10.0},
            {"date": "2023-01-02", "close": 10.1},
            {"date": "2023-01-03", "close": 10.2},
            {"date": "2023-01-04", "close": 10.1},
            {"date": "2023-01-05", "close": 10.3},
        ]
        
        result = engine.run(data, "buy_and_hold")
        
        assert "total_return" in result
        assert "final_capital" in result
        assert result["final_capital"] > 0
    
    def test_backtest_moving_average(self):
        """测试移动平均线策略回测"""
        engine = BacktestEngine(initial_capital=100000)
        
        # 模拟历史数据
        data = [
            {"date": "2023-01-01", "close": 10.0},
            {"date": "2023-01-02", "close": 10.1},
            {"date": "2023-01-03", "close": 10.2},
            {"date": "2023-01-04", "close": 10.1},
            {"date": "2023-01-05", "close": 10.3},
            {"date": "2023-01-06", "close": 10.4},
            {"date": "2023-01-07", "close": 10.5},
            {"date": "2023-01-08", "close": 10.4},
            {"date": "2023-01-09", "close": 10.3},
            {"date": "2023-01-10", "close": 10.2},
        ]
        
        result = engine.run(data, "moving_average", fast_period=3, slow_period=5)
        
        assert "total_return" in result
        assert "num_trades" in result
