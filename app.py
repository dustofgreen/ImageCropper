import streamlit as st
import requests
import base64
from io import BytesIO
from PIL import Image
import time

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
# ============================================

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
            image_base64 = base64.b64encode(image_bytes).decode()
            
            # 获取图片格式
            file_extension = uploaded_file.name.split('.')[-1].lower()
            mime_type = {
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'webp': 'image/webp'
            }.get(file_extension, 'image/png')
            
            # 使用 data URL 格式
            data_url = f"data:{mime_type};base64,{image_base64}"
            
            status_text.text("✅ 图片已准备完成")
            progress_bar.progress(30)
            
            # 步骤2: 调用扣子编程 API
            status_text.text("🔄 正在调用 AI 处理图案，请耐心等待...")
            progress_bar.progress(40)
            
            # 构建请求参数
            payload = {
                "image": {
                    "url": data_url,
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
                st.text(f"Data URL 长度: {len(data_url)} chars")
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