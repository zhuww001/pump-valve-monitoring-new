import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import json


class WarningPredictor:
    """
    基于AI的预警预测器
    使用历史数据训练模型，预测未来可能的预警
    """
    
    def __init__(self, prediction_horizon: int = 5):
        """
        Args:
            prediction_horizon: 预测未来多少个时间步（默认5步，约25秒）
        """
        self.prediction_horizon = prediction_horizon
        self.device_models: Dict[str, Dict] = {}
        self.historical_data: Dict[str, List[Dict]] = {}
        
    def add_training_data(self, device_id: str, data: Dict) -> None:
        """添加训练数据"""
        if device_id not in self.historical_data:
            self.historical_data[device_id] = []
        
        self.historical_data[device_id].append({
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'pressure': data.get('pressure', 0.0),
            'flow': data.get('flow', 0.0),
            'temperature': data.get('temperature', 0.0),
            'status': data.get('status', 'normal')
        })
        
        # 保持最多1000条历史数据
        if len(self.historical_data[device_id]) > 1000:
            self.historical_data[device_id] = self.historical_data[device_id][-1000:]
    
    def predict_warning(self, device_id: str, current_data: Dict) -> Tuple[bool, float, str, Dict]:
        """
        预测未来是否会发生预警
        
        Returns:
            (是否预测预警, 置信度, 预警类型, 详细信息)
        """
        self.add_training_data(device_id, current_data)
        
        if device_id not in self.historical_data or len(self.historical_data[device_id]) < 10:
            return False, 0.0, "", {}
        
        recent_data = self.historical_data[device_id][-20:]
        
        # 使用简单的时间序列预测（移动平均 + 趋势）
        predictions = self._predict_future_values(recent_data)
        
        # 检查预测值是否会触发预警
        warning_check = self._check_predicted_warnings(predictions)
        
        return warning_check
    
    def _predict_future_values(self, recent_data: List[Dict]) -> Dict[str, List[float]]:
        """预测未来值"""
        pressures = [d['pressure'] for d in recent_data]
        flows = [d['flow'] for d in recent_data]
        temperatures = [d['temperature'] for d in recent_data]
        
        predictions = {
            'pressure': [],
            'flow': [],
            'temperature': []
        }
        
        # 使用加权移动平均 + 趋势
        for i in range(self.prediction_horizon):
            # 压力预测
            pressure_pred = self._weighted_prediction(pressures, i)
            predictions['pressure'].append(pressure_pred)
            pressures.append(pressure_pred)
            
            # 流量预测
            flow_pred = self._weighted_prediction(flows, i)
            predictions['flow'].append(flow_pred)
            flows.append(flow_pred)
            
            # 温度预测
            temp_pred = self._weighted_prediction(temperatures, i)
            predictions['temperature'].append(temp_pred)
            temperatures.append(temp_pred)
        
        return predictions
    
    def _weighted_prediction(self, values: List[float], step: int) -> float:
        """加权预测"""
        if len(values) < 3:
            return values[-1] if values else 0.0
        
        # 最近的数据权重更高
        weights = np.exp(np.linspace(-1, 0, len(values)))
        weights /= weights.sum()
        
        weighted_mean = np.sum(np.array(values) * weights)
        
        # 添加趋势
        if len(values) >= 5:
            trend = (values[-1] - values[-5]) / 5
            weighted_mean += trend * (step + 1)
        
        return round(weighted_mean, 2)
    
    def _check_predicted_warnings(self, predictions: Dict[str, List[float]]) -> Tuple[bool, float, str, Dict]:
        """检查预测值是否会触发预警"""
        thresholds = {
            'pressure': {'high': 2.0, 'critical': 2.5},
            'flow': {'low': 5.0, 'critical_low': 3.0},
            'temperature': {'high': 80.0, 'critical': 90.0}
        }
        
        max_confidence = 0.0
        warning_type = ""
        warning_step = -1
        
        # 检查压力
        for i, pressure in enumerate(predictions['pressure']):
            if pressure > thresholds['pressure']['critical']:
                confidence = 0.9 - i * 0.1
                if confidence > max_confidence:
                    max_confidence = confidence
                    warning_type = "pressure_critical"
                    warning_step = i
            elif pressure > thresholds['pressure']['high']:
                confidence = 0.7 - i * 0.1
                if confidence > max_confidence:
                    max_confidence = confidence
                    warning_type = "pressure_high"
                    warning_step = i
        
        # 检查流量
        for i, flow in enumerate(predictions['flow']):
            if flow < thresholds['flow']['critical_low']:
                confidence = 0.9 - i * 0.1
                if confidence > max_confidence:
                    max_confidence = confidence
                    warning_type = "flow_critical_low"
                    warning_step = i
            elif flow < thresholds['flow']['low']:
                confidence = 0.7 - i * 0.1
                if confidence > max_confidence:
                    max_confidence = confidence
                    warning_type = "flow_low"
                    warning_step = i
        
        # 检查温度
        for i, temp in enumerate(predictions['temperature']):
            if temp > thresholds['temperature']['critical']:
                confidence = 0.9 - i * 0.1
                if confidence > max_confidence:
                    max_confidence = confidence
                    warning_type = "temperature_critical"
                    warning_step = i
            elif temp > thresholds['temperature']['high']:
                confidence = 0.7 - i * 0.1
                if confidence > max_confidence:
                    max_confidence = confidence
                    warning_type = "temperature_high"
                    warning_step = i
        
        time_to_warning = warning_step * 5 if warning_step >= 0 else None  # 假设每5秒一个数据点
        
        return (
            max_confidence > 0,
            max_confidence,
            warning_type,
            {
                'predicted_values': predictions,
                'time_to_warning_seconds': time_to_warning,
                'warning_step': warning_step,
                'thresholds': thresholds
            }
        )
    
    def get_prediction_stats(self, device_id: str) -> Dict:
        """获取预测统计信息"""
        if device_id not in self.historical_data:
            return {}
        
        data = self.historical_data[device_id]
        if len(data) < 10:
            return {'status': 'insufficient_data', 'message': '需要更多数据才能进行预测'}
        
        # 计算数据质量
        normal_count = sum(1 for d in data if d['status'] == 'normal')
        warning_count = len(data) - normal_count
        
        return {
            'status': 'ready',
            'total_data_points': len(data),
            'normal_count': normal_count,
            'warning_count': warning_count,
            'warning_ratio': warning_count / len(data) if data else 0,
            'prediction_horizon': self.prediction_horizon,
            'time_window_seconds': len(data) * 5  # 假设每5秒一个数据点
        }
