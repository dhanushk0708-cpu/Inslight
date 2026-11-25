import re
import json
from typing import Tuple, Optional
from pydantic import BaseModel
from app.services.ai_service import ai_service
from app.core.logging import logger

GUARD_REJECTION_MESSAGE = (
    "I'm Inslight, your AI Business Intelligence assistant. I can help you analyze business data, "
    "understand performance, identify trends, generate insights and support data-driven decisions.\n\n"
    "Your question appears to be outside my business intelligence capabilities. "
    "Please ask me something related to your business data."
)

NO_DATASET_MESSAGE = (
    "Please upload a business dataset before asking dataset-specific questions."
)


class GuardClassification(BaseModel):
    is_business: bool
    requires_dataset: bool
    reason: str


class BusinessContextGuard:
    # Explicit business intelligence keywords and phrases
    BUSINESS_PATTERNS = [
        r"\brevenue\b", r"\bsales\b", r"\bprofit\b", r"\bcost\b", r"\bunits?\b",
        r"\bdiscount\b", r"\bmargin\b", r"\bgrowth\b", r"\btrends?\b", r"\bmonthly\b",
        r"\byearly\b", r"\bdaily\b", r"\bquarterly\b", r"\bproducts?\b", r"\bcustomers?\b",
        r"\bcategor(y|ies)\b", r"\bregions?\b", r"\border_date\b", r"\borders?\b",
        r"\bprice\b", r"\baverage\b", r"\btotal\b", r"\bcount\b", r"\brating\b",
        r"\bperformance\b", r"\bforecast\b", r"\bproject(ion|ed)?\b", r"\banomal(y|ies)\b",
        r"\bcompare\b", r"\bversus\b", r"\bvs\b", r"\bbreakdown\b", r"\bdistribution\b",
        r"\bpercentage\b", r"\bdataset\b", r"\bcolumns?\b", r"\brows?\b", r"\bdata\b",
        r"\bsalesperson\b", r"\bpayment\b", r"\bmetric\b", r"\bkpi\b", r"\bshare\b",
        r"\bdeep dive\b", r"\bwhat-if\b", r"\brisk\b", r"\bdrivers?\b",
        r"\bbusiness\b", r"\boverview\b", r"\bopportunit(y|ies)\b", r"\bunderperforming\b",
        r"\blosing money\b", r"\bmanagement\b", r"\bstrategic\b", r"\bstrategy\b",
        r"\banalyze\b", r"\banalysis\b", r"\bfinancial\b", r"\bexecutive\b"
    ]

    # Explicit non-business / general knowledge patterns to reject
    NON_BUSINESS_PATTERNS = [
        r"\bprime minister\b", r"\bpresident\b", r"\bwho is\b", r"\bcapital of\b",
        r"\btell me a joke\b", r"\bjoke\b", r"\bpoem\b", r"\bsong\b", r"\bmovie\b",
        r"\bweather\b", r"\bfootball\b", r"\bcricket\b", r"\bbasketball\b",
        r"\bpython (program|code|script)\b", r"\bwrite (a )?code\b", r"\bhello world\b",
        r"\bwhat is 1\s*\+\s*1\b", r"\b2\s*\+\s*2\b", r"\bmath question\b",
        r"\btranslate to\b", r"\bwho won\b", r"\bhistory of\b", r"\brecipe\b"
    ]

    @classmethod
    def evaluate_deterministic(cls, question: str) -> Optional[Tuple[bool, str]]:
        """Fast Layer-1 regex check."""
        q = question.lower().strip()

        # Check explicit non-business patterns first
        for pat in cls.NON_BUSINESS_PATTERNS:
            if re.search(pat, q):
                return False, f"Matched non-business pattern: {pat}"

        # Check explicit business patterns
        for pat in cls.BUSINESS_PATTERNS:
            if re.search(pat, q):
                return True, f"Matched business pattern: {pat}"

        return None

    @classmethod
    async def classify_with_llm(cls, question: str) -> GuardClassification:
        """Layer-2 LLM Intent Classification."""
        system_prompt = """You are the Inslight AI Business Context Guard.
Your role is to strictly classify whether a user's question belongs to Business Intelligence, analytics, sales, financial metrics, tabular dataset queries, or business forecasting.

CLASSIFICATION RULES:
1. ALLOW: Questions about business performance, revenue, sales, profit, orders, prices, units, customer behavior, market trends, business calculations, or dataset schema.
2. REJECT: General knowledge, trivia, politics, entertainment, coding exercises (e.g. 'write python code'), recipes, jokes, basic non-business math (e.g. 'what is 1+1'), sports, or personal chatter.

Return ONLY a valid JSON object matching:
{
  "is_business": true | false,
  "requires_dataset": true | false,
  "reason": "Brief explanation"
}"""
        user_prompt = f"User Question: \"{question}\""

        try:
            raw = await ai_service.chat(system_prompt, user_prompt, temp=0.0, max_tokens=150)
            from app.utils.helpers import parse_json
            data = parse_json(raw)
            return GuardClassification(
                is_business=bool(data.get("is_business", False)),
                requires_dataset=bool(data.get("requires_dataset", True)),
                reason=str(data.get("reason", "LLM classified"))
            )
        except Exception as e:
            logger.warning(f"Business Context Guard LLM fallback error: {e}")
            # Fail closed for safety
            return GuardClassification(
                is_business=False,
                requires_dataset=False,
                reason="Failed to verify question relevance"
            )

    @classmethod
    async def validate_query(cls, question: str, has_dataset: bool) -> Tuple[bool, Optional[str]]:
        """
        Validate question against business context guard layers.
        Returns: (is_valid, rejection_message_or_none)
        """
        q = question.strip()
        if not q:
            return False, "Please enter a valid business question."

        # Layer 1: Deterministic evaluation
        det = cls.evaluate_deterministic(q)
        if det is not None:
            is_biz, reason = det
            if not is_biz:
                logger.info(f"[GUARD REJECT Layer 1] {q} -> {reason}")
                return False, GUARD_REJECTION_MESSAGE
            # It is a business question; now check dataset availability if question refers to data
            if not has_dataset and any(w in q.lower() for w in ["my", "this", "our", "data", "revenue", "sales", "trend"]):
                return False, NO_DATASET_MESSAGE
            return True, None

        # Layer 2: LLM Intent Classification
        classification = await cls.classify_with_llm(q)
        if not classification.is_business:
            logger.info(f"[GUARD REJECT Layer 2] {q} -> {classification.reason}")
            return False, GUARD_REJECTION_MESSAGE

        if classification.requires_dataset and not has_dataset:
            return False, NO_DATASET_MESSAGE

        return True, None
