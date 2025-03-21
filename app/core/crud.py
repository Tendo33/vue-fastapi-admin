from typing import Any, Dict, Generic, List, NewType, Tuple, Type, TypeVar, Union

from pydantic import BaseModel
from tortoise.expressions import Q
from tortoise.models import Model

# 定义一个新的类型 Total，表示总数
Total = NewType("Total", int)

# 定义类型变量，用于泛型类
ModelType = TypeVar("ModelType", bound=Model)  # 模型类型，必须是继承自 Model 的类
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)  # 创建时的输入类型，必须是继承自 BaseModel 的类
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)  # 更新时的输入类型，必须是继承自 BaseModel 的类


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    CRUD 基础类，提供了对数据库模型的增删改查操作。
    CRUD 代表 Create（创建）、Read（读取）、Update（更新）、Delete（删除）。
    """

    def __init__(self, model: Type[ModelType]):
        """
        初始化方法，接收一个模型类作为参数。
        参数:
            model: 数据库模型类。
        """
        self.model = model

    async def get(self, id: int) -> ModelType:
        """
        异步获取单个对象，通过 ID 查询。
        参数:
            id: 对象的唯一标识符。
        返回:
            ModelType: 查询到的对象。
        """
        return await self.model.get(id=id)

    async def list(self, page: int, page_size: int, search: Q = Q(), order: list = []) -> Tuple[Total, List[ModelType]]:
        """
        异步获取对象列表，支持分页、搜索和排序。
        参数:
            page: 当前页码。
            page_size: 每页的大小。
            search: 过滤条件，使用 Q 对象表示。
            order: 排序规则，列表形式。
        返回:
            Tuple[Total, List[ModelType]]: 包含总数和对象列表的元组。
        """
        query = self.model.filter(search)  # 应用过滤条件
        return await query.count(), await query.offset((page - 1) * page_size).limit(page_size).order_by(*order)

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """
        异步创建新对象。
        参数:
            obj_in: 创建对象的输入数据，可以是字典或 Pydantic 模型。
        返回:
            ModelType: 创建的对象。
        """
        if isinstance(obj_in, Dict):  # 如果输入是字典，直接使用
            obj_dict = obj_in
        else:  # 否则使用 Pydantic 的 model_dump 方法转换为字典
            obj_dict = obj_in.model_dump()
        obj = self.model(**obj_dict)  # 创建模型实例
        await obj.save()  # 保存到数据库
        return obj

    async def update(self, id: int, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        """
        异步更新对象。
        参数:
            id: 要更新的对象的唯一标识符。
            obj_in: 更新对象的输入数据，可以是字典或 Pydantic 模型。
        返回:
            ModelType: 更新后的对象。
        """
        if isinstance(obj_in, Dict):  # 如果输入是字典，直接使用
            obj_dict = obj_in
        else:  # 否则转换为字典，排除未设置的字段和 ID
            obj_dict = obj_in.model_dump(exclude_unset=True, exclude={"id"})
        obj = await self.get(id=id)  # 获取现有对象
        obj = obj.update_from_dict(obj_dict)  # 更新对象
        await obj.save()  # 保存更改
        return obj

    async def remove(self, id: int) -> None:
        """
        异步删除对象。
        参数:
            id: 要删除的对象的唯一标识符。
        """
        obj = await self.get(id=id)  # 获取对象
        await obj.delete()  # 删除对象
