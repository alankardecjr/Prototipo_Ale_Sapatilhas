"""
ui_utils.py — Camada de apresentação compartilhada (Design System leve).

Por que centralizar cores e estilos?
  - Consistência visual entre dezenas de telas Tkinter
  - Alteração de tema em um único arquivo
  - Separação entre "como aparece" (UI) e "o que faz" (database)

STATUS_MENU_*: mapeiam rótulos amigáveis do menu de contexto para valores
gravados no SQLite (constraints CHECK exigem texto exato).
"""

import calendar
import os
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta

# --- PALETA DE CORES PADRONIZADA ---
LARGURA_MODULO_PADRAO = 700

TIPOS_PRODUTO_UI = ("Calçado", "Vestuário")
TIPO_PRODUTO_UI_PARA_BD = {"Calçado": "Calçados", "Vestuário": "Confecções"}
TIPO_PRODUTO_BD_PARA_UI = {v: k for k, v in TIPO_PRODUTO_UI_PARA_BD.items()}

PALETA = {
    "bg_fundo": "#F1F5F9",
    "bg_card": "#FFFFFF",
    "cor_borda": "#8BA2BD",
    "cor_texto": "#0B1933",
    "cor_lbl": "#020C18",
    "cor_destaque": "#6366F1",
    "cor_btn_menu": "#1E293B",
    "cor_btn_sair": "#25324E",
    "cor_btn_acao1": "#425074",
    "cor_btn_acao2": "#6366F1",
    "cor_letra_botoes": "#FFFFFF",
    "cor_btn_acao": "#425074",
    "cor_hover_btn": "#6F7CA0",
    "cor_hover_field": "#484AD6",
}

def calcular_dimensoes_janela(root, largura_desejada=700, altura_desejada=850, maximizar=False):
    """
    Calcula e define as dimensões da janela respeitando:
    - Tamanho do monitor
    - Barra de tarefas do SO
    - Centralização na tela
    
    Args:
        root: Janela Tkinter
        largura_desejada: Largura desejada (padrão 700)
        altura_desejada: Altura desejada (padrão 850)
        maximizar: Se True, maximiza; se False, usa dimensões padrão
    """
    # Atualiza para capturar dimensões corretas
    root.update_idletasks()
    
    # Dimensões do monitor (aproximadamente)
    largura_tela = root.winfo_screenwidth()
    altura_tela = root.winfo_screenheight()
    
    if maximizar:
        # Maximiza deixando espaço para barra de tarefas e bordas da janela
        root.geometry(f"{largura_tela}x{altura_tela - 100}+0+0")
    else:
        # Usa dimensões padrão
        # Verifica se o tamanho desejado cabe na tela
        largura_final = min(largura_desejada, largura_tela - 20)
        altura_final = min(altura_desejada, altura_tela - 100)
        
        # Centraliza a janela
        x = (largura_tela - largura_final) // 2
        y = (altura_tela - altura_final) // 2
        
        root.geometry(f"{largura_final}x{altura_final}+{x}+{y}")

def get_paleta():
    """Retorna a paleta de cores padronizada (cópia para painel de temas futuro)."""
    p = PALETA.copy()
    p.setdefault("cor_btn_acao1", p.get("cor_btn_acao", "#425074"))
    p.setdefault("cor_btn_acao2", p.get("cor_destaque", "#6366F1"))
    p.setdefault("cor_letra_botoes", "#FFFFFF")
    return p


def cor_botao(paleta, estilo):
    """Resolve cor do botão: acao1 | acao2 | sair."""
    mapa = {
        "acao1": paleta.get("cor_btn_acao1", paleta.get("cor_btn_acao")),
        "acao2": paleta.get("cor_btn_acao2", paleta.get("cor_destaque")),
        "sair": paleta.get("cor_btn_sair"),
    }
    return mapa.get(estilo, mapa["acao1"])

