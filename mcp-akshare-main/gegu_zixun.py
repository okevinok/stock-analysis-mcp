# 通用的数据处理函数
import pandas


def process_dataframe_result(result, description: str = "data"):
    """处理DataFrame结果，确保返回正确的字典格式"""
    if type(result) is pandas.core.frame.DataFrame:
        limited_result = result[:min(60, len(result))]
        return {
            "success": True,
            "count": len(limited_result),
            "total_count": len(result),
            description: limited_result.to_dict(orient="records")
        }
    elif isinstance(result, dict):
        return {
            "success": True,
            description: result
        }
    else:
        return {
            "success": True,
            description: result
        }

def xinlang_gegu_telegraph_detailed(symbol: str = "01877") -> list:
    """ 通过新浪财经抓取个股资讯数据 
    https://stock.finance.sina.com.cn/hkstock/news/01877.html
    :param symbol: 股票代码
    :return: 包含详细信息的字典列表，按时间倒序排列
    :rtype: list
    """
    import requests
    from bs4 import BeautifulSoup
    from datetime import datetime
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

        url = f"https://stock.finance.sina.com.cn/hkstock/news/{symbol}.html"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = 'GB2312'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找class为list01的ul元素
        list01_element = soup.find('ul', class_='list01')
        
        news_list = []
        
        if list01_element:
            # 查找所有li元素
            li_elements = list01_element.find_all('li')
            
            for i, li in enumerate(li_elements):
                # 查找a标签
                a_element = li.find('a')
                # 查找时间span标签
                time_element = li.find('span', class_='rt')
                
                if a_element and time_element:
                    # 提取新闻链接
                    news_url = a_element.get('href', '')
                    # 提取新闻标题（优先使用title属性，否则使用文本内容）
                    news_title = a_element.get('title', '') or a_element.get_text(strip=True)
                    # 提取时间
                    news_time = time_element.get_text(strip=True)
                    
                    # 清理标题文本
                    news_title = news_title.replace('\n', ' ').replace('\r', '').strip()
                    
                    news_item = {
                        'index': i,
                        'time': news_time,
                        'title': news_title,
                        'url': news_url,
                        'content': news_title,  # 在这个页面，标题就是主要内容
                        'full_text': news_title
                    }
                    
                    news_list.append(news_item)
        
        # 按时间倒序排列（最新的在前面）
        def parse_time(time_str):
            try:
                return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                # 如果时间格式不匹配，返回一个很早的时间作为默认值
                return datetime.min
        
        news_list.sort(key=lambda x: parse_time(x['time']), reverse=True)
        
        # 重新分配index
        for i, item in enumerate(news_list):
            item['index'] = i
        
        return process_dataframe_result(news_list, "news_list")
            
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        return []
    except Exception as e:
        print(f"解析错误: {e}")
        return []

res = xinlang_gegu_telegraph_detailed()
print(res)
