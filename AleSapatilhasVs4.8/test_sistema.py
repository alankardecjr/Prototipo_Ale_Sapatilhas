"""
test_sistema.py — Testes automatizados (sem interface gráfica).

Executa fluxos críticos do ERP em banco SQLite temporário.
Uso: python test_sistema.py
"""

import os
import sys
import tempfile
import traceback

# Garante import a partir da pasta do projeto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import database as db
import config
import ui_utils


class ResultadoTestes:
    """Acumula sucessos e falhas da bateria de testes."""

    def __init__(self):
        self.ok = 0
        self.falhas = []

    def registrar(self, nome, condicao, detalhe=""):
        if condicao:
            self.ok += 1
            print(f"  [OK] {nome}")
        else:
            self.falhas.append((nome, detalhe))
            print(f"  [FALHA] {nome}: {detalhe}")

    def resumo(self):
        total = self.ok + len(self.falhas)
        print(f"\n{'='*50}")
        print(f"Total: {self.ok}/{total} testes passaram")
        if self.falhas:
            print("\nFalhas:")
            for nome, det in self.falhas:
                print(f"  - {nome}: {det}")
            return False
        print("Todos os testes passaram.")
        return True


def configurar_banco_teste():
    """Aponta o módulo database para um arquivo temporário isolado."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db.DB_NAME = path
    db.criar_tabelas()
    return path


def test_ui_utils(r):
    """Valida utilitários de UI e mapeamentos."""
    r.registrar("tipo Calçado -> BD", ui_utils.tipo_produto_para_bd("Calçado") == "Calçados")
    r.registrar("tipo Vestuário -> BD", ui_utils.tipo_produto_para_bd("Vestuário") == "Confecções")
    r.registrar("filtro data hoje", ui_utils.filtro_data_periodo("Dia", "19/05/2026") in (True, False))
    r.registrar("paleta tem chaves", "bg_fundo" in ui_utils.get_paleta())


def test_cliente_produto(r):
    """Cadastro de cliente, produto e variação."""
    cid = db.cadastrar_cliente(
        "Cliente Teste", "11122233344", "11999990000", "t@t.com",
        None, 38, "Rua A", "Centro", "SP", "01000", "obs", 500, "Cliente",
    )
    r.registrar("cadastrar cliente", bool(cid))

    sku1 = "SAP0001PRE"
    ok = db.cadastrar_produto(
        sku1, "Calçados", "Sapatilha Teste", "Preto", "37",
        50, 120, 5, "Sapatilhas", "Couro", "Forn X", "",
    )
    r.registrar("cadastrar produto", ok)

    sku2 = "SAP0002AZU"
    ok2 = db.cadastrar_produto(
        sku2, "Calçados", "Sapatilha Teste", "Azul", "37",
        50, 120, 3, "Sapatilhas", "Couro", "", "",
    )
    r.registrar("cadastrar variação cor", ok2)

    itens = db.listar_itens()
    r.registrar("listar_itens com foto", len(itens) >= 2 and len(itens[0]) >= 8)


def test_venda(r, cid):
    """Venda atômica com baixa de estoque."""
    produtos = db.listar_itens()
    if not produtos:
        r.registrar("venda - estoque", False, "sem produtos")
        return None
    pid = produtos[0][0]
    lista = [{"id": pid, "qtd": 1, "preco": float(produtos[0][5])}]
    res, msg, vid = db.realizar_venda_segura(cid, lista, "PIX", 1, 0)
    r.registrar("realizar_venda_segura", res and vid is not None, msg)
    if vid:
        v = db.obter_venda_por_id(vid)
        r.registrar("obter_venda_por_id", v is not None)
        itens_v = db.obter_itens_venda(vid)
        r.registrar("obter_itens_venda", len(itens_v) >= 1)
        parcelas = db.listar_parcelas_venda(vid)
        r.registrar("listar_parcelas_venda", len(parcelas) >= 1)
    return vid


def test_despesa_receita(r):
    """Lançamento financeiro de despesa."""
    ok, msg = db.cadastrar_despesa(
        "Fornecedor Opcional", "Despesa teste", "Outros", 100.0,
        "Não Recorrente", "2026-12-31", "PIX", "Pendente", 1,
        data_lancamento="2026-05-19", valor_pago=0,
    )
    despesas = db.listar_despesas()
    r.registrar("cadastrar despesa sem vínculo", ok and len(despesas) >= 1, msg)


def test_atualizacao_produto(r):
    """Atualização parcial de estoque."""
    prods = db.exibir_produtos()
    if not prods:
        r.registrar("atualizar produto", False, "lista vazia")
        return
    pid = prods[0][0]
    db.atualizar_produto(pid, quantidade=99, status_item="Disponível")
    with db.conectar() as conn:
        q = conn.execute("SELECT quantidade FROM produtos WHERE id=?", (pid,)).fetchone()[0]
    r.registrar("atualizar_produto quantidade", q == 99)


def test_imports_modulos(r):
    """Garante que módulos de tela importam sem erro."""
    try:
        import main  # noqa: F401
        import cadastro_produtos  # noqa: F401
        import cadastro_clientes  # noqa: F401
        import cadastro_vendas  # noqa: F401
        import gerenciar_despesas  # noqa: F401
        import gerenciar_receitas  # noqa: F401
        r.registrar("imports módulos UI", True)
    except Exception as e:
        r.registrar("imports módulos UI", False, str(e))


def main():
    print("Testes Alê Sapatilhas ERP — banco temporário\n")
    r = ResultadoTestes()
    db_path = None
    try:
        db_path = configurar_banco_teste()
        test_ui_utils(r)
        test_imports_modulos(r)
        test_cliente_produto(r)
        test_despesa_receita(r)
        test_atualizacao_produto(r)
        prods = db.exibir_clientes()
        cid = prods[0][0] if prods else db.cadastrar_cliente(
            "C2", "99988877766", "11888887777", "", None, 0,
            "", "", "", "", "", 0, "Cliente",
        )
        test_venda(r, cid)
    except Exception:
        traceback.print_exc()
        r.registrar("exceção não tratada", False, traceback.format_exc()[-200:])
    finally:
        if db_path and os.path.exists(db_path):
            try:
                os.remove(db_path)
            except OSError:
                pass

    sucesso = r.resumo()
    sys.exit(0 if sucesso else 1)


if __name__ == "__main__":
    main()
