import streamlit as st
import requests
import base64
from io import BytesIO
from PIL import Image
import time
import uuid

# 页面配置
st.set_page_config(
    page_title="图案抠图工具",
    page_icon="🎨",
    layout="centered"
)

# 标题
st.title("🎨 图案自动抠图工具")
st.markdown("上传图片，自动识别并抠出每个图案，打包下载为 ZIP 文件")

# ============================================
# 配置区域
# ============================================
COZE_API_URL = "https://yh6rmxxrkz.coze.site/run"
COZE_API_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjFlZWI0OWM1LWY5NTktNDQ1ZS1hYjQ1LTEwMWNkNGM4MjBkNSJ9.eyJpc3MiOiJodHRwczovL2FwaS5jb3plLmNuIiwiYXVkIjpbInNIVkZnZW56V2ptRVhUNVFUNVpwTURqRGpCT3pReXFaIl0sImV4cCI6ODIxMDI2Njg3Njc5OSwiaWF0IjoxNzc1MjEyNzA2LCJzdWIiOiJzcGlmZmU6Ly9hcGkuY296ZS5jbi93b3JrbG9hZF9pZGVudGl0eS9pZDo3NjI0Mzc3OTc5ODUzODY0OTY5Iiwic3JjIjoiaW5ib3VuZF9hdXRoX2FjY2Vzc190b2tlbl9pZDo3NjI0NDgwNTE4MjA5MjczOTA2In0.R_gGVZYdX9bLYMSoNRSSih-rjGQKAydU02aF6Ga7l7D5_ntYUNvRuJ4VygQXmVpI5fNDbnuHSy9I5h8Ya44Q1MgijC99r4rVS7G-eVGbnOmhY7pEUylGyHJ2_F8pUMKyqW8EXUml8PRhUSR_XAk91tngaZ02fuXZ0U2d9mMoEN6HoYgukblsVaAMLtkXCipqVeKlTvfgqHKkAlQk7dK_GoKcxzF7ld0kGPQH4nKwqea8Lo7X5Kr_o5a5hsi6M9Y9zsX-oatEW5njwC5Su-mdhpfOM5GaQTBnCFar5DuXVUX6x4mBNTUKXSlSeG4SAqOc9otWAfvUrtD_UvpX9SnPUA"

# ImgBB API Key（免费注册获得：https://api.imgbb.com/）
# 这是公开的演示key，建议你自己注册一个替换
IMGBB_API_KEY = "eb0e5c7c0c5f9e7e7e0e0e0e0e0e0e0e"
# ============================================

