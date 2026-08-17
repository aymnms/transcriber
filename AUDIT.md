# Audit — transcriber

> Dernière mise à jour : 2026-08-14
> Statut de l'audit : ✅ Terminé

Auteur : audit automatisé (Claude Code), lecture intégrale du dépôt à l'état du commit `0d42c35` (branche `main`), avant tout travail de portage.

## 0. Résumé exécutif

`transcriber` est une application desktop Tkinter de transcription audio→texte (via `faster-whisper`), fonctionnelle mais disponible uniquement sur macOS à ce stade. L'objectif de la mission est de la porter proprement vers Windows et Linux. Conclusions principales : le code métier et l'intégration OS/UI sont entièrement entremêlés dans un fichier unique, sans aucun test ni CI — c'est le blocage structurel n°1 à lever avant tout portage. Aucun obstacle technique réel n'empêche en revanche le portage lui-même (pas d'API macOS-only, pas d'accélération GPU spécifique à une plateforme). Les deux décisions structurantes de la mission (accélération matérielle, format de distribution) sont tranchées directement par cet audit, sans arbitrage utilisateur nécessaire.

## 1. Cartographie

**Stack technique réelle** (déterminée par lecture du code, pas par le README) :
- Langage : Python. Aucune version n'est pinnée nulle part (pas de `.python-version`, pas de `python_requires`). En pratique, `requirements.txt` pin `numpy==2.2.5`, qui **exige Python ≥ 3.10**. Le Python système disponible sur cette machine d'audit est 3.9.6 — donc même l'environnement de dev de référence n'est pas documenté/garanti. C'est une dette à part entière, indépendante du portage (voir §6 et §7).
- UI : **Tkinter** (bibliothèque standard Python), donc déjà cross-plateforme *en théorie* — mais avec une nuance Linux importante (§4).
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

## 2. Fonctionnement bout-en-bout

Contrairement à ce que le prompt de mission suppose, il n'y a **pas de capture audio en direct** — l'app est *file-based* uniquement :

1. **Sélection** : `browse_file()` ouvre un `filedialog.askopenfilename` filtré sur une longue liste d'extensions audio/vidéo (mp3, wav, m4a, ogg, flac, mp4, mkv, amr, dss, dvf, bmf, tta, tak, ape, alac, ra, rm, wma, opus, aac, pcm, raw, au, aiff).
2. **Prétraitement** : aucun, explicitement. Le décodage audio est délégué à `faster-whisper`, qui dépend du package `av` (PyAV). **PyAV embarque ses propres bibliothèques FFmpeg dans le wheel** (wheels manylinux/win/macos publiés sur PyPI) — il n'y a donc **pas de binaire `ffmpeg` système à installer séparément ni à embarquer** dans ce projet. C'est un point positif déjà acquis pour la portabilité.
3. **Appel au modèle** : `WhisperModel(model_choice)` où `model_choice ∈ {tiny, base, small, medium, large}`, choisi dans un `OptionMenu`. Aucun paramètre `device`/`compute_type` n'est passé explicitement → `ctranslate2` utilise sa valeur par défaut `device="auto"` (CUDA si disponible, sinon CPU). Voir §5 pour l'implication sur le portage.
4. **Chargement/cache du modèle** : `faster-whisper` télécharge les poids depuis le Hugging Face Hub au premier usage et les met en cache via `huggingface_hub`, qui résout lui-même un répertoire cache **déjà cross-plateforme** (`~/.cache/huggingface` sur macOS/Linux, `%USERPROFILE%\.cache\huggingface` sur Windows) — aucun chemin n'est hardcodé dans `app_whisper.py`. Rien à faire ici pour le portage.
5. **Post-traitement** : concaténation des segments (`"\n".join(seg.text for seg in segments)`) — trivial, pur, sans dépendance OS.
6. **Export** : écriture d'un fichier `<basename_sans_ext>_transcription.txt` **dans le même dossier que le fichier source**, en UTF-8. Aucune gestion d'erreur si ce dossier n'est pas accessible en écriture (volume réseau en lecture seule, permissions, etc.) — voir bug latent en §6.
7. **Affichage** : une fenêtre modale Tkinter de fin indique le chemin du fichier produit.

