import os
import pandas as pd

data_dir = r'C:\Users\life8\.qlib\stock_data\source\all_1d_original'
files = os.listdir(data_dir)

print('Checking date ranges of downloaded files:\n')

for i, f in enumerate(files[:10]):
    try:
        df = pd.read_csv(os.path.join(data_dir, f))
        dates = df['date'].astype(str)
        print(f'{f}:')
        print(f'  Rows: {len(df)}')
        print(f'  Earliest: {dates.min()}')
        print(f'  Latest: {dates.max()}')
        print()
    except Exception as e:
        print(f'{f}: error - {e}\n')
