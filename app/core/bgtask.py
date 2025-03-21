from starlette.background import BackgroundTasks

from .ctx import CTX_BG_TASKS


class BgTasks:
    """
    后台任务统一管理类，用于在请求处理过程中添加和执行后台任务。
    """

    @classmethod
    async def init_bg_tasks_obj(cls):
        """
        实例化后台任务对象，并将其设置到上下文。
        作用:
            - 在请求开始时，初始化一个 BackgroundTasks 实例。
            - 将该实例存储到上下文（CTX_BG_TASKS）中，以便在请求处理过程中使用。
        """
        bg_tasks = BackgroundTasks()  # 实例化 BackgroundTasks
        CTX_BG_TASKS.set(bg_tasks)  # 将实例设置到上下文

    @classmethod
    async def get_bg_tasks_obj(cls):
        """
        从上下文中获取后台任务实例。
        返回:
            BackgroundTasks: 后台任务实例。
        """
        return CTX_BG_TASKS.get()

    @classmethod
    async def add_task(cls, func, *args, **kwargs):
        """
        添加后台任务。
        参数:
            func: 需要执行的函数。
            *args: 函数的参数。
            **kwargs: 函数的关键字参数。
        作用:
            - 将任务添加到后台任务队列中，等待执行。
        """
        bg_tasks = await cls.get_bg_tasks_obj()  # 从上下文中获取后台任务实例
        bg_tasks.add_task(func, *args, **kwargs)  # 添加任务到后台任务队列

    @classmethod
    async def execute_tasks(cls):
        """
        执行后台任务，通常在请求结果返回之后执行。
        作用:
            - 执行所有已添加到后台任务队列中的任务。
        """
        bg_tasks = await cls.get_bg_tasks_obj()  # 从上下文中获取后台任务实例
        if bg_tasks.tasks:  # 如果任务队列不为空
            await bg_tasks()  # 执行所有任务
