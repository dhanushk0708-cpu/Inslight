from typing import Any, Dict
from app.models.dataset import Dataset
from app.services.deep_dive_service import DeepDiveResearchService


class DeepDiveEngine:
    @classmethod
    async def analyze_dataset(cls, dataset: Dataset, refresh: bool = False) -> Dict[str, Any]:
        """Delegates to the comprehensive 10-section DeepDiveResearchService."""
        return await DeepDiveResearchService.analyze_dataset(dataset, refresh=refresh)
