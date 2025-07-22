#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
澳元汇率测试程序
"""

import requests
import json
from datetime import datetime

def get_exchange_rate():
    """获取澳元汇率"""
    try:
        url = "https://api.exchangerate-api.com/v4/latest/CNY"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'rates' in data and 'AUD' in data['rates']:
            rate = data['rates']['AUD']
            return {
                'rate': rate,
                'base': 'CNY',
                'target': 'AUD',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'date': data.get('date', datetime.now().strftime('%Y-%m-%d'))
            }
        else:
            print("API响应中未找到AUD汇率")
            return None
            
    except Exception as e:
        print(f"获取汇率失败: {e}")
        return None

def format_message(rate_data):
    """格式化消息"""
    if not rate_data:
        return "获取澳元汇率失败，请检查网络连接"
    
    message = f"""澳元汇率播报

日期: {rate_data['date']}
时间: {rate_data['timestamp']}
汇率: 1 {rate_data['base']} = {rate_data['rate']:.4f} {rate_data['target']}
即: 1 澳元 = {1/rate_data['rate']:.4f} 人民币

祝您投资顺利！"""
    
    return message

if __name__ == '__main__':
    print("测试澳元汇率获取...")
    rate_data = get_exchange_rate()
    message = format_message(rate_data)
    print("\n" + "="*50)
    print(message)
    print("="*50)