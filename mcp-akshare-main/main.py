#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AKShare MCP Server - 重构版本

这是一个基于AKShare的股票数据MCP服务器，使用FastMCP框架构建。
重构后的版本具有更好的可维护性和扩展性。
"""

import akshare as ak
import pandas as pd
from fastmcp import FastMCP
import datetime
import urllib3
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass
from functools import wraps
import logging

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置类
@dataclass
class MCPConfig:
    """MCP服务器配置"""
    max_data_rows: int = 50
    default_timeout: int = 30
    service_name: str = "AKShare股票数据服务"
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = ["akshare>=1.16.76"]

# 全局配置实例
config = MCPConfig()

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPToolRegistry:
    """MCP工具注册器"""
    
    def __init__(self, mcp_instance: FastMCP):
        self.mcp = mcp_instance
        self.tools = {}
        
    def register_tool(self, 
                     category: str = "default",
                     name: Optional[str] = None,
                     description: Optional[str] = None):
        """工具注册装饰器"""
        def decorator(func: Callable):
            tool_name = name or func.__name__
            tool_description = description or func.__doc__ or ""
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self._execute_with_error_handling(func, *args, **kwargs)
            
            # 注册到FastMCP
            try:
                mcp_tool = self.mcp.tool()(wrapper)
            except Exception as e:
                logger.error(f"Failed to register tool {tool_name}: {e}")
                return func
            
            # 保存到内部注册表
            if category not in self.tools:
                self.tools[category] = {}
            self.tools[category][tool_name] = {
                'func': wrapper,
                'description': tool_description,
                'original_func': func
            }
            
            return wrapper
        return decorator
    
    def _execute_with_error_handling(self, func: Callable, *args, **kwargs) -> Dict[str, Any]:
        """统一的错误处理执行器"""
        try:
            result = func(*args, **kwargs)
            return self._process_result(result, func.__name__)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            return {"success": False, "error": str(e), "function": func.__name__}
    
    def _process_result(self, result: Any, func_name: str) -> Dict[str, Any]:
        """统一的结果处理器"""
        if isinstance(result, pd.DataFrame):
            if result.empty:
                return {
                    "success": True,
                    "count": 0,
                    "total_count": 0,
                    "data": [],
                    "function": func_name,
                    "message": "No data available"
                }
            limited_result = result.head(config.max_data_rows)
            return {
                "success": True,
                "count": len(limited_result),
                "total_count": len(result),
                "data": limited_result.to_dict(orient="records"),
                "function": func_name
            }
        elif isinstance(result, dict):
            return {
                "success": True,
                "data": result,
                "function": func_name
            }
        elif isinstance(result, list):
            limited_result = result[:config.max_data_rows]
            return {
                "success": True,
                "count": len(limited_result),
                "total_count": len(result),
                "data": limited_result,
                "function": func_name
            }
        else:
            return {
                "success": True,
                "data": result,
                "function": func_name
            }

class AKShareDataProvider:
    """AKShare数据提供器"""
    
    @staticmethod
    def get_stock_data(symbol: str, **kwargs) -> pd.DataFrame:
        """获取股票基础数据"""
        try:
            return ak.stock_zh_a_hist(symbol=symbol, **kwargs)
        except Exception as e:
            logger.error(f"Failed to get stock data for {symbol}: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def get_stock_realtime(symbol: str) -> dict:
        """获取股票实时数据"""
        try:
            return ak.stock_bid_ask_em(symbol=symbol)
        except Exception as e:
            logger.error(f"Failed to get realtime data for {symbol}: {e}")
            return {}

class NewsDataProvider:
    """新闻数据提供器"""
    
    @staticmethod
    def get_cls_telegraph() -> List[Dict[str, Any]]:
        """获取财联社电报数据"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            url = "https://www.cls.cn/telegraph"
            response = requests.get(url, headers=headers, timeout=config.default_timeout, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            telegraph_boxes = soup.find_all(class_='telegraph-content-box')
            
            results = []
            for i, box in enumerate(telegraph_boxes):
                try:
                    time_element = box.find(class_='telegraph-time-box')
                    content_element = box.find('span', class_='c-34304b')
                    
                    if time_element and content_element:
                        results.append({
                            'index': i,
                            'time': time_element.get_text(strip=True),
                            'content': content_element.get_text(strip=True),
                        })
                except Exception as e:
                    logger.warning(f"Failed to parse telegraph item {i}: {e}")
                    continue
            
            return results
        except Exception as e:
            logger.error(f"获取财联社数据失败: {e}")
            return []

# 创建MCP服务器实例
mcp = FastMCP(config.service_name, dependencies=config.dependencies)
registry = MCPToolRegistry(mcp)

# 数据提供器实例
akshare_provider = AKShareDataProvider()
news_provider = NewsDataProvider()

# ==================== 基础工具 ====================
@registry.register_tool(category="basic", description="获取当前时间")
def get_current_time() -> dict:
    """获取当前时间"""
    return {"current_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

# ==================== 股票行情工具 ====================
@registry.register_tool(category="stock_quote", description="获取A股分时行情数据")
def stock_bid_ask_em(symbol: str) -> dict:
    """获取A股分时行情数据
    
    Args:
        symbol: 股票代码，如"000001"
    """
    return akshare_provider.get_stock_realtime(symbol)

@registry.register_tool(category="stock_quote", description="获取风险警示板股票行情")
def stock_zh_a_st_em() -> dict:
    """获取风险警示板股票行情数据"""
    return ak.stock_zh_a_st_em()

@registry.register_tool(category="stock_quote", description="获取新股板块股票行情")
def stock_zh_a_new_em() -> dict:
    """获取新股板块股票行情数据"""
    return ak.stock_zh_a_new_em()

# ==================== 新闻资讯工具 ====================
@registry.register_tool(category="news", description="获取财联社电报详细信息")
def cls_telegraph_detailed() -> dict:
    """获取财联社电报详细信息"""
    return news_provider.get_cls_telegraph()

@registry.register_tool(category="news", description="获取个股新闻资讯")
def stock_news_em(symbol: str) -> dict:
    """获取个股新闻资讯数据
    
    Args:
        symbol: 股票代码或关键词，如"300059"
    """
    return ak.stock_news_em(symbol=symbol)

@registry.register_tool(category="news", description="获取财新网财经内容精选数据")
def stock_news_main_cx() -> dict:
    """获取财新网财经内容精选数据"""
    try:
        return ak.stock_news_main_cx()
    except Exception as e:
        logger.error(f"Failed to get Caixin news: {e}")
        return {"error": str(e)}

@registry.register_tool(category="news", description="获取财联社消息")
def stock_info_global_cls() -> dict:
    """获取财联社消息"""
    try:
        return ak.stock_info_global_cls()
    except Exception as e:
        logger.error(f"Failed to get CLS global info: {e}")
        return {"error": str(e)}

@registry.register_tool(category="news", description="获取新浪财经全球财经快讯")
def stock_info_global_sina(symbol: str = "") -> dict:
    """获取新浪财经全球财经快讯
    
    Args:
        symbol: 占位符参数，保持接口一致性
    """
    try:
        return ak.stock_info_global_sina()
    except Exception as e:
        logger.error(f"Failed to get Sina global news: {e}")
        return {"error": str(e)}

# ==================== 市场统计工具 ====================
@registry.register_tool(category="market_stats", description="获取上海证券交易所股票数据总貌")
def stock_sse_summary() -> dict:
    """获取上海证券交易所-股票数据总貌"""
    return ak.stock_sse_summary()

@registry.register_tool(category="market_stats", description="获取深圳证券交易所证券类别统计")
def stock_szse_summary(date: str) -> dict:
    """获取深圳证券交易所-市场总貌-证券类别统计
    
    Args:
        date: 统计日期，格式为YYYYMMDD，如"20200619"
    """
    return ak.stock_szse_summary(date=date)

@registry.register_tool(category="market_stats", description="获取深圳证券交易所地区交易排序")
def stock_szse_area_summary(date: str) -> dict:
    """获取深圳证券交易所-市场总貌-地区交易排序
    
    Args:
        date: 统计年月，格式为YYYYMM，如"202203"
    """
    return ak.stock_szse_area_summary(date=date)

@registry.register_tool(category="market_stats", description="获取深圳证券交易所股票行业成交数据")
def stock_szse_industry_summary(date: str) -> dict:
    """获取深圳证券交易所-市场总貌-股票行业成交数据
    
    Args:
        date: 统计日期，格式为YYYYMMDD，如"20200619"
    """
    return ak.stock_szse_industry_summary(date=date)

# ==================== 历史数据工具 ====================
@registry.register_tool(category="historical", description="获取美股历史行情数据")
def stock_us_hist(symbol: str, period: str = "daily", 
                  start_date: str = "", end_date: str = "", 
                  adjust: str = "") -> dict:
    """获取美股历史行情数据
    
    Args:
        symbol: 美股代码
        period: 时间周期，可选值: 'daily', 'weekly', 'monthly'
        start_date: 开始日期，格式为YYYYMMDD
        end_date: 结束日期，格式为YYYYMMDD
        adjust: 复权类型，可选值: "", "qfq", "hfq"
    """
    return ak.stock_us_hist(symbol=symbol, period=period, 
                           start_date=start_date, end_date=end_date, 
                           adjust=adjust)

# ==================== 工具管理功能 ====================
@registry.register_tool(category="meta", description="获取所有可用工具列表")
def list_available_tools() -> dict:
    """获取所有可用工具列表，按类别分组"""
    tools_by_category = {}
    for category, tools in registry.tools.items():
        tools_by_category[category] = {
            name: info['description'] 
            for name, info in tools.items()
        }
    return tools_by_category

def main():
    """主函数"""
    logger.info(f"启动 {config.service_name}")
    logger.info(f"已注册 {sum(len(tools) for tools in registry.tools.values())} 个工具")
    mcp.run()

if __name__ == "__main__":
    main()