# Rótulos do menu de contexto → valores aceitos no banco (CHECK constraints)
STATUS_MENU_CLIENTE = {
    "✓ Ativo": "Ativo", "★ VIP": "Vip", "⛔ Bloqueado": "Bloqueado", "✗ Inativo": "Inativo",
}
STATUS_MENU_PRODUTO = {
    "✓ Disponível": "Disponível", "✗ Indisponível": "Indisponível", "★ Promocional": "Promocional",
}
STATUS_MENU_FINANCEIRO = {
    "◎ Pendente": "Pendente", "✓ Pago": "Pago", "⚠ Atrasado": "Atrasado", "✗ Cancelado": "Cancelado",
}
STATUS_MENU_VENDA = {
    "✓ Finalizada": "Finalizada", "⏳ Pendente": "Pendente", "✗ Cancelada": "Cancelada",
}

def normalizar_status_menu(rotulo, mapa):
    """Converte rótulo do menu para valor persistível."""
    if rotulo in mapa:
        return mapa[rotulo]
    for k, v in mapa.items():
        if v == rotulo or rotulo.endswith(v):
            return v
    return rotulo

def criar_style_padrao(root):
    """Configura estilos padrão para ttk.Combobox e ttk.Treeview"""
    from tkinter import ttk
    
    style = ttk.Style()
    style.theme_use('clam')
    
    # Combobox
    style.configure("TCombobox", 
                   fieldbackground=PALETA["bg_card"],
                   background=PALETA["bg_card"],
                   arrowcolor=PALETA["cor_btn_acao"],
                   bordercolor=PALETA["cor_borda"])
    
    # Treeview
    style.configure("Treeview",
                   background=PALETA["bg_card"],
                   foreground=PALETA["cor_texto"],
                   rowheight=22,
                   borderwidth=0,
                   font=("Segoe UI", 9))
    
    style.configure("Treeview.Heading",
                   font=("Segoe UI", 10, "bold"),
                   background=PALETA["bg_card"])
    
    style.map("Treeview",
             background=[('selected', PALETA["cor_destaque"])])
    
    return style


def confirmar(parent, titulo, mensagem):
    """Confirmação Sim/Não padronizada para ações destrutivas ou importantes."""
    return messagebox.askyesno(titulo, mensagem, parent=parent)


def tipo_produto_para_bd(valor_ui):
    """Converte rótulo da UI (Calçado/Vestuário) para valor gravado no SQLite."""
    return TIPO_PRODUTO_UI_PARA_BD.get(valor_ui, valor_ui or "Calçados")


def tipo_produto_para_ui(valor_bd):
    """Converte valor do banco para exibição no formulário de produtos."""
    return TIPO_PRODUTO_BD_PARA_UI.get(valor_bd, "Calçado")


