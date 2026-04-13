# CLAUDE.md — Contexte projet MistralxAllan Hackathon

## Contexte général

Hackathon **Mistral AI x Alan** (2026), thème : IA & Santé.
Objectif : finir **premier**.

Notre projet global s'appelle (provisoirement) **MedBridge** — une plateforme qui réduit le "medical comprehension gap" entre médecins et patients.

## Périmètre de ce repo

On implémente **uniquement** la feature patient :

> "Patients can upload prescriptions and medical imagery to receive clear explanations of their medications and condition, and interact with an AI assistant to ask questions at any time."

Les autres features (vidéos générées pour médecins, dashboard médecin) sont hors scope pour l'instant.

## Contraintes & décisions techniques

- **Modèles** : Mistral API (imposé par le hackathon). Utiliser Pixtral pour la vision (OCR prescriptions + images médicales).
- **Knowledge base** : MedlinePlus (imposé par l'utilisateur).
  - API Web Service : `https://wsearch.nlm.nih.gov/ws/query` (XML, sans auth, 85 req/min max)
  - Fichiers XML téléchargeables (tous les health topics EN + ES)
  - MedlinePlus Connect API (pour lookup par code médicament/pathologie)
  - MedlinePlus Genetics API (JSON/XML)
- **Scope pathologies** : On ne couvre PAS toutes les pathologies. On cible les pathologies communes (diabète, hypertension, cardiovasculaire, respiratoire, antibiotiques, douleur, cholestérol) pour avoir une démo solide. La base peut être élargie post-hackathon.
- **Livrable obligatoire** : repo GitHub public avec code fonctionnel (open-source).

## Stack technique décidée

- **Backend** : Python + FastAPI
- **Frontend** : React (simple, orienté démo)
- **Vector DB** : ChromaDB (local, pas de service externe, rapide à setup)
- **Embeddings** : Mistral Embed API (`mistral-embed`)
- **LLM chat** : `mistral-large-latest` (RAG + réponses patient)
- **Vision prescriptions/PDF** : `pixtral-12b` — extraction texte, médicaments, dosages
- **Vision imagerie médicale** : `MedGemma 4B` (Google, open source HuggingFace) — spécialisé radio/CT/IRM
- **RAG** : Implémentation custom légère (pas de LangChain)
- **PDF handling** :
  - PDF texte → `pdfplumber` (extraction texte directe)
  - PDF scanné → `pdf2image` (conversion pages en images) puis Pixtral

## Architecture des flux

```
Prescription (photo ou PDF)    →  Pixtral          → extraction médicaments + explications
Imagerie médicale (radio etc)  →  MedGemma 4B      → analyse spécialisée
Chat patient                   →  Mistral Large    → RAG + réponses langage simple
```

## Critères de jugement (25% chacun)

1. **Impact** — angle "coût de la non-adhérence pour les assureurs" bien positionné
2. **Technical implementation** — démo fonctionnelle end-to-end obligatoire
3. **Creativity** — explication visuelle claire, langage simplifié, multimodal
4. **Pitch** — à préparer sérieusement (25% de la note)

## État d'avancement

- [x] Contexte hackathon compris et documenté
- [x] Feature scope défini
- [x] Roadmap validée
- [x] Étape 1 : Setup & infrastructure
- [x] Étape 2 : Knowledge base MedlinePlus (11028 chunks dans ChromaDB)
- [x] Étape 3 : Prescription processing (Pixtral Large, photo + PDF)
- [x] Étape 4 : Medical image understanding (MedGemma 4B + fallback Pixtral)
- [x] Étape 5 : RAG + assistant conversationnel (testé et fonctionnel)
- [x] Étape 7 : Polish & démo (README, scénarios, dépendances vérifiées)

## Endpoints disponibles

| Endpoint | Méthode | Description |
|---|---|---|
| `/health` | GET | Vérification serveur |
| `/analyze/prescription` | POST | Analyse ordonnance (image ou PDF) |
| `/analyze/image` | POST | Analyse imagerie médicale |
| `/chat` | POST | Assistant conversationnel |
| `/chat/{session_id}` | DELETE | Effacer une session |

## Notes importantes

- Le modèle Pixtral utilisé est `pixtral-large-latest` (pas `pixtral-12b`)
- MedGemma s'active automatiquement si GPU disponible, sinon Pixtral prend le relais
- La base ChromaDB est déjà construite dans `data/chroma/` — pas besoin de la reconstruire
- Le chat a été testé avec succès avec `mistral-large-latest`
- Le test complet prescription/image nécessite une clé API avec accès Pixtral (free tier trop limité)

## Variables d'environnement nécessaires

```
MISTRAL_API_KEY=...
```

## À retenir pour les prochaines sessions

- L'utilisateur veut qu'on exécute les étapes **une par une** après validation.
- Priorité absolue : **démo fonctionnelle** devant jury, pas la perfection technique.
- Pas besoin de couvrir toutes les pathologies — focus sur les courantes.
- L'utilisateur est au hackathon avec une équipe.
- Le hackathon est celui de **2026** (pas 2024).
