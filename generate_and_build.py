"""GitHub Actions用 - 記事自動生成 & サイトビルドスクリプト

1. Gemini APIでキーワードを選定
2. 記事を1本生成
3. SEOスコアをチェック
4. サイト全体をビルド
"""
import json
import logging
import sys
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def select_keyword() -> tuple[str, str]:
    """Gemini APIでカテゴリとキーワードを自動選定する"""
    from llm import get_llm_client
    from config import GEMINI_API_KEY, GEMINI_MODEL, TARGET_CATEGORIES

    client = get_llm_client(__import__('types').SimpleNamespace(GEMINI_API_KEY=GEMINI_API_KEY))

    categories_text = "\n".join(f"- {cat}" for cat in TARGET_CATEGORIES)

    prompt = (
        "あなたはテクノロジーブログの編集者です。\n"
        "以下のカテゴリから1つ選び、そのカテゴリで今注目されている"
        "ブログ記事のキーワードを1つ提案してください。\n\n"
        "過去に書かれていない新鮮なテーマを選んでください。\n\n"
        f"カテゴリ一覧:\n{categories_text}\n\n"
        "以下の形式でJSON形式のみで回答してください（説明不要）:\n"
        '{"category": "カテゴリ名", "keyword": "キーワード"}'
    )

    response = client.models.generate_content(
        model=GEMINI_MODEL, contents=prompt
    )

    response_text = response.text.strip()

    # JSONブロックを抽出
    if "```" in response_text:
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
        response_text = response_text.strip()

    data = json.loads(response_text)
    return data["category"], data["keyword"]


def main():
    """メイン処理: 記事生成 -> SEOチェック -> サイトビルド"""
    from article_generator import ArticleGenerator
    from seo_optimizer import SEOOptimizer
    from site_generator import SiteGenerator

    # ステップ1: キーワード選定
    logger.info("ステップ1: キーワードを選定中...")
    try:
        category, keyword = select_keyword()
    except Exception as e:
        logger.error(f"キーワード選定に失敗: {e}")
        sys.exit(1)

    logger.info(f"選定結果 - カテゴリ: {category}, キーワード: {keyword}")

    # ステップ2: 記事生成（リトライ付き）
    logger.info("ステップ2: 記事を生成中...")
    max_retries = 3
    article = None
    for attempt in range(1, max_retries + 1):
        try:
            generator = ArticleGenerator()
            article = generator.generate_article(keyword=keyword, category=category)
            break
        except Exception as e:
            logger.warning(f"記事生成 試行{attempt}/{max_retries} 失敗: {e}")
            if attempt == max_retries:
                logger.error(f"記事生成に{max_retries}回失敗しました。終了します。")
                sys.exit(1)
            import time
            time.sleep(5)

    logger.info(f"記事生成完了: {article.get('title', '不明')}")
    logger.info(f"保存先: {article.get('file_path', '不明')}")

    # ステップ3: SEOチェック
    logger.info("ステップ3: SEOスコアをチェック中...")
    optimizer = SEOOptimizer()
    seo_result = optimizer.check_seo_score(article)
    score = seo_result.get("total_score", 0)
    grade = seo_result.get("grade", "?")
    logger.info(f"SEOスコア: {score}/100 (グレード: {grade})")

    if seo_result.get("recommendations"):
        logger.info("改善提案:")
        for rec in seo_result["recommendations"]:
            logger.info(f"  - {rec}")

    # ステップ4: サイトビルド
    logger.info("ステップ4: サイトをビルド中...")
    try:
        site_gen = SiteGenerator()
        site_gen.build_site()
    except Exception as e:
        logger.error(f"サイトビルドに失敗: {e}")
        sys.exit(1)

    logger.info("全処理が正常に完了しました")

    # サマリー出力
    print("\n" + "=" * 60)
    print(f"記事タイトル: {article.get('title', '不明')}")
    print(f"カテゴリ: {category}")
    print(f"キーワード: {keyword}")
    print(f"SEOスコア: {score}/100 ({grade})")
    print(f"生成日時: {datetime.now().isoformat()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
