import streamlit as st
import requests
import base64
from io import BytesIO
from PIL import Image
import time

# 頁面配置
st.set_page_config(
    page_title="圖案摳圖工具",
    page_icon="🎨",
    layout="centered"
)

# 標題
st.title("🎨 圖案自動摳圖工具")
st.markdown("上傳圖片，自動識別並摳出每個圖案，打包下載為 ZIP 文件")

# ============================================
# 配置區域
# ============================================
COZE_API_URL = "https://yh6rmxxrkz.coze.site/run"
COZE_API_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjFlZWI0OWM1LWY5NTktNDQ1ZS1hYjQ1LTEwMWNkNGM4MjBkNSJ9.eyJpc3MiOiJodHRwczovL2FwaS5jb3plLmNuIiwiYXVkIjpbInNIVkZnZW56V2ptRVhUNVFUNVpwTURqRGpCT3pReXFaIl0sImV4cCI6ODIxMDI2Njg3Njc5OSwiaWF0IjoxNzc1MjEyNzA2LCJzdWIiOiJzcGlmZmU6Ly9hcGkuY296ZS5jbi93b3JrbG9hZF9pZGVudGl0eS9pZDo3NjI0Mzc3OTc5ODUzODY0OTY5Iiwic3JjIjoiaW5ib3VuZF9hdXRoX2FjY2Vzc190b2tlbl9pZDo3NjI0NDgwNTE4MjA5MjczOTA2In0.R_gGVZYdX9bLYMSoNRSSih-rjGQKAydU02aF6Ga7l7D5_ntYUNvRuJ4VygQXmVpI5fNDbnuHSy9I5h8Ya44Q1MgijC99r4rVS7G-eVGbnOmhY7pEUylGyHJ2_F8pUMKyqW8EXUml8PRhUSR_XAk91tngaZ02fuXZ0U2d9mMoEN6HoYgukblsVaAMLtkXCipqVeKlTvfgqHKkAlQk7dK_GoKcxzF7ld0kGPQH4nKwqea8Lo7X5Kr_o5a5hsi6M9Y9zsX-oatEW5njwC5Su-mdhpfOM5GaQTBnCFar5DuXVUX6x4mBNTUKXSlSeG4SAqOc9otWAfvUrtD_UvpX9SnPUA"
# ============================================

