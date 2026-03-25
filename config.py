"""AI自動ブログ運営サービス - 設定"""
import os
from pathlib import Path

# プロジェクトルート
BASE_DIR = Path(__file__).parent

# Gemini API設定
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"

# ブログ設定
BLOG_NAME = "AI Tech Insights"
BLOG_DESCRIPTION = "AIが自動生成する最新テクノロジーブログ"
BLOG_URL = "/ai-tech-blog"  # GitHub Pages用のベースパス
BLOG_LANGUAGE = "ja"

# 出力ディレクトリ
OUTPUT_DIR = BASE_DIR / "output"
ARTICLES_DIR = OUTPUT_DIR / "articles"
SITE_DIR = OUTPUT_DIR / "site"

# 記事生成設定
MAX_ARTICLE_LENGTH = 3000  # 文字数目安
ARTICLES_PER_DAY = 2
TARGET_CATEGORIES = [
    "AI・機械学習",
    "プログラミング",
    "テクノロジートレンド",
    "ビジネス×AI",
    "自動化・効率化",
]

# SEO設定
MIN_KEYWORD_DENSITY = 1.0  # %
MAX_KEYWORD_DENSITY = 3.0  # %
META_DESCRIPTION_LENGTH = 120  # 文字

# スケジューラー設定
SCHEDULE_HOURS = [9, 15]  # 投稿時刻（時）

# ダッシュボード設定
DASHBOARD_HOST = "127.0.0.1"
DASHBOARD_PORT = 8000

# GitHub Pages設定
GITHUB_REPO = os.getenv("GITHUB_REPO", "MuscleLove-777/ai-tech-blog")
GITHUB_BRANCH = "gh-pages"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# Google AdSense設定
ADSENSE_CLIENT_ID = os.getenv("ADSENSE_CLIENT_ID", "")  # 例: "ca-pub-XXXXXXXX"
ADSENSE_ENABLED = bool(ADSENSE_CLIENT_ID)

# アフィリエイト設定
AFFILIATE_LINKS = {
    "AI": [
        {"service": "ChatGPT Plus", "url": "https://chat.openai.com", "description": "OpenAI公式"},
        {"service": "Claude Pro", "url": "https://claude.ai", "description": "Anthropic公式"},
    ],
    "プログラミング": [
        {"service": "Udemy", "url": "https://www.udemy.com", "description": "オンライン学習"},
        {"service": "Progate", "url": "https://prog-8.com", "description": "プログラミング学習"},
    ],
    "書籍": [
        {"service": "Amazon", "url": "https://www.amazon.co.jp", "description": "書籍購入"},
        {"service": "楽天ブックス", "url": "https://books.rakuten.co.jp", "description": "書籍購入"},
    ],
}
AFFILIATE_TAG = os.getenv("AMAZON_AFFILIATE_TAG", "")  # 例: "yourtag-22"