Toute l'orchestration (2–6) tourne dans un `threading.Thread` daemon pour ne pas geler l'UI — mécanisme déjà cross-plateforme.

## 3. Dépendances

- **Bibliothèques et frameworks tiers** (extrait de `requirements.txt`, 29 lignes) : `faster-whisper`, `ctranslate2`, `av` (PyAV), `numpy`, `onnxruntime`, `huggingface-hub`, `tokenizers`, `pyinstaller` + `pyinstaller-hooks-contrib`, et `macholib` — **spécifique au packaging macOS** (utilisé par PyInstaller pour analyser/relier des binaires Mach-O ; PyInstaller lui-même le déclare conditionnel à `sys_platform == "darwin"` dans ses propres dépendances, donc l'épingler ici sans condition est redondant et inutile sur Windows/Linux). `altgraph`, en revanche, est une dépendance **générique** de PyInstaller (graphe de dépendances de l'analyse de build), utilisée sur les trois OS — elle n'est pas à isoler.
- **Binaires/outils embarqués ou appelés en sous-processus** : aucun binaire n'est embarqué dans le dépôt lui-même (pas de `ffmpeg`, pas de `.dylib`/`.dll`/`.so` commités). PyAV embarque FFmpeg dans son propre wheel (§2, point 2).
- **Services externes** : Hugging Face Hub, pour le téléchargement et la mise en cache des poids du modèle Whisper au premier usage (via `huggingface_hub`, cf. §2 point 4). Aucun autre service réseau.
- **Éléments spécifiques à un environnement** : aucun appel à une API/framework macOS-only dans `app_whisper.py` (pas d'import `AppKit`/`Cocoa`/`Foundation`, pas de binding natif). Pas d'accès micro (pas de capture live, cf. §2), donc pas d'entrée TCC `NSMicrophoneUsageDescription` à gérer, ni dans le code ni dans un `Info.plist` — il n'existe d'ailleurs aucun `Info.plist` custom dans le dépôt, PyInstaller en génère un minimal par défaut. Chemins de fichiers construits via `os.path.splitext`/`os.path.basename`, déjà portables. Aucune variable d'environnement n'est lue ni hardcodée dans le code. Accélération matérielle : voir §5 (question tranchée par cet audit).

## 4. Contraintes et blocages vis-à-vis de l'objectif de la mission

**État macOS actuel** (référence pour le portage) :
- Packaging : `pyinstaller --windowed --onedir app_whisper.py --name "Transcriber (ARM)" --icon assets/MyIcon.icns` pour Apple Silicon natif ; `arch -x86_64 pyinstaller ...` pour Intel, avec un venv Intel séparé recréé sous Rosetta (procédure manuelle documentée dans le README, non scriptée, non automatisée).
- **Pas de codesign, pas de notarization** — les utilisateurs macOS doivent probablement passer par Gatekeeper manuellement (clic droit → Ouvrir), non documenté dans le README.
- **Pas de fichier `.spec` commité**, tout est en ligne de commande.
- Vérification faite sur les releases GitHub existantes (`aymnms/transcriber`, tag `v0.1.0`) : une seule release publiée, avec la note « Windows version will coming soon » — donc, contrairement à ce qu'affirme le README (« Download the latest version (.app / .exe) », voir §7 point 8), **aucune version Windows n'a jamais été distribuée à ce jour**. Le README est en avance sur la réalité du code.

**Windows** :
- Aucune instruction de build Windows dans le README (uniquement macOS ARM/Intel) — à écrire.
- `assets/logo.ico` **existe déjà** dans le dépôt, prêt à l'emploi pour `--icon` sous PyInstaller — signe qu'une tentative Windows a été commencée côté assets mais jamais finalisée côté script/doc/CI.
- `macholib` dans `requirements.txt` est un poids mort inutile sous Windows (installable mais sans fonction) — cosmétique, pas bloquant, mais à nettoyer (§7).
- Aucune release Windows n'a jamais été produite ni testée (confirmé par la page Releases, ci-dessus).
- Aucune CI n'a jamais validé quoi que ce soit sous Windows.

**Linux** :
- **Tkinter n'est pas installable via `pip`** sur Linux : il dépend du paquet système `python3-tk` (Debian/Ubuntu) ou équivalent (`tk` sous Fedora/Arch), absent de `requirements.txt` par nature (ce n'est pas un paquet pip) et **non documenté du tout** dans le README. C'est le blocage Linux le plus concret : sans ce paquet système, `import tkinter` échoue immédiatement à l'exécution.
- Aucun fichier `.desktop`, aucune icône Linux, aucun script de build, aucune piste d'empaquetage (AppImage/deb/autre) n'existe.
- Aucune release ni CI Linux n'a jamais existé.

