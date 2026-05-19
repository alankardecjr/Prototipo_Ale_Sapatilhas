"""
cadastro_vendas.py — PDV / checkout (cliente, estoque, carrinho, pagamento).
"""

import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

import config
import database
import ui_utils


class JanelaCadastroVendas(tk.Toplevel):
    """
    Tela de PDV (checkout): busca de cliente, estoque, carrinho e pagamento.

    Fluxos principais:
        - finalizar_venda: exige pagamento preenchido e pergunta sobre recibo
        - cadastrar_pagamento: grava venda e abre gerenciar_receitas para baixa
        - filtros fixos de cor/tamanho até limpar o formulário
    """

    FORMAS_PAGAMENTO = list(config.FORMAS_PAGAMENTO)
    CORES_FILTRO = ["", "Amarelo", "Azul", "Branco", "Caramelo", "Massala", "Nude", "Off", "Preto", "Rosa", "Verde", "Vermelho"]
    TAMANHOS_FILTRO = [""] + [str(i) for i in range(33, 41)] + ["G", "GG", "M", "P", "U"]

    def __init__(self, master, cliente_selecionado=None, dados_venda=None):
        """Monta o PDV; opcionalmente pré-carrega cliente ou venda em edição."""
        super().__init__(master)
        self.master = master
        self.title("Alê Sapatilhas - Checkout de Vendas")
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

        self.cliente_atual = None
        self.carrinho_itens = {}
        self.venda_id = dados_venda.get("id") if dados_venda else None
        self._imgs_tree = {}
        self._estoque_cache = []

        self.configurar_estilos()
        self.setup_layout()

        if cliente_selecionado:
            cid = cliente_selecionado[0] if isinstance(cliente_selecionado, (tuple, list)) else cliente_selecionado
            self.carregar_dados_cliente_completo(cid)
            if isinstance(cliente_selecionado, (tuple, list)) and len(cliente_selecionado) > 1:
                self.ent_busca_cli.delete(0, tk.END)
                self.ent_busca_cli.insert(0, cliente_selecionado[1])
        elif self.venda_id:
            v = database.obter_venda_por_id(self.venda_id)
            if v:
                self.carregar_dados_cliente_completo(v[1])
                self.cb_forma.set(v[8] or "Dinheiro")
                self.ent_parcelas.delete(0, tk.END)
                self.ent_parcelas.insert(0, str(v[9] or 1))
                self.ent_desconto.delete(0, tk.END)
                self.ent_desconto.insert(0, f"{v[6]:.2f}")
                self._carregar_itens_venda()
                if v[11] == config.STATUS_VENDA_CANCELADA:
                    self.lbl_modo.config(text="VENDA CANCELADA (somente consulta)")
                    self.btn_finalizar.config(state="disabled")

        self.listar_estoque_completo()
        self._atualizar_estado_botao_finalizar()

    def configurar_estilos(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("PDV.Treeview", background=self.bg_card, foreground=self.cor_texto,
                             rowheight=42, font=("Segoe UI", 10))
        self.style.configure("PDV.Treeview.Heading", font=("Segoe UI", 10, "bold"), background=self.bg_card)
        self.style.map("PDV.Treeview", background=[("selected", self.cor_destaque)])

    def setup_layout(self):
        self.sidebar = tk.Frame(self, bg=self.cor_btn_sair, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="ALÊ\nSAPATILHAS", font=("Segoe UI", 20, "bold"),
                 bg=self.cor_btn_sair, fg="white", pady=20).pack()

        btn_estilo = {
            "font": ("Segoe UI", 9, "bold"), "bg": self.cor_btn_menu, "fg": "white",
            "relief": "flat", "cursor": "hand2", "anchor": "w", "padx": 15, "pady": 8,
        }
        titulo_acao = "💾 SALVAR ALTERAÇÕES" if self.venda_id else "💰 FINALIZAR VENDA"

        botoes = [
            (titulo_acao, self.finalizar_venda),
            ("💳 CADASTRAR PAGAMENTO", self.cadastrar_pagamento),
            ("❌ REMOVER ITEM", self.remover_do_carrinho),
            ("↩ ESTORNAR VENDA", self.estornar_venda) if self.venda_id else None,
            ("👤 NOVO CLIENTE", self.abrir_novo_cliente),
            ("📦 NOVO PRODUTO", self.abrir_cadastro_produto),
            ("🔄 LIMPAR DADOS", self.limpar_formulario),
            ("🔄 ATUALIZAR", self.listar_estoque_completo),
            ("🚪 SAIR", self._fechar_pdv),
        ]

        for item in botoes:
            if not item:
                continue
            text_aux, cmd_aux = item
            btn = tk.Button(self.sidebar, text=text_aux, command=cmd_aux, **btn_estilo)
            btn.pack(fill="x", pady=3, padx=5)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.cor_hover_btn))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.cor_btn_menu))
            if "FINALIZAR" in text_aux or "SALVAR" in text_aux:
                self.btn_finalizar = btn
                self.btn_finalizar.config(state="disabled")

        self.main_container = tk.Frame(self, bg=self.bg_fundo, padx=20, pady=10)
        self.main_container.pack(side="right", fill="both", expand=True)

        self.lbl_modo = tk.Label(
            self.main_container,
            text="EDIÇÃO DE VENDA" if self.venda_id else "NOVA VENDA (PDV)",
            font=("Segoe UI", 12, "bold"), bg=self.bg_fundo, fg=self.cor_destaque,
        )
        self.lbl_modo.pack(anchor="w", pady=(0, 5))

        self.setup_sessao_cliente()
        self.colunas_frame = tk.Frame(self.main_container, bg=self.bg_fundo)
        self.colunas_frame.pack(fill="both", expand=True, pady=10)
        self.setup_sessao_produtos(self.colunas_frame)
        self.setup_sessao_carrinho(self.colunas_frame)
        self._setup_pagamento()

    def _setup_pagamento(self):
        f = tk.LabelFrame(self.main_container, text=" Pagamento ", bg=self.bg_fundo,
                          fg=self.cor_texto, font=("Segoe UI", 9, "bold"), relief="solid", borderwidth=1)
        f.pack(fill="x", side="bottom", pady=(5, 0))
        for c in range(6):
            f.columnconfigure(c, weight=1)

        tk.Label(f, text="Forma *", bg=self.bg_fundo, font=("Segoe UI", 8, "bold")).grid(row=0, column=0, padx=5, sticky="w")
        self.cb_forma = ttk.Combobox(f, values=self.FORMAS_PAGAMENTO, state="readonly", width=22, font=("Segoe UI", 11))
        self.cb_forma.set("Dinheiro")
        self.cb_forma.grid(row=1, column=0, padx=5, pady=4, sticky="ew")
        self.cb_forma.bind("<<ComboboxSelected>>", lambda e: self._atualizar_estado_botao_finalizar())

        tk.Label(f, text="Parcelas *", bg=self.bg_fundo, font=("Segoe UI", 8, "bold")).grid(row=0, column=1, padx=5, sticky="w")
        self.ent_parcelas = tk.Entry(f, width=8, font=("Segoe UI", 11))
        self.ent_parcelas.insert(0, "1")
        self.ent_parcelas.grid(row=1, column=1, padx=5, pady=4, sticky="ew")
        self.ent_parcelas.bind("<KeyRelease>", lambda e: self._atualizar_estado_botao_finalizar())

        tk.Label(f, text="Desconto (R$)", bg=self.bg_fundo, font=("Segoe UI", 8, "bold")).grid(row=0, column=2, padx=5, sticky="w")
        self.ent_desconto = tk.Entry(f, width=12, font=("Segoe UI", 11))
        self.ent_desconto.insert(0, "0.00")
        self.ent_desconto.bind("<KeyRelease>", lambda e: (self.atualizar_view_carrinho(), self._atualizar_estado_botao_finalizar()))
        self.ent_desconto.grid(row=1, column=2, padx=5, pady=4, sticky="ew")

        tk.Label(f, text="Valor pago (R$) *", bg=self.bg_fundo, font=("Segoe UI", 8, "bold")).grid(row=0, column=3, padx=5, sticky="w")
        self.ent_valor_pago = tk.Entry(f, width=14, font=("Segoe UI", 11))
        self.ent_valor_pago.insert(0, "0.00")
        self.ent_valor_pago.grid(row=1, column=3, padx=5, pady=4, sticky="ew")
        self.ent_valor_pago.bind("<KeyRelease>", lambda e: self._atualizar_estado_botao_finalizar())

        tk.Label(f, text="Data pagamento", bg=self.bg_fundo, font=("Segoe UI", 8, "bold")).grid(row=0, column=4, padx=5, sticky="w")
        self.ent_data_pag = tk.Entry(f, width=14, font=("Segoe UI", 11))
        self.ent_data_pag.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.ent_data_pag.grid(row=1, column=4, padx=5, pady=4, sticky="ew")
        self.ent_data_pag.bind("<KeyRelease>", lambda e: self._atualizar_estado_botao_finalizar())
        ui_utils.anexar_botao_calendario(f, self.ent_data_pag, row=1, column=5, sticky="w")

    def setup_sessao_cliente(self):
        frame_cli = tk.Frame(self.main_container, bg=self.bg_fundo)
        frame_cli.pack(fill="x", pady=5)

        f_busca = tk.Frame(frame_cli, bg=self.bg_fundo)
        f_busca.pack(side="left", fill="y")

        tk.Label(f_busca, text="BUSCAR CLIENTE", font=("Segoe UI", 8, "bold"), bg=self.bg_fundo).pack(anchor="w")
        self.ent_busca_cli = tk.Entry(f_busca, font=("Segoe UI", 11), width=42, highlightthickness=1)
        self.ent_busca_cli.pack(pady=2, fill="x")
        self.ent_busca_cli.bind("<KeyRelease>", lambda e: self.buscar_cliente_db())

        self.tree_cli = ttk.Treeview(f_busca, columns=("nome",), show="headings", height=3, style="PDV.Treeview")
        self.tree_cli.heading("nome", text="NOME")
        self.tree_cli.column("nome", width=320)
        self.tree_cli.pack(fill="both", expand=True)
        self.tree_cli.bind("<<TreeviewSelect>>", self.selecionar_cliente_busca)

        self.frame_dados_detalhados = tk.LabelFrame(
            frame_cli, text=" 👤 DADOS DO CLIENTE ", bg=self.bg_card, fg=self.cor_texto,
            font=("Segoe UI", 10, "bold"), relief="solid", borderwidth=1,
        )
        self.frame_dados_detalhados.pack(side="right", fill="both", expand=True, padx=(20, 0))

        self.txt_dados_cliente = tk.Text(
            self.frame_dados_detalhados, font=("Segoe UI", 10), height=4,
            bg=self.bg_card, relief="flat", state="disabled",
        )
        self.txt_dados_cliente.pack(fill="both", expand=True, padx=10, pady=5)

    def setup_sessao_produtos(self, parent):
        f_prod = tk.LabelFrame(parent, text=" 👠 LISTA DE PRODUTOS ", bg=self.bg_fundo,
                               fg=self.cor_texto, font=("Segoe UI", 10, "bold"), relief="solid", borderwidth=1)
        f_prod.pack(side="left", fill="both", expand=True, padx=(0, 10))

        barra_busca = tk.Frame(f_prod, bg=self.bg_fundo)
        barra_busca.pack(fill="x", padx=5, pady=5)

        self.ent_busca_prod = tk.Entry(barra_busca, font=("Segoe UI", 11), highlightthickness=1)
        self.ent_busca_prod.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self._placeholder_prod = "Pesquisar produto..."
        self.ent_busca_prod.insert(0, self._placeholder_prod)
        self.ent_busca_prod.bind("<FocusIn>", lambda e: self._clear_placeholder())
        self.ent_busca_prod.bind("<FocusOut>", lambda e: self._add_placeholder())
        self.ent_busca_prod.bind("<KeyRelease>", lambda e: self.filtrar_produtos())

        tk.Label(barra_busca, text="Cor", bg=self.bg_fundo, font=("Segoe UI", 8, "bold")).pack(side="left")
        self.cb_filtro_cor = ttk.Combobox(barra_busca, values=self.CORES_FILTRO, width=10, state="readonly", font=("Segoe UI", 9))
        self.cb_filtro_cor.set("")
        self.cb_filtro_cor.pack(side="left", padx=4)
        self.cb_filtro_cor.bind("<<ComboboxSelected>>", lambda e: self.filtrar_produtos())

        tk.Label(barra_busca, text="Tam.", bg=self.bg_fundo, font=("Segoe UI", 8, "bold")).pack(side="left")
        self.cb_filtro_tam = ttk.Combobox(barra_busca, values=self.TAMANHOS_FILTRO, width=6, state="readonly", font=("Segoe UI", 9))
        self.cb_filtro_tam.set("")
        self.cb_filtro_tam.pack(side="left", padx=4)
        self.cb_filtro_tam.bind("<<ComboboxSelected>>", lambda e: self.filtrar_produtos())

        cols = ("prod", "cor", "tam", "preco", "qtd")
        self.tree_estoque = ttk.Treeview(f_prod, columns=cols, show="tree headings", style="PDV.Treeview", height=10)
        self.tree_estoque.heading("#0", text="FOTO")
        self.tree_estoque.column("#0", width=52, anchor="center")
        for col in cols:
            self.tree_estoque.heading(col, text=col.upper())
            self.tree_estoque.column(col, width=80, anchor="center")
        self.tree_estoque.pack(fill="both", expand=True, padx=5, pady=5)
        self.tree_estoque.bind("<Double-1>", self.adicionar_ao_carrinho)

    def setup_sessao_carrinho(self, parent):
        f_cart = tk.LabelFrame(parent, text=" 🛒 CARRINHO ", bg=self.bg_card, fg=self.cor_destaque,
                               font=("Segoe UI", 10, "bold"), relief="solid", borderwidth=1)
        f_cart.pack(side="right", fill="both", expand=True)

        cols = ("prod", "tam", "qtd", "sub")
        self.tree_cart = ttk.Treeview(f_cart, columns=cols, show="tree headings", style="PDV.Treeview", height=10)
        self.tree_cart.heading("#0", text="FOTO")
        self.tree_cart.column("#0", width=52, anchor="center")
        for col in cols:
            self.tree_cart.heading(col, text=col.upper())
            self.tree_cart.column(col, width=85, anchor="center")
        self.tree_cart.pack(fill="both", expand=True, padx=5, pady=5)

        self.lbl_total = tk.Label(f_cart, text="TOTAL: R$ 0,00", font=("Segoe UI", 20, "bold"),
                                  bg=self.bg_card, fg=self.cor_destaque)
        self.lbl_total.pack(pady=5, side="bottom")

    def _fechar_pdv(self):
        if ui_utils.confirmar(self, "Sair", "Deseja fechar o PDV?"):
            self.destroy()

    def _clear_placeholder(self):
        if self.ent_busca_prod.get() == self._placeholder_prod:
            self.ent_busca_prod.delete(0, tk.END)

    def _add_placeholder(self):
        if not self.ent_busca_prod.get():
            self.ent_busca_prod.insert(0, self._placeholder_prod)

    def _total_liquido(self):
        total = sum(d["sub"] for d in self.carrinho_itens.values())
        try:
            desc = float(self.ent_desconto.get().replace(",", "."))
        except ValueError:
            desc = 0
        return max(total - desc, 0)

    def _validar_pagamento_preenchido(self):
        if not self.cb_forma.get().strip():
            return False
        try:
            parcelas = int(self.ent_parcelas.get() or "0")
            if parcelas < 1:
                return False
        except ValueError:
            return False
        try:
            pago = float(self.ent_valor_pago.get().replace(",", "."))
        except ValueError:
            return False
        if pago <= 0:
            return False
        if not self.ent_data_pag.get().strip():
            return False
        return True

    def _atualizar_estado_botao_finalizar(self):
        ok = (
            self.cliente_atual is not None
            and bool(self.carrinho_itens)
            and self._validar_pagamento_preenchido()
            and not self.venda_id
        )
        if hasattr(self, "btn_finalizar"):
            self.btn_finalizar.config(state="normal" if ok else "disabled")

    def _miniatura_produto(self, pid, foto_path):
        if pid in self._imgs_tree:
            return self._imgs_tree[pid]
        img = ui_utils.carregar_miniatura_foto(foto_path, (36, 36))
        if img:
            self._imgs_tree[pid] = img
        return img

    def _inserir_linha_estoque(self, p):
        pid, prod, cor, tam, _custo, preco, qtd, foto = p
        img = self._miniatura_produto(pid, foto if len(p) > 7 else "")
        self.tree_estoque.insert(
            "", "end", iid=pid, image=img or "", text="" if img else "—",
            values=(prod, cor, tam, f"R$ {preco:.2f}", qtd),
        )

    def carregar_dados_cliente_completo(self, cliente_id):
        with database.conectar() as conn:
            c = conn.execute(
                "SELECT * FROM clientes WHERE id = ? AND tipo = ?",
                (cliente_id, config.TIPO_CLIENTE),
            ).fetchone()
        if c:
            info = (
                f"NOME: {c[2]}\nCPF: {c[3] or 'N/A'} | TEL: {c[4]}\n"
                f"CALÇADO: {c[7] or 'N/A'} | LIMITE: R$ {float(c[13] or 0):.2f}\n"
                f"STATUS: {c[15]}"
            )
            self.txt_dados_cliente.config(state="normal")
            self.txt_dados_cliente.delete("1.0", tk.END)
            self.txt_dados_cliente.insert("1.0", info)
            self.txt_dados_cliente.config(state="disabled")
            self.cliente_atual = c
            self._atualizar_estado_botao_finalizar()

    def _carregar_itens_venda(self):
        self.carrinho_itens = {}
        for row in database.obter_itens_venda(self.venda_id):
            pid, prod, _cor, tam, qtd, preco, sub = row
            self.carrinho_itens[str(pid)] = {
                "id": pid, "prod": prod, "tam": tam, "preco": preco, "qtd": qtd, "sub": sub, "foto": "",
            }
        self.atualizar_view_carrinho()

    def buscar_cliente_db(self):
        termo = self.ent_busca_cli.get()
        self.tree_cli.delete(*self.tree_cli.get_children())
        if len(termo) >= 2:
            for row in database.listar_contatos(tipo=config.TIPO_CLIENTE, termo=termo):
                self.tree_cli.insert("", "end", iid=row[0], values=(row[2],))

    def selecionar_cliente_busca(self, event):
        sel = self.tree_cli.selection()
        if sel:
            self.carregar_dados_cliente_completo(sel[0])

    def _passa_filtros_fixos(self, p):
        cor_f = self.cb_filtro_cor.get().strip()
        tam_f = self.cb_filtro_tam.get().strip()
        if cor_f and p[2] != cor_f:
            return False
        if tam_f and str(p[3]) != tam_f:
            return False
        return True

    def listar_estoque_completo(self):
        self.tree_estoque.delete(*self.tree_estoque.get_children())
        self._estoque_cache = list(database.listar_itens())
        for p in self._estoque_cache:
            if self._passa_filtros_fixos(p):
                self._inserir_linha_estoque(p)

    def filtrar_produtos(self):
        termo = self.ent_busca_prod.get().lower()
        if termo == self._placeholder_prod.lower():
            termo = ""
        self.tree_estoque.delete(*self.tree_estoque.get_children())
        for p in self._estoque_cache:
            if not self._passa_filtros_fixos(p):
                continue
            if termo and termo not in p[1].lower() and termo not in p[2].lower():
                continue
            self._inserir_linha_estoque(p)

    def adicionar_ao_carrinho(self, event):
        sel = self.tree_estoque.selection()
        if not sel:
            return
        id_prod = str(sel[0])
        item = self.tree_estoque.item(id_prod, "values")
        qtd_estoque = int(item[4])
        if qtd_estoque <= 0:
            messagebox.showwarning("Aviso", "Produto esgotado!", parent=self)
            return
        preco = float(item[3].replace("R$ ", "").replace(",", "."))
        foto = ""
        for p in self._estoque_cache:
            if str(p[0]) == id_prod:
                foto = p[7] if len(p) > 7 else ""
                break
        if id_prod in self.carrinho_itens:
            if self.carrinho_itens[id_prod]["qtd"] < qtd_estoque:
                self.carrinho_itens[id_prod]["qtd"] += 1
                self.carrinho_itens[id_prod]["sub"] = self.carrinho_itens[id_prod]["qtd"] * preco
            else:
                messagebox.showwarning("Limite", "Quantidade máxima em estoque atingida.", parent=self)
        else:
            self.carrinho_itens[id_prod] = {
                "id": int(id_prod), "prod": item[0], "tam": item[2],
                "preco": preco, "qtd": 1, "sub": preco, "foto": foto,
            }
        self.atualizar_view_carrinho()

    def remover_do_carrinho(self):
        if not ui_utils.confirmar(self, "Remover", "Remover item do carrinho?"):
            return
        sel = self.tree_cart.selection()
        if not sel:
            return
        id_prod = str(sel[0])
        if id_prod in self.carrinho_itens:
            if self.carrinho_itens[id_prod]["qtd"] > 1:
                self.carrinho_itens[id_prod]["qtd"] -= 1
                self.carrinho_itens[id_prod]["sub"] = (
                    self.carrinho_itens[id_prod]["qtd"] * self.carrinho_itens[id_prod]["preco"]
                )
            else:
                del self.carrinho_itens[id_prod]
        self.atualizar_view_carrinho()

    def atualizar_view_carrinho(self):
        self.tree_cart.delete(*self.tree_cart.get_children())
        for dados in self.carrinho_itens.values():
            img = self._miniatura_produto(dados["id"], dados.get("foto", ""))
            self.tree_cart.insert(
                "", "end", iid=str(dados["id"]),
                image=img or "", text="" if img else "—",
                values=(dados["prod"], dados["tam"], dados["qtd"], f"R$ {dados['sub']:.2f}"),
            )
        total = self._total_liquido()
        self.lbl_total.config(text=f"TOTAL: R$ {total:.2f}")
        if not self.ent_valor_pago.get().strip() or self.ent_valor_pago.get() == "0.00":
            self.ent_valor_pago.delete(0, tk.END)
            self.ent_valor_pago.insert(0, f"{total:.2f}")
        self._atualizar_estado_botao_finalizar()

    def _perguntar_imprimir_recibo(self, venda_id, total):
        """Gancho para futura integração com impressora."""
        if messagebox.askyesno(
            "Recibo",
            f"Venda #{venda_id} registrada.\nTotal: R$ {total:.2f}\n\nDeseja imprimir o recibo?",
            parent=self,
        ):
            messagebox.showinfo(
                "Impressão",
                "Função de impressão preparada para configuração futura de impressora.",
                parent=self,
            )

    def _dados_venda_para_api(self):
        desconto = float(self.ent_desconto.get().replace(",", "."))
        parcelas = max(1, int(self.ent_parcelas.get() or 1))
        forma = self.cb_forma.get()
        lista_final = [{"id": d["id"], "qtd": d["qtd"], "preco": d["preco"]} for d in self.carrinho_itens.values()]
        return lista_final, forma, parcelas, desconto

    def estornar_venda(self):
        if not self.venda_id:
            return
        if ui_utils.confirmar(self, "Estornar venda", "Cancelar esta venda e devolver itens ao estoque?"):
            ok, msg = database.cancelar_venda(self.venda_id)
            if ok:
                messagebox.showinfo("Sucesso", msg, parent=self)
                if hasattr(self.master, "atualizar_lista"):
                    self.master.atualizar_lista()
                self.destroy()
            else:
                messagebox.showerror("Erro", msg, parent=self)

    def finalizar_venda(self):
        """Registra a venda no banco após validar pagamento; oferece impressão de recibo."""
        if not self._validar_pagamento_preenchido():
            messagebox.showwarning("Pagamento", "Informe forma, parcelas, valor pago e data antes de finalizar.", parent=self)
            return
        if not self.cliente_atual or not self.carrinho_itens:
            messagebox.showerror("Erro", "Selecione um cliente e adicione itens ao carrinho.", parent=self)
            return

        lista_final, forma, parcelas, desconto = self._dados_venda_para_api()
        total = self._total_liquido()
        limite = float(self.cliente_atual[13] or 0)
        if total > limite and self.cliente_atual[15] != "Vip" and forma == "Crediário":
            if not ui_utils.confirmar(self, "Limite", f"Venda excede limite (R$ {limite:.2f}). Continuar?"):
                return
        if not ui_utils.confirmar(self, "Confirmar", f"Finalizar venda?\nTotal: R$ {total:.2f}\n{forma} | {parcelas}x"):
            return

        if self.venda_id:
            res, msg = database.atualizar_venda_comercial(self.venda_id, self.cliente_atual[0], lista_final, desconto)
            vid = self.venda_id
        else:
            res, msg, vid = database.realizar_venda_segura(
                self.cliente_atual[0], lista_final, forma, parcelas, desconto,
            )
        if res:
            self._perguntar_imprimir_recibo(vid, total)
            if hasattr(self.master, "atualizar_lista"):
                self.master.atualizar_lista()
            self.destroy()
        else:
            messagebox.showerror("Erro", msg, parent=self)

    def cadastrar_pagamento(self):
        """Cria a venda e abre receitas para confirmar pagamento; depois limpa o PDV."""
        if not self.cliente_atual or not self.carrinho_itens:
            messagebox.showwarning("Atenção", "Selecione cliente e itens antes de cadastrar pagamento.", parent=self)
            return
        if not self._validar_pagamento_preenchido():
            messagebox.showwarning("Pagamento", "Preencha todos os campos de pagamento.", parent=self)
            return
        if not ui_utils.confirmar(self, "Cadastrar pagamento", "Registrar venda e abrir receitas para confirmar pagamento?"):
            return

        lista_final, forma, parcelas, desconto = self._dados_venda_para_api()
        res, msg, vid = database.realizar_venda_segura(
            self.cliente_atual[0], lista_final, forma, parcelas, desconto,
        )
        if not res:
            messagebox.showerror("Erro", msg, parent=self)
            return

        from gerenciar_receitas import JanelaGerenciarReceitas
        JanelaGerenciarReceitas(self.master, venda_id=vid, on_sucesso=self._apos_registrar_pagamento)

    def _apos_registrar_pagamento(self):
        if hasattr(self.master, "atualizar_lista"):
            self.master.atualizar_lista()
        self.limpar_formulario()
        messagebox.showinfo("PDV", "Pagamento registrado. PDV liberado para nova venda.", parent=self)

    def abrir_novo_cliente(self):
        from cadastro_clientes import JanelaCadastroClientes
        JanelaCadastroClientes(self)

    def abrir_cadastro_produto(self):
        from cadastro_produtos import JanelaCadastroProdutos
        JanelaCadastroProdutos(self)

    def limpar_formulario(self):
        self.cliente_atual = None
        self.carrinho_itens = {}
        self.txt_dados_cliente.config(state="normal")
        self.txt_dados_cliente.delete("1.0", tk.END)
        self.txt_dados_cliente.config(state="disabled")
        self.ent_busca_cli.delete(0, tk.END)
        self.tree_cli.delete(*self.tree_cli.get_children())
        self.ent_busca_prod.delete(0, tk.END)
        self._add_placeholder()
        self.cb_filtro_cor.set("")
        self.cb_filtro_tam.set("")
        self.ent_desconto.delete(0, tk.END)
        self.ent_desconto.insert(0, "0.00")
        self.ent_parcelas.delete(0, tk.END)
        self.ent_parcelas.insert(0, "1")
        self.ent_valor_pago.delete(0, tk.END)
        self.ent_valor_pago.insert(0, "0.00")
        self.ent_data_pag.delete(0, tk.END)
        self.ent_data_pag.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.cb_forma.set("Dinheiro")
        self.listar_estoque_completo()
        self.atualizar_view_carrinho()


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Main Window Mock")
    app = JanelaCadastroVendas(root)
    root.mainloop()
