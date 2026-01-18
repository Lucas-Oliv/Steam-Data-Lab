import pandas as pd
import os
import requests
import google.generativeai as genai
from datetime import datetime

# --- CONFIGURAÇÕES ---
ARQUIVO_DB = 'meu_historico_games.csv'
BLOCKLIST_IDS = [431960, 228980, 1904150, 413080, 266410, 250820]
BLOCKLIST_TERMS = ['hentai', 'sex', 'porn', 'adult only', '18+', 'uncensored', 'nude', 'waifu', 'neko', 'sakura']

try:
    from sklearn.cluster import KMeans
    from sklearn.neighbors import NearestNeighbors
    TEM_SKLEARN = True
except ImportError:
    TEM_SKLEARN = False

# --- GERENCIAMENTO DE DADOS ---
def carregar_historico():
    colunas = ["Data_Registro", "Nome_Jogo", "Plataforma", "Horas_Totais", "Conquistas_Feitas", "Conquistas_Total", "Porcentagem", "Capa_URL", "AppID", "Status", "Ultima_Vez_Jogado"]
    if not os.path.exists(ARQUIVO_DB):
        df = pd.DataFrame(columns=colunas)
        df.to_csv(ARQUIVO_DB, index=False)
        return df
    df = pd.read_csv(ARQUIVO_DB)
    if 'Ultima_Vez_Jogado' not in df.columns: df['Ultima_Vez_Jogado'] = pd.NaT
    if 'Status' not in df.columns: df['Status'] = 'Backlog'
    return df

def salvar_no_historico(novos_dados_lista):
    df = carregar_historico()
    df_novos = pd.DataFrame(novos_dados_lista)
    if 'Status' not in df_novos.columns: df_novos['Status'] = 'Backlog'
    
    status_map = dict(zip(df['Nome_Jogo'], df['Status']))
    df_final = pd.concat([df, df_novos], ignore_index=True)
    df_final['Data_Registro'] = pd.to_datetime(df_final['Data_Registro'], errors='coerce')
    df_final = df_final.sort_values(by='Data_Registro')
    df_final = df_final.drop_duplicates(subset=['Nome_Jogo'], keep='last')
    
    for idx, row in df_final.iterrows():
        nome = row['Nome_Jogo']
        perc = row['Porcentagem']
        if perc == 100: df_final.at[idx, 'Status'] = 'Platinado'
        elif nome in status_map: df_final.at[idx, 'Status'] = status_map[nome]
            
    df_final.to_csv(ARQUIVO_DB, index=False)
    return df_final

def salvar_lote_status(df_editado):
    df_original = carregar_historico()
    for idx, row in df_editado.iterrows():
        df_original.loc[df_original['Nome_Jogo'] == row['Nome_Jogo'], 'Status'] = row['Status']
    df_original.to_csv(ARQUIVO_DB, index=False)
    return True

# --- API STEAM ---
def resolver_steam_id(api_key, input_usuario):
    input_usuario = input_usuario.strip()
    if input_usuario.isdigit(): return input_usuario
    if "steamcommunity.com" in input_usuario:
        if "/id/" in input_usuario: input_usuario = input_usuario.split("/id/")[-1].replace("/", "")
        elif "/profiles/" in input_usuario: return input_usuario.split("/profiles/")[-1].replace("/", "")
    try:
        r = requests.get("http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/", params={'key': api_key, 'vanityurl': input_usuario}, timeout=5)
        data = r.json().get('response', {})
        if data.get('success') == 1: return data.get('steamid')
    except: return None
    return None

