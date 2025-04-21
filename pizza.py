import streamlit as st
import sqlite3
import pandas as pd
import datetime
import base64
import warnings
from streamlit.runtime.scriptrunner import ScriptRunContext

warnings.filterwarnings("ignore", category=UserWarning, message="missing ScriptRunContext")

# Criar contexto fake se necessário
try:
    from streamlit.runtime.scriptrunner import get_script_run_ctx
    if not get_script_run_ctx():
        ctx = ScriptRunContext()
        ctx.script_requests = []
except:
    pass

# Configuração inicial da página
st.set_page_config(page_title="Sistema de Vendas de Pizzas", layout="wide")

# Configurações de autenticação (em produção, use um sistema mais seguro!)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "pizza123"

# Função para verificar login
def check_login(username, password):
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

# Tela de Login
def login_screen():
    st.title("🍕 Sistema de Vendas de Pizzas")
    
    # Layout bonito para a tela de login
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        with st.container(border=True):
            st.markdown("""
            <style>
                .login-title {
                    text-align: center;
                    color: #FF5733;
                    font-size: 28px;
                    margin-bottom: 30px;
                }
                .stButton>button {
                    width: 100%;
                    background-color: #FF5733;
                    color: white;
                }
            </style>
            <div class='login-title'>Acesso Administrativo</div>
            """, unsafe_allow_html=True)
            
            username = st.text_input("Usuário", key="username")
            password = st.text_input("Senha", type="password", key="password")
            
            if st.button("Entrar"):
                if check_login(username, password):
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Credenciais inválidas. Tente novamente.")

