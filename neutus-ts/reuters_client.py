# neutus-ts/reuters_client.py
import json
import requests
from typing import Optional, Dict, List, Any, Union
from dataclasses import dataclass
from enum import Enum


class ApiError(Exception):
    """API 错误基类"""
    pass


class RedirectError(ApiError):
    """重定向错误"""
    def __init__(self, status_code: int, location: str):
        self.status_code = status_code
        self.location = location
        super().__init__(f"Redirect {status_code} to {location}")


class ExternalError(ApiError):
    """外部 API 错误"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"External error {status_code}: {message}")


class InternalError(ApiError):
    """内部错误"""
    pass


@dataclass
class Image:
    """图片信息"""
    caption: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    resizer_url: str = ""


@dataclass
class Topic:
    """主题/作者信息"""
    name: str
    topic_url: Optional[str] = None
    byline: str = ""


@dataclass
class Article:
    """文章信息"""
    title: str
    subtype: Optional[str] = None
    canonical_url: str = ""
    description: str = ""
    content_elements: Optional[List[Dict[str, Any]]] = None
    authors: Optional[List[Topic]] = None
    thumbnail: Optional[Image] = None
    published_time: str = ""


@dataclass
class Pagination:
    """分页信息"""
    total_size: Optional[int] = None


@dataclass
class Articles:
    """文章列表响应"""
    pagination: Pagination
    articles: Optional[List[Article]] = None
    topics: Optional[List[Topic]] = None


@dataclass
class Section:
    """分类信息"""
    name: str
    id: str
    children: Optional[List['Section']] = None


@dataclass
class ApiResponse:
    """API 响应包装"""
    status_code: int
    message: Optional[str] = None
    result: Optional[Any] = None


class ReutersClient:
    """Reuters API 客户端"""
    
    BASE_URL = "https://www.reuters.com"
    
    def __init__(self, timeout: int = 30):
        self.session = requests.Session()
        self.timeout = timeout
        
        # 设置默认请求头
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-GB,en;q=0.9',
            'Referer': 'https://www.reuters.com/',
            'Origin': 'https://www.reuters.com',
            'Cookie': 'cleared-onetrust-cookies=Thu, 17 Feb 2022 19:17:07 GMT; usprivacy=1---; _gcl_au=1.1.1644174517.1755241032; _li_dcdm_c=.reuters.com; _lc2_fpi=f511229f0ef8--01k2p89arht3qzwny252ghayyr; _lc2_fpi_js=f511229f0ef8--01k2p89arht3qzwny252ghayyr; _fbp=fb.1.1755241033497.268690643371457521; sa-user-id=s%253A0-ab2954a1-a1bf-4b41-52cb-feb95f725f44.MYGdUTr3B5SteYctSaYNYGLOiH%252B3F5xdjRTh6cfOwnw; sa-user-id-v2=s%253AqylUoaG_S0FSy_65X3JfRD7Ar18.AtY6docCCFyF%252FqNSdIzfRWlwXQWDWKTxpxEwrUdW2dA; sa-user-id-v3=s%253AAQAKIBgvtu6HwSxupj2zC5qYZU6_AD1kquAm4DOYSWrd75yhEHwYAiDj2vrBBjoEtKIe0EIEiwQquQ.Lk%252BKeHlNTEEKcCcqIcD7M%252BdwOQMuVJ0pzoNyPw3n11Y; permutive-id=4582370c-99ea-47b1-b5b4-c821075f9cf2; _cb=CPNBaHCtxdvGsjk5H; _ga=GA1.2.753013835.1755241036; _gid=GA1.2.263185755.1755241036; cnx_userId=2-fc73794db9fd472ab4cd10ad51d79fac; ajs_anonymous_id=cb0ac241-f21d-4995-9f96-ebe6d65ad046; _v__chartbeat3=0G1CrDTjGWhCkziQJ; _cc_id=39be7e078d2a9d90c1d9feef044b65ac; panoramaId_expiry=1755327440485; panoramaId=0294451ead73ad503acecc6f9e88a9fb927a243e43ca048a043438eed0c2db09; panoramaIdType=panoDevice; idw-fe-id=5250eea5-a507-4516-ac8d-31781c530906; BOOMR_CONSENT="opted-in"; bounceClientVisit5431v=N4IgNgDiBcIBYBcEQM4FIDMBBNAmAYnvgO6kB0ATgKYCuCVFKZAxgPYC2RKNKCAhgEsAdnwBGAsAIQBPIs0ns+9ALRUhDAOayCEMH14DmyiKzBg6A1kOX8wAaxTKNrZcIQvWANwYIB7KspsNEIIFAJUjhA8cMp6KqLUfHYIcBSsNBoxuAAMuACsytkAHMoAjAAsRCAANCAUMCA1ILxKVDCgACZUnoZUAPoCHQ2luKUY2QBsGCMA7DOleeXlpbkYTRodEPXQAGZ8YChUtcz6YDB7B0cgPOf7h7VdPcxt0KAJrMSH2yAAwqkcbVq3kYliEwwwRTI2ShUKauiUO1YFHYDQA6sIOh8UE1Hr0+jIIC8QF0UMlWFBagk+EIhrAmsQqKIelRiLdLgBfWpCVh9OzCCICbHQUI0K7UACOot4+NYdjUDQweVE2VEAE48kVVYzssxRHqJpNyqIKkUinwqDtVR1cKrcFQ+B1shg+BNVbaOhMZswOsxTcwdkVRDNyhMDUrcEUmuxWOIwC8LvcQD0oLAJrgyKVbRmZnkM0UZusqKx2iAgiEKNIGgAJADSTQAXgIU41aiYWmA+mwug0mswpJXYFWrBoAAQ14e9qy+dQhTusbuwLAAZSa1A0oJ7tTXoL6In8m9L6XL0l3fH3g+HY4nxyPoRPXaJtcnwTvc66a0HNYA4k0+Ik30SOKKABMDZLU-ihDyD6gbUcRSDQC64OmGCwcO8ELqUFRkLgnIgKwOw7L0bKJigKA7J4CAwSACBgtApQ5nkuDLJMEy1O4cpCAAaoKUgAJK0iA9F5IxzGhnk2T0RgExND0KB8QAIsMDFMSsYkSTMUkgOy7JAA; OneTrustWPCCPAGoogleOptOut=false; _lr_retry_request=true; _lr_env_src_ats=false; _cb_svref=external; _lr_sampling_rate=100; _pbjs_userid_consent_data=3524755945110770; __gads=ID=621a923ae4af9ed1:T=1755241038:RT=1755241461:S=ALNI_MabX7LzAQdikEO9xZmn9qrUPaJ9jg; __gpi=UID=0000118075137b68:T=1755241038:RT=1755241461:S=ALNI_MbQjtXIoUrEP-Apps5HW0ek26X2mA; __eoi=ID=8f9883b9e0b28a09:T=1755241038:RT=1755241461:S=AA-AfjYsKHwaU9yqxPIuEZWBkC7A; dicbo_id=%7B%22dicbo_fetch%22%3A1755241643202%7D; _awl=2.1755241646.5-5dd0209f83c437a6053f786c790c4f7b-6763652d617369612d6561737431-0; cto_bundle=qczVwV9HQW15VjJsTkFuMiUyQlFnQ1JKTjlHS1JnRDJyWkk4OXFiUFJIeU9qalRWcmFwWWh3QVpyN3hLcjhiTVBNMnFDUDduYlJCTUdwN29vVEtBeWtiN09jMVczRlN3SW1jSlE0WVF0ekV4SGdNMHhUYWElMkZhdGFrY3RrNFlIMWxmdSUyRmFYejh6TkxyalEwZ0JQUWlJMHNGcTQxVHA2a2VsR3V5dllEOVRnTm1BSjFPSE5ickFhMWlTRndaWTFudlk5T0VnbGc5d3l1bnFtTG5RZDV6YkxSJTJGaEphWEElM0QlM0Q; _gat=1; reuters-geo={"country":"-", "region":"-"}; datadome=pu9J7SCuXhsWlqyhGO4d_QKpgaxAe3GqC0vn6mMiUswvjVBJ1xzO1ZYhuD0c1UlK3UlEmiUGa71HYfEYVIw7bIs22IX4SEWEztQU75RCEqbWn7E53TvHWjK9pzib6L2v; ABTasty=uid=qrdd8pk3zqqy7ymk; ABTastySession=mrasn=&lp=https%253A%252F%252Fwww.reuters.com%252Fsustainability%252Fclimate-energy%252Fplastic-pollution-talks-go-into-overtime-countries-push-late-breakthrough-2025-08-14%252F; OptanonConsent=isGpcEnabled=0&datestamp=Fri+Aug+15+2025+15%3A08%3A40+GMT%2B0800+(%E4%B8%AD%E5%9B%BD%E6%A0%87%E5%87%86%E6%97%B6%E9%97%B4)&version=202505.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=95dbfeb6-4330-4fbc-a69e-9d3866ef28e9&interactionCount=0&isAnonUser=1&landingPath=NotLandingPage&groups=1%3A1%2C2%3A1%2C3%3A1%2C4%3A1&AwaitingReconsent=false; _li_ss=CrcBCgYI-QEQvxsKBgj3ARC_GwoFCAoQvxsKBgjdARC_GwoGCPgBEL8bCgYIgQEQvxsKBQgMEMkbCgYI9QEQvxsKBQgLEL8bCgYI4wEQvxsKBgikARC_GwoGCLMBEL8bCgYIiQEQvxsKBgilARC_GwoGCIACEMEbCgYI4QEQvxsKBgiiARC_GwoGCP8BEL8bCgkI_____wcQyRsKBgiHAhC_GwoGCNIBEL8bCgUIfhC_GwoGCIgBEL8b; _chartbeat2=.1755241034327.1755241723589.1.BDkzGYDJaVEeuVYKiDIkF3uBoiWW_.3; _chartbeat5=46|786|%2Fmarkets%2Fus%2F|https%3A%2F%2Fwww.reuters.com%2Fmarkets%2Fquote%2F.DJI%2F|DfzhrFCD7w1WDOoGpsDLar1CBmdxo6||c|DS4V75DSSN9sDRgAYxCnIEHmzl4Mf|reuters.com||; _dd_s=rum=0&expire=1755242627928; _chartbeat4=t=D4pgAKC25dcqkFf0X6ffowCmFG_k&E=2&x=300&c=0.09&y=7850&w=991; _v__cb_cp=B6PxK9Bap5OhDb9vJofLTMTDKP4FY'
        })
    
    def _make_request(self, url: str, query: str, debug: bool = False, extra_params: dict = None) -> Any:
        """发起 API 请求"""
        try:
            if debug:
                print(f"🔍 请求URL: {url}")
                print(f"🔍 查询参数: {query}")
            
            # 基础参数
            params = {'query': query}
            
            # 根据不同的API端点添加不同的参数
            if extra_params:
                params.update(extra_params)
            elif 'articles-by-stock-symbol' in url:
                # 只对股票API添加这些参数
                params.update({
                    'd': 303,
                    'mxId': '00000000',
                    '_website': 'reuters'
                })
            
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )
            
            if debug:
                print(f"🔍 响应状态码: {response.status_code}")
                print(f"🔍 响应内容: {response.text[:500]}...")
            
            # 处理重定向
            if 300 <= response.status_code < 400:
                location = response.headers.get('Location', '/')
                raise RedirectError(response.status_code, location)
            
            # 检查 HTTP 状态码
            if not (200 <= response.status_code < 300):
                raise ExternalError(response.status_code, response.text)
            
            # 解析 JSON 响应
            api_response = response.json()
            
            # 检查 API 响应状态
            status_code = api_response.get('statusCode', response.status_code)
            if not (200 <= status_code < 300) or api_response.get('result') is None:
                message = api_response.get('message', 'Unknown error')
                raise ExternalError(status_code, message)
            
            return api_response['result']
            
        except requests.RequestException as e:
            raise InternalError(f"Request failed: {str(e)}")
        except json.JSONDecodeError as e:
            raise InternalError(f"Failed to parse JSON response: {str(e)}")
    
    def fetch_article_by_url(self, path: str) -> Article:
        """通过 URL 获取文章"""
        url = "https://www.reuters.com/pf/api/v3/content/fetch/article-by-id-or-url-v1"
        query = json.dumps({"website_url": path, "website": "reuters"})
        
        result = self._make_request(url, query)
        return self._parse_article(result)
    
    def search_articles(self, keyword: str, offset: int = 0, size: int = 20) -> Articles:
        """按关键词搜索文章"""
        url = "https://www.reuters.com/pf/api/v3/content/fetch/articles-by-search-v2"
        query = json.dumps({
            "keyword": keyword,
            "offset": offset,
            "orderby": "display_date:desc",
            "size": size,
            "website": "reuters"
        })
        
        result = self._make_request(url, query)
        return self._parse_articles(result)
    
    def fetch_articles_by_stock_symbol(self, symbol: str) -> List[Article]:
        """按股票代码获取相关文章"""
        url = "https://www.reuters.com/pf/api/v3/content/fetch/articles-by-stock-symbol-v1"
        
        # 确保与Rust版本完全一致的JSON格式
        query = f'{{"website":"reuters","symbol":"{symbol}","size": 1 }}'
        
        try:
            result = self._make_request(url, query)
            articles_data = result.get('articles', [])
            return [self._parse_article(article_data) for article_data in articles_data]
        except ExternalError as e:
            # 如果404，可能是股票代码不存在，返回空列表而不是抛出异常
            if e.status_code == 404:
                return []
            raise
    
    def fetch_articles_by_topic(self, path: str, offset: int = 0, size: int = 20) -> Articles:
        """按主题获取文章"""
        url = "https://www.reuters.com/pf/api/v3/content/fetch/articles-by-topic-v1"
        
        # 确保路径格式正确
        if not path.startswith('/'):
            path = '/' + path
        
        query = json.dumps({
            "offset": offset,
            "size": size,
            "topic_url": path,
            "website": "reuters"
        })
        
        result = self._make_request(url, query)
        return self._parse_articles(result)
    
    def fetch_articles_by_section(self, path: str, offset: int = 0, size: int = 20) -> Articles:
        """按分类获取文章"""
        url = "https://www.reuters.com/pf/api/v3/content/fetch/recent-stories-by-sections-v1"
        query = json.dumps({
            "offset": offset,
            "size": size,
            "section_ids": path,
            "website": "reuters"
        })
        
        result = self._make_request(url, query)
        return self._parse_articles(result)
    
    def fetch_site_hierarchy(self) -> Section:
        """获取网站层级结构"""
        url = "https://www.reuters.com/pf/api/v3/content/fetch/site-hierarchy-by-name-v1"
        
        result = self._make_request(url, "")
        return self._parse_section(result)
    
    def _ensure_full_url(self, url: str) -> str:
        """确保URL是完整的绝对链接"""
        if not url:
            return ""
        
        # 如果已经是完整URL，直接返回
        if url.startswith('http://') or url.startswith('https://'):
            return url
        
        # 如果是相对路径，添加基础URL
        if url.startswith('/'):
            return f"{self.BASE_URL}{url}"
        else:
            return f"{self.BASE_URL}/{url}"
    
    def _parse_article(self, data: Dict[str, Any]) -> Article:
        """解析文章数据"""
        thumbnail = None
        if data.get('thumbnail'):
            thumbnail_data = data['thumbnail']
            thumbnail = Image(
                caption=thumbnail_data.get('caption'),
                width=thumbnail_data.get('width'),
                height=thumbnail_data.get('height'),
                resizer_url=thumbnail_data.get('resizer_url', '')
            )
        
        authors = None
        if data.get('authors'):
            authors = [
                Topic(
                    name=author.get('name', ''),
                    topic_url=self._ensure_full_url(author.get('topic_url', '')),
                    byline=author.get('byline', '')
                )
                for author in data['authors']
            ]
        
        # 确保canonical_url是完整的URL
        canonical_url = self._ensure_full_url(data.get('canonical_url', ''))
        
        return Article(
            title=data.get('title', ''),
            subtype=data.get('subtype'),
            canonical_url=canonical_url,
            description=data.get('description', ''),
            content_elements=data.get('content_elements'),
            authors=authors,
            thumbnail=thumbnail,
            published_time=data.get('published_time', '')
        )
    
    def _parse_articles(self, data: Dict[str, Any]) -> Articles:
        """解析文章列表数据"""
        pagination_data = data.get('pagination', {})
        pagination = Pagination(total_size=pagination_data.get('total_size'))
        
        articles = None
        if data.get('articles'):
            articles = [self._parse_article(article_data) for article_data in data['articles']]
        
        topics = None
        if data.get('topics'):
            topics = [
                Topic(
                    name=topic.get('name', ''),
                    topic_url=topic.get('topic_url'),
                    byline=topic.get('byline', '')
                )
                for topic in data['topics']
            ]
        
        return Articles(
            pagination=pagination,
            articles=articles,
            topics=topics
        )
    
    def _parse_section(self, data: Dict[str, Any]) -> Section:
        """解析分类数据"""
        children = None
        if data.get('children'):
            children = [self._parse_section(child) for child in data['children']]
        
        return Section(
            name=data.get('name', ''),
            id=data.get('id', ''),
            children=children
        )


# 使用示例
if __name__ == "__main__":
    client = ReutersClient()
    
    try:
        # 搜索文章
        search_results = client.search_articles("technology", size=5)
        print(f"Found {search_results.pagination.total_size} articles")
        
        if search_results.articles:
            for article in search_results.articles:
                print(f"Title: {article.title}")
                print(f"URL: {article.canonical_url}")
                print(f"Published: {article.published_time}")
                print("---")
        
        # 按股票代码搜索
        stock_articles = client.fetch_articles_by_stock_symbol(".DJI")
        print(f"\nFound {len(stock_articles)} articles for .DJI")
        
    except ApiError as e:
        print(f"API Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")