import requests  # 用于发HTTP请求
import json      # 备用，但本版不用
from datetime import datetime  # 用于格式化日期

def parse_subscription(url):
    """
    解析订阅链接，获取剩余流量和时间。（修复版：支持分号格式）
    """
    # 模拟浏览器头
    headers = {
        'User-Agent': 'ClashX-Pro/1.0'
    }
    
    try:
        # 发GET请求（禁用代理）
        response = requests.get(url, headers=headers, timeout=10, proxies={'http': None, 'https': None})
        response.raise_for_status()
        
        # 抓取userinfo头（不区分大小写）
        user_info_str = response.headers.get('subscription-userinfo') or response.headers.get('Subscription-Userinfo')
        if not user_info_str or user_info_str.strip() == '':
            print("❌ 错误：未找到流量信息！检查链接或机场格式。")
            return
        
        # 新增：解析分号分隔字符串（非JSON）
        parts = [part.strip() for part in user_info_str.split(';')]
        user_info = {}
        for part in parts:
            if '=' in part:
                key, val = part.split('=', 1)  # 只split一次，避免值里有=
                user_info[key.strip()] = int(val.strip())
        
        # 提取数据（字节单位）
        upload = user_info.get('upload', 0)
        download = user_info.get('download', 0)
        total = user_info.get('total', 0)
        expire = user_info.get('expire', 0)
        
        # 计算剩余流量（字节）
        used = upload + download
        remaining_bytes = total - used
        if remaining_bytes < 0:
            remaining_bytes = 0
        
        # 转GB
        def bytes_to_gb(bytes_val):
            return round(bytes_val / (1024**3), 2)
        
        remaining_gb = bytes_to_gb(remaining_bytes)
        total_gb = bytes_to_gb(total)
        used_gb = bytes_to_gb(used)
        
        # 计算剩余时间
        if expire > 0:
            expire_date = datetime.fromtimestamp(expire)
            remaining_days = (expire_date - datetime.now()).days
            if remaining_days < 0:
                remaining_days = 0
        else:
            expire_date = "未知"
            remaining_days = "未知"
        
        # 打印结果
        print("✅ 解析成功！")
        print(f"总流量: {total_gb} GB")
        print(f"已用流量: {used_gb} GB")
        print(f"剩余流量: {remaining_gb} GB")
        print(f"到期时间: {expire_date}")
        print(f"剩余天数: {remaining_days} 天")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求出错: {e}")
    except ValueError as e:  # int转换出错
        print(f"❌ 数据格式出错: {e}（值不是数字）")
    except Exception as e:
        print(f"❌ 未知错误: {e}")

# 主程序
if __name__ == "__main__":
    url = input("请输入订阅链接: ").strip()
    if not url:
        print("❌ 链接不能为空！")
    else:
        parse_subscription(url)