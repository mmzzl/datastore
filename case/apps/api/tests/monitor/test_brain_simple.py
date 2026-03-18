import sys
import os

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 往上推2层找到api目录
api_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, api_dir)

print(f"Added to path: {api_dir}")
print(f"Python version: {sys.version}")

# 测试Brain模型（不依赖pandas/numpy）
def test_brain_models():
    """测试Brain模型"""
    from app.monitor.brain.models import BrainDecision, UnhookStrategy
    
    # 测试BrainDecision
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
    print("BrainDecision模型测试通过")
    
    # 测试UnhookStrategy
    strategy = UnhookStrategy(
        code="sh.600000",
        current_price=8.0,
        cost_price=10.0,
        suggestion="补仓摊平",
        details={"action": "buy", "price": 8.5, "percent": 0.5}
    )
    assert strategy.code == "sh.600000"
    assert strategy.suggestion == "补仓摊平"
    print("UnhookStrategy模型测试通过")

def test_unhook_engine():
    """测试解套引擎"""
    from app.monitor.brain.unhook import UnhookEngine
    
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
        loss_rate = (cost - current) / cost
        print(f"亏损{loss_rate:.1%} - 期望: {expected_suggestion}, 实际: {strategy.suggestion}")
        assert strategy.suggestion == expected_suggestion, f"亏损{loss_rate:.1%}测试失败"

if __name__ == "__main__":
    test_brain_models()
    test_unhook_engine()
    print("\n所有Brain系统测试通过！")
