# neutus-ts/test_reuters_client.py
import unittest
from unittest.mock import Mock, patch
from reuters_client import ReutersClient, ApiError, ExternalError, InternalError

class TestReutersClient(unittest.TestCase):
    
    def setUp(self):
        self.client = ReutersClient()
    
    @patch('requests.Session.get')
    def test_search_articles_success(self, mock_get):
        """测试成功搜索文章"""
        # 模拟成功响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'statusCode': 200,
            'result': {
                'pagination': {'total_size': 100},
                'articles': [
                    {
                        'title': 'Test Article',
                        'canonical_url': 'https://example.com/article',
                        'description': 'Test description',
                        'published_time': '2025-01-01T00:00:00Z'
                    }
                ]
            }
        }
        mock_get.return_value = mock_response
        
        # 执行测试
        result = self.client.search_articles("test")
        
        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result.pagination.total_size, 100)
        self.assertEqual(len(result.articles), 1)
        self.assertEqual(result.articles[0].title, 'Test Article')
    
    @patch('requests.Session.get')
    def test_api_error_handling(self, mock_get):
        """测试 API 错误处理"""
        # 模拟 404 错误
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_get.return_value = mock_response
        
        # 验证异常抛出
        with self.assertRaises(ExternalError) as context:
            self.client.search_articles("test")
        
        self.assertEqual(context.exception.status_code, 404)
    
    def test_article_parsing(self):
        """测试文章数据解析"""
        article_data = {
            'title': 'Test Title',
            'canonical_url': 'https://example.com',
            'description': 'Test description',
            'published_time': '2025-01-01T00:00:00Z',
            'authors': [
                {'name': 'John Doe', 'byline': 'Reporter'}
            ],
            'thumbnail': {
                'caption': 'Test image',
                'width': 800,
                'height': 600,
                'resizer_url': 'https://example.com/image.jpg'
            }
        }
        
        article = self.client._parse_article(article_data)
        
        self.assertEqual(article.title, 'Test Title')
        self.assertEqual(article.canonical_url, 'https://example.com')
        self.assertEqual(len(article.authors), 1)
        self.assertEqual(article.authors[0].name, 'John Doe')
        self.assertIsNotNone(article.thumbnail)
        self.assertEqual(article.thumbnail.width, 800)

if __name__ == '__main__':
    unittest.main()