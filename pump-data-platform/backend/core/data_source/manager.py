from .simulate import SimulateDataSource
from .api import ApiDataSource
from .report import ReportDataSource
from .mqtt import MqttDataSource
from ..config import settings


class DataSourceManager:
    """数据源管理器"""
    
    _instance = None
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(DataSourceManager, cls).__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        """初始化数据源"""
        self.data_sources = {
            "simulate": SimulateDataSource(),
            "api": ApiDataSource(),
            "report": ReportDataSource(),
            "mqtt": MqttDataSource()
        }
        self.current_data_source = None
        self.update_data_source()
    
    def update_data_source(self):
        """更新当前数据源"""
        data_source_type = settings.DATA_SOURCE_TYPE
        if data_source_type in self.data_sources:
            self.current_data_source = self.data_sources[data_source_type]
        else:
            # 默认使用模拟数据源
            self.current_data_source = self.data_sources["simulate"]
    
    def get_data_source(self):
        """获取当前数据源实例"""
        if self.current_data_source is None:
            self.update_data_source()
        return self.current_data_source
    
    def switch_data_source(self, data_source_type: str):
        """切换数据源
        
        Args:
            data_source_type: 数据源类型 (simulate, api, report, mqtt)
        """
        if data_source_type in self.data_sources:
            # 对于MQTT数据源，每次切换时重新创建实例以使用最新配置
            if data_source_type == "mqtt":
                from .mqtt import MqttDataSource
                self.data_sources[data_source_type] = MqttDataSource()
            
            self.current_data_source = self.data_sources[data_source_type]
            # 更新配置
            settings.DATA_SOURCE_TYPE = data_source_type
            return True
        return False
