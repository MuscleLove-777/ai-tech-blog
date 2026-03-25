"""AI自動ブログ運営サービス - SEO最適化モジュール

記事のSEOスコアを分析し、キーワード密度・メタディスクリプション・
見出し構造などの観点から最適化を支援する。
"""

import hashlib
import logging
import re

import config

# ロガー設定
logger = logging.getLogger(__name__)


class SEOOptimizer:
    """記事のSEO最適化を分析・支援するクラス

    キーワード密度の計算、メタディスクリプションの最適化、
    SEOスコアの算出、内部リンク候補の提案などを行う。
    """

    def __init__(self) -> None:
        """SEOOptimizerを初期化する"""
        self.min_keyword_density = config.MIN_KEYWORD_DENSITY
        self.max_keyword_density = config.MAX_KEYWORD_DENSITY
        self.meta_description_length = config.META_DESCRIPTION_LENGTH
        logger.info("SEOOptimizer を初期化しました")

    def analyze_keyword_density(self, content: str, keyword: str) -> float:
        """本文中のキーワード密度（出現率）を計算する

        キーワード密度 = (キーワード出現回数 × キーワード文字数) / 本文文字数 × 100

        Args:
            content: 分析対象の本文テキスト
            keyword: 対象キーワード

        Returns:
            float: キーワード密度（パーセント）。本文が空の場合は0.0
        """
        if not content or not keyword:
            return 0.0

        # Markdownの記号を除去して純粋なテキストにする
        plain_text = self._strip_markdown(content)

        if len(plain_text) == 0:
            return 0.0

        # キーワードの出現回数をカウント（大文字小文字を無視）
        keyword_lower = keyword.lower()
        text_lower = plain_text.lower()
        count = text_lower.count(keyword_lower)

        # キーワード密度を計算
        density = (count * len(keyword)) / len(plain_text) * 100

        logger.debug(
            "キーワード密度: '%.2f%%（'%s' × %d回 / %d文字）",
            density, keyword, count, len(plain_text),
        )
        return round(density, 2)

    def optimize_meta_description(self, description: str) -> str:
        """メタディスクリプションを最適化する

        文字数が上限を超える場合は切り詰め、末尾に「...」を付与する。
        空白の正規化も行う。

        Args:
            description: 元のメタディスクリプション

        Returns:
            str: 最適化されたメタディスクリプション
        """
        if not description:
            logger.warning("メタディスクリプションが空です")
            return ""

        # 前後の空白を除去し、連続する空白を1つに正規化
        optimized = re.sub(r"\s+", " ", description.strip())

        # 文字数チェック
        if len(optimized) > self.meta_description_length:
            logger.info(
                "メタディスクリプションを切り詰め: %d文字 → %d文字",
                len(optimized), self.meta_description_length,
            )
            # 上限文字数 - 3（「...」分）で切り詰め
            optimized = optimized[: self.meta_description_length - 3] + "..."

        return optimized

    def generate_slug(self, title: str) -> str:
        """記事タイトルからURLスラッグを生成する

        日本語タイトルはハッシュベースでスラッグを生成する。
        英数字部分はそのまま使用し、日本語部分は短いハッシュに変換する。

        Args:
            title: 記事タイトル

        Returns:
            str: URL用スラッグ（半角英数字とハイフンのみ）
        """
        if not title:
            return "untitled"

        # 英数字部分を抽出
        ascii_parts = re.findall(r"[a-zA-Z0-9]+", title)

        # 日本語部分のハッシュを生成（短い識別子として使用）
        title_hash = hashlib.md5(title.encode("utf-8")).hexdigest()[:8]

        if ascii_parts:
            # 英数字部分をハイフンで結合し、ハッシュを末尾に付与
            slug_base = "-".join(part.lower() for part in ascii_parts)
            slug = f"{slug_base}-{title_hash}"
        else:
            # 全て日本語の場合はハッシュのみ
            slug = f"article-{title_hash}"

        # スラッグの最大長を制限（URL可読性のため）
        max_slug_length = 80
        if len(slug) > max_slug_length:
            slug = slug[:max_slug_length].rstrip("-")

        logger.debug("スラッグ生成: '%s' → '%s'", title, slug)
        return slug

    def check_seo_score(self, article: dict) -> dict:
        """記事のSEOスコアを総合的に算出する

        以下の観点で0〜100点のスコアを算出する:
        - タイトルの長さと品質
        - 見出し構造（H2/H3の使用状況）
        - キーワード密度
        - メタディスクリプションの品質
        - コンテンツの長さ

        Args:
            article: 記事データの辞書
                必須キー: title, content, meta_description, keyword（任意）

        Returns:
            dict: SEO分析結果
                - total_score (int): 総合スコア（0〜100）
                - details (dict): 各項目のスコアと詳細
                - recommendations (list[str]): 改善提案のリスト
        """
        details = {}
        recommendations = []
        keyword = article.get("keyword", "")
        title = article.get("title", "")
        content = article.get("content", "")
        meta_description = article.get("meta_description", "")

        # --- 1. タイトル評価（25点満点） ---
        title_score = 0
        title_length = len(title)

        if 20 <= title_length <= 35:
            title_score += 15  # 最適な長さ
        elif 10 <= title_length <= 45:
            title_score += 10  # 許容範囲
        elif title_length > 0:
            title_score += 5
            recommendations.append(
                f"タイトルの長さを20〜35文字に調整してください（現在: {title_length}文字）"
            )
        else:
            recommendations.append("タイトルが設定されていません")

        # タイトルにキーワードが含まれているか
        if keyword and keyword.lower() in title.lower():
            title_score += 10
        elif keyword:
            recommendations.append(
                f"タイトルにキーワード「{keyword}」を含めてください"
            )

        details["title"] = {
            "score": title_score,
            "max": 25,
            "length": title_length,
            "has_keyword": keyword.lower() in title.lower() if keyword else False,
        }

        # --- 2. 見出し構造評価（20点満点） ---
        heading_score = 0
        h2_count = len(re.findall(r"^## ", content, re.MULTILINE))
        h3_count = len(re.findall(r"^### ", content, re.MULTILINE))

        if h2_count >= 3:
            heading_score += 10
        elif h2_count >= 1:
            heading_score += 5
            recommendations.append("H2見出しを3つ以上使用することを推奨します")
        else:
            recommendations.append("H2見出しが使用されていません。記事に見出し構造を追加してください")

        if h3_count >= 2:
            heading_score += 10
        elif h3_count >= 1:
            heading_score += 5
        else:
            recommendations.append("H3見出しを使って内容を細分化することを推奨します")

        details["headings"] = {
            "score": heading_score,
            "max": 20,
            "h2_count": h2_count,
            "h3_count": h3_count,
        }

        # --- 3. キーワード密度評価（20点満点） ---
        kw_score = 0
        if keyword:
            density = self.analyze_keyword_density(content, keyword)

            if self.min_keyword_density <= density <= self.max_keyword_density:
                kw_score = 20  # 最適範囲
            elif 0.5 <= density <= 4.0:
                kw_score = 12  # 許容範囲
                if density < self.min_keyword_density:
                    recommendations.append(
                        f"キーワード密度が低いです（{density}%）。"
                        f"{self.min_keyword_density}%以上を目指してください"
                    )
                else:
                    recommendations.append(
                        f"キーワード密度が高すぎます（{density}%）。"
                        f"{self.max_keyword_density}%以下に抑えてください"
                    )
            elif density > 0:
                kw_score = 5
                recommendations.append(
                    f"キーワード密度を{self.min_keyword_density}%〜"
                    f"{self.max_keyword_density}%の範囲に調整してください（現在: {density}%）"
                )
            else:
                recommendations.append(
                    f"キーワード「{keyword}」が本文に含まれていません"
                )

            details["keyword_density"] = {
                "score": kw_score,
                "max": 20,
                "density": density,
                "optimal_range": f"{self.min_keyword_density}%〜{self.max_keyword_density}%",
            }
        else:
            kw_score = 10  # キーワード未指定の場合は中間点
            details["keyword_density"] = {
                "score": kw_score,
                "max": 20,
                "note": "キーワード未指定",
            }

        # --- 4. メタディスクリプション評価（20点満点） ---
        meta_score = 0
        meta_length = len(meta_description)

        if 50 <= meta_length <= self.meta_description_length:
            meta_score += 15  # 最適な長さ
        elif 0 < meta_length <= 150:
            meta_score += 8
            recommendations.append(
                f"メタディスクリプションを50〜{self.meta_description_length}文字に"
                f"調整してください（現在: {meta_length}文字）"
            )
        elif meta_length == 0:
            recommendations.append("メタディスクリプションが設定されていません")

        # メタディスクリプションにキーワードが含まれているか
        if keyword and keyword.lower() in meta_description.lower():
            meta_score += 5
        elif keyword and meta_description:
            recommendations.append(
                f"メタディスクリプションにキーワード「{keyword}」を含めてください"
            )

        details["meta_description"] = {
            "score": meta_score,
            "max": 20,
            "length": meta_length,
            "has_keyword": (
                keyword.lower() in meta_description.lower()
                if keyword and meta_description
                else False
            ),
        }

        # --- 5. コンテンツ長評価（15点満点） ---
        content_score = 0
        plain_text = self._strip_markdown(content)
        content_length = len(plain_text)

        if content_length >= config.MAX_ARTICLE_LENGTH:
            content_score = 15
        elif content_length >= config.MAX_ARTICLE_LENGTH * 0.7:
            content_score = 10
        elif content_length >= config.MAX_ARTICLE_LENGTH * 0.4:
            content_score = 5
            recommendations.append(
                f"記事の文字数を増やしてください"
                f"（現在: {content_length}文字、目標: {config.MAX_ARTICLE_LENGTH}文字以上）"
            )
        elif content_length > 0:
            content_score = 2
            recommendations.append(
                f"記事の内容が不十分です（{content_length}文字）。"
                f"{config.MAX_ARTICLE_LENGTH}文字以上を目指してください"
            )
        else:
            recommendations.append("記事の本文が空です")

        details["content_length"] = {
            "score": content_score,
            "max": 15,
            "length": content_length,
            "target": config.MAX_ARTICLE_LENGTH,
        }

        # --- 総合スコア算出 ---
        total_score = (
            title_score + heading_score + kw_score + meta_score + content_score
        )

        result = {
            "total_score": total_score,
            "max_score": 100,
            "grade": self._score_to_grade(total_score),
            "details": details,
            "recommendations": recommendations,
        }

        logger.info(
            "SEOスコア算出: %d/100（%s）- 改善提案%d件",
            total_score, result["grade"], len(recommendations),
        )
        return result

    def suggest_internal_links(
        self, content: str, existing_articles: list
    ) -> list:
        """本文の内容に基づいて内部リンク候補を提案する

        既存記事のタイトル・キーワード・タグと本文を照合し、
        関連性の高い記事を内部リンク候補として提案する。

        Args:
            content: 現在の記事の本文
            existing_articles: 既存記事データのリスト
                各記事は {"title": str, "slug": str, "keyword": str, "tags": list} を含む

        Returns:
            list[dict]: 内部リンク候補のリスト
                各候補は {"title": str, "slug": str, "relevance_score": float} の形式
        """
        if not content or not existing_articles:
            return []

        plain_text = self._strip_markdown(content).lower()
        suggestions = []

        for article in existing_articles:
            relevance = 0.0
            title = article.get("title", "")
            keyword = article.get("keyword", "")
            tags = article.get("tags", [])

            # キーワードが本文に含まれているかチェック
            if keyword and keyword.lower() in plain_text:
                relevance += 3.0

            # タグが本文に含まれているかチェック
            for tag in tags:
                if tag.lower() in plain_text:
                    relevance += 1.0

            # タイトルの一部が本文に含まれているかチェック
            # タイトルを分割して各単語をチェック（2文字以上の単語のみ）
            title_words = [
                w for w in re.findall(r"[\w]+", title) if len(w) >= 2
            ]
            matched_words = sum(
                1 for w in title_words if w.lower() in plain_text
            )
            if title_words:
                relevance += (matched_words / len(title_words)) * 2.0

            # 関連性がある記事のみ候補に追加
            if relevance > 0:
                suggestions.append({
                    "title": title,
                    "slug": article.get("slug", ""),
                    "url": f"{config.BLOG_URL}/articles/{article.get('slug', '')}",
                    "relevance_score": round(relevance, 2),
                })

        # 関連性スコアの降順でソート
        suggestions.sort(key=lambda x: x["relevance_score"], reverse=True)

        # 上位5件に絞る
        top_suggestions = suggestions[:5]

        logger.info(
            "内部リンク候補: %d件中%d件を提案",
            len(suggestions), len(top_suggestions),
        )
        return top_suggestions

    # --- プライベートメソッド ---

    @staticmethod
    def _strip_markdown(text: str) -> str:
        """Markdownの装飾記号を除去してプレーンテキストを返す

        Args:
            text: Markdown形式のテキスト

        Returns:
            str: 装飾記号を除去したプレーンテキスト
        """
        # コードブロックを除去
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        # インラインコードを除去
        text = re.sub(r"`[^`]+`", "", text)
        # 見出し記号を除去
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        # 強調記号を除去
        text = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", text)
        # リンクをテキスト部分のみに
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        # 画像を除去
        text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", "", text)
        # リスト記号を除去
        text = re.sub(r"^[\s]*[-*+]\s+", "", text, flags=re.MULTILINE)
        # 番号付きリスト記号を除去
        text = re.sub(r"^[\s]*\d+\.\s+", "", text, flags=re.MULTILINE)
        # 水平線を除去
        text = re.sub(r"^[-*_]{3,}$", "", text, flags=re.MULTILINE)
        # 余分な空行を整理
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    @staticmethod
    def _score_to_grade(score: int) -> str:
        """数値スコアを評価グレードに変換する

        Args:
            score: 0〜100のスコア

        Returns:
            str: 評価グレード（S/A/B/C/D）
        """
        if score >= 90:
            return "S"
        elif score >= 75:
            return "A"
        elif score >= 60:
            return "B"
        elif score >= 40:
            return "C"
        else:
            return "D"


