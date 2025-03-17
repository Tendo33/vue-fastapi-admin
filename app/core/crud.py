from typing import Any, Dict, Generic, List, NewType, Tuple, Type, TypeVar, Union

from pydantic import BaseModel
from tortoise.expressions import Q
from tortoise.models import Model

# 定义一个新的类型 Total，表示总数
Total = NewType("Total", int)

# 定义类型变量，用于泛型类
ModelType = TypeVar("ModelType", bound=Model)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

# CRUD 代表 Create（创建）、Read（读取）、Update（更新）、Delete（删除）
class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        # 初始化方法，接收一个模型类作为参数
        self.model = model

    async def get(self, id: int) -> ModelType:
        # 异步获取单个对象，通过 ID 查询
        return await self.model.get(id=id)

    async def list(self, page: int, page_size: int, search: Q = Q(), order: list = []) -> Tuple[Total, List[ModelType]]:
        # 异步获取对象列表，支持分页、搜索和排序
        query = self.model.filter(search)  # 过滤条件
        return await query.count(), await query.offset((page - 1) * page_size).limit(page_size).order_by(*order)

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        # 异步创建新对象
        if isinstance(obj_in, Dict):
            obj_dict = obj_in  # 如果输入是字典，直接使用
        else:
            obj_dict = obj_in.model_dump()  # 否则使用 Pydantic 的 model_dump 方法转换为字典
        obj = self.model(**obj_dict)  # 创建模型实例
        await obj.save()  # 保存到数据库
        return obj

    async def update(self, id: int, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        # 异步更新对象
        if isinstance(obj_in, Dict):
            obj_dict = obj_in  # 如果输入是字典，直接使用
        else:
            obj_dict = obj_in.model_dump(exclude_unset=True, exclude={"id"})  # 否则转换为字典，排除未设置的字段和 ID
        obj = await self.get(id=id)  # 获取现有对象
        obj = obj.update_from_dict(obj_dict)  # 更新对象
        await obj.save()  # 保存更改
        return obj

    async def remove(self, id: int) -> None:
        # 异步删除对象
        obj = await self.get(id=id)  # 获取对象
        await obj.delete()  # 删除对象
