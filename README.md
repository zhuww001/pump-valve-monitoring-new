# 泵阀管道堵塞预警系统

实时监测泵阀设备运行状态、预测管道堵塞风险，并提供历史数据查询与分析功能。

---

## 快速启动

### 一键启动（本地开发模式）

```bash
./start.sh
```

启动后访问：

| 服务 | 地址 |
|------|------|
| 主监控界面（Flask） | http://localhost:5001 |
| 前端平台（Vue3） | http://localhost:5173 |
| 后端 API（FastAPI） | http://localhost:8000 |
| API 文档（Swagger） | http://localhost:8000/docs |
| 边缘计算网关 | http://localhost:8001 |

按 **Ctrl+C** 停止所有服务。

### 启动选项

```bash
./start.sh              # 默认：本地开发模式，启动所有服务
./start.sh --docker     # Docker Compose 模式（需安装 Docker）
./start.sh --simple     # 仅启动主监控服务（Flask，不含完整平台）
./start.sh --no-edge    # 不启动边缘计算网关
./start.sh --skip-install  # 跳过依赖安装（已安装过时使用）
./start.sh --help       # 查看所有选项
```

### Docker 部署

```bash
./start.sh --docker
```

启动后访问 http://localhost （前端）和 http://localhost:8000 （后端 API）。

停止：

```bash
cd pump-data-platform && docker-compose down
```

---

## 项目结构

```
pump-valve-monitoring/
├── start.sh                  # ★ 一键启动脚本
├── app.py                    # 主监控服务（Flask，端口 5001）
├── config/
│   └── config.yaml           # 设备配置
├── data/                     # 设备数据（CSV）
├── logs/                     # 运行日志
├── templates/                # Flask HTML 模板
├── edge-gateway/             # 边缘计算网关（FastAPI，端口 8001）
│   ├── main.py               # 网关服务
│   ├── client.py             # 模拟客户端（测试用）
│   └── requirements.txt
└── pump-data-platform/       # 完整监控平台
    ├── backend/              # 后端（FastAPI，端口 8000）
    │   ├── main.py
    │   ├── api/              # API 路由
    │   ├── core/             # 核心模块（配置、数据采集、服务）
    │   └── requirements.txt
    ├── frontend/             # 前端（Vue3 + Vite，端口 5173）
    │   ├── src/
    │   │   ├── views/        # 页面组件
    │   │   ├── router.js     # 路由配置
    │   │   └── App.vue
    │   ├── package.json
    │   └── vite.config.js
    ├── docker-compose.yml    # Docker 编排配置
    ├── .env                  # 环境变量配置
    └── start.sh              # 平台内部启动脚本
```

---

## 技术栈

| 层次 | 技术 |
|------|------|
| 主监控后端 | Python + Flask |
| 完整平台后端 | FastAPI + Uvicorn |
| 前端 | Vue3 + Element Plus + ECharts + Vite |
| 边缘网关 | FastAPI + httpx + paho-mqtt |
| AI 模型 | TensorFlow/Keras (LSTM) + NumPy + SciPy |
| 数据库（Docker 模式） | PostgreSQL + InfluxDB + Redis |
| 容器化 | Docker Compose |

---

## 环境要求

- **Python 3.8+**（脚本自动创建 `.venv` 虚拟环境）
- **Node.js 16+**（完整平台前端，`--simple` 模式不需要）
- **Docker**（仅 `--docker` 模式需要）

---

## 功能模块

### 主监控服务（Flask）

- 设备列表与设备详情
- 实时数据展示与历史数据查询
- 预警记录管理
- 设备信息编辑
- 数据读取自 `data/` 目录 CSV 文件，无需数据库

### 完整平台（pump-data-platform）

- **实时监控**：设备状态实时展示与趋势图，支持分页（每页 3/6/9/12 条数据）
- **设备管理**：列表、搜索、跳转操作，支持分页
- **历史数据**：支持 1h/24h/72h 及自定义时间范围，图表 + 列表双视图，数据导出
- **预警管理**：预警记录查询与状态管理，支持 AI 智能检测
- **配置中心**：系统配置与设备阈值管理
- **系统管理**：用户管理、角色管理、菜单管理（完整权限控制）

### AI 预警检测

- **多模式检测**：Z-Score 统计检测、趋势分析、阈值突破检测
- **智能预测**：基于 LSTM 模型的异常预测
- **置信度评估**：自动计算预警置信度（0-100%）
- **动态阈值**：支持设备级阈值配置

### 边缘计算网关

- 接收传感器数据并转发到主系统
- 支持多设备数据聚合
- 断网缓存与续传
- 模拟上报接口（测试用）
- MQTT 协议支持（可选）

---

## 日志

服务日志写入 `logs/` 目录：

```
logs/
├── flask.log          # 主监控服务日志
├── backend.log        # 后端 API 日志
├── frontend.log       # 前端开发服务日志
└── edge-gateway.log   # 边缘网关日志
```

---

## 数据说明

**设备数据结构**：`device_id, name, location, manager, contact, status, timestamp, pressure, flow, temperature, source_type, gateway_id`

**预警数据结构**：`warning_id, device_id, warning_type, message, timestamp, status`

**默认预警阈值**（可在 `.env` 中修改）：

| 指标 | 阈值 | 说明 |
|------|------|------|
| 压力 | 2.0 MPa | 超过此值触发预警 |
| 流量 | 5.0 m³/h | 低于此值触发预警 |
| 温度 | 80.0 °C | 超过此值触发预警 |

**AI 检测置信度**：
- 高置信度预警：≥ 80%（立即触发）
- 低置信度预警：< 50%（忽略）
- 中等置信度：50%-80%（持续监测）

---

## 注意事项

- 本地开发模式使用模拟数据，无需数据库
- Docker 模式会自动启动 PostgreSQL、InfluxDB、Redis
- 边缘网关通过环境变量 `MAIN_SYSTEM_URL` 配置主系统地址（默认 `http://localhost:8000`）
- 修改 `.env` 文件可调整端口、数据库连接、预警阈值等配置
