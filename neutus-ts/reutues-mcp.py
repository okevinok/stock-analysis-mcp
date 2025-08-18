#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Reuters MCP Server

这是一个基于Reuters API的新闻数据MCP服务器，使用FastMCP框架构建。
它提供了对Reuters新闻数据的访问，通过MCP协议暴露Reuters API。
"""

import sys
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd

# 添加当前目录到Python路径，以便导入reuters_client
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from reuters_client import (
    ReutersClient, 
    ApiError, 
    RedirectError, 
    ExternalError, 
    InternalError,
    Article,
    Articles,
    Topic,
    Section
)

from fastmcp import FastMCP

# 限制返回的最大数据行数
MAX_DATA_ROW = 50

# 创建MCP服务器实例
mcp = FastMCP("Reuters新闻数据服务", dependencies=["requests>=2.25.0"])

# 创建全局Reuters客户端实例
reuters_client = ReutersClient(timeout=30)

# 通用的数据处理函数
def process_articles_result(articles: List[Article], description: str = "articles") -> dict:
    """处理文章列表结果，确保返回正确的字典格式"""
    try:
        # 限制返回的文章数量
        limited_articles = articles[:min(MAX_DATA_ROW, len(articles))]
        
        # 将Article对象转换为字典
        articles_data = []
        for article in limited_articles:
            article_dict = {
                "title": article.title,
                "canonical_url": article.canonical_url,
                "description": article.description,
                "published_time": article.published_time,
                "subtype": article.subtype,
                "authors": [{"name": author.name, "topic_url": author.topic_url, "byline": author.byline} 
                           for author in article.authors] if article.authors else [],
                "thumbnail": {
                    "caption": article.thumbnail.caption,
                    "width": article.thumbnail.width,
                    "height": article.thumbnail.height,
                    "resizer_url": article.thumbnail.resizer_url
                } if article.thumbnail else None
            }
            articles_data.append(article_dict)
        
        return {
            "success": True,
            "count": len(limited_articles),
            "total_count": len(articles),
            description: articles_data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            description: []
        }

def process_articles_with_pagination_result(articles_result: Articles, description: str = "articles") -> dict:
    """处理带分页的文章结果"""
    try:
        articles_data = []
        
        if articles_result.articles:
            # 限制返回的文章数量
            limited_articles = articles_result.articles[:min(MAX_DATA_ROW, len(articles_result.articles))]
            
            # 将Article对象转换为字典
            for article in limited_articles:
                article_dict = {
                    "title": article.title,
                    "canonical_url": article.canonical_url,
                    "description": article.description,
                    "published_time": article.published_time,
                    "subtype": article.subtype,
                    "authors": [{"name": author.name, "topic_url": author.topic_url, "byline": author.byline} 
                               for author in article.authors] if article.authors else [],
                    "thumbnail": {
                        "caption": article.thumbnail.caption,
                        "width": article.thumbnail.width,
                        "height": article.thumbnail.height,
                        "resizer_url": article.thumbnail.resizer_url
                    } if article.thumbnail else None
                }
                articles_data.append(article_dict)
        
        # 处理主题信息
        topics_data = []
        if articles_result.topics:
            for topic in articles_result.topics:
                topic_dict = {
                    "name": topic.name,
                    "topic_url": topic.topic_url,
                    "byline": topic.byline
                }
                topics_data.append(topic_dict)
        
        return {
            "success": True,
            "count": len(articles_data),
            "total_count": articles_result.pagination.total_size,
            "pagination": {
                "total_size": articles_result.pagination.total_size
            },
            description: articles_data,
            "topics": topics_data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            description: [],
            "topics": []
        }

# 工具函数：获取当前时间
@mcp.tool()
def mcp_get_current_time() -> dict:
    """获取当前时间
    
    获取当前时间数据
    
    Returns:
        dict: 包含当前时间的字典
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {"current_time": current_time}

# 工具函数：搜索Reuters文章
@mcp.tool()
def mcp_search_articles(keyword: str, offset: int = 0, size: int = 20) -> dict:
    """按关键词搜索Reuters文章
    
    数据来源: Reuters API - 文章搜索
    
    Args:
        keyword: 搜索关键词，如"technology"、"artificial intelligence"等
        offset: 偏移量，用于分页，默认0
        size: 返回文章数量，默认20，最大50
        
    Returns:
        dict: 包含搜索结果的字典，包括文章列表、分页信息等
    """
    try:
        # 限制size的最大值
        size = min(size, MAX_DATA_ROW)
        
        search_results = reuters_client.search_articles(keyword=keyword, offset=offset, size=size)
        return process_articles_with_pagination_result(search_results, "search_results")
    except ApiError as e:
        return {
            "success": False,
            "error": f"Reuters API错误: {str(e)}",
            "search_results": []
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"搜索失败: {str(e)}",
            "search_results": []
        }