# Tela inicial bonita
def welcome_screen():
    st.title("🍕 Bem-vindo ao Sistema de Vendas de Pizzas!")
    
    st.markdown("""
    <style>
        .welcome-container {
            background-color: #FFF5F0;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .welcome-title {
            color: #FF5733;
            text-align: center;
            font-size: 32px;
        }
        .welcome-text {
            font-size: 18px;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="welcome-title">Sistema de Gerenciamento de Vendas</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="welcome-text">
        <p>Gerencie seus pedidos, acompanhe vendas e controle estoque de forma eficiente.</p>
        <p>Para acessar o sistema, faça login como administrador.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Acessar Painel Administrativo"):
            st.session_state.show_login = True
            st.rerun()

# Funções de banco de dados
def init_db():
    conn = sqlite3.connect('pizza.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS orders
                 (id TEXT PRIMARY KEY,
                  timestamp TEXT,
                  sellerName TEXT,
                  frangoComCebola INTEGER,
                  frangoSemCebola INTEGER,
                  calabresaComCebola INTEGER,
                  calabresaSemCebola INTEGER,
                  pickupTime TEXT,
                  observations TEXT,
                  paymentProof TEXT,
                  paymentChecked INTEGER,
                  deliveredToSeller INTEGER,
                  deliveredToCustomer INTEGER)''')
    conn.commit()
    conn.close()

def get_all_orders():
    conn = sqlite3.connect('pizza.db')
    df = pd.read_sql_query("SELECT * FROM orders", conn)
    conn.close()
    return df

def save_order(order_id, order_data):
    conn = sqlite3.connect('pizza.db')
    c = conn.cursor()
    order_data['paymentChecked'] = int(order_data.get('paymentChecked', False))
    order_data['deliveredToSeller'] = int(order_data.get('deliveredToSeller', False))
    order_data['deliveredToCustomer'] = int(order_data.get('deliveredToCustomer', False))
    
    c.execute("SELECT id FROM orders WHERE id=?", (order_id,))
    exists = c.fetchone()
    
    if exists:
        query = '''UPDATE orders SET
                   timestamp=?,
                   sellerName=?,
                   frangoComCebola=?,
                   frangoSemCebola=?,
                   calabresaComCebola=?,
                   calabresaSemCebola=?,
                   pickupTime=?,
                   observations=?,
                   paymentProof=?,
                   paymentChecked=?,
                   deliveredToSeller=?,
                   deliveredToCustomer=?
                   WHERE id=?'''
        params = (
            order_data['timestamp'],
            order_data['sellerName'],
            order_data['frangoComCebola'],
            order_data['frangoSemCebola'],
            order_data['calabresaComCebola'],
            order_data['calabresaSemCebola'],
            order_data['pickupTime'],
            order_data.get('observations', ''),
            order_data.get('paymentProof', ''),
            order_data['paymentChecked'],
            order_data['deliveredToSeller'],
            order_data['deliveredToCustomer'],
            order_id
        )
    else:
        query = '''INSERT INTO orders VALUES
                   (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''
        params = (
            order_id,
            order_data['timestamp'],
            order_data['sellerName'],
            order_data['frangoComCebola'],
            order_data['frangoSemCebola'],
            order_data['calabresaComCebola'],
            order_data['calabresaSemCebola'],
            order_data['pickupTime'],
            order_data.get('observations', ''),
            order_data.get('paymentProof', ''),
            order_data['paymentChecked'],
            order_data['deliveredToSeller'],
            order_data['deliveredToCustomer']
        )
    
    c.execute(query, params)
    conn.commit()
    conn.close()

def delete_order(order_id):
    conn = sqlite3.connect('pizza.db')
    c = conn.cursor()
    c.execute("DELETE FROM orders WHERE id=?", (order_id,))
    conn.commit()
    conn.close()

# Função para calcular os totais
def calculate_totals(orders_df):
    totals = {}
    totals['frangoComCebola'] = orders_df['frangoComCebola'].sum()
    totals['frangoSemCebola'] = orders_df['frangoSemCebola'].sum()
    totals['calabresaComCebola'] = orders_df['calabresaComCebola'].sum()
    totals['calabresaSemCebola'] = orders_df['calabresaSemCebola'].sum()
    totals['totalPizzas'] = totals['frangoComCebola'] + totals['frangoSemCebola'] + totals['calabresaComCebola'] + totals['calabresaSemCebola']
    totals['retiradas9'] = len(orders_df[orders_df['pickupTime'] == 'entre 9 e 10'])
    totals['retiradas10'] = len(orders_df[orders_df['pickupTime'] == 'entre 10 e 11'])
    totals['retiradas11'] = len(orders_df[orders_df['pickupTime'] == 'entre 11 e 12'])
    totals['retiradas12'] = len(orders_df[orders_df['pickupTime'] == 'entre 12 e 13'])
    totals['pagamentosCorretos'] = orders_df['paymentChecked'].sum()
    totals['pagamentosIncorretos'] = (~orders_df['paymentChecked'].astype(bool)).sum()
    totals['pagamentosNaoConferidos'] = orders_df['paymentChecked'].isna().sum()
    totals['entreguesVendedor'] = orders_df['deliveredToSeller'].sum()
    totals['naoEntreguesVendedor'] = (~orders_df['deliveredToSeller'].astype(bool)).sum()
    totals['entreguesCliente'] = orders_df['deliveredToCustomer'].sum()
    totals['naoEntreguesCliente'] = (~orders_df['deliveredToCustomer'].astype(bool)).sum()
    totals['totalCebolas'] = totals['frangoComCebola'] + totals['calabresaComCebola']
    totals['totalMussarela'] = 0.3 * totals['totalPizzas']
    totals['totalMassaTomate'] = 0.4 * totals['totalPizzas']
    totals['totalFrango'] = 0.4 * (totals['frangoComCebola'] + totals['frangoSemCebola'])
    totals['totalCalabresa'] = 0.2 * (totals['calabresaComCebola'] + totals['calabresaSemCebola'])
    return totals

def get_csv_download_link(df, filename):
    csv = df.to_csv(index=False, sep=';')
    b64 = base64.b64encode(csv.encode()).decode()
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}">Baixar arquivo CSV</a>'

# Página principal do sistema
def main_app():
    # Inicializar banco de dados
    init_db()
    
    # Barra de logout no topo
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("🍕 Sistema de Vendas de Pizzas")
    with col2:
        if st.button("Sair"):
            st.session_state.logged_in = False
            st.session_state.show_login = False
            st.rerun()
    
    # Carregar pedidos do banco de dados
    orders_df = get_all_orders()

    # Inicializar estado do formulário
    if 'form_data' not in st.session_state:
        st.session_state.form_data = {
            'seller_name': "",
            'pickup_time': "entre 9 e 10",
            'observations': "",
            'payment_proof': "",
            'frango_com': 0,
            'frango_sem': 0,
            'calabresa_com': 0,
            'calabresa_sem': 0,
            'payment_checked': False,
            'delivered_seller': False,
            'delivered_customer': False
        }

    if 'editing_order_id' not in st.session_state:
        st.session_state.editing_order_id = None

    # Formulário para novo pedido
    with st.expander("📝 Novo Pedido", expanded=True):
        with st.form("order_form"):
            col1, col2 = st.columns(2)
            with col1:
                seller_name = st.text_input("Vendedor", value=st.session_state.form_data['seller_name'])
                pickup_time = st.selectbox(
                    "Horário de Retirada",
                    ["entre 9 e 10", "entre 10 e 11", "entre 11 e 12", "entre 12 e 13"],
                    index=["entre 9 e 10", "entre 10 e 11", "entre 11 e 12", "entre 12 e 13"].index(
                        st.session_state.form_data['pickup_time'])
                )
            with col2:
                observations = st.text_input("Observações", value=st.session_state.form_data['observations'])
                payment_proof = st.text_input("Comprovante (URL)", value=st.session_state.form_data['payment_proof'])
            
            col3, col4, col5, col6 = st.columns(4)
            with col3:
                frango_com = st.number_input("Frango COM cebola", min_value=0, value=st.session_state.form_data['frango_com'])
            with col4:
                frango_sem = st.number_input("Frango SEM cebola", min_value=0, value=st.session_state.form_data['frango_sem'])
            with col5:
                calabresa_com = st.number_input("Calabresa COM cebola", min_value=0, value=st.session_state.form_data['calabresa_com'])
            with col6:
                calabresa_sem = st.number_input("Calabresa SEM cebola", min_value=0, value=st.session_state.form_data['calabresa_sem'])
            
            status_col1, status_col2, status_col3 = st.columns(3)
            with status_col1:
                payment_checked = st.checkbox("Pagamento Conferido", value=st.session_state.form_data['payment_checked'])
            with status_col2:
                delivered_seller = st.checkbox("Entregue ao Vendedor", value=st.session_state.form_data['delivered_seller'])
            with status_col3:
                delivered_customer = st.checkbox("Entregue ao Cliente", value=st.session_state.form_data['delivered_customer'])
            
            submitted = st.form_submit_button("Salvar Pedido")
            if submitted:
                if not seller_name or not pickup_time:
                    st.error("Vendedor e Horário de Retirada são obrigatórios!")
                else:
                    order_data = {
                        'timestamp': datetime.datetime.now().isoformat(),
                        'sellerName': seller_name,
                        'frangoComCebola': frango_com,
                        'frangoSemCebola': frango_sem,
                        'calabresaComCebola': calabresa_com,
                        'calabresaSemCebola': calabresa_sem,
                        'pickupTime': pickup_time,
                        'observations': observations,
                        'paymentProof': payment_proof,
                        'paymentChecked': payment_checked,
                        'deliveredToSeller': delivered_seller,
                        'deliveredToCustomer': delivered_customer
                    }
                    
                    order_id = st.session_state.editing_order_id or str(datetime.datetime.now().timestamp())
                    save_order(order_id, order_data)
                    
                    # Resetar o formulário
                    st.session_state.form_data = {
                        'seller_name': "",
                        'pickup_time': "entre 9 e 10",
                        'observations': "",
                        'payment_proof': "",
                        'frango_com': 0,
                        'frango_sem': 0,
                        'calabresa_com': 0,
                        'calabresa_sem': 0,
                        'payment_checked': False,
                        'delivered_seller': False,
                        'delivered_customer': False
                    }
                    
                    if st.session_state.editing_order_id:
                        st.session_state.editing_order_id = None
                        st.success("Pedido atualizado com sucesso!")
                    else:
                        st.success("Pedido adicionado com sucesso!")
                    
                    # Atualizar dados
                    orders_df = get_all_orders()

    # Seção de Resumo
    st.subheader("📊 Resumo de Vendas")
    if not orders_df.empty:
        totals = calculate_totals(orders_df)
    else:
        totals = {
            'frangoComCebola': 0, 'frangoSemCebola': 0, 'calabresaComCebola': 0, 'calabresaSemCebola': 0,
            'totalPizzas': 0, 'retiradas9': 0, 'retiradas10': 0, 'retiradas11': 0, 'retiradas12': 0,
            'pagamentosCorretos': 0, 'pagamentosIncorretos': 0, 'pagamentosNaoConferidos': 0,
            'entreguesVendedor': 0, 'naoEntreguesVendedor': 0, 'entreguesCliente': 0, 'naoEntreguesCliente': 0,
            'totalCebolas': 0, 'totalMussarela': 0, 'totalMassaTomate': 0, 'totalFrango': 0, 'totalCalabresa': 0
        }

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Totais de Pizzas")
        st.metric("Frango COM cebola", totals['frangoComCebola'])
        st.metric("Frango SEM cebola", totals['frangoSemCebola'])
        st.metric("Calabresa COM cebola", totals['calabresaComCebola'])
        st.metric("Calabresa SEM cebola", totals['calabresaSemCebola'])
        st.metric("Total Pizzas", totals['totalPizzas'])

    with col2:
        st.markdown("### Retiradas por Horário")
        st.metric("9-10", totals['retiradas9'])
        st.metric("10-11", totals['retiradas10'])
        st.metric("11-12", totals['retiradas11'])
        st.metric("12-13", totals['retiradas12'])

    st.subheader("🧾 Controle de Qualidade")
    col3, col4 = st.columns(2)
    with col3:
        st.metric("Pagamentos Corretos", totals['pagamentosCorretos'])
        st.metric("Pagamentos Incorretos", totals['pagamentosIncorretos'])
        st.metric("Pagamentos Não Conferidos", totals['pagamentosNaoConferidos'])

    with col4:
        st.metric("Entregues ao Vendedor", totals['entreguesVendedor'])
        st.metric("Não Entregues ao Vendedor", totals['naoEntreguesVendedor'])
        st.metric("Entregues ao Cliente", totals['entreguesCliente'])
        st.metric("Não Entregues ao Cliente", totals['naoEntreguesCliente'])

    st.subheader("🧂 Necessidade de Ingredientes")
    col5, col6, col7 = st.columns(3)
    with col5:
        st.metric("Cabeças de Cebola", totals['totalCebolas'])
        st.metric("Quilos de Mussarela", f"{totals['totalMussarela']:.2f} kg")
    with col6:
        st.metric("Quilos de Massa/Tomate", f"{totals['totalMassaTomate']:.2f} kg")
        st.metric("Quilos de Frango", f"{totals['totalFrango']:.2f} kg")
    with col7:
        st.metric("Quilos de Calabresa", f"{totals['totalCalabresa']:.2f} kg")

    # Botão de exportação
    st.markdown("### Exportar Dados")
    if not orders_df.empty:
        st.markdown(get_csv_download_link(orders_df, "vendas_pizzas.csv"), unsafe_allow_html=True)
    else:
        st.warning("Nenhum pedido cadastrado para exportar")

    # Lista de Pedidos
    st.subheader("📋 Pedidos Registrados")

    # Opções de ordenação
    sort_option = st.selectbox(
        "Ordenar por",
        ["Data (Mais Recente)", "Data (Mais Antigo)", "Vendedor (A-Z)", "Vendedor (Z-A)"]
    )

    # Aplicar ordenação
    if not orders_df.empty:
        if sort_option == "Data (Mais Recente)":
            orders_sorted = orders_df.sort_values('timestamp', ascending=False)
        elif sort_option == "Data (Mais Antigo)":
            orders_sorted = orders_df.sort_values('timestamp', ascending=True)
        elif sort_option == "Vendedor (A-Z)":
            orders_sorted = orders_df.sort_values('sellerName', ascending=True)
        else:  # "Vendedor (Z-A)"
            orders_sorted = orders_df.sort_values('sellerName', ascending=False)
    else:
        orders_sorted = pd.DataFrame()

    # Exibir tabela de pedidos
    if not orders_sorted.empty:
        for _, row in orders_sorted.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**Vendedor:** {row['sellerName']} | **Data:** {pd.to_datetime(row['timestamp']).strftime('%d/%m/%Y %H:%M')}")
                    st.markdown(f"**Frango C/Cebola:** {row['frangoComCebola']} | **Frango S/Cebola:** {row['frangoSemCebola']}")
                    st.markdown(f"**Calabresa C/Cebola:** {row['calabresaComCebola']} | **Calabresa S/Cebola:** {row['calabresaSemCebola']}")
                    st.markdown(f"**Retirada:** {row['pickupTime']}")
                    if pd.notna(row['observations']) and row['observations'] != '':
                        st.markdown(f"**Observações:** {row['observations']}")
                    
                    # Status
                    status = []
                    if row['paymentChecked']:
                        status.append("✅ Pago")
                    if row['deliveredToSeller']:
                        status.append("🚚 Vendedor")
                    if row['deliveredToCustomer']:
                        status.append("🏠 Cliente")
                    if status:
                        st.markdown("**Status:** " + " | ".join(status))
                
                with col2:
                    # Botões de ação
                    if st.button("✏️ Editar", key=f"edit_{row['id']}"):
                        st.session_state.editing_order_id = row['id']
                        st.session_state.form_data = {
                            'seller_name': row['sellerName'],
                            'pickup_time': row['pickupTime'],
                            'observations': row['observations'] if pd.notna(row['observations']) else "",
                            'payment_proof': row['paymentProof'] if pd.notna(row['paymentProof']) else "",
                            'frango_com': row['frangoComCebola'],
                            'frango_sem': row['frangoSemCebola'],
                            'calabresa_com': row['calabresaComCebola'],
                            'calabresa_sem': row['calabresaSemCebola'],
                            'payment_checked': bool(row['paymentChecked']),
                            'delivered_seller': bool(row['deliveredToSeller']),
                            'delivered_customer': bool(row['deliveredToCustomer'])
                        }
                        st.rerun()
                    
                    if st.button("🗑️ Excluir", key=f"delete_{row['id']}"):
                        delete_order(row['id'])
                        st.success("Pedido excluído com sucesso!")
                        st.rerun()
    else:
        st.info("Nenhum pedido cadastrado ainda.")

# Fluxo principal do aplicativo
def main():
    # Inicializar estados da sessão
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'show_login' not in st.session_state:
        st.session_state.show_login = False
    
    # Mostrar a tela apropriada
    if st.session_state.logged_in:
        main_app()
    elif st.session_state.show_login:
        login_screen()
    else:
        welcome_screen()

if __name__ == "__main__":
    main()