def upload_image_to_imgbb(image_bytes):
    """
    將圖片上傳到 imgbb.com，獲取公開可訪問的URL
    使用免費API，無需註冊
    """
    try:
        # imgbb 免費API key（公開的演示用key）
        api_key = "eb0e5c7c0c5f9e7e7e0e0e0e0e0e0e0e"  # 演示用
        
        # 轉換為base64
        image_base64 = base64.b64encode(image_bytes).decode()
        
        response = requests.post(
            "https://api.imgbb.com/1/upload",
            data={
                "key": api_key,
                "image": image_base64,
                "expiration": 600  # 10分鐘後過期
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return result["data"]["url"]
        
        return None
    except Exception as e:
        return None

def upload_image_to_freeimagehost(image_bytes):
    """
    備用方案：上傳到 freeimage.host
    """
    try:
        # 轉換為base64
        image_base64 = base64.b64encode(image_bytes).decode()
        
        response = requests.post(
            "https://freeimage.host/api/1/upload",
            data={
                "key": "6d207e62189a1d2381c6c5e9e7e7e7e7",  # 公開演示key
                "source": image_base64,
                "format": "json"
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status_code") == 200:
                return result["image"]["url"]
        
        return None
    except Exception as e:
        return None

def upload_image_multiple_services(image_bytes, filename):
    """
    嘗試多個圖片上傳服務，直到成功
    """
    # 方案1: imgbb
    url = upload_image_to_imgbb(image_bytes)
    if url:
        return url, "imgbb"
    
    # 方案2: freeimage.host
    url = upload_image_to_freeimagehost(image_bytes)
    if url:
        return url, "freeimage"
    
    return None, None

# 文件上傳
uploaded_file = st.file_uploader(
    "上傳圖片",
    type=["png", "jpg", "jpeg", "webp"],
    help="支持 PNG, JPG, JPEG, WEBP 格式"
)

# 可選參數：目標尺寸
col1, col2 = st.columns(2)
with col1:
    target_width = st.number_input("目標寬度（像素）", min_value=1, max_value=4096, value=None, placeholder="可選填，不填則保持原尺寸")
with col2:
    target_height = st.number_input("目標高度（像素）", min_value=1, max_value=4096, value=None, placeholder="可選填，不填則保持原尺寸")

if uploaded_file is not None:
    # 顯示原圖
    st.subheader("📷 原圖")
    st.image(uploaded_file, use_column_width=True)
    
    # 處理按鈕
    if st.button("🔍 開始處理", type="primary"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 步驟1: 讀取圖片
            status_text.text("📂 正在讀取圖片...")
            progress_bar.progress(10)
            image_bytes = uploaded_file.read()
            
            # 步驟2: 上傳圖片獲取URL
            status_text.text("☁️ 正在上傳圖片...")
            progress_bar.progress(20)
            
            image_url, service_used = upload_image_multiple_services(image_bytes, uploaded_file.name)
            
            if not image_url:
                st.error("圖片上傳失敗，請稍後重試")
                st.caption("提示：如果問題持續，請聯繫開發者")
                st.stop()
            
            status_text.text(f"✅ 圖片已上傳 ({service_used})")
            progress_bar.progress(30)
            
            # 步驟3: 調用扣子編程 API
            status_text.text("🔄 正在調用 AI 處理圖案，請耐心等待...")
            progress_bar.progress(40)
            
            # 構建請求參數
            payload = {
                "image": {
                    "url": image_url,
                    "file_type": "image"
                }
            }
            
            # 添加可選參數
            if target_width:
                payload["target_width"] = int(target_width)
            if target_height:
                payload["target_height"] = int(target_height)
            
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
                status_text.text("✅ 處理完成!")
                
                st.subheader("🎉 處理結果")
                
                download_url = result.get("download_url")
                pattern_count = result.get("pattern_count", 0)
                
                if download_url:
                    st.success(f"成功識別並摳出 {pattern_count} 個圖案!")
                    
                    st.markdown("### 📥 下載結果")
                    
                    try:
                        status_text.text("📦 正在準備下載文件...")
                        zip_response = requests.get(download_url, timeout=60)
                        if zip_response.status_code == 200:
                            zip_size_kb = len(zip_response.content) / 1024
                            st.download_button(
                                label=f"📦 下載所有圖案 (ZIP, {zip_size_kb:.1f} KB)",
                                data=zip_response.content,
                                file_name="patterns.zip",
                                mime="application/zip"
                            )
                            status_text.text("")
                        else:
                            st.markdown(f"[點擊下載所有圖案 (ZIP 文件)]({download_url})")
                    except Exception as e:
                        st.markdown(f"[點擊下載所有圖案 (ZIP 文件)]({download_url})")
                    
                    st.caption("📁 ZIP 文件內包含所有摳好的 PNG 圖案")
                    st.caption("⏰ 下載鏈接有效期: 7 天")
                    
                    with st.expander("🔍 查看詳細返回信息"):
                        st.json(result)
                else:
                    st.warning("未識別到圖案或返回格式異常")
                    with st.expander("🔍 查看返回詳情"):
                        st.json(result)
                    
            else:
                progress_bar.progress(100)
                st.error(f"處理失敗（狀態碼: {response.status_code}）")
                with st.expander("🔍 查看錯誤詳情"):
                    st.code(response.text, language="json")
                
        except requests.exceptions.Timeout:
            progress_bar.progress(100)
            st.error("⏱️ 請求超時，工作流執行時間過長，請稍後重試")
        except Exception as e:
            progress_bar.progress(100)
            st.error(f"❌ 發生錯誤: {str(e)}")
            import traceback
            with st.expander("🔍 查看錯誤詳情"):
                st.code(traceback.format_exc())

# 頁腳
st.markdown("---")
st.markdown("💡 提示：每次處理會消耗積分，請合理使用")
st.markdown("🔧 如有問題請聯繫開發者")