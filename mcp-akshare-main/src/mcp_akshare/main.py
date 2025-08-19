#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AKShare MCP Server - 重构版本

这是一个基于AKShare的股票数据MCP服务器，使用FastMCP框架构建。
重构后的版本具有更好的可维护性和扩展性。
"""
import os
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

# 禁用所有代理设置
proxy_env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
for var in proxy_env_vars:
    if var in os.environ:
        del os.environ[var]
        
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
    def stock_bid_ask_em(symbol: str) -> dict:
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
    return akshare_provider.stock_bid_ask_em(symbol)

@registry.register_tool(category="stock_quote", description="获取A股分时行情数据")
def get_stock_data(symbol: str) -> dict:
    """ 沪深京 A 股-每日行情
        https://quote.eastmoney.com/concept/sh603777.html?from=classic
    Args:
        symbol: 股票代码，如"000001"
        period: choice of {'daily', 'weekly', 'monthly'}
        start_date: 开始日期
        end_date: 结束日期
        adjust: choice of {"qfq": "前复权", "hfq": "后复权", "": "不复权"}
        timeout: choice of None or a positive float number
    """
    return akshare_provider.get_stock_data(symbol)

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

# 工具函数：个股资金流数据 - 修复版本
@registry.register_tool(category="stock_stats", description="获取个股资金流数据")
def stock_fund_flow_individual(symbol: str) -> dict:
    """获取个股资金流数据
    网址: https://data.10jqka.com.cn/funds/ggzjl/#refCountId=data_55f13c2c_254
    Args:
        symbol: 时间周期，可选值: 
               "即时"(默认), 
               "3日排行", 
               "5日排行", 
               "10日排行", 
               "20日排行"
    Returns:
        dict: 包含个股资金流数据的字典，包括流入流出资金、净额等
    """
    return ak.stock_fund_flow_individual(symbol=symbol)

@registry.register_tool(category="stock_stats", description=" 获取沪深港通-港股通(沪>港)-股票")
def stock_hsgt_sh_hk_spot_em() -> dict:
    """ 获取沪深港通-港股通(沪>港)-股票
    https://quote.eastmoney.com/center/gridlist.html#hk_sh_stocks
    Returns:
        dict: 包含沪深港通所有股票数据，代码,名称,最新价,涨跌额,涨跌幅,今开,最高,最低,昨收,成交量,成交额    
    """
    return ak.stock_hsgt_sh_hk_spot_em()

@registry.register_tool(category="market_stats", description=" 获取股票主力控盘与机构参与度数据")
def stock_comment_detail_zlkp_jgcyd_em(symbol: str) -> dict:
    """获取股票主力控盘与机构参与度数据
    Args:
        symbol: 股票代码，如"600000"
    Returns:
        dict: 包含主力控盘和机构参与度数据的字典，机构参与度单位为%
    """
    return ak.stock_comment_detail_zlkp_jgcyd_em(symbol=symbol)

@registry.register_tool(category="stock_stats", description=" 获取上市公司主营构成数据")
def stock_zygc_em(symbol: str) -> dict:
    """获取上市公司主营构成数据
    Args:
        symbol: 带市场标识的股票代码，如"SH688041"(上海)或"SZ000001"(深圳)
    Returns:
        dict: 包含公司主营构成数据的字典，包括收入、成本、利润及比例等财务指标
    """
    return ak.stock_zygc_em(symbol=symbol)

@registry.register_tool(category="stock_quote", description=" 获取港股分时行情数据")
def stock_hk_hist_min_em(symbol: str, period: str = "5", adjust: str = "", 
                        start_date: str = "1979-09-01 09:32:00", 
                        end_date: str = "2222-01-01 09:32:00") -> dict:
    """获取港股分时行情数据
    Args:
        symbol: 港股代码(可通过ak.stock_hk_spot_em()获取)，如"01611"
        period: 时间周期，可选值: '1'(1分钟), '5'(5分钟), '15'(15分钟), '30'(30分钟), '60'(60分钟)
        adjust: 复权类型，可选值: 
               ""(默认): 不复权
               "qfq": 前复权
               "hfq": 后复权
        start_date: 开始日期时间，格式为"YYYY-MM-DD HH:MM:SS"，默认"1979-09-01 09:32:00"
        end_date: 结束日期时间，格式为"YYYY-MM-DD HH:MM:SS"，默认"2222-01-01 09:32:00"
    Returns:
        dict: 包含港股分时行情数据的字典，包括时间、价格、成交量等
    """
    return ak.stock_hk_hist_min_em(symbol=symbol, period=period, adjust=adjust,
                                       start_date=start_date, end_date=end_date)

@registry.register_tool(category="stock_quote", description=" 获取美股分时行情数据")
def stock_us_hist_min_em(symbol: str, start_date: str = "1979-09-01 09:32:00", end_date: str = "2222-01-01 09:32:00") -> dict:
    """获取美股分时行情数据
    Args:
        symbol: 美股代码(可通过ak.stock_us_spot_em()获取)，如"105.ATER"
        start_date: 开始日期时间，格式为"YYYY-MM-DD HH:MM:SS"，默认"1979-09-01 09:32:00"
        end_date: 结束日期时间，格式为"YYYY-MM-DD HH:MM:SS"，默认"2222-01-01 09:32:00"
    Returns:
        dict: 包含美股分时行情数据的字典，包括时间、价格、成交量等
    """
    return ak.stock_us_hist_min_em(symbol=symbol, start_date=start_date, end_date=end_date)

@registry.register_tool(category="stock_quote", description="获取A+H股历史行情数据")
def stock_zh_ah_daily(symbol: str, start_year: str, end_year: str, adjust: str = "") -> dict:
    """获取A+H股历史行情数据
    Args:
        symbol: 港股股票代码，如"02318"(可通过ak.stock_zh_ah_name()获取)
        start_year: 开始年份，如"2000"
        end_year: 结束年份，如"2019"
        adjust: 复权类型，可选值: 
               ""(默认): 不复权
               "qfq": 前复权
               "hfq": 后复权
    Returns:
        dict: 包含A+H股历史行情数据的字典，包括日期、价格、成交量等
    """
    return ak.stock_zh_ah_daily(symbol=symbol, start_year=start_year, end_year=end_year, adjust=adjust)

# 工具函数：新股上市首日数据
@registry.register_tool(category="stock_quote", description="获取新股上市首日数据")
def stock_xgsr_ths() -> dict:
    """获取新股上市首日数据
    Returns:
        dict: 包含新股上市首日数据的字典，包括发行价、首日价格表现、涨跌幅及破发情况
    """
    return ak.stock_xgsr_ths()

@registry.register_tool(category="stock_quote", description="获取科创板股票历史行情数据")
def stock_zh_kcb_daily(symbol: str, adjust: str = "") -> dict:
    """获取科创板股票历史行情数据
    Args:
        symbol: 带市场标识的股票代码，如"sh688008"
        adjust: 复权类型，可选值: 
               ""(默认): 不复权
               "qfq": 前复权
               "hfq": 后复权
               "hfq-factor": 后复权因子
               "qfq-factor": 前复权因子
    Returns:
        dict: 包含科创板股票历史行情数据的字典，包括日期、价格、成交量等
    """
    return ak.stock_zh_kcb_daily(symbol=symbol, adjust=adjust)

@registry.register_tool(category="market_stats", description="获取深圳证券交易所-统计资料-股票行业成交数据")
def stock_szse_sector_summary(symbol: str, date: str) -> dict:
    """获取深圳证券交易所-统计资料-股票行业成交数据
    Args:
        symbol: 统计周期，可选值: "当月" 或 "当年"
        date: 统计年月，格式为YYYYMM，如"202501"
    Returns:
        dict: 包含股票行业成交数据的字典，包括交易天数、成交金额、成交股数、成交笔数等
    """
    return ak.stock_szse_sector_summary(symbol=symbol, date=date)

def main():
    """主函数"""
    logger.info(f"启动 {config.service_name}")
    logger.info(f"已注册 {sum(len(tools) for tools in registry.tools.values())} 个工具")
    mcp.run()

if __name__ == "__main__":
    main()
