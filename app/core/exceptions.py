from fastapi.exceptions import (
    HTTPException,
    RequestValidationError,
    ResponseValidationError,
)
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from tortoise.exceptions import DoesNotExist, IntegrityError


class SettingNotFound(Exception):
    """
    自定义异常类，用于表示设置未找到的情况。
    """

    pass


async def DoesNotExistHandle(req: Request, exc: DoesNotExist) -> JSONResponse:
    """
    处理 DoesNotExist 异常，返回 404 状态码和错误信息。
    参数:
        req: 请求对象。
        exc: DoesNotExist 异常实例。
    返回:
        JSONResponse: 包含错误信息的 JSON 响应。
    """
    content = dict(
        code=404,
        msg=f"Object has not found, exc: {exc}, query_params: {req.query_params}",
    )
    return JSONResponse(content=content, status_code=404)


async def IntegrityHandle(_: Request, exc: IntegrityError) -> JSONResponse:
    """
    处理 IntegrityError 异常，返回 500 状态码和错误信息。
    参数:
        _: 请求对象（未使用）。
        exc: IntegrityError 异常实例。
    返回:
        JSONResponse: 包含错误信息的 JSON 响应。
    """
    content = dict(
        code=500,
        msg=f"IntegrityError，{exc}",
    )
    return JSONResponse(content=content, status_code=500)


async def HttpExcHandle(_: Request, exc: HTTPException) -> JSONResponse:
    """
    处理 HTTPException 异常，返回对应的状态码和错误信息。
    参数:
        _: 请求对象（未使用）。
        exc: HTTPException 异常实例。
    返回:
        JSONResponse: 包含错误信息的 JSON 响应。
    """
    content = dict(code=exc.status_code, msg=exc.detail, data=None)
    return JSONResponse(content=content, status_code=exc.status_code)


async def RequestValidationHandle(_: Request, exc: RequestValidationError) -> JSONResponse:
    """
    处理 RequestValidationError 异常，返回 422 状态码和错误信息。
    参数:
        _: 请求对象（未使用）。
        exc: RequestValidationError 异常实例。
    返回:
        JSONResponse: 包含错误信息的 JSON 响应。
    """
    content = dict(code=422, msg=f"RequestValidationError, {exc}")
    return JSONResponse(content=content, status_code=422)


async def ResponseValidationHandle(_: Request, exc: ResponseValidationError) -> JSONResponse:
    """
    处理 ResponseValidationError 异常，返回 500 状态码和错误信息。
    参数:
        _: 请求对象（未使用）。
        exc: ResponseValidationError 异常实例。
    返回:
        JSONResponse: 包含错误信息的 JSON 响应。
    """
    content = dict(code=500, msg=f"ResponseValidationError, {exc}")
    return JSONResponse(content=content, status_code=500)
