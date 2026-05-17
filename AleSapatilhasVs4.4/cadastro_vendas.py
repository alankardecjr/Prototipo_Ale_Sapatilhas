import tkinter as tk
from tkinter import messagebox, ttk
import database 
import ui_utils
from datetime import datetime

class JanelaCadastroVendas(tk.Toplevel):
    def __init__(self, master, cliente_selecionado=None, dados_venda=None):
        super().__init__(master)
        self.master = master
        self.title("Alê Sapatilhas - Checkout de Vendas")
        
        # --- Configurações de Janela Modal ---
        self.transient(master)
        self.grab_set()
        self.focus_set()

        ui_utils.calcular_dimensoes_janela(self, maximizar=True)
        paleta = ui_utils.get_paleta()
        self.bg_fundo = paleta["bg_fundo"]
        self.bg_card = paleta["bg_card"]
        self.cor_borda = paleta["cor_borda"]
        self.cor_texto = paleta["cor_texto"]
        self.cor_destaque = paleta["cor_destaque"]
        self.cor_btn_menu = paleta["cor_btn_menu"]
        self.cor_btn_sair = paleta["cor_btn_sair"]
        self.cor_hover_btn = paleta["cor_hover_btn"]
        
        self.configure(bg=self.bg_fundo)
        
        # --- Variáveis de Controle ---
        self.cliente_atual = cliente_selecionado
        self.carrinho_itens = {} 
        self.modo_atual = "vendas"

        self.configurar_estilos()
        self.setup_layout()

        # --- Inicialização de Dados ---
        if self.cliente_atual:
            # cliente_selecionado geralmente vem como (id, nome, tel) da main
            self.carregar_dados_cliente_completo(self.cliente_atual[0])
        
        self.listar_estoque_completo()

    def configurar_estilos(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("PDV.Treeview", background=self.bg_card, foreground=self.cor_texto, 
                             rowheight=30, font=("Segoe UI", 10))
        self.style.configure("PDV.Treeview.Heading", font=("Segoe UI", 10, "bold"), background=self.bg_card)
        self.style.map("PDV.Treeview", background=[('selected', self.cor_destaque)])

    def executar_comando_menu(self, comando, modo):
        """Gerencia a execução de comandos da sidebar"""
        if comando:
            comando()

    def aplicar_hover(self, btn):
        btn.bind("<Enter>", lambda e: btn.config(bg=self.cor_hover_btn))
        btn.bind("<Leave>", lambda e: btn.config(bg=self.cor_btn_menu))

    def setup_layout(self):
        # --- Sidebar ---
        self.sidebar = tk.Frame(self, bg=self.cor_btn_sair, width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        tk.Label(self.sidebar, text="ALÊ\nSAPATILHAS", font=("Segoe UI", 16, "bold"), 
                 bg=self.cor_btn_sair, fg="white", pady=20).pack()
    
        btn_estilo = {
            "font": ("Segoe UI", 10, "bold"), "bg": self.cor_btn_menu, "fg": "white",
            "relief": "flat", "cursor": "hand2", "anchor": "w", "padx": 20, "pady": 10
        }

        botoes = [
            ("💰 FINALIZAR VENDA", self.finalizar_venda, "vendas"),
            ("❌ REMOVER ITEM", self.remover_do_carrinho, "vendas"),
            ("", None, None), 
            ("👤 NOVO CLIENTE", self.abrir_novo_cliente, "clientes"),
            ("📦 NOVO PRODUTO", self.abrir_cadastro_produto, "produtos"),
            ("🔄 ATUALIZAR", self.listar_estoque_completo, None),
            ("", None, None),
            ("🚪SAIR", self.destroy, None)
        ]

        for texto, comando, modo in botoes:
            if texto == "":
                tk.Label(self.sidebar, bg=self.cor_btn_sair, pady=5).pack()
                continue

            btn = tk.Button(self.sidebar, text=texto, 
                            command=lambda c=comando, m=modo: self.executar_comando_menu(c, m), **btn_estilo)
            btn.pack(fill="x", pady=2)
            self.aplicar_hover(btn)

        # --- Container Principal ---
        self.main_container = tk.Frame(self, bg=self.bg_fundo, padx=20, pady=10)
        self.main_container.pack(side="right", fill="both", expand=True)

        self.setup_sessao_cliente()

        self.colunas_frame = tk.Frame(self.main_container, bg=self.bg_fundo)
        self.colunas_frame.pack(fill="both", expand=True, pady=10)

        self.setup_sessao_produtos(self.colunas_frame)
        self.setup_sessao_carrinho(self.colunas_frame)

    def setup_sessao_cliente(self):
        frame_cli = tk.Frame(self.main_container, bg=self.bg_fundo)
        frame_cli.pack(fill="x")

        f_busca = tk.Frame(frame_cli, bg=self.bg_fundo)
        f_busca.pack(side="left", fill="y")
        
        tk.Label(f_busca, text="BUSCAR CLIENTE", font=("Segoe UI", 8, "bold"), bg=self.bg_fundo).pack(anchor="w")
        self.ent_busca_cli = tk.Entry(f_busca, font=("Segoe UI", 10), width=30, highlightthickness=1)
        self.ent_busca_cli.pack(pady=2)
        self.ent_busca_cli.bind("<KeyRelease>", lambda e: self.buscar_cliente_db())
        self.ent_busca_cli.bind("<FocusIn>", lambda e: self.ent_busca_cli.config(highlightbackground=self.cor_destaque))

        self.tree_cli = ttk.Treeview(f_busca, columns=("nome"), show="headings", height=3, style="PDV.Treeview")
        self.tree_cli.heading("nome", text="NOME")
        self.tree_cli.column("nome", width=250)
        self.tree_cli.pack()
        self.tree_cli.bind("<<TreeviewSelect>>", self.selecionar_cliente_busca)

        self.frame_dados_detalhados = tk.LabelFrame(frame_cli, text=" 👤 DADOS DO CLIENTE ", 
                                                    bg=self.bg_card, fg=self.cor_texto, font=("Segoe UI", 9, "bold"))
        self.frame_dados_detalhados.pack(side="right", fill="both", expand=True, padx=(20, 0))

        self.txt_dados_cliente = tk.Text(self.frame_dados_detalhados, font=("Segoe UI", 10), 
                                         height=6, bg=self.bg_card, relief="flat", state="disabled")
        self.txt_dados_cliente.pack(fill="both", expand=True, padx=10, pady=5)

    def setup_sessao_produtos(self, parent):
        f_prod = tk.LabelFrame(parent, text=" 👠 LISTA DE PRODUTOS ", bg=self.bg_fundo, fg=self.cor_texto, font=("Segoe UI", 9, "bold"))
        f_prod.pack(side="left", fill="both", expand=True, padx=(0, 10))

        barra_busca = tk.Frame(f_prod, bg=self.bg_fundo)
        barra_busca.pack(fill="x", padx=5, pady=5)
        
        self.ent_busca_prod = tk.Entry(barra_busca, font=("Segoe UI", 10), highlightthickness=1)
        self.ent_busca_prod.pack(side="left", fill="x", expand=True)
        
        placeholder = "Pesquisar produto..."
        self.ent_busca_prod.insert(0, placeholder)
        self.ent_busca_prod.bind("<FocusIn>", lambda e: self._clear_placeholder(placeholder))
        self.ent_busca_prod.bind("<FocusOut>", lambda e: self._add_placeholder(placeholder))
        self.ent_busca_prod.bind("<KeyRelease>", lambda e: self.filtrar_produtos())

        cols = ("id", "prod", "cor", "tam", "preco", "qtd")
        self.tree_estoque = ttk.Treeview(f_prod, columns=cols, show="headings", style="PDV.Treeview")
        for col in cols:
            self.tree_estoque.heading(col, text=col.upper())
            self.tree_estoque.column(col, width=70, anchor="center")
        self.tree_estoque.pack(fill="both", expand=True, padx=5, pady=5)
        self.tree_estoque.bind("<Double-1>", self.adicionar_ao_carrinho)

    def setup_sessao_carrinho(self, parent):
        f_cart = tk.LabelFrame(parent, text=" 🛒 CARRINHO ", bg=self.bg_card, fg=self.cor_destaque, font=("Segoe UI", 10, "bold"))
        f_cart.pack(side="right", fill="both", expand=True)

        self.tree_cart = ttk.Treeview(f_cart, columns=("id", "prod", "tam", "qtd", "sub"), show="headings", style="PDV.Treeview")
        for col in ("id", "prod", "tam", "qtd", "sub"):
            self.tree_cart.heading(col, text=col.upper())
            self.tree_cart.column(col, width=80, anchor="center")
        self.tree_cart.pack(fill="both", expand=True, padx=5, pady=5)

        self.lbl_total = tk.Label(f_cart, text="TOTAL: R$ 0,00", font=("Segoe UI", 22, "bold"), 
                                  bg=self.bg_card, fg=self.cor_destaque)
        self.lbl_total.pack(pady=10)

    # --- Placeholders ---
    def _clear_placeholder(self, txt):
        if self.ent_busca_prod.get() == txt:
            self.ent_busca_prod.delete(0, tk.END)
            self.ent_busca_prod.config(highlightbackground=self.cor_destaque)

    def _add_placeholder(self, txt):
        if not self.ent_busca_prod.get():
            self.ent_busca_prod.insert(0, txt)
            self.ent_busca_prod.config(highlightbackground=self.cor_borda)

    # --- Lógica de Dados ---
    def carregar_dados_cliente_completo(self, cliente_id):
        with database.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,))
            c = cursor.fetchone()
            if c:
                info = (f"NOME: {c[1]}\n"
                        f"CPF: {c[2]} | TEL: {c[3]}\n"
                        f"CALÇADO: {c[6]} | LIMITE: R$ {c[12]:.2f}\n"
                        f"STATUS: {c[14]}")
                
                self.txt_dados_cliente.config(state="normal")
                self.txt_dados_cliente.delete("1.0", tk.END)
                self.txt_dados_cliente.insert("1.0", info)
                self.txt_dados_cliente.config(state="disabled")
                self.cliente_atual = c

    def buscar_cliente_db(self):
        termo = self.ent_busca_cli.get()
        self.tree_cli.delete(*self.tree_cli.get_children())
        if len(termo) >= 2:
            with database.conectar() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, nome FROM clientes WHERE nome LIKE ? AND status_cliente != 'Bloqueado'", (f"%{termo}%",))
                for row in cursor.fetchall():
                    self.tree_cli.insert("", "end", iid=row[0], values=(row[1],))

    def selecionar_cliente_busca(self, event):
        sel = self.tree_cli.selection()
        if sel:
            self.carregar_dados_cliente_completo(sel[0])

    def listar_estoque_completo(self):
        self.tree_estoque.delete(*self.tree_estoque.get_children())
        for p in database.listar_itens():
            # p[0]=id, p[1]=prod, p[2]=cor, p[3]=tam, p[5]=preco, p[6]=qtd
            self.tree_estoque.insert("", "end", iid=p[0], values=(p[0], p[1], p[2], p[3], f"R$ {p[5]:.2f}", p[6]))

    def filtrar_produtos(self):
        termo = self.ent_busca_prod.get().lower()
        if termo == "pesquisar produto...": return
        self.tree_estoque.delete(*self.tree_estoque.get_children())
        for p in database.listar_itens():
            if termo in p[1].lower() or termo in p[2].lower():
                self.tree_estoque.insert("", "end", iid=p[0], values=(p[0], p[1], p[2], p[3], f"R$ {p[5]:.2f}", p[6]))

    # --- Lógica de Carrinho ---
    def adicionar_ao_carrinho(self, event):
        sel = self.tree_estoque.selection()
        if not sel: return
        id_prod = sel[0]
        item = self.tree_estoque.item(id_prod, "values")
        
        qtd_estoque = int(item[5])
        if qtd_estoque <= 0:
            messagebox.showwarning("Aviso", "Produto esgotado!")
            return

        preco = float(item[4].replace("R$ ", "").replace(",", "."))

        if id_prod in self.carrinho_itens:
            if self.carrinho_itens[id_prod]['qtd'] < qtd_estoque:
                self.carrinho_itens[id_prod]['qtd'] += 1
                self.carrinho_itens[id_prod]['sub'] = self.carrinho_itens[id_prod]['qtd'] * preco
            else:
                messagebox.showwarning("Limite", "Quantidade máxima em estoque atingida.")
        else:
            self.carrinho_itens[id_prod] = {
                'id': id_prod, 'prod': item[1], 'tam': item[3],
                'preco': preco, 'qtd': 1, 'sub': preco
            }
        
        self.atualizar_view_carrinho()

    def remover_do_carrinho(self):
        sel = self.tree_cart.selection()
        if not sel: return
        id_prod = self.tree_cart.item(sel[0], "values")[0]

        if id_prod in self.carrinho_itens:
            if self.carrinho_itens[id_prod]['qtd'] > 1:
                self.carrinho_itens[id_prod]['qtd'] -= 1
                self.carrinho_itens[id_prod]['sub'] = self.carrinho_itens[id_prod]['qtd'] * self.carrinho_itens[id_prod]['preco']
            else:
                del self.carrinho_itens[id_prod]
        
        self.atualizar_view_carrinho()

    def atualizar_view_carrinho(self):
        self.tree_cart.delete(*self.tree_cart.get_children())
        total_geral = 0
        for dados in self.carrinho_itens.values():
            self.tree_cart.insert("", "end", values=(
                dados['id'], dados['prod'], dados['tam'], dados['qtd'], f"R$ {dados['sub']:.2f}"
            ))
            total_geral += dados['sub']
        self.lbl_total.config(text=f"TOTAL: R$ {total_geral:.2f}")

    def finalizar_venda(self):
        if not self.cliente_atual or not self.carrinho_itens:
            messagebox.showerror("Erro", "Selecione um cliente e adicione itens ao carrinho.")
            return
        
        total = sum(d['sub'] for d in self.carrinho_itens.values())
        
        # Validação de Limite de Crédito (exemplo de conversa com dados do banco)
        limite = float(self.cliente_atual[12])
        if total > limite and self.cliente_atual[14] != 'Vip':
            if not messagebox.askyesno("Limite Excedido", f"Venda (R${total:.2f}) excede o limite (R${limite:.2f}). Prosseguir?"):
                return

        lista_final = [{'id': d['id'], 'qtd': d['qtd'], 'preco': d['preco']} for d in self.carrinho_itens.values()]

        if messagebox.askyesno("Finalizar", f"Total: R$ {total:.2f}\nConfirmar venda?"):
            res, msg = database.realizar_venda_segura(self.cliente_atual[0], lista_final, "Dinheiro")
            if res:
                messagebox.showinfo("Sucesso", msg)
                # Conversa com a Main: chama atualização das listas na janela principal
                if hasattr(self.master, 'atualizar_lista'):
                    self.master.atualizar_lista()
                self.destroy()
            else:
                messagebox.showerror("Erro", msg)

    # --- Métodos de Navegação (Sidebar) ---
    def abrir_novo_cliente(self):
        from cadastro_clientes import JanelaCadastroClientes
        JanelaCadastroClientes(self)

    def abrir_cadastro_produto(self):
        from cadastro_produtos import JanelaCadastroProdutos
        JanelaCadastroProdutos(self)

if __name__ == "__main__":
    root = tk.Tk()
    app = JanelaCadastroVendas(root)
    root.mainloop()