def get_steam_profile(api_key, steam_id):
    try:
        r_sum = requests.get("http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/", params={'key': api_key, 'steamids': steam_id}, timeout=5)
        if r_sum.status_code != 200: return None
        data = r_sum.json().get('response', {}).get('players', [])
        if not data: return None
        data_sum = data[0]
        
        avatar_url = data_sum.get('avatarfull', '') or "https://avatars.steamstatic.com/fef49e7fa7e1997310d705b2a6158ff8dc1cdfeb_full.jpg"
            
        xp_atual, xp_prox, perc_xp, level, total_badges = 0, 0, 0, 0, 0
        badges_recentes = []
        try:
            r_badges = requests.get("http://api.steampowered.com/IPlayerService/GetBadges/v1/", params={'key': api_key, 'steamid': steam_id}, timeout=5)
            if r_badges.status_code == 200:
                d = r_badges.json().get('response', {})
                level = d.get('player_level', 0)
                xp_atual = d.get('player_xp', 0)
                xp_prox = d.get('player_xp_needed_to_level_up', 0)
                xp_total = xp_atual + xp_prox
                if xp_total > 0: perc_xp = round((xp_atual / xp_total) * 100)
                
                all_badges = d.get('badges', [])
                total_badges = len(all_badges)
                badges_com_data = [b for b in all_badges if 'completion_time' in b]
                badges_recentes = sorted(badges_com_data, key=lambda x: x['completion_time'], reverse=True)[:5]
        except: pass
        
        return {
            "persona": data_sum.get('personaname', 'Jogador'),
            "avatar": avatar_url,
            "country": data_sum.get('loccountrycode', 'BR'),
            "level": level, "xp_atual": xp_atual, "xp_prox": xp_prox, "xp_perc": perc_xp, 
            "total_badges": total_badges, "recent_badges": badges_recentes
        }
    except: return None

def buscar_jogos_api(api_key, steam_id, corte_minimo):
    try:
        resp = requests.get("http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/", params={'key': api_key, 'steamid': steam_id, 'format': 'json', 'include_appinfo': '1', 'include_played_free_games': '1'}, timeout=15)
        if resp.status_code != 200: return None, f"Erro API: {resp.status_code}"
        data = resp.json()
        if 'response' not in data or 'games' not in data['response']: return None, "Nenhum jogo."
        
        todos = data['response']['games']
        finais = []
        hoje = datetime.now().strftime("%Y-%m-%d")
        url_conq = "http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/"
        
        for game in todos:
            appid = game.get('appid')
            if appid in BLOCKLIST_IDS: continue
            if any(termo in game.get('name', '').lower() for termo in BLOCKLIST_TERMS): continue
            minutos = game.get('playtime_forever', 0)
            if minutos == 0: continue 
            
            last_ts = game.get('rtime_last_played', 0)
            last_str = datetime.fromtimestamp(last_ts).strftime("%Y-%m-%d") if last_ts > 0 else ""
            try:
                r_c = requests.get(url_conq, params={'appid': appid, 'key': api_key, 'steamid': steam_id}, timeout=1.5)
                feitos, total, perc = 0, 0, 0.0
                if r_c.status_code == 200:
                    d_c = r_c.json()
                    if 'playerstats' in d_c and 'achievements' in d_c['playerstats']:
                        lst = d_c['playerstats']['achievements']
                        total = len(lst)
                        feitos = sum(1 for a in lst if a.get('achieved') == 1)
                        if total > 0: perc = round((feitos/total)*100, 1)
                st_ini = 'Platinado' if perc == 100 else 'Backlog'
                if perc >= corte_minimo:
                    capa = f"https://shared.fastly.steamstatic.com/store_item_assets/steam/apps/{appid}/header.jpg"
                    finais.append({
                        "Data_Registro": hoje, "Nome_Jogo": game.get('name'), "Plataforma": "Steam",
                        "Horas_Totais": round(minutos/60, 1), "Conquistas_Feitas": feitos,
                        "Conquistas_Total": total, "Porcentagem": perc, "Capa_URL": capa, "AppID": appid, 
                        "Status": st_ini, "Ultima_Vez_Jogado": last_str
                    })
            except: continue
        return finais, None
    except Exception as e: return None, str(e)

# --- IA, DATA SCIENCE & RECOMENDAÇÃO ---
def analista_real_ia(df, api_key, pergunta_personalizada=None):
    if not api_key: return "⚠️ Erro: Insira sua chave Gemini na aba Configurações."
    try:
        genai.configure(api_key=api_key)
        # Detecção de modelo
        modelos_disp = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if not modelos_disp: return "Erro: Sua chave não tem acesso a modelos de texto."
        
        preferencias = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro', 'models/gemini-1.0-pro']
        escolhido = next((p for p in preferencias if p in modelos_disp), modelos_disp[0])
        model = genai.GenerativeModel(escolhido)
        
        # Prepara dados (Top 40 para economizar tokens)
        dados_csv = df[['Nome_Jogo', 'Horas_Totais', 'Porcentagem', 'Status']].sort_values(by='Horas_Totais', ascending=False).head(40).to_csv(index=False)
        estats = df.describe().to_string()
        
        ctx = f"Pergunta: '{pergunta_personalizada}'" if pergunta_personalizada else "Análise geral e sarcástica."
        prompt = f"Data Scientist Gamer Sênior. Dados:\n{dados_csv}\nStats: {estats}\nTarefa: {ctx}\nRegras: Direto, use emojis e Markdown."
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e: return f"Erro na IA: {str(e)}"

