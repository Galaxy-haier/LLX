import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime
import threading
import json
import os

class TrafficCheckerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("机场流量查询工具")
        self.root.geometry("550x650")
        self.root.resizable(False, False)
        
        # 配置文件路径
        self.config_file = "subscriptions.json"
        self.history = self.load_history()
        
        # 设置样式
        self.setup_styles()
        
        # 创建界面
        self.create_widgets()
        
        # 加载上次的订阅地址
        self.load_last_subscription()
        
    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置颜色
        style.configure('Title.TLabel', font=('Microsoft YaHei UI', 20, 'bold'), 
                       foreground='#667eea')
        style.configure('Info.TLabel', font=('Microsoft YaHei UI', 10))
        style.configure('Value.TLabel', font=('Microsoft YaHei UI', 12, 'bold'),
                       foreground='#2c3e50')
        style.configure('TButton', font=('Microsoft YaHei UI', 11))
        style.configure('Small.TButton', font=('Microsoft YaHei UI', 9))
        
    def load_history(self):
        """加载历史记录"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {'last_url': '', 'urls': []}
        return {'last_url': '', 'urls': []}
    
    def save_history(self):
        """保存历史记录"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")
    
    def add_to_history(self, url):
        """添加到历史记录"""
        self.history['last_url'] = url
        
        # 添加到历史列表(去重)
        if url not in self.history['urls']:
            self.history['urls'].insert(0, url)
            # 最多保存10条记录
            self.history['urls'] = self.history['urls'][:10]
        else:
            # 如果已存在,移到最前面
            self.history['urls'].remove(url)
            self.history['urls'].insert(0, url)
        
        self.save_history()
        self.update_history_menu()
        
    def load_last_subscription(self):
        """加载上次的订阅地址"""
        if self.history['last_url']:
            self.url_entry.delete("1.0", tk.END)
            self.url_entry.insert("1.0", self.history['last_url'])
        
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title = ttk.Label(main_frame, text="✈️ 机场流量查询", style='Title.TLabel')
        title.pack(pady=(0, 20))
        
        # 输入框架
        input_frame = ttk.LabelFrame(main_frame, text="订阅地址", padding="15")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.url_entry = tk.Text(input_frame, height=3, font=('Consolas', 9), 
                                 wrap=tk.WORD, relief=tk.SOLID, borderwidth=1)
        self.url_entry.pack(fill=tk.X)
        
        # 历史记录按钮框架
        history_frame = ttk.Frame(main_frame)
        history_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.history_btn = ttk.Button(history_frame, text="📋 历史记录", 
                                     command=self.show_history_menu,
                                     style='Small.TButton')
        self.history_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.clear_btn = ttk.Button(history_frame, text="🗑️ 清空输入", 
                                   command=self.clear_input,
                                   style='Small.TButton')
        self.clear_btn.pack(side=tk.LEFT)
        
        # 查询按钮
        self.query_btn = tk.Button(main_frame, text="查询流量", 
                                   command=self.query_traffic,
                                   bg='#667eea', fg='white', 
                                   font=('Microsoft YaHei UI', 12, 'bold'),
                                   relief=tk.FLAT, cursor='hand2',
                                   activebackground='#5568d3',
                                   height=2)
        self.query_btn.pack(fill=tk.X, pady=(0, 20))
        
        # 结果框架
        self.result_frame = ttk.LabelFrame(main_frame, text="流量信息", padding="15")
        self.result_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建结果显示区域
        self.create_result_display()
        
        # 状态栏
        self.status_label = ttk.Label(main_frame, text="就绪 | 上次查询会自动保存", 
                                     foreground='#7f8c8d',
                                     font=('Microsoft YaHei UI', 9))
        self.status_label.pack(pady=(10, 0))
        
    def create_result_display(self):
        """创建结果显示区域"""
        items = [
            ("总流量", "total"),
            ("已用流量", "used"),
            ("剩余流量", "remaining"),
            ("到期时间", "expire"),
            ("剩余天数", "days")
        ]
        
        self.result_labels = {}
        
        for label_text, key in items:
            frame = ttk.Frame(self.result_frame)
            frame.pack(fill=tk.X, pady=8)
            
            label = ttk.Label(frame, text=label_text + ":", style='Info.TLabel')
            label.pack(side=tk.LEFT)
            
            value = ttk.Label(frame, text="-", style='Value.TLabel')
            value.pack(side=tk.RIGHT)
            
            self.result_labels[key] = value
        
        # 进度条
        progress_frame = ttk.Frame(self.result_frame)
        progress_frame.pack(fill=tk.X, pady=(15, 5))
        
        ttk.Label(progress_frame, text="使用进度:", style='Info.TLabel').pack(anchor=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate',
                                           length=400)
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        
        self.progress_label = ttk.Label(progress_frame, text="0%", 
                                       font=('Microsoft YaHei UI', 9))
        self.progress_label.pack(anchor=tk.E, pady=(2, 0))
    
    def clear_input(self):
        """清空输入框"""
        self.url_entry.delete("1.0", tk.END)
        
    def show_history_menu(self):
        """显示历史记录菜单"""
        if not self.history['urls']:
            messagebox.showinfo("提示", "暂无历史记录")
            return
        
        # 创建弹出菜单
        menu = tk.Menu(self.root, tearoff=0)
        
        for url in self.history['urls']:
            # 截取URL显示(最多显示50个字符)
            display_url = url[:50] + "..." if len(url) > 50 else url
            menu.add_command(label=display_url, 
                           command=lambda u=url: self.load_url(u))
        
        menu.add_separator()
        menu.add_command(label="🗑️ 清空历史记录", command=self.clear_history)
        
        # 在按钮下方显示菜单
        x = self.history_btn.winfo_rootx()
        y = self.history_btn.winfo_rooty() + self.history_btn.winfo_height()
        menu.post(x, y)
    
    def update_history_menu(self):
        """更新历史记录菜单"""
        pass  # 每次点击时重新生成菜单
    
    def load_url(self, url):
        """加载选中的URL"""
        self.url_entry.delete("1.0", tk.END)
        self.url_entry.insert("1.0", url)
        self.status_label.config(text="已加载历史记录", foreground='#3498db')
    
    def clear_history(self):
        """清空历史记录"""
        if messagebox.askyesno("确认", "确定要清空所有历史记录吗?"):
            self.history = {'last_url': '', 'urls': []}
            self.save_history()
            self.status_label.config(text="历史记录已清空", foreground='#e74c3c')
        
    def query_traffic(self):
        """查询流量(在新线程中运行)"""
        url = self.url_entry.get("1.0", tk.END).strip()
        
        if not url:
            messagebox.showwarning("警告", "请输入订阅地址!")
            return
        
        # 保存到历史记录
        self.add_to_history(url)
        
        # 禁用按钮,防止重复点击
        self.query_btn.config(state=tk.DISABLED, text="查询中...")
        self.status_label.config(text="正在查询...", foreground='#3498db')
        
        # 在新线程中执行查询
        thread = threading.Thread(target=self._do_query, args=(url,))
        thread.daemon = True
        thread.start()
        
    def _do_query(self, url):
        """执行实际的查询操作"""
        headers = {'User-Agent': 'ClashX-Pro/1.0'}
        
        try:
            response = requests.get(url, headers=headers, timeout=10, 
                                  proxies={'http': None, 'https': None})
            response.raise_for_status()
            
            user_info_str = (response.headers.get('subscription-userinfo') or 
                           response.headers.get('Subscription-Userinfo'))
            
            if not user_info_str or user_info_str.strip() == '':
                self.show_error("未找到流量信息!请检查订阅地址。")
                return
            
            # 解析数据
            parts = [part.strip() for part in user_info_str.split(';')]
            user_info = {}
            for part in parts:
                if '=' in part:
                    key, val = part.split('=', 1)
                    user_info[key.strip()] = int(val.strip())
            
            upload = user_info.get('upload', 0)
            download = user_info.get('download', 0)
            total = user_info.get('total', 0)
            expire = user_info.get('expire', 0)
            
            used = upload + download
            remaining_bytes = max(0, total - used)
            
            # 转换单位
            def bytes_to_gb(b):
                return round(b / (1024**3), 2)
            
            total_gb = bytes_to_gb(total)
            used_gb = bytes_to_gb(used)
            remaining_gb = bytes_to_gb(remaining_bytes)
            
            # 计算到期时间
            if expire > 0:
                expire_date = datetime.fromtimestamp(expire)
                expire_str = expire_date.strftime("%Y-%m-%d %H:%M")
                remaining_days = max(0, (expire_date - datetime.now()).days)
                days_str = f"{remaining_days} 天"
            else:
                expire_str = "未知"
                days_str = "未知"
            
            # 计算使用百分比
            usage_percent = (used / total * 100) if total > 0 else 0
            
            # 更新界面(必须在主线程中)
            self.root.after(0, self.update_results, {
                'total': f"{total_gb} GB",
                'used': f"{used_gb} GB",
                'remaining': f"{remaining_gb} GB",
                'expire': expire_str,
                'days': days_str,
                'percent': usage_percent
            })
            
        except requests.exceptions.RequestException as e:
            self.show_error(f"网络请求失败: {str(e)}")
        except ValueError as e:
            self.show_error(f"数据格式错误: {str(e)}")
        except Exception as e:
            self.show_error(f"未知错误: {str(e)}")
    
    def update_results(self, data):
        """更新结果显示"""
        self.result_labels['total'].config(text=data['total'])
        self.result_labels['used'].config(text=data['used'])
        self.result_labels['remaining'].config(text=data['remaining'])
        self.result_labels['expire'].config(text=data['expire'])
        self.result_labels['days'].config(text=data['days'])
        
        # 更新进度条
        self.progress_bar['value'] = data['percent']
        self.progress_label.config(text=f"{data['percent']:.1f}%")
        
        # 重置按钮
        self.query_btn.config(state=tk.NORMAL, text="查询流量")
        self.status_label.config(text="查询成功! 已保存到历史记录", foreground='#27ae60')
        
    def show_error(self, message):
        """显示错误信息"""
        self.root.after(0, lambda: messagebox.showerror("错误", message))
        self.root.after(0, lambda: self.query_btn.config(state=tk.NORMAL, text="查询流量"))
        self.root.after(0, lambda: self.status_label.config(text="查询失败", foreground='#e74c3c'))

def main():
    root = tk.Tk()
    app = TrafficCheckerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()