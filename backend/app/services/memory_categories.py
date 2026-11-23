"""记忆分类：全链路只用中文，写入、注入、界面展示共用这一份定义。

模型输出、历史英文数据、注入标签最终都走 normalize_category，
保证「类目」只有一个真源，不给脏值进库的机会。
"""

CATEGORIES = (
    "身份",  # 姓名、年龄、城市、时区、母语等不变的自我标识
    "职业",  # 公司、职位、行业、从业年限
    "教育",  # 学校、专业、学位、证书
    "技能",  # 语言、框架、工具及熟练度
    "项目",  # 在做或做过的产品、技术选型、进展
    "目标",  # 想达成但还没做到的计划与期限
    "偏好",  # 主观喜欢/讨厌的技术、工具、内容、审美
    "沟通",  # 希望被怎么回答：语言、篇幅、语气
    "习惯",  # 作息、工作流、固定流程
    "关系",  # 家人、同事、合作者及其角色
    "约束",  # 硬规则：禁止事项、必须满足的条件
    "兴趣",  # 工作之外的爱好与关注领域
    "其他",  # 确实无法归类的稳定事实，占比应低于 10%
)

# 历史英文值与模型偶发别名的兼容映射；未知值统一降级为「其他」
CATEGORY_ALIASES = {
    "profile": "身份",
    "identity": "身份",
    "personal": "身份",
    "career": "职业",
    "occupation": "职业",
    "job": "职业",
    "work": "职业",
    "education": "教育",
    "skill": "技能",
    "skills": "技能",
    "project": "项目",
    "projects": "项目",
    "goal": "目标",
    "goals": "目标",
    "plan": "目标",
    "preference": "偏好",
    "preferences": "偏好",
    "communication": "沟通",
    "style": "沟通",
    "habit": "习惯",
    "habits": "习惯",
    "routine": "习惯",
    "relationship": "关系",
    "relationships": "关系",
    "people": "关系",
    "constraint": "约束",
    "constraints": "约束",
    "rule": "约束",
    "interest": "兴趣",
    "interests": "兴趣",
    "hobby": "兴趣",
    "other": "其他",
    "misc": "其他",
}


def normalize_category(raw: str | None) -> str:
    """把任意来源的分类值归一成 CATEGORIES 里的中文值。

    模型输出、历史英文数据、注入标签都走这里，保证只有一个真源；
    认不出的值一律落到「其他」，不让脏值进库，也不让注入时显示成英文。
    """
    value = str(raw or "").strip()
    if value in CATEGORIES:
        return value
    return CATEGORY_ALIASES.get(value.lower(), "其他")