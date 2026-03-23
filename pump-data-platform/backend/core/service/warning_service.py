from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
import random
from ..db import get_postgres_connection, release_postgres_connection
from ..config import settings
from ..ai_models.anomaly_detector import AnomalyDetector
from ..ai_models.warning_predictor import WarningPredictor


class WarningService:
    """预警管理服务 - 基于AI模型"""
    
    # AI模型实例（单例模式）
    _anomaly_detector: Optional[AnomalyDetector] = None
    _warning_predictor: Optional[WarningPredictor] = None
    
    # 内存存储预警记录（本地开发模式使用）
    _warning_cache: List[Dict] = []
    _warning_id_counter: int = 1
    
    @classmethod
    def initialize_warning_cache(cls):
        """初始化本地开发模式的预警缓存"""
        if not cls._warning_cache:
            # 生成模拟预警数据
            import random
            from datetime import datetime, timedelta
            
            # 模拟设备ID
            device_ids = [f"Device-{i}" for i in range(1, 6)]
            
            # 预警类型
            warning_types = ['pressure', 'flow', 'temperature']
            
            # 生成10条模拟预警记录
            for i in range(10):
                device_id = random.choice(device_ids)
                warning_type = random.choice(warning_types)
                
                # 生成随机预警值（超过阈值）
                if warning_type == 'pressure':
                    warning_value = round(random.uniform(2.1, 3.0), 2)
                    threshold = 2.0
                elif warning_type == 'flow':
                    warning_value = round(random.uniform(5.1, 8.0), 2)
                    threshold = 5.0
                else:  # temperature
                    warning_value = round(random.uniform(81.0, 100.0), 2)
                    threshold = 80.0
                
                # 随机状态
                status = random.choice(['unprocessed', 'processed'])
                
                # 随机时间
                time_offset = random.randint(0, 24 * 60 * 60)  # 0-24小时
                created_at = (datetime.now() - timedelta(seconds=time_offset)).isoformat()
                
                warning_record = {
                    "id": cls._warning_id_counter,
                    "device_id": device_id,
                    "warning_type": warning_type,
                    "warning_value": warning_value,
                    "threshold": threshold,
                    "status": status,
                    "created_at": created_at,
                    "updated_at": created_at
                }
                
                cls._warning_cache.append(warning_record)
                cls._warning_id_counter += 1
            
            # 按时间倒序排序
            cls._warning_cache.sort(key=lambda x: x['created_at'], reverse=True)
            print(f"初始化预警缓存完成，生成了 {len(cls._warning_cache)} 条模拟预警记录")
    
    @classmethod
    def get_anomaly_detector(cls) -> AnomalyDetector:
        """获取异常检测器实例"""
        if cls._anomaly_detector is None:
            cls._anomaly_detector = AnomalyDetector(window_size=10)
        return cls._anomaly_detector
    
    @classmethod
    def get_warning_predictor(cls) -> WarningPredictor:
        """获取预警预测器实例"""
        if cls._warning_predictor is None:
            cls._warning_predictor = WarningPredictor(prediction_horizon=5)
        return cls._warning_predictor
    
    @staticmethod
    def get_warning_list(page: int = 1, page_size: int = 10, device_id: str = None) -> List[Dict]:
        """获取预警列表，支持按设备ID筛选"""
        # 本地开发模式下返回内存中的预警记录
        if settings.LOCAL_MODE:
            # 初始化预警缓存
            WarningService.initialize_warning_cache()
            filtered_cache = WarningService._warning_cache
            if device_id:
                filtered_cache = [w for w in filtered_cache if w.get('device_id') == device_id]
            start = (page - 1) * page_size
            end = start + page_size
            return filtered_cache[start:end]
        
        # 尝试从数据库获取
        try:
            conn = get_postgres_connection()
            cursor = conn.cursor()
            
            # 计算偏移量
            offset = (page - 1) * page_size
            
            # 查询预警列表，支持设备ID筛选
            if device_id:
                query = "SELECT * FROM warning_record WHERE device_id = %s ORDER BY created_at DESC LIMIT %s OFFSET %s"
                cursor.execute(query, (device_id, page_size, offset))
            else:
                query = "SELECT * FROM warning_record ORDER BY created_at DESC LIMIT %s OFFSET %s"
                cursor.execute(query, (page_size, offset))
            
            # 处理结果
            db_warnings = []
            for row in cursor.fetchall():
                db_warnings.append({
                    "id": row[0],
                    "device_id": row[1],
                    "warning_type": row[2],
                    "warning_value": row[3],
                    "threshold": row[4],
                    "status": row[5],
                    "created_at": row[6].isoformat(),
                    "updated_at": row[7].isoformat()
                })
            
            cursor.close()
            release_postgres_connection(conn)
            if db_warnings:
                return db_warnings
        except Exception as e:
            print(f"从数据库获取预警列表失败: {e}")
            if 'conn' in locals():
                release_postgres_connection(conn)
        
        # 如果没有数据，返回空列表
        return []
    
    @staticmethod
    def get_warning_count(device_id: str = None) -> int:
        """获取预警记录总数，支持按设备ID筛选"""
        # 本地开发模式下返回内存中的预警记录数量
        if settings.LOCAL_MODE:
            # 初始化预警缓存
            WarningService.initialize_warning_cache()
            if device_id:
                return len([w for w in WarningService._warning_cache if w.get('device_id') == device_id])
            return len(WarningService._warning_cache)
        
        # 尝试从数据库获取
        try:
            conn = get_postgres_connection()
            cursor = conn.cursor()
            
            # 查询预警记录总数，支持设备ID筛选
            if device_id:
                query = "SELECT COUNT(*) FROM warning_record WHERE device_id = %s"
                cursor.execute(query, (device_id,))
            else:
                query = "SELECT COUNT(*) FROM warning_record"
                cursor.execute(query)
            
            # 处理结果
            count = cursor.fetchone()[0]
            
            cursor.close()
            release_postgres_connection(conn)
            return count
        except Exception as e:
            print(f"获取预警记录总数失败: {e}")
            if 'conn' in locals():
                release_postgres_connection(conn)
        
        # 如果获取失败，返回0
        return 0
    
    @staticmethod
    def check_warning_with_ai(device_id: str, data: Dict) -> Tuple[bool, float, str, Dict]:
        """
        使用AI模型检测预警
        
        Returns:
            (是否预警, 置信度, 预警类型, 详细信息)
        """
        detector = WarningService.get_anomaly_detector()
        
        # 使用AI模型检测异常
        is_anomaly, confidence, warning_type, details = detector.detect_anomaly(device_id, data)
        
        return is_anomaly, confidence, warning_type, details
    
    @staticmethod
    def predict_warning_with_ai(device_id: str, data: Dict) -> Tuple[bool, float, str, Dict]:
        """
        使用AI模型预测未来预警
        
        Returns:
            (是否预测预警, 置信度, 预警类型, 详细信息)
        """
        predictor = WarningService.get_warning_predictor()
        
        # 使用AI模型预测
        will_warn, confidence, warning_type, details = predictor.predict_warning(device_id, data)
        
        return will_warn, confidence, warning_type, details
    
    @staticmethod
    def process_data_and_check_warning(device_id: str, data: Dict) -> Optional[Dict]:
        """
        处理数据并检查是否需要生成预警
        
        Returns:
            预警记录字典，如果没有预警则返回None
        """
        # 使用AI模型检测
        is_anomaly, confidence, warning_type, details = WarningService.check_warning_with_ai(device_id, data)
        
        if not is_anomaly or confidence < 0.5:
            return None
        
        # 解析预警类型
        warning_category = warning_type.split('_')[0] if '_' in warning_type else warning_type
        
        # 获取阈值
        threshold_map = {
            'pressure': settings.PRESSURE_THRESHOLD,
            'flow': settings.FLOW_THRESHOLD,
            'temperature': settings.TEMPERATURE_THRESHOLD
        }
        threshold = threshold_map.get(warning_category, 0)
        
        # 获取当前值
        value_map = {
            'pressure': data.get('pressure', 0),
            'flow': data.get('flow', 0),
            'temperature': data.get('temperature', 0)
        }
        warning_value = value_map.get(warning_category, 0)
        
        # 创建预警记录
        warning_record = {
            "device_id": device_id,
            "warning_type": warning_category,
            "warning_value": warning_value,
            "threshold": threshold,
            "status": "unprocessed",
            "ai_confidence": confidence,
            "ai_details": details,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # 存储到数据库
        if not settings.LOCAL_MODE:
            try:
                WarningService._save_warning_to_db(warning_record)
            except Exception as e:
                print(f"保存预警到数据库失败: {e}")
        else:
            # 本地开发模式下存储到内存
            warning_record['id'] = WarningService._warning_id_counter
            WarningService._warning_id_counter += 1
            WarningService._warning_cache.append(warning_record)
            # 限制内存缓存大小
            if len(WarningService._warning_cache) > 100:
                WarningService._warning_cache = WarningService._warning_cache[-100:]
        
        return warning_record
    
    @staticmethod
    def _save_warning_to_db(warning: Dict) -> bool:
        """保存预警到数据库"""
        try:
            conn = get_postgres_connection()
            cursor = conn.cursor()
            
            # 插入预警记录
            query = """
                INSERT INTO warning_record 
                (device_id, warning_type, warning_value, threshold, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            """
            
            cursor.execute(query, (
                warning['device_id'],
                warning['warning_type'],
                warning['warning_value'],
                warning['threshold'],
                warning['status']
            ))
            
            conn.commit()
            cursor.close()
            release_postgres_connection(conn)
            return True
        except Exception as e:
            print(f"保存预警失败: {e}")
            if 'conn' in locals():
                release_postgres_connection(conn)
            return False
    
    @staticmethod
    def update_warning_status(warning_id: int, status: str) -> bool:
        """更新预警状态"""
        # 本地运行模式下直接返回成功
        if settings.LOCAL_MODE:
            return True
        
        try:
            conn = get_postgres_connection()
            cursor = conn.cursor()
            
            # 更新状态
            query = """
                UPDATE warning_record SET 
                    status = %s, 
                    updated_at = NOW()
                WHERE id = %s
            """
            
            cursor.execute(query, (status, warning_id))
            
            conn.commit()
            cursor.close()
            release_postgres_connection(conn)
            return True
        except Exception as e:
            print(f"更新预警状态失败: {e}")
            if 'conn' in locals():
                release_postgres_connection(conn)
            return False
    
    @staticmethod
    def get_ai_stats(device_id: str) -> Dict:
        """获取AI模型统计信息"""
        detector = WarningService.get_anomaly_detector()
        predictor = WarningService.get_warning_predictor()
        
        return {
            "anomaly_detection": detector.get_device_stats(device_id),
            "prediction": predictor.get_prediction_stats(device_id)
        }
