from __future__ import annotations
import logging
from pathlib import Path
from typing import Union
from llama_parse import LlamaParse
from llama_parse.utils import ResultType, Language
from app.core.config import settings
from app.core.error.exceptions import DocumentProcessingException
from app.infra.document.schemas import ParsedDocument

logger = logging.getLogger(__name__)


class DocumentParser:
    def __init__(
        self,
        api_key: str | None = None,
        result_type: ResultType = ResultType.TXT,
        language: Language = Language.KOREAN,
        num_workers: int = 4,
        verbose: bool = False,
    ) -> None:
        resolved_key = api_key or settings.LLAMA_CLOUD_API_KEY
        if not resolved_key:
            raise DocumentProcessingException(
                message="LLAMA_CLOUD_API_KEY가 설정되지 않았습니다.",
                details={"hint": "환경변수 또는 .env 파일에 LLAMA_CLOUD_API_KEY를 설정하세요."},
            )
        self._parser = LlamaParse(
            api_key=resolved_key,
            result_type=result_type,
            language=language,
            num_workers=num_workers,
            verbose=verbose,
        )

    async def parse_pdf(
        self, file_path: Union[str, Path], file_name: str | None = None
    ) -> ParsedDocument:
        path = Path(file_path)
        if not path.exists():
            raise DocumentProcessingException(
                message=f"파일을 찾을 수 없습니다: {path}",
                details={"file_path": str(path)},
            )
        if path.suffix.lower() != ".pdf":
            raise DocumentProcessingException(
                message=f"PDF 파일만 지원합니다. 전달된 확장자: {path.suffix}",
                details={"file_path": str(path)},
            )
        name = file_name or path.name
        logger.info("LlamaParse 파싱 시작", extra={"file": name})
        try:
            llama_docs = await self._parser.aload_data(str(path))
        except Exception as exc:
            logger.exception("LlamaParse 파싱 실패")
            raise DocumentProcessingException(
                message=f"PDF 파싱 중 오류가 발생했습니다: {exc}",
                details={"file_name": name, "error": str(exc)},
            ) from exc
        if not llama_docs:
            raise DocumentProcessingException(
                message="파싱 결과가 비어 있습니다.",
                details={"file_name": name},
            )
        result = ParsedDocument.from_llama_documents(file_name=name, llama_docs=llama_docs)
        logger.info("LlamaParse 파싱 완료", extra={"file": name, "pages": result.total_pages})
        return result