class MiniCalendario(tk.Toplevel):
    """Janela popup com calendário mensal para preencher um Entry com data DD/MM/AAAA."""

    DIAS_SEMANA = ("Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb")

    def __init__(self, master, entry_alvo, titulo="Selecionar data"):
        """Exibe o mês atual e grava a data escolhida em entry_alvo."""
        super().__init__(master)
        self.entry_alvo = entry_alvo
        self.title(titulo)
        self.configure(bg=PALETA["bg_fundo"])
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self._hoje = datetime.now().date()
        self._coluna_hoje = (self._hoje.weekday() + 1) % 7
        self.ano = tk.IntVar(value=self._hoje.year)
        self.mes = tk.IntVar(value=self._hoje.month)

        topo = tk.Frame(self, bg=PALETA["bg_fundo"], padx=10, pady=8)
        topo.pack(fill="x")
        tk.Button(topo, text="◀", command=self._mes_anterior, width=3).pack(side="left")
        self.lbl_mes = tk.Label(topo, text="", font=("Segoe UI", 10, "bold"), bg=PALETA["bg_fundo"])
        self.lbl_mes.pack(side="left", expand=True)
        tk.Button(topo, text="▶", command=self._mes_proximo, width=3).pack(side="right")

        self.grid_dias = tk.Frame(self, bg=PALETA["bg_fundo"], padx=8, pady=4)
        self.grid_dias.pack()
        self._lbl_dias = []
        for i, d in enumerate(self.DIAS_SEMANA):
            destaque = i == self._coluna_hoje
            lbl = tk.Label(
                self.grid_dias, text=d, width=4,
                font=("Segoe UI", 8, "bold"),
                bg=PALETA["cor_destaque"] if destaque else PALETA["bg_fundo"],
                fg="white" if destaque else PALETA["cor_texto"],
            )
            lbl.grid(row=0, column=i, padx=1, pady=(0, 2))
            self._lbl_dias.append(lbl)

        self._desenhar_dias()
        calcular_dimensoes_janela(self, largura_desejada=300, altura_desejada=340)

    def _mes_anterior(self):
        m, a = self.mes.get(), self.ano.get()
        if m == 1:
            self.mes.set(12)
            self.ano.set(a - 1)
        else:
            self.mes.set(m - 1)
        self._desenhar_dias()

    def _mes_proximo(self):
        m, a = self.mes.get(), self.ano.get()
        if m == 12:
            self.mes.set(1)
            self.ano.set(a + 1)
        else:
            self.mes.set(m + 1)
        self._desenhar_dias()

    def _desenhar_dias(self):
        for w in self.grid_dias.winfo_children():
            if int(w.grid_info().get("row", 0)) > 0:
                w.destroy()
        mes, ano = self.mes.get(), self.ano.get()
        meses_pt = (
            "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
        )
        self.lbl_mes.config(text=f"{meses_pt[mes]} / {ano}")
        linha, col = 1, 0
        semanas = calendar.Calendar(firstweekday=calendar.SUNDAY).monthdayscalendar(ano, mes)
        for semana in semanas:
            for dia in semana:
                if dia == 0:
                    col += 1
                    continue
                eh_hoje = (
                    ano == self._hoje.year and mes == self._hoje.month and dia == self._hoje.day
                )
                btn = tk.Button(
                    self.grid_dias, text=str(dia), width=4, relief="flat",
                    font=("Segoe UI", 9, "bold" if eh_hoje else "normal"),
                    bg=PALETA["cor_destaque"] if eh_hoje else PALETA["bg_card"],
                    fg="white" if eh_hoje else PALETA["cor_texto"],
                    activebackground=PALETA["cor_hover_btn"],
                    command=lambda d=dia: self._selecionar(d),
                )
                btn.grid(row=linha, column=col, padx=1, pady=1)
                col += 1
            linha += 1
            col = 0

    def _selecionar(self, dia):
        data = datetime(self.ano.get(), self.mes.get(), dia).strftime("%d/%m/%Y")
        self.entry_alvo.delete(0, tk.END)
        self.entry_alvo.insert(0, data)
        self.destroy()


def anexar_botao_calendario(parent, entry, row, column=1, sticky="e"):
    """Adiciona botão 📅 ao lado de um Entry para abrir o mini calendário."""
    btn = tk.Button(
        parent, text="📅", relief="flat", cursor="hand2", width=2,
        command=lambda: MiniCalendario(parent.winfo_toplevel(), entry),
    )
    btn.grid(row=row, column=column, sticky=sticky, padx=(0, 5))
    return btn


def texto_botao_salvar(rotulo, em_edicao):
    """Rótulo dual mode: Salvar X (novo) ou Atualizar X (edição)."""
    return f"Atualizar {rotulo}" if em_edicao else f"Salvar {rotulo}"


def anexar_botao_calculadora(parent, entry, row, column=0, sticky="e"):
    """Adiciona botão 🧮 ao lado de um Entry; OK envia o resultado para o campo."""
    btn = tk.Button(
        parent, text="🧮", relief="flat", cursor="hand2", width=2,
        command=lambda: abrir_calculadora(parent.winfo_toplevel(), entry),
    )
    btn.grid(row=row, column=column, sticky=sticky, padx=(0, 5))
    return btn


def configurar_entry_inteiro(entry, master, permitir_vazio=True):
    """Restringe Entry a dígitos (quantidades, parcelas, etc.)."""
    def _valido(proposto):
        if proposto == "":
            return permitir_vazio
        return proposto.isdigit()

    vcmd = (master.register(_valido), "%P")
    entry.config(validate="key", validatecommand=vcmd)


