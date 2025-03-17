from datetime import date
from typing import List, Optional
import uuid
from ninja import NinjaAPI, Schema
from catalog.models import Author, Genre, Language, Book, BookInstance


libapi = NinjaAPI(urls_namespace="libapi-v1")


class AuthorSchema(Schema):
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    date_of_death: Optional[date] = None


class AuthorSchemaUpdate(Schema):
    first_name: str = None
    last_name: str = None
    date_of_birth: Optional[date] = None
    date_of_death: Optional[date] = None


class GenreSchema(Schema):
    name: str


class LanguageSchema(Schema):
    name: str


class BookSchema(Schema):
    title: str
    author: AuthorSchema = None
    summary: str
    isbn: str
    genre: List[GenreSchema] = None


class BookSchemaUpdate(Schema):
    title: str = None
    author: AuthorSchema = None
    summary: str = None
    isbn: str = None
    genre: List[GenreSchema] = None


class BookInstanceSchema(Schema):
    id: uuid.UUID
    book: BookSchema
    imprint: str
    due_back: Optional[date] = None
    status: str


class BookInstanceSchemaUpdate(Schema):
    imprint: str = None
    due_back: Optional[date] = None
    status: str = None


class Error(Schema):
    message: str


@libapi.get("/all_books", response=List[BookSchema])
def all_books(request):
    books = Book.objects.all()
    return books


@libapi.get("/books", response=List[BookSchema])
def books(request, title: str = None, author: str = None, genre: str = None):
    books = Book.objects.all()
    if title:
        books = books.filter(title__icontains=title)
    if author:
        books = books.filter(author__first_name__icontains=author) | books.filter(
            author__last_name__icontains=author)
    if genre:
        books = books.filter(genre__name__icontains=genre)
    return books


@libapi.post("/books", response={200: BookSchema, 403: Error})
def create_book(request, data_in: BookSchema):
    if not request.user.is_authenticated:
        return 403, {"message": "Please sign in first"}
    book = Book.objects.create(
        title=data_in.title,
        author=Author.objects.get_or_create(
            first_name=data_in.author.first_name,
            last_name=data_in.author.last_name,
            date_of_birth=data_in.author.date_of_birth,
            date_of_death=data_in.author.date_of_death
        )[0],
        summary=data_in.summary,
        isbn=data_in.isbn,
    )

    book.genre.set([Genre.objects.get_or_create(name=genre.name)[0]
                    for genre in data_in.genre])
    return 200, book


@libapi.get("/books/{id}", response={200: BookSchema, 404: Error})
def book_id(request, id: int):
    try:
        book = Book.objects.get(id=id)
    except Book.DoesNotExist:
        return 404, {"message": "Book not found"}
    return 200, book


@libapi.put("/books/{id}", response={200: BookSchema, 404: Error, 403: Error})
def update_book(request, id: int, data_in: BookSchemaUpdate):
    if not request.user.is_authenticated:
        return 403, {"message": "Please sign in first"}
    try:
        book = Book.objects.get(id=id)
    except Book.DoesNotExist:
        return 404, {"message": "Book not found"}
    if data_in.title:
        book.title = data_in.title
    if data_in.author:
        book.author = Author.objects.get_or_create(
            first_name=data_in.author.first_name,
            last_name=data_in.author.last_name,
            date_of_birth=data_in.author.date_of_birth,
            date_of_death=data_in.author.date_of_death
        )[0]
    if data_in.summary:
        book.summary = data_in.summary
    if data_in.isbn:
        book.isbn = data_in.isbn
    if data_in.genre:
        book.genre.set([Genre.objects.get_or_create(name=genre.name)[0]
                        for genre in data_in.genre])
    book.save()
    return 200, book


@libapi.delete("/books/{id}", response={204: None, 404: Error, 403: Error})
def delete_book(request, id: int):
    if not request.user.is_authenticated:
        return 403, {"message": "Please sign in first"}
    try:
        book = Book.objects.get(id=id)
    except Book.DoesNotExist:
        return 404, {"message": "Book not found"}
    book.bookinstance_set.all().delete()
    book.delete()
    return 204, None


