import jwt  # 导入用于创建和验证 JWT 的库

from app.schemas.login import JWTPayload  # 导入 JWT 有效载荷的结构定义
from app.settings.config import settings  # 导入应用程序的配置参数


# 定义一个函数用于创建访问令牌，接收一个 JWTPayload 类型的数据
def create_access_token(*, data: JWTPayload):
    # 将数据模型转换为字典并复制，以便后续操作
    payload = data.model_dump().copy()

    # 使用指定的密钥和算法对有效载荷进行编码，生成 JWT
    encoded_jwt = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    # 返回生成的 JWT 字符串
    return encoded_jwt
