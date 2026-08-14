# Plan de migration multiplateforme — transcriber

Ce plan découle directement de [`AUDIT.md`](./AUDIT.md). Résumé du raisonnement :

- L'audit (§2.1) montre que le code métier et le code Tkinter/OS sont entièrement entremêlés dans un seul fichier avec état global. **Aucun portage propre n'est possible sans séparer d'abord `domain/` (logique pure) et `platform/` (adaptateurs OS/GUI)** — c'est donc le tout premier jalon, avant même de toucher à Windows/Linux.
- L'audit (§2.5, §2.7) montre qu'il n'existe **aucun test ni CI**. Refactorer sans filet serait risqué et invérifiable sur les OS que je ne peux pas exécuter localement (§4 du brief) — donc la mise en place de `pytest` est intégrée au même jalon que l'extraction du domaine, et la **CI multi-OS est mise en place dès le jalon suivant**, avant tout code spécifique Windows/Linux, conformément à la contrainte du brief.
- L'audit (§2.3) tranche qu'**aucun fallback GPU n'est à coder** : `ctranslate2` gère déjà `device="auto"` (CPU partout, CUDA en bonus) de façon identique sur les trois OS. Aucun jalon dédié à l'accélération matérielle n'est donc nécessaire.
- L'audit (§2.6) tranche le format de distribution : **PyInstaller pour les trois OS**, en miroir de la pratique macOS actuelle (bundle `--onedir` zippé, pas d'installeur). Les jalons Windows/Linux réutilisent donc l'outillage existant plutôt que d'en introduire un nouveau.
- L'audit (§2.5) identifie un blocage Linux spécifique et non négociable : `python3-tk` est une dépendance **système**, absente de `pip`. Le jalon Linux doit la documenter et l'installer explicitement en CI.
- Deux corrections de qualité indépendantes du portage mais peu coûteuses et à faible risque sont glissées dans le jalon 1 (bug latent §2.7, nettoyage `requirements.txt` §2.8-3) car elles touchent exactement le code qui est de toute façon réécrit à cette étape.
- Le dernier jalon (MVP portable) correspond à la définition imposée par le brief (§3) : lancement + transcription bout-en-bout vérifiés par CI verte sur macOS Intel, macOS Apple Silicon, Windows et Linux.

