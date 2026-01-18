import streamlit as st
import pandas as pd
import altair as alt
import time
import requests
import os
import backend as db
from streamlit_lottie import st_lottie
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Game Tracker V32 (Cinematic)", layout="wide", page_icon="🕹️", initial_sidebar_state="expanded")

# --- CSS LOAD ---
def carregar_css():
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_css = os.path.join(diretorio_atual, 'assets', 'style.css')
    try:
        with open(caminho_css, encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError: st.error("Arquivo 'style.css' não encontrado na pasta 'assets'.")
carregar_css()

# --- ASSETS ---
def load_lottieurl(url):
    try:
        r = requests.get(url, timeout=3)
        return r.json() if r.status_code == 200 else None
    except: return None
lottie_gamer = load_lottieurl("https://lottie.host/801a2139-4979-436d-9279-373a21648a1d/P6aK0p0Lz1.json")
lottie_analytics = load_lottieurl("https://assets5.lottiefiles.com/packages/lf20_qp1q7mct.json")

# --- SYNC AUTOMÁTICO ---
default_key = st.secrets.get("steam_key", "")
default_id = st.secrets.get("steam_id", "")
if 'steam_cfg' not in st.session_state: st.session_state['steam_cfg'] = {'id': default_id, 'key': default_key}

def auto_sync():
    if 'ja_sincronizou' not in st.session_state: st.session_state['ja_sincronizou'] = False
    if not st.session_state['ja_sincronizou'] and default_key:
        sid = db.resolver_steam_id(default_key, default_id)
        if sid:
            st.session_state['steam_cfg']['id'] = sid
            jogos, erro = db.buscar_jogos_api(default_key, sid, 10)
            if jogos: db.salvar_no_historico(jogos)
        st.session_state['ja_sincronizou'] = True
auto_sync()

# ==============================================================================
# INTERFACE PRINCIPAL
# ==============================================================================
aba_dash, aba_organizer, aba_ds, aba_sync = st.tabs(["🔥 Dashboard", "🗂️ Gerenciamento", "🧬 Data Lab", "⚙️ Config"])

# === ABA 1: DASHBOARD ===
with aba_dash:
    df = db.carregar_historico()

    # --- HEADER PERFIL (NOVO DESIGN FADE) ---
    if st.session_state['steam_cfg']['key'] and st.session_state['steam_cfg']['id']:
        p_data = db.get_steam_profile(st.session_state['steam_cfg']['key'], st.session_state['steam_cfg']['id'])
        if p_data:
            badges_html = ""
            if p_data['recent_badges']:
                for b in p_data['recent_badges']:
                    badges_html += f'<div class="steam-badge-slot" title="ID: {b.get("badgeid")}">🏅</div>'
            
            # HTML ESTRUTURADO PARA O NOVO CSS
            st.markdown(f"""
            <div class="profile-container">
                <div class="profile-pic">
                    <img src="{p_data['avatar']}">
                </div>
                <div class="profile-info">
                    <h1>{p_data['persona']}</h1>
                    <div class="badge-showcase">
                        {badges_html}
                        <div class="steam-badge-slot" style="background:none; border:none; width:auto; color:#b0c4de;">+{p_data['total_badges']} <br>Badges</div>
                    </div>
                    <div class="profile-details">
                        <span class="level-badge">Nível {p_data['level']}</span>
                        <span>🇧🇷 {p_data['country']}</span>
                        <span style="font-size:0.9rem; color:#66c0f4;">XP: {p_data['xp_atual']}</span>
                    </div>
                    <div style="margin-top:10px; width:100%; height:4px; background:#1b2838; border-radius:2px;">
                        <div style="width:{p_data['xp_perc']}%; height:100%; background:#66c0f4; box-shadow: 0 0 10px #66c0f4;"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Fallback se não tiver logado
        c1, c2 = st.columns([1,4])
        with c1: st_lottie(lottie_gamer, height=130) if lottie_gamer else None
        with c2: st.info("Conecte a Steam na aba 'Config' para carregar seu perfil.")

    if not df.empty:
        # Métricas
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Biblioteca", len(df))
        k2.metric("Horas Totais", f"{df['Horas_Totais'].sum():.0f}h")
        k3.metric("Platinas", len(df[df['Porcentagem'] == 100]))
        k4.metric("Média Completude", f"{df['Porcentagem'].mean():.1f}%")
        st.markdown("<br>", unsafe_allow_html=True)

        # Filtros
        c1, c2 = st.columns([1, 3])
        status_sel = c1.selectbox("Filtrar Status", ["Todos", "Platinado", "Meta Platinar", "Backlog", "Abandonado"])
        busca = c2.text_input("Buscar Jogo", placeholder="Nome...")
        
        df_view = df.copy()
        if status_sel != "Todos": df_view = df_view[df_view['Status'] == status_sel]
        if busca: df_view = df_view[df_view['Nome_Jogo'].str.contains(busca, case=False, na=False)]

        # --- RENDERIZAÇÃO GRID ---
        html_content = '<div class="games-grid">'
        for idx, row in df_view.sort_values(by='Horas_Totais', ascending=False).iterrows():
            bg_cls = "bg-back"
            if row['Status'] == 'Platinado': bg_cls = "bg-plat"
            elif row['Status'] == 'Meta Platinar': bg_cls = "bg-meta"
            elif row['Status'] == 'Abandonado': bg_cls = "bg-drop"
            
            capa, nome = row['Capa_URL'], row['Nome_Jogo']
            horas = row['Horas_Totais']
            perc = int(row['Porcentagem']) if pd.notnull(row['Porcentagem']) else 0
            feitos = int(row['Conquistas_Feitas']) if pd.notnull(row['Conquistas_Feitas']) else 0
            total = int(row['Conquistas_Total']) if pd.notnull(row['Conquistas_Total']) else 0
            
            card_html = f"""
<div class="card-hover">
    <div class="card-img-bg" style="background-image: url('{capa}');"></div>
    <div class="card-info-overlay">
        <div class="overlay-title">{nome}</div>
        <div class="overlay-stats">⏱️ {horas}h &nbsp;•&nbsp; 🏆 {feitos}/{total}</div>
        <div class="overlay-perc">{perc}%</div>
        <span class="mini-badge {bg_cls}">{row['Status']}</span>
    </div>
</div>"""
            html_content += card_html
        html_content += '</div>'
        st.markdown(html_content, unsafe_allow_html=True)

# === ABA 2: ORGANIZER ===
with aba_organizer:
    st.header("🗂️ Gerenciamento")
    df_org = db.carregar_historico()
    if not df_org.empty:
        edited_df = st.data_editor(
            df_org[['Nome_Jogo', 'Status', 'Horas_Totais', 'Porcentagem']],
            column_config={
                "Status": st.column_config.SelectboxColumn("Status", options=['Backlog', 'Meta Platinar', 'Platinado', 'Abandonado'], required=True),
                "Nome_Jogo": st.column_config.TextColumn("Jogo", disabled=True),
                "Horas_Totais": st.column_config.NumberColumn("Horas", disabled=True),
                "Porcentagem": st.column_config.ProgressColumn("Progresso", format="%d%%")
            }, hide_index=True, use_container_width=True, height=600
        )
        if st.button("💾 Salvar Alterações", type="primary"):
            db.salvar_lote_status(edited_df)
            st.success("Dados salvos!")
            time.sleep(1)
            st.rerun()

# === ABA 3: DATA LAB (COMPLETO) ===
with aba_ds:
    c_title, c_anim = st.columns([4, 1])
    with c_title:
        st.markdown("## 🔬 Data Lab Pro")
        st.markdown("Estatística Avançada + IA Gemini.")
    with c_anim: st_lottie(lottie_analytics, height=100) if lottie_analytics else None

    df = db.carregar_historico()
    gemini_key = st.session_state.get('gemini_key', '')

    st.markdown("---")
    if not gemini_key:
        st.warning("⚠️ Para ativar a IA, coloque sua API Key na aba 'Config'.")
    else:
        c_in, c_btn = st.columns([4, 1])
        pergunta = c_in.text_input("💬 Pergunte algo aos dados:", placeholder="Ex: Qual meu gênero favorito?")
        if c_btn.button("Enviar", type="primary"):
            with st.spinner("Analisando..."):
                st.chat_message("assistant", avatar="🧠").write(db.analista_real_ia(df, gemini_key, pergunta))
    st.markdown("---")

    if not df.empty and db.TEM_SKLEARN:
        if 'Cluster' not in df.columns: df = db.aplicar_clusterizacao(df)

        # ABAS DE ANÁLISE
        tab_matriz, tab_evolucao, tab_dist, tab_calor, tab_cluster, tab_pareto, tab_risco, tab_prev, tab_rec = st.tabs([
            "📊 Matriz", "📈 Evolução", "📦 Distribuição", "🔥 Mapa Calor", 
            "🤖 Clusters", "📉 Pareto", "⚠️ Risco", "📅 Previsão", "🔍 Recomendação"
        ])

        with tab_matriz:
            st.subheader("Matriz: Esforço vs Retorno")
            base = alt.Chart(df).encode(x='Horas_Totais', y='Porcentagem', tooltip=['Nome_Jogo'])
            points = base.mark_circle(size=100).encode(color=alt.Color('Status', scale=alt.Scale(domain=['Platinado', 'Meta Platinar', 'Backlog', 'Abandonado'], range=['#00E676', '#FF9100', '#2979FF', '#FF1744']))).interactive()
            st.altair_chart(points, use_container_width=True)
            if gemini_key and st.button("🧠 Explicar Matriz", key="ai_matriz"):
                st.info(db.analista_real_ia(df, gemini_key, "Analise a Matriz (Esforço x Retorno). Ache 'Quick Wins'. Ignore Platinados."))

        with tab_evolucao:
            st.subheader("Linha do Tempo")
            df_evo = df.dropna(subset=['Ultima_Vez_Jogado']).sort_values(by='Ultima_Vez_Jogado')
            line = alt.Chart(df_evo).mark_line(point=True).encode(x='Ultima_Vez_Jogado', y='Horas_Totais', color='Status', tooltip=['Nome_Jogo', 'Horas_Totais']).interactive()
            st.altair_chart(line, use_container_width=True)
            if gemini_key and st.button("🧠 Analisar Tendência", key="ai_evo"):
                st.info(db.analista_real_ia(df, gemini_key, "Analise a evolução temporal. Estou jogando jogos mais longos recentemente?"))

        with tab_dist:
            st.subheader("Boxplot")
            box = alt.Chart(df).mark_boxplot(extent='min-max').encode(x='Status', y=alt.Y('Horas_Totais', scale=alt.Scale(type='symlog')), color='Status').properties(height=400)
            st.altair_chart(box, use_container_width=True)
            if gemini_key and st.button("🧠 Explicar Distribuição", key="ai_dist"):
                st.info(db.analista_real_ia(df, gemini_key, "Analise o Boxplot. Existem outliers de tempo?"))

        with tab_calor:
            st.subheader("Status x Perfil")
            heat = alt.Chart(df).mark_rect().encode(x='Status', y='Perfil_Jogo', color=alt.Color('count()', scale=alt.Scale(scheme='inferno'))).properties(height=350)
            st.altair_chart(heat + heat.mark_text().encode(text='count()', color=alt.value('white')), use_container_width=True)
            if gemini_key and st.button("🧠 Interpretar Mapa", key="ai_map"):
                st.info(db.analista_real_ia(df, gemini_key, "Analise o Mapa de Calor. Onde está a concentração?"))

        with tab_cluster:
            st.subheader("Clusters AI")
            df_cl = db.aplicar_clusterizacao(df)
            chart = alt.Chart(df_cl).mark_circle(size=120).encode(x=alt.X('Horas_Totais', scale=alt.Scale(type='symlog')), y='Porcentagem', color='Perfil_Jogo', tooltip=['Nome_Jogo']).interactive()
            st.altair_chart(chart, use_container_width=True)
            if gemini_key and st.button("🧠 Meu Perfil", key="ai_clus"):
                st.info(db.analista_real_ia(df, gemini_key, "Defina minha personalidade gamer baseada nos clusters."))

        with tab_pareto:
            st.subheader("Pareto 80/20")
            df_par = db.analise_pareto(df)
            st.dataframe(df_par[df_par['Categoria_Pareto'] == 'Vital (Top 20%)'][['Nome_Jogo', 'Horas_Totais', 'Pareto_Perc']], use_container_width=True, hide_index=True)
            if gemini_key and st.button("🧠 Analisar Foco", key="ai_par"):
                st.info(db.analista_real_ia(df, gemini_key, "Analise o Pareto. Sou focado ou disperso?"))

        with tab_risco:
            st.subheader("Risco de Abandono")
            risco = db.analise_churn(df)
            for i, r in risco.head(5).iterrows(): st.warning(f"**{r['Nome_Jogo']}** parado há {int(r['Dias_Sem_Jogar'])} dias.")
            if gemini_key and st.button("🧠 Consultoria Churn", key="ai_churn"):
                st.error(db.analista_real_ia(df, gemini_key, "Analise o Risco de Abandono. Diga o que desinstalar."))

        with tab_prev:
            st.subheader("Forecasting")
            horas = st.slider("Horas/dia?", 1, 12, 2)
            prev = db.calculadora_previsao(df, horas)
            if not prev.empty:
                dias = int(prev['Dias_Para_Terminar'].sum())
                st.metric("Dias p/ Zerar", dias, delta=f"Fim: {(datetime.now()+timedelta(days=dias)).strftime('%d/%m/%Y')}")
                bars = alt.Chart(prev.reset_index()).mark_bar().encode(x='Dias_Para_Terminar', y=alt.Y('Nome_Jogo', sort='x'), color=alt.Color('Dias_Para_Terminar', scale=alt.Scale(scheme='teals')))
                st.altair_chart(bars, use_container_width=True)
                if gemini_key and st.button("🧠 Analisar Cronograma", key="ai_fore"):
                    st.success(db.analista_real_ia(df, gemini_key, f"Jogado {horas}h/dia, terminarei em {dias} dias. É realista?"))

        with tab_rec:
            st.subheader("Recomendação KNN")
            escolha = st.selectbox("Gostei de:", df['Nome_Jogo'].unique())
            if escolha and hasattr(db, 'recomendar_jogos_parecidos'):
                recs = db.recomendar_jogos_parecidos(df, escolha)
                cols = st.columns(3)
                for i, (j, s) in enumerate(recs):
                    if i < 3:
                        with cols[i]:
                            st.image(df[df['Nome_Jogo'] == j]['Capa_URL'].values[0])
                            st.caption(j)

    elif not db.TEM_SKLEARN: st.error("Instale scikit-learn.")

# === ABA 4: CONFIG ===
with aba_sync:
    st.header("⚙️ Configurações")
    c1, c2 = st.columns(2)
    id_in = c1.text_input("Steam ID", value=st.session_state['steam_cfg']['id'])
    key_in = c2.text_input("Steam API Key", value=st.session_state['steam_cfg']['key'], type="password")
    
    st.markdown("---")
    gemini_in = st.text_input("Google Gemini API Key (IA)", type="password", value=st.session_state.get('gemini_key', ''))
    if gemini_in: st.session_state['gemini_key'] = gemini_in
    
    if st.button("🚀 Sincronizar Tudo"):
        if id_in and key_in:
            sid = db.resolver_steam_id(key_in, id_in)
            if sid:
                st.session_state['steam_cfg']['id'] = sid
                st.session_state['steam_cfg']['key'] = key_in
                jogos, erro = db.buscar_jogos_api(key_in, sid, 10)
                if jogos:
                    db.salvar_no_historico(jogos)
                    st.success("Sincronizado!")
                    time.sleep(1)
                    st.rerun()