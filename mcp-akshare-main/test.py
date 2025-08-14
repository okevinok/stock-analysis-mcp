import inspect
import akshare as ak


res = inspect.getmembers(ak, inspect.isfunction)


white_list = [
    "stock_info_global_cls",  # 资讯数据-财联社
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

for name, func in inspect.getmembers(ak, inspect.isfunction):
    if(name in white_list):
        print(f"Function {name} is in the white list.")
        sig = inspect.signature(func)
        print(f"Signature of {name}: {sig}")
   