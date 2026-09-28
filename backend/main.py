from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os

from database import engine, get_db, Base
import models
import schemas
from calculator import evaluate_expression

# Création des tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CalcNotes",
    description="Notes de calcul (style SMath / Excel)",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Chemin vers les fichiers statiques
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


# ---------- Notes ----------

@app.get("/api/notes", response_model=List[schemas.Note])
def list_notes(
    category: str | None = None,
    tag: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Note)

    if category:
        query = query.filter(models.Note.category == category)
    if tag:
        query = query.join(models.Note.tags).filter(models.Tag.name == tag)
    if q:
        query = query.filter(
            models.Note.title.contains(q) | models.Note.content.contains(q)
        )

    notes = query.order_by(models.Note.updated_at.desc()).all()
    return notes


@app.post("/api/notes", response_model=schemas.Note)
def create_note(note: schemas.NoteCreate, db: Session = Depends(get_db)):
    db_note = models.Note(
        title=note.title,
        content=note.content,
        category=note.category,
    )

    # Gestion des tags
    for tag_name in note.tags:
        tag = db.query(models.Tag).filter(models.Tag.name == tag_name).first()
        if not tag:
            tag = models.Tag(name=tag_name)
            db.add(tag)
        db_note.tags.append(tag)

    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


@app.get("/api/notes/{note_id}", response_model=schemas.Note)
def get_note(note_id: int, db: Session = Depends(get_db)):
    note = db.query(models.Note).filter(models.Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note non trouvée")
    return note


@app.put("/api/notes/{note_id}", response_model=schemas.Note)
def update_note(
    note_id: int, note_update: schemas.NoteUpdate, db: Session = Depends(get_db)
):
    note = db.query(models.Note).filter(models.Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note non trouvée")

    if note_update.title is not None:
        note.title = note_update.title
    if note_update.content is not None:
        note.content = note_update.content
    if note_update.category is not None:
        note.category = note_update.category

    if note_update.tags is not None:
        note.tags.clear()
        for tag_name in note_update.tags:
            tag = db.query(models.Tag).filter(models.Tag.name == tag_name).first()
            if not tag:
                tag = models.Tag(name=tag_name)
                db.add(tag)
            note.tags.append(tag)

    db.commit()
    db.refresh(note)
    return note


@app.delete("/api/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = db.query(models.Note).filter(models.Note.id == note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note non trouvée")
    db.delete(note)
    db.commit()
    return {"ok": True}


# ---------- Tags & Categories ----------

@app.get("/api/tags", response_model=List[schemas.Tag])
def list_tags(db: Session = Depends(get_db)):
    return db.query(models.Tag).order_by(models.Tag.name).all()


@app.get("/api/categories")
def list_categories(db: Session = Depends(get_db)):
    cats = db.query(models.Note.category).distinct().all()
    return [c[0] for c in cats if c[0]]


# ---------- Calcul ----------

@app.post("/api/evaluate", response_model=schemas.CellEvalResponse)
def evaluate_cell(req: schemas.CellEvalRequest):
    success, result, result_latex, variables = evaluate_expression(
        req.expression, req.context
    )

    if not success:
        error = variables.pop("__error__", "Erreur d'évaluation")
        return schemas.CellEvalResponse(
            success=False, error=error, variables=variables
        )

    # Sérialisation simple des variables (on ne garde que str/int/float pour le JSON)
    safe_vars = {}
    for k, v in variables.items():
        if k.startswith("__"):
            continue
        try:
            safe_vars[k] = str(v)
        except Exception:
            pass

    return schemas.CellEvalResponse(
        success=True,
        result=result,
        result_latex=result_latex,
        variables=safe_vars,
    )


# ---------- Frontend (SPA) ----------

@app.get("/")
def serve_frontend():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "CalcNotes API v0.1", "docs": "/docs"}


# Monter les fichiers statiques (si besoin d'autres assets plus tard)
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