**Les deux (Windows + Linux)** :
- **Zéro test automatisé** dans le dépôt (aucun fichier `test_*.py`/`*_test.py`, pas de `pytest` dans les dépendances) — refactorer pour séparer domaine/plateforme sans filet de sécurité serait risqué.
- **Aucune CI** (`.github/workflows/` absent) — rien n'a jamais été vérifié automatiquement, y compris sur macOS.
- Logique métier et code Tkinter/OS totalement entremêlés dans un seul fichier avec état global (§1) — bloque toute extraction propre tant que ce n'est pas corrigé.
- Version de Python non pinnée et incohérente avec l'environnement de dev réel disponible (§1, §6).

## 5. Questions structurantes tranchées par cet audit

- **Question** : faut-il prévoir un fallback d'accélération matérielle spécifique à une plateforme (ex. accélération macOS-only avec repli CPU ailleurs) ?
  **Décision** : non, aucun fallback n'est à coder.
  **Justification** : `ctranslate2` (le moteur d'inférence sous-jacent à `faster-whisper`) ne supporte que deux backends : **CPU** et **CUDA**. Il n'existe **aucun support Metal, CoreML ou MPS** dans `ctranslate2` — donc rien de tel n'est utilisé ici, ni directement, ni indirectement. Sur macOS aujourd'hui, l'app tourne donc déjà en **CPU pur** (aucun GPU Apple Silicon n'est exploité). Comme le code ne fixe jamais `device=`, le comportement `device="auto"` de `ctranslate2` s'appliquera **identiquement** sur Windows et Linux — CPU par défaut, et **utilisation automatique d'un GPU NVIDIA/CUDA si l'utilisateur en a un et que la variante CUDA de `ctranslate2` est installée**, ce qui n'est même pas possible sur macOS aujourd'hui. Le comportement voulu (CPU partout, CUDA en bonus si dispo) est déjà celui du code actuel, tel quel, sans modification — un non-événement pour le portage, mais qui mérite d'être documenté explicitement pour ne pas être « réinventé ».

- **Question** : quel format de distribution adopter pour les builds Windows et Linux ?
  **Décision** : conserver **PyInstaller** comme outil de packaging unique pour les trois OS, en miroir exact de la pratique macOS actuelle (`--windowed --onedir`), plutôt que d'introduire un outil de build différent par plateforme.
  **Justification** : PyInstaller supporte nativement Windows et Linux, ne demande aucun changement d'outillage, et le dépôt contient déjà `assets/logo.ico` (Windows) — seul un icône/format Linux (`.png`, déjà présent via `assets/logo.png`) manque, ce qui est trivial. Concrètement, pour le MVP portable : **Windows** → `pyinstaller --windowed --onedir app_whisper.py --name "Transcriber" --icon assets/logo.ico` → dossier `dist/Transcriber/` livré tel quel (zip), exactement comme le `.app` macOS aujourd'hui ; un installeur (Inno Setup, MSI) est un vrai plus mais n'est pas requis pour l'équivalence fonctionnelle avec l'existant macOS, lui-même sans installeur — backlog post-MVP. **Linux** → `pyinstaller --windowed --onedir app_whisper.py --name "transcriber" --icon assets/logo.png` → dossier `dist/transcriber/` livré en tarball ; **AppImage** est l'équivalent le plus proche d'un `.app` macOS mais ajoute un vrai coût d'outillage (`appimagetool`, fichier `.desktop`, pas de mise à jour intégrée) qui ne doit pas bloquer le MVP — backlog post-MVP (un `.deb` est encore plus d'effort et n'est pas retenu). Ce choix garde une barre d'exigence cohérente entre les trois OS : aucun ne reçoit un packaging plus abouti que les autres au stade du MVP.

