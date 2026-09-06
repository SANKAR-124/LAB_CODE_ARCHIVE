# LabVault — Lab Exam Prep Website — Backend Build Documentation (V1)

> "LabVault" is a working title used throughout this doc so tables/routes/scripts have a consistent name to refer to. Rename it freely (find-and-replace) — it has zero effect on the architecture.

Reference document for building the FastAPI backend end-to-end, stage by stage. Follow the stages in section 8 in order — each one assumes the previous is done. Table names, column names, and route paths in this document are final for V1; don't rename mid-build unless a stage tells you to. No application code is included anywhere in this doc on purpose — this is a spec and a checklist, not a tutorial; you write every line yourself as you go through each stage.

---

## 1. Project overview

LabVault is a website where lab experiments (code + explanation) for any subject that involves coding are stored in one place, so students can pull up a clean reference while studying for lab exams instead of digging through WhatsApp groups and half-broken PDFs.

**Primary motives for building it (yours):**
1. Get real, practical experience with FastAPI beyond tutorials — this is your second FastAPI project, and this one has actual auth/permission logic, not just CRUD.
2. Genuinely help yourself and other students study for lab exams by having every experiment for every subject in one browsable, searchable place.

**Who uses it:**
- **Students (public visitors)** — the actual audience. No login. They browse subjects, open an experiment, read the code + explanation side by side, and download the code file if they want it locally.
- **Contributor admins** — you and other students who want to upload lab content. Each gets their own login. They can add new subjects/experiments and upload content, but can only edit or delete content *they personally created*.
- **Super admin (you)** — full access to everything, plus the only role that can create contributor accounts and reset their passwords.

**Core browsing flow:**
```
Home (subject list, filterable) → Subject page (list of experiments) → Experiment page (code | description) → Download
```

---

## 2. Feature list (V1)

- Browse subjects filtered by **class/year (1–4)**, **department**, and **syllabus scheme** — scheme is a real filter, not just a label, since the same subject name can have different experiments across syllabus revisions (e.g. a 2019 scheme vs a 2024 scheme).
- Each subject shows its list of experiments (number + name).
- Each experiment has a **two-pane view**: code on one side, description (including any line-by-line explanation the admin chose to write) on the other.
- A **language field** per experiment (Python / C / C++ / Java / SQL / JavaScript / R / MATLAB / Other), used both to syntax-highlight the code on the frontend and to pick the correct file extension for downloads.
- A **download button** that generates the code file on the fly (no files sit on disk or in cloud storage — the code lives in the database as text and is streamed out as a file at request time).
- An optional **viva questions** field per experiment — cheap to add, high value for exam prep.
- **`created_by` and `updated_at`** shown on the experiment page, so students can see who contributed it and how fresh it is.
- Three-tier access: public read-only browsing, contributor admins with ownership-scoped write access, and a super admin with full access.
- Contributors get **individual accounts** (created by the super admin, not self-registered) so ownership can actually be tracked per person — this is what makes "you can't delete someone else's upload" technically possible.
- Super admin can **reset** (not view) any contributor's password if they forget it.

