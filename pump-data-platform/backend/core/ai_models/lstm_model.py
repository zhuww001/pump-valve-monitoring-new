import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input
from tensorflow.keras.optimizers import Adam
from typing import List, Dict, Tuple, Optional
import os
import json


class LSTMModel:
    """
    基于LSTM的异常检测和预测模型
    """
    
    def __init__(self, sequence_length: int = 10, model_path: str = None):
        """
        Args:
            sequence_length: 序列长度（时间步）
            model_path: 模型保存路径
        """
        self.sequence_length = sequence_length
        self.model = None
        self.model_path = model_path
        self.is_trained = False
        self.feature_min = None
        self.feature_max = None
    
    def create_model(self, input_shape: tuple) -> tf.keras.Model:
        """创建LSTM模型"""
        model = Sequential()
        model.add(Input(shape=input_shape))
        model.add(LSTM(64, return_sequences=True))
        model.add(Dropout(0.2))
        model.add(LSTM(32, return_sequences=False))
        model.add(Dropout(0.2))
        model.add(Dense(16, activation='relu'))
        model.add(Dense(3, activation='linear'))  # 预测压力、流量、温度
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def normalize(self, features: np.ndarray) -> np.ndarray:
        """归一化数据"""
        if self.feature_min is None or self.feature_max is None:
            self.feature_min = np.min(features, axis=0)
            self.feature_max = np.max(features, axis=0)
        
        # 避免除零
        feature_range = self.feature_max - self.feature_min
        feature_range[feature_range == 0] = 1
        
        return (features - self.feature_min) / feature_range
    
    def denormalize(self, normalized_features: np.ndarray) -> np.ndarray:
        """反归一化数据"""
        if self.feature_min is None or self.feature_max is None:
            raise ValueError("模型未训练，无法反归一化")
        
        feature_range = self.feature_max - self.feature_min
        feature_range[feature_range == 0] = 1
        
        return normalized_features * feature_range + self.feature_min
    
    def prepare_data(self, data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """准备训练数据"""
        if len(data) < self.sequence_length + 1:
            raise ValueError(f"数据长度不足，需要至少{self.sequence_length + 1}个数据点")
        
        # 提取特征
        features = []
        for item in data:
            features.append([
                item.get('pressure', 0),
                item.get('flow', 0),
                item.get('temperature', 0)
            ])
        
        features = np.array(features)
        
        # 归一化
        scaled_features = self.normalize(features)
        
        # 创建序列数据
        X = []
        y = []
        
        for i in range(len(scaled_features) - self.sequence_length):
            X.append(scaled_features[i:i+self.sequence_length])
            y.append(scaled_features[i+self.sequence_length])
        
        return np.array(X), np.array(y)
    
    def train(self, data: List[Dict], epochs: int = 100, batch_size: int = 32) -> Dict:
        """训练模型"""
        X, y = self.prepare_data(data)
        
        if self.model is None:
            self.model = self.create_model((X.shape[1], X.shape[2]))
        
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            verbose=1
        )
        
        self.is_trained = True
        
        # 保存模型
        if self.model_path:
            self.save_model(self.model_path)
        
        return {
            'loss': history.history['loss'][-1],
            'val_loss': history.history['val_loss'][-1],
            'mae': history.history['mae'][-1],
            'val_mae': history.history['val_mae'][-1]
        }
    
    def predict(self, recent_data: List[Dict]) -> List[float]:
        """
        预测未来值
        
        Args:
            recent_data: 最近的序列数据
        
        Returns:
            预测的压力、流量、温度值
        """
        if not self.is_trained:
            raise ValueError("模型未训练")
        
        if len(recent_data) < self.sequence_length:
            raise ValueError(f"需要至少{self.sequence_length}个数据点")
        
        # 提取特征
        features = []
        for item in recent_data[-self.sequence_length:]:
            features.append([
                item.get('pressure', 0),
                item.get('flow', 0),
                item.get('temperature', 0)
            ])
        
        features = np.array(features)
        
        # 归一化
        scaled_features = self.normalize(features)
        X = np.array([scaled_features])
        
        # 预测
        prediction = self.model.predict(X, verbose=0)[0]
        
        # 反归一化
        prediction = self.denormalize(prediction)
        
        return prediction.tolist()
    
    def detect_anomaly(self, recent_data: List[Dict], threshold: float = 0.1) -> Tuple[bool, float, Dict]:
        """
        检测异常
        
        Args:
            recent_data: 最近的数据
            threshold: 异常阈值
        
        Returns:
            (是否异常, 异常评分, 详细信息)
        """
        if not self.is_trained:
            raise ValueError("模型未训练")
        
        if len(recent_data) < self.sequence_length + 1:
            raise ValueError(f"需要至少{self.sequence_length + 1}个数据点")
        
        # 预测最后一个点
        prediction = self.predict(recent_data[:-1])
        
        # 实际值
        actual = [
            recent_data[-1].get('pressure', 0),
            recent_data[-1].get('flow', 0),
            recent_data[-1].get('temperature', 0)
        ]
        
        # 计算误差
        error = np.abs(np.array(prediction) - np.array(actual))
        
        # 计算异常评分
        max_error = max(error)
        mean_error = np.mean(error)
        
        # 归一化误差（基于历史数据的范围）
        feature_ranges = self.get_feature_ranges(recent_data)
        normalized_errors = error / feature_ranges
        
        anomaly_score = np.mean(normalized_errors)
        is_anomaly = anomaly_score > threshold
        
        return is_anomaly, anomaly_score, {
            'prediction': prediction,
            'actual': actual,
            'error': error.tolist(),
            'normalized_error': normalized_errors.tolist(),
            'threshold': threshold
        }
    
    def get_feature_ranges(self, data: List[Dict]) -> np.ndarray:
        """获取特征的范围"""
        pressures = [item.get('pressure', 0) for item in data]
        flows = [item.get('flow', 0) for item in data]
        temperatures = [item.get('temperature', 0) for item in data]
        
        ranges = [
            max(pressures) - min(pressures) if len(pressures) > 1 else 1,
            max(flows) - min(flows) if len(flows) > 1 else 1,
            max(temperatures) - min(temperatures) if len(temperatures) > 1 else 1
        ]
        
        # 避免除零
        ranges = [max(r, 0.1) for r in ranges]
        
        return np.array(ranges)
    
    def save_model(self, path: str):
        """保存模型"""
        if self.model:
            os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
            self.model.save(path)
            
            # 保存归一化参数
            scaler_path = path.replace('.keras', '_scaler.json')
            with open(scaler_path, 'w') as f:
                json.dump({
                    'feature_min': self.feature_min.tolist() if self.feature_min is not None else None,
                    'feature_max': self.feature_max.tolist() if self.feature_max is not None else None
                }, f)
    
    def load_model(self, path: str):
        """加载模型"""
        if os.path.exists(path):
            self.model = load_model(path)
            
            # 加载归一化参数
            scaler_path = path.replace('.keras', '_scaler.json')
            if os.path.exists(scaler_path):
                with open(scaler_path, 'r') as f:
                    scaler_params = json.load(f)
                    if scaler_params['feature_min']:
                        self.feature_min = np.array(scaler_params['feature_min'])
                    if scaler_params['feature_max']:
                        self.feature_max = np.array(scaler_params['feature_max'])
            
            self.is_trained = True
    
    def generate_synthetic_data(self, samples: int = 1000) -> List[Dict]:
        """生成合成数据用于训练"""
        data = []
        base_pressure = 1.0
        base_flow = 10.0
        base_temperature = 45.0
        
        for i in range(samples):
            # 正常波动
            pressure = base_pressure + np.sin(i * 0.1) * 0.2 + np.random.normal(0, 0.05)
            flow = base_flow + np.cos(i * 0.15) * 1.0 + np.random.normal(0, 0.2)
            temperature = base_temperature + np.sin(i * 0.05) * 2.0 + np.random.normal(0, 0.5)
            
            # 注入异常
            if i % 50 == 0:
                # 压力异常
                pressure = base_pressure + 1.0 + np.random.normal(0, 0.2)
            elif i % 70 == 0:
                # 流量异常
                flow = base_flow - 5.0 + np.random.normal(0, 0.5)
            elif i % 90 == 0:
                # 温度异常
                temperature = base_temperature + 20.0 + np.random.normal(0, 2.0)
            
            data.append({
                'timestamp': f'2026-03-18T10:{i//60:02d}:{i%60:02d}',
                'pressure': max(0, round(pressure, 2)),
                'flow': max(0, round(flow, 2)),
                'temperature': max(0, round(temperature, 2)),
                'status': 'normal'
            })
        
        return data
