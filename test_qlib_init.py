import sys, os
sys.path.insert(0, 'apps/api')
os.environ['PYTHONPATH'] = 'apps/api'

try:
    import qlib
    from qlib.config import REG_CN
    from app.qlib.config import QlibConfig

    print(f"Qlib provider_uri: {QlibConfig.provider_uri}")
    print(f"Provider uri exists: {os.path.exists(QlibConfig.provider_uri)}")
    
    if os.path.exists(QlibConfig.provider_uri):
        print(f"Contents of provider_uri: {os.listdir(QlibConfig.provider_uri)}")
        
        cal_path = os.path.join(QlibConfig.provider_uri, "calendars", "day.txt")
        print(f"Calendar file exists: {os.path.exists(cal_path)}")
        
        if os.path.exists(cal_path):
            with open(cal_path, 'r') as f:
                lines = f.readlines()
                print(f"Calendar has {len(lines)} lines")
                print(f"Last 5 lines: {lines[-5:] if len(lines) > 5 else lines}")
        
        inst_path = os.path.join(QlibConfig.provider_uri, "instruments", "all.txt")
        print(f"Instruments file exists: {os.path.exists(inst_path)}")

    print("Trying to initialize Qlib...")
    qlib.init(
        provider_uri=QlibConfig.provider_uri,
        region=REG_CN,
        kernels=1,
    )
    print("Qlib initialized successfully!")

except Exception as e:
    import traceback
    print(f"Error: {e}")
    print(f"Traceback:\n{traceback.format_exc()}")
