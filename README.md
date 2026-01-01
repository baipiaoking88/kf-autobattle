# kf-autobattle

[绯月](https://bbs.kfpromax.com)的老争夺自动争夺脚本

## 使用方法

### 1. 获取登录凭证
```bash
python3 get_cookies.py
```
- 输入登录URL
- 输入用户名和密码
- 脚本会自动登录并保存cookies到`session_cookies.json`

### 2. 执行自动战斗
```bash
python3 auto_battle.py
```
- 脚本会自动加载cookies并开始战斗
- 持续战斗直到结束
- 显示战斗进度和最终统计

## 文件说明

- `get_cookies.py` - 获取登录凭证脚本
- `auto_battle.py` - 自动争夺脚本  
- `session_cookies.json` - 存储会话cookies的文件

## 注意事项

- 首次使用需要先运行`get_cookies.py`获取登录凭证
- 请合理使用，避免对服务器造成过大压力

## 依赖

- requests>=2.25.1
- beautifulsoup4>=4.9.3

如需安装依赖：
```bash
pip3 install -r requirements.txt
```
