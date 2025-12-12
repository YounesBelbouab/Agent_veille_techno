# 🤖 Jarvis - Agent de Veille Technologique Automatisée

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Discord](https://img.shields.io/badge/Discord-Bot-5865F2)
![AI](https://img.shields.io/badge/AI-Llama%203.3%20via%20Groq-orange)
![GCP](https://img.shields.io/badge/Cloud-BigQuery-green)

**Jarvis** est un écosystème d'agents IA conçu pour transformer la corvée de la veille technologique en une expérience automatisée, précise et divertissante. Il récupère des articles, les filtre selon des critères de qualité stricts, les nettoie, et utilise un LLM pour générer des résumés techniques avec une personnalité unique (ton mafieux/arrogant).

Le système fonctionne de manière hybride : à la demande via Discord, ou de manière totalement autonome via des tâches planifiées.

---

## ✨ Fonctionnalités Principales

### 🕵️ Agrégation Intelligente
Jarvis surveille le web en continu via NewsAPI sur des thématiques ciblées (Data Engineering, IA, Cybersécurité, DevOps, etc.) et supporte la veille multilingue (Français/Anglais).

### 🧠 Algorithme de Pertinence (`SortAgent`)
Fini le bruit et les articles "putaclic". Jarvis applique un système de scoring rigoureux :
* **Bonus** pour la présence de mots-clés techniques dans le titre et le contenu.
* **Bonus** pour les sources issues d'une "Whitelist" fiable (TechCrunch, Wired, Engineering Blogs...).
* **Malus** drastique pour les articles de type RH, annonces d'événements ou généralistes.

### 🧹 Scraping "Compound" Hybride
L'extraction du contenu utilise une approche à deux vitesses :
1.  **Fast Extract :** Extraction ultra-rapide via `Trafilatura`.
2.  **Smart Extract :** Si le contenu est complexe, Jarvis utilise des outils LLM (Tool Use) pour analyser le DOM et extraire chirurgicalement l'information pertinente.

### 💬 Le Persona Jarvis
Les rapports ne sont pas de simples résumés. Ils sont rédigés par l'IA avec une personnalité forte : cynique, autoritaire et "Business-first". Chaque rapport analyse :
* Le résumé technique.
* L'impact sur le marché.
* La maturité de la technologie.

### 🔄 Orchestration & Distribution
* **Bot Discord Interactif :** Pour poser des questions ou lancer une recherche immédiate.
* **Batch Automation :** Un moteur qui tourne en arrière-plan pour envoyer chaque matin une newsletter personnalisée par Email et Message Privé Discord, basée sur les préférences stockées dans **Google BigQuery**.

---

## 🧠 Architecture des Agents

Le système repose sur la collaboration de trois agents spécialisés :

| Agent | Rôle | Technologie |
| :--- | :--- | :--- |
| **ScrapingAgent** | "Le Nettoyeur". Il va chercher le texte brut sur les pages web, contourne les menus et les publicités pour ne livrer que la matière première. | Trafilatura + Groq Tools |
| **SortAgent** | "Le Filtre". Il analyse 50+ articles par requête, calcule un score de pertinence et ne garde que la crème de la crème (Top-K). | Python Logic + Scoring |
| **ConversationAgent** | "Le Cerveau". Il reçoit les données brutes et rédige le rapport final en appliquant le style et le formatage Jarvis. | Llama 3.3 (via Groq) |

---

## 💾 Gestion des Données

Les préférences des utilisateurs (Sujets de veille, fréquence, langue, canal de réception) sont stockées de manière persistante dans le Cloud via **Google BigQuery**. Cela permet au système de scaler et de gérer des centaines d'utilisateurs sans perte de configuration.

---

## 👤 Auteur

Projet développé par **Kylian**, **Leopold**, **Paul**, **Yassine**, **Younes** (et Jarvis).

> *"La Data c'est le pouvoir, ne laisse pas traîner ça."* — Jarvis