"""
Settings配置模块单元测试

测试配置加载和解析功能。
"""

import pytest

from cn_pii_anonymization.config.settings import Settings


class TestSettingsNameLists:
    """Settings姓名列表配置测试类"""

    def test_default_name_allow_list_empty(self):
        """测试默认allow_list为空"""
        settings = Settings()
        assert settings.name_allow_list == ""
        assert settings.parsed_name_allow_list == []

    def test_default_name_deny_list_empty(self):
        """测试默认deny_list为空"""
        settings = Settings()
        assert settings.name_deny_list == ""
        assert settings.parsed_name_deny_list == []

    def test_parsed_name_allow_list_with_values(self, monkeypatch):
        """测试解析allow_list"""
        monkeypatch.setenv("NAME_ALLOW_LIST", "张三,李四,王五")
        settings = Settings()
        assert settings.parsed_name_allow_list == ["张三", "李四", "王五"]

    def test_parsed_name_deny_list_with_values(self, monkeypatch):
        """测试解析deny_list"""
        monkeypatch.setenv("NAME_DENY_LIST", "赵六,钱七")
        settings = Settings()
        assert settings.parsed_name_deny_list == ["赵六", "钱七"]

    def test_parsed_name_list_with_spaces(self, monkeypatch):
        """测试带空格的列表解析"""
        monkeypatch.setenv("NAME_ALLOW_LIST", " 张三 , 李四 , 王五 ")
        settings = Settings()
        assert settings.parsed_name_allow_list == ["张三", "李四", "王五"]

    def test_parsed_name_list_with_empty_items(self, monkeypatch):
        """测试包含空项的列表解析"""
        monkeypatch.setenv("NAME_ALLOW_LIST", "张三,,李四,")
        settings = Settings()
        assert settings.parsed_name_allow_list == ["张三", "李四"]

    def test_parsed_name_list_single_item(self, monkeypatch):
        """测试单个项目的列表"""
        monkeypatch.setenv("NAME_DENY_LIST", "单个名字")
        settings = Settings()
        assert settings.parsed_name_deny_list == ["单个名字"]

    def test_parsed_name_list_trailing_comma(self, monkeypatch):
        """测试末尾逗号"""
        monkeypatch.setenv("NAME_ALLOW_LIST", "张三,李四,")
        settings = Settings()
        assert settings.parsed_name_allow_list == ["张三", "李四"]
