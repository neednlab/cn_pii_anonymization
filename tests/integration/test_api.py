"""
API集成测试

测试FastAPI应用的各个端点。
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from cn_pii_anonymization.api.app import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture
async def async_client():
    """创建异步测试客户端"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


class TestHealthCheck:
    """健康检查测试"""

    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "success"
        assert data["data"]["status"] == "healthy"

    def test_root(self, client):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 200
        assert "name" in data["data"]
        assert "version" in data["data"]


class TestTextAnonymize:
    """文本匿名化测试"""

    def test_anonymize_phone(self, client):
        """测试手机号匿名化"""
        response = client.post(
            "/api/v1/text/anonymize",
            json={
                "text": "我的手机号是13812345678",
                "entities": ["CN_PHONE_NUMBER"],
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 200
        assert "138****5678" in data["data"]["anonymized_text"]
        assert len(data["data"]["pii_entities"]) == 1
        assert data["data"]["pii_entities"][0]["entity_type"] == "CN_PHONE_NUMBER"

    def test_anonymize_id_card(self, client):
        """测试身份证匿名化"""
        response = client.post(
            "/api/v1/text/anonymize",
            json={
                "text": "身份证号110101199001011237",
                "entities": ["CN_ID_CARD"],
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 200
        assert len(data["data"]["pii_entities"]) == 1
        assert data["data"]["pii_entities"][0]["entity_type"] == "CN_ID_CARD"

    def test_anonymize_mixed(self, client):
        """测试混合PII匿名化"""
        response = client.post(
            "/api/v1/text/anonymize",
            json={
                "text": "手机号13812345678，身份证110101199001011237",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 200
        assert len(data["data"]["pii_entities"]) >= 2

    def test_anonymize_no_pii(self, client):
        """测试无PII文本"""
        response = client.post(
            "/api/v1/text/anonymize",
            json={
                "text": "这是一段普通文本",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 200
        assert len(data["data"]["pii_entities"]) == 0
        assert data["data"]["anonymized_text"] == "这是一段普通文本"

    def test_anonymize_with_custom_operator(self, client):
        """测试自定义操作符"""
        response = client.post(
            "/api/v1/text/anonymize",
            json={
                "text": "手机号13812345678",
                "entities": ["CN_PHONE_NUMBER"],
                "operators": {
                    "CN_PHONE_NUMBER": {
                        "type": "mask",
                        "masking_char": "#",
                        "keep_prefix": 3,
                        "keep_suffix": 2,
                    }
                },
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 200
        assert "138######78" in data["data"]["anonymized_text"]

    def test_anonymize_empty_text(self, client):
        """测试空文本"""
        response = client.post(
            "/api/v1/text/anonymize",
            json={
                "text": "",
            },
        )
        assert response.status_code == 422

    def test_anonymize_text_too_long(self, client):
        """测试超长文本"""
        long_text = "a" * 100001
        response = client.post(
            "/api/v1/text/anonymize",
            json={
                "text": long_text,
            },
        )
        assert response.status_code == 422


class TestTextAnalyze:
    """文本分析测试"""

    def test_analyze_phone(self, client):
        """测试手机号分析"""
        response = client.post(
            "/api/v1/text/analyze",
            json={
                "text": "我的手机号是13812345678",
                "entities": ["CN_PHONE_NUMBER"],
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 200
        assert data["data"]["has_pii"] is True
        assert len(data["data"]["pii_entities"]) == 1

    def test_analyze_no_pii(self, client):
        """测试无PII分析"""
        response = client.post(
            "/api/v1/text/analyze",
            json={
                "text": "这是一段普通文本",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 200
        assert data["data"]["has_pii"] is False
        assert len(data["data"]["pii_entities"]) == 0


class TestSupportedEntities:
    """支持实体类型测试"""

    def test_get_entities(self, client):
        """测试获取支持的实体类型"""
        response = client.get("/api/v1/text/entities")
        assert response.status_code == 200

        data = response.json()
        assert data["code"] == 200
        assert "entities" in data["data"]
        assert "CN_PHONE_NUMBER" in data["data"]["entities"]
        assert "CN_ID_CARD" in data["data"]["entities"]