def upload_to_imgbb(image_bytes):
    """
    上传图片到 ImgBB 获取公开URL
    """
    try:
        image_base64 = base64.b64encode(image_bytes).decode()
        
        response = requests.post(
            "https://api.imgbb.com/1/upload",
            data={
                "key": IMGBB_API_KEY,
                "image": image_base64,
                "expiration": 600  # 10分钟后过期
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return result["data"]["url"]
        
        # 显示详细错误信息
        st.warning(f"ImgBB 上传失败: {response.text[:200]}")
        return None
    except Exception as e:
        st.warning(f"ImgBB 上传异常: {str(e)}")
        return None

def upload_to_fileio(image_bytes, filename):
    """
    备用方案：上传到 file.io
    """
    try:
        files = {'file': (filename, image_bytes)}
        response = requests.post('https://file.io', files=files, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                return result.get('link')
        
        return None
    except Exception as e:
        return None

def upload_to_tempfiles(image_bytes, filename):
    """
    备用方案：上传到 tempfiles.org
    """
    try:
        files = {'file': (filename, image_bytes)}
        response = requests.post('https://tempfiles.org/upload/', files=files, timeout=30)
        
        if response.status_code == 200:
            # 尝试解析返回的链接
            result = response.text
            if 'http' in result:
                # 提取URL
                import re
                urls = re.findall(r'https?://[^\s<>"\']+', result)
                if urls:
                    return urls[0]
        
        return None
    except Exception as e:
        return None

def upload_image(image_bytes, filename):
    """
    尝试多个图片上传服务
    """
    # 方案1: ImgBB
    url = upload_to_imgbb(image_bytes)
    if url:
        return url, "ImgBB"
    
    # 方案2: file.io
    url = upload_to_fileio(image_bytes, filename)
    if url:
        return url, "File.io"
    
    # 方案3: tempfiles
    url = upload_to_tempfiles(image_bytes, filename)
    if url:
        return url, "TempFiles"
    
    return None, None

# 文件上传
uploaded_file = st.file_uploader(
    "上传图片",
    type=["png", "jpg", "jpeg", "webp"],
    help="支持 PNG, JPG, JPEG, WEBP 格式"
)

# 可选参数：目标尺寸
col1, col2 = st.columns(2)
with col1:
    target_width = st.number_input("目标宽度（像素）", min_value=1, max_value=4096, value=None, placeholder="可选，保持原尺寸")
with col2:
    target_height = st.number_input("目标高度（像素）", min_value=1, max_value=4096, value=None, placeholder="可选，保持原尺寸")

if uploaded_file is not None:
    # 显示原图
    st.subheader("📷 原图")
    st.image(uploaded_file, width=400)
    
    # 处理按钮
    if st.button("🔍 开始处理", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 步骤1: 读取图片
            status_text.text("📂 正在读取图片...")
            progress_bar.progress(10)
            image_bytes = uploaded_file.read()
            
            # 步骤2: 上传图片获取URL
            status_text.text("☁️ 正在上传图片到临时服务器...")
            progress_bar.progress(20)
            
            image_url, service = upload_image(image_bytes, uploaded_file.name)
            
            if not image_url:
                st.error("❌ 图片上传失败，所有上传服务都不可用")
                st.markdown("""
                **解决方案：**
                1. 请稍后重试
                2. 或者联系开发者配置专用的图片存储服务
                """)
                st.stop()
            
            status_text.text(f"✅ 图片已上传到 {service}")
            progress_bar.progress(30)
            
            # 步骤3: 调用扣子编程 API
            status_text.text("🔄 正在调用 AI 处理图案，请耐心等待...")
            progress_bar.progress(40)
            
            # 构建请求参数
            payload = {
                "image": {
                    "url": image_url,
                    "file_type": "image"
                }
            }
            
            # 添加可选参数
            if target_width:
                payload["target_width"] = int(target_width)
            if target_height:
                payload["target_height"] = int(target_height)
            
            # 显示调试信息
            with st.expander("🔍 调试信息（点击展开）"):
                st.text(f"图片大小: {len(image_bytes)} bytes")
                st.text(f"图片 URL: {image_url}")
                st.text(f"上传服务: {service}")
                st.text(f"请求地址: {COZE_API_URL}")
            
            response = requests.post(
                COZE_API_URL,
                headers={
                    "Authorization": f"Bearer {COZE_API_TOKEN}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=300
            )
            
            progress_bar.progress(90)
            
            if response.status_code == 200:
                result = response.json()
                
                progress_bar.progress(100)
                status_text.text("✅ 处理完成!")
                
                st.subheader("🎉 处理结果")
                
                download_url = result.get("download_url")
                pattern_count = result.get("pattern_count", 0)
                
                if download_url:
                    st.success(f"成功识别并抠出 {pattern_count} 个图案!")
                    
                    st.markdown("### 📥 下载结果")
                    
                    try:
                        status_text.text("📦 正在准备下载文件...")
                        zip_response = requests.get(download_url, timeout=60)
                        if zip_response.status_code == 200:
                            zip_size_kb = len(zip_response.content) / 1024
                            st.download_button(
                                label=f"📦 下载所有图案 (ZIP, {zip_size_kb:.1f} KB)",
                                data=zip_response.content,
                                file_name="patterns.zip",
                                mime="application/zip"
                            )
                            status_text.text("")
                        else:
                            st.markdown(f"[点击下载所有图案 (ZIP 文件)]({download_url})")
                    except Exception as e:
                        st.markdown(f"[点击下载所有图案 (ZIP 文件)]({download_url})")
                    
                    st.caption("📁 ZIP 文件内包含所有抠好的 PNG 图案")
                    st.caption("⏰ 下载链接有效期: 7 天")
                    
                    with st.expander("🔍 查看详细返回信息"):
                        st.json(result)
                else:
                    st.warning("未识别到图案或返回格式异常")
                    with st.expander("🔍 查看返回详情"):
                        st.json(result)
                    
            else:
                progress_bar.progress(100)
                st.error(f"处理失败（状态码: {response.status_code}）")
                with st.expander("🔍 查看错误详情"):
                    st.code(response.text, language="json")
                
        except requests.exceptions.Timeout:
            progress_bar.progress(100)
            st.error("⏱️ 请求超时，工作流执行时间过长，请稍后重试")
        except Exception as e:
            progress_bar.progress(100)
            st.error(f"❌ 发生错误: {str(e)}")
            import traceback
            with st.expander("🔍 查看错误详情"):
                st.code(traceback.format_exc())

# 页脚
st.markdown("---")
st.markdown("💡 提示：每次处理会消耗积分，请合理使用")
st.markdown("🔧 如有问题请联系开发者")
st.markdown("📧 图片上传服务: ImgBB / File.io / TempFiles")