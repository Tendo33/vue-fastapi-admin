from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException, Request

from app.core.ctx import CTX_USER_ID
from app.models import Role, User
from app.settings import settings


class AuthControl:
    """
    用于处理用户认证的逻辑。
    """

    @classmethod
    async def is_authed(cls, token: str = Header(..., description="token验证")) -> Optional["User"]:
        """
        验证用户的 Token，并返回对应的用户对象。
        参数:
            token: 用户提供的 Token，通过 Header 传递。
        返回:
            User: 用户对象，如果验证成功。
        异常:
            HTTPException: 如果 Token 无效、过期或其他错误，抛出 401 或 500 状态码的异常。
        """
        try:
            if token == "dev":  # 开发模式下，直接返回第一个用户
                user = await User.filter().first()
                user_id = user.id
            else:
                # 解码 Token，获取用户 ID
                decode_data = jwt.decode(token, settings.SECRET_KEY, algorithms=settings.JWT_ALGORITHM)
                user_id = decode_data.get("user_id")
            # 根据用户 ID 查询用户
            user = await User.filter(id=user_id).first()
            if not user:
                raise HTTPException(status_code=401, detail="Authentication failed")
            # 将用户 ID 设置到上下文
            CTX_USER_ID.set(int(user_id))
            return user
        except jwt.DecodeError:  # Token 解码失败
            raise HTTPException(status_code=401, detail="无效的Token")
        except jwt.ExpiredSignatureError:  # Token 过期
            raise HTTPException(status_code=401, detail="登录已过期")
        except Exception as e:  # 其他异常
            raise HTTPException(status_code=500, detail=f"{repr(e)}")


class PermissionControl:
    """
    用于处理用户权限验证的逻辑。
    """

    @classmethod
    async def has_permission(cls, request: Request, current_user: User = Depends(AuthControl.is_authed)) -> None:
        """
        验证当前用户是否具有访问当前路径的权限。
        参数:
            request: 请求对象，包含请求方法和路径。
            current_user: 当前用户对象，通过依赖注入获取。
        异常:
            HTTPException: 如果用户没有权限，抛出 403 状态码的异常。
        """
        if current_user.is_superuser:  # 超级用户拥有所有权限
            return
        method = request.method  # 请求方法
        path = request.url.path  # 请求路径
        roles: list[Role] = await current_user.roles  # 获取用户绑定的角色
        if not roles:  # 如果用户没有绑定角色
            raise HTTPException(status_code=403, detail="The user is not bound to a role")
        # 获取所有角色对应的 API 权限
        apis = [await role.apis for role in roles]
        # 去重，得到用户的所有权限 API
        permission_apis = list(set((api.method, api.path) for api in sum(apis, [])))
        # 检查当前请求是否在权限范围内
        if (method, path) not in permission_apis:
            raise HTTPException(status_code=403, detail=f"Permission denied method:{method} path:{path}")


# 依赖注入的快捷方式
DependAuth = Depends(AuthControl.is_authed)  # 用于依赖注入用户认证
DependPermisson = Depends(PermissionControl.has_permission)  # 用于依赖注入权限验证
