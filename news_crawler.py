#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
新闻爬虫 - 可配置主题和数量
"""
import requests
import re
import json
import time
import random
from bs4 import BeautifulSoup
import urllib.parse
from datetime import datetime
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://news.163.com/'
}

def parse_jsonp(text):
    """解析JSONP格式"""
    match = re.match(r'data_callback\((.*)\)', text, re.DOTALL)
    if match:
        json_str = match.group(1).rstrip(';')
        return json.loads(json_str)
    return None

def get_real_image_url(imgurl):
    """从网易图片URL中提取真实地址"""
    if not imgurl:
        return None
    parsed = urllib.parse.urlparse(imgurl)
    if parsed.query:
        params = urllib.parse.parse_qs(parsed.query)
        if 'url' in params:
            return params['url'][0]
    return imgurl

def extract_article_content(url):
    """提取文章详情页内容"""
    try:
        response = requests.get(url, headers=headers, timeout=10)
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
    """爬取新闻"""
    print(f"\n开始爬取: {topic}, 数量: {count}")

    topic_map = {
        "美以伊战争": "https://news.163.com/special/cm_guoji/",
        "AI": "https://news.163.com/special/cm_tech/",
        "股市原油": "https://news.163.com/special/cm_stock/",
        "科技": "https://news.163.com/special/cm_tech/",
        "国际": "https://news.163.com/special/cm_guoji/",
        "国内": "https://news.163.com/special/cm_guonei/",
    }

    url = topic_map.get(topic, topic_map["国际"])
    results = []

    try:
        response = requests.get(url, headers=headers, timeout=10)
        news_list = parse_jsonp(response.text)

        if not news_list:
            print("获取新闻列表失败")
            return results

        filtered = []
        for news in news_list:
            title = news.get('title', '')
            if any(kw in title for kw in keywords):
                filtered.append(news)

        print(f"筛选到 {len(filtered)} 条新闻")
        filtered = filtered[:count]

        for i, news in enumerate(filtered, 1):
            title = news.get('title', '')
            docurl = news.get('docurl', '')
            imgurl = get_real_image_url(news.get('imgurl', ''))
            hot = news.get('tienum', 0)
            news_time = news.get('time', '')
            news_source = news.get('source', '')

            print(f"  [{i}/{len(filtered)}] {title[:30]}...")

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

        print(f"爬取完成，共 {len(results)} 条")

    except Exception as e:
        print(f"爬取失败: {e}")

    return results

def generate_report(topic, results):
    """生成简报"""
    today = datetime.now().strftime('%Y-%m-%d %H:%M')

    report = f"# {topic} 简报\n\n"
    report += f"**简报日期：{today}**\n"
    report += f"**数据来源：网易新闻**\n"
    report += f"**数量：{len(results)}条**\n\n---\n\n"

    for i, news in enumerate(results, 1):
        report += f"### {i}. {news['title']}\n\n"
        if news['image']:
            report += f"![配图]({news['image']})\n\n"
        if news['time']:
            report += f"**发布时间**：{news['time']}\n\n"
        if news['source']:
            report += f"**来源**：{news['source']}\n\n"
        report += f"**热度**：{news['hot']} 评论\n\n"
        if news['content']:
            summary = news['content'][:200] + "..." if len(news['content']) > 200 else news['content']
            report += f"**摘要**：{summary}\n\n"
        report += f"**链接**：[查看原文]({news['url']})\n\n---\n\n"

    report += f"*本简报由 Claude Code 自动生成*\n*生成时间：{today}*"

    return report

def main(topic="美以伊战争", keywords=None, count=10):
    """主函数"""
    if keywords is None:
        keywords = ["伊朗", "以色列", "美以", "中东", "霍尔木兹", "石油"]

    print(f"新闻爬虫 - 主题: {topic}, 数量: {count}")

    results = crawl_news(topic, keywords, count)

    if results:
        report = generate_report(topic, results)
        filename = f"z临时文件夹/{topic}简报_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"简报已保存: {filename}")
        return filename, results
    else:
        print("未获取到任何新闻")
        return None, []

if __name__ == "__main__":
    main()
