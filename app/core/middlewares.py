import json
import re
from datetime import datetime
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.dependency import AuthControl
from app.models.admin import AuditLog, User

from .bgtask import BgTasks


class SimpleBaseMiddleware:
    """
    这是一个基础的中间件类，提供了中间件的框架结构。
    """

    def __init__(self, app: ASGIApp) -> None:
        """
        初始化中间件，接收一个 ASGI 应用实例。
        参数:
            app: ASGI 应用实例。
        """
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        处理请求，根据请求类型决定是否执行前置和后置处理。
        参数:
            scope: 请求的作用域。
            receive: 接收请求的函数。
            send: 发送响应的函数。
        """
        if scope["type"] != "http":  # 如果请求类型不是HTTP，直接传递给下一个中间件或应用
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive=receive)

        response = await self.before_request(request) or self.app  # 执行前置处理
        await response(request.scope, request.receive, send)  # 继续处理请求
        await self.after_request(request)  # 执行后置处理

    async def before_request(self, request: Request):
        """
        前置处理逻辑，默认直接返回应用实例。
        """
        return self.app

    async def after_request(self, request: Request):
        """
        后置处理逻辑，默认不执行任何操作。
        """
        return None


class BackGroundTaskMiddleware(SimpleBaseMiddleware):
    """
    继承自 SimpleBaseMiddleware，用于处理后台任务。
    """

    async def before_request(self, request):
        """
        初始化后台任务对象。
        """
        await BgTasks.init_bg_tasks_obj()

    async def after_request(self, request):
        """
        执行后台任务。
        """
        await BgTasks.execute_tasks()


class HttpAuditLogMiddleware(BaseHTTPMiddleware):
    """
    继承自 BaseHTTPMiddleware，用于记录 HTTP 请求的审计日志。
    """

    def __init__(self, app, methods: list[str], exclude_paths: list[str]):
        """
        初始化中间件，设置需要记录日志的 HTTP 方法和不需要记录日志的路径。
        参数:
            app: ASGI 应用实例。
            methods: 需要记录日志的 HTTP 方法列表。
            exclude_paths: 不需要记录日志的路径列表。
        """
        super().__init__(app)
        self.methods = methods  # 需要记录日志的HTTP方法
        self.exclude_paths = exclude_paths  # 不需要记录日志的路径
        self.audit_log_paths = ["/api/v1/auditlog/list"]  # 需要特殊处理的审计日志路径
        self.max_body_size = 1024 * 1024  # 1MB 响应体大小限制

    async def get_request_args(self, request: Request) -> dict:
        """
        获取请求的查询参数和请求体。
        参数:
            request: 请求对象。
        返回:
            包含请求参数的字典。
        """
        args = {}
        # 获取查询参数
        for key, value in request.query_params.items():
            args[key] = value

        # 获取请求体
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.json()
                args.update(body)
            except json.JSONDecodeError:
                try:
                    body = await request.form()
                    args.update(body)
                except Exception:
                    pass

        return args

    async def get_response_body(self, request: Request, response: Response) -> Any:
        """
        获取响应体内容，并根据大小限制和路径规则处理。
        参数:
            request: 请求对象。
            response: 响应对象。
        返回:
            处理后的响应体内容。
        """
        # 检查Content-Length
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) > self.max_body_size:
            return {"code": 0, "msg": "Response too large to log", "data": None}

        if hasattr(response, "body"):
            body = response.body
        else:
            body_chunks = []
            async for chunk in response.body_iterator:
                if not isinstance(chunk, bytes):
                    chunk = chunk.encode(response.charset)
                body_chunks.append(chunk)

            response.body_iterator = self._async_iter(body_chunks)
            body = b"".join(body_chunks)

        if any(request.url.path.startswith(path) for path in self.audit_log_paths):
            try:
                data = self.lenient_json(body)
                # 只保留基本信息，去除详细的响应内容
                if isinstance(data, dict):
                    data.pop("response_body", None)
                    if "data" in data and isinstance(data["data"], list):
                        for item in data["data"]:
                            item.pop("response_body", None)
                return data
            except Exception:
                return None

        return self.lenient_json(body)

    def lenient_json(self, v: Any) -> Any:
        """
        尝试将字符串或字节转换为 JSON 对象，失败则返回原始值。
        参数:
            v: 需要转换的值。
        返回:
            JSON 对象或原始值。
        """
        if isinstance(v, (str, bytes)):
            try:
                return json.loads(v)
            except (ValueError, TypeError):
                pass
        return v

    async def _async_iter(self, items: list[bytes]) -> AsyncGenerator[bytes, None]:
        """
        异步迭代器，用于处理响应体的分块数据。
        参数:
            items: 字节列表。
        返回:
            异步生成器。
        """
        for item in items:
            yield item

    async def get_request_log(self, request: Request, response: Response) -> dict:
        """
        根据 request 和 response 对象获取对应的日志记录数据。
        参数:
            request: 请求对象。
            response: 响应对象。
        返回:
            包含日志数据的字典。
        """
        data: dict = {"path": request.url.path, "status": response.status_code, "method": request.method}
        # 路由信息
        app: FastAPI = request.app
        for route in app.routes:
            if (
                isinstance(route, APIRoute)
                and route.path_regex.match(request.url.path)
                and request.method in route.methods
            ):
                data["module"] = ",".join(route.tags)
                data["summary"] = route.summary
        # 获取用户信息
        try:
            token = request.headers.get("token")
            user_obj = None
            if token:
                user_obj: User = await AuthControl.is_authed(token)
            data["user_id"] = user_obj.id if user_obj else 0
            data["username"] = user_obj.username if user_obj else ""
        except Exception:
            data["user_id"] = 0
            data["username"] = ""
        return data

    async def before_request(self, request: Request):
        """
        前置处理逻辑，获取请求参数并存储在 request.state 中。
        参数:
            request: 请求对象。
        """
        request_args = await self.get_request_args(request)
        request.state.request_args = request_args  # 将请求参数存储在request.state中

    async def after_request(self, request: Request, response: Response, process_time: int):
        """
        后置处理逻辑，根据规则记录审计日志。
        参数:
            request: 请求对象。
            response: 响应对象。
            process_time: 请求处理时间。
        返回:
            响应对象。
        """
        if request.method in self.methods:
            for path in self.exclude_paths:
                if re.search(path, request.url.path, re.I) is not None:
                    return
            data: dict = await self.get_request_log(request=request, response=response)
            data["response_time"] = process_time

            data["request_args"] = request.state.request_args
            data["response_body"] = await self.get_response_body(request, response)
            await AuditLog.create(**data)  # 创建审计日志记录

        return response

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        中间件的核心方法，处理请求并记录审计日志。
        参数:
            request: 请求对象。
            call_next: 调用下一个中间件或应用的函数。
        返回:
            响应对象。
        """
        start_time: datetime = datetime.now()
        await self.before_request(request)
        response = await call_next(request)
        end_time: datetime = datetime.now()
        process_time = int((end_time.timestamp() - start_time.timestamp()) * 1000)  # 计算处理时间
        await self.after_request(request, response, process_time)
        return response
