# API Specification

## Base URL
`/api/v1/`

## Authentication
Token Authentication is used.
Include the token in the `Authorization` header for protected endpoints.

**Header Format:**
```
Authorization: Token <your_token>
```

---

## Endpoints

### 1. Accounts
Base Path: `/api/v1/accounts/`

#### Signup
Create a new user account.

- **URL:** `/signup/`
- **Method:** `POST`
- **Permission:** Allow Any
- **Request Body:**
  - `username` (string, required)
  - `password` (string, required)
  - `email` (string, optional)
  - `nickname` (string, optional)
  - `sex` (string, optional)
  - `birth_year` (integer, optional)
  - `books_per_month` (integer, optional, default: 0)
- **Response (201 Created):**
  ```json
  {
    "token": "string",
    "user": {
      "id": 1,
      "username": "string",
      "email": "string",
      "nickname": "string",
      "sex": "string",
      "birth_year": 1990,
      "books_per_month": 0
    }
  }
  ```

#### Login
Authenticate a user and retrieve a token.

- **URL:** `/login/`
- **Method:** `POST`
- **Permission:** Allow Any
- **Request Body:**
  - `username` (string, required)
  - `password` (string, required)
- **Response (200 OK):**
  ```json
  {
    "token": "string",
    "user_id": 1,
    "username": "string"
  }
  ```

#### Logout
Invalidate the current token.

- **URL:** `/logout/`
- **Method:** `POST`
- **Permission:** IsAuthenticated
- **Response (200 OK):**
  ```json
  {
    "message": "Successfully logged out."
  }
  ```

#### Profile
Get or update the current user's profile.

- **URL:** `/profile/`
- **Method:** `GET`, `PATCH`
- **Permission:** IsAuthenticated

**GET Response:**
- Returns the user object (same fields as Signup response).

**PATCH Request Body:**
- Any of the user fields (`email`, `nickname`, `sex`, `birth_year`, `books_per_month`).

---

### 2. Books
Base Path: `/api/v1/books/`

#### List Books
Get a list of books with optional filtering.

- **URL:** `/`
- **Method:** `GET`
- **Permission:** Allow Any
- **Query Parameters:**
  - `search`: Search by title, author name, or genre.
  - `genre`: Filter by exact genre match.
  - `page`: Page number for pagination.
- **Response (200 OK):**
  - List of Book objects.

#### Book Detail
Get detailed information about a specific book.

- **URL:** `/<isbn>/`
- **Method:** `GET`
- **Permission:** Allow Any
- **Response (200 OK):**
  - Book object.

**Book Object Structure:**
```json
{
  "isbn": 1234567890,
  "title": "string",
  "subtitle": "string",
  "genre": "string",
  "publisher": "string",
  "one_line_desc": "string",
  "two_line_desc": "string",
  "full_desc": "string",
  "cover": "string (URL)",
  "readed_num_month": 0,
  "readed_num_week": 0,
  "is_steady": false,
  "published_date": "datetime",
  "page_count": 0,
  "series": "string",
  "lang": "string",
  "like_num": 0,
  "toc": {},
  "content": "string (URL or path)",
  "authors": [
    {
      "name": "string",
      "role": "string"
    }
  ],
  "tags": ["string"]
}
```

---

### 3. Library (My Books)
Base Path: `/api/v1/library/`

#### List Library
Get the list of books in the user's library.

- **URL:** `/`
- **Method:** `GET`
- **Permission:** IsAuthenticated
- **Response (200 OK):**
  - List of Library objects.

**Library Object Structure:**
```json
{
  "id": 1,
  "user": 1,
  "isbn": 1234567890,
  "is_downloaded": false,
  "book_verification": "datetime",
  "added_at": "datetime",
  "book": { ...Book Object... }
}
```

#### Add to Library
Add a book to the user's library.

- **URL:** `/`
- **Method:** `POST`
- **Permission:** IsAuthenticated
- **Request Body:**
  - `isbn` (integer, required)
- **Response (201 Created):**
  - Created Library object.

#### Remove from Library
Remove a book from the user's library.

- **URL:** `/<isbn>/`
- **Method:** `DELETE`
- **Permission:** IsAuthenticated
- **Response (204 No Content)**

#### Download Book
Download the book content (EPUB).

- **URL:** `/<isbn>/download/`
- **Method:** `GET`
- **Permission:** IsAuthenticated
- **Response (200 OK):**
  - File download or JSON with `download_url`.

