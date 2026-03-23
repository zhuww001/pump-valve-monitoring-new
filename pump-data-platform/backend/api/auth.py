from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import jwt
import datetime

# 创建路由器
auth_router = APIRouter(prefix="/auth", tags=["auth"])

# 模拟用户数据
users = [
    {"id": 1, "username": "admin", "password": "123456", "role": "superadmin"},
    {"id": 2, "username": "test", "password": "123456", "role": "user"}
]

# 密钥（实际项目中应该从配置文件读取）
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 请求模型
class LoginRequest(BaseModel):
    username: str
    password: str

# 响应模型
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

# 创建访问令牌
def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# 登录接口
@auth_router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest):
    """
    用户登录
    """
    # 查找用户
    user = next((u for u in users if u["username"] == login_data.username), None)
    if not user or user["password"] != login_data.password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 创建访问令牌
    access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires
    )
    
    # 返回令牌和用户信息
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"]
        }
    }

# 获取当前用户信息
@auth_router.get("/me")
def get_current_user():
    """
    获取当前用户信息
    """
    # 实际项目中应该从请求头中获取令牌并验证
    # 这里为了演示，直接返回模拟用户信息
    # 注意：在实际项目中，应该从token中解析用户信息
    return {
        "id": 1,
        "username": "admin",
        "role": "superadmin"
    }

# 注销接口
@auth_router.post("/logout")
def logout():
    """
    用户注销
    """
    # 实际项目中应该处理令牌失效逻辑
    return {"message": "注销成功"}
