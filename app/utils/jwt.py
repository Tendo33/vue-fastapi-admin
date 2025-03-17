import jwt  # 导入用于创建和验证 JWT 的库

from app.schemas.login import JWTPayload  # 导入 JWT 有效载荷的结构定义
from app.settings.config import settings  # 导入应用程序的配置参数


def create_access_token(*, data: JWTPayload):
    # 定义一个函数用于创建访问令牌，接收一个 JWTPayload 类型的数据
    payload = data.model_dump().copy()
    # 将数据模型转换为字典并复制，以便后续操作

    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    # 使用指定的密钥和算法对有效载荷进行编码，生成 JWT

    return encoded_jwt
    # 返回生成的 JWT 字符串
