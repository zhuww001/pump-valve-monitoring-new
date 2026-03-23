-- 创建设备表
CREATE TABLE IF NOT EXISTS device (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    location VARCHAR(200) NOT NULL,
    pressure_threshold FLOAT NOT NULL DEFAULT 2.0,
    flow_threshold FLOAT NOT NULL DEFAULT 5.0,
    temperature_threshold FLOAT NOT NULL DEFAULT 80.0,
    status VARCHAR(20) NOT NULL DEFAULT 'normal',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 创建预警记录表
CREATE TABLE IF NOT EXISTS warning_record (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(50) NOT NULL,
    warning_type VARCHAR(50) NOT NULL,
    warning_value FLOAT NOT NULL,
    threshold FLOAT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'unprocessed',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 创建数据源表
CREATE TABLE IF NOT EXISTS data_source (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_enabled BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 插入初始数据
-- 插入设备数据（包含 B0320001）
INSERT INTO device (device_id, name, location) VALUES
('device_1', '泵 A', '一号车间'),
('device_2', '泵 B', '二号车间'),
('device_3', '泵 C', '三号车间'),
('B0320001', '泵 D', '四号车间')
ON CONFLICT (device_id) DO NOTHING;

-- 插入数据源数据
INSERT INTO data_source (name, type, config, is_enabled) VALUES
('模拟数据源', 'simulate', '{}'::jsonb, false),
('API 数据源', 'api', '{"base_url": "", "token": "", "endpoint": "/api/pump-data"}'::jsonb, false),
('设备上报数据源', 'report', '{}'::jsonb, false),
('MQTT 数据源', 'mqtt', '{"broker": "10.20.110.60", "port": 1883, "topic": "/iot/data"}'::jsonb, true)
ON CONFLICT DO NOTHING;