# 工具函数：通过URL获取文章详情
@mcp.tool()
def mcp_article_by_url(article_path: str) -> dict:
    """通过URL路径获取文章详情
    
    数据来源: Reuters API - 文章详情
    
    Args:
        article_path: 文章URL路径，如"/business/energy/oil-prices-rise-2024-01-15/"
        
    Returns:
        dict: 包含文章详情的字典，包括完整内容、作者信息等
    """
    try:
        article = reuters_client.fetch_article_by_url(article_path)
        
        # 将单个Article对象转换为字典
        article_dict = {
            "title": article.title,
            "canonical_url": article.canonical_url,
            "description": article.description,
            "published_time": article.published_time,
            "subtype": article.subtype,
            "authors": [{"name": author.name, "topic_url": author.topic_url, "byline": author.byline} 
                       for author in article.authors] if article.authors else [],
            "thumbnail": {
                "caption": article.thumbnail.caption,
                "width": article.thumbnail.width,
                "height": article.thumbnail.height,
                "resizer_url": article.thumbnail.resizer_url
            } if article.thumbnail else None,
            "content_elements": article.content_elements[:10] if article.content_elements else []  # 限制内容元素数量
        }
        
        return {
            "success": True,
            "article_detail": article_dict
        }
    except ApiError as e:
        return {
            "success": False,
            "error": f"Reuters API错误: {str(e)}",
            "article_detail": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"获取文章详情失败: {str(e)}",
            "article_detail": None
        }

# 工具函数：多关键词搜索（高级搜索）
@mcp.tool()
def mcp_advanced_search(keywords: List[str], max_results_per_keyword: int = 10) -> dict:
    """多关键词高级搜索
    
    对多个关键词分别进行搜索并合并结果
    
    Args:
        keywords: 关键词列表，如["technology", "AI", "blockchain"]
        max_results_per_keyword: 每个关键词的最大结果数，默认10
        
    Returns:
        dict: 包含所有关键词搜索结果的合并字典
    """
    try:
        all_results = []
        search_summary = []
        
        # 限制关键词数量和每个关键词的结果数
        keywords = keywords[:5]  # 最多5个关键词
        max_results_per_keyword = min(max_results_per_keyword, 10)
        
        for keyword in keywords:
            try:
                search_results = reuters_client.search_articles(keyword=keyword, size=max_results_per_keyword)
                
                keyword_summary = {
                    "keyword": keyword,
                    "total_found": search_results.pagination.total_size,
                    "returned_count": len(search_results.articles) if search_results.articles else 0
                }
                search_summary.append(keyword_summary)
                
                if search_results.articles:
                    for article in search_results.articles:
                        article_dict = {
                            "search_keyword": keyword,  # 标记来源关键词
                            "title": article.title,
                            "canonical_url": article.canonical_url,
                            "description": article.description,
                            "published_time": article.published_time,
                            "subtype": article.subtype,
                            "authors": [{"name": author.name, "topic_url": author.topic_url} 
                                       for author in article.authors] if article.authors else []
                        }
                        all_results.append(article_dict)
                        
            except Exception as e:
                keyword_summary = {
                    "keyword": keyword,
                    "error": str(e),
                    "total_found": 0,
                    "returned_count": 0
                }
                search_summary.append(keyword_summary)
        
        return {
            "success": True,
            "search_summary": search_summary,
            "total_articles_found": len(all_results),
            "combined_results": all_results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"高级搜索失败: {str(e)}",
            "combined_results": []
        }

# 工具函数：热门主题文章聚合
@mcp.tool()
def mcp_trending_topics(topics: List[str] = None, articles_per_topic: int = 5) -> dict:
    """获取热门主题的文章聚合
    
    Args:
        topics: 主题列表，如果为None则使用默认热门主题
        articles_per_topic: 每个主题的文章数量，默认5
        
    Returns:
        dict: 包含各主题文章的聚合结果
    """
    try:
        # 默认热门主题
        if topics is None:
            topics = ["technology", "artificial intelligence", "cryptocurrency", "climate change", "electric vehicles"]
        
        # 限制主题数量和每个主题的文章数
        topics = topics[:5]
        articles_per_topic = min(articles_per_topic, 10)
        
        trending_results = {}
        
        for topic in topics:
            try:
                # 先尝试作为搜索关键词
                search_results = reuters_client.search_articles(keyword=topic, size=articles_per_topic)
                
                topic_articles = []
                if search_results.articles:
                    for article in search_results.articles:
                        article_dict = {
                            "title": article.title,
                            "canonical_url": article.canonical_url,
                            "description": article.description[:200] + "..." if len(article.description) > 200 else article.description,
                            "published_time": article.published_time
                        }
                        topic_articles.append(article_dict)
                
                trending_results[topic] = {
                    "total_available": search_results.pagination.total_size,
                    "articles_returned": len(topic_articles),
                    "articles": topic_articles
                }
                
            except Exception as e:
                trending_results[topic] = {
                    "error": str(e),
                    "articles": []
                }
        
        return {
            "success": True,
            "trending_topics": trending_results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"获取热门主题失败: {str(e)}",
            "trending_topics": {}
        }


@mcp.tool()
def cls_telegram():
    """ 获取财联社实时电报 """
    # https://www.cls.cn/telegraph
    


def main():
    """主函数"""
    print("🚀 启动 Reuters MCP 服务器...")
    print("📰 可用功能:")
    print("  - mcp_search_articles: 搜索文章")
    print("  - mcp_stock_articles: 获取股票相关文章")
    print("  - mcp_topic_articles: 获取主题文章")
    print("  - mcp_section_articles: 获取分类文章")
    print("  - mcp_article_by_url: 获取文章详情")
    print("  - mcp_site_hierarchy: 获取网站结构")
    print("  - mcp_advanced_search: 高级多关键词搜索")
    print("  - mcp_trending_topics: 热门主题聚合")
    print("  - mcp_get_current_time: 获取当前时间")
    
    try:
        mcp.run()
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")

if __name__ == "__main__":
    main()