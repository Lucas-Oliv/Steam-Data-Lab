# Steam-Data-Lab

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Full%20Stack-red)
![AI](https://img.shields.io/badge/AI-Google%20Gemini-orange)
![Status](https://img.shields.io/badge/Status-Completed-success)

> **Uma solução Full-Stack de Data Science para análise de comportamento gamer, utilizando ETL via API, Machine Learning para clusterização e IA Generativa (RAG) para insights.**

---

## 📸 Screenshots

<img width="1874" height="954" alt="image" src="https://github.com/user-attachments/assets/4bb93768-ac26-4616-b2c0-8a3e00e74c0c" />
<img width="1860" height="951" alt="image" src="https://github.com/user-attachments/assets/f1476b5d-7fb3-4e06-81f3-73f3c5ff5ede" />
<img width="1864" height="949" alt="image" src="https://github.com/user-attachments/assets/9c00ef6f-6516-417f-af9b-3998db2379d0" />
<img width="1870" height="931" alt="image" src="https://github.com/user-attachments/assets/2ebfff47-febc-4dc6-8ce6-e97d7501b5ff" />

---

## 🚀 Sobre o Projeto

O **Game Tracker** não é apenas um organizador de biblioteca. É uma ferramenta analítica que consome dados reais da **Steam API**, processa essas informações para gerar estatísticas avançadas e utiliza Inteligência Artificial para atuar como um "Consultor de Dados" pessoal.

O objetivo foi criar um pipeline completo de dados: **Extração -> Transformação -> Armazenamento -> Modelagem (ML) -> Visualização -> Explicação (LLM).**

### ✨ Principais Funcionalidades

* **🔄 ETL Automatizado:** Conexão direta com a API da Steam para baixar/atualizar jogos, horas e conquistas em tempo real.
* **🤖 Machine Learning (Scikit-Learn):**
    * **K-Means Clustering:** Segmenta o perfil do jogador (Ex: *Hardcore, Casual, Completionist*) baseado em horas vs. progresso.
    * **KNN (K-Nearest Neighbors):** Sistema de recomendação que sugere jogos da biblioteca com base em vetores de similaridade comportamental.
* **🧠 IA Generativa (RAG):** Integração com **Google Gemini** para análise contextual. O usuário pode pedir explicações sobre gráficos específicos (ex: "Analise meu Boxplot") e receber insights personalizados.
* **📊 Análise Estatística:**
    * Princípio de Pareto (80/20).
    * Análise de Churn (Risco de Abandono).
    * Forecasting (Regressão Linear para prever data de "zeramento").
* **🎨 UI/UX Premium:** Interface desenvolvida em Streamlit com CSS customizado (Glassmorphism, Grid Layout, Animations).

---

## 🛠️ Tech Stack

* **Linguagem:** Python
* **Frontend:** Streamlit, CSS3, HTML5
* **Data Manipulation:** Pandas, NumPy
* **Machine Learning:** Scikit-Learn (KMeans, NearestNeighbors)
* **AI & LLM:** Google Generative AI (Gemini Pro/Flash)
* **Data Viz:** Altair
* **API:** Steam Web API

---

## 📂 Estrutura do Projeto

```text
Game-Tracker/
├── assets/
│   └── style.css          # Estilização avançada (Dark Mode, Cards, Profile)
├── .streamlit/
│   └── secrets.toml       # (Opcional) Armazenamento seguro de chaves
├── app.py                 # Aplicação Frontend (Streamlit)
├── backend.py             # Lógica de Negócios, ML e Conexão com IA
└── README.md              # Documentação