def aplicar_estilo_foco_entry(ent, paleta=None):
    """Hover e foco consistentes em campos Entry."""
    p = paleta or PALETA

    def on_enter(_e):
        if ent.focus_get() != ent:
            ent.config(highlightbackground=p["cor_hover_field"])
    def on_leave(_e):
        if ent.focus_get() != ent:
            ent.config(highlightbackground=p["cor_borda"])
    def on_focus_in(_e):
        ent.config(highlightbackground=p["cor_destaque"], highlightthickness=2)
    def on_focus_out(_e):
        ent.config(highlightbackground=p["cor_borda"], highlightthickness=1)

    ent.bind("<Enter>", on_enter)
    ent.bind("<Leave>", on_leave)
    ent.bind("<FocusIn>", on_focus_in)
    ent.bind("<FocusOut>", on_focus_out)


def criar_botao_rodape(parent, texto, comando, estilo="acao1", paleta=None):
    """Botão de rodapé: estilo em acao1, acao2 ou sair."""
    p = paleta or get_paleta()
    cor = cor_botao(p, estilo)
    fg = p.get("cor_letra_botoes", "#FFFFFF")
    btn = tk.Button(
        parent, text=texto, bg=cor, fg=fg, font=("Segoe UI", 10, "bold"),
        relief="flat", cursor="hand2", command=comando,
        activeforeground=fg,
    )
    btn._cor_base = cor
    btn._estilo = estilo

    def _on_enter(_e):
        btn.config(bg=p["cor_hover_btn"])

    def _on_leave(_e):
        btn.config(bg=btn._cor_base)

    btn.bind("<Enter>", _on_enter)
    btn.bind("<Leave>", _on_leave)
    return btn


def atualizar_cor_botao_rodape(btn, estilo="acao1", paleta=None):
    """Atualiza estilo/cor do botão de rodapé (dual mode Salvar/Atualizar)."""
    p = paleta or get_paleta()
    cor = cor_botao(p, estilo)
    btn._cor_base = cor
    btn._estilo = estilo
    btn.config(bg=cor)


