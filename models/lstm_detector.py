import numpy as np

class LSTMAnomalyDetector:
    def __init__(self):
        # 简单的模拟实现，避免依赖TensorFlow
        pass
    
    def detect_anomaly(self, recent_data):
        """使用简单的统计方法检测异常"""
        if len(recent_data) < 5:
            return False, 0.0
        
        # 提取压力和流量数据
        pressures = [data.get('pressure', 0) for data in recent_data[-5:]]
        flows = [data.get('flow', 0) for data in recent_data[-5:]]
        
        # 计算平均值和标准差
        mean_pressure = np.mean(pressures)
        mean_flow = np.mean(flows)
        std_pressure = np.std(pressures) if len(pressures) > 1 else 0.01
        std_flow = np.std(flows) if len(flows) > 1 else 0.01
        
        # 获取当前值
        current_pressure = recent_data[-1].get('pressure', 0)
        current_flow = recent_data[-1].get('flow', 0)
        
        # 计算Z-score
        z_score_pressure = abs(current_pressure - mean_pressure) / std_pressure
        z_score_flow = abs(current_flow - mean_flow) / std_flow
        
        # 设定阈值
        threshold = 2.0  # Z-score大于2.0视为异常
        is_anomaly = z_score_pressure > threshold or z_score_flow > threshold
        
        # 计算异常置信度
        confidence = max(z_score_pressure, z_score_flow) / threshold
        
        return is_anomaly, confidence
