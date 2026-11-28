"""身份词表单一事实来源的完整性测试。

锁定两件事：
1. 枚举取值必须与数据库/前端的实际词表一致（Role 四值、OwnerKind 两值）；
2. 谓词与比较对"裸字符串"（数据库返回的就是 str）同样生效。
"""

from app.roles import GUEST_OWNER_PREFIX, USER_OWNER_PREFIX, OwnerKind, Role, is_admin, is_guest, owner_key_for


def test_role_values_match_known_vocabulary():
    assert {r.value for r in Role} == {"guest", "member", "admin", "superadmin"}
    assert {k.value for k in OwnerKind} == {"user", "guest"}


def test_enum_equals_raw_db_strings():
    assert Role.ADMIN == "admin"
    assert "superadmin" == Role.SUPERADMIN
    assert OwnerKind.GUEST == "guest"
    # require_role 内部用 set 判权，依赖 str 枚举与裸字符串哈希一致
    assert "admin" in {Role.ADMIN, Role.SUPERADMIN}


def test_predicates_accept_raw_strings():
    assert is_guest("guest") and not is_guest("member")
    assert is_admin("admin") and is_admin("superadmin")
    assert not is_admin("member") and not is_admin("guest")


def test_owner_key_helpers_agree_with_prefixes():
    assert owner_key_for(OwnerKind.GUEST, "g1") == GUEST_OWNER_PREFIX + "g1"
    assert owner_key_for("user", "u1") == USER_OWNER_PREFIX + "u1"