---

### 4. Wishlist
Base Path: `/api/v1/wishlist/`

#### List Wishlist
Get the user's wishlist.

- **URL:** `/`
- **Method:** `GET`
- **Permission:** IsAuthenticated
- **Response (200 OK):**
  - List of Wishlist objects.

**Wishlist Object Structure:**
```json
{
  "id": 1,
  "user": 1,
  "isbn": 1234567890,
  "added_at": "datetime",
  "book": { ...Book Object... }
}
```

#### Add to Wishlist
Add a book to the wishlist.

- **URL:** `/`
- **Method:** `POST`
- **Permission:** IsAuthenticated
- **Request Body:**
  - `isbn` (integer, required)
- **Response (201 Created):**
  - Created Wishlist object.

#### Remove from Wishlist
Remove a book from the wishlist.

- **URL:** `/<isbn>/`
- **Method:** `DELETE`
- **Permission:** IsAuthenticated
- **Response (204 No Content)**

---

### 5. Highlights
Base Path: `/api/v1/highlights/`

#### List Highlights
Get the user's highlights.

- **URL:** `/`
- **Method:** `GET`
- **Permission:** IsAuthenticated
- **Query Parameters:**
  - `isbn`: Filter by book ISBN.
- **Response (200 OK):**
  - List of Highlight objects.

**Highlight Object Structure:**
```json
{
  "id": 1,
  "user": 1,
  "isbn": 1234567890,
  "content": "string",
  "created_at": "datetime",
  "location_start": 0,
  "location_end": 0
}
```

#### Create Highlight
Create a new highlight.

- **URL:** `/`
- **Method:** `POST`
- **Permission:** IsAuthenticated
- **Request Body:**
  - `isbn` (integer, required)
  - `content` (string, required)
  - `location_start` (integer, required)
  - `location_end` (integer, required)
- **Response (201 Created):**
  - Created Highlight object.

#### Delete Highlight
Delete a highlight.

- **URL:** `/<pk>/` (Note: Uses Highlight ID, not ISBN)
- **Method:** `DELETE`
- **Permission:** IsAuthenticated
- **Response (204 No Content)**

---

### 6. Reading History
Base Path: `/api/v1/history/`

#### List History
Get the user's reading history.

- **URL:** `/`
- **Method:** `GET`
- **Permission:** IsAuthenticated
- **Response (200 OK):**
  - List of UserBookHistory objects.

**UserBookHistory Object Structure:**
```json
{
  "id": 1,
  "user": 1,
  "isbn": 1234567890,
  "started_at": "datetime",
  "finished_at": "datetime",
  "last_page": 0,
  "last_read_at": "datetime",
  "progress": 0.0,
  "review": "string",
  "like": false,
  "book": { ...Book Object... }
}
```

#### Start Reading
Create a new reading history entry.

- **URL:** `/`
- **Method:** `POST`
- **Permission:** IsAuthenticated
- **Request Body:**
  - `isbn` (integer, required)
- **Response (201 Created):**
  - Created UserBookHistory object.

#### Update History
Update reading progress, review, etc.

- **URL:** `/<isbn>/`
- **Method:** `PATCH`
- **Permission:** IsAuthenticated
- **Request Body:**
  - `finished_at` (datetime, optional)
  - `last_page` (integer, optional)
  - `last_read_at` (datetime, optional)
  - `progress` (float, optional)
  - `review` (string, optional)
  - `like` (boolean, optional)
- **Response (200 OK):**
  - Updated UserBookHistory object.

---

### 7. Recommendations
Base Path: `/api/v1/recommendations/`

#### Get Recommendations
Get a list of recommended books for the user.

- **URL:** `/`
- **Method:** `GET`
- **Permission:** IsAuthenticated
- **Response (200 OK):**
  - List of Book objects.

---

### 8. Auth Utilities
Base Path: `/api/v1/auth/`

#### Get Current User Info
Get the currently logged-in user's information.

- **URL:** `/me/`
- **Method:** `GET`
- **Permission:** IsAuthenticated
- **Response (200 OK):**
  - User object (id, username, email, nickname, sex, birth_year, books_per_month).

#### Get Current User Token
Get the token for the currently logged-in user.

- **URL:** `/token/`
- **Method:** `GET`
- **Permission:** IsAuthenticated
- **Response (200 OK):**
  ```json
  {
    "token": "string"
  }
  ```
