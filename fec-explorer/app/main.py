import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.fec_parser import parse_multiple_fec
from app.core.indicators import calculate_indicators

app = FastAPI(
    title="FEC Explorer API",
    description="Parse des fichiers FEC et calcule les indicateurs financiers par SIRET.",
    version="1.0.0",
)

# CORS — autorise le CRM (local ou distant) à appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # restreindre en production à l'URL du CRM
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ── Schémas ──────────────────────────────────────────────────────────────────

class FolderRequest(BaseModel):
    folder_path: str


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", summary="Sanity check")
def root():
    return {"message": "FEC Explorer API"}


@app.post("/api/fec/upload", summary="Parse un dossier FEC et retourne les indicateurs")
def upload_fec(body: FolderRequest):
    folder = body.folder_path

    if not os.path.isdir(folder):
        raise HTTPException(
            status_code=400,
            detail=f"Dossier introuvable ou inaccessible : {folder}",
        )

    rows = parse_multiple_fec(folder)

    if not rows:
        raise HTTPException(
            status_code=422,
            detail="Aucun fichier FEC valide trouvé dans ce dossier (pattern attendu : 9chiffres+FEC+8chiffres.txt).",
        )

    indicateurs = calculate_indicators(rows)

    return {
        "folder":      folder,
        "nb_entites":  len(indicateurs),
        "indicateurs": indicateurs,
    }
