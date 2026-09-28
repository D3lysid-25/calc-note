from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime


class TagBase(BaseModel):
    name: str


class TagCreate(TagBase):
    pass


class Tag(TagBase):
    id: int

    class Config:
        from_attributes = True


class NoteBase(BaseModel):
    title: str = "Nouvelle note"
    content: str = "[]"  # JSON string of cells
    category: str = "Général"
    tags: List[str] = []


class NoteCreate(NoteBase):
    pass


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None


class Note(NoteBase):
    id: int
    created_at: datetime
    updated_at: datetime
    tags: List[Tag] = []

    class Config:
        from_attributes = True


class CellEvalRequest(BaseModel):
    expression: str
    context: dict = Field(default_factory=dict)  # previous variables


class CellEvalResponse(BaseModel):
    success: bool
    result: Optional[str] = None
    result_latex: Optional[str] = None
    error: Optional[str] = None
    variables: dict = Field(default_factory=dict)