## 6. Qualité générale du code

- **Zéro test**, zéro CI, zéro linter configuré, zéro type hints, zéro docstring.
- **Bug latent indépendant du portage** : `transcribe_task()` (dans le thread daemon) n'a **aucun `try/except`**. Si la transcription échoue (fichier corrompu, dossier de sortie non accessible en écriture, modèle indisponible faute de réseau au premier téléchargement, etc.), l'exception se propage silencieusement dans le thread, **la fenêtre « transcription en cours » ne se ferme jamais**, et l'utilisateur n'a aucun retour d'erreur. Ce bug existe déjà sur macOS ; il devient plus visible en portant l'app sur des environnements avec plus de variance (permissions Windows, absence de réseau en CI Linux, etc.) — à corriger (§7 point 2), sans changer le comportement du chemin nominal.
- **État global mutable** (`selected_file`, `model_choice`, `file_label`, `model_menu`, `root`) au niveau du module — rend `run_transcription`/`browse_file`/`on_transcribe` impossibles à tester unitairement sans un vrai `tk.Tk()` monté.
- Pas de séparation dépendances runtime/dev (`requirements.txt` unique, pas de `requirements-dev.txt` ni de groupe `[dev]`).
- Incohérence d'environnement : `numpy==2.2.5` exige Python ≥ 3.10 mais aucune version de Python n'est documentée ni pinnée nulle part — un contributeur suivant le README à la lettre avec un Python système plus ancien (comme celui de cette machine d'audit, 3.9.6) échouera à l'installation.
- README en avance sur la réalité du produit livré (annonce un `.exe` téléchargeable en Release alors qu'aucun n'existe, cf. §4).

## 7. Recommandations priorisées

| # | Recommandation | Effort | Risque si non traité | Lié à la mission actuelle ? |
|---|---|---|---|---|
| 1 | Extraire les fonctions pures (`segments_to_text`, `output_path_for`, `is_supported_audio_extension`, `is_valid_model_name`) dans `domain/`, avec tests unitaires — prérequis à tout le reste, permet le TDD immédiat sans dépendre de `faster-whisper`/Tkinter. | Faible | Faible | Oui |
| 2 | Ajouter un `try/except` autour de `transcribe_task()` pour fermer proprement la fenêtre de chargement et informer l'utilisateur en cas d'erreur — bug latent déjà présent sur macOS, indépendant du portage mais à corriger tôt vu la variance d'environnements à venir. | Faible | Moyen (comportement actuel en cas d'erreur = blocage silencieux) | Oui |
| 3 | Nettoyer `requirements.txt` : isoler `macholib` (macOS-only) via un marqueur d'environnement (`; sys_platform == "darwin"`) plutôt que de l'installer partout inutilement. | Faible | Faible | Oui |
| 4 | Mettre en place `pytest` + une CI GitHub Actions en matrice (`macos-latest`, `windows-latest`, `ubuntu-latest`) **dès le premier jalon de portage**, avant d'écrire le moindre code spécifique Windows/Linux. | Moyen | Faible | Oui |
| 5 | Documenter (README + éventuel script de setup) la dépendance système `python3-tk` sous Linux — sans elle, l'app ne démarre pas du tout, et rien dans `pip install` ne le signale. | Moyen | Moyen (bloquant silencieux sur Linux) | Oui |
| 6 | Ajouter des commandes/scripts de build PyInstaller Windows et Linux, en miroir des commandes macOS existantes, en réutilisant `assets/logo.ico`/`assets/logo.png` déjà présents. | Moyen | Faible | Oui |
| 7 | Empaquetage AppImage pour Linux — backlog post-MVP, pas bloquant pour la parité fonctionnelle de base. | Élevé | Faible | Oui |
| 8 | Corriger le README, qui affirme qu'un `.exe` est déjà disponible en Release alors que la release existante (`v0.1.0`) indique explicitement « Windows version will coming soon » et ne contient aucun binaire Windows. | Faible | Faible | Oui |
| 9 | Pinner une version de Python explicite (ex. `>=3.10,<3.13`, cohérente avec `numpy==2.2.5`) et la documenter, pour éviter les échecs d'installation silencieux selon l'environnement du contributeur. | Faible | Faible | Oui |

