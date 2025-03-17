import asyncio
from datetime import datetime

from tortoise import fields, models

from app.settings import settings


class SqlBaseModel(models.Model):
    # 定义一个大整数类型的主键字段，并为其创建索引
    id = fields.BigIntField(pk=True, index=True)

    # 异步方法，将模型实例转换为字典
    async def to_dict(self, m2m: bool = False, exclude_fields: list[str] | None = None):
        if exclude_fields is None:
            exclude_fields = []

        d = {}
        # 遍历模型的数据库字段
        for field in self._meta.db_fields:
            if field not in exclude_fields:
                value = getattr(self, field)
                # 如果字段值是日期时间类型，则格式化为字符串
                if isinstance(value, datetime):
                    value = value.strftime(settings.DATETIME_FORMAT)
                d[field] = value

        # 如果需要处理多对多关系字段
        if m2m:
            tasks = [
                self.__fetch_m2m_field(field, exclude_fields)
                for field in self._meta.m2m_fields
                if field not in exclude_fields
            ]
            # 异步获取所有多对多字段的值
            results = await asyncio.gather(*tasks)
            for field, values in results:
                d[field] = values

        return d

    # 私有异步方法，获取多对多字段的值
    async def __fetch_m2m_field(self, field: str, exclude_fields: list[str]):
        # 获取所有相关对象的值
        values = await getattr(self, field).all().values()
        formatted_values = []

        for value in values:
            formatted_value = {}
            for k, v in value.items():
                if k not in exclude_fields:
                    # 如果值是日期时间类型，则格式化为字符串
                    if isinstance(v, datetime):
                        formatted_value[k] = v.strftime(settings.DATETIME_FORMAT)
                    else:
                        formatted_value[k] = v
            formatted_values.append(formatted_value)

        return field, formatted_values

    class Meta:
        # 声明这是一个抽象模型类，不会在数据库中创建表
        abstract = True


class UUIDModel:
    # 定义一个唯一的UUID字段，但不是主键，并为其创建索引
    uuid = fields.UUIDField(unique=True, pk=False, index=True)


class TimestampMixin:
    # 定义自动添加创建时间的字段，并为其创建索引
    created_at = fields.DatetimeField(auto_now_add=True, index=True)
    # 定义自动更新的更新时间字段，并为其创建索引
    updated_at = fields.DatetimeField(auto_now=True, index=True)
