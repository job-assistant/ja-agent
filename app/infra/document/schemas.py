from __future__ import annotations
from pydantic import BaseModel, Field


class ParsedPage(BaseModel):
    page: int = Field(..., description="1-based 페이지 번호")
    text: str = Field(..., description="페이지에서 추출된 텍스트")
    metadata: dict = Field(default_factory=dict)


class ParsedDocument(BaseModel):
    file_name: str = Field(..., description="원본 파일명")
    total_pages: int = Field(..., description="전체 페이지 수")
    pages: list[ParsedPage] = Field(default_factory=list)
    full_text: str = Field("", description="모든 페이지 텍스트 합산")

    @classmethod
    def from_llama_documents(cls, file_name: str, llama_docs: list) -> "ParsedDocument":
        pages: list[ParsedPage] = []
        for idx, doc in enumerate(llama_docs, start=1):
            raw_meta = doc.metadata if hasattr(doc, "metadata") else {}
            page_num = int(raw_meta.get("page_label", raw_meta.get("page", idx)))
            pages.append(ParsedPage(page=page_num, text=doc.text, metadata=raw_meta))
        full_text = "\n\n".join(p.text for p in pages)
        return cls(file_name=file_name, total_pages=len(pages), pages=pages, full_text=full_text)