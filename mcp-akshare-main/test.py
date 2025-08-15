
import akshare
import pandas as pd
import urllib3


def stock_info_global_cls(symbol: str = "全部"): 
    """
    财联社-电报
    https://www.cls.cn/telegraph
    :param symbol: choice of {"全部", "重点"}
    :type symbol: str
    :return: 财联社-电报
    :rtype: pandas.DataFrame
    """
    url = "https://www.cls.cn/nodeapi/telegraphList"
    response = urllib3.request('GET', url, timeout=10)
    data_json = response.json()
    temp_df = pd.DataFrame(data_json["data"]["roll_data"])
    big_df = temp_df.copy()
    big_df = big_df[["title", "content", "ctime", "level"]]
    big_df["ctime"] = pd.to_datetime(big_df["ctime"], unit="s", utc=True).dt.tz_convert(
        "Asia/Shanghai"
    )
    big_df.columns = ["标题", "内容", "发布时间", "等级"]
    big_df.sort_values(["发布时间"], inplace=True)
    big_df.reset_index(inplace=True, drop=True)
    big_df["发布日期"] = big_df["发布时间"].dt.date
    big_df["发布时间"] = big_df["发布时间"].dt.time
    if symbol == "重点":
        big_df = big_df[(big_df["等级"] == "B") | (big_df["等级"] == "A")]
        big_df.reset_index(inplace=True, drop=True)
        big_df = big_df[["标题", "内容", "发布日期", "发布时间"]]
        return big_df
    else:
        big_df = big_df[["标题", "内容", "发布日期", "发布时间"]]
        return big_df
    
# res = stock_info_global_cls()
# print(res)

# res = akshare.macro_cons_gold()

# res = akshare.stock_hsgt_sh_hk_spot_em()
res = akshare.stock_hold_management_detail_em()

print(res)
