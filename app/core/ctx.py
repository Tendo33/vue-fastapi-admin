import contextvars

from starlette.background import BackgroundTasks

# 这个变量可以用于在异步请求处理过程中存储和传递当前用户的 ID。例如，你可以在请求开始时设置用户 ID，然后在请求的各个部分（如中间件、路由处理函数等）中访问它。
CTX_USER_ID: contextvars.ContextVar[int] = contextvars.ContextVar("user_id", default=0)

# 这个变量可以用于在请求处理过程中收集后台任务。例如，你可以在请求的不同部分添加后台任务，然后在请求结束时统一执行这些任务。
CTX_BG_TASKS: contextvars.ContextVar[BackgroundTasks] = contextvars.ContextVar("bg_task", default=None)