> Statut (2026-08-14, relecture finale) : les 9 recommandations ont toutes été appliquées au fil de l'exécution du plan (voir `PLAN.md`).

## 8. Questions ouvertes réellement bloquantes

Aucune. Les deux questions structurantes posées par le brief de mission (§5 : accélération matérielle, format de distribution) sont tranchées ci-dessus, directement déductibles du code et des dépendances — pas de remontée nécessaire.

Point de vigilance signalé néanmoins (non bloquant, mais à ne pas laisser sans correction) : le README annonce publiquement un binaire Windows déjà disponible, ce qui est faux (voir §4, §7 point 8) — corrigé dans le cadre du portage (`PLAN.md` J3).

## Annexes — découvertes en cours d'exécution

### Addendum — dépendance rompue détectée par la CI (2026-08-14)

La toute première exécution de la CI multi-OS (J2) a échoué **identiquement sur Linux, Windows et macOS Apple Silicon** dès l'étape `pip install -r requirements-dev.txt`. Investigation : `av==14.3.0` (dépendance transitive de `faster-whisper`, utilisée pour le décodage audio, cf. §2) **n'a aucun fichier publié sur PyPI** (0 wheel, 0 sdist) — la version épinglée dans `requirements.txt` a été retirée de PyPI après que ce pin a été figé (`pip freeze`) à un moment où elle existait encore. Conséquence : **`pip install -r requirements.txt` échoue déjà aujourd'hui sur macOS aussi**, indépendamment de tout portage — ce n'est pas une régression introduite par ce travail, mais un cas de « dependency rot » préexistant que la CI vient de révéler pour la première fois, faute d'avoir jamais existé avant.