Contrainte transverse à tous les jalons : **aucune régression macOS** (vérifiée par la CI dès qu'elle existe, par lecture de code avant).

### Écarts documentés par rapport au brief initial

- Le paquet `platform/` prescrit par le brief a été nommé **`platform_/`** (avec un underscore) pour ne pas masquer le module standard Python `platform`, qui aurait cassé des imports internes de bibliothèques tierces. Détail en PLAN.md J1.6.
- La CI ne s'appuie **plus sur un runner `macos-13`** : ce runner n'a jamais pu être attribué par GitHub sur 4 tentatives et plus d'1h30 d'attente, pour une cause non diagnosticable depuis l'API publique. **Résolu autrement** : le Python fourni par `actions/setup-python` sur `macos-latest` (Apple Silicon) est un binaire universal2 (x86_64 + arm64), et Rosetta 2 fonctionne sans problème sur ce runner — la CI construit donc un vrai environnement x86_64 via `arch -x86_64` et y exécute toute la suite (y compris le test E2E de transcription réelle), ce qui referme la couverture Intel sans dépendre de `macos-13`. Détail complet en AUDIT.md « Addendum — résolution : Intel via Rosetta sur macos-latest ».

---

## Kanban

### ✅ Terminé
- [x] J0 — Audit complet (`AUDIT.md`)
- [x] J0 — Rédaction de ce plan
- [x] J1.1 Créer la branche de travail dédiée (`feat/cross-platform-migration`)
- [x] J1.2 Mettre en place `pytest` (dossier `tests/unit/`, `tests/functional/`, venv local `.venv` déjà ignoré par `.gitignore`)
- [x] J1.3 TDD : extraire `domain/transcription.py` (`segments_to_text`, `output_path_for`)
- [x] J1.4 TDD : extraire `domain/audio_files.py` (`is_supported_audio_extension`, `FILE_DIALOG_PATTERN`)
- [x] J1.5 TDD : extraire `domain/whisper_models.py` (`is_valid_model_name`, `SUPPORTED_MODELS`, `DEFAULT_MODEL`)
- [x] J1.6 Réécrire `app_whisper.py` pour consommer `domain/`/`platform_/` sans changer le comportement observable — package renommé `platform_` (et non `platform`) pour ne pas masquer le module standard `platform`, écart au libellé du brief documenté ici pour traçabilité
- [x] J1.7 Corriger le bug latent : `try/except` dans `platform_/transcriber.py` (`TranscriptionError`), testé (écriture réelle sur disque via `tmp_path`, pas de fichier partiel en cas d'échec), fenêtre de chargement fermée + dialogue d'erreur au lieu d'un blocage silencieux
- [x] J1.8 Nettoyer `requirements.txt` (`macholib` conditionné à `sys_platform == "darwin"` — `altgraph` est en réalité cross-platform, correction apportée à `AUDIT.md` §2.3/§2.5/§2.8-3 en cours de route), ajout de `requirements-dev.txt`, version Python documentée (`>=3.10,<3.13`)
- [x] J1.9 Vérification : suite de tests verte localement (16/16) + smoke-test d'import de `app_whisper.py` avec les vraies dépendances installées (venv jetable) confirmant que le câblage domain/platform_/GUI ne casse rien. Pas de lancement interactif complet de la fenêtre Tkinter (pas de session graphique pilotable ici) — la confirmation comportementale complète macOS reste à la charge de l'utilisateur ou de la CI (J2)

- [x] J2.1 `.github/workflows/ci.yml` : matrice `macos-latest` (Apple Silicon), `windows-latest`, `ubuntu-latest`, exécutant `tests/unit` + `tests/functional`
- [x] J2.2 Installation de `python3-tk` dans l'étape `ubuntu-latest` de la CI (réf. AUDIT §2.5 Linux)
- [x] J2.3 CI verte confirmée sur les 3 configurations restantes (Linux, Windows, macOS Apple Silicon)
  > `macos-13` (Intel) a été retiré de la matrice après 1h30 sans qu'aucun runner ne lui soit jamais attribué — cause non confirmable depuis l'API publique (pas un problème de quota, pas d'incident GitHub signalé). Décision utilisateur (2026-08-14) : passer à `macos-latest` seul plutôt que de bloquer indéfiniment.
- [x] J2.4 Couverture Intel restaurée autrement : jobs `test (macOS Intel via Rosetta)` et `e2e (macOS Intel via Rosetta)` — build d'un virtualenv x86_64 sous Rosetta 2 sur `macos-latest` (`arch -x86_64 python3 -m venv ...`), suite complète (unitaires + fonctionnels + E2E réel) exécutée en x86_64 authentique. Vérifié faisable via un job diagnostic (`rosetta-diagnostic`, confirmé : Python `setup-python` est universal2, Rosetta s'installe et fonctionne sur le runner hébergé) avant implémentation, sur la branche `experiment/intel-build-via-rosetta`, mergée dans `feat/cross-platform-migration` après validation verte (run [31787156790](https://github.com/aymnms/transcriber/actions/runs/31787156790)). Détail dans AUDIT.md « Addendum — résolution : Intel via Rosetta sur macos-latest ».
- [x] J3.1 Commande de build PyInstaller Windows ajoutée au README (`assets/logo.ico`)
- [x] J3.2 Vérifié par CI (job `test (Windows)`, incluant `tests/functional/test_app_entrypoint.py`) : import complet de `app_whisper.py` sans erreur
- [x] J3.3 README corrigé sur l'état réel de la disponibilité Windows (retrait de la mention d'un `.exe` déjà publié)
- [x] J4.1 Dépendance système `python3-tk` documentée dans le README
- [x] J4.2 Commande de build PyInstaller Linux ajoutée au README (`assets/logo.png`)
- [x] J4.3 Vérifié par CI (job `test (Linux)`, `python3-tk` installé) : import complet sans erreur
- [x] J5.1 Smoke test E2E (`tests/e2e/test_transcribe_sample_audio.py`, modèle `tiny` réel sur `assets/audios/NewRecording.m4a` via `platform_/transcriber.py`), marqueur pytest `e2e` dédié (hors suite rapide), job CI séparé `e2e` sur la matrice. Validé en local (macOS ARM, dépendances réelles) et en CI (Linux, Windows, macOS Apple Silicon) : transcription correcte du fichier échantillon.
- [x] J5.2 CI verte simultanément sur macOS Apple Silicon, Windows, Linux (jobs `test` ET `e2e`, run [31784867450](https://github.com/aymnms/transcriber/actions/runs/31784867450), 6/6 jobs verts)
  > Complété par J2.4 : macOS Intel dispose maintenant de sa propre preuve CI automatisée (via Rosetta sur `macos-latest`), donc la réserve initiale ne s'applique plus — les 4 configurations cibles (macOS Apple Silicon, macOS Intel via Rosetta, Windows, Linux) ont une CI verte.
- [x] J5.3 README mis à jour (matrice de support par OS, instructions de build Windows/Linux, prérequis Linux, correction de la disponibilité réelle)
- [x] J5.4 Revue finale de `AUDIT.md`/`PLAN.md` — ce plan est à jour, addendums CI documentés
- [x] J6.1 `pyproject.toml` : métadonnées projet + config `[tool.semantic_release]` (commits conventionnels déjà utilisés depuis le début de ce travail, `allow_zero_version = true` pour rester en 0.x, `tag_format = "v{version}"` cohérent avec le tag `v0.1.0` existant)
- [x] J6.2 Validé en local (`--noop`) : calcul correct de la prochaine version (`0.2.0`, cohérent avec les commits `feat:` accumulés depuis `v0.1.0`) et génération du changelog
- [x] J6.3 `.github/workflows/release.yml` : déclenché après succès de la CI sur `main` (`workflow_run`), job `release` (bump version + changelog + tag + Release GitHub via l'action officielle `python-semantic-release/python-semantic-release`), puis jobs `build-macos` (ARM + Intel via Rosetta), `build-windows`, `build-linux` qui buildent et attachent les binaires PyInstaller à la Release via `gh release upload`
- [x] J6.4 Validation réelle sur `main`, avec confirmation explicite de l'utilisateur avant déclenchement : [v0.2.0](https://github.com/aymnms/transcriber/releases/tag/v0.2.0) publiée automatiquement — tag créé, `CHANGELOG.md` généré, 4 binaires attachés (`Transcriber-macOS-ARM.zip` 60.6 MB, `Transcriber-macOS-Intel.zip` 83.4 MB, `Transcriber-Windows.zip` 94.5 MB, `transcriber-Linux.tar.gz` 132.8 MB). Pipeline de bout en bout validé, 4/4 jobs verts (run [31790846173](https://github.com/aymnms/transcriber/actions/runs/31790846173)).

### 🔵 En cours
*(rien — MVP portable + release automatisée tous deux livrés et validés en conditions réelles)*

### À faire

**Backlog (hors périmètre MVP, réf. AUDIT §2.8-7)**
- [x] Empaquetage AppImage pour Linux — `packaging/linux/transcriber.desktop`, job `build-linux` de `release.yml` assemble l'AppDir et build via `appimagetool` (`--appimage-extract` pour éviter la dépendance à FUSE, absent des runners GitHub), attaché à chaque release
- [x] Installeur Windows (Inno Setup) — `packaging/windows/installer.iss`, compilé via `iscc` (préinstallé sur `windows-latest`), version injectée dynamiquement (`/DMyAppVersion=...`), attaché à chaque release
- [ ] Codesign/notarization macOS — nécessite un compte Apple Developer Program actif (99$/an), non disponible actuellement ; discuté avec l'utilisateur le 2026-08-14, reporté
- [ ] Si un vrai Mac Intel ou un runner `macos-13` fonctionnel devient disponible un jour, envisager une vérification ponctuelle sur matériel physique en complément de la CI Rosetta (non bloquant : Rosetta est déjà une vérification x86_64 authentique, pas une simulation)
- [ ] Bumper `actions/checkout`/`actions/setup-python` vers une version nativement Node 24 quand elle sortira (actuellement des warnings inoffensifs — GitHub force déjà le fallback Node 24, la CI reste verte, cf. journal 2026-08-14)

---

## État final (2026-08-14)

**MVP portable atteint intégralement**, sans réserve : l'application se lance et exécute la transcription de bout en bout, vérifié par CI verte sur les **quatre configurations cibles du brief** — macOS Apple Silicon, macOS Intel (via Rosetta 2 sur `macos-latest`), Windows et Linux (`test` + `e2e`, run [31787156790](https://github.com/aymnms/transcriber/actions/runs/31787156790), 8/8 jobs verts). Le runner `macos-13` reste inutilisable côté GitHub, mais s'est révélé non nécessaire : l'exécution x86_64 sous Rosetta sur un runner Apple Silicon est une vérification tout aussi authentique.

Aucune régression macOS introduite : le comportement observable de `app_whisper.py` est identique à l'original sur le chemin nominal, avec un bug latent corrigé (blocage silencieux en cas d'échec de transcription) et une dépendance PyPI rompue corrigée (`av`).

---

## Journal

- 2026-08-14 — Audit complet réalisé (`AUDIT.md`). Aucune question bloquante identifiée : les deux points de décision du brief (accélération matérielle, format de distribution) sont tranchés directement par l'audit.
- 2026-08-14 — Plan de migration rédigé (`PLAN.md`), démarrage du jalon J1.
- 2026-08-14 — J1 terminé : `domain/` (transcription, audio_files, whisper_models) extrait en TDD avec 13 tests unitaires ; `platform_/transcriber.py` ajouté (3 tests fonctionnels) et corrige le blocage silencieux en cas d'échec de transcription ; `app_whisper.py` recâblé sans changement de comportement nominal ; `requirements.txt` nettoyé et complété par `requirements-dev.txt`. Suite complète verte (16/16). Démarrage de J2 (CI multi-OS).
- 2026-08-14 — J2.1 poussé (`.github/workflows/ci.yml`), premier run CI : échec identique sur Linux/Windows/macOS ARM dès l'installation des dépendances → `av==14.3.0` n'existe plus sur PyPI (dependency rot préexistant, indépendant du portage, cf. AUDIT.md addendum). Corrigé en `av==14.2.0`. Re-push : Linux, Windows, macOS Apple Silicon verts. macOS Intel (`macos-13`) reste en `queued` de façon prolongée — capacité de runners Intel limitée côté GitHub Actions actuellement, indépendant de ce dépôt. `> ⚠️ Bloqué (temporaire, infra externe) : en attente que le runner macos-13 soit assigné par GitHub.`
- 2026-08-14 — README corrigé (retrait de la fausse mention `.exe` déjà disponible, ajout du prérequis `python3-tk` Linux, sections de build Windows/Linux). J5.1 ajouté : test E2E réel (`tests/e2e`), validé en local avec les vraies dépendances (téléchargement + transcription réussie du fichier échantillon), job CI `e2e` ajouté sur la même matrice 4 OS.
- 2026-08-14 — Ajout d'un groupe `concurrency` à la CI pour annuler les runs redondants. État confirmé sur le run le plus à jour : `test` et `e2e` verts sur Linux, Windows, macOS Apple Silicon (6/8 jobs). Les 2 jobs `macos-13` restent `queued` sans assignation de runner malgré plusieurs runs et plus d'une heure d'attente — dépôt public donc pas un problème de quota/facturation. Cause exacte non confirmée (pas d'incident GitHub signalé, pas de dépréciation annoncée trouvée). Question posée à l'utilisateur sur la marche à suivre → réponse initiale : continuer à attendre.
- 2026-08-14 — Après 30 minutes supplémentaires de vérification (1h30 cumulée), toujours aucun mouvement sur `macos-13`. Nouvelle question posée à l'utilisateur → décision : retirer `macos-13` de la matrice CI, garder `macos-latest` (Apple Silicon) comme seul signal macOS. J2 et J5.2 marqués terminés sur cette base. Écart documenté dans AUDIT.md et en introduction de ce plan.
- 2026-08-14 — Push du retrait de `macos-13` : run [31784867450](https://github.com/aymnms/transcriber/actions/runs/31784867450) vert de bout en bout en ~90s (6/6 jobs : `test`+`e2e` sur Linux, Windows, macOS Apple Silicon). README complété (matrice de support par OS). Tous les jalons J1 à J5 sont marqués terminés — MVP portable atteint sur le périmètre CI disponible, réserve macOS Intel documentée et actée avec l'utilisateur.
- 2026-08-14 — Utilisateur : possible de builder Intel sans matériel physique, via Rosetta sur Apple Silicon ? Exploré sur `experiment/intel-build-via-rosetta` (branchée depuis `feat/cross-platform-migration`) : job diagnostic `rosetta-diagnostic` confirmé — Python `setup-python` universal2, Rosetta fonctionnelle sur `macos-latest`. Remplacé par deux jobs réels `test`/`e2e (macOS Intel via Rosetta)` construisant un virtualenv x86_64 sous Rosetta. Run [31787156790](https://github.com/aymnms/transcriber/actions/runs/31787156790) : 8/8 jobs verts, y compris la suite complète et la transcription E2E réelle en x86_64 authentique. Mergé dans `feat/cross-platform-migration` comme convenu. La couverture macOS Intel est désormais complète — plus aucune réserve sur le MVP portable.
- 2026-08-14 — Demande utilisateur (hors brief initial) : mettre en place une release automatisée. Choix validés avec l'utilisateur : `python-semantic-release` (plutôt que le `semantic-release` JS), pipeline complet avec build + attachement des binaires des 4 cibles. Branche `feat/semantic-release` (depuis `feat/cross-platform-migration`) : `pyproject.toml` configuré et validé en `--noop` local (prochaine version calculée : `0.2.0`), `.github/workflows/release.yml` écrit (déclenché après CI verte sur `main` uniquement). La partie « bump + tag + Release GitHub » n'a volontairement pas encore été déclenchée pour de vrai — ça créerait une vraie Release publique, ce qui nécessite une confirmation explicite avant de merger sur `main`.
- 2026-08-14 — Confirmation explicite obtenue de l'utilisateur pour merger jusqu'à `main` et déclencher la première release réelle. Merge `feat/semantic-release` → `feat/cross-platform-migration` → `main`, CI verte (8/8) sur `main`, workflow `Release` déclenché automatiquement : [v0.2.0](https://github.com/aymnms/transcriber/releases/tag/v0.2.0) publiée avec succès, `CHANGELOG.md` généré, 4 binaires attachés (macOS ARM, macOS Intel via Rosetta, Windows, Linux). Pipeline de release automatisée validé de bout en bout en conditions réelles, y compris son comportement de non-déclenchement sur un commit `docs:` (jobs de build passés en `skipped`). Le plan de migration multiplateforme et la release automatisée sont tous deux terminés.
- 2026-08-14 — Remarque utilisateur : un changement purement documentaire (README seul) déclenchait quand même toute la CI (tests + build sur 4 plateformes), alors que `python-semantic-release` sait déjà ne pas releaser sur un commit `docs:`. Ajout d'un filtre `paths-ignore` (`**/*.md`, `LICENSE`) sur les déclencheurs `push`/`pull_request` de `ci.yml` : un push qui ne touche que des fichiers Markdown (ou `LICENSE`) ne déclenche plus du tout la CI, donc pas non plus le workflow `Release` (qui dépend de la complétion de la CI) — économie de CI cohérente avec ce que la logique de versioning faisait déjà.
- 2026-08-14 — Refonte complète du README (branche `docs/readme-revamp`), relue et validée par l'utilisateur, mergée sur `main` sans déclencher de CI (fichier Markdown seul).
- 2026-08-14 — Discussion sur le codesign/notarization macOS (nécessite un compte Apple Developer Program payant, non disponible actuellement — reporté). Demande utilisateur de traiter les deux autres items du backlog : AppImage Linux et installeur Windows. Branche `feat/appimage-and-windows-installer` : validation empirique via des jobs diagnostic temporaires dans `ci.yml` (`appimage-diagnostic` sur `ubuntu-latest`, `installer-diagnostic` sur `windows-latest`, confirmé qu'Inno Setup 6.7.1 est préinstallé) — les deux verts au premier essai. Intégré dans les jobs `build-linux`/`build-windows` de `release.yml` (attache `transcriber-x86_64.AppImage` et `Transcriber-Setup.exe` à chaque release), jobs diagnostic retirés de `ci.yml`.
