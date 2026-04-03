"""
图案提取工作流 - Streamlit Web 界面
用户上传图片，自动识别并提取被纯色分隔的图案，去背后打包下载
"""

import streamlit as st
import zipfile
import time
from PIL import Image
import numpy as np
import cv2
from io import BytesIO

# 页面配置
st.set_page_config(
    page_title="图案提取工具",
    page_icon="🎨",
    layout="centered"
)

# 标题和说明
st.title("🎨 图案提取工具")
st.markdown("""
上传图片，自动识别并提取被纯色分隔的图案，去背后打包下载。
""")

# 侧边栏设置
with st.sidebar:
    st.header("⚙️ 设置")
    st.markdown("---")
    
    # 尺寸设置
    st.subheader("📐 尺寸设置（可选）")
    use_resize = st.checkbox("调整图案尺寸", value=False)
    
    target_width = None
    target_height = None
    
    if use_resize:
        col1, col2 = st.columns(2)
        with col1:
            target_width = st.number_input("宽度(px)", min_value=10, max_value=2000, value=100, step=10)
        with col2:
            target_height = st.number_input("高度(px)", min_value=10, max_value=2000, value=100, step=10)
    
    st.markdown("---")
    st.markdown("**提示**：不设置尺寸则保持原大")


def detect_patterns(image: np.ndarray) -> list:
    """检测图片中被纯色分隔的图案区域"""
    # 预处理：灰度化 + 高斯模糊
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 边缘检测
    edges = cv2.Canny(blurred, 50, 150)
    
    # 形态学操作
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    
    # 轮廓检测
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 过滤并提取图案区域
    pattern_regions = []
    min_area = 1000
    img_area = image.shape[0] * image.shape[1]
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > min_area and area < img_area * 0.5:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 20 and h > 20:
                pattern_regions.append({"x": int(x), "y": int(y), "w": int(w), "h": int(h)})
    
    # 按面积排序
    pattern_regions.sort(key=lambda r: r["w"] * r["h"], reverse=True)
    return pattern_regions


def extract_pattern(image: np.ndarray, region: dict, target_width: int = None, target_height: int = None) -> Image.Image:
    """提取并去背单个图案"""
    x, y, w, h = region["x"], region["y"], region["w"], region["h"]
    
    # 确保不超出边界
    x = max(0, x)
    y = max(0, y)
    w = min(w, image.shape[1] - x)
    h = min(h, image.shape[0] - y)
    
    pattern = image[y:y+h, x:x+w]
    
    # 检测背景色（从四角取色）
    corners = [pattern[0, 0], pattern[0, -1], pattern[-1, 0], pattern[-1, -1]]
    corner_colors = np.array(corners)
    bg_color = np.median(corner_colors, axis=0).astype(np.uint8)
    
    # 边缘扫描去除背景
    alpha = np.ones((h, w), dtype=np.uint8) * 255
    tolerance = 40
    
    # 四边扫描
    for col in range(w):
        for row in range(h):
            pixel = pattern[row, col].astype(float)
            distance = np.sqrt(np.sum((pixel - bg_color) ** 2))
            if distance > tolerance:
                break
            alpha[row, col] = 0
    
    for col in range(w):
        for row in range(h-1, -1, -1):
            pixel = pattern[row, col].astype(float)
            distance = np.sqrt(np.sum((pixel - bg_color) ** 2))
            if distance > tolerance:
                break
            alpha[row, col] = 0
    
    for row in range(h):
        for col in range(w):
            pixel = pattern[row, col].astype(float)
            distance = np.sqrt(np.sum((pixel - bg_color) ** 2))
            if distance > tolerance:
                break
            alpha[row, col] = 0
    
    for row in range(h):
        for col in range(w-1, -1, -1):
            pixel = pattern[row, col].astype(float)
            distance = np.sqrt(np.sum((pixel - bg_color) ** 2))
            if distance > tolerance:
                break
            alpha[row, col] = 0
    
    # 边缘羽化
    alpha_blur = cv2.GaussianBlur(alpha.astype(float), (3, 3), 0)
    alpha_blur = np.clip(alpha_blur, 0, 255).astype(np.uint8)
    
    # 转换为PIL Image
    pattern_rgb = cv2.cvtColor(pattern, cv2.COLOR_BGR2RGB)
    pattern_pil = Image.fromarray(pattern_rgb)
    pattern_pil.putalpha(Image.fromarray(alpha_blur))
    
    # 调整尺寸
    if target_width or target_height:
        orig_w, orig_h = pattern_pil.size
        if target_width and target_height:
            ratio_w = target_width / orig_w
            ratio_h = target_height / orig_h
            ratio = min(ratio_w, ratio_h)
            new_w, new_h = int(orig_w * ratio), int(orig_h * ratio)
        elif target_width:
            ratio = target_width / orig_w
            new_w, new_h = target_width, int(orig_h * ratio)
        else:
            ratio = target_height / orig_h
            new_w, new_h = int(orig_w * ratio), target_height
        
        pattern_pil = pattern_pil.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    return pattern_pil


