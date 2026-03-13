import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import os

# 确保models目录存在
os.makedirs('models', exist_ok=True)

# 生成模拟数据
def generate_simulation_data(n_samples=1000, normal_periods=800, anomaly_periods=200):
    """生成模拟的泵阀管道数据"""
    timestamps = pd.date_range(start='2026-01-01', periods=n_samples, freq='10S')
    
    # 正常数据：压力和流量相对稳定
    pressure = np.random.normal(0.8, 0.02, normal_periods)
    flow = np.random.normal(12.5, 0.2, normal_periods)
    
    # 异常数据：压力逐渐上升，流量逐渐下降（模拟堵塞）
    anomaly_pressure = np.linspace(0.8, 1.2, anomaly_periods) + np.random.normal(0, 0.02, anomaly_periods)
    anomaly_flow = np.linspace(12.5, 8.0, anomaly_periods) + np.random.normal(0, 0.2, anomaly_periods)
    
    # 合并数据
    pressure = np.concatenate([pressure, anomaly_pressure])
    flow = np.concatenate([flow, anomaly_flow])
    
    # 标签：0-正常，1-异常
    labels = np.concatenate([np.zeros(normal_periods), np.ones(anomaly_periods)])
    
    # 创建DataFrame
    df = pd.DataFrame({
        'timestamp': timestamps,
        'pressure': pressure,
        'flow': flow,
        'label': labels
    })
    
    return df

# 准备训练数据
def prepare_data(data, look_back=10):
    """准备LSTM模型的训练数据"""
    # 只使用压力和流量数据
    features = data[['pressure', 'flow']].values
    labels = data['label'].values
    
    # 数据归一化
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_features = scaler.fit_transform(features)
    
    # 创建序列数据
    X, y = [], []
    for i in range(len(scaled_features) - look_back):
        X.append(scaled_features[i:i+look_back])
        y.append(labels[i+look_back])
    
    X = np.array(X)
    y = np.array(y)
    
    return X, y, scaler

# 构建LSTM模型
def build_lstm_model(input_shape):
    """构建LSTM模型"""
    model = Sequential([
        LSTM(64, return_sequences=True, input_shape=input_shape),
        Dropout(0.2),
        LSTM(32, return_sequences=False),
        Dropout(0.2),
        Dense(1, activation='sigmoid')
    ])
    
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model

# 训练模型
def train_model():
    """训练LSTM模型"""
    # 生成模拟数据
    data = generate_simulation_data()
    
    # 准备数据
    look_back = 10
    X, y, scaler = prepare_data(data, look_back)
    
    # 划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 构建模型
    input_shape = (X_train.shape[1], X_train.shape[2])
    model = build_lstm_model(input_shape)
    
    # 训练模型
    model.fit(X_train, y_train, epochs=50, batch_size=32, validation_data=(X_test, y_test))
    
    # 评估模型
    loss, accuracy = model.evaluate(X_test, y_test)
    print(f"模型测试准确率: {accuracy:.4f}")
    
    # 保存模型
    model.save('models/lstm_anomaly_detector.h5')
    
    # 保存scaler
    import joblib
    joblib.dump(scaler, 'models/scaler.pkl')
    
    print("模型训练完成并保存到models目录")

if __name__ == "__main__":
    train_model()
