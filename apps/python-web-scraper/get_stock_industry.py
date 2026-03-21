import akshare as ak
import pandas as pd
import time
import warnings
warnings.filterwarnings("ignore")

def get_all_concept_boards_stocks(save_excel: bool = True) -> pd.DataFrame:
    """
    遍历所有概念板块（concept_boards），批量获取每个板块下的所有股票
    :param save_excel: 是否保存到Excel
    :return: 包含所有板块+对应股票的DataFrame
    """
    # ===================== 步骤1：获取所有概念板块列表（df） =====================
    print("📌 正在获取所有概念板块列表...")
    concept_boards = ak.stock_board_concept_name_em()
    total_boards = len(concept_boards)
    print(f"✅ 共获取到 {total_boards} 个概念板块")
    
    # 存储所有板块的股票数据
    all_board_stocks = []
    fail_boards = []  # 记录获取失败的板块

    # ===================== 步骤2：循环遍历每个概念板块 =====================
    for idx, row in concept_boards.iterrows():
        board_name = row["板块名称"]
        board_code = row["板块代码"]
        progress = f"({idx+1}/{total_boards})"

        print(f"\n{progress} 正在获取「{board_name}」板块的股票...")
        
        try:
            # 获取当前板块的股票数据
            board_stocks = ak.stock_board_concept_cons_em(symbol=board_name)
            
            # 空数据跳过
            if board_stocks.empty:
                print(f"⚠️ {progress} 「{board_name}」板块无股票数据，跳过")
                fail_boards.append({"板块名称": board_name, "原因": "无股票数据"})
                continue
            
            # 仅保留核心字段：板块名称 + 板块代码 + 股票代码 + 股票名称
            board_stocks = board_stocks[["代码", "名称"]].copy()
            board_stocks["板块名称"] = board_name
            board_stocks["板块代码"] = board_code
            
            # 调整字段顺序
            board_stocks = board_stocks[["板块名称", "板块代码", "代码", "名称"]]
            
            # 添加到总列表
            all_board_stocks.append(board_stocks)
            
            # 打印当前板块结果
            stock_count = len(board_stocks)
            print(f"✅ {progress} 「{board_name}」获取成功，共 {stock_count} 只股票")
            
            # 防反爬：间隔0.3秒，避免请求过快被限制
            time.sleep(0.3)
            
        except Exception as e:
            print(f"❌ {progress} 「{board_name}」获取失败：{str(e)[:50]}")
            fail_boards.append({"板块名称": board_name, "原因": str(e)[:50]})
            continue

    # ===================== 步骤3：合并所有数据 =====================
    if not all_board_stocks:
        raise ValueError("❌ 所有板块均获取失败！")
    
    df_all = pd.concat(all_board_stocks, ignore_index=True)
    
    # ===================== 步骤4：保存数据 =====================
    if save_excel:
        # 保存所有板块股票数据
        main_excel = "东方财富_所有概念板块_所有股票.csv"
        df_all.to_csv(main_excel, encoding="utf-8", index=False)
        print(f"\n📊 所有板块数据已保存到：{main_excel}")
        
        # 保存失败的板块（便于排查）
        if fail_boards:
            fail_df = pd.DataFrame(fail_boards)
            fail_excel = "获取失败的板块列表.xlsx"
            fail_df.to_excel(fail_excel, index=False)
            print(f"⚠️ 失败板块列表已保存到：{fail_excel}")

    # ===================== 步骤5：输出统计信息 =====================
    print(f"\n===================== 统计结果 =====================")
    print(f"📈 成功获取板块数：{len(all_board_stocks)}")
    print(f"❌ 失败板块数：{len(fail_boards)}")
    print(f"📋 总计股票数：{len(df_all)}")
    print(f"🌐 涉及板块示例：{df_all['板块名称'].unique()[:10]}")

    return df_all

# ===================== 主程序执行 =====================
if __name__ == "__main__":
    try:
        # 调用函数：遍历所有概念板块，获取所有股票
        all_stock_data = get_all_concept_boards_stocks()
        
        # 示例：筛选「腾讯云」板块的股票
        tencent_cloud_stocks = all_stock_data[all_stock_data["板块名称"] == "腾讯云"]
        print(f"\n🔍 腾讯云板块股票：")
        print(tencent_cloud_stocks)
        
    except Exception as e:
        print(f"\n❌ 程序执行失败：{str(e)}")