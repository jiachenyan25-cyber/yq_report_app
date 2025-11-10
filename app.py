import streamlit as st
from datetime import datetime
from io import BytesIO
import re

# ---- 安全导入 docx ----
try:
    from docx import Document
except ModuleNotFoundError:
    st.error("❌ 缺少依赖：python-docx。请在仓库中添加 requirements.txt 文件并包含 'python-docx'。")
    st.stop()

# ---- 页面配置 ----
st.set_page_config(page_title="舆情快报自动生成系统", layout="centered")

TITLE = "舆情快报"
SECTION_INDENT = "　　"

# ---- 基础函数 ----
def ensure_period(text: str) -> str:
    """若结尾无句号则自动补全。"""
    text = text.strip()
    if not text:
        return ""
    if text.endswith(("。", ".", "！", "?", "？", "!")):
        return text
    return text + "。"

def validate_time_hms(t: str) -> bool:
    """验证 00:00:00 格式"""
    return bool(re.match(r"^(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d$", t.strip()))

def validate_time_hm(t: str) -> bool:
    """验证 00:00 格式"""
    return bool(re.match(r"^(?:[01]\d|2[0-3]):[0-5]\d$", t.strip()))

def make_docx(report_text: str) -> bytes:
    """生成 DOCX 文件"""
    doc = Document()
    for line in report_text.split("\n"):
        doc.add_paragraph(line)
    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio.read()

def build_report(date_obj, time_str, platform, author, author_id, region, other_region,
                 content, count, likes, comments, spread_extra,
                 assigned_to, has_order, deleted, delete_time, delete_type, guidance_text, links):
    
    date_str = date_obj.strftime("%Y年%m月%d日")
    full_time = f"{date_str}{time_str}"
    author_id_part = f"（ID：{author_id}）" if author_id else ""

    if region == "其他" and other_region.strip():
        region_text = f"{other_region.strip()}地区"
    else:
        region_text = f"{region}地区" if region else ""

    spread_text = ensure_period(spread_extra) if spread_extra.strip() else ""

    delete_text = ""
    if deleted:
        if delete_time:
            delete_text = f"，{delete_type}于{delete_time}已删除"
        else:
            delete_text = f"，{delete_type}已删除"

    order_text = f"，并向{assigned_to}下发网络舆情交办单" if has_order and assigned_to else ""

    part1 = (
        f"{SECTION_INDENT}一、基本情况\n"
        f"{SECTION_INDENT}{full_time}，{platform}用户“{author}”{author_id_part}发布{delete_type}称，"
        f"{region_text}{ensure_period(content)}"
    )

    part2 = (
        f"{SECTION_INDENT}二、传播情况\n"
        f"{SECTION_INDENT}该系列{delete_type}共{count}条，累计点赞{likes}次、{comments}条评论。{spread_text}"
    )

    part3 = (
        f"{SECTION_INDENT}三、工作措施\n"
        f"{SECTION_INDENT}市委网信办已第一时间交办{assigned_to}核实处置{order_text}{delete_text}。"
        f"\n{SECTION_INDENT}{ensure_period(guidance_text)}"
        f"市委网信办将持续关注相关网上动态。"
    )

    link_line = "、".join([x.strip() for x in links.split(",") if x.strip()])
    part4 = f"{SECTION_INDENT}四、链接：{link_line}" if link_line else f"{SECTION_INDENT}四、链接："

    return f"{TITLE}\n{part1}\n{part2}\n{part3}\n{part4}"

# ---- Streamlit 页面 ----
st.title("🧾 舆情快报自动生成系统（V3.5）")

# --- 一、基本情况 ---
st.subheader("一、基本情况")

col1, col2 = st.columns(2)
with col1:
    date_obj = st.date_input("事件日期", datetime.today())
with col2:
    time_str = st.text_input("具体时间（格式：00:00:00，例如09:08:22）", "")

platform = st.text_input("平台名称（如抖音/微博等）", "抖音")
author = st.text_input("发布者昵称")
author_id = st.text_input("发布者ID（可选）")

region_options = ["湖滨区", "陕州区", "灵宝市", "义马市", "渑池县", "卢氏县", "示范区", "经开区", "其他"]
region = st.selectbox("涉事地域", region_options)
other_region = ""
if region == "其他":
    other_region = st.text_input("进一步精确的地域名称")

content = st.text_area("视频/帖文主要内容（简要描述）")

# --- 二、传播情况 ---
st.subheader("二、传播情况")
col3, col4, col5 = st.columns(3)
with col3:
    count = st.number_input("视频/帖文数量", min_value=1, value=1)
with col4:
    likes = st.text_input("累计点赞次数")
with col5:
    comments = st.text_input("累计评论条数")
spread_extra = st.text_area("传播补充说明（如媒体转发、话题热度等）")

# --- 三、工作措施 ---
st.subheader("三、工作措施")
assigned_to = st.text_input("交办对象（如某区/镇/部门）")
has_order = st.checkbox("是否下发网络舆情交办单")

st.markdown("**贴文删除情况：**")
deleted = st.checkbox("是否已删除")
delete_time = ""
delete_type = "贴文"

if deleted:
    delete_type = st.selectbox("选择贴文类型", ["视频", "图文", "评论", "综合内容"])
    delete_time = st.text_input("删除时间（格式：00:00，例如09:22）", "")

# --- 指导意见 ---
st.markdown("**指导意见内容（可选/可改）：**")
guidance_options = {
    "常规处置建议": "近期类似情况多发，建议各县（市、区）职能部门加强对于此类现象的现场管控和线下疏导。",
    "舆论监测建议": "请各地持续加强网络舆情监测和源头排查，及时发现并妥善处置苗头性信息。",
    "信息发布建议": "各地在后续信息发布中应注意口径统一、信息准确，避免造成公众误解。",
    "线下协调建议": "请相关部门加强与属地公安、应急、交通等单位的沟通协调，确保线下稳控有力。",
    "自定义": "",
}
guidance_choice = st.selectbox("选择指导意见模板", list(guidance_options.keys()))
if guidance_choice == "自定义":
    guidance_text = st.text_area("请输入自定义指导意见内容")
else:
    guidance_text = guidance_options[guidance_choice]

# --- 四、链接信息 ---
st.subheader("四、链接信息")
links = st.text_area("视频或帖文链接（多条可用逗号分隔）")

# --- 生成按钮 ---
if st.button("✨ 生成舆情快报"):
    if not author.strip() or not content.strip():
        st.error("请填写【发布者昵称】和【主要内容】。")
    elif not validate_time_hms(time_str):
        st.error("❌ 时间格式错误，请按 00:00:00（如 09:08:22）格式填写。")
    elif deleted and delete_time and not validate_time_hm(delete_time):
        st.error("❌ 删除时间格式错误，请按 00:00（如 09:22）格式填写。")
    else:
        report = build_report(
            date_obj, time_str, platform, author, author_id, region, other_region,
            content, count, likes, comments, spread_extra,
            assigned_to, has_order, deleted, delete_time, delete_type, guidance_text, links
        )
        st.success("✅ 已生成舆情快报")
        st.code(report, language="markdown")

        st.download_button("💾 下载 TXT", data=report.encode("utf-8"),
                           file_name="舆情快报.txt", mime="text/plain")

        docx_bytes = make_docx(report)
        st.download_button("💾 下载 DOCX", data=docx_bytes,
                           file_name="舆情快报.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

st.caption("V3.5版：优化错误提示、自动补句号、指导意见模板+自定义可共存、增强云端兼容性。")
