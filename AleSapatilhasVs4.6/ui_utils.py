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
    "cor_btn_acao": "#425074",
    "cor_hover_btn": "#6F7CA0",
    "cor_hover_field": "#484AD6"
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
        # Maximiza deixando espaço para barra de tarefas (~70px)
        root.geometry(f"{largura_tela}x{altura_tela - 70}+0+0")
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
    """Retorna a paleta de cores padronizada"""
    return PALETA.copy()

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

    def __init__(self, master, entry_alvo, titulo="Selecionar data"):
        """Exibe o mês atual e grava a data escolhida em entry_alvo."""
        super().__init__(master)
        self.entry_alvo = entry_alvo
        self.title(titulo)
        self.configure(bg=PALETA["bg_fundo"])
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        hoje = datetime.now()
        self.ano = tk.IntVar(value=hoje.year)
        self.mes = tk.IntVar(value=hoje.month)

        topo = tk.Frame(self, bg=PALETA["bg_fundo"], padx=10, pady=8)
        topo.pack(fill="x")
        tk.Button(topo, text="◀", command=self._mes_anterior, width=3).pack(side="left")
        self.lbl_mes = tk.Label(topo, text="", font=("Segoe UI", 10, "bold"), bg=PALETA["bg_fundo"])
        self.lbl_mes.pack(side="left", expand=True)
        tk.Button(topo, text="▶", command=self._mes_proximo, width=3).pack(side="right")

        self.grid_dias = tk.Frame(self, bg=PALETA["bg_fundo"], padx=8, pady=4)
        self.grid_dias.pack()
        for i, d in enumerate(["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]):
            tk.Label(self.grid_dias, text=d, width=4, font=("Segoe UI", 8, "bold"),
                     bg=PALETA["bg_fundo"]).grid(row=0, column=i)

        self._desenhar_dias()
        calcular_dimensoes_janela(self, largura_desejada=280, altura_desejada=320)

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
        self.lbl_mes.config(text=f"{calendar.month_name[mes]} / {ano}")
        linha, col = 1, 0
        for semana in calendar.monthcalendar(ano, mes):
            for dia in semana:
                if dia == 0:
                    col += 1
                    continue
                btn = tk.Button(
                    self.grid_dias, text=str(dia), width=4, relief="flat",
                    command=lambda d=dia: self._selecionar(d),
                )
                btn.grid(row=linha, column=col)
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


def criar_botao_rodape(parent, texto, cor, comando, paleta=None):
    """Botão de rodapé com hover padronizado."""
    p = paleta or PALETA
    btn = tk.Button(
        parent, text=texto, bg=cor, fg="white", font=("Segoe UI", 10, "bold"),
        relief="flat", cursor="hand2", command=comando,
    )
    btn.bind("<Enter>", lambda _e: btn.config(bg=p["cor_hover_btn"]))
    btn.bind("<Leave>", lambda _e: btn.config(bg=cor))
    return btn


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


def abrir_calculadora(parent):
    """Calculadora simples embutida."""
    win = tk.Toplevel(parent)
    win.title("Calculadora")
    win.configure(bg=PALETA["bg_fundo"])
    win.transient(parent)
    calcular_dimensoes_janela(win, largura_desejada=260, altura_desejada=340)

    display = tk.Entry(win, font=("Segoe UI", 14), justify="right")
    display.pack(fill="x", padx=10, pady=10)
    expr = {"txt": ""}

    def press(tecla):
        if tecla == "C":
            expr["txt"] = ""
        elif tecla == "=":
            try:
                expr["txt"] = str(eval(expr["txt"]))
            except Exception:
                expr["txt"] = "Erro"
        else:
            expr["txt"] += tecla
        display.delete(0, tk.END)
        display.insert(0, expr["txt"])

    grid = tk.Frame(win, bg=PALETA["bg_fundo"])
    grid.pack(padx=10, pady=5)
    teclas = [
        "7", "8", "9", "/",
        "4", "5", "6", "*",
        "1", "2", "3", "-",
        "C", "0", "=", "+",
    ]
    for i, t in enumerate(teclas):
        tk.Button(grid, text=t, width=5, command=lambda x=t: press(x)).grid(
            row=i // 4, column=i % 4, padx=2, pady=2
        )


def abrir_calendario_info(parent):
    """Exibe calendário do mês atual (utilidade informativa)."""
    hoje = datetime.now()
    texto = calendar.month(hoje.year, hoje.month)
    messagebox.showinfo(
        "Calendário",
        f"Hoje: {hoje.strftime('%d/%m/%Y')}\n\n{texto}",
        parent=parent,
    )


def abrir_anotacoes(parent):
    """Bloco de anotações rápidas salvo em arquivo local."""
    win = tk.Toplevel(parent)
    win.title("Anotações")
    win.configure(bg=PALETA["bg_fundo"])
    calcular_dimensoes_janela(win, largura_desejada=420, altura_desejada=380)
    txt = tk.Text(win, font=("Segoe UI", 10), wrap="word")
    txt.pack(fill="both", expand=True, padx=10, pady=10)
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "anotacoes_erp.txt")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            txt.insert("1.0", f.read())

    def salvar():
        with open(path, "w", encoding="utf-8") as f:
            f.write(txt.get("1.0", tk.END).strip())
        messagebox.showinfo("Anotações", "Anotações salvas.", parent=win)

    tk.Button(win, text="Salvar", command=salvar, bg=PALETA["cor_btn_acao"], fg="white").pack(pady=8)


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
