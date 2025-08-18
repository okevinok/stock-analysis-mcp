import akshare


def cls_telegraph():
    """
    抓取财联社电报页面HTML并解析出类名为telegraph-content-box的时间和内容
    https://www.cls.cn/telegraph
    :return: 包含时间和内容的字典列表
    :rtype: list
    """
    import requests
    from bs4 import BeautifulSoup
    
    try:
        # 设置请求头，模拟浏览器访问
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # 发送GET请求获取页面内容
        url = "https://www.cls.cn/telegraph"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # 检查请求是否成功
        response.encoding = 'utf-8'  # 设置编码
        
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找类名为telegraph-content-box的元素
        telegraph_boxes = soup.find_all(class_='telegraph-content-box')
        
        telegraph_data = []
        for i, box in enumerate(telegraph_boxes):
            # 查找时间元素
            time_element = box.find(class_='telegraph-time-box')
            time_text = time_element.get_text(strip=True) if time_element else ""
            
            # 查找内容元素 - 在span.c-34304b中
            content_element = box.find('span', class_='c-34304b')
            content_text = ""
            
            if content_element:
                # 提取strong标签中的标题
                strong_element = content_element.find('strong')
                title = strong_element.get_text(strip=True) if strong_element else ""
                
                # 获取完整内容文本
                full_content = content_element.get_text(strip=True)
                
                # 移除br标签并清理文本
                content_text = full_content.replace('\n', ' ').replace('\r', '').strip()
            
            telegraph_item = {
                'index': i,
                'time': time_text,
                'content': content_text
            }
            
            telegraph_data.append(telegraph_item)
        
        return telegraph_data
            
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        return []
    except Exception as e:
        print(f"解析错误: {e}")
        return []


def cls_telegraph_detailed():
    """
    抓取财联社电报页面HTML并解析出详细的时间、标题和内容信息
    https://www.cls.cn/telegraph
    :return: 包含详细信息的字典列表
    :rtype: list
    """
    import requests
    from bs4 import BeautifulSoup
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        url = "https://www.cls.cn/telegraph"
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找类名为telegraph-content-box的元素
        telegraph_boxes = soup.find_all(class_='telegraph-content-box')
        
        telegraph_details = []
        for i, box in enumerate(telegraph_boxes):
            # 查找时间元素
            time_element = box.find(class_='telegraph-time-box')
            time_text = time_element.get_text(strip=True) if time_element else ""
            
            # 查找内容元素
            content_element = box.find('span', class_='c-34304b')
            title = ""
            content = ""
            
            if content_element:
                # 提取strong标签中的标题
                strong_element = content_element.find('strong')
                if strong_element:
                    title = strong_element.get_text(strip=True)
                    # 移除strong标签以获取剩余内容
                    strong_element.decompose()
                
                # 获取剩余内容
                content = content_element.get_text(strip=True)
                # 清理文本
                content = content.replace('\n', ' ').replace('\r', '').strip()
            
            telegraph_item = {
                'index': i,
                'time': time_text,
                'title': title,
                'content': content,
                'full_text': f"{title} {content}".strip()
            }
            
            telegraph_details.append(telegraph_item)
        
        return telegraph_details
            
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        return []
    except Exception as e:
        print(f"解析错误: {e}")
        return []


# 使用示例
if __name__ == "__main__":
    
    result = akshare.stock_fund_flow_individual(symbol='即时')
    print(result)


    # 获取简化的时间和内容
    print("=== 简化版本 ===")
    contents = cls_telegraph()
    for item in contents:
        print(f"时间: {item['time']}")
        print(f"内容: {item['content'][:100]}...")  # 只显示前100个字符
        print("-" * 50)
    
    print("\n=== 详细版本 ===")
    # 获取详细信息
    details = cls_telegraph_detailed()
    for detail in details:
        print(f"时间: {detail['time']}")
        print(f"标题: {detail['title']}")
        print(f"内容: {detail['content'][:100]}...")  # 只显示前100个字符
        print("-" * 50)