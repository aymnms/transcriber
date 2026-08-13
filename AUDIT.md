# Audit — transcriber

Date : 2026-08-14
Auteur : audit automatisé (Claude Code), lecture intégrale du dépôt à l'état du commit `0d42c35` (branche `main`).

---

## 2.1 Cartographie

**Stack technique réelle** (déterminée par lecture du code, pas par le README) :
- Langage : Python. Aucune version n'est pinnée nulle part (pas de `.python-version`, pas de `python_requires`). En pratique, `requirements.txt` pin `numpy==2.2.5`, qui **exige Python ≥ 3.10**. Le Python système disponible sur cette machine d'audit est 3.9.6 — donc même l'environnement de dev de référence n'est pas documenté/garanti. C'est une dette à part entière, indépendante du portage (voir §2.7 et §2.8).
- UI : **Tkinter** (bibliothèque standard Python), donc déjà cross-plateforme *en théorie* — mais avec une nuance Linux importante (§2.5).
- Moteur de transcription : [`faster-whisper`](https://github.com/SYSTRAN/faster-whisper) 1.1.1, basé sur `ctranslate2` 4.6.0.
- Gestionnaire de dépendances : `pip` + `requirements.txt` figé (pas de `pyproject.toml`, pas de lockfile de type `pip-tools`/`poetry`, pas de séparation dépendances runtime/dev).
- Packaging : **PyInstaller** 6.13.0, invoqué manuellement en CLI (pas de fichier `.spec` commité — il est généré à la volée et ignoré par `.gitignore`).

**Arborescence réelle du dépôt** (tout le code utile) :
```
app_whisper.py       # unique fichier source, 104 lignes — TOUT le programme
requirements.txt     # dépendances runtime figées
assets/               # logo.png, logo.ico, MyIcon.icns, screenshots, gif, 1 audio de test
README.md, LICENSE, MyIcon.icns (dupliqué à la racine), .gitignore
```
Il n'existe **aucun** dossier `src/`, `tests/`, `domain/`, `platform/`, ni fichier de config CI (`.github/workflows/` absent). Il n'y a pas de découpage en modules : `app_whisper.py` est un script unique.

**Découpage métier / intégration OS** : inexistant. Un seul fichier mélange :
- la construction de l'UI Tkinter (fenêtres, boutons, menus),
- l'orchestration métier (lancement du thread de transcription, appel à `faster_whisper`),
- l'I/O disque (écriture du `.txt` de sortie),
- l'état applicatif, porté par des **variables globales de module** (`selected_file`, `model_choice`, `file_label`, `model_menu`, `root`).

Cette absence totale de frontière est le blocage structurel n°1 pour tout portage propre ou tout test unitaire (rien n'est testable sans instancier un vrai `tk.Tk()`).

Une branche `origin/docker-version` existe (1 commit, `910885f feat: whisper with docker`), antérieure à la version Tkinter actuelle et jamais fusionnée dans `main` : une piste Docker a été explorée puis abandonnée au profit de l'app de bureau. Elle est morte et hors périmètre, mentionnée ici pour mémoire seulement.

---

## 2.2 Fonctionnement bout-en-bout

Contrairement à ce que le prompt de mission suppose, il n'y a **pas de capture audio en direct** — l'app est *file-based* uniquement :

1. **Sélection** : `browse_file()` ouvre un `filedialog.askopenfilename` filtré sur une longue liste d'extensions audio/vidéo (mp3, wav, m4a, ogg, flac, mp4, mkv, amr, dss, dvf, bmf, tta, tak, ape, alac, ra, rm, wma, opus, aac, pcm, raw, au, aiff).
2. **Prétraitement** : aucun, explicitement. Le décodage audio est délégué à `faster-whisper`, qui dépend du package `av` (PyAV). **PyAV embarque ses propres bibliothèques FFmpeg dans le wheel** (wheels manylinux/win/macos publiés sur PyPI) — il n'y a donc **pas de binaire `ffmpeg` système à installer séparément ni à embarquer** dans ce projet. C'est un point positif déjà acquis pour la portabilité.
3. **Appel au modèle** : `WhisperModel(model_choice)` où `model_choice ∈ {tiny, base, small, medium, large}`, choisi dans un `OptionMenu`. Aucun paramètre `device`/`compute_type` n'est passé explicitement → `ctranslate2` utilise sa valeur par défaut `device="auto"` (CUDA si disponible, sinon CPU). Voir §2.3 pour l'implication sur le portage.
4. **Chargement/cache du modèle** : `faster-whisper` télécharge les poids depuis le Hugging Face Hub au premier usage et les met en cache via `huggingface_hub`, qui résout lui-même un répertoire cache **déjà cross-plateforme** (`~/.cache/huggingface` sur macOS/Linux, `%USERPROFILE%\.cache\huggingface` sur Windows) — aucun chemin n'est hardcodé dans `app_whisper.py`. Rien à faire ici pour le portage.
5. **Post-traitement** : concaténation des segments (`"\n".join(seg.text for seg in segments)`) — trivial, pur, sans dépendance OS.
6. **Export** : écriture d'un fichier `<basename_sans_ext>_transcription.txt` **dans le même dossier que le fichier source**, en UTF-8. Aucune gestion d'erreur si ce dossier n'est pas accessible en écriture (volume réseau en lecture seule, permissions, etc.) — voir bug latent en §2.7.
7. **Affichage** : une fenêtre modale Tkinter de fin indique le chemin du fichier produit.

Toute l'orchestration (2–6) tourne dans un `threading.Thread` daemon pour ne pas geler l'UI — mécanisme déjà cross-plateforme.

---

## 2.3 Dépendances et accélération matérielle

**Bibliothèques tierces** (extrait de `requirements.txt`, 29 lignes) : `faster-whisper`, `ctranslate2`, `av` (PyAV), `numpy`, `onnxruntime`, `huggingface-hub`, `tokenizers`, `pyinstaller` + `pyinstaller-hooks-contrib`, et `macholib` — **spécifique au packaging macOS** (utilisé par PyInstaller pour analyser/relier des binaires Mach-O ; PyInstaller lui-même le déclare conditionnel à `sys_platform == "darwin"` dans ses propres dépendances, donc l'épingler ici sans condition est redondant et inutile sur Windows/Linux). `altgraph`, en revanche, est une dépendance **générique** de PyInstaller (graphe de dépendances de l'analyse de build), utilisée sur les trois OS — elle n'est pas à isoler. Aucun binaire n'est embarqué dans le dépôt lui-même (pas de `ffmpeg`, pas de `.dylib`/`.dll`/`.so` commités).

**Question tranchée — accélération matérielle macOS-only ?**
Réponse : **non, il n'y en a pas.** `ctranslate2` (le moteur d'inférence sous-jacent à `faster-whisper`) ne supporte que deux backends : **CPU** et **CUDA**. Il n'existe **aucun support Metal, CoreML ou MPS** dans `ctranslate2` — donc rien de tel n'est utilisé ici, ni directement, ni indirectement. Sur macOS aujourd'hui, l'app tourne donc déjà en **CPU pur** (aucun GPU Apple Silicon n'est exploité).

Conséquence directe pour le portage : comme le code ne fixe jamais `device=`, le comportement `device="auto"` de `ctranslate2` s'appliquera **identiquement** sur Windows et Linux — CPU par défaut, et **utilisation automatique d'un GPU NVIDIA/CUDA si l'utilisateur en a un et que la variante CUDA de `ctranslate2` est installée**, ce qui n'est même pas possible sur macOS aujourd'hui. **Aucun code de fallback à écrire** : le comportement voulu (CPU partout, CUDA en bonus si dispo) est déjà celui du code actuel, tel quel, sans modification. C'est un non-événement pour le portage, mais mérite d'être documenté explicitement pour ne pas être « réinventé ».

---

## 2.4 Spécificités macOS

- **Aucun appel à une API/framework macOS-only** dans `app_whisper.py` (pas d'import `AppKit`/`Cocoa`/`Foundation`, pas de binding natif).
- **Pas d'accès micro** (pas de capture live, cf. §2.2), donc **pas d'entrée TCC `NSMicrophoneUsageDescription`** à gérer, ni dans le code ni dans un `Info.plist` — il n'existe d'ailleurs aucun `Info.plist` custom dans le dépôt, PyInstaller en génère un minimal par défaut.
- **Chemins de fichiers** : construits via `os.path.splitext`/`os.path.basename`, déjà portables.
- **Variables d'environnement** : aucune n'est lue ni hardcodée dans le code.
- **Packaging actuel** :
  - `pyinstaller --windowed --onedir app_whisper.py --name "Transcriber (ARM)" --icon assets/MyIcon.icns` pour Apple Silicon natif.
  - `arch -x86_64 pyinstaller ... --name "Transcriber (Intel)" ...` pour Intel, avec un venv Intel séparé recréé sous Rosetta (procédure manuelle documentée dans le README, non scriptée, non automatisée).
  - **Pas de codesign, pas de notarization** — les utilisateurs macOS doivent probablement passer par Gatekeeper manuellement (clic droit → Ouvrir), non documenté dans le README.
  - **Pas de fichier `.spec` commité**, tout est en ligne de commande.
- Vérification faite sur les releases GitHub existantes (`aymnms/transcriber`, tag `v0.1.0`) : une seule release publiée, avec la note **« Windows version will coming soon »** — donc, contrairement à ce qu'affirme le README (« Download the latest version (.app / .exe) », voir §2.8 point 8), **aucune version Windows n'a jamais été distribuée à ce jour**. Le README est en avance sur la réalité du code.

---

## 2.5 Blocages précis par OS cible

### Windows
- Aucune instruction de build Windows dans le README (uniquement macOS ARM/Intel) — à écrire.
- `assets/logo.ico` **existe déjà** dans le dépôt, prêt à l'emploi pour `--icon` sous PyInstaller — signe qu'une tentative Windows a été commencée côté assets mais jamais finalisée côté script/doc/CI.
- `macholib` dans `requirements.txt` est un poids mort inutile sous Windows (installable mais sans fonction) — cosmétique, pas bloquant, mais à nettoyer (§2.8).
- Aucune release Windows n'a jamais été produite ni testée (confirmé par la page Releases, voir §2.4).
- Aucune CI n'a jamais validé quoi que ce soit sous Windows.

### Linux
- **Tkinter n'est pas installable via `pip`** sur Linux : il dépend du paquet système `python3-tk` (Debian/Ubuntu) ou équivalent (`tk` sous Fedora/Arch), absent de `requirements.txt` par nature (ce n'est pas un paquet pip) et **non documenté du tout** dans le README. C'est le blocage Linux le plus concret : sans ce paquet système, `import tkinter` échoue immédiatement à l'exécution.
- Aucun fichier `.desktop`, aucune icône Linux, aucun script de build, aucune piste d'empaquetage (AppImage/deb/autre) n'existe.
- Aucune release ni CI Linux n'a jamais existé.

### Les deux (Windows + Linux)
- **Zéro test automatisé** dans le dépôt (aucun fichier `test_*.py`/`*_test.py`, pas de `pytest` dans les dépendances) — refactorer pour séparer domaine/plateforme sans filet de sécurité serait risqué.
- **Aucune CI** (`.github/workflows/` absent) — rien n'a jamais été vérifié automatiquement, y compris sur macOS.
- Logique métier et code Tkinter/OS totalement entremêlés dans un seul fichier avec état global (§2.1) — bloque toute extraction propre tant que ce n'est pas corrigé.
- Version de Python non pinnée et incohérente avec l'environnement de dev réel disponible (§2.1, §2.7).

---

## 2.6 Format de distribution attendu

**Décision tranchée** : conserver **PyInstaller** comme outil de packaging unique pour les trois OS, en miroir exact de la pratique macOS actuelle (`--windowed --onedir`), plutôt que d'introduire un outil de build différent par plateforme. Justification : PyInstaller supporte nativement Windows et Linux, ne demande aucun changement d'outillage, et le dépôt contient déjà `assets/logo.ico` (Windows) — seul un icône/format Linux (`.png`, déjà présent via `assets/logo.png`) manque, ce qui est trivial.

Concrètement, pour le **MVP portable** (§3 du plan) :
- **Windows** : `pyinstaller --windowed --onedir app_whisper.py --name "Transcriber" --icon assets/logo.ico` → dossier `dist/Transcriber/` livré tel quel (zip), exactement comme le `.app` macOS aujourd'hui. Un installeur (Inno Setup, MSI) est un vrai plus mais **n'est pas requis pour l'équivalence fonctionnelle avec l'existant macOS**, qui lui-même ne fournit aucun installeur — juste un bundle zippé. Backlog post-MVP.
- **Linux** : `pyinstaller --windowed --onedir app_whisper.py --name "transcriber" --icon assets/logo.png` → dossier `dist/transcriber/` livré en tarball. **AppImage** est l'équivalent le plus proche d'un `.app` macOS (auto-suffisant, double-clic) et est documenté comme cible **backlog post-MVP** (§2.8 point 7) : il ajoute un vrai coût d'outillage (`appimagetool`, fichier `.desktop`, pas de mise à jour intégrée) qui ne doit pas bloquer le MVP. Un `.deb` est encore plus d'effort (dépendances système, maintenance d'un dépôt APT) et n'est pas retenu pour le MVP.

Ce choix garde une barre d'exigence **cohérente entre les trois OS** : aucun ne reçoit un packaging plus abouti que les autres au stade du MVP.

---

## 2.7 Qualité générale du code

- **Zéro test**, zéro CI, zéro linter configuré, zéro type hints, zéro docstring.
- **Bug latent indépendant du portage** : `transcribe_task()` (dans le thread daemon) n'a **aucun `try/except`**. Si la transcription échoue (fichier corrompu, dossier de sortie non accessible en écriture, modèle indisponible faute de réseau au premier téléchargement, etc.), l'exception se propage silencieusement dans le thread, **la fenêtre « transcription en cours » ne se ferme jamais**, et l'utilisateur n'a aucun retour d'erreur. Ce bug existe déjà sur macOS ; il devient plus visible en portant l'app sur des environnements avec plus de variance (permissions Windows, absence de réseau en CI Linux, etc.) — à corriger (§2.8 point 2), sans changer le comportement du chemin nominal.
- **État global mutable** (`selected_file`, `model_choice`, `file_label`, `model_menu`, `root`) au niveau du module — rend `run_transcription`/`browse_file`/`on_transcribe` impossibles à tester unitairement sans un vrai `tk.Tk()` monté.
- Pas de séparation dépendances runtime/dev (`requirements.txt` unique, pas de `requirements-dev.txt` ni de groupe `[dev]`).
- Incohérence d'environnement : `numpy==2.2.5` exige Python ≥ 3.10 mais aucune version de Python n'est documentée ni pinnée nulle part — un contributeur suivant le README à la lettre avec un Python système plus ancien (comme celui de cette machine d'audit, 3.9.6) échouera à l'installation.
- README en avance sur la réalité du produit livré (annonce un `.exe` téléchargeable en Release alors qu'aucun n'existe, cf. §2.4).

---

## 2.8 Critiques et recommandations priorisées

| # | Recommandation | Effort | Risque |
|---|---|---|---|
| 1 | Extraire les fonctions pures (`segments_to_text`, `output_path_for`, `is_supported_audio_extension`, `is_valid_model_name`) dans `domain/`, avec tests unitaires — prérequis à tout le reste, permet le TDD immédiat sans dépendre de `faster-whisper`/Tkinter. | Faible | Faible |
| 2 | Ajouter un `try/except` autour de `transcribe_task()` pour fermer proprement la fenêtre de chargement et informer l'utilisateur en cas d'erreur — bug latent déjà présent sur macOS, indépendant du portage mais à corriger tôt vu la variance d'environnements à venir. | Faible | Moyen (comportement actuel en cas d'erreur = blocage silencieux) |
| 3 | Nettoyer `requirements.txt` : isoler `macholib` (macOS-only) via un marqueur d'environnement (`; sys_platform == "darwin"`) plutôt que de l'installer partout inutilement. | Faible | Faible |
| 4 | Mettre en place `pytest` + une CI GitHub Actions en matrice (`macos-latest`, `windows-latest`, `ubuntu-latest`) **dès le premier jalon de portage**, avant d'écrire le moindre code spécifique Windows/Linux. | Moyen | Faible |
| 5 | Documenter (README + éventuel script de setup) la dépendance système `python3-tk` sous Linux — sans elle, l'app ne démarre pas du tout, et rien dans `pip install` ne le signale. | Moyen | Moyen (bloquant silencieux sur Linux) |
| 6 | Ajouter des commandes/scripts de build PyInstaller Windows et Linux, en miroir des commandes macOS existantes, en réutilisant `assets/logo.ico`/`assets/logo.png` déjà présents. | Moyen | Faible |
| 7 | Empaquetage AppImage pour Linux — backlog post-MVP, pas bloquant pour la parité fonctionnelle de base. | Élevé | Faible |
| 8 | Corriger le README, qui affirme qu'un `.exe` est déjà disponible en Release alors que la release existante (`v0.1.0`) indique explicitement « Windows version will coming soon » et ne contient aucun binaire Windows. | Faible | Faible |
| 9 | Pinner une version de Python explicite (ex. `>=3.10,<3.13`, cohérente avec `numpy==2.2.5`) et la documenter, pour éviter les échecs d'installation silencieux selon l'environnement du contributeur. | Faible | Faible |

---

## Addendum — dépendance rompue détectée par la CI (2026-08-14)

La toute première exécution de la CI multi-OS (J2) a échoué **identiquement sur Linux, Windows et macOS Apple Silicon** dès l'étape `pip install -r requirements-dev.txt`. Investigation : `av==14.3.0` (dépendance transitive de `faster-whisper`, utilisée pour le décodage audio, cf. §2.2) **n'a aucun fichier publié sur PyPI** (0 wheel, 0 sdist) — la version épinglée dans `requirements.txt` a été retirée de PyPI après que ce pin a été figé (`pip freeze`) à un moment où elle existait encore. Conséquence : **`pip install -r requirements.txt` échoue déjà aujourd'hui sur macOS aussi**, indépendamment de tout portage — ce n'est pas une régression introduite par ce travail, mais un cas de « dependency rot » préexistant que la CI vient de révéler pour la première fois, faute d'avoir jamais existé avant.

Correctif appliqué : `av==14.2.0` (version antérieure la plus proche disposant de wheels prébuilts complets pour cp39–cp313 sur `win_amd64`, `macosx_arm64`/`x86_64`, et `manylinux_x86_64`/`aarch64` — vérifié via l'API PyPI). Aucun changement de comportement attendu : PyAV n'est jamais appelé directement par le code applicatif, uniquement en interne par `faster-whisper` pour le décodage.

## Questions ouvertes (aucune bloquante à ce stade)

Les deux questions structurantes posées par le brief de mission (§2.3 accélération matérielle, §2.6 format de distribution) sont **tranchées ci-dessus**, directement déductibles du code et des dépendances — pas de remontée nécessaire.

Point de vigilance à signaler néanmoins : le README annonce publiquement un binaire Windows déjà disponible, ce qui est faux (voir §2.4, §2.8-8). Il sera corrigé dans le cadre du portage, mais je le signale explicitement car c'est une divergence entre la communication existante du projet et son état réel — à ne pas laisser sans correction.