# --- メインエントリーポイント（テスト・動作確認用） ---

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    optimizer = SEOOptimizer()

    # テスト用のサンプル記事
    sample_article = {
        "title": "生成AIで業務効率化を実現する5つの方法",
        "keyword": "生成AI 業務効率化",
        "content": """# 生成AIで業務効率化を実現する5つの方法

## はじめに
生成AIの進化により、業務効率化の可能性が大きく広がっています。
本記事では、生成AIを活用して業務効率化を実現する具体的な方法を紹介します。

## 1. ドキュメント作成の自動化
生成AIを使えば、報告書やメールの下書きを自動生成できます。

### 活用のポイント
プロンプトを工夫することで、より質の高い文書が生成できます。

## 2. データ分析の効率化
大量のデータから生成AIがインサイトを抽出します。

## 3. カスタマーサポートの自動化
チャットボットとして生成AIを活用し、業務効率化を図ります。

### 導入時の注意点
人間によるチェック体制も重要です。

## まとめ
生成AIによる業務効率化は、もはや選択肢ではなく必須の取り組みです。
""",
        "meta_description": "生成AIを活用した業務効率化の具体的な方法を5つ紹介。ドキュメント作成、データ分析、カスタマーサポートなど、すぐに実践できる活用法を解説します。",
        "tags": ["生成AI", "業務効率化", "自動化", "ChatGPT", "DX"],
    }

    # SEOスコアチェック
    print("=== SEOスコア分析 ===")
    result = optimizer.check_seo_score(sample_article)
    print(f"総合スコア: {result['total_score']}/100（グレード: {result['grade']}）")
    print("\n--- 各項目の詳細 ---")
    for key, detail in result["details"].items():
        print(f"  {key}: {detail['score']}/{detail['max']}")
    print("\n--- 改善提案 ---")
    for rec in result["recommendations"]:
        print(f"  ・{rec}")

    # キーワード密度チェック
    print("\n=== キーワード密度 ===")
    density = optimizer.analyze_keyword_density(
        sample_article["content"], "生成AI"
    )
    print(f"キーワード密度: {density}%")

    # スラッグ生成
    print("\n=== スラッグ生成 ===")
    slug = optimizer.generate_slug(sample_article["title"])
    print(f"スラッグ: {slug}")

    # メタディスクリプション最適化
    print("\n=== メタディスクリプション最適化 ===")
    optimized = optimizer.optimize_meta_description(sample_article["meta_description"])
    print(f"最適化後: {optimized}（{len(optimized)}文字）")
