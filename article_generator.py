"""AI自動ブログ運営サービス - 記事生成エンジン

Gemini APIを使用してSEO最適化されたブログ記事を自動生成するモジュール。
キーワードとカテゴリを指定するだけで、構造化された高品質な記事を生成する。
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path

from google import genai

import config

# ロガー設定
logger = logging.getLogger(__name__)


class ArticleGenerator:
    """Gemini APIを使ったブログ記事生成エンジン

    SEO最適化されたブログ記事を自動生成し、JSON形式で保存する。
    タイトル、本文（Markdown）、メタディスクリプション、タグ、スラッグを
    一括で生成する。
    """

    def __init__(self) -> None:
        """Geminiクライアントを初期化する

        Raises:
            ValueError: APIキーが未設定の場合
        """
        if not config.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY が設定されていません。"
                "環境変数 GEMINI_API_KEY を設定してください。"
            )

        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model_name = config.GEMINI_MODEL

        # 出力ディレクトリを作成
        config.ARTICLES_DIR.mkdir(parents=True, exist_ok=True)

        logger.info("ArticleGenerator を初期化しました（モデル: %s）", config.GEMINI_MODEL)

    def generate_article(self, keyword: str, category: str) -> dict:
        """キーワードとカテゴリからSEO最適化されたブログ記事を生成する

        Args:
            keyword: 記事の主要キーワード
            category: 記事のカテゴリ（config.TARGET_CATEGORIES から選択）

        Returns:
            dict: 生成された記事データ
                - title (str): 記事タイトル
                - content (str): 本文（Markdown形式）
                - meta_description (str): メタディスクリプション
                - tags (list[str]): 関連タグ一覧
                - slug (str): URLスラッグ
                - keyword (str): 使用したキーワード
                - category (str): カテゴリ
                - generated_at (str): 生成日時（ISO形式）
                - file_path (str): 保存先ファイルパス

        Raises:
            Exception: API呼び出しに失敗した場合
            ValueError: レスポンスのパースに失敗した場合
        """
        logger.info("記事生成を開始: キーワード='%s', カテゴリ='%s'", keyword, category)

        # SEO最適化プロンプトを構築
        prompt = self._build_prompt(keyword, category)

        try:
            # Gemini APIを呼び出し
            response = self.client.models.generate_content(
                model=self.model_name, contents=prompt
            )

            response_text = response.text
            logger.debug("APIレスポンスを受信（%d文字）", len(response_text))

        except Exception as e:
            logger.error("Gemini API呼び出しに失敗: %s", e)
            raise

        # レスポンスをパース
        article = self._parse_response(response_text)
        article["keyword"] = keyword
        article["category"] = category
        article["generated_at"] = datetime.now().isoformat()

        # JSON形式で保存
        file_path = self._save_article(article)
        article["file_path"] = str(file_path)

        logger.info("記事生成完了: '%s' → %s", article["title"], file_path)
        return article

    def generate_outline(self, keyword: str, category: str) -> list:
        """記事のアウトライン（見出し構造）を先に生成する

        本文生成前にアウトラインを確認・調整したい場合に使用する。

        Args:
            keyword: 記事の主要キーワード
            category: 記事のカテゴリ

        Returns:
            list[dict]: アウトライン項目のリスト
                各項目は {"level": "H2"|"H3", "heading": "見出しテキスト"} の形式

        Raises:
            Exception: API呼び出しに失敗した場合
        """
        logger.info("アウトライン生成を開始: キーワード='%s'", keyword)

        outline_prompt = f"""あなたはSEOに精通したプロのブログライターです。

以下の条件でブログ記事のアウトライン（見出し構造）をJSON形式で生成してください。

【条件】
- キーワード: {keyword}
- カテゴリ: {category}
- 対象読者: テクノロジーに関心のある日本語話者
- 記事構成: 導入 → 本文（3〜5セクション）→ まとめ

【出力形式】
以下のJSON配列のみを出力してください。余計な説明は不要です。
```json
[
  {{"level": "H2", "heading": "見出しテキスト"}},
  {{"level": "H3", "heading": "小見出しテキスト"}},
  ...
]
```

