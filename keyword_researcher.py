"""AI自動ブログ運営サービス - キーワードリサーチモジュール

Gemini APIを使って、トレンドキーワードの提案・ロングテール分析・
競合分析・コンテンツカレンダー生成を行う。
"""
import json
import logging
from datetime import datetime, timedelta

from llm import get_llm_client
from config import GEMINI_API_KEY, GEMINI_MODEL, TARGET_CATEGORIES

logger = logging.getLogger(__name__)


class KeywordResearcher:
    """Gemini APIを活用したキーワードリサーチャー"""

    def __init__(self):
        """Geminiクライアントを初期化する"""
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model_name = GEMINI_MODEL
        logger.info("KeywordResearcher を初期化しました")

    def _call_ai(self, prompt: str, max_tokens: int = 2000) -> str:
        """Gemini APIを呼び出して応答テキストを返す共通メソッド

        Args:
            prompt: ユーザープロンプト
            max_tokens: 最大トークン数

        Returns:
            str: AIの応答テキスト
        """
        response = self.client.models.generate_content(
            model=self.model_name, contents=prompt
        )
        return response.text.strip()

    def _parse_json_response(self, response_text: str) -> any:
        """AIレスポンスからJSONを抽出してパースする

        Args:
            response_text: AIの応答テキスト

        Returns:
            パースされたJSONオブジェクト
        """
        text = response_text.strip()

        # ```json ... ``` ブロックを抽出
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        return json.loads(text)

    def research_trending_keywords(
        self, category: str, count: int = 10
    ) -> list[dict]:
        """カテゴリに基づいてトレンドキーワードをAIで提案する

        Args:
            category: 対象カテゴリ（例: "AI・機械学習"）
            count: 提案するキーワード数（デフォルト10）

        Returns:
            list[dict]: 各キーワードの情報を含むリスト
                - keyword: キーワード文字列
                - volume: 検索ボリューム予測（"高" / "中" / "低"）
                - competition: 競合度予測（"高" / "中" / "低"）
                - article_type: 推奨記事タイプ（例: "ハウツー", "まとめ"）
        """
        logger.info(f"トレンドキーワードをリサーチ中: カテゴリ={category}, 件数={count}")

        prompt = (
            f"「{category}」カテゴリで、現在トレンドになっているブログ記事向けの"
            f"キーワードを{count}個提案してください。\n\n"
            "各キーワードについて以下の情報を含めてください:\n"
            "- keyword: キーワード\n"
            "- volume: 検索ボリューム予測（「高」「中」「低」のいずれか）\n"
            "- competition: 競合度予測（「高」「中」「低」のいずれか）\n"
            "- article_type: 推奨記事タイプ（例: ハウツー、まとめ、比較、レビュー、解説）\n\n"
            "JSON配列形式のみで回答してください（説明不要）:\n"
            '[{"keyword": "...", "volume": "...", "competition": "...", "article_type": "..."}]'
        )

        response = self._call_ai(prompt)
        keywords = self._parse_json_response(response)

        logger.info(f"{len(keywords)}件のキーワードを取得しました")
        return keywords

    def suggest_long_tail_keywords(self, base_keyword: str) -> list[str]:
        """ベースキーワードからロングテールキーワードを提案する

        Args:
            base_keyword: 元になるキーワード（例: "AI活用法"）

        Returns:
            list[str]: ロングテールキーワードのリスト
        """
        logger.info(f"ロングテールキーワードを提案中: {base_keyword}")

        prompt = (
            f"「{base_keyword}」をベースに、ブログ記事で狙えるロングテール"
            "キーワードを10個提案してください。\n\n"
            "検索意図が明確で、記事が書きやすいものを優先してください。\n\n"
            "JSON配列形式（文字列の配列）のみで回答してください（説明不要）:\n"
            '["キーワード1", "キーワード2", ...]'
        )

        response = self._call_ai(prompt)
        keywords = self._parse_json_response(response)

        logger.info(f"{len(keywords)}件のロングテールキーワードを取得しました")
        return keywords

    def analyze_competition(self, keyword: str) -> dict:
        """指定キーワードの競合分析をAIで行う

        Args:
            keyword: 分析対象のキーワード

        Returns:
            dict: 競合分析結果
                - keyword: 対象キーワード
                - difficulty: 難易度（1-10）
                - top_content_types: 上位表示されやすいコンテンツタイプ
                - recommended_word_count: 推奨文字数
                - key_topics: 記事に含めるべきトピック
                - differentiation_tips: 差別化のポイント
        """
        logger.info(f"競合分析を実行中: {keyword}")

        prompt = (
            f"「{keyword}」というキーワードでブログ記事を書く場合の競合分析を"
            "行ってください。\n\n"
            "以下の項目を含むJSON形式のみで回答してください（説明不要）:\n"
            "{\n"
            '  "keyword": "対象キーワード",\n'
            '  "difficulty": 難易度（1-10の数値）,\n'
            '  "top_content_types": ["上位表示されやすいコンテンツタイプ"],\n'
            '  "recommended_word_count": 推奨文字数（数値）,\n'
            '  "key_topics": ["記事に含めるべきトピック"],\n'
            '  "differentiation_tips": ["差別化のポイント"]\n'
            "}"
        )

        response = self._call_ai(prompt)
        analysis = self._parse_json_response(response)

        logger.info(f"競合分析完了: 難易度={analysis.get('difficulty', '不明')}")
        return analysis

    def get_content_calendar(self, days: int = 7) -> list[dict]:
        """指定日数分のコンテンツカレンダーを生成する

        Args:
            days: カレンダーの日数（デフォルト7日）

        Returns:
            list[dict]: 日ごとのコンテンツ計画
                - date: 日付（YYYY-MM-DD形式）
                - keyword: 対象キーワード
                - category: カテゴリ
                - article_type: 記事タイプ
        """
        logger.info(f"コンテンツカレンダーを生成中: {days}日分")

        # 日付リストを作成
        start_date = datetime.now()
        dates = [
            (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(days)
        ]
        dates_text = "\n".join(f"- {d}" for d in dates)

        # カテゴリ一覧
        categories_text = "\n".join(f"- {cat}" for cat in TARGET_CATEGORIES)

        prompt = (
            f"以下の日付とカテゴリを使って、ブログのコンテンツカレンダーを"
            "作成してください。\n\n"
            f"日付:\n{dates_text}\n\n"
            f"カテゴリ:\n{categories_text}\n\n"
            "各日付に対して、カテゴリをバランスよく配分し、"
            "トレンドを意識したキーワードと記事タイプを設定してください。\n\n"
            "JSON配列形式のみで回答してください（説明不要）:\n"
            '[{"date": "YYYY-MM-DD", "keyword": "...", '
            '"category": "...", "article_type": "..."}]'
        )

        response = self._call_ai(prompt, max_tokens=3000)
        calendar = self._parse_json_response(response)

        logger.info(f"コンテンツカレンダー生成完了: {len(calendar)}件")
        return calendar


# 直接実行時のテスト用
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    researcher = KeywordResearcher()

    # テスト: トレンドキーワード取得
    print("\n=== トレンドキーワード ===")
    keywords = researcher.research_trending_keywords("AI・機械学習", count=5)
    for kw in keywords:
        print(f"  {kw['keyword']} (ボリューム: {kw['volume']}, 記事タイプ: {kw['article_type']})")

    # テスト: ロングテールキーワード
    print("\n=== ロングテールキーワード ===")
    long_tail = researcher.suggest_long_tail_keywords("AI活用法")
    for lt in long_tail:
        print(f"  {lt}")