**Deliberately excluded from V1** (matches your original scope — don't add these without a reason): comments, ratings/likes, student accounts, real-time features, file/image uploads, structured line-by-line code annotations (free-text explanation is used instead — see section 6).

---

## 3. Roles & permissions

Three tiers, two of which require login:

| Role | Login required | Can do |
|---|---|---|
| Public visitor | No | Browse all subjects/experiments, download code |
| Contributor admin | Yes (own account) | Create subjects/experiments; edit/delete **only what they created** |
| Super admin | Yes (your account) | Everything a contributor can do, on **any** resource, plus create contributor accounts and reset their passwords |

The entire write-permission system reduces to one rule, checked on every `PUT`/`DELETE`:

```
can_modify(resource, current_user) =
    current_user.role == "super_admin"
    OR resource.created_by == current_user.id
```

Two things worth being explicit about, since they're easy to get wrong once you're mid-build:

- **Creating** a subject or experiment only requires being logged in as *any* admin (contributor or super) — it does not require ownership of anything, since ownership doesn't exist yet for something that's being created. Ownership is assigned automatically at creation time (`created_by = current_user.id`).
- A contributor **can** add a new experiment under a subject that someone else created (that's the collaborative point — most subjects will already exist, and people are filling in missing experiments). The ownership check only applies when *editing or deleting* — and it applies at the level of the specific row being touched (a specific subject or a specific experiment), not at the level of "who owns the subject this experiment lives under."

---

## 4. Tech stack (locked)

| Layer | Choice |
|---|---|
| Framework | FastAPI |
| Database | MySQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Admin UI | REST API (JSON responses) — admin panel consumes the same API |
| Media storage | None needed — code is stored as text in MySQL, downloads are generated on the fly |
| Auth | Session-based (signed cookie via `itsdangerous`), multiple users, two roles |

---

## 5. Folder structure

```
labvault-backend/
├── main.py                          # FastAPI app instance, includes app_router, CORS setup
│
├── app/
│   ├── core/
│   │   ├── config.py                # loads .env, exposes settings
│   │   ├── security.py              # password hashing, session token sign/verify
│   │   └── dependencies.py          # get_current_user(), require_super_admin()
│   │
│   ├── db/
│   │   ├── database.py              # engine
│   │   └── session.py               # SessionLocal, Base, get_db()
│   │
│   ├── models/                      # SQLAlchemy ORM models (one file per table)
│   │   ├── __init__.py              # imports all models so Alembic can discover them
│   │   ├── user.py
│   │   ├── subject.py
│   │   └── experiment.py
│   │
│   ├── schemas/                     # Pydantic request/response models
│   │   ├── auth_schema.py           # loginRequest
│   │   ├── user_schema.py           # userCreateRequest, userResponse, resetPasswordRequest
│   │   ├── subject_schema.py        # subjectCreateRequest, subjectUpdateRequest, subjectResponse
│   │   └── experiment_schema.py     # experimentCreateRequest, experimentUpdateRequest, experimentResponse
│   │
│   ├── controllers/                 # route handlers, split public vs admin
│   │   ├── public/
│   │   │   ├── subject_controller.py
│   │   │   └── experiment_controller.py
│   │   └── admin/
│   │       ├── auth_controller.py
│   │       ├── user_admin_controller.py       # super-admin only: create/list users, reset password
│   │       ├── subject_admin_controller.py
│   │       └── experiment_admin_controller.py
│   │
│   ├── routes/                      # APIRouter definitions, mounted in __init__.py
│   │   ├── __init__.py              # app_router, includes all sub-routers
│   │   ├── auth_route.py            # POST /admin/login, POST /admin/logout, GET /admin/me
│   │   ├── user_admin_route.py      # /admin/users...
│   │   ├── subject_route.py         # public + admin subject routes
│   │   └── experiment_route.py      # public + admin experiment routes, download route
│   │
│   ├── services/                    # business logic, called by controllers
│   │   ├── user_service.py
│   │   ├── subject_service.py
│   │   ├── experiment_service.py
│   │   ├── permission_service.py    # can_modify() logic
│   │   └── file_service.py          # language → file extension map + download response builder
│   │
│   └── scripts/
│       └── seed_super_admin.py      # one-off script to seed the first super admin
│
├── alembic/
│   ├── versions/
│   └── env.py
│
├── .env
├── .gitignore
├── alembic.ini
├── requirements.txt
└── README.md
```

---

## 6. Database schema

Naming: tables plural snake_case, columns snake_case, every table gets `id INT PK AUTO_INCREMENT`.

### `users`
One table for both roles — `role` decides what a user *can generally do*; `created_by` columns elsewhere decide what a *specific* user can touch.
| Column | Type | Notes |
|---|---|---|
| id | INT | PK |
| username | VARCHAR(100) | UNIQUE, NOT NULL |
| email | VARCHAR(255) | UNIQUE, NOT NULL |
| password_hash | VARCHAR(255) | NOT NULL — never store a raw password anywhere |
| role | ENUM('super_admin', 'contributor_admin') | NOT NULL |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |

### `subjects`
| Column | Type | Notes |
|---|---|---|
| id | INT | PK |
| name | VARCHAR(255) | NOT NULL |
| class_year | TINYINT | NOT NULL — valid range 1–4, enforced at the API layer (Pydantic), not as a DB constraint, so the range is easy to extend later without a migration |
| department | VARCHAR(150) | NOT NULL — free text, not an ENUM, since department names vary across colleges and shouldn't need a migration to add one |
| syllabus_scheme | VARCHAR(100) | NOT NULL — free text, e.g. `"KTU 2019"`, `"KTU 2024"` |
| created_by | INT | FK → users.id |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| updated_at | DATETIME | ON UPDATE CURRENT_TIMESTAMP |

Add a composite index on `(class_year, department, syllabus_scheme)` — this is exactly the combination the public filter UI queries against, so it's worth indexing from day one rather than retrofitting it once the table has real data.

### `experiments`
Code and its explanation are **not** split into a separate table — an experiment always has exactly one code block and one explanation, so splitting them would only add a join for zero benefit.
| Column | Type | Notes |
|---|---|---|
| id | INT | PK |
| subject_id | INT | FK → subjects.id, ON DELETE CASCADE |
| experiment_number | INT | NOT NULL |
| experiment_name | VARCHAR(255) | NOT NULL |
| language | ENUM('python','c','cpp','java','sql','javascript','r','matlab','other') | NOT NULL — see note below |
| code_content | LONGTEXT | NOT NULL — the raw code, pasted in by the admin |
| description | TEXT | NOT NULL — free-text/markdown; the admin pastes in the description **and** any line-by-line explanation here as one block, generated however they like (including AI-assisted). No structured line-number mapping in V1 — keeping it as one text field avoids the complexity of keeping line numbers in sync every time code is edited. |
| viva_questions | TEXT | nullable — optional, but genuinely one of the most-used things before a lab exam |
| created_by | INT | FK → users.id |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP |
| updated_at | DATETIME | ON UPDATE CURRENT_TIMESTAMP |

Add an index on `subject_id` (every "list experiments for this subject" query filters on it).

**On the `language` ENUM:** the list above is a sensible starting set for a typical AI&ML lab curriculum (Python, C, C++, Java, SQL, JavaScript, R, MATLAB) plus a catch-all `other`. It's a fixed dropdown on the frontend, not free text — this is what makes "admin enters a wrong/unknown language" structurally impossible; they can only pick from what's in the ENUM. If your actual lab subjects need a language not listed, add it to the ENUM before Stage 3 (migrations) — changing an ENUM after real data exists means an Alembic migration, so get this list right early if you can.

---

## 7. Environment variables (`.env`)

```
DATABASE_URL=mysql+pymysql://user:password@host:3306/dbname
SECRET_KEY=change-this-to-a-random-string
SUPER_ADMIN_SEED_USERNAME=
SUPER_ADMIN_SEED_EMAIL=
SUPER_ADMIN_SEED_PASSWORD=
```

`SUPER_ADMIN_SEED_*` are only used once, by a seed script, to create the very first row in `users` (with `role = super_admin`). Every contributor account after that is created through the API by the super admin — never through this script.

---

## 8. Build sequence

### Stage 0 — Project skeleton
a. Create and activate a virtual environment.
b. Install: `fastapi`, `uvicorn`, `sqlalchemy`, `pymysql`, `alembic`, `python-dotenv`, `pydantic-settings`, `email-validator`, `passlib[bcrypt]`, `itsdangerous`. (Note: no `python-multipart` needed — unlike a typical CRUD app, V1 has no file/image uploads at all, since code is pasted as text.)
c. Create the full folder structure from section 5 now, even the empty files — it's easier to see what's missing as you go than to create files ad hoc mid-stage.
d. Write a bare `main.py`: just the FastAPI app instance and one `GET /health` route returning `{"status": "ok"}`.
e. Add `CORSMiddleware` in `main.py` now, even though the frontend doesn't exist yet — since the frontend will be a separate app on a different origin, it needs `allow_credentials=True` and the frontend's exact origin listed (never `"*"` — wildcard origins silently break credentialed/cookie requests). Use `http://localhost:5173` (or whatever port your frontend tooling defaults to) for local dev.
f. Run `uvicorn main:app --reload` and confirm `http://localhost:8000/health` responds. Don't touch the database until this works — a broken server is much easier to debug with nothing else built on top of it.
g. Initialize git, add a `.gitignore` (make sure `.env` and `__pycache__/` are in it from the very first commit, not added later).

### Stage 1 — Config and DB connection
a. Write `core/config.py`: a `Settings` class (via `pydantic-settings`) that loads every variable from section 7 out of `.env`.
b. Write `db/database.py`: create the SQLAlchemy engine from `settings.DATABASE_URL`.
c. Write `db/session.py`: `SessionLocal` (sessionmaker bound to the engine), a declarative `Base`, and a `get_db()` generator dependency (open a session, yield it, close it in a `finally`).
d. Confirm the connection works before writing any models — either a tiny standalone script that calls `engine.connect()`, or just wait for Stage 3's migration to prove it; either is fine, but don't skip verifying this.

### Stage 2 — Models
a. Write `models/user.py` — matches the `users` schema exactly, including the `role` as a SQLAlchemy `Enum`.
b. Write `models/subject.py` — matches `subjects` exactly, with the FK to `users.id` and the composite index from section 6.
c. Write `models/experiment.py` — matches `experiments` exactly, with the FK to `subjects.id` (`ondelete="CASCADE"`), the `language` Enum, and the index on `subject_id`.
d. Import all three models into `models/__init__.py` so Alembic's autogenerate can discover them via `Base.metadata`.
e. Re-read section 6 side by side with what you wrote — column names, types, and nullability need to match exactly, since fixing a mismatch after real data exists means a migration instead of a one-line edit.

### Stage 3 — Migrations
a. `alembic init alembic`.
b. In `alembic/env.py`, point `target_metadata` at your `Base.metadata`, and pull the DB URL from `settings.DATABASE_URL` instead of hardcoding it in `alembic.ini`.
c. Generate the first migration: `alembic revision --autogenerate -m "create initial tables"`.
d. **Open the generated migration file and actually read it** before running it — MySQL's handling of `ENUM` columns via Alembic autogenerate is occasionally imperfect (autogenerate can miss ENUM value changes on later migrations), so it's worth knowing what the file actually contains from the start.
e. `alembic upgrade head`.
f. Connect to MySQL directly (CLI or a GUI client) and confirm all three tables exist with the right columns. From this point on, every schema change goes through a new migration — never a manual `ALTER TABLE`.

### Stage 4 — Super admin seed
a. Write `scripts/seed_super_admin.py`: reads `SUPER_ADMIN_SEED_USERNAME` / `_EMAIL` / `_PASSWORD` from settings, hashes the password, inserts one row into `users` with `role = "super_admin"`.
b. Add a guard so running it twice doesn't create duplicate rows (check if a user with that username already exists first, skip if so).
c. Run it once: `python -m app.scripts.seed_super_admin`.
d. Confirm the row exists in `users` with a properly hashed (not plaintext) password.

### Stage 5 — Auth
a. Write `core/security.py`: `hash_password` / `verify_password` (bcrypt via `passlib`), and `generate_session_token` / `verify_session_token` using `itsdangerous`'s `URLSafeSerializer` — the token payload only needs to hold the user's `id` (not their role — see substep d below for why).
b. Write `core/dependencies.py` with `get_current_user()`: reads the session cookie, verifies its signature, looks the user up in the DB by the `id` in the payload, and returns the user object. If the cookie is missing, invalid, or the user no longer exists, raise `HTTPException(401)` — **not** a redirect. (This is a deliberate difference from a server-rendered app: since the admin frontend here is a fully decoupled SPA calling a JSON API, the frontend — not FastAPI — is responsible for redirecting to a login screen when it receives a 401.)
c. Also in `dependencies.py`, write `require_super_admin()`: calls `get_current_user()`, then raises `HTTPException(403)` if `role != "super_admin"`.
d. Fetching the user fresh from the DB on every request (rather than trusting a role baked into the token) means a role change or account issue takes effect immediately instead of only after the token expires — a small extra DB lookup that's worth it for a system with an actual permission hierarchy.
e. Write `controllers/admin/auth_controller.py`: a login function (verify credentials against `users`, set the signed cookie) and a logout function (clear the cookie). Also add a simple "who am I" endpoint here — it returns the current user's `username` and `role` and is what the frontend calls on load to decide whether to show the login screen and whether to show super-admin-only UI.
f. Wire these to `routes/auth_route.py`: `POST /admin/login`, `POST /admin/logout`, `GET /admin/me`.
g. Cookie settings: `samesite="lax"`, `secure=False` for local dev over `http://localhost`; in production, since the frontend and API run on different origins, switch to `samesite="none"`, `secure=True` (browsers silently drop the cookie otherwise).
h. Test in Swagger UI (`/docs`): log in, confirm the cookie is set and sent back automatically on the next request, confirm `/admin/me` reflects the logged-in user, confirm logout clears it.

### Stage 6 — Permission logic
a. Write `services/permission_service.py` with one function implementing the rule from section 3: given a resource (something with a `.created_by` attribute) and the current user, return `True`/`False`.
b. This is deliberately **not** a FastAPI `Depends()` — ownership can't be checked until the specific row has been fetched from the DB (you need the row to know who created it), and the row can't be fetched until the path parameter (e.g. `experiment_id`) has been resolved. The natural place to call this is inside each admin controller function, right after fetching the row and right before applying the update/delete: fetch → check `can_modify()` → raise `HTTPException(403)` if false → proceed.
c. Keep this function tiny and reused everywhere — every ownership check in the whole app (subjects and experiments both) should call this same function, not duplicate the `role == "super_admin" or ...` logic inline in each controller.

### Stage 7 — Admin: user management (super-admin only)
a. Schemas: `UserCreateRequest` (username, email, password, role fixed to `contributor_admin` — the super admin can't create another super admin through this endpoint), `UserResponse` (id, username, email, role, created_at — **never** include `password_hash`), `ResetPasswordRequest` (new_password).
b. Service (`user_service.py`): `create_contributor()` (hash password, insert), `list_users()`, `reset_password(user_id, new_password)` (hash the new password, overwrite `password_hash` — this is the entire "forgot password" flow; there is no "view password" feature, and there shouldn't be).
c. Controller (`user_admin_controller.py`): all three functions, every one behind `Depends(require_super_admin)`.
d. Routes (`user_admin_route.py`): `POST /admin/users`, `GET /admin/users`, `PUT /admin/users/{user_id}/reset-password`.
e. Test: as the super admin, create a contributor account, log out, log in as that contributor, confirm it works and confirm `/admin/me` correctly reports `role: contributor_admin`.

### Stage 8 — Admin: Subjects CRUD
a. Schemas: `SubjectCreateRequest`, `SubjectUpdateRequest`, `SubjectResponse` (include `created_by` — ideally the *username*, not just the raw id, which means a join or a second lookup in the service layer).
b. Service (`subject_service.py`): `create_subject()` (sets `created_by = current_user.id` automatically — never accept this from the request body), `update_subject()`, `delete_subject()`, `get_subject()`.
c. Controller (`subject_admin_controller.py`): create requires only `Depends(get_current_user)` (any logged-in admin, per section 3). Update and delete fetch the subject first, then call `permission_service.can_modify()` before proceeding.
d. Routes: `POST /admin/subjects`, `PUT /admin/subjects/{subject_id}`, `DELETE /admin/subjects/{subject_id}`.
e. Test as both roles: confirm a contributor can create a subject, can edit/delete their own, and gets a 403 trying to edit/delete another contributor's subject. Confirm the super admin can edit/delete anything.

### Stage 9 — Admin: Experiments CRUD
a. Schemas: `ExperimentCreateRequest`, `ExperimentUpdateRequest`, `ExperimentResponse` (include `created_by` username and `updated_at`, per the locked feature list).
b. Service (`experiment_service.py`): same shape as subjects — `create_experiment()`, `update_experiment()`, `delete_experiment()`, `get_experiment()`.
c. Controller (`experiment_admin_controller.py`): create requires only `Depends(get_current_user)` and a valid `subject_id` — **not** ownership of that subject (per section 3, any admin can add an experiment to any existing subject). Update and delete are ownership-checked exactly like subjects, but against the *experiment's own* `created_by`, not the parent subject's.
d. Routes: `POST /admin/subjects/{subject_id}/experiments`, `PUT /admin/experiments/{experiment_id}`, `DELETE /admin/experiments/{experiment_id}`.
e. Test: confirm contributor B can add an experiment under a subject contributor A created, confirm B can edit/delete *that experiment* but not one of A's, confirm deleting a subject cascades and removes its experiments (including experiments other contributors added to it — this is an accepted V1 trade-off, noted again at the end of this doc).

### Stage 10 — Public API
a. Now that real data exists (create a few real or test rows through the admin routes you just built), write the read-only public endpoints.
b. Schemas: lightweight response models distinct from the admin ones — e.g. the subject list view only needs `id, name, class_year, department, syllabus_scheme`, not every column.
c. Service functions: `list_subjects()` accepting optional `class_year`, `department`, `syllabus_scheme` query filters (combinable — a student should be able to filter by all three at once); `list_experiments_by_subject()` (returns just number + name, matching the "click a subject, see a list of experiment names" flow); `get_experiment_detail()` (returns everything — code, description, viva_questions, language, created_by username, updated_at).
d. Controllers (`controllers/public/`): thin — just call the service and return the response schema, no auth dependency anywhere in this file.
e. Routes: `GET /subjects`, `GET /subjects/{subject_id}`, `GET /subjects/{subject_id}/experiments`, `GET /experiments/{experiment_id}`.
f. Test every filter combination (single filter, two filters, all three, no filters) and confirm none of these routes require the session cookie.

### Stage 11 — Code download endpoint
a. Write `services/file_service.py` with a hardcoded dict mapping each `language` ENUM value to a file extension (`python → .py`, `c → .c`, `cpp → .cpp`, `java → .java`, `sql → .sql`, `javascript → .js`, `r → .R`, `matlab → .m`, `other → .txt`). This is a plain Python dict, not a database table — it never changes at runtime, so there's no reason to make it editable through the admin panel.
b. Same file: a function that takes an experiment, looks up its extension, builds a safe filename (e.g. slugify the experiment name, prefix with the experiment number), and returns a `Response` with `code_content` as the body, the right `media_type` (`text/plain` is a safe universal choice regardless of language), and a `Content-Disposition: attachment; filename=...` header.
c. If a `language` value somehow isn't in the map (only possible if you add a new ENUM value later and forget to update this dict), fall back to `.txt` rather than raising an error — a download should never break; worst case is a `.txt` file with perfectly correct code inside it.
d. Route: `GET /experiments/{experiment_id}/download` — public, no auth.
e. Test downloading experiments in a few different languages and confirm the file opens with the correct extension and content; test the fallback path deliberately if you can (e.g. temporarily add an ENUM value without a matching dict entry, confirm you get a `.txt` instead of a 500 error, then revert).

### Stage 12 — Manual verification
a. Walk every route in section 9 using FastAPI's `/docs` (Swagger UI).
b. Re-test the three-role matrix end to end: visitor (no login) can read everything and download, cannot reach any `/admin/*` route; contributor can create anything, edit/delete only their own; super admin can edit/delete anything.
c. Confirm cascade delete: deleting a subject removes all its experiments.
d. Confirm the password-reset flow: super admin resets a contributor's password, the contributor's old password stops working, the new one logs them in.
e. Confirm CORS actually works from a real second origin, not just from Swagger UI on the same origin as the API (Swagger UI can mask CORS issues since it's served by FastAPI itself).

### Stage 13 — Deployment prep
a. Freeze dependencies: `pip freeze > requirements.txt`.
b. Double-check `.env` is gitignored and was never committed (check `git log` for it if you're not sure).
c. Pick a host — since this needs both a Python process and a persistent MySQL database, something like Railway or Render (with a managed MySQL add-on, or PlanetScale/Aiven's free MySQL tiers) is a reasonable fit for a student project budget.
d. Run the Alembic migrations against the production database (`alembic upgrade head`, pointed at the prod `DATABASE_URL`).
e. Set the real environment variables on the host.
f. Run `seed_super_admin.py` **once**, against production, to create your own login. Do not run it again after that, and do not use it to create contributor accounts — those go through `POST /admin/users` from here on.

---

## 9. API endpoint reference

### Public (JSON, no auth)

| Method | Path | Purpose |
|---|---|---|
| GET | `/subjects` | List subjects; optional query filters `class_year`, `department`, `syllabus_scheme` |
| GET | `/subjects/{subject_id}` | Subject detail |
| GET | `/subjects/{subject_id}/experiments` | List experiments for a subject (number + name) |
| GET | `/experiments/{experiment_id}` | Full experiment detail: code, description, viva_questions, language, created_by, updated_at |
| GET | `/experiments/{experiment_id}/download` | Streams the code as a downloadable file with the correct extension |

### Admin (JSON REST API, session-protected except login)

All admin endpoints except login require the session cookie set by `POST /admin/login`. Endpoints marked **(super admin only)** additionally require `role == "super_admin"`. All other admin endpoints allow both roles, with ownership enforced on update/delete per section 3.

| Method | Path | Purpose |
|---|---|---|
| POST | `/admin/login` | Verifies credentials, sets session cookie |
| POST | `/admin/logout` | Clears session cookie |
| GET | `/admin/me` | Returns the logged-in user's username + role (used by the frontend route guard) |
| POST | `/admin/users` | **(super admin only)** Create a contributor account |
| GET | `/admin/users` | **(super admin only)** List all users (no passwords) |
| PUT | `/admin/users/{user_id}/reset-password` | **(super admin only)** Set a new password for a contributor |
| POST | `/admin/subjects` | Create a subject (any logged-in admin) |
| PUT | `/admin/subjects/{subject_id}` | Update a subject (owner or super admin) |
| DELETE | `/admin/subjects/{subject_id}` | Delete a subject, cascades its experiments (owner or super admin) |
| POST | `/admin/subjects/{subject_id}/experiments` | Add an experiment to any existing subject (any logged-in admin) |
| PUT | `/admin/experiments/{experiment_id}` | Update an experiment (owner or super admin) |
| DELETE | `/admin/experiments/{experiment_id}` | Delete an experiment (owner or super admin) |

---

## 10. Frontend — prompts

You're building the frontend with AI coding agents rather than by hand, so no step-by-step here — just the two prompts, ready to paste in as-is. There are two because they're genuinely different projects: the public site is what students actually use to study, and the admin dashboard is the tool you and contributors use to manage content.

### 10.1 Public study site — prompt

```
Build a permanent public-facing frontend for a college lab-exam study
website called LabVault. Students use this to browse lab experiments
(code + explanation) while studying — treat readability and speed of
finding an experiment as the top priorities.

STACK
React (functional components, hooks), React Router, plain CSS or CSS
modules. All data comes from a FastAPI backend at http://localhost:8000
(configurable via an environment variable, e.g. VITE_API_BASE_URL). No
authentication anywhere in this app — every endpoint it calls is public.

DATA (read-only JSON endpoints)
- GET /subjects?class_year=&department=&syllabus_scheme=
    -> list: id, name, class_year, department, syllabus_scheme
- GET /subjects/{id}/experiments -> list: id, experiment_number, experiment_name
- GET /experiments/{id} -> detail: experiment_number, experiment_name,
    language, code_content, description, viva_questions (nullable),
    created_by (username), updated_at
- GET /experiments/{id}/download -> triggers a file download

VISUAL STYLE
Clean and light overall (this needs to be easy to read for long study
sessions), but give the code panel on the experiment page its own dark
"code editor" background (something like #1E1E2E) so code is visually
distinct from the explanation text next to it — this should feel like a
real code reference tool, not a generic content site.
- Primary accent: indigo, around #101b2aff
- Page background: white / very light gray, around #FAFAFA
- Code panel background: dark, around #1E1E2E, with light monospace text
- Text (outside the code panel): dark slate, around #1F2937
- Rounded corners (8px), generous spacing, a monospace font
  (e.g. "Fira Code" or "JetBrains Mono") anywhere code appears

PAGES

1. Home / Subject browser
   - Filter controls at the top: dropdowns for class/year (1st–4th),
     department, and syllabus scheme (populate department and scheme
     options dynamically from whatever the API returns, don't hardcode
     them), all combinable
   - Grid or list of subject cards below: name, year, department, scheme
   - Clicking a card navigates to that subject's experiment list
   - Empty state: "No subjects match these filters" if filtering returns
     nothing

2. Subject page
   - Subject name/details as a header
   - A simple numbered list of experiments (number + name) fetched from
     /subjects/{id}/experiments
   - Clicking an experiment navigates to its detail page

3. Experiment page (the core screen)
   - Two-column layout on desktop (stacks vertically on mobile): code
     panel on one side (with syntax highlighting based on the `language`
     field — use a library like Prism.js or highlight.js), description
     panel on the other, rendered as markdown
   - Below or within the description panel, a "Viva Questions" section
     if viva_questions is present, hidden entirely if it's null
   - A "Download Code" button that links directly to
     /experiments/{id}/download
   - Small metadata line: "Added by {created_by} · updated {updated_at,
     formatted as a relative or short date}"

GENERAL UX
- Loading states for every fetch (skeleton or spinner, not a blank page)
- Friendly empty states, not blank sections
- Handle a slow/failed API gracefully (a visible error state, not a
  silent blank screen)
- Responsive down to a phone-sized screen, since students will check
  this on their phones before a lab exam

Organize code into components/, pages/, and api/ (fetch wrapper
functions per resource).
```

### 10.2 Admin dashboard — prompt

```
Build a permanent admin dashboard frontend for LabVault, a college
lab-exam study website. This is a long-term tool used by a super admin
and several contributor admins to manage subjects and experiments —
invest in clean componentization and good UX, not a throwaway scaffold.

STACK
React (functional components, hooks), React Router, plain CSS or CSS
modules. All data comes from a FastAPI backend at http://localhost:8000
(configurable via an environment variable, e.g. VITE_API_BASE_URL).

AUTH
- Session-based via an httpOnly cookie set by the backend — the frontend
  never touches the token directly.
- Every fetch call to the backend must include `credentials: 'include'`.
- POST /admin/login with { username, password } logs in.
- POST /admin/logout logs out.
- On app load and after login, call GET /admin/me to get the current
  user's username and role ("super_admin" or "contributor_admin") and
  store it in context — this drives which nav items and action buttons
  are shown.
- On any 401 response from a protected endpoint, redirect to /login.
- Wrap all routes except /login in a route guard based on the /admin/me
  check.

ROLE-AWARE UI (important — this is not optional styling, it changes
what's rendered)
- Every subject/experiment list item should compare its `created_by`
  username against the logged-in user: if the logged-in user is the
  creator, OR the logged-in user's role is "super_admin", show Edit and
  Delete buttons on that item. Otherwise, hide them (don't just disable
  them — hide them, since a contributor has no reason to see controls
  they can never use on someone else's content).
- The "Manage Contributors" nav item and page (described below) should
  only appear at all if role === "super_admin". A contributor logging in
  should never see it exists.

VISUAL STYLE — indigo + slate, clean and professional
- Primary accent (buttons, active nav, links): indigo, around #4F46E5
- Secondary accent (badges, hover states): soft violet, around #818CF8
- Page background: very light gray, around #F9FAFB
- Card/panel background: white, soft shadow, rounded corners (8-10px)
- Text: dark slate, around #1F2937, not pure black
- Monospace font for the code textarea specifically (e.g. "Fira Code")
  so pasted code is easy to read while editing

LAYOUT
- Left sidebar (collapsible on smaller screens): Dashboard, Subjects,
  Manage Contributors (super admin only), with active-state highlighting
- Top bar: page title on the left, logged-in username + role badge +
  logout button on the right

PAGES

1. Login
   - Centered card, username + password, inline error on failure
     (don't reveal whether the username or password was wrong)

2. Dashboard
   - Welcome message with the logged-in username
   - Count cards: total subjects, total experiments, and (super admin
     only) total contributor accounts

3. Subjects (GET/POST /admin/subjects, PUT/DELETE
   /admin/subjects/{id}, plus nested experiments)
   - List/table of subjects: name, year, department, scheme, created_by,
     edit/delete actions (role-aware per the rules above)
   - "Add subject" form: name, year (dropdown 1-4), department (text),
     syllabus scheme (text)
   - Clicking into a subject shows its experiments in a sub-list, each
     with number, name, language badge, created_by, updated_at, and
     role-aware edit/delete actions
   - "Add experiment" form (from within a subject's page): experiment
     number, experiment name, language (dropdown — python, c, cpp, java,
     sql, javascript, r, matlab, other), a large monospace textarea for
     the code, a textarea for the description (mention that markdown is
     supported), an optional textarea for viva questions
   - Edit reuses the same form, pre-filled, and additionally shows
     created_by and updated_at as read-only fields
   - Delete asks for confirmation before calling the DELETE endpoint,
     and for subjects specifically, the confirmation copy should warn
     that this also deletes every experiment under it

4. Manage Contributors (super admin only — GET/POST /admin/users, PUT
   /admin/users/{id}/reset-password)
   - Table of all users: username, email, role, created_at — never show
     a password field anywhere, there is no "view password" feature
   - "Add contributor" form: username, email, password (this is a
     temporary password the super admin sets and shares directly with
     the contributor — make this expectation clear in the form's helper
     text)
   - "Reset Password" button per row opens a small form with just a new
     password field — no old password required, since this is explicitly
     for the case where the contributor forgot theirs

GENERAL UX REQUIREMENTS
- Loading states for every fetch (skeleton or spinner, not a blank
  screen)
- Empty states with friendly copy ("No subjects yet — add the first
  one") instead of blank tables
- Success/error toast notifications after create/update/delete/reset
  actions
- Client-side validation on required fields before submitting, with
  inline error text, not browser alert() popups
- Confirm-before-delete on every destructive action

Organize code into components/, pages/, api/ (fetch wrapper functions
per resource), and a single theme/constants file holding the color
palette.
```

---

## Notes

- This document assumes the schema in section 6 is final for V1. If you need to change it later, update the schema table here first, then generate a new Alembic migration — don't edit old migrations.
- The `language` ENUM list in section 6 is a suggested starting set, not something you're locked into forever — just get it right *before* Stage 3, since changing it after real data exists is a migration instead of a one-line edit.
- Deleting a subject cascades and removes every experiment under it, including experiments other contributors added — this is an accepted V1 trade-off for keeping the permission model simple (no "can't delete a subject if others contributed to it" logic). Worth knowing about, not necessarily worth solving in V1.
- The `services/` layer is what future contributors (in the open-source sense — people sending you pull requests) should mostly be extending. New features should mean new service functions + new routes, not rewrites of existing ones.
- Section 10's prompts assume React, matching your existing MERN experience from the Skope Kitchens internship — swap the "STACK" line in either prompt if you'd rather use something else.
- Running two separate frontends (public site + admin dashboard) against one backend is exactly why CORS and cross-origin cookies are configured explicitly from Stage 0 onward — don't skip that step even though nothing depends on it yet at that point in the build.
