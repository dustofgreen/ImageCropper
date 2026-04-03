#图案提取工作流 - Streamlit Web 应用

## 概述
这是一个独立的 Web 应用，用户可以直接在浏览器中上传图片，自动识别并提取被纯色分隔的图案，去背后打包下载。

## 功能特点
- 🔍 自动识别被纯色分隔的图案
- ✂️ 智能去除纯色背景
- 📐 支持自定义图案尺寸（等比缩放）
- 📦 批量打包下载为 ZIP

## 部署到 Streamlit Cloud

### 步骤 1: 推送到 GitHub
```bash
# 创建新仓库或使用现有仓库
git init
git add .
git commit -m "feat: 添加图案提取 Streamlit 应用"
git remote add origin https://github.com/你的用户名/图案提取工具.git
git push -u origin main
```

### 步骤 2: 部署到 Streamlit Cloud
1. 访问 [share.streamlit.io](https://share.streamlit.io)
2. 使用 GitHub 登录
3. 点击 "New app"
4. 选择你的仓库和分支
5. 设置主文件路径：`app.py`
6. 点击 "Deploy!"

### 步骤 3: 完成！
部署成功后，你会获得一个公开的 URL，例如：
`https://你的用户名-pattern-extractor.streamlit.app`

## 本地运行

```bash
# 安装依赖
pip install streamlit opencv-python-headless pillow numpy

# 运行应用
streamlit run app.py
```

## API 参数

无 - 这是一个独立的 Web 应用，所有处理在浏览器中完成。

## 技术栈

- **Streamlit**: Web 界面框架
- **OpenCV**: 图像处理和边缘检测
- **Pillow**: 图像格式处理和透明通道
- **NumPy**: 数值计算

## 许可证

MIT License
