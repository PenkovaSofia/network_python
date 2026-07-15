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
    def __init__(self) -> None:
        super().__init__(status_code=404, detail="Book not found")
        self.code = "NOT_FOUND"


class DuplicateIsbnException(HTTPException):
    def __init__(self) -> None:
        super().__init__(status_code=409, detail="ISBN already exists")
        self.code = "DUPLICATE_ISBN"


# ═══════════════════════════════════════════════════════════
# ПРИЛОЖЕНИЕ
# ═══════════════════════════════════════════════════════════

app = FastAPI(title="Bookstore API")

@app.exception_handler(BookNotFoundException)
def book_not_found_handler(request, exc: BookNotFoundException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code},
    )


@app.exception_handler(DuplicateIsbnException)
def duplicate_isbn_handler(request, exc: DuplicateIsbnException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.code},
    )

# Хранилище
BOOKS: list[dict] = []
CATEGORIES: list[dict] = []

_book_id_seq = 0
_category_id_seq = 0

# ═══════════════════════════════════════════════════════════
# КАТЕГОРИИ
# ═══════════════════════════════════════════════════════════


@app.get("/categories")
def list_categories():
    return CATEGORIES


@app.post("/categories", status_code=201)
def create_category(category: CategoryCreate):
    global _category_id_seq
    _category_id_seq += 1
    new = {"id": _category_id_seq, "name": category.name}
    CATEGORIES.append(new)
    return new


# ═══════════════════════════════════════════════════════════
# CRUID КНИГ
# ═══════════════════════════════════════════════════════════


@app.get("/books")
def list_books(category_id: Optional[int] = None, year: Optional[int] = None):
    result = BOOKS
    if category_id is not None:
        result = [b for b in result if b.get("category_id") == category_id]
    if year is not None:
        result = [b for b in result if b["year"] == year]
    return result


@app.get("/books/search")
def search_books(query: str):
    q = query.lower()
    return [
        b for b in BOOKS
        if q in b["title"].lower() or q in b["author"].lower()
    ]


@app.get("/books/{book_id}")
def get_book(book_id: int):
    for b in BOOKS:
        if b["id"] == book_id:
            return b
    raise BookNotFoundException()


@app.post("/books", status_code=201)
def create_book(book: BookCreate):
    global _book_id_seq
    for b in BOOKS:
        if b["isbn"] == book.isbn:
            raise DuplicateIsbnException()
    _book_id_seq += 1
    new = {"id": _book_id_seq, **book.model_dump()}
    BOOKS.append(new)
    return new


@app.put("/books/{book_id}")
def update_book(book_id: int, book: BookCreate):
    for b in BOOKS:
        if b["id"] == book_id:
            b.update(book.model_dump())
            return b
    raise BookNotFoundException()


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int):
    for i, b in enumerate(BOOKS):
        if b["id"] == book_id:
            BOOKS.pop(i)
            return
    raise BookNotFoundException()