def process_image(image_bytes: bytes, target_width: int = None, target_height: int = None) -> tuple:
    """处理图片，返回ZIP数据和图案数量"""
    # 直接从字节读取图片
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        raise ValueError("无法解析图片格式")
    
    # 检测图案
    regions = detect_patterns(image)
    
    # 提取图案
    patterns = []
    for region in regions:
        pattern = extract_pattern(image, region, target_width, target_height)
        patterns.append(pattern)
    
    # 创建ZIP
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for idx, pattern in enumerate(patterns, start=1):
            img_buffer = BytesIO()
            pattern.save(img_buffer, format='PNG')
            zipf.writestr(f"pattern_{idx:03d}.png", img_buffer.getvalue())
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue(), len(patterns)


# 主界面 - 文件上传
st.markdown("### 📤 上传图片")
uploaded_file = st.file_uploader(
    "",
    type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'],
    label_visibility="collapsed",
    help="支持 PNG, JPG, GIF, BMP、WebP 格式"
)

# 预览和处理
if uploaded_file is not None:
    # 直接显示上传的图片（使用BytesIO，不依赖URL）
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("**上传的图片：**")
        # 使用 BytesIO 显示图片，不依赖URL
        img_display = Image.open(BytesIO(uploaded_file.getvalue()))
        st.image(img_display, use_container_width=True)
    
    with col2:
        st.markdown("**文件信息：**")
        st.write(f"- 文件名：{uploaded_file.name}")
        st.write(f"- 文件大小：{len(uploaded_file.getvalue()) / 1024:.1f} KB")
        st.write(f"- 文件类型：{uploaded_file.type}")
    
    # 开始处理
    st.markdown("---")
    if st.button("🚀 开始提取", type="primary", use_container_width=True):
        with st.spinner("正在处理，请稍候..."):
            try:
                # 直接使用上传的文件内容，不依赖URL
                image_bytes = uploaded_file.getvalue()
                
                # 处理图片
                zip_data, pattern_count = process_image(
                    image_bytes,
                    target_width if use_resize else None,
                    target_height if use_resize else None
                )
                
                st.success(f"✅ 成功识别出 {pattern_count} 个图案！")
                
                # 下载按钮
                st.markdown("### 📥 下载图案")
                
                st.download_button(
                    label="⬇️ 下载 ZIP 文件",
                    data=zip_data,
                    file_name=f"patterns_{int(time.time())}.zip",
                    mime="application/zip",
                    type="primary",
                    use_container_width=True
                )
                
                st.caption("📌 文件为PNG格式，可直接使用")
                
            except Exception as e:
                st.error(f"发生错误: {str(e)}")

# 使用说明
st.markdown("---")
with st.expander("📖 使用说明"):
    st.markdown("""
    1. **上传图片**：点击上方按钮选择图片文件
    2. **设置尺寸**（可选）：在左侧勾选"调整图案尺寸"并设置宽高
    3. **开始处理**：点击"开始提取"按钮
    4. **下载结果**：处理完成后点击下载按钮获取ZIP文件
    
    **功能特点**：
    - 🔍 自动识别被纯色分隔的图案
    - ✂️ 智能去除纯色背景
    - 📐 支持自定义图案尺寸（等比缩放）
    - 📦 批量打包下载
    
    **适用场景**：
    - 📦 电商图片处理
    - 🎨 设计素材提取
    - 📚 文档扫描去背景
    """)

# 页脚
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "🎨 图案提取工具 | Powered by OpenCV + Streamlit"
    "</div>",
    unsafe_allow_html=True
)
