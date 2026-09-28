# CalcNotes – Notes de calcul

Application web de notes de calcul (style SMath / Excel)  
Calcul numérique + symbolique + unités + classification.

## Déploiement en ligne (recommandé)

### Méthode la plus simple : Render.com (gratuit)

1. Crée un compte sur https://render.com
2. Clique sur **New → Web Service**
3. Connecte ton dépôt GitHub (ou uploade le code)
4. Configure :
   - **Root Directory** : `backend`
   - **Runtime** : Python 3
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Clique sur **Create Web Service**

Une fois déployé, tu obtiens une URL du type :  
`https://calcnotes-xxxx.onrender.com`

Tu peux y accéder depuis ton téléphone.

> Note : le plan gratuit de Render met l’application en veille après 15 min d’inactivité (premier chargement un peu long).

### Alternative : Railway.app

1. Va sur https://railway.app
2. New Project → Deploy from GitHub (ou dossier)
3. Sélectionne le dossier `backend`
4. Railway détecte le `Procfile` automatiquement

### Alternative : Docker

```bash
cd backend
docker build -t calcnotes .
docker run -p 8000:8000 calcnotes
```

## Lancement en local

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Ouvre ensuite : http://localhost:8000

## Fonctionnalités v0.1

- Notebook libre (cellules Texte + Calcul)
- Calcul numérique et symbolique (SymPy)
- Unités physiques (Pint) → `F = 150 * kN`
- Sauvegarde SQLite
- Catégories + tags + recherche
- Interface responsive (ordinateur + téléphone)

## Structure

```
calc-notes/
├── backend/               ← Application complète (API + frontend)
│   ├── main.py
│   ├── calculator.py
│   ├── static/index.html  ← Interface
│   ├── Dockerfile
│   └── Procfile
├── frontend/              ← Copie de développement
├── render.yaml
└── README.md
```

## Exemples d’expressions

```
2 + 2
x = 5
x**2 + 3*x
F = 150 * kN
A = 200 * mm**2
sigma = F / A
```
