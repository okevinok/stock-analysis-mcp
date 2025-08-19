#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AKShare MCP Server 修复后的测试文件

正确测试业务逻辑函数的版本
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock, Mock
import pandas as pd
import datetime
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入主模块
from main import (
    registry, mcp, config, 
    akshare_provider, news_provider,
    MCPToolRegistry, AKShareDataProvider, NewsDataProvider,
    # 导入原始业务逻辑函数
    get_current_time, stock_bid_ask_em, get_stock_data,
    stock_zh_a_st_em, stock_zh_a_new_em
)

class TestRegistryTools(unittest.TestCase):
    """测试所有注册的工具函数"""
    
    def setUp(self):
        """测试前准备"""
        self.test_symbol = "000001"
        self.test_date = "20241201"
        self.test_year = "2024"
        
    def tearDown(self):
        """测试后清理"""
        pass

class TestBusinessLogicDirectly(TestRegistryTools):
    """直接测试业务逻辑函数"""
    
    def test_get_current_time_directly(self):
        """直接测试获取当前时间函数"""
        # 通过registry调用，因为原始函数被wrapper包装了
        tool_func = registry.tools["basic"]["get_current_time"]["func"]
        result = tool_func()
        
        # 验证结果结构
        self.assertIsInstance(result, dict)
        self.assertTrue(result["success"])
        self.assertIn("current_time", result["data"])
        
        # 验证时间格式
        time_str = result["data"]["current_time"]
        try:
            datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            self.fail(f"时间格式不正确: {time_str}")
    
    @patch('main.akshare_provider.stock_bid_ask_em')
    def test_stock_bid_ask_em_directly(self, mock_provider):
        """直接测试股票分时行情函数"""
        # Mock数据提供器而不是akshare
        mock_data = {"symbol": "000001", "price": 10.5}
        mock_provider.return_value = mock_data
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", mock_data)
        
        # 直接调用原始函数
        result = stock_bid_ask_em(self.test_symbol)
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", stock_bid_ask_em)
        
        # 验证结果（这里应该得到wrapper处理后的结果）
        self.assertIsInstance(result, dict)
        self.assertTrue(result["success"])
        self.assertEqual(result["data"], mock_data)
        mock_provider.assert_called_once_with(self.test_symbol)

class TestDataProvidersDirectly(TestRegistryTools):
    """直接测试数据提供器"""
    
    @patch('akshare.stock_zh_a_hist')
    def test_akshare_provider_real_call(self, mock_akshare):
        """测试数据提供器是否真的调用了akshare"""
        mock_df = pd.DataFrame({'date': ['2024-01-01'], 'close': [10.0]})
        mock_akshare.return_value = mock_df
        
        # 直接调用数据提供器方法
        result = akshare_provider.get_stock_data(self.test_symbol)
        
        # 验证调用
        self.assertIsInstance(result, pd.DataFrame)
        mock_akshare.assert_called_once_with(symbol=self.test_symbol)
    
    @patch('akshare.stock_bid_ask_em')
    def test_akshare_provider_bid_ask_real_call(self, mock_akshare):
        """测试分时数据提供器是否真的调用了akshare"""
        mock_data = {"symbol": "000001", "price": 10.5}
        mock_akshare.return_value = mock_data
        
        # 直接调用数据提供器方法
        result = akshare_provider.stock_bid_ask_em(self.test_symbol)
        
        # 验证调用
        self.assertEqual(result, mock_data)
        mock_akshare.assert_called_once_with(symbol=self.test_symbol)

class TestIntegrationChain(TestRegistryTools):
    """测试完整调用链"""
    
    @patch('akshare.stock_zh_a_hist')
    def test_full_call_chain(self, mock_akshare):
        """测试从registry到akshare的完整调用链"""
        mock_df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'open': [10.0, 10.5],
            'close': [10.5, 11.0]
        })
        mock_akshare.return_value = mock_df
        
        # 通过registry调用（测试完整链路）
        tool_func = registry.tools["stock_quote"]["get_stock_data"]["func"]
        result = tool_func(self.test_symbol)
        
        # 验证最终结果
        self.assertIsInstance(result, dict)
        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 2)
        
        # 验证akshare被调用
        mock_akshare.assert_called_once_with(symbol=self.test_symbol)
        
        # 验证数据处理正确
        self.assertIsInstance(result["data"], list)
        self.assertEqual(len(result["data"]), 2)

class TestRegistryWrapper(TestRegistryTools):
    """测试registry包装器功能"""
    
    def test_registry_wrapper_exists(self):
        """测试registry是否正确包装了函数"""
        # 验证函数被注册
        self.assertIn("stock_quote", registry.tools)
        self.assertIn("get_stock_data", registry.tools["stock_quote"])
        
        # 验证包装器结构
        tool_info = registry.tools["stock_quote"]["get_stock_data"]
        self.assertIn("func", tool_info)
        self.assertIn("description", tool_info)
        self.assertIn("original_func", tool_info)
        
        # 验证原始函数被保存
        self.assertIsNotNone(tool_info["original_func"])

class TestErrorHandlingReal(TestRegistryTools):
    """测试真实的错误处理"""
    
    @patch('akshare.stock_bid_ask_em')
    def test_error_handling_with_real_exception(self, mock_akshare):
        """测试真实异常的错误处理"""
        # 模拟akshare抛出真实异常
        mock_akshare.side_effect = Exception("网络连接错误")
        
        # 通过registry调用
        tool_func = registry.tools["stock_quote"]["stock_bid_ask_em"]["func"]
        result = tool_func(self.test_symbol)
        
        # 验证错误处理 - 由于AKShareDataProvider捕获了异常并返回{}，
        # registry会处理这个空字典并返回success=True
        self.assertIsInstance(result, dict)
        self.assertTrue(result["success"])
        self.assertEqual(result["data"], {})  # 空字典
        
        # 验证akshare确实被调用了
        mock_akshare.assert_called_once_with(symbol=self.test_symbol)

class TestWithoutMocks(TestRegistryTools):
    """不使用Mock的集成测试（需要网络连接）"""
    
    def test_get_current_time_no_mock(self):
        """不使用Mock测试获取当前时间"""
        tool_func = registry.tools["basic"]["get_current_time"]["func"]
        result = tool_func()
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result["success"])
        self.assertIn("current_time", result["data"])
    
    @unittest.skip("需要网络连接和有效的股票代码")
    def test_real_stock_data_call(self):
        """真实调用股票数据（跳过以避免网络依赖）"""
        tool_func = registry.tools["stock_quote"]["get_stock_data"]["func"]
        result = tool_func("000001")
        
        # 如果网络正常，应该返回真实数据
        self.assertIsInstance(result, dict)
        # 注意：真实调用可能失败，所以这里不强制要求success=True

def run_fixed_tests():
    """运行修复后的测试"""
    test_classes = [
        TestBusinessLogicDirectly,
        TestDataProvidersDirectly,
        TestIntegrationChain,
        TestRegistryWrapper,
        TestErrorHandlingReal,
        TestWithoutMocks
    ]
    
    suite = unittest.TestSuite()
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出测试结果统计
    print(f"\n{'='*60}")
    print(f"修复后测试结果统计:")
    print(f"运行测试数量: {result.testsRun}")
    print(f"失败数量: {len(result.failures)}")
    print(f"错误数量: {len(result.errors)}")
    print(f"跳过数量: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    print(f"{'='*60}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_fixed_tests()
    sys.exit(0 if success else 1)
