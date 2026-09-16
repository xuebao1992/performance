# 雪豹市场部绩效考核工作台 - 在线版

## 功能说明
- 前端：HTML工作台（打分、计算、汇总、打印）
- 后端：Python Flask，负责调用飞书API
- 数据存储：飞书多维表格（实时同步）

## 本地运行
```bash
pip install flask gunicorn
python server.py
# 打开 http://localhost:5000
```

## 部署到 Render（免费）

### 方法一：通过 render.yaml 一键部署（推荐）
1. 把这个项目上传到 GitHub
2. 登录 https://render.com
3. 点 "New" → "Web Service"
4. 选择你刚上传的 GitHub 仓库
5. Render 会自动识别 render.yaml 配置
6. 点 "Create Web Service"
7. 等待部署完成（约2-3分钟），会得到一个 https://xxx.onrender.com 的网址

### 方法二：手动配置
1. 登录 https://render.com
2. 点 "New" → "Web Service"
3. 连接 GitHub 仓库
4. 配置：
   - Runtime: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn server:app --bind 0.0.0.0:$PORT`
5. 添加环境变量：
   - FEISHU_APP_ID = cli_aa23415d8c781bb7
   - FEISHU_APP_SECRET = w4NtPJV1MuJkdTqDoWiMBcpSLgqkFth1
   - BITABLE_APP_TOKEN = SUCswFlF5i3zwxkrHADci1Emnl3
   - BITABLE_TABLE_ID = tblUq5sXETfPDOwH
6. 点 "Create Web Service"

## 数据迁移（从本地版迁移到在线版）
1. 先打开本地版工作台，点左侧"数据备份"→"导出数据"，下载 JSON 文件
2. 打开在线版工作台，点"数据备份"→"导入数据"，选择刚才的 JSON 文件
3. 导入后，数据会自动同步到飞书多维表格

## 使用说明
- 你和老板都访问同一个网址（https://xxx.onrender.com）
- 老板打完分，数据自动保存到飞书，你刷新页面就能看到
- 不需要再导出导入文件
- 免费版长时间不访问会休眠，第一次打开可能慢3-5秒

## 飞书多维表格
数据存在这个多维表格里：
https://e0gxuujsk20.feishu.cn/wiki/SUCswFlF5i3zwxkrHADci1Emnl3

每条记录是一个员工一个月的评分数据（JSON格式）。
