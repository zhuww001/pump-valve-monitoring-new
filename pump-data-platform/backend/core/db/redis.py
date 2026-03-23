from ..config import settings

# 创建Redis客户端
redis_client = None

# 模拟Redis客户端类
class MockRedis:
    def __init__(self):
        self.data = {}
    
    def get(self, key):
        return self.data.get(key)
    
    def setex(self, key, expire, value):
        self.data[key] = value
    
    def close(self):
        pass


def init_redis_client():
    """初始化Redis客户端"""
    global redis_client
    if not settings.LOCAL_MODE:
        import redis
        redis_kwargs = {
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT,
            "decode_responses": True
        }
        if settings.REDIS_PASSWORD is not None:
            redis_kwargs["password"] = settings.REDIS_PASSWORD
        redis_client = redis.Redis(**redis_kwargs)

def get_redis_client():
    """获取Redis客户端"""
    # 本地运行模式下返回模拟客户端
    if settings.LOCAL_MODE:
        return MockRedis()
    
    global redis_client
    if redis_client is None:
        init_redis_client()
    return redis_client