@libapi.get("/all_book_instances", response=List[BookInstanceSchema])
def all_book_instances(request):
    book_instances = BookInstance.objects.all()
    return book_instances


@libapi.get("/book_instances/{id}", response={200: BookInstanceSchema, 404: Error})
def book_instances(request, id: uuid.UUID):
    try:
        book_instances = BookInstance.objects.get(id=id)
    except BookInstance.DoesNotExist:
        return 404, {"message": "Book instance not found"}
    return 200, book_instances


@libapi.post("/book_instances", response={200: BookInstanceSchema, 403: Error})
def create_book_instance(request, data_in: BookInstanceSchema):
    if not request.user.is_authenticated:
        return 403, {"message": "Please sign in first"}
    book, _ = Book.objects.get_or_create(
        title=data_in.book.title,
        author=Author.objects.get_or_create(
            first_name=data_in.book.author.first_name,
            last_name=data_in.book.author.last_name,
            date_of_birth=data_in.book.author.date_of_birth,
            date_of_death=data_in.book.author.date_of_death
        )[0],
        summary=data_in.book.summary,
        isbn=data_in.book.isbn
    )

    book.genre.set([Genre.objects.get_or_create(name=genre.name)[0]
                   for genre in data_in.book.genre])

    book_instance = BookInstance.objects.create(
        book=book,
        imprint=data_in.imprint,
        due_back=data_in.due_back,
        status=data_in.status
    )
    return 200, book_instance


@libapi.put("/book_instances{id}", response={200: BookInstanceSchema, 404: Error, 403: Error})
def update_book_instance(request, id: uuid.UUID, data_in: BookInstanceSchemaUpdate):
    if not request.user.is_authenticated:
        return 403, {"message": "Please sign in first"}
    try:
        book_instance = BookInstance.objects.get(id=id)
    except BookInstance.DoesNotExist:
        return 404, {"message": "Book instance not found"}

    if data_in.imprint:
        book_instance.imprint = data_in.imprint
    if data_in.due_back:
        book_instance.due_back = data_in.due_back
    if data_in.status:
        book_instance.status = data_in.status
    book_instance.save()
    return 200, book_instance


@libapi.delete("/book_instances/{id}", response={204: None, 404: Error, 403: Error})
def delete_book_instance(request, id: uuid.UUID):
    if not request.user.is_authenticated:
        return 403, {"message": "Please sign in first"}
    try:
        book_instance = BookInstance.objects.get(id=id)
    except BookInstance.DoesNotExist:
        return 404, {"message": "Book instance not found"}
    book_instance.delete()
    return 204, None


@libapi.get("/authors", response=List[AuthorSchema])
def authors(request, first_name: str = None, last_name: str = None):
    if first_name and last_name:
        authors = Author.objects.filter(
            first_name__icontains=first_name, last_name__icontains=last_name
        )
    elif first_name:
        authors = Author.objects.filter(first_name__icontains=first_name)
    elif last_name:
        authors = Author.objects.filter(last_name__icontains=last_name)
    else:
        authors = Author.objects.all()
    return authors


@libapi.post("/authors", response={200: AuthorSchema, 403: Error})
def create_author(request, data_in: AuthorSchema):
    if not request.user.is_authenticated:
        return 403, {"message": "Please sign in first"}
    # if not data_in.first_name or not data_in.last_name:
    #     return 422, {"message": "First name and last name are required fields"}
    author = Author.objects.create(
        first_name=data_in.first_name,
        last_name=data_in.last_name,
        date_of_birth=data_in.date_of_birth,
        date_of_death=data_in.date_of_death)
    return 200, author


@libapi.get("/authors/{id}", response={200: AuthorSchema, 404: Error})
def author_id(request, id: int):
    try:
        author = Author.objects.get(id=id)
    except Author.DoesNotExist:
        return 404, {"message": "Author not found"}
    return 200, author


