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

---

## Kanban

### ✅ Terminé
- [x] J0 — Audit complet (`AUDIT.md`)
- [x] J0 — Rédaction de ce plan

### 🔵 En cours
- [ ] J1.1 — Créer la branche de travail dédiée

### À faire

**J1 — Fondations : séparation domain/platform + infra de tests** (réf. AUDIT §2.1, §2.7, §2.8-1, §2.8-2, §2.8-3)
- [ ] J1.1 Créer la branche de travail dédiée
- [ ] J1.2 Mettre en place `pytest` (dossier `tests/unit/`, `tests/functional/`)
- [ ] J1.3 TDD : extraire `domain/transcription.py` (`segments_to_text`, `output_path_for`) — fonctions pures, zéro dépendance tierce
- [ ] J1.4 TDD : extraire `domain/audio_files.py` (`is_supported_audio_extension`, liste des extensions supportées)
- [ ] J1.5 TDD : extraire `domain/whisper_models.py` (`is_valid_model_name`, liste des modèles supportés)
- [ ] J1.6 Réécrire `app_whisper.py` pour consommer `domain/` sans changer le comportement observable (macOS)
- [ ] J1.7 Corriger le bug latent : `try/except` autour de `transcribe_task`, avec test fonctionnel sur `platform/` (fermeture du loader + message d'erreur au lieu d'un blocage silencieux)
- [ ] J1.8 Nettoyer `requirements.txt` (marqueur `sys_platform` pour `macholib`, seul paquet réellement macOS-only), pinner la version de Python (`>=3.10,<3.13`)
- [ ] J1.9 Vérification manuelle macOS (lancement de `app_whisper.py` en local) pour confirmer l'absence de régression avant la mise en place de la CI

**J2 — CI multi-OS** (réf. AUDIT §2.5, §4 du brief)
- [ ] J2.1 `.github/workflows/ci.yml` : matrice `macos-13` (Intel), `macos-14` (Apple Silicon), `windows-latest`, `ubuntu-latest`, exécutant les tests `domain/` (aucune dépendance système requise)
- [ ] J2.2 Ajouter l'installation de `python3-tk` dans l'étape `ubuntu-latest` de la CI (réf. AUDIT §2.5 Linux) pour permettre les tests `platform/` impliquant Tkinter
- [ ] J2.3 Confirmer CI verte sur les 4 configurations avant de passer au jalon suivant

**J3 — Portage Windows** (réf. AUDIT §2.5 Windows, §2.6, §2.8-6, §2.8-8)
- [ ] J3.1 Ajouter la commande de build PyInstaller Windows au README (réutilise `assets/logo.ico` déjà présent)
- [ ] J3.2 Vérifier par CI (job `windows-latest`) que `python app_whisper.py --help`/smoke-import démarre sans erreur d'import (pas de dépendance macOS-only chargée)
- [ ] J3.3 Corriger le README sur l'état réel de la disponibilité Windows (retirer la mention d'un `.exe` déjà publié tant qu'aucune release Windows n'existe)

**J4 — Portage Linux** (réf. AUDIT §2.5 Linux, §2.6, §2.8-5, §2.8-6)
- [ ] J4.1 Documenter la dépendance système `python3-tk` dans le README (prérequis, non installable via pip)
- [ ] J4.2 Ajouter la commande de build PyInstaller Linux au README (réutilise `assets/logo.png`)
- [ ] J4.3 Vérifier par CI (job `ubuntu-latest`, avec `python3-tk` installé) le smoke-import complet

**J5 — MVP portable** (réf. AUDIT §2.6, §3 du brief)
- [ ] J5.1 Smoke test E2E (transcription bout-en-bout sur un fichier audio court, modèle `tiny`) exécuté par CI sur les 4 configurations
- [ ] J5.2 CI verte simultanément sur macOS Intel, macOS Apple Silicon, Windows, Linux
- [ ] J5.3 Mise à jour finale du README (matrice de support, instructions de build par OS)
- [ ] J5.4 Revue finale de `AUDIT.md`/`PLAN.md` pour clôturer le plan

**Backlog (hors périmètre MVP, réf. AUDIT §2.8-7)**
- [ ] Empaquetage AppImage pour Linux
- [ ] Installeur Windows (Inno Setup/MSI)
- [ ] Codesign/notarization macOS

---

## Journal

- 2026-08-14 — Audit complet réalisé (`AUDIT.md`). Aucune question bloquante identifiée : les deux points de décision du brief (accélération matérielle, format de distribution) sont tranchés directement par l'audit.
- 2026-08-14 — Plan de migration rédigé (`PLAN.md`), démarrage du jalon J1.