H2は主要セクション、H3はH2の下位セクションとして使用してください。
キーワード「{keyword}」を自然な形で見出しに含めてください。"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name, contents=outline_prompt
            )

            response_text = response.text

            # JSONブロックを抽出してパース
            json_match = re.search(
                r"```json\s*(.*?)\s*```", response_text, re.DOTALL
            )
            if json_match:
                outline = json.loads(json_match.group(1))
            else:
                # JSONブロックがない場合、レスポンス全体をパース試行
                outline = json.loads(response_text.strip())

            logger.info("アウトライン生成完了: %d項目", len(outline))
            return outline

        except Exception as e:
            logger.error("アウトライン生成のAPI呼び出しに失敗: %s", e)
            raise
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("アウトラインのパースに失敗: %s", e)
            raise ValueError(f"アウトラインのパースに失敗しました: {e}") from e

    def _build_prompt(self, keyword: str, category: str) -> str:
        """SEO最適化された記事生成プロンプトを構築する

        Args:
            keyword: 記事の主要キーワード
            category: 記事のカテゴリ

        Returns:
            str: Gemini APIに送信するプロンプト文字列
        """
        return f"""あなたはSEOに精通したプロのテクノロジーブログライターです。
以下の条件に従って、高品質なブログ記事を生成してください。

【基本条件】
- ブログ名: {config.BLOG_NAME}
- キーワード: {keyword}
- カテゴリ: {category}
- 言語: 日本語
- 文字数目安: {config.MAX_ARTICLE_LENGTH}文字程度

【SEO要件】
1. タイトルにキーワード「{keyword}」を必ず含めること
2. タイトルは32文字以内で魅力的に
3. H2、H3の見出し構造を適切に使用すること
4. キーワード密度は{config.MIN_KEYWORD_DENSITY}%〜{config.MAX_KEYWORD_DENSITY}%を目安に
5. メタディスクリプションは{config.META_DESCRIPTION_LENGTH}文字以内
6. 内部リンクのプレースホルダーを2〜3箇所に配置（{{{{internal_link:関連トピック}}}}の形式）

【記事構成】
1. 導入（読者の関心を引く問いかけやデータ）
2. 本文（H2で3〜5セクション、必要に応じてH3を使用）
3. まとめ（要点整理と次のアクション提案）

【出力形式】
以下のJSON形式で出力してください。JSONブロック以外のテキストは出力しないでください。

```json
{{
  "title": "SEO最適化されたタイトル",
  "content": "# タイトル\\n\\n本文（Markdown形式）...",
  "meta_description": "120文字以内のメタディスクリプション",
  "tags": ["タグ1", "タグ2", "タグ3", "タグ4", "タグ5"],
  "slug": "url-friendly-slug"
}}
```

【注意事項】
- content内のMarkdownは適切にエスケープしてJSON文字列として有効にすること
- tagsは5個ちょうど生成すること
- slugは半角英数字とハイフンのみ使用すること
- 読者にとって実用的で具体的な内容を心がけること
- 専門用語には簡単な補足説明を付けること"""

    def _parse_response(self, response_text: str) -> dict:
        """Gemini APIのレスポンスをパースして記事データを抽出する

        Args:
            response_text: APIから返されたテキスト

        Returns:
            dict: パースされた記事データ（title, content, meta_description, tags, slug）

        Raises:
            ValueError: パースに失敗した場合、または必須フィールドが欠落している場合
        """
        # JSONブロックを抽出
        json_match = re.search(
            r"```json\s*(.*?)\s*```", response_text, re.DOTALL
        )

        try:
            if json_match:
                article_data = json.loads(json_match.group(1))
            else:
                # JSONブロックがない場合、レスポンス全体をパース試行
                # 先頭・末尾の非JSON文字を除去
                cleaned = response_text.strip()
                # JSON部分を探す
                start = cleaned.find("{")
                end = cleaned.rfind("}") + 1
                if start >= 0 and end > start:
                    cleaned = cleaned[start:end]
                article_data = json.loads(cleaned)

        except json.JSONDecodeError as e:
            logger.error(
                "JSONパースに失敗: %s\nレスポンス先頭200文字: %s",
                e,
                response_text[:200],
            )
            raise ValueError(
                f"APIレスポンスのJSONパースに失敗しました: {e}"
            ) from e

        # 必須フィールドの検証
        required_fields = ["title", "content", "meta_description", "tags", "slug"]
        missing = [f for f in required_fields if f not in article_data]
        if missing:
            raise ValueError(
                f"APIレスポンスに必須フィールドが不足しています: {missing}"
            )

        # タグの検証（リスト形式であること）
        if not isinstance(article_data["tags"], list):
            article_data["tags"] = [article_data["tags"]]

        # スラッグの正規化（半角英数字とハイフンのみ）
        article_data["slug"] = re.sub(
            r"[^a-z0-9-]", "", article_data["slug"].lower().replace(" ", "-")
        )

        logger.debug("レスポンスのパース完了: タイトル='%s'", article_data["title"])
        return article_data

    def _save_article(self, article: dict) -> Path:
        """生成された記事をJSON形式でファイルに保存する

        ファイル名形式: YYYYMMDD_HHMMSS_slug.json

        Args:
            article: 記事データの辞書

        Returns:
            Path: 保存先のファイルパス
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = article.get("slug", "untitled")
        filename = f"{timestamp}_{slug}.json"
        file_path = config.ARTICLES_DIR / filename

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(article, f, ensure_ascii=False, indent=2)

        logger.info("記事を保存しました: %s", file_path)
        return file_path


# --- メインエントリーポイント（テスト・動作確認用） ---

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    generator = ArticleGenerator()

    # テスト: アウトライン生成
    print("=== アウトライン生成テスト ===")
    outline = generator.generate_outline(
        keyword="生成AI 業務効率化",
        category="ビジネス×AI",
    )
    for item in outline:
        indent = "  " if item["level"] == "H3" else ""
        print(f"{indent}{item['level']}: {item['heading']}")

    # テスト: 記事生成
    print("\n=== 記事生成テスト ===")
    article = generator.generate_article(
        keyword="生成AI 業務効率化",
        category="ビジネス×AI",
    )
    print(f"タイトル: {article['title']}")
    print(f"スラッグ: {article['slug']}")
    print(f"タグ: {', '.join(article['tags'])}")
    print(f"メタ説明: {article['meta_description']}")
    print(f"保存先: {article['file_path']}")
    print(f"本文冒頭200文字:\n{article['content'][:200]}...")
