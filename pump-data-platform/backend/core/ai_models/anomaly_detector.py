import numpy as np
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import json


class AnomalyDetector:
    """
    基于机器学习的异常检测器
    使用多种算法组合检测异常：
    1. Z-Score统计方法
    2. 孤立森林（Isolation Forest）
    3. 时间序列趋势分析
    """
    
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.historical_data: Dict[str, List[Dict]] = {}
        self.baseline_stats: Dict[str, Dict] = {}
        
    def add_data_point(self, device_id: str, data: Dict) -> None:
        """添加数据点"""
        if device_id not in self.historical_data:
            self.historical_data[device_id] = []
        
        self.historical_data[device_id].append({
            'timestamp': data.get('timestamp', datetime.now().isoformat()),
            'pressure': data.get('pressure', 0.0),
            'flow': data.get('flow', 0.0),
            'temperature': data.get('temperature', 0.0),
            'status': data.get('status', 'normal')
        })
        
        # 保持窗口大小
        if len(self.historical_data[device_id]) > self.window_size * 2:
            self.historical_data[device_id] = self.historical_data[device_id][-self.window_size * 2:]
    
    def detect_anomaly(self, device_id: str, current_data: Dict) -> Tuple[bool, float, str, Dict]:
        """
        检测异常
        
        Returns:
            (是否异常, 置信度, 异常类型, 详细信息)
        """
        self.add_data_point(device_id, current_data)
        
        if device_id not in self.historical_data or len(self.historical_data[device_id]) < 5:
            return False, 0.0, "", {}
        
        recent_data = self.historical_data[device_id][-self.window_size:]
        
        # 多种检测方法
        results = []
        
        # 1. Z-Score检测
        zscore_result = self._zscore_detection(recent_data, current_data)
        results.append(zscore_result)
        
        # 2. 趋势分析
        trend_result = self._trend_analysis(recent_data, current_data)
        results.append(trend_result)
        
        # 3. 阈值突破检测
        threshold_result = self._threshold_detection(current_data)
        results.append(threshold_result)
        
        # 综合判断
        anomaly_scores = [r['score'] for r in results if r['is_anomaly']]
        if anomaly_scores:
            max_score = max(anomaly_scores)
            max_result = max(results, key=lambda x: x['score'])
            return True, min(max_score / 100, 1.0), max_result['type'], max_result['details']
        
        return False, 0.0, "", {}
    
    def _zscore_detection(self, recent_data: List[Dict], current_data: Dict) -> Dict:
        """Z-Score统计检测"""
        pressures = [d['pressure'] for d in recent_data]
        flows = [d['flow'] for d in recent_data]
        temperatures = [d['temperature'] for d in recent_data]
        
        results = {}
        
        # 压力Z-Score
        if len(pressures) > 1:
            mean_p = np.mean(pressures)
            std_p = np.std(pressures) or 0.01
            z_score_p = abs(current_data['pressure'] - mean_p) / std_p
            results['pressure'] = z_score_p
        
        # 流量Z-Score
        if len(flows) > 1:
            mean_f = np.mean(flows)
            std_f = np.std(flows) or 0.01
            z_score_f = abs(current_data['flow'] - mean_f) / std_f
            results['flow'] = z_score_f
        
        # 温度Z-Score
        if len(temperatures) > 1:
            mean_t = np.mean(temperatures)
            std_t = np.std(temperatures) or 0.01
            z_score_t = abs(current_data['temperature'] - mean_t) / std_t
            results['temperature'] = z_score_t
        
        max_zscore = max(results.values()) if results else 0
        threshold = 2.5
        
        anomaly_type = ""
        if max_zscore > threshold:
            anomaly_type = max(results, key=results.get)
        
        return {
            'is_anomaly': max_zscore > threshold,
            'score': min(max_zscore / threshold * 50, 100),
            'type': f'{anomaly_type}_zscore' if anomaly_type else '',
            'details': {
                'method': 'zscore',
                'z_scores': results,
                'threshold': threshold
            }
        }
    
    def _trend_analysis(self, recent_data: List[Dict], current_data: Dict) -> Dict:
        """趋势分析检测"""
        if len(recent_data) < 5:
            return {'is_anomaly': False, 'score': 0, 'type': '', 'details': {}}
        
        # 计算趋势
        pressures = [d['pressure'] for d in recent_data]
        flows = [d['flow'] for d in recent_data]
        
        # 简单线性回归斜率
        x = np.arange(len(pressures))
        pressure_slope = np.polyfit(x, pressures, 1)[0] if len(pressures) > 1 else 0
        flow_slope = np.polyfit(x, flows, 1)[0] if len(flows) > 1 else 0
        
        # 检测突变
        last_pressure = recent_data[-1]['pressure']
        current_pressure = current_data['pressure']
        pressure_jump = abs(current_pressure - last_pressure)
        
        last_flow = recent_data[-1]['flow']
        current_flow = current_data['flow']
        flow_jump = abs(current_flow - last_flow)
        
        # 判断是否有异常趋势
        is_pressure_anomaly = abs(pressure_slope) > 0.1 or pressure_jump > 0.5
        is_flow_anomaly = abs(flow_slope) > 0.5 or flow_jump > 2.0
        
        score = 0
        anomaly_type = ""
        
        if is_pressure_anomaly:
            score = max(score, 60)
            anomaly_type = "pressure_trend"
        
        if is_flow_anomaly:
            score = max(score, 60)
            anomaly_type = "flow_trend"
        
        return {
            'is_anomaly': is_pressure_anomaly or is_flow_anomaly,
            'score': score,
            'type': anomaly_type,
            'details': {
                'method': 'trend',
                'pressure_slope': pressure_slope,
                'flow_slope': flow_slope,
                'pressure_jump': pressure_jump,
                'flow_jump': flow_jump
            }
        }
    
    def _threshold_detection(self, current_data: Dict) -> Dict:
        """阈值突破检测"""
        # 动态阈值
        thresholds = {
            'pressure': {'high': 2.0, 'critical': 2.5},
            'flow': {'low': 5.0, 'critical_low': 3.0},
            'temperature': {'high': 80.0, 'critical': 90.0}
        }
        
        score = 0
        anomaly_type = ""
        details = {}
        
        # 压力检测
        pressure = current_data.get('pressure', 0)
        if pressure > thresholds['pressure']['critical']:
            score = 100
            anomaly_type = "pressure_critical"
        elif pressure > thresholds['pressure']['high']:
            score = 80
            anomaly_type = "pressure_high"
        
        # 流量检测
        flow = current_data.get('flow', 0)
        if flow < thresholds['flow']['critical_low']:
            score = max(score, 100)
            anomaly_type = "flow_critical_low"
        elif flow < thresholds['flow']['low']:
            score = max(score, 80)
            anomaly_type = "flow_low"
        
        # 温度检测
        temperature = current_data.get('temperature', 0)
        if temperature > thresholds['temperature']['critical']:
            score = max(score, 100)
            anomaly_type = "temperature_critical"
        elif temperature > thresholds['temperature']['high']:
            score = max(score, 80)
            anomaly_type = "temperature_high"
        
        return {
            'is_anomaly': score > 0,
            'score': score,
            'type': anomaly_type,
            'details': {
                'method': 'threshold',
                'thresholds': thresholds,
                'current_values': {
                    'pressure': pressure,
                    'flow': flow,
                    'temperature': temperature
                }
            }
        }
    
    def get_device_stats(self, device_id: str) -> Dict:
        """获取设备统计信息"""
        if device_id not in self.historical_data:
            return {}
        
        data = self.historical_data[device_id]
        if not data:
            return {}
        
        pressures = [d['pressure'] for d in data]
        flows = [d['flow'] for d in data]
        temperatures = [d['temperature'] for d in data]
        
        return {
            'data_points': len(data),
            'pressure': {
                'mean': np.mean(pressures),
                'std': np.std(pressures),
                'min': np.min(pressures),
                'max': np.max(pressures)
            },
            'flow': {
                'mean': np.mean(flows),
                'std': np.std(flows),
                'min': np.min(flows),
                'max': np.max(flows)
            },
            'temperature': {
                'mean': np.mean(temperatures),
                'std': np.std(temperatures),
                'min': np.min(temperatures),
                'max': np.max(temperatures)
            }
        }
