"""
Dashboard Mew - Korean Learning
FastAPI app for Korean courses and vocabulary.
Content lives in content/vocab/ and content/lessons/ (versioned in this repo).
Port: 8181
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import csv
import io
import re
import uvicorn
from dataclasses import dataclass, field
from typing import List, Optional

# === Config ===
BASE_DIR = Path(__file__).parent
VOCAB_DIR = BASE_DIR / "content" / "vocab"
LESSONS_DIR = BASE_DIR / "content" / "lessons"
HOST = "0.0.0.0"
PORT = 8181

app = FastAPI(title="Dashboard Mew 🐱", description="Korean Learning Dashboard", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


# === Models ===
@dataclass
class VocabEntry:
    hangul: str
    french: str
    example: str
    translated: str
    explanation: str
    chapter: int = 0
    book: str = ""


@dataclass
class VocabBook:
    id: str  # e.g. "3A"
    name: str  # e.g. "Vocab 3A"
    filename: str
    chapters: dict = field(default_factory=dict)  # chapter_num -> list of VocabEntry
    total_words: int = 0


@dataclass
class LessonFile:
    filename: str
    name: str
    level: str  # "3A", "4A", etc.
    path: str
    topics: List[str] = field(default_factory=list)  # Roman numeral sections


def extract_lesson_topics(filepath: Path) -> List[str]:
    """Extract Roman numeral section titles from a lesson HTML file."""
    try:
        content = filepath.read_text(encoding='utf-8')
        h2s = re.findall(r'<h2[^>]*>(.*?)</h2>', content, re.DOTALL)
        topics = []
        for h in h2s:
            clean = re.sub(r'<[^>]+>', '', h).strip()
            # Normalize whitespace
            clean = re.sub(r'\s+', ' ', clean)
            # Only keep lines starting with Roman numerals (I., II., III., IV., V., etc.)
            if clean and re.match(r'^(I{1,3}|IV|V|VI{0,3})\.', clean):
                topics.append(clean)
        return topics
    except Exception:
        return []

def parse_vocab_csv(filepath: Path) -> VocabBook:
    """Parse a vocab CSV file into a VocabBook with chapters."""
    stem = filepath.stem  # "Vocab 3A"
    book_id = stem.replace("Vocab ", "")
    book = VocabBook(id=book_id, name=stem, filename=filepath.name, chapters={})
    
    current_chapter = 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    reader = csv.reader(io.StringIO(content))
    header = next(reader, None)  # Skip header
    
    for row in reader:
        if len(row) < 5:
            continue
        
        hangul, french, example, translated, explanation = row[0], row[1], row[2], row[3], row[4]
        
        # Detect chapter markers like "1과", "2과"
        if hangul.strip() and hangul.strip().replace("과", "").isdigit() and not french.strip():
            current_chapter = int(hangul.strip().replace("과", ""))
            if current_chapter not in book.chapters:
                book.chapters[current_chapter] = []
            continue
        
        # Skip empty separator rows
        if not hangul.strip() and not french.strip():
            continue
        
        entry = VocabEntry(
            hangul=hangul.strip(),
            french=french.strip(),
            example=example.strip(),
            translated=translated.strip(),
            explanation=explanation.strip(),
            chapter=current_chapter,
            book=book_id,
        )
        
        if current_chapter not in book.chapters:
            book.chapters[current_chapter] = []
        book.chapters[current_chapter].append(entry)
        book.total_words += 1
    
    return book


def list_vocab_books() -> List[VocabBook]:
    """List all available vocab books."""
    books = []
    if VOCAB_DIR.exists():
        for csv_file in sorted(VOCAB_DIR.glob("*.csv")):
            book = parse_vocab_csv(csv_file)
            books.append(book)
    return books


def get_vocab_book(book_id: str) -> Optional[VocabBook]:
    """Get a specific vocab book by ID."""
    csv_file = VOCAB_DIR / f"Vocab {book_id}.csv"
    if csv_file.exists():
        return parse_vocab_csv(csv_file)
    return None


def list_lessons() -> dict:
    """List all available lessons grouped by level."""
    lessons_by_level = {}
    if LESSONS_DIR.exists():
        for level_dir in sorted(LESSONS_DIR.iterdir()):
            if level_dir.is_dir():
                level = level_dir.name
                lessons_by_level[level] = []
                for html_file in sorted(level_dir.glob("*.html")):
                    topics = extract_lesson_topics(html_file)
                    lessons_by_level[level].append(LessonFile(
                        filename=html_file.name,
                        name=html_file.stem,
                        level=level,
                        path=str(html_file),
                        topics=topics,
                    ))
    return lessons_by_level


# === API ===
@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "dashboard-mew"}


@app.get("/api/books")
async def api_books():
    books = list_vocab_books()
    return {
        "books": [
            {"id": b.id, "name": b.name, "total_words": b.total_words, "chapters": len(b.chapters)}
            for b in books
        ]
    }


@app.get("/api/books/{book_id}")
async def api_book(book_id: str):
    book = get_vocab_book(book_id)
    if not book:
        return {"error": "Not found"}, 404
    
    chapters_data = {}
    for ch_num, entries in sorted(book.chapters.items()):
        chapters_data[ch_num] = [
            {
                "hangul": e.hangul,
                "french": e.french,
                "example": e.example,
                "translated": e.translated,
                "explanation": e.explanation,
            }
            for e in entries
        ]
    
    return {
        "id": book.id,
        "name": book.name,
        "total_words": book.total_words,
        "chapters": chapters_data,
    }


# === Pages ===
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    books = list_vocab_books()
    return templates.TemplateResponse(request, "home.html", context={"books": books})


@app.get("/vocab/{book_id}", response_class=HTMLResponse)
async def vocab_detail(request: Request, book_id: str, chapter: Optional[int] = None):
    book = get_vocab_book(book_id)
    if not book:
        return HTMLResponse("<h1>Book not found</h1>", status_code=404)
    
    books = list_vocab_books()
    return templates.TemplateResponse(
        request,
        "vocab.html",
        context={
            "book": book,
            "books": books,
            "selected_chapter": chapter,
        }
    )


@app.get("/lessons", response_class=HTMLResponse)
async def lessons_home(request: Request):
    lessons_data = list_lessons()
    return templates.TemplateResponse(request, "lessons.html", context={"lessons_by_level": lessons_data})


@app.get("/lessons/view/{level}/{filename}", response_class=HTMLResponse)
async def view_lesson(level: str, filename: str):
    file_path = LESSONS_DIR / level / filename
    if not file_path.exists():
        return HTMLResponse("<h1>Lesson not found</h1>", status_code=404)
    # Return raw HTML content of the lesson
    content = file_path.read_text(encoding='utf-8')
    # Inject a back button at the top for easy navigation
    back_btn = f'''
    <div style="background:#0a0a0f; padding:15px 25px; border-bottom:1px solid #2a2a3e; display:flex; gap:10px; align-items:center; position:sticky; top:0; z-index:1000;">
        <a href="/lessons" style="color:#e8e8f0; text-decoration:none; font-family:sans-serif; font-size:14px; background:#22223a; padding:8px 16px; border-radius:8px;">← Retour aux lessons</a>
        <span style="color:#8888aa; font-family:sans-serif; font-size:14px;">/ Lessons / {level} / {filename.replace(".html", "")}</span>
    </div>
    '''
    # Insert right after body tag if possible
    if '<body' in content:
        import re
        content = re.sub(r'(<body[^>]*>)', f'\\1\n{back_btn}', content, count=1)
    else:
        content = back_btn + content
        
    return HTMLResponse(content)


if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True, log_level="info")
