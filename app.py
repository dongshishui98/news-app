#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
新闻简报生成器 - Streamlit 网页版
按用户要求布局：标题、搜索框、按钮、说明、结果
"""
import streamlit as st
import sys
import os
from datetime import datetime

# 设置路径
sys.path.insert(0, 'C:/Users/Administrator/Documents/Obsidian Vault/d_AI工具箱/爬虫/新闻')

# 页面配置
st.set_page_config(page_title="News Report Generator", page_icon="N")

# ===== 1. 标题 =====
st.title("News Report Generator")

# ===== 2. 说明文本 =====
st.markdown("""
This tool automatically crawls news from NetEase and generates a report.
- Default topic: US-Israel-Iran War
- Default source: NetEase News
- Each report includes: date, time, source, image, link, hot score
""")

# ===== 3. 搜索框（设置）=====
col1, col2, col3 = st.columns(3)

with col1:
    topic = st.selectbox(
        "Topic:",
        ["科技", "国际", "国内", "AI", "股市原油"],
        index=0
    )

with col2:
    keywords = st.text_input("Keywords:", value="")

with col3:
    count = st.number_input("Number:", min_value=5, max_value=20, value=10)

# ===== 4. 按钮 =====
if st.button("Generate Report"):
    # 导入爬虫模块
    import sys
    sys.path.insert(0, 'C:/Users/Administrator/Documents/Obsidian Vault/d_AI工具箱/爬虫/新闻')
    import news_crawler

    with st.spinner("Crawling... Please wait..."):
        # 处理关键词
        keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]

        # 运行爬虫
        filename, results = news_crawler.main(topic=topic, keywords=keyword_list, count=count)

        if results:
            # ===== 5. 结果框 =====
            st.markdown("---")
            st.subheader(f"Report: {topic}")

            for i, news in enumerate(results, 1):
                st.markdown(f"### {i}. {news['title']}")

                # 图片
                if news['image']:
                    st.image(news['image'], width=500)

                # 元信息
                col_time, col_source, col_hot = st.columns(3)
                with col_time:
                    st.caption(f"Time: {news['time']}")
                with col_source:
                    st.caption(f"Source: {news['source']}")
                with col_hot:
                    st.caption(f"Hot: {news['hot']}")

                # 摘要
                if news['content']:
                    st.text(news['content'][:200] + "...")

                # 链接
                st.markdown(f"[Read More]({news['url']})")
                st.markdown("---")

            st.success(f"Done! {len(results)} news crawled.")
        else:
            st.error("No news found. Try different keywords.")
else:
    st.info("Click 'Generate Report' button to start.")
