#!/usr/bin/env python3
"""
数据库初始化脚本
用于创建必要的数据库表结构
"""

import psycopg2
from core.config import settings


def init_database():
    """初始化数据库表结构"""
    try:
        # 连接数据库
        conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB
        )
        cursor = conn.cursor()
        
        print("开始创建数据库表...")
        
        # 创建 device 表
        device_table_sql = """
        CREATE TABLE IF NOT EXISTS device (
            id SERIAL PRIMARY KEY,
            device_id VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            location VARCHAR(200),
            pressure_threshold FLOAT DEFAULT 2.0,
            flow_threshold FLOAT DEFAULT 5.0,
            temperature_threshold FLOAT DEFAULT 80.0,
            status VARCHAR(20) DEFAULT 'normal',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """
        cursor.execute(device_table_sql)
        print("创建 device 表成功")
        
        # 创建 warning_record 表
        warning_record_table_sql = """
        CREATE TABLE IF NOT EXISTS warning_record (
            id SERIAL PRIMARY KEY,
            device_id VARCHAR(50) NOT NULL,
            warning_type VARCHAR(50) NOT NULL,
            warning_value FLOAT NOT NULL,
            threshold FLOAT NOT NULL,
            status VARCHAR(20) DEFAULT 'unprocessed',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            FOREIGN KEY (device_id) REFERENCES device(device_id)
        )
        """
        cursor.execute(warning_record_table_sql)
        print("创建 warning_record 表成功")
        
        # 插入初始设备数据
        insert_devices_sql = """
        INSERT INTO device (device_id, name, location) VALUES
        ('device_1', '泵A', '一号车间'),
        ('device_2', '泵B', '二号车间'),
        ('device_3', '泵C', '三号车间')
        ON CONFLICT (device_id) DO NOTHING
        """
        cursor.execute(insert_devices_sql)
        print("插入初始设备数据成功")
        
        # 提交事务
        conn.commit()
        print("数据库初始化完成")
        
        # 关闭连接
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        raise


if __name__ == "__main__":
    init_database()
