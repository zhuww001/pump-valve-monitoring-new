from influxdb_client import InfluxDBClient
import sys

# 直接复用你 config.py 的配置
INFLUXDB_URL = "http://localhost:8086"
INFLUXDB_TOKEN = "your-token"
INFLUXDB_ORG = "your-org"
INFLUXDB_BUCKET = "pump_data"

print("开始连接InfluxDB...")
try:
    # 连接 InfluxDB
    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
    print("InfluxDB连接成功")
    
    query_api = client.query_api()
    print("获取查询API成功")
    
    # 查询最近1小时所有设备数据
    query = '''
    from(bucket: "pump_data")
      |> range(start: -1h)
      |> filter(fn: (r) => r._measurement == "pump_monitor")
      |> yield(name: "pump_monitor")
    '''
    
    print("执行查询...")
    tables = query_api.query(query)
    print(f"查询完成，返回 {len(tables)} 个表")
    
    if not tables:
        print("没有找到数据")
    else:
        print("打印查询结果:")
        for table in tables:
            print(f"表: {table}")
            for record in table.records:
                print(f"时间: {record['_time']} | 设备: {record['device_id']} | {record['_field']}: {record['_value']}")
    
    client.close()
    print("连接已关闭")
except Exception as e:
    print(f"错误: {e}")
    print(f"错误类型: {type(e).__name__}")
    print(f"错误详情: {sys.exc_info()}")
    if 'client' in locals():
        client.close()
    sys.exit(1)