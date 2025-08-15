# neutus-ts/example_usage.py

import sys
import os
from datetime import datetime
from reuters_client import (
    ReutersClient, 
    ApiError, 
    RedirectError, 
    ExternalError, 
    InternalError
)


def print_separator(title: str):
    """打印分隔符"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def print_article(article, index=None):
    """打印文章信息"""
    prefix = f"[{index}] " if index is not None else ""
    print(f"{prefix}标题: {article.title}")
    print(f"    URL: {article.canonical_url}")
    print(f"    描述: {article.description[:100]}..." if len(article.description) > 100 else f"    描述: {article.description}")
    print(f"    发布时间: {article.published_time}")
    print(f"    子类型: {article.subtype}")
    
    if article.authors:
        authors = [author.name for author in article.authors]
        print(f"    作者: {', '.join(authors)}")
    
    if article.thumbnail:
        print(f"    缩略图: {article.thumbnail.resizer_url}")
        if article.thumbnail.caption:
            print(f"    图片说明: {article.thumbnail.caption}")
    
    print("-" * 40)


def print_topic(topic, index=None):
    """打印主题信息"""
    prefix = f"[{index}] " if index is not None else ""
    print(f"{prefix}主题: {topic.name}")
    print(f"    URL: {topic.topic_url}")
    print(f"    副标题: {topic.byline}")
    print("-" * 40)


def print_section(section, level=0):
    """递归打印分类信息"""
    indent = "  " * level
    print(f"{indent}- {section.name} (ID: {section.id})")
    
    if section.children:
        for child in section.children:
            print_section(child, level + 1)


def test_search_articles(client):
    """测试搜索文章功能"""
    print_separator("测试搜索文章功能")
    
    keywords = ["technology", "artificial intelligence", "stock market", "climate change"]
    
    for keyword in keywords:
        try:
            print(f"\n🔍 搜索关键词: '{keyword}'")
            search_results = client.search_articles(keyword, size=3)
            
            print(f"📊 找到 {search_results.pagination.total_size} 篇文章")
            
            if search_results.articles:
                print(f"📝 显示前 {len(search_results.articles)} 篇:")
                for i, article in enumerate(search_results.articles, 1):
                    print_article(article, i)
            else:
                print("❌ 没有找到文章")
                
            # 测试分页
            if search_results.pagination.total_size and search_results.pagination.total_size > 3:
                print(f"\n📄 测试分页 - 获取第二页:")
                page2_results = client.search_articles(keyword, offset=3, size=2)
                if page2_results.articles:
                    for i, article in enumerate(page2_results.articles, 1):
                        print_article(article, f"第二页-{i}")
                        
        except ApiError as e:
            print(f"❌ 搜索 '{keyword}' 时出错: {e}")
        except Exception as e:
            print(f"❌ 意外错误: {e}")

# 获取的是指数
def test_stock_symbol_articles(client):
    """测试按股票代码获取文章功能"""
    print_separator("测试按股票代码获取文章功能")
    
    # 分为两组：常见股票和可能不存在的股票
    common_stocks = [".DJI", ".IXIC", '.HSI']
    test_stocks = [".DJI", ".HSI"]  # 用于测试的股票
    
    # 首先测试一个常见股票，启用调试模式
    print("\n🔍 调试模式 - 测试.DJI:")
    try:
        # 临时启用调试模式
        client_debug = ReutersClient(timeout=30)
        # 修改_make_request为支持调试的版本
        original_method = client_debug._make_request
        
        def debug_make_request(url, query):
            return original_method(url, query, debug=True)
        
        client_debug._make_request = debug_make_request
        
        stock_articles = client_debug.fetch_articles_by_stock_symbol(".DJI")
        print(f"✅ 调试测试成功，找到 {len(stock_articles)} 篇文章")
        
    except Exception as e:
        print(f"❌ 调试测试失败: {e}")
    
    # 然后正常测试所有股票
    for symbol in common_stocks:
        try:
            print(f"\n📈 股票代码: {symbol}")
            stock_articles = client.fetch_articles_by_stock_symbol(symbol)
            
            print(f"📊 找到 {len(stock_articles)} 篇相关文章")
            
            if stock_articles:
                print(f"📝 显示前 3 篇:")
                for i, article in enumerate(stock_articles[:3], 1):
                    print_article(article, i)
            else:
                print("❌ 没有找到相关文章")
                
        except ApiError as e:
            print(f"❌ 获取 {symbol} 文章时出错: {e}")
            
            # 如果是404错误，提供更多信息
            if isinstance(e, ExternalError) and e.status_code == 404:
                print(f"💡 提示: 股票代码 {symbol} 可能不存在或API端点已更改")
                print(f"💡 建议: 检查股票代码是否正确，或尝试其他股票代码")
                
        except Exception as e:
            print(f"❌ 意外错误: {e}")


# 添加专门的股票API测试函数
def test_stock_api_endpoints(client):
    """测试股票API端点的可用性"""
    print_separator("测试股票API端点可用性")
    
    # 测试不同的API端点和参数组合
    test_cases = [
        {
            "name": "原始参数格式",
            "query": '{"website":"reuters","symbol":".DJI","arc-site":"reuters"}'
        },
        {
            "name": "简化参数格式", 
            "query": '{"symbol":".DJI"}'
        },
        {
            "name": "不同顺序参数",
            "query": '{"arc-site":"reuters","symbol":".DJI","website":"reuters"}'
        }
    ]
    
    url = "https://www.reuters.com/pf/api/v3/content/fetch/articles-by-stock-symbol-v1"
    
    for case in test_cases:
        try:
            print(f"\n🧪 测试: {case['name']}")
            print(f"📝 查询: {case['query']}")
            
            response = client.session.get(
                url,
                params={'query': case['query']},
                timeout=client.timeout
            )
            
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    result = data.get('result', {})
                    articles = result.get('articles', [])
                    print(f"✅ 成功获取 {len(articles)} 篇文章")
                except:
                    print(f"❌ JSON解析失败")
            else:
                print(f"❌ 请求失败: {response.text[:200]}...")
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")


def test_article_by_url(client):
    """测试通过URL获取文章功能"""
    print_separator("测试通过URL获取文章功能")
    
    # 先搜索一些文章获取URL
    try:
        search_results = client.search_articles("technology", size=3)
        
        if search_results.articles:
            for i, article in enumerate(search_results.articles, 1):
                if article.canonical_url:
                    try:
                        print(f"\n🔗 测试获取文章 {i}: {article.canonical_url}")
                        
                        # 从完整URL提取路径
                        url_path = article.canonical_url.replace('https://www.reuters.com', '')
                        if not url_path.startswith('/'):
                            url_path = '/' + url_path
                            
                        detailed_article = client.fetch_article_by_url(url_path)
                        
                        print("✅ 成功获取文章详情:")
                        print_article(detailed_article)
                        
                        # 显示内容元素
                        if detailed_article.content_elements:
                            print(f"📄 内容元素数量: {len(detailed_article.content_elements)}")
                            for j, element in enumerate(detailed_article.content_elements[:2]):
                                print(f"    元素 {j+1}: {element.get('type', 'unknown')} - {str(element)[:100]}...")
                        
                        break  # 只测试第一个有效URL
                        
                    except ApiError as e:
                        print(f"❌ 获取文章详情时出错: {e}")
                    except Exception as e:
                        print(f"❌ 意外错误: {e}")
        else:
            print("❌ 没有找到可测试的文章URL")
            
    except Exception as e:
        print(f"❌ 搜索文章失败: {e}")


def test_topic_articles(client):
    """测试按主题获取文章功能"""
    print_separator("测试按主题获取文章功能")
    
    # 首先测试网站层级结构来获取真实的主题路径
    print("🔍 首先获取网站层级结构来查找有效主题...")
    try:
        hierarchy = client.fetch_site_hierarchy()
        valid_topics = []
        
        def find_topics(section, level=0):
            if hasattr(section, 'children') and section.children:
                for child in section.children:
                    # 查找可能的主题相关分类
                    if any(keyword in child.name.lower() for keyword in ['tech', 'business', 'market', 'world']):
                        topic_path = f"/topic/{child.name.lower().replace(' ', '-')}"
                        valid_topics.append((child.name, topic_path))
                        if len(valid_topics) >= 3:  # 限制数量
                            return
                    find_topics(child, level + 1)
        
        find_topics(hierarchy)
        print(f"✅ 发现 {len(valid_topics)} 个可能的主题")
        
    except Exception as e:
        print(f"⚠️  无法获取层级结构: {e}")
        valid_topics = []
    
    # 使用预定义的主题路径作为备选
    fallback_topics = [
        ("Fintech", "/topic/fintech"),
        ("Technology", "/topic/technology"), 
        ("Markets", "/topic/markets"),
        ("Business", "/topic/business"),
        ("World News", "/topic/world")
    ]
    
    # 合并主题列表
    all_topics = valid_topics + fallback_topics
    
    # 测试每个主题
    for topic_name, topic_path in all_topics[:5]:  # 限制测试数量
        try:
            print(f"\n🏷️  主题: {topic_name} (路径: {topic_path})")
            
            # 启用调试模式来查看请求详情
            debug_client = ReutersClient(timeout=30)
            original_method = debug_client._make_request
            
            def debug_make_request(url, query, debug=False, extra_params=None):
                return original_method(url, query, debug=True, extra_params=extra_params)
            
            debug_client._make_request = debug_make_request
            
            topic_results = debug_client.fetch_articles_by_topic(topic_path, size=3)
            
            print(f"📊 找到 {topic_results.pagination.total_size} 篇文章")
            
            if topic_results.articles:
                print(f"📝 显示前 {len(topic_results.articles)} 篇:")
                for i, article in enumerate(topic_results.articles, 1):
                    print_article(article, i)
            
            if topic_results.topics:
                print(f"🏷️  相关主题 ({len(topic_results.topics)} 个):")
                for i, topic in enumerate(topic_results.topics, 1):
                    print_topic(topic, i)
            
            # 如果成功，就跳出循环
            if topic_results.articles:
                break
                    
        except ApiError as e:
            print(f"❌ 获取主题 '{topic_path}' 文章时出错: {e}")
            
            # 尝试不同的主题路径格式
            if "/topic/" in topic_path:
                alt_path = topic_path.replace("/topic/", "/")
                try:
                    print(f"🔄 尝试替代路径: {alt_path}")
                    topic_results = client.fetch_articles_by_topic(alt_path, size=3)
                    print(f"✅ 替代路径成功！找到 {topic_results.pagination.total_size} 篇文章")
                    if topic_results.articles:
                        for i, article in enumerate(topic_results.articles[:2], 1):
                            print_article(article, i)
                        break
                except Exception as alt_e:
                    print(f"❌ 替代路径也失败: {alt_e}")
                    
        except Exception as e:
            print(f"❌ 意外错误: {e}")
    
    # 如果所有主题都失败，尝试通过搜索获取主题相关文章
    print("\n🔍 备选方案：通过搜索获取主题相关文章")
    try:
        search_results = client.search_articles("fintech technology", size=3)
        if search_results.articles:
            print(f"✅ 通过搜索找到 {len(search_results.articles)} 篇相关文章:")
            for i, article in enumerate(search_results.articles, 1):
                print_article(article, i)
    except Exception as e:
        print(f"❌ 搜索备选方案也失败: {e}")


# 添加新的测试函数来专门调试主题API
def test_topic_api_debug(client):
    """调试主题API的详细测试"""
    print_separator("调试主题API详细测试")
    
    # 测试不同的主题API格式
    test_cases = [
        {
            "name": "标准主题格式",
            "url": "https://www.reuters.com/pf/api/v3/content/fetch/articles-by-topic-v1",
            "query": '{"topic_url":"/topic/technology","website":"reuters","size":3,"offset":0}'
        },
        {
            "name": "简化主题格式",
            "url": "https://www.reuters.com/pf/api/v3/content/fetch/articles-by-topic-v1", 
            "query": '{"topic_url":"/technology","website":"reuters","size":3}'
        },
        {
            "name": "分类格式",
            "url": "https://www.reuters.com/pf/api/v3/content/fetch/recent-stories-by-sections-v1",
            "query": '{"section_ids":"technology","website":"reuters","size":3,"offset":0}'
        }
    ]
    
    for case in test_cases:
        try:
            print(f"\n🧪 测试: {case['name']}")
            print(f"📝 URL: {case['url']}")
            print(f"📝 查询: {case['query']}")
            
            response = client.session.get(
                case['url'],
                params={'query': case['query']},
                timeout=client.timeout
            )
            
            print(f"📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ JSON解析成功")
                    
                    result = data.get('result', {})
                    if 'articles' in result:
                        articles = result['articles']
                        print(f"✅ 找到 {len(articles)} 篇文章")
                    elif 'pagination' in result:
                        pagination = result.get('pagination', {})
                        total = pagination.get('total_size', 0)
                        print(f"✅ 分页信息显示总共 {total} 篇文章")
                    else:
                        print(f"⚠️  响应结构: {list(result.keys())}")
                        
                except Exception as json_e:
                    print(f"❌ JSON解析失败: {json_e}")
                    print(f"📄 原始响应: {response.text[:300]}...")
            else:
                print(f"❌ 请求失败")
                print(f"📄 错误响应: {response.text[:300]}...")
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")


def test_error_handling(client):
    """测试错误处理功能"""
    print_separator("测试错误处理功能")
    
    # 测试无效股票代码
    print("\n🧪 测试无效股票代码:")
    try:
        invalid_articles = client.fetch_articles_by_stock_symbol("INVALID_SYMBOL_123")
        print(f"📊 结果: {len(invalid_articles)} 篇文章")
    except ApiError as e:
        print(f"✅ 正确捕获API错误: {e}")
    except Exception as e:
        print(f"❌ 意外错误: {e}")
    
    # 测试无效URL
    print("\n🧪 测试无效URL:")
    try:
        invalid_article = client.fetch_article_by_url("/invalid/url/path")
        print("❌ 应该抛出错误但没有")
    except ApiError as e:
        print(f"✅ 正确捕获API错误: {e}")
    except Exception as e:
        print(f"❌ 意外错误: {e}")
    
    # 测试空搜索
    print("\n🧪 测试空搜索:")
    try:
        empty_results = client.search_articles("", size=1)
        print(f"📊 空搜索结果: {empty_results.pagination.total_size}")
    except ApiError as e:
        print(f"✅ 正确捕获API错误: {e}")
    except Exception as e:
        print(f"❌ 意外错误: {e}")


def run_comprehensive_test():
    """运行完整测试"""
    print("🚀 开始 Reuters API 客户端完整功能测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 创建客户端实例
    client = ReutersClient(timeout=30)
    
    try:
        # 执行所有测试
        test_search_articles(client)
        test_stock_symbol_articles(client)
        test_article_by_url(client)
        test_topic_articles(client)
        test_section_articles(client)
        test_site_hierarchy(client)
        test_error_handling(client)
        test_stock_api_endpoints(client)
        
        print_separator("测试完成")
        print("✅ 所有功能测试完成!")
        print(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except KeyboardInterrupt:
        print("\n❌ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生意外错误: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数 - 提供交互式菜单"""
    while True:
        print("\n" + "="*50)
        print("📰 Reuters API 客户端测试菜单")
        print("="*50)       
        print("1. 🔍 测试搜索文章功能")
        print("2. 📈 测试股票代码文章功能")
        print("3. 🔗 测试URL获取文章功能")
        print("4. 🏷️  测试主题文章功能")
        print("5. 📂 测试分类文章功能")
        print("6. 🌐 测试网站层级结构功能")
        print("7. 🧪 测试错误处理功能")
        print("8. 🔧 测试股票API端点可用性")
        print("9. 🔍 调试主题API详细测试")  # 新增
        print("10. 🚀 运行完整测试")
        print("0. 🚪 退出")
        print("-" * 50)
        
        choice = input("请选择功能 (0-10): ").strip()
        
        if choice == "0":
            print("👋 再见!")
            break
        elif choice == "1":
            test_search_articles(ReutersClient())
        elif choice == "2":
            test_stock_symbol_articles(ReutersClient())
        elif choice == "3":
            test_article_by_url(ReutersClient())
        elif choice == "4":
            test_topic_articles(ReutersClient())
        elif choice == "5":
            test_section_articles(ReutersClient())
        elif choice == "6":
            test_site_hierarchy(ReutersClient())
        elif choice == "7":
            test_error_handling(ReutersClient())
        elif choice == "8":
            test_stock_api_endpoints(ReutersClient())
        elif choice == "9":
            test_topic_api_debug(ReutersClient())  # 新增
        elif choice == "10":
            run_comprehensive_test()
        else:
            print("❌ 无效选择，请重新输入")


if __name__ == "__main__":
    # 检查是否传入了命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == "--full":
            run_comprehensive_test()
        elif sys.argv[1] == "--help":
            print("使用方法:")
            print("  python example_usage.py          # 交互式菜单")
            print("  python example_usage.py --full   # 运行完整测试")
            print("  python example_usage.py --help   # 显示帮助")
        else:
            print(f"❌ 未知参数: {sys.argv[1]}")
            print("使用 --help 查看帮助")
    else:
        main()