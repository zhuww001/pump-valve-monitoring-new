# 数据库部署指南

## 📋 部署模式说明

本项目支持两种部署模式：
1. **本地开发模式**（LOCAL_MODE=true）- 使用内存缓存和模拟数据
2. **生产数据库模式**（LOCAL_MODE=false）- 使用 PostgreSQL + InfluxDB + Redis

---

## 🚀 快速部署（Docker Compose）

### 1. 启动所有服务

```bash
cd pump-data-platform

# 启动数据库和后端服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 2. 验证服务状态

```bash
# 检查容器运行状态
docker-compose ps

# 应该看到以下服务：
# - postgres (PostgreSQL 数据库)
# - influxdb (InfluxDB 时序数据库)
# - redis (Redis 缓存)
# - backend (FastAPI 后端服务)
# - frontend (Vue3 前端服务)
```

### 3. 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端界面 | http://localhost | Vue3 管理控制台 |
| 后端 API | http://localhost:8000 | FastAPI 接口 |
| API 文档 | http://localhost:8000/docs | Swagger 文档 |
| PostgreSQL | localhost:5432 | 关系型数据库 |
| InfluxDB | http://localhost:8086 | 时序数据库 |
| Redis | localhost:6379 | 缓存服务 |

---

## 🔧 手动部署（不使用 Docker）

### 1. 安装数据库

#### PostgreSQL 15+

```bash
# macOS (Homebrew)
brew install postgresql@15
brew services start postgresql@15

# Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql-15
sudo systemctl start postgresql

# 创建数据库
createdb pump_valve_db
psql -d pump_valve_db -f pump-data-platform/sql/init.sql
```

#### InfluxDB 2.7+

```bash
# 下载并安装
# https://portal.influxdata.com/downloads/

# 初始化配置
influx setup \
  --username admin \
  --password password \
  --org your-org \
  --bucket pump_data \
  --retention 0 \
  --token your-token \
  --force
```

#### Redis 7+

```bash
# macOS (Homebrew)
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis
```

### 2. 配置环境变量

编辑 `pump-data-platform/.env` 文件：

```bash
# 关闭本地模式
LOCAL_MODE=false

# 数据库配置
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=你的密码
POSTGRES_DB=pump_valve_db

# InfluxDB 配置
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your-token
INFLUXDB_ORG=your-org
INFLUXDB_BUCKET=pump_data

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 3. 安装依赖并启动

```bash
# 后端
cd pump-data-platform/backend
pip install -r requirements.txt
python main.py

# 前端
cd pump-data-platform/frontend
npm install
npm run dev
```

---

## 📊 数据库表结构

### PostgreSQL 表

1. **device** - 设备信息表
   - id, device_id, name, location
   - pressure_threshold, flow_threshold, temperature_threshold
   - status, created_at, updated_at

2. **warning_record** - 预警记录表
   - id, device_id, warning_type, warning_value, threshold
   - status, created_at, updated_at

3. **data_source** - 数据源配置表
   - id, name, type, config (JSONB)
   - is_enabled, created_at, updated_at

### InfluxDB Bucket

- **pump_data** - 存储实时监测数据和历史数据

### Redis Key 结构

- `realtime:{device_id}` - 设备实时数据（TTL: 3600s）
- `device:list` - 设备列表缓存

---

## ⚙️ MQTT 数据源配置

当前配置为从 MQTT 接收实时数据：

```bash
# .env 配置
DATA_SOURCE_TYPE=mqtt
MQTT_BROKER=10.20.110.60
MQTT_PORT=1883
MQTT_USERNAME=admin
MQTT_PASSWORD=Tsit@2023
MQTT_TOPIC=/iot/data
```

**MQTT 消息格式：**

```json
{
  "B0320001": [
    {
      "values": {
        "flow": 4.5,
        "temperature": 82,
        "pressure": 2.1
      },
      "ts": 1774236290086
    }
  ]
}
```

---

## 🔍 常见问题

### 1. 数据库连接失败

```bash
# 检查 PostgreSQL 是否运行
pg_isready -h localhost -p 5432

# 检查 InfluxDB 是否运行
curl http://localhost:8086/health

# 检查 Redis 是否运行
redis-cli ping
```

### 2. 数据表不存在

```bash
# 重新执行初始化脚本
psql -U postgres -d pump_valve_db -f sql/init.sql
```

### 3. MQTT 无法连接

```bash
# 测试 MQTT 连接
mosquitto_sub -h 10.20.110.60 -p 1883 -t "/iot/data" -v
```

---

## 📝 部署检查清单

- [ ] PostgreSQL 已安装并运行
- [ ] InfluxDB 已安装并完成初始化
- [ ] Redis 已安装并运行
- [ ] `.env` 文件已正确配置
- [ ] `LOCAL_MODE=false` 已设置
- [ ] 数据库表已创建（执行 init.sql）
- [ ] MQTT 连接配置正确
- [ ] 后端服务可以正常启动
- [ ] 前端服务可以正常访问
- [ ] 预警功能测试通过

---

## 🎯 下一步

部署完成后，系统会自动：
1. ✅ 从 MQTT 接收实时数据
2. ✅ 使用 AI 模型进行异常检测
3. ✅ 自动生成预警记录
4. ✅ 存储历史数据到 InfluxDB
5. ✅ 缓存实时数据到 Redis

访问前端界面查看设备监控和预警信息！
