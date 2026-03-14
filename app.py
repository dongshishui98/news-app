#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
新闻简报生成器 - Streamlit 网页版
"""
import streamlit as st
import requests
import re
import json
import time
import random
from bs4 import BeautifulSoup
import urllib.parse
from datetime import datetime
import os

# 页面配置
st.set_page_config(page_title="News Report Generator", page_icon="N")

# ===== 爬虫函数 =====
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://news.163.com/'
}

def parse_jsonp(text):
    match = re.match(r'data_callback\((.*)\)', text, re.DOTALL)
    if match:
        json_str = match.group(1).rstrip(';')
        return json.loads(json_str)
    return None

def get_real_image_url(imgurl):
    if not imgurl:
        return None
    parsed = urllib.parse.urlparse(imgurl)
    if parsed.query:
        params = urllib.parse.parse_qs(parsed.query)
        if 'url' in params:
            return params['url'][0]
    return imgurl

def extract_article_content(url):
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return None, None, None
        soup = BeautifulSoup(response.text, 'lxml')
        content = ""
        source = ""
        pub_time = ""
        article_body = soup.find('div', class_='post_body') or soup.find('div', class_='article_body')
        if article_body:
            content = article_body.get_text(separator='\n', strip=True)
        source_elem = soup.find('a', class_='ep-editor') or soup.find('span', class_='source')
        if source_elem:
            source = source_elem.get_text(strip=True)
        time_elem = soup.find('span', class_='post_time') or soup.find('div', class_='post_time_source')
        if time_elem:
            pub_time = time_elem.get_text(strip=True)
        if not content:
            og_desc = soup.find('meta', property='og:description')
            if og_desc:
                content = og_desc.get('content', '')
        return content[:3000], source, pub_time
    except Exception as e:
        return None, None, None

def crawl_news(topic, keywords, count=10):
    topic_map = {
        "科技": "https://news.163.com/special/cm_tech/",
        "国际": "https://news.163.com/special/cm_guoji/",
        "国内": "https://news.163.com/special/cm_guonei/",
        "AI": "https://news.163.com/special/cm_tech/",
        "股市原油": "https://news.163.com/special/cm_stock/",
    }
    url = topic_map.get(topic, topic_map["科技"])
    results = []
    try:
        response = requests.get(url, headers=headers, timeout=15)
        news_list = parse_jsonp(response.text)
        if not news_list:
            return results
        filtered = []
        for news in news_list:
            title = news.get('title', '')
            if keywords and any(kw in title for kw in keywords):
                filtered.append(news)
            elif not keywords:
                filtered.append(news)
        filtered = filtered[:count]
        for i, news in enumerate(filtered, 1):
            title = news.get('title', '')
            docurl = news.get('docurl', '')
            imgurl = get_real_image_url(news.get('imgurl', ''))
            hot = news.get('tienum', 0)
            news_time = news.get('time', '')
            news_source = news.get('source', '')
            content, source, pub_time = extract_article_content(docurl)
            final_source = source if source else news_source
            final_time = pub_time if pub_time else news_time
            results.append({
                'title': title,
                'url': docurl,
                'image': imgurl,
                'hot': hot,
                'source': final_source,
                'time': final_time,
                'content': content[:500] if content else ""
            })
            if i < len(filtered):
                time.sleep(random.randint(1, 2))
    except Exception as e:
        st.error(f"Error: {e}")
    return results

# ===== 1. 标题 =====
st.title("News Report Generator")

# ===== 2. 说明文本 =====
st.markdown("""
This tool automatically crawls news from NetEase and generates a report.
- Default topic: 科技/科技
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
    keywords_input = st.text_input("Keywords:", value="")

with col3:
    count = st.number_input("Number:", min_value=5, max_value=20, value=10)

# ===== 4. 按钮 =====
if st.button("Generate Report"):
    with st.spinner("Crawling... Please wait..."):
        keyword_list = [k.strip() for k in keywords_input.split(",") if k.strip()]
        results = crawl_news(topic, keyword_list, count)

        if results:
            st.markdown("---")
            st.subheader(f"Report: {topic}")

            for i, news in enumerate(results, 1):
                st.markdown(f"### {i}. {news['title']}")
                if news['image']:
                    st.image(news['image'], width=500)
                col_time, col_source, col_hot = st.columns(3)
                with col_time:
                    st.caption(f"Time: {news['time']}")
                with col_source:
                    st.caption(f"Source: {news['source']}")
                with col_hot:
                    st.caption(f"Hot: {news['hot']}")
                if news['content']:
                    st.text(news['content'][:200] + "...")
                st.markdown(f"[Read More]({news['url']})")
                st.markdown("---")

            st.success(f"Done! {len(results)} news crawled.")
        else:
            st.error("No news found. Please try different keywords.")
else:
    st.info("Click 'Generate Report' button to start.")
