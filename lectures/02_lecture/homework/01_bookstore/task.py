"""
01_bookstore — CRUD API для книжного магазина 📚
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional

# ═══════════════════════════════════════════════════════════
# МОДЕЛИ
# ═══════════════════════════════════════════════════════════


class Category(BaseModel):
    """Доменная модель категории. Возвращается в ответах."""

    id: int
    name: str = Field(min_length=1, max_length=50)


class CategoryCreate(BaseModel):
    """Модель для создания категории (без id, лишние поля запрещены)."""

    name: str = Field(min_length=1, max_length=50)

    model_config = {"extra": "forbid"}


class Book(BaseModel):
    """Доменная модель книги. Возвращается в ответах GET/PUT."""

    id: int
    title: str = Field(min_length=1, max_length=100)
    author: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=0, le=2025)
    isbn: str
    price: float = Field(gt=0)
    category_id: Optional[int] = None


class BookCreate(BaseModel):
    """Модель для создания/обновления книги (без id — сервер сгенерирует)."""

    title: str = Field(min_length=1, max_length=100)
    author: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=0, le=2025)
    isbn: str
    price: float = Field(gt=0)
    category_id: Optional[int] = None


# ═══════════════════════════════════════════════════════════
# ИСКЛЮЧЕНИЯ
# ═══════════════════════════════════════════════════════════


class BookNotFoundException(HTTPException):
    """404 — книга не найдена."""

    def __init__(self):
        super().__init__(status_code=404, detail="Book not found")


class DuplicateIsbnException(HTTPException):
    """409 — ISBN уже существует."""

    def __init__(self, isbn: str):
        super().__init__(status_code=409, detail=f"Book with ISBN {isbn} already exists")


# ═══════════════════════════════════════════════════════════
# ОБРАБОТЧИКИ ОШИБОК
# ═══════════════════════════════════════════════════════════

app = FastAPI(title="Bookstore API")


@app.exception_handler(BookNotFoundException)
async def book_not_found_handler(request, exc: BookNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"detail": exc.detail, "code": "NOT_FOUND"},
    )


@app.exception_handler(DuplicateIsbnException)
async def duplicate_isbn_handler(request, exc: DuplicateIsbnException):
    return JSONResponse(
        status_code=409,
        content={"detail": exc.detail, "code": "DUPLICATE_ISBN"},
    )


# Хранилище
BOOKS: list[dict] = []
CATEGORIES: list[dict] = []
_next_book_id = 1
_next_category_id = 1


# ═══════════════════════════════════════════════════════════
# КАТЕГОРИИ
# ═══════════════════════════════════════════════════════════


@app.get("/categories")
def list_categories():
    """GET /categories — список всех категорий."""
    return CATEGORIES


@app.post("/categories", status_code=201)
def create_category(category: CategoryCreate):
    """POST /categories — создать категорию."""
    global _next_category_id
    new_category = {"id": _next_category_id, "name": category.name}
    CATEGORIES.append(new_category)
    _next_category_id += 1
    return new_category


# ═══════════════════════════════════════════════════════════
# CRUID КНИГ
# ═══════════════════════════════════════════════════════════


@app.get("/books")
def list_books(category_id: Optional[int] = None, year: Optional[int] = None):
    """GET /books — список книг. Опциональная фильтрация по category_id и year."""
    result = BOOKS
    if category_id is not None:
        result = [b for b in result if b.get("category_id") == category_id]
    if year is not None:
        result = [b for b in result if b.get("year") == year]
    return result


@app.get("/books/search")
def search_books(query: str):
    """GET /books/search?query=... — поиск по title и author (case-insensitive)."""
    q = query.lower()
    return [
        b for b in BOOKS
        if q in b["title"].lower() or q in b["author"].lower()
    ]


@app.get("/books/{book_id}")
def get_book(book_id: int):
    """GET /books/{id} — одна книга."""
    for b in BOOKS:
        if b["id"] == book_id:
            return b
    raise BookNotFoundException()


@app.post("/books", status_code=201)
def create_book(book: BookCreate):
    """POST /books — создать книгу.

    Проверять уникальность ISBN. Если дубликат — DuplicateIsbnException.
    """
    global _next_book_id
    if any(b["isbn"] == book.isbn for b in BOOKS):
        raise DuplicateIsbnException(book.isbn)
    new_book = book.model_dump()
    new_book["id"] = _next_book_id
    BOOKS.append(new_book)
    _next_book_id += 1
    return new_book


@app.put("/books/{book_id}")
def update_book(book_id: int, book: BookCreate):
    """PUT /books/{id} — полностью обновить книгу."""
    for i, b in enumerate(BOOKS):
        if b["id"] == book_id:
            updated = book.model_dump()
            updated["id"] = book_id
            BOOKS[i] = updated
            return updated
    raise BookNotFoundException()


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int):
    """DELETE /books/{id} — удалить книгу."""
    for i, b in enumerate(BOOKS):
        if b["id"] == book_id:
            BOOKS.pop(i)
            return
    raise BookNotFoundException()
