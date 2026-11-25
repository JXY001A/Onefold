"""提取器的输出契约：Pydantic 模型、JSON Schema 与系统提示词。

模型返回的结构在这里定死，prompt、校验、落库三方共用同一份定义，
避免字段或分类取值在两处各写一份而漂移。
"""

import json
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from ..config import settings
from ..services.memory import CATEGORIES, normalize_category

# 分类枚举直接由服务层常量生成，避免两处各写一份导致取值漂移
CategoryName = Literal[*CATEGORIES]


class CardOp(BaseModel):
    """模型返回的一张卡片；只接受 upsert，不在这里做删除。

    key    卡片的稳定标识（如 name、tech_stack），同一 key 视为同一事实
    value  结构化值（JSON 可表达的任意类型），null 不合法
    text   给人看的一句话描述，限制长度避免占满上下文
    """

    action: Literal["upsert"] = "upsert"
    # 枚举定义会进 JSON Schema，模型能直接看到合法取值；
    # 英文别名/旧字段 type 在校验前由 normalize_legacy_shape 先归一成中文
    category: CategoryName = Field(description="记忆分类，只能是：" + "/".join(CATEGORIES))
    key: str = Field(min_length=1, max_length=64)
    value: Any
    text: str = Field(min_length=1, max_length=settings.memory_card_chars)
    confidence: float = Field(default=0.8, ge=0, le=1)
    source_message_id: str

    @field_validator("value")
    @classmethod
    def value_not_null(cls, value: Any) -> Any:
        # 卡片必须有值；null 卡片没有注入意义
        if value is None:
            raise ValueError("card value must not be null")
        return value

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_shape(cls, data: Any) -> Any:
        """兼容模型偶尔返回的 id/type/content 旧形状，再做严格校验。"""
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if "text" not in data and "content" in data:
            data["text"] = data["content"]
        if "key" not in data and "id" in data:
            data["key"] = str(data["id"])[:64]
        if "value" not in data:
            data["value"] = data.get("content", data.get("text"))
        # 分类必须在 Literal 校验前变成中文，否则一个 unknown 值会让整次提取失败（走重试直到 failed）
        data["category"] = normalize_category(data.get("category") or data.get("type"))
        return data


class NoteOp(BaseModel):
    """模型返回的一条笔记；text 必须是短背景，不是整段对话。

    happened_at 可选，用来保留「什么时候发生」这类时间信息。
    """

    action: Literal["add"] = "add"
    # 笔记与卡片共用同一套中文分类，默认「其他」只作兜底
    category: CategoryName = Field(
        default="其他", description="记忆分类，只能是：" + "/".join(CATEGORIES)
    )
    text: str = Field(min_length=1, max_length=settings.memory_note_chars)
    confidence: float = Field(default=0.8, ge=0, le=1)
    happened_at: datetime | None = None
    source_message_id: str

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_shape(cls, data: Any) -> Any:
        """兼容模型把 note 正文写成 content 的情况。"""
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if "text" not in data and "content" in data:
            data["text"] = data["content"]
        # 与卡片同样先归一成中文，避免非法分类值中断整次提取
        data["category"] = normalize_category(data.get("category") or data.get("type"))
        return data


class ExtractionResult(BaseModel):
    """一次提取的完整结果，对应模型返回的 {"cards": [...], "notes": [...]}。"""

    cards: list[CardOp] = Field(default_factory=list)
    notes: list[NoteOp] = Field(default_factory=list)


class MemorySchemaError(RuntimeError):
    """模型两次输出都不符合 schema；重试也不会好，直接标记 failed。"""


# 直接由 Pydantic 生成字段约束，避免 prompt 和模型字段漂移
EXTRACTION_SCHEMA = json.dumps(
    ExtractionResult.model_json_schema(), ensure_ascii=False, indent=2
)

EXTRACTION_EXAMPLE = """{
  "cards": [
    {
      "action": "upsert",
      "category": "身份",
      "key": "name",
      "value": "金显昱",
      "text": "姓名：金显昱",
      "confidence": 0.95,
      "source_message_id": "msg-1"
    }
  ],
  "notes": [
    {
      "action": "add",
      "category": "项目",
      "text": "用户在做 Onefold 平台。",
      "confidence": 0.8,
      "happened_at": null,
      "source_message_id": "msg-2"
    }
  ]
}"""

SYSTEM_PROMPT = """你是用户长期记忆提取器。只提取用户明确说过或明确确认过的信息。

规则：
1. 用户的话是主要证据；助手的话只用于理解上下文，不能单独成为用户事实。
2. 不保存搜索结果、工具输出、临时任务进度、模型推测。
3. 稳定事实/偏好写 card；带原因、时间、人物、事件的写 note。
4. category 只能取下面 13 个中文值之一，选语义最接近的，不要用「其他」凑数：
   身份 = 姓名 / 年龄 / 性别 / 城市 / 时区 / 母语
   职业 = 公司 / 职位 / 行业 / 从业年限
   教育 = 学校 / 专业 / 学位 / 证书
   技能 = 语言 / 框架 / 工具 / 熟练度
   项目 = 在做或做过的产品 / 技术选型 / 当前进展
   目标 = 想达成但还没做到的计划与期限
   偏好 = 喜欢或讨厌的技术 / 工具 / 内容 / 审美
   沟通 = 希望被怎么回答：语言 / 篇幅 / 语气
   习惯 = 作息 / 工作流 / 固定流程
   关系 = 家人 / 同事 / 合作者及其角色
   约束 = 禁止事项 / 必须满足的条件 / 合规要求
   兴趣 = 工作之外的爱好与关注领域
   其他 = 仅当以上都不适用时才用，禁止因为偷懒选它
5. 每条记忆必须给出 source_message_id，且必须是上下文中 role=user 的消息。
6. 没有值得长期保留的信息时，返回 {"cards": [], "notes": []}；不要凑数。
7. 候选信息已存在于当前卡片时，也返回空数组，不要重复写入。
8. 不保存密码、API Key、身份证号、银行卡号等敏感信息。
9. 只输出 JSON，不要输出解释。"""