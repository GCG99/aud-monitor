# 澳元汇率监控程序

每天定时获取澳元汇率并发送到指定邮箱。

## 功能特点
- 自动获取CNY/AUD汇率
- 每日定时邮件推送
- 24小时云端运行
- 历史数据记录

## 配置说明
在 `config.json` 中配置：
- `sender_email`: 发送邮箱
- `sender_password`: 邮箱授权码
- `receiver_email`: 接收邮箱
- `send_time`: 发送时间（格式：HH:MM）

## 云端部署
本程序已配置为在Railway平台自动部署运行。