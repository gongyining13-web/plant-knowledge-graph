#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
荆楚植物文化知识图谱 - Web界面
纯Streamlit原生组件版，不使用手写HTML，杜绝标签泄漏
"""

import streamlit as st
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from api.free_qa_system import PlantQASystem

# 页面配置
st.set_page_config(
    page_title="荆楚植物文化图谱",
    page_icon="🌿",
    layout="wide"
)

# 初始化问答系统（缓存）
@st.cache_resource
def init_qa():
    return PlantQASystem("bolt://localhost:7687", "neo4j", "12345678")

qa = init_qa()

# ------------------------------------------------------------
# 侧边栏：植物列表 + 详情卡片（纯Streamlit组件，无手写HTML）
# ------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/plant-under-sun.png", width=80)
    st.markdown("## 📚 植物知识库")
    st.caption(f"共收录 {len(qa.plant_names)} 种荆楚地区植物")
    
    # 植物选择下拉框
    selected_plant = st.selectbox(
        "🌱 选择植物查看详情",
        qa.plant_names,
        index=0,
        key="plant_selector"
    )
    
    if selected_plant:
        detail = qa.get_plant_detail(selected_plant)
        if detail:
            # ---------- 使用原生Streamlit组件展示信息卡片 ----------
            st.markdown("---")
            st.subheader(f"🌿 {detail['name']}")
            st.caption(f"*{detail['latin']}*")
            
            # 科属
            st.markdown("**🏷️ 科属**")
            st.write(f"{detail['family']} · {detail['genus']}")
            
            # 分布
            st.markdown("**🗺️ 分布**")
            st.write(detail['distribution'])
            
            # 文化象征（简要）
            st.markdown("**✨ 文化象征**")
            st.write(detail['cultural_symbol'])
            
            # 详细象征（如果有）
            if detail['symbols']:
                st.markdown("**🔖 详细象征**")
                # 以标签形式展示，使用st.chip或st.write均可，这里简单用逗号连接
                st.write("、".join(detail['symbols']))
            
            # 药用价值
            if detail['medicinal']:
                st.markdown("**💊 药用价值**")
                st.write("、".join(detail['medicinal']))
            
            # 民俗用途
            if detail['folk_use'] and detail['folk_use'] != '暂无民俗用途':
                st.markdown("**🏮 民俗用途**")
                st.write(detail['folk_use'])
            
            # 相关节日
            if detail['festivals']:
                st.markdown("**🎉 相关节日**")
                st.write("、".join(detail['festivals']))
            
            # 文献记载
            if detail['literature']:
                st.markdown("**📖 文献记载**")
                st.write("、".join(detail['literature']))
            
            st.markdown("---")
    
    st.markdown("---")
    st.markdown("### 💡 试试这样问")
    if st.button("兰有什么文化象征？", key="ex1"):
        st.session_state.question = "兰有什么文化象征？"
    if st.button("端午节和什么植物有关？", key="ex2"):
        st.session_state.question = "端午节和什么植物有关？"
    if st.button("梅花分布在哪里？", key="ex3"):
        st.session_state.question = "梅花分布在哪里？"
    if st.button("菊花的药用价值", key="ex4"):
        st.session_state.question = "菊花的药用价值是什么？"

# ------------------------------------------------------------
# 主界面：问答区域
# ------------------------------------------------------------
st.title("🌿 荆楚植物文化知识图谱问答系统")
st.markdown("基于50种荆楚地区植物的文化、药用、民俗、分布等数据构建的智能问答系统。")

# 输入框和提问按钮
col1, col2 = st.columns([4, 1])
with col1:
    default_question = st.session_state.get("question", "")
    question = st.text_input(
        "💬 请输入您的问题：",
        placeholder="例如：兰有什么文化象征？",
        value=default_question,
        label_visibility="collapsed"
    )
with col2:
    ask_button = st.button("🚀 提问", type="primary", use_container_width=True)

# 处理提问
if ask_button and question:
    with st.spinner("🔍 正在查询知识图谱..."):
        answer = qa.answer(question)
    
    st.markdown("### 📝 回答")
    if "暂未收录" in answer:
        st.warning(answer)
    elif "请明确指定" in answer:
        st.info(answer)
    else:
        st.success(answer)
    
    # 保存到历史记录
    if "history" not in st.session_state:
        st.session_state.history = []
    st.session_state.history.insert(0, {
        "question": question,
        "answer": answer
    })
    
    # 清除 session_state 中的 question，避免下次自动填充
    if "question" in st.session_state:
        del st.session_state.question

# 显示历史记录
if "history" in st.session_state and st.session_state.history:
    st.markdown("---")
    st.subheader("📜 最近提问")
    for i, h in enumerate(st.session_state.history[:5]):
        with st.expander(f"Q{i+1}: {h['question'][:30]}..."):
            st.write(h['answer'])

# 页脚
st.markdown("---")
st.markdown(
    "🌿 数据来源：荆楚植物文化图谱 · Neo4j知识图谱 · 免费问答系统",
    unsafe_allow_html=False  # 纯文本，不需要HTML
)