"""
集成测试：合规规则路由 (R2)
Integration tests for compliance rules routes

覆盖范围：
- R2.6/2.7/2.8 各分支（422/403/404 与正常流）
- Property 2: 单 Rule Set 规则数上限（连续插入 200 条 → 全部成功；第 201 条 → 409）

**Validates: Requirements 2.5, 2.6, 2.7, 2.8, 2.9**
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

# ── 路径设置 ──────────────────────────────────────────────────────────────────
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app
from app.core.config import settings

# ── 辅助函数 ──────────────────────────────────────────────────────────────────

def _make_token(user_id: str, role: str, name: str = "测试用户") -> str:
    """生成测试用 JWT Token"""
    payload = {
        "user_id": user_id,
        "dingtalk_user_id": f"dt_{user_id}",
        "name": name,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=24),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def _admin_headers(role: str = "法务") -> dict:
    return {"Authorization": f"Bearer {_make_token(str(uuid4()), role)}"}


def _sales_headers() -> dict:
    return {"Authorization": f"Bearer {_make_token(str(uuid4()), '销售')}"}


def _make_rule_orm(
    rule_id: str = None,
    rule_set_id: str = None,
    title: str = "测试规则",
    rule_type: str = "number",
    severity: str = "must",
    order: int = 0,
) -> MagicMock:
    """构造规则 ORM mock 对象"""
    rule = MagicMock()
    rule.id = uuid4() if rule_id is None else rule_id
    rule.rule_set_id = uuid4() if rule_set_id is None else rule_set_id
    rule.title = title
    rule.requirement = "规则要求描述"
    rule.rule_type = rule_type
    rule.severity = severity
    rule.order = order
    rule.created_at = datetime.utcnow()
    rule.updated_at = datetime.utcnow()
    return rule


def _make_rule_set_orm(
    rule_set_id: str = None,
    name: str = "测试规则集合",
    is_active: bool = False,
    rule_count: int = 0,
) -> MagicMock:
    """构造规则集合 ORM mock 对象"""
    rs = MagicMock()
    rs.id = uuid4() if rule_set_id is None else rule_set_id
    rs.name = name
    rs.description = "描述"
    rs.is_active = is_active
    rs.rule_count = rule_count
    rs.created_at = datetime.utcnow()
    rs.updated_at = datetime.utcnow()
    return rs


# ── 同步测试客户端 ────────────────────────────────────────────────────────────
client = TestClient(app)

# ── 有效规则请求体 ────────────────────────────────────────────────────────────
VALID_RULE_BODY = {
    "rule_type": "number",
    "title": "合同编号规则",
    "requirement": "合同编号必须符合公司规范",
    "severity": "must",
    "order": 0,
}


# ═════════════════════════════════════════════════════════════════════════════
# R2.7: 403 权限不足
# ═════════════════════════════════════════════════════════════════════════════

class TestRuleAuthorization:
    """R2.7: 非法务/运营角色调用写接口返回 403"""

    def test_sales_cannot_create_rule(self):
        resp = client.post(
            f"/api/compliance/rule-sets/{uuid4()}/rules",
            json=VALID_RULE_BODY,
            headers=_sales_headers(),
        )
        assert resp.status_code == 403

    def test_sales_cannot_update_rule(self):
        resp = client.put(
            f"/api/compliance/rules/{uuid4()}",
            json={"title": "新标题"},
            headers=_sales_headers(),
        )
        assert resp.status_code == 403

    def test_sales_cannot_delete_rule(self):
        resp = client.delete(
            f"/api/compliance/rules/{uuid4()}",
            headers=_sales_headers(),
        )
        assert resp.status_code == 403

    @patch("app.routes.compliance.compliance_service.list_rules")
    def test_sales_can_list_rules(self, mock_list):
        """销售可以查看规则列表（只读）"""
        mock_list.return_value = []
        resp = client.get(
            f"/api/compliance/rule-sets/{uuid4()}/rules",
            headers=_sales_headers(),
        )
        assert resp.status_code == 200

    @patch("app.routes.compliance.compliance_service.create_rule")
    def test_ops_can_create_rule(self, mock_create):
        """运营也属于管理员，可以创建规则"""
        mock_create.return_value = _make_rule_orm(title="运营创建的规则")
        resp = client.post(
            f"/api/compliance/rule-sets/{uuid4()}/rules",
            json=VALID_RULE_BODY,
            headers=_admin_headers(role="运营"),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

    def test_no_token_create_rule_returns_401(self):
        resp = client.post(
            f"/api/compliance/rule-sets/{uuid4()}/rules",
            json=VALID_RULE_BODY,
        )
        assert resp.status_code == 401

    def test_no_token_list_rules_returns_401(self):
        resp = client.get(f"/api/compliance/rule-sets/{uuid4()}/rules")
        assert resp.status_code == 401

    def test_no_token_update_rule_returns_401(self):
        resp = client.put(
            f"/api/compliance/rules/{uuid4()}",
            json={"title": "新标题"},
        )
        assert resp.status_code == 401

    def test_no_token_delete_rule_returns_401(self):
        resp = client.delete(f"/api/compliance/rules/{uuid4()}")
        assert resp.status_code == 401


# ═════════════════════════════════════════════════════════════════════════════
# R2.6: 422 字段约束
# ═════════════════════════════════════════════════════════════════════════════

class TestCreateRuleValidation:
    """R2.6: 字段约束验证"""

    def test_create_rule_missing_title_returns_422(self):
        resp = client.post(
            f"/api/compliance/rule-sets/{uuid4()}/rules",
            json={"rule_type": "number", "requirement": "要求", "severity": "must"},
            headers=_admin_headers(),
        )
        assert resp.status_code == 422

    def test_create_rule_empty_title_returns_422(self):
        body = {**VALID_RULE_BODY, "title": ""}
        resp = client.post(
            f"/api/compliance/rule-sets/{uuid4()}/rules",
            json=body,
            headers=_admin_headers(),
        )
        assert resp.status_code == 422

    def test_create_rule_blank_title_returns_422(self):
        body = {**VALID_RULE_BODY, "title": "   "}
        resp = client.post(
            f"/api/compliance/rule-sets/{uuid4()}/rules",
            json=body,
            headers=_admin_headers(),
        )
        assert resp.status_code == 422

    def test_create_rule_title_too_long_returns_422(self):
        body = {**VALID_RULE_BODY, "title": "x" * 101}
        resp = client.post(
            f"/api/compliance/rule-sets/{uuid4()}/rules",
            json=body,
            headers=_admin_headers(),
        )
        assert resp.status_code == 422

    def test_create_rule_requirement_too_long_returns_422(self):
        body = {**VALID_RULE_BODY, "requirement": "x" * 2001}
        resp = client.post(
            f"/api/compliance/rule-sets/{uuid4()}/rules",
            json=body,
            headers=_admin_headers(),
        )
        assert resp.status_code == 422

    def test_create_rule_invalid_rule_type_returns_422(self):
        body = {**VALID_RULE_BODY, "rule_type": "invalid_type"}
        resp = client.post(
            f"/api/compliance/rule-sets/{uuid4()}/rules",
            json=body,
            headers=_admin_headers(),
        )
        assert resp.status_code == 422

    def test_create_rule_invalid_severity_returns_422(self):
        body = {**VALID_RULE_BODY, "severity": "critical"}
        resp = client.post(
            f"/api/compliance/rule-sets/{uuid4()}/rules",
            json=body,
            headers=_admin_headers(),
        )
        assert resp.status_code == 422

    def test_update_rule_title_too_long_returns_422(self):
        resp = client.put(
            f"/api/compliance/rules/{uuid4()}",
            json={"title": "x" * 101},
            headers=_admin_headers(),
        )
        assert resp.status_code == 422

    def test_update_rule_invalid_severity_returns_422(self):
        resp = client.put(
            f"/api/compliance/rules/{uuid4()}",
            json={"severity": "critical"},
            headers=_admin_headers(),
        )
        assert resp.status_code == 422


# ═════════════════════════════════════════════════════════════════════════════
# R2.1/2.2: POST /api/compliance/rule-sets/{rule_set_id}/rules 正常流
# ═════════════════════════════════════════════════════════════════════════════

class TestCreateRule:
    """R2.1/2.2: 创建规则正常流"""

    @patch("app.routes.compliance.compliance_service.create_rule")
    def test_create_rule_success(self, mock_create):
        mock_create.return_value = _make_rule_orm(title="合同编号规则")
        resp = client.post(
            f"/api/compliance/rule-sets/{uuid4()}/rules",
            json=VALID_RULE_BODY,
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        rule = data["data"]["rule"]
        assert rule["title"] == "合同编号规则"
        assert "id" in rule
        assert "rule_set_id" in rule
        assert "created_at" in rule
        assert "updated_at" in rule

    @patch("app.routes.compliance.compliance_service.create_rule")
    def test_create_rule_all_rule_types(self, mock_create):
        """四种 rule_type 都可以创建"""
        for rule_type in ["number", "name", "description", "file"]:
            mock_create.return_value = _make_rule_orm(rule_type=rule_type)
            body = {**VALID_RULE_BODY, "rule_type": rule_type}
            resp = client.post(
                f"/api/compliance/rule-sets/{uuid4()}/rules",
                json=body,
                headers=_admin_headers(),
            )
            assert resp.status_code == 200, f"rule_type={rule_type} 应该成功"

    @patch("app.routes.compliance.compliance_service.create_rule")
    def test_create_rule_both_severities(self, mock_create):
        """must 和 should 两种严重程度都可以创建"""
        for severity in ["must", "should"]:
            mock_create.return_value = _make_rule_orm(severity=severity)
            body = {**VALID_RULE_BODY, "severity": severity}
            resp = client.post(
                f"/api/compliance/rule-sets/{uuid4()}/rules",
                json=body,
                headers=_admin_headers(),
            )
            assert resp.status_code == 200, f"severity={severity} 应该成功"

    @patch("app.routes.compliance.compliance_service.create_rule")
    def test_create_rule_response_has_required_fields(self, mock_create):
        """创建响应包含所有必需字段"""
        mock_create.return_value = _make_rule_orm()
        resp = client.post(
            f"/api/compliance/rule-sets/{uuid4()}/rules",
            json=VALID_RULE_BODY,
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        rule = resp.json()["data"]["rule"]
        required_fields = [
            "id", "rule_set_id", "rule_type", "title",
            "requirement", "severity", "order", "created_at", "updated_at",
        ]
        for field in required_fields:
            assert field in rule, f"响应缺少字段: {field}"


# ═════════════════════════════════════════════════════════════════════════════
# R2.3: GET /api/compliance/rule-sets/{rule_set_id}/rules 列表
# ═════════════════════════════════════════════════════════════════════════════

class TestListRules:
    """R2.3: 查询规则列表"""

    @patch("app.routes.compliance.compliance_service.list_rules")
    def test_list_rules_empty(self, mock_list):
        mock_list.return_value = []
        resp = client.get(
            f"/api/compliance/rule-sets/{uuid4()}/rules",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["rules"] == []

    @patch("app.routes.compliance.compliance_service.list_rules")
    def test_list_rules_returns_items(self, mock_list):
        rule1 = _make_rule_orm(title="规则1", rule_type="number")
        rule2 = _make_rule_orm(title="规则2", rule_type="name")
        mock_list.return_value = [rule1, rule2]
        resp = client.get(
            f"/api/compliance/rule-sets/{uuid4()}/rules",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]["rules"]) == 2

    @patch("app.routes.compliance.compliance_service.list_rules")
    def test_list_rules_includes_all_fields(self, mock_list):
        mock_list.return_value = [_make_rule_orm()]
        resp = client.get(
            f"/api/compliance/rule-sets/{uuid4()}/rules",
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        rule = resp.json()["data"]["rules"][0]
        for field in ["id", "rule_set_id", "rule_type", "title",
                      "requirement", "severity", "order"]:
            assert field in rule, f"列表响应缺少字段: {field}"


# ═════════════════════════════════════════════════════════════════════════════
# R2.4/2.8: PUT /api/compliance/rules/{rule_id} 更新
# ═════════════════════════════════════════════════════════════════════════════

class TestUpdateRule:
    """R2.4/2.8: 更新规则"""

    @patch("app.routes.compliance.compliance_service.update_rule")
    def test_update_rule_title(self, mock_update):
        mock_update.return_value = _make_rule_orm(title="更新后的标题")
        resp = client.put(
            f"/api/compliance/rules/{uuid4()}",
            json={"title": "更新后的标题"},
            headers=_admin_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["rule"]["title"] == "更新后的标题"

    @patch("app.routes.compliance.compliance_service.update_rule")
    def test_update_rule_severity(self, mock_update):
        mock_update.return_value = _make_rule_orm(severity="should")
        resp = client.put(
            f"/api/compliance/rules/{uuid4()}",
            json={"severity": "should"},
            headers=_admin_headers(),
        )
        assert resp.status_code == 200

    @patch("app.routes.compliance.compliance_service.update_rule")
    def test_update_rule_not_found_returns_404(self, mock_update):
        """R2.8: 不存在的 rule_id 返回 404"""
        mock_update.side_effect = HTTPException(status_code=404, detail="规则不存在")
        resp = client.put(
            f"/api/compliance/rules/{uuid4()}",
            json={"title": "不存在"},
            headers=_admin_headers(),
        )
        assert resp.status_code == 404


# ═════════════════════════════════════════════════════════════════════════════
# R2.5: DELETE /api/compliance/rules/{rule_id} 删除
# ═════════════════════════════════════════════════════════════════════════════

class TestDeleteRule:
    """R2.5: 删除规则"""

    @patch("app.routes.compliance.compliance_service.delete_rule")
    def test_delete_rule_success(self, mock_delete):
        """删除规则成功，返回 204"""
        mock_delete.return_value = None
        resp = client.delete(
            f"/api/compliance/rules/{uuid4()}",
            headers=_admin_headers(),
        )
        assert resp.status_code == 204

    @patch("app.routes.compliance.compliance_service.delete_rule")
    def test_delete_rule_not_found_returns_404(self, mock_delete):
        """R2.8: 不存在的 rule_id 返回 404"""
        mock_delete.side_effect = HTTPException(status_code=404, detail="规则不存在")
        resp = client.delete(
            f"/api/compliance/rules/{uuid4()}",
            headers=_admin_headers(),
        )
        assert resp.status_code == 404


# ═════════════════════════════════════════════════════════════════════════════
# Property 2: 单 Rule Set 规则数上限
# **Validates: Requirements 2.9**
# ═════════════════════════════════════════════════════════════════════════════

class TestProperty2RulesQuotaLimit:
    """
    Property 2: 单 Rule Set 规则数上限
    **Validates: Requirements 2.9**

    连续插入 200 条 → 全部成功；第 201 条 → 409 且错误码为 compliance_rules_quota_exceeded。
    使用 mock 模拟 service 层行为：前 200 次调用成功，第 201 次抛 HTTPException(409)。
    """

    def test_200_rules_all_succeed(self):
        """
        连续插入 200 条规则，全部应返回 200。
        **Validates: Requirements 2.9**
        """
        call_count = 0

        async def mock_create_rule(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return _make_rule_orm(title=f"规则 {call_count}")

        rule_set_id = str(uuid4())

        with patch(
            "app.routes.compliance.compliance_service.create_rule",
            side_effect=mock_create_rule,
        ):
            for i in range(200):
                body = {**VALID_RULE_BODY, "title": f"规则 {i + 1}"}
                resp = client.post(
                    f"/api/compliance/rule-sets/{rule_set_id}/rules",
                    json=body,
                    headers=_admin_headers(),
                )
                assert resp.status_code == 200, (
                    f"第 {i + 1} 条规则应该成功，实际状态码: {resp.status_code}"
                )

        assert call_count == 200, f"service 应被调用 200 次，实际: {call_count}"

    def test_201st_rule_returns_409(self):
        """
        第 201 条规则应返回 409，错误码为 compliance_rules_quota_exceeded。
        **Validates: Requirements 2.9**
        """
        call_count = 0

        async def mock_create_rule(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count > 200:
                raise HTTPException(
                    status_code=409,
                    detail="单个规范集合下最多可包含 200 条规则",
                )
            return _make_rule_orm(title=f"规则 {call_count}")

        rule_set_id = str(uuid4())

        with patch(
            "app.routes.compliance.compliance_service.create_rule",
            side_effect=mock_create_rule,
        ):
            # 前 200 条成功
            for i in range(200):
                body = {**VALID_RULE_BODY, "title": f"规则 {i + 1}"}
                resp = client.post(
                    f"/api/compliance/rule-sets/{rule_set_id}/rules",
                    json=body,
                    headers=_admin_headers(),
                )
                assert resp.status_code == 200, (
                    f"第 {i + 1} 条规则应该成功，实际状态码: {resp.status_code}"
                )

            # 第 201 条应返回 409
            body = {**VALID_RULE_BODY, "title": "第 201 条规则"}
            resp = client.post(
                f"/api/compliance/rule-sets/{rule_set_id}/rules",
                json=body,
                headers=_admin_headers(),
            )
            assert resp.status_code == 409, (
                f"第 201 条规则应返回 409，实际状态码: {resp.status_code}"
            )
            data = resp.json()
            assert data.get("error", {}).get("code") == "compliance_rules_quota_exceeded", (
                f"错误码应为 compliance_rules_quota_exceeded，实际: {data}"
            )

        # service 被调用了 201 次（200 成功 + 1 失败）
        assert call_count == 201, f"service 应被调用 201 次，实际: {call_count}"

    def test_201st_rule_db_count_remains_200(self):
        """
        第 201 条失败后，DB 内仍为 200 条（通过 mock 验证 service 调用次数）。
        **Validates: Requirements 2.9**
        """
        successful_calls = 0

        async def mock_create_rule(*args, **kwargs):
            nonlocal successful_calls
            if successful_calls >= 200:
                raise HTTPException(
                    status_code=409,
                    detail="单个规范集合下最多可包含 200 条规则",
                )
            successful_calls += 1
            return _make_rule_orm(title=f"规则 {successful_calls}")

        rule_set_id = str(uuid4())

        with patch(
            "app.routes.compliance.compliance_service.create_rule",
            side_effect=mock_create_rule,
        ):
            for i in range(200):
                body = {**VALID_RULE_BODY, "title": f"规则 {i + 1}"}
                client.post(
                    f"/api/compliance/rule-sets/{rule_set_id}/rules",
                    json=body,
                    headers=_admin_headers(),
                )

            # 第 201 条失败
            body = {**VALID_RULE_BODY, "title": "超限规则"}
            resp = client.post(
                f"/api/compliance/rule-sets/{rule_set_id}/rules",
                json=body,
                headers=_admin_headers(),
            )
            assert resp.status_code == 409

        # 成功写入的规则数量仍为 200
        assert successful_calls == 200, (
            f"Property 2: DB 内规则数应为 200，实际成功调用次数: {successful_calls}"
        )

    def test_quota_exceeded_error_code(self):
        """
        超限时返回的错误码必须是 compliance_rules_quota_exceeded。
        **Validates: Requirements 2.9**
        """
        async def mock_create_rule(*args, **kwargs):
            raise HTTPException(
                status_code=409,
                detail="单个规范集合下最多可包含 200 条规则",
            )

        with patch(
            "app.routes.compliance.compliance_service.create_rule",
            side_effect=mock_create_rule,
        ):
            resp = client.post(
                f"/api/compliance/rule-sets/{uuid4()}/rules",
                json=VALID_RULE_BODY,
                headers=_admin_headers(),
            )
            assert resp.status_code == 409
            data = resp.json()
            error_code = data.get("error", {}).get("code")
            assert error_code == "compliance_rules_quota_exceeded", (
                f"错误码应为 compliance_rules_quota_exceeded，实际: {error_code}\n"
                f"完整响应: {data}"
            )