def aplicar_clusterizacao(df):
    if not TEM_SKLEARN or len(df) < 5: return df
    X = df[['Horas_Totais', 'Porcentagem']].copy()
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df['Cluster'] = kmeans.fit_predict(X)
    media_h = df['Horas_Totais'].mean()
    stats = df.groupby('Cluster')[['Horas_Totais', 'Porcentagem']].mean()
    nomes = {}
    for cid, row in stats.iterrows():
        if row['Horas_Totais'] > media_h * 1.5: nomes[cid] = "🔥 Hardcore"
        elif row['Porcentagem'] > 80: nomes[cid] = "💎 Completionist"
        elif row['Porcentagem'] < 30 and row['Horas_Totais'] < 10: nomes[cid] = "🎲 Casual"
        else: nomes[cid] = "⚖️ Padrão"
    df['Perfil_Jogo'] = df['Cluster'].map(nomes).fillna("Outro")
    return df

def recomendar_jogos_parecidos(df, nome_jogo_alvo):
    if not TEM_SKLEARN or df.empty: return []
    try:
        features = df[['Horas_Totais', 'Porcentagem']].copy()
        model = NearestNeighbors(n_neighbors=4, algorithm='auto').fit(features)
        jogo_alvo = df[df['Nome_Jogo'] == nome_jogo_alvo]
        if jogo_alvo.empty: return []
        
        distances, indices = model.kneighbors(jogo_alvo[['Horas_Totais', 'Porcentagem']].values)
        recomendacoes = []
        for i in range(1, len(indices[0])):
            idx = indices[0][i]
            nome = df.iloc[idx]['Nome_Jogo']
            sim = 100 - (distances[0][i] * 100)
            recomendacoes.append((nome, max(0, sim)))
        return recomendacoes
    except: return []

def analise_pareto(df):
    df_par = df.sort_values(by='Horas_Totais', ascending=False).copy()
    df_par['Acumulado'] = df_par['Horas_Totais'].cumsum()
    total = df_par['Horas_Totais'].sum()
    df_par['Pareto_Perc'] = (df_par['Acumulado'] / total) * 100
    df_par['Categoria_Pareto'] = df_par['Pareto_Perc'].apply(lambda x: 'Vital (Top 20%)' if x <= 80 else 'Trivial (Bottom 80%)')
    return df_par

def analise_churn(df):
    if 'Ultima_Vez_Jogado' not in df.columns: return pd.DataFrame()
    df['dt_last'] = pd.to_datetime(df['Ultima_Vez_Jogado'], errors='coerce')
    hoje = pd.to_datetime(datetime.now())
    df['Dias_Sem_Jogar'] = (hoje - df['dt_last']).dt.days
    risco = df[(df['Porcentagem'] < 100) & (df['Horas_Totais'] > 5) & (df['Dias_Sem_Jogar'] > 30) & (df['Dias_Sem_Jogar'] < 365)].sort_values(by='Dias_Sem_Jogar')
    return risco

def calculadora_previsao(df, horas_por_dia=2):
    pend = df[(df['Status'].isin(['Meta Platinar', 'Backlog'])) & (df['Porcentagem'] > 0) & (df['Porcentagem'] < 100)].copy()
    if pend.empty: return pd.DataFrame()
    pend['Estimativa'] = pend.apply(lambda x: (x['Horas_Totais'] * 100) / x['Porcentagem'] if x['Porcentagem'] > 0 else 0, axis=1)
    pend['Horas_Restantes'] = pend['Estimativa'] - pend['Horas_Totais']
    pend = pend[pend['Horas_Restantes'] > 0]
    pend['Dias_Para_Terminar'] = pend['Horas_Restantes'] / horas_por_dia
    return pend[['Nome_Jogo', 'Horas_Totais', 'Porcentagem', 'Horas_Restantes', 'Dias_Para_Terminar']].sort_values('Dias_Para_Terminar')