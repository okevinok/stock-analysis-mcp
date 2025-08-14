import inspect
import pathlib
import sys
from functools import wraps
from typing import Literal

import akshare as ak
import fastmcp
import pandas as pd

mcp = fastmcp.FastMCP("AKShare MCP Server")

# 请复制函数名到名单中。https://akshare.akfamily.xyz/data/index.html

# 白名单
white_list = [
    # "stock_info_global_cls",  # 资讯数据-财联社
    "stock_info_cjzc_em",  # 资讯数据-财经早餐-东方财富
    "stock_info_global_em" , # 资讯数据-东方财富
    "stock_info_global_sina",  # 资讯数据-新浪财经
    "stock_info_global_futu",  # 资讯数据-富途牛牛
    "stock_info_global_ths",  # 资讯数据-同花顺
    "stock_info_broker_sina",  # 新浪财经-证券-证券原创
    "stock_zh_index_spot_em",
    "index_global_spot_em",
    "stock_zh_a_spot_em",
    "stock_yjbb_em",
    "stock_zt_pool_em",
]

# 黑名单
black_list = [
    "car_market_total_cpca",
]

def output_format(func, format: Literal["markdown", "csv", "json"]):
    @wraps(func)
    def decorated(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            
            # 检查返回结果类型
            if result is None:
                return {"content": "No data available"}
            
            # 如果不是 DataFrame，尝试转换或直接返回
            if not isinstance(result, pd.DataFrame):
                if isinstance(result, (list, dict)):
                    # 将 list 或 dict 转换为 DataFrame
                    if isinstance(result, list) and len(result) > 0:
                        if isinstance(result[0], dict):
                            df = pd.DataFrame(result)
                        else:
                            df = pd.DataFrame({"value": result})
                    elif isinstance(result, dict):
                        df = pd.DataFrame([result])
                    else:
                        return {"content": str(result)}
                else:
                    return {"content": str(result)}
            else:
                df = result
            
            # 检查 DataFrame 是否为空
            if df.empty:
                return {"content": "No data available"}
            
            # 格式化输出
            if format == 'markdown':
                content = df.to_markdown(index=False)
            elif format == 'csv':
                content = df.to_csv(index=False)
            elif format == 'json':
                content = df.to_json(force_ascii=False, indent=2, orient='records')
            else:
                content = df.to_markdown(index=False)
            
            # 确保返回字典格式
            return {"content": content}
            
        except Exception as e:
            # 错误处理
            return {"content": f"Error processing data: {str(e)}"}

    return decorated


def register(white_list, black_list, format: Literal["markdown", "csv", "json"]):
    for name, func in inspect.getmembers(ak, inspect.isfunction):
        if white_list and name not in white_list:
            continue
        if black_list and name in black_list:
            continue

        try:
            # 添加函数签名检查，避免注册有问题的函数
            sig = inspect.signature(func)
            # 跳过没有参数或参数过多的函数
                
            wrapped_func = output_format(func, format=format)
            mcp.tool()(wrapped_func)
            
        except Exception as e:
            # 可以使用日志记录而不是打印
            pass


def serve(format: Literal["markdown", "csv", "json"], transport: Literal["stdio", "sse", "streamable-http"], host: str, port: int, config: str = None):
    register(white_list, black_list, format=format)

    fastmcp.settings.host = host
    fastmcp.settings.port = port
    mcp.run(transport=transport)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="AKShare MCP Server",
    )

    parser.add_argument("--format", type=str, help="输出格式",
                        default='markdown', choices=['markdown', 'csv', 'json'])
    parser.add_argument("--transport", type=str, help="传输类型",
                        default='stdio', choices=['stdio', 'sse', 'streamable-http'])
    parser.add_argument("--host", type=str, help="MCP服务端绑定地址",
                        default='0.0.0.0')
    parser.add_argument("--port", type=int, help="MCP服务端绑定端口",
                        default='8000')
    parser.add_argument("--config", type=str, help="配置文件路径",
                        nargs="?")
    args = parser.parse_args()
    serve(args.format, args.transport, args.host, args.port, args.config)


if __name__ == "__main__":
    main()