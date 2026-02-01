import os
import pandas as pd

data_dir = r'C:\Users\life8\.qlib\stock_data\source\all_1d_original'
files = os.listdir(data_dir)

print(f'Total files: {len(files)}')

found_2024 = False
for i, f in enumerate(files[:50]):
    try:
        df = pd.read_csv(os.path.join(data_dir, f))
        dates = df['date'].astype(str)
        if dates.str.contains('2024').any():
            print(f'{f}: has 2024 data')
            print(f'  Date range: {dates.min()} to {dates.max()}')
            found_2024 = True
            break
    except Exception as e:
        print(f'{f}: error - {e}')

print(f'\nFound 2024 data: {found_2024}')
