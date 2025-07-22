#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
澳元汇率监控程序 - 简化版
每天定时获取澳元汇率并保存到文件，可选择发送邮件通知
"""

import requests
import json
import time
import schedule
import logging
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('aud_rate.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AUDRateMonitor:
    """澳元汇率监控器"""
    
    def __init__(self, config_file='config.json'):
        self.config = self.load_config(config_file)
        self.api_key = self.config.get('api_key', '')
        self.email_enabled = self.config.get('email_enabled', False)
        self.smtp_server = self.config.get('smtp_server', 'smtp.qq.com')
        self.smtp_port = self.config.get('smtp_port', 587)
        self.sender_email = self.config.get('sender_email', '')
        self.sender_password = self.config.get('sender_password', '')
        self.receiver_email = self.config.get('receiver_email', '')
        self.base_currency = self.config.get('base_currency', 'CNY')
        self.target_currency = 'AUD'
        
    def load_config(self, config_file: str) -> Dict:
        """加载配置文件"""
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 创建默认配置文件
                default_config = {
                    "api_key": "",
                    "base_currency": "CNY",
                    "send_time": "09:00",
                    "email_enabled": False,
                    "smtp_server": "smtp.qq.com",
                    "smtp_port": 587,
                    "sender_email": "",
                    "sender_password": "",
                    "receiver_email": ""
                }
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4, ensure_ascii=False)
                logger.info(f"已创建默认配置文件 {config_file}，请填写相关配置")
                return default_config
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return {}
    
    def get_exchange_rate(self) -> Optional[Dict]:
        """获取澳元汇率"""
        try:
            # 使用免费汇率API (exchangerate-api.com)
            url = f"https://api.exchangerate-api.com/v4/latest/{self.base_currency}"
            
            # 如果有API key，使用付费版本获得更高稳定性
            if self.api_key:
                url = f"https://v6.exchangerate-api.com/v6/{self.api_key}/latest/{self.base_currency}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'rates' in data and self.target_currency in data['rates']:
                rate = data['rates'][self.target_currency]
                return {
                    'rate': rate,
                    'base': self.base_currency,
                    'target': self.target_currency,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'date': data.get('date', datetime.now().strftime('%Y-%m-%d'))
                }
            else:
                logger.error(f"API响应中未找到{self.target_currency}汇率")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"获取汇率失败 - 网络错误: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"获取汇率失败 - JSON解析错误: {e}")
            return None
        except Exception as e:
            logger.error(f"获取汇率失败 - 未知错误: {e}")
            return None
    
    def format_message(self, rate_data: Dict) -> str:
        """格式化消息"""
        if not rate_data:
            return "获取澳元汇率失败，请检查网络连接或API配置"
        
        message = f"""澳元汇率播报

日期: {rate_data['date']}
时间: {rate_data['timestamp']}
汇率: 1 {rate_data['base']} = {rate_data['rate']:.4f} {rate_data['target']}
即: 1 澳元 = {1/rate_data['rate']:.4f} 人民币

祝您投资顺利！"""
        
        return message
    
    def save_to_file(self, message: str, rate_data: Dict) -> bool:
        """保存汇率信息到文件"""
        try:
            # 保存到日志文件
            with open('daily_rates.txt', 'a', encoding='utf-8') as f:
                f.write(f"\n{'-'*50}\n")
                f.write(message)
                f.write(f"\n{'-'*50}\n")
            
            # 保存JSON格式数据
            if rate_data:
                json_file = 'rates_history.json'
                history = []
                if os.path.exists(json_file):
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            history = json.load(f)
                    except:
                        history = []
                
                history.append(rate_data)
                
                # 只保留最近30天的数据
                if len(history) > 30:
                    history = history[-30:]
                
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(history, f, indent=2, ensure_ascii=False)
            
            logger.info("汇率信息已保存到文件")
            return True
            
        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            return False
    
    def send_email(self, message: str) -> bool:
        """发送邮件通知"""
        if not self.email_enabled or not self.sender_email or not self.receiver_email:
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.receiver_email
            msg['Subject'] = "澳元汇率播报"
            
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            
            logger.info("邮件通知已发送")
            return True
            
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False
    
    def run_daily_task(self):
        """执行每日任务"""
        logger.info("开始执行澳元汇率获取任务")
        
        # 获取汇率
        rate_data = self.get_exchange_rate()
        
        # 格式化消息
        message = self.format_message(rate_data)
        
        # 输出到控制台
        print(f"\n{message}\n")
        
        # 保存到文件
        self.save_to_file(message, rate_data)
        
        # 尝试发送邮件
        if self.email_enabled:
            self.send_email(message)
        
        logger.info("澳元汇率播报任务完成")
    
    def start_monitoring(self):
        """开始监控"""
        logger.info("启动澳元汇率监控程序")
        
        # 设置定时任务
        send_time = self.config.get('send_time', '09:00')
        schedule.every().day.at(send_time).do(self.run_daily_task)
        
        logger.info(f"已设置每日 {send_time} 发送汇率信息")
        
        # 立即执行一次任务进行测试
        logger.info("执行测试任务...")
        self.run_daily_task()
        
        # 开始定时任务循环
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
            except KeyboardInterrupt:
                logger.info("程序被用户中断")
                break
            except Exception as e:
                logger.error(f"定时任务执行出错: {e}")
                time.sleep(300)  # 出错后等待5分钟再继续


def main():
    """主函数"""
    try:
        monitor = AUDRateMonitor()
        monitor.start_monitoring()
    except Exception as e:
        logger.error(f"程序启动失败: {e}")


if __name__ == '__main__':
    main()