def carregar_miniatura_foto(caminho, tamanho=(40, 40)):
    """Retorna PhotoImage redimensionada ou None se indisponível."""
    if not caminho or not os.path.exists(caminho):
        return None
    try:
        from PIL import Image, ImageTk
        img = Image.open(caminho)
        img.thumbnail(tamanho, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        try:
            return tk.PhotoImage(file=caminho)
        except Exception:
            return None


class _CalculadoraPadrao:
    """Calculadora estilo Windows/iOS: % sobre total em +/- e OK para campo alvo."""

    def __init__(self, master, entry_alvo=None):
        self.entry_alvo = entry_alvo
        self.win = tk.Toplevel(master)
        self.win.title("Calculadora")
        self.win.configure(bg=PALETA["bg_fundo"])
        self.win.resizable(False, False)
        self.win.transient(master)

        self.display_var = tk.StringVar(value="0")
        self._acc = None
        self._op = None
        self._nova_entrada = True

        painel = tk.Frame(self.win, bg=PALETA["bg_card"], padx=8, pady=8)
        painel.pack(fill="both", expand=True, padx=10, pady=10)

        self.display = tk.Entry(
            painel, textvariable=self.display_var, font=("Segoe UI", 22), justify="right",
            relief="flat", bg=PALETA["bg_card"], fg=PALETA["cor_texto"],
            readonlybackground=PALETA["bg_card"], state="readonly",
        )
        self.display.pack(fill="x", ipady=10, pady=(0, 10))

        grid = tk.Frame(painel, bg=PALETA["bg_card"])
        grid.pack(fill="both", expand=True)
        for c in range(4):
            grid.columnconfigure(c, weight=1, uniform="calc")
        for r in range(5):
            grid.rowconfigure(r, weight=1, uniform="calc")

        layout = [
            ("CE", "func"), ("C", "func"), ("⌫", "func"), ("/", "op"),
            ("7", "num"), ("8", "num"), ("9", "num"), ("*", "op"),
            ("4", "num"), ("5", "num"), ("6", "num"), ("-", "op"),
            ("1", "num"), ("2", "num"), ("3", "num"), ("+", "op"),
            ("0", "num"), (".", "num"), ("%", "func"), ("=", "eq"),
        ]
        for i, (txt, tipo) in enumerate(layout):
            bg = PALETA["cor_btn_acao1"] if tipo in ("op", "eq") else PALETA["bg_fundo"]
            fg = PALETA["cor_letra_botoes"] if tipo in ("op", "eq") else PALETA["cor_texto"]
            if tipo == "func":
                bg, fg = PALETA["cor_btn_acao2"], PALETA["cor_letra_botoes"]
            tk.Button(
                grid, text=txt, command=lambda t=txt: self._pressionar(t),
                font=("Segoe UI", 14, "bold"), bg=bg, fg=fg, relief="flat",
                cursor="hand2", activebackground=PALETA["cor_hover_btn"],
            ).grid(row=i // 4, column=i % 4, padx=3, pady=3, sticky="nsew")

        if entry_alvo is not None:
            rodape = tk.Frame(self.win, bg=PALETA["bg_fundo"])
            rodape.pack(fill="x", padx=10, pady=(0, 10))
            criar_botao_rodape(rodape, "OK", self._confirmar_ok, "acao2").pack(fill="x", ipady=8)

        calcular_dimensoes_janela(self.win, largura_desejada=300, altura_desejada=440 if entry_alvo else 400)

    def _valor_display(self):
        try:
            return float(self.display_var.get().replace(",", "."))
        except ValueError:
            return 0.0

    def _set_display(self, valor):
        if isinstance(valor, str):
            self.display_var.set(valor or "0")
            return
        if isinstance(valor, float) and abs(valor - round(valor)) < 1e-9:
            self.display_var.set(str(int(round(valor))))
            return
        texto = f"{valor:.10g}".replace(".", ",")
        self.display_var.set(texto)

    def _pressionar(self, tecla):
        if tecla == "CE":
            self._set_display(0)
            self._nova_entrada = True
            return
        if tecla == "C":
            self._acc = None
            self._op = None
            self._set_display(0)
            self._nova_entrada = True
            return
        if tecla == "⌫":
            cur = self.display_var.get()
            if self._nova_entrada or cur in ("0", ""):
                self._set_display(0)
            else:
                self._set_display(cur[:-1] if len(cur) > 1 else "0")
            self._nova_entrada = False
            return
        if tecla == "%":
            self._aplicar_porcentagem()
            return
        if tecla in ("+", "-", "*", "/"):
            if self._op and not self._nova_entrada:
                self._calcular()
            self._acc = self._valor_display()
            self._op = tecla
            self._nova_entrada = True
            return
        if tecla == "=":
            self._calcular()
            self._op = None
            self._acc = None
            self._nova_entrada = True
            return
        if tecla == ".":
            cur = "" if self._nova_entrada else self.display_var.get()
            if "," not in cur and "." not in cur:
                self.display_var.set((cur or "0") + ",")
            self._nova_entrada = False
            return
        if tecla.isdigit():
            if self._nova_entrada or self.display_var.get() == "0":
                self.display_var.set(tecla)
                self._nova_entrada = False
            else:
                self.display_var.set(self.display_var.get() + tecla)

    def _aplicar_porcentagem(self):
        """% estilo calculadora comercial: 500 + 10% => 50; fora de +/- divide por 100."""
        atual = self._valor_display()
        if self._op in ("+", "-") and self._acc is not None:
            self._set_display(self._acc * atual / 100.0)
        else:
            self._set_display(atual / 100.0)
        self._nova_entrada = True

    def _calcular(self):
        if self._op is None or self._acc is None:
            return
        b = self._valor_display()
        a = self._acc
        try:
            if self._op == "+":
                self._set_display(a + b)
            elif self._op == "-":
                self._set_display(a - b)
            elif self._op == "*":
                self._set_display(a * b)
            elif self._op == "/":
                self._set_display(a / b if b else 0)
            self._acc = self._valor_display()
        except Exception:
            self.display_var.set("Erro")

    def _confirmar_ok(self):
        if self.entry_alvo is not None:
            try:
                v = self._valor_display()
                self.entry_alvo.delete(0, tk.END)
                self.entry_alvo.insert(0, f"{v:.2f}")
                self.entry_alvo.event_generate("<KeyRelease>")
            except Exception:
                pass
        self.win.destroy()


def abrir_calculadora(parent, entry_alvo=None):
    """Abre calculadora em layout padrão; OK envia valor ao entry_alvo."""
    _CalculadoraPadrao(parent, entry_alvo)


def abrir_calendario_info(parent):
    """Exibe calendário do mês atual (utilidade informativa)."""
    hoje = datetime.now()
    texto = calendar.month(hoje.year, hoje.month)
    messagebox.showinfo(
        "Calendário",
        f"Hoje: {hoje.strftime('%d/%m/%Y')}\n\n{texto}",
        parent=parent,
    )


def _pasta_notas_salvas():
    pasta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notas_salvas")
    os.makedirs(pasta, exist_ok=True)
    return pasta


def _listar_arquivos_notas():
    pasta = _pasta_notas_salvas()
    return sorted(
        [f for f in os.listdir(pasta) if f.lower().endswith(".txt")],
        reverse=True,
    )


def abrir_anotacoes(parent):
    """Anotações: salvar, buscar e excluir arquivos em notas_salvas."""
    win = tk.Toplevel(parent)
    win.title("Anotações")
    win.configure(bg=PALETA["bg_fundo"])
    calcular_dimensoes_janela(win, largura_desejada=560, altura_desejada=480)

    corpo = tk.Frame(win, bg=PALETA["bg_fundo"], padx=10, pady=8)
    corpo.pack(fill="both", expand=True)
    corpo.columnconfigure(1, weight=1)
    corpo.rowconfigure(1, weight=1)

    tk.Label(corpo, text="Notas salvas", bg=PALETA["bg_fundo"], font=("Segoe UI", 9, "bold")).grid(
        row=0, column=0, sticky="w", pady=(0, 4),
    )
    lista_frame = tk.Frame(corpo, bg=PALETA["bg_fundo"])
    lista_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
    scroll = ttk.Scrollbar(lista_frame, orient="vertical")
    lst = tk.Listbox(
        lista_frame, font=("Segoe UI", 9), height=16, width=28,
        yscrollcommand=scroll.set, relief="flat",
        highlightthickness=1, highlightbackground=PALETA["cor_borda"],
    )
    scroll.config(command=lst.yview)
    scroll.pack(side="right", fill="y")
    lst.pack(side="left", fill="both", expand=True)

    direita = tk.Frame(corpo, bg=PALETA["bg_fundo"])
    direita.grid(row=0, column=1, rowspan=2, sticky="nsew")
    direita.rowconfigure(2, weight=1)
    direita.columnconfigure(0, weight=1)

    tk.Label(direita, text="Nome da nota", bg=PALETA["bg_fundo"], font=("Segoe UI", 9, "bold")).grid(
        row=0, column=0, sticky="w",
    )
    ent_nome = tk.Entry(
        direita, font=("Segoe UI", 10), relief="flat",
        highlightthickness=1, highlightbackground=PALETA["cor_borda"],
    )
    ent_nome.grid(row=1, column=0, sticky="ew", pady=(2, 6), ipady=4)
    ent_nome.insert(0, datetime.now().strftime("nota_%Y%m%d_%H%M%S"))

    txt = tk.Text(
        direita, font=("Segoe UI", 10), wrap="word", relief="flat",
        highlightthickness=1, highlightbackground=PALETA["cor_borda"],
    )
    txt.grid(row=2, column=0, sticky="nsew")

    def atualizar_lista(selecionar=None):
        lst.delete(0, tk.END)
        arquivos = _listar_arquivos_notas()
        for arq in arquivos:
            lst.insert(tk.END, arq)
        if selecionar and selecionar in arquivos:
            idx = arquivos.index(selecionar)
            lst.selection_set(idx)
            lst.see(idx)

    def caminho_nota(nome):
        n = nome.strip()
        if not n.lower().endswith(".txt"):
            n += ".txt"
        return os.path.join(_pasta_notas_salvas(), n)

    def salvar_nota():
        nome = ent_nome.get().strip() or datetime.now().strftime("nota_%Y%m%d_%H%M%S")
        caminho = caminho_nota(nome)
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(txt.get("1.0", tk.END).strip())
        ent_nome.delete(0, tk.END)
        ent_nome.insert(0, os.path.basename(caminho))
        atualizar_lista(os.path.basename(caminho))
        messagebox.showinfo("Anotações", "Nota salva com sucesso.", parent=win)

    def buscar_nota():
        sel = lst.curselection()
        if sel:
            nome = lst.get(sel[0])
        else:
            nome = ent_nome.get().strip()
        if not nome:
            messagebox.showwarning("Anotações", "Selecione ou informe o nome da nota.", parent=win)
            return
        caminho = caminho_nota(nome)
        if not os.path.isfile(caminho):
            messagebox.showwarning("Anotações", "Arquivo não encontrado.", parent=win)
            return
        with open(caminho, "r", encoding="utf-8") as f:
            conteudo = f.read()
        txt.delete("1.0", tk.END)
        txt.insert("1.0", conteudo)
        ent_nome.delete(0, tk.END)
        ent_nome.insert(0, os.path.basename(caminho))

    def excluir_nota():
        sel = lst.curselection()
        if not sel:
            messagebox.showwarning("Anotações", "Selecione uma nota na lista para excluir.", parent=win)
            return
        nome = lst.get(sel[0])
        if not confirmar(win, "Excluir nota", f"Excluir permanentemente:\n{nome}?"):
            return
        try:
            os.remove(caminho_nota(nome))
            txt.delete("1.0", tk.END)
            ent_nome.delete(0, tk.END)
            ent_nome.insert(0, datetime.now().strftime("nota_%Y%m%d_%H%M%S"))
            atualizar_lista()
            messagebox.showinfo("Anotações", "Nota excluída.", parent=win)
        except OSError as e:
            messagebox.showerror("Anotações", f"Não foi possível excluir: {e}", parent=win)

    lst.bind("<Double-1>", lambda _e: buscar_nota())

    rodape = tk.Frame(win, bg=PALETA["bg_fundo"], padx=10, pady=8)
    rodape.pack(fill="x")
    rodape.columnconfigure((0, 1, 2), weight=1, uniform="notas_btn")
    criar_botao_rodape(rodape, "Salvar Nota", salvar_nota, "acao1").grid(row=0, column=0, sticky="ew", padx=(0, 4), ipady=6)
    criar_botao_rodape(rodape, "Buscar Nota", buscar_nota, "acao2").grid(row=0, column=1, sticky="ew", padx=4, ipady=6)
    criar_botao_rodape(rodape, "Excluir Nota", excluir_nota, "sair").grid(row=0, column=2, sticky="ew", padx=(4, 0), ipady=6)

    atualizar_lista()


def abrir_configuracoes(parent):
    """Placeholder para futuras configurações (impressora, tema, etc.)."""
    messagebox.showinfo(
        "Configurações",
        "Módulo de configurações reservado para versões futuras.\n"
        "• Impressora de recibos\n"
        "• Backup automático\n"
        "• Tema e cores",
        parent=parent,
    )


def filtro_data_periodo(opcao, data_str):
    """Retorna True se data_str (DD/MM/YYYY ou YYYY-MM-DD) está no período."""
    if not data_str:
        return False
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(str(data_str), fmt).date()
            break
        except ValueError:
            dt = None
    if not dt:
        return False
    hoje = datetime.now().date()
    if opcao == "Dia":
        return dt == hoje
    if opcao == "Semana":
        inicio = hoje - timedelta(days=hoje.weekday())
        fim = inicio + timedelta(days=6)
        return inicio <= dt <= fim
    if opcao == "Mês":
        return dt.year == hoje.year and dt.month == hoje.month
    return True