@libapi.put("/authors/{id}", response={200: AuthorSchema, 404: Error, 403: Error})
def update_author(request, id: int, data_in: AuthorSchemaUpdate):
    if not request.user.is_authenticated:
        return 403, {"message": "Please sign in first"}
    try:
        author = Author.objects.get(id=id)
    except Author.DoesNotExist:
        return 404, {"message": "Author not found"}
    if data_in.first_name:
        author.first_name = data_in.first_name
    if data_in.last_name:
        author.last_name = data_in.last_name
    if data_in.date_of_birth:
        author.date_of_birth = data_in.date_of_birth
    if data_in.date_of_death:
        author.date_of_death = data_in.date_of_death
    author.save()
    return 200, author


@libapi.delete("/authors/{id}", response={204: None, 404: Error, 403: Error})
def delete_author(request, id: int):
    if not request.user.is_authenticated:
        return 403, {"message": "Please sign in first"}
    try:
        author = Author.objects.get(id=id)
    except Author.DoesNotExist:
        return 404, {"message": "Author not found"}
    author.delete()
    return 204, None


@libapi.get("/genres", response=List[GenreSchema])
def genres(request):
    genres = Genre.objects.all()
    return genres


@libapi.post("/genres", response={200: GenreSchema, 403: Error})
def create_genre(request, data_in: GenreSchema):
    if not request.user.is_authenticated:
        return 403, {"message": "Please sign in first"}
    genre = Genre.objects.create(name=data_in.name)
    return genre


@libapi.get("/genres/{id}", response={200: GenreSchema, 404: Error})
def genre_id(request, id: int):
    try:
        genre = Genre.objects.get(id=id)
    except Genre.DoesNotExist:
        return 404, {"message": "Genre not found"}
    return genre


@libapi.put("/genres/{id}", response={200: GenreSchema, 404: Error, 403: Error})
def update_genre(request, id: int, data_in: GenreSchema):
    if not request.user.is_authenticated:
        return 403, {"message": "Please sign in first"}
    try:
        genre = Genre.objects.get(id=id)
    except Genre.DoesNotExist:
        return 404, {"message": "Genre not found"}
    genre.name = data_in.name
    genre.save()
    return genre


@libapi.delete("/genres/{id}", response={204: None, 404: Error, 403: Error})
def delete_genre(request, id: int):
    if not request.user.is_authenticated:
        return 403, {"message": "Please sign in first"}
    try:
        genre = Genre.objects.get(id=id)
    except Genre.DoesNotExist:
        return 404, {"message": "Genre not found"}
    genre.delete()
    return 204, None


@libapi.get("/languages", response=List[LanguageSchema])
def languages(request):
    languages = Language.objects.all()
    return languages


@libapi.post("/languages", response={200: LanguageSchema, 403: Error})
def create_language(request, data_in: LanguageSchema):
    if not request.user.is_authenticated:
        return 403, {"message": "Please sign in first"}
    language = Language.objects.create(name=data_in.name)
    return 200, language


@libapi.get("/languages/{id}", response={200: LanguageSchema, 404: Error})
def language_id(request, id: int):
    try:
        language = Language.objects.get(id=id)
    except Language.DoesNotExist:
        return 404, {"message": "Language not found"}
    return 200, language


@libapi.put("/languages/{id}", response={200: LanguageSchema, 404: Error, 403: Error})
def update_language(request, id: int, data_in: LanguageSchema):
    if not request.user.is_authenticated:
        return 403, {"message": "Please sign in first"}
    try:
        language = Language.objects.get(id=id)
    except Language.DoesNotExist:
        return 404, {"message": "Language not found"}
    language.name = data_in.name
    language.save()
    return 200, language


@libapi.delete("/languages/{id}", response={204: None, 404: Error, 403: Error})
def delete_language(request, id: int):
    if not request.user.is_authenticated:
        return 403, {"message": "Please sign in first"}
    try:
        language = Language.objects.get(id=id)
    except Language.DoesNotExist:
        return 404, {"message": "Language not found"}
    language.delete()
    return 204, None