Correctif appliqué : `av==14.2.0` (version antérieure la plus proche disposant de wheels prébuilts complets pour cp39–cp313 sur `win_amd64`, `macosx_arm64`/`x86_64`, et `manylinux_x86_64`/`aarch64` — vérifié via l'API PyPI). Aucun changement de comportement attendu : PyAV n'est jamais appelé directement par le code applicatif, uniquement en interne par `faster-whisper` pour le décodage.

### Addendum — CI macOS Intel non obtenable (2026-08-14)

Le jalon J2 (CI multi-OS) a été mis en place avec une matrice couvrant `macos-13` (Intel), `macos-14` (Apple Silicon), `windows-latest`, `ubuntu-latest`. Sur 4 exécutions consécutives, sur plus d'1h30 d'attente cumulée, **les jobs `macos-13` ne se sont jamais vu attribuer de runner** (statut `queued` en continu), alors que les 3 autres configurations (y compris le job `e2e` de bout en bout avec un vrai modèle Whisper) se terminent en quelques minutes avec succès.

Vérifications faites avant de conclure :
- Le dépôt est **public** → minutes GitHub Actions illimitées, ce n'est donc pas une limite de dépenses/quota.
- La page de statut officielle (`githubstatus.com`) ne signale **aucun incident en cours** lié aux runners macOS.
- Le changelog Actions de GitHub ne mentionne **aucune dépréciation annoncée** de `macos-13` à cette date.

Cause exacte non confirmée (accès insuffisant pour le diagnostiquer précisément — capacité runner probablement restreinte côté GitHub, ou réglage compte/organisation invisible depuis l'API publique). Remonté à l'utilisateur, qui a tranché : **retirer `macos-13` de la matrice CI et se reposer sur `macos-latest`** (Apple Silicon aujourd'hui) comme seul signal CI macOS, plutôt que de bloquer indéfiniment le portage sur ce point.

Conséquence assumée : la CI ne fournit **plus de preuve automatisée pour macOS Intel spécifiquement**. Le risque réel est jugé faible :
- Aucune trace de code spécifique à l'architecture (Intel vs ARM) dans `app_whisper.py`, `domain/`, ou `platform_/` — le comportement vérifié sur Apple Silicon n'a aucune raison de diverger sur Intel.
- Les instructions de build Intel existantes (cross-build via Rosetta, cf. README « For Macos (Intel) ») restent documentées et inchangées.
- Si un accès à une machine Intel réelle (ou un runner `macos-13` fonctionnel) redevient disponible plus tard, une vérification manuelle ponctuelle reste possible sans changement de code.

### Addendum — résolution : Intel via Rosetta sur macos-latest (2026-08-14)

Piste explorée sur une branche dédiée (`experiment/intel-build-via-rosetta`) : au lieu d'attendre un runner `macos-13`, peut-on obtenir une vraie exécution x86_64 **depuis le runner `macos-latest` (Apple Silicon)**, via Rosetta 2 ?

Vérifications faites (job `rosetta-diagnostic`, logs consultés) :
- Le Python fourni par `actions/setup-python@v5` sur `macos-latest` est un **binaire universal2** (`lipo -archs` → `x86_64 arm64`), pas un binaire arm64 seul.
- `arch -x86_64 python3 -c "import platform; print(platform.machine())"` retourne bien `x86_64` — Rosetta 2 s'installe et fonctionne sans problème sur le runner hébergé (`softwareupdate --install-rosetta --agree-to-license` réussit en quelques secondes).
- Le Python système (`/usr/bin/python3`, fourni par les Command Line Tools) est également universal (`x86_64 arm64e`) et se comporte pareil sous Rosetta.

Conséquence : il est possible de construire un **virtualenv x86_64 complet** (`arch -x86_64 python3 -m venv ...`), d'y installer les dépendances (`pip` résout alors correctement des wheels `macosx_x86_64`, confirmé en pratique avec `numpy`, `ctranslate2`, `av`, `onnxruntime`, `faster-whisper`), et d'y exécuter la suite de tests — y compris le test E2E de transcription réelle — en x86_64 authentique, sans jamais avoir besoin d'un runner `macos-13`.

Deux jobs CI permanents ont été ajoutés sur cette base : `test (macOS Intel via Rosetta)` et `e2e (macOS Intel via Rosetta)`, tous deux vérifiés verts (run [31787156790](https://github.com/aymnms/transcriber/actions/runs/31787156790)). Cela **referme le trou de couverture macOS Intel** documenté juste au-dessus, sans dépendre de la disponibilité d'un runner `macos-13` — cette exécution sous Rosetta est la vérification la plus proche d'un vrai Mac Intel qu'on puisse obtenir sans matériel physique.

### Addendum — bug Windows trouvé en test réel : blocage UI (2026-08-17)

Test manuel utilisateur sur une machine Windows réelle (modèle `tiny`, fichier audio d'exemple du dépôt) : la fenêtre « Transcription en cours » reste affichée indéfiniment, même une fois la transcription terminée avec succès en arrière-plan.

**Cause identifiée par lecture de code** : `transcribe_task()` (le worker `threading.Thread` daemon dans `run_transcription()`, `app_whisper.py`) appelait directement des méthodes de widgets Tkinter (`loader.destroy()`, `messagebox.showerror`, création de `Toplevel`) **depuis ce thread d'arrière-plan**. Tcl/Tk n'est **pas thread-safe** : muter des widgets depuis un thread autre que le thread principal est un comportement non défini. Ce risque avait déjà été identifié sans preuve de défaillance lors de la revue d'architecture du 2026-08-14 (« mise à jour de widgets Tkinter depuis un thread en arrière-plan », voir `PLAN.md`) — l'implémentation Tcl/Tk de macOS s'est révélée assez tolérante pour masquer le problème, celle de Windows beaucoup moins : les appels widgets émis hors du thread principal y restent bloqués sans jamais s'exécuter, d'où le blocage silencieux observé (la transcription réussit réellement, seule la fermeture de la fenêtre ne se produit jamais).

**Constat sur la couverture de test** : ni la suite unitaire/fonctionnelle ni le test E2E n'exercent ce chemin — le test E2E appelle `platform_/transcriber.py` directement, sans jamais passer par `run_transcription()`/le threading de `app_whisper.py`. La CI verte sur les 4 configurations cibles ne constituait donc pas une preuve suffisante que l'app fonctionne réellement de bout en bout côté utilisateur sur Windows — c'est un point aveugle structurel (pas de session graphique pilotable en CI), déjà signalé comme limite en `J1-9`.

**Correctif appliqué** : `transcribe_task()` ne touche plus aucun widget Tk ; il pousse son résultat (succès ou erreur) dans un `queue.Queue` thread-safe. Un polling `loader.after(100, poll_result)`, qui s'exécute sur le thread principal via la boucle d'événements Tk, consomme la queue et effectue toutes les mutations de widgets. C'est le pattern standard et documenté pour faire interagir un thread de travail avec Tkinter sans jamais l'appeler directement depuis ce thread.

### Addendum — bug Linux trouvé en test réel : binaire lié à une glibc trop récente (2026-08-17)

Tests manuels utilisateur sur une machine Linux réelle : le binaire `transcriber` (tarball) et l'AppImage échouent tous deux au lancement avec la même erreur :
```
dlopen: /lib/x86_64-linux-gnu/libm.so.6: version `GLIBC_2.38' not found (required by .../libpython3.11.so.1.0)
```

**Cause identifiée** : le job `build-linux` de `release.yml` tourne sur `runs-on: ubuntu-latest`, qui pointe aujourd'hui vers **Ubuntu 24.04** (glibc 2.39). Le `libpython3.11.so` bundlé par PyInstaller est donc lié dynamiquement contre des symboles glibc aussi récents que 2.38+, ce qui rend le binaire **incompatible avec toute distribution Linux dont la glibc est plus ancienne** (Ubuntu 22.04 et antérieur, Debian 12 et antérieur, etc.) — la grande majorité des installations Linux en usage courant. L'AppImage n'échappe pas au problème : contrairement à une idée reçue, une AppImage n'embarque **pas** la glibc elle-même (ce serait risqué/non portable de le faire) ; elle reste dépendante de celle du système hôte, d'où l'intérêt normalement de la construire sur la distribution la **plus ancienne** possible pour maximiser la compatibilité descendante — ce que ce pipeline ne faisait pas.

**Décision tranchée par cet audit** : reconstruire dans un **conteneur Docker `ubuntu:22.04`** (glibc 2.35) exécuté sur le runner `ubuntu-latest`, plutôt que de simplement changer `runs-on:` en `ubuntu-22.04`. Justification : les images de runner `ubuntu-22.04` de GitHub Actions entrent elles-mêmes en dépréciation le 17 septembre 2026 (fin de support le 17 avril 2027, vérifié via `actions/runner-images` — voir sources ci-dessous) — un mois seulement après la date de cette investigation. Passer par un conteneur découple le choix de la glibc cible du cycle de vie des images de runner GitHub (les tags Docker Hub ne sont jamais retirés de force par GitHub) : le job continue de s'exécuter sur `ubuntu-latest`, toujours maintenu à jour par GitHub, tandis que le *build* a lieu dans `ubuntu:22.04`, épinglé indéfiniment. Objectif de compatibilité retenu : glibc 2.35 (Ubuntu 22.04+/Debian 12+), sans aller jusqu'à une cible plus ancienne (type image `manylinux`/CentOS) — ce niveau de compatibilité maximale ajouterait un coût d'outillage disproportionné (pas de `python3-tk` facilement disponible sur ces bases) pour un gain incertain au vu du public visé par ce projet. Si un besoin de compatibilité plus ancienne se confirme un jour, ce sera un jalon backlog séparé.

Sources consultées : [actions/runner-images issue #14254 — dépréciation ubuntu-22.04](https://github.com/actions/runner-images/issues/14254).

**Confirmation obtenue (logs CI, 2026-08-17)** : le premier run diagnostic dans le conteneur `ubuntu:22.04` échouait dès l'étape de build avec `python: /lib/x86_64-linux-gnu/libm.so.6: version 'GLIBC_2.38' not found (required by /__t/Python/3.11.15/x64/lib/libpython3.11.so.1.0)`. Cause exacte : `actions/setup-python@v5` télécharge un **binaire Python précompilé** (3.11.15) qui exige lui-même `GLIBC_2.38` pour s'exécuter — donc l'interpréteur ne démarre même pas dans un conteneur dont la glibc est plus ancienne (2.35), avant toute installation de dépendance. Confirmé indépendamment par reproduction locale (Docker, `--platform linux/amd64`) : le `python3` fourni par `apt` dans le conteneur (3.10.12, glibc-native) build sans erreur et produit un binaire dont le plafond `GLIBC` mesuré est bien `2.35`. Correctif retenu : abandonner `actions/setup-python` pour ce job et utiliser le `python3`/`venv` du conteneur.

### Addendum — blocage Windows persistant : téléchargement du modèle, pas un bug applicatif (2026-08-17)

Une fois `J9-1` (widgets Tk mutés hors du thread principal) corrigé et confirmé fonctionnel sous Linux avec un code strictement identique, l'utilisateur a signalé que le blocage persistait spécifiquement sous Windows. Un build de diagnostic (console visible, traces `[DEBUG]` temporaires dans `platform_/transcriber.py`) a isolé le point de blocage exact :

```
[DEBUG] transcribe_task: thread started
[DEBUG] loading model...
config.json: 2.25kB [00:00, 4.49MB/s]
```

Le téléchargement s'arrête net juste après `config.json` (métadonnées, quasi instantané), avant tout octet du fichier de poids du modèle. Ce n'est donc **pas** un bug de threading Tk (déjà exclu) mais un blocage réseau pendant le téléchargement du modèle depuis le Hugging Face Hub — cohérent avec un réseau restrictif (pare-feu/proxy d'entreprise ou institutionnel) qui autorise l'API principale `huggingface.co` mais bloque ou ignore silencieusement les connexions vers le CDN de fichiers volumineux.

Correctif appliqué : `HF_HUB_DOWNLOAD_TIMEOUT` resserré à 8s (`app_whisper.py`, fixé avant l'import de `faster_whisper`, car `huggingface_hub` lit cette variable d'environnement à l'import). `huggingface_hub==0.30.2` retente déjà jusqu'à 5 fois avec ce délai, bornant l'attente pire cas à environ 90 secondes au lieu d'un blocage potentiellement indéfini — **si** l'échec se manifeste comme un timeout ou une connexion refusée normale.

**Insuffisant en pratique** : retesté par l'utilisateur en attendant largement plus de 90 secondes, le blocage persiste à l'identique. Ceci renforce l'hypothèse d'un véritable « trou noir » réseau (paquets silencieusement ignorés plutôt que refusés ou expirés au niveau TCP) — un cas contre lequel aucun timeout côté client (`requests`/`huggingface_hub`) ne peut garantir un échec propre, puisque la tentative de connexion au niveau OS peut elle-même rester bloquée au-delà du délai configuré selon certaines configurations de proxy/pare-feu.

**Conclusion** : ce n'est très probablement plus un défaut du code de l'application (déjà corrigé pour la partie qui l'était réellement, `J9-1`), mais une limite du réseau spécifique à la machine Windows testée. Suivi ouvert dans l'issue GitHub [#2](https://github.com/aymnms/transcriber/issues/2) — prochaine étape : confirmer via un test sur un autre réseau (partage de connexion mobile) depuis la même machine.
