# Alê Sapatilhas — ERP / PDV Desktop

Alê Sapatilhas é um sistema desktop de gestão comercial para loja de calçados e confecções, pensado para uso em vendas presenciais, controle de estoque, fluxo financeiro e gestão de contatos.

Construído com **Python 3**, **Tkinter** e **SQLite**, o projeto reúne recursos de PDV moderno, registro de receitas/despesas, cadastro unificado de clientes e fornecedores, e controles de segurança para fluxo de caixa.

---

## Visão geral

O sistema entrega uma experiência de portfólio sólida para aplicações comerciais:

- Interface desktop responsiva com navegação por sidebar e telas modais centralizadas.
- PDV com carrinho, desconto em reais, cliente buscável por popup e pagamento direto.
- Modelo de dados unificado para contatos, incluindo clientes e fornecedores.
- Estoque controlado somente após confirmação de pagamento, evitando baixa prematura.
- Registro financeiro completo com contas a pagar, contas a receber e fluxo de caixa.
- Ferramentas auxiliares de produtividade: calculadora, calendário e anotação.

---

## Recursos principais

- PDV em duas colunas com seleção rápida de produtos e carrinho dinâmico.
- Busca de cliente com autocomplete e preenchimento automático de ficha.
- Desconto aplicado em valor fixo no fechamento da venda.
- Tratamento de parcelas para cartão de crédito e pagamentos parcelados.
- Registro de vendas pendentes e pagamentos com histórico financeiro.
- Controle de estoque integrado ao processo de pagamento.
- Cadastro de produtos com SKU, tipo, cor, tamanho, fornecedor e status.
- Gestão unificada de contatos para clientes e fornecedores.
- Registro de despesas e fluxo financeiro com senha de proteção de caixa.
- Organização de entregas via tabelas SQL e transações atômicas em SQLite.

---

## Tecnologias

- Python 3.10+
- Tkinter para interface gráfica nativa
- SQLite para persistência local leve
- Pillow para miniaturas de produto (opcional)

---

## Instalação

1. Clone este repositório:

```powershell
git clone https://github.com/alankardecjr/Prototipo_Ale_Sapatilhas.git
cd Prototipo_Ale_Sapatilhas\AleSapatilhasVs4.8.2
```

2. Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

3. Configure a senha do fluxo de caixa:

```powershell
copy secrets.local.json.example secrets.local.json
```

Edite `secrets.local.json` e defina o valor de `senha_fluxo_caixa`.

4. Execute a aplicação:

```powershell
python main.py
```

---

## Executando com dados de demonstração

Para popular a base com registros iniciais e testar rapidamente:

```powershell
python populardb.py
```

---

## Uso recomendado

1. Cadastre fornecedores/clientes em **NOVO CONTATOS**.
2. Cadastre produtos em **NOVO PRODUTOS**.
3. Acesse **NOVA VENDAS** para abrir o PDV.
4. Selecione cliente, adicione itens ao carrinho e finalize a venda.
5. Registre pagamentos em **Gerenciar Receitas** para efetivar a baixa de estoque.
6. Consulte despesas, contas a pagar e fluxo de caixa nas telas financeiras.

---

## Estrutura do projeto

```text
AleSapatilhasVs4.8.2/
├── main.py                 # Shell principal e navegação
├── database.py             # Camada de persistência e regras de negócio
├── ui_utils.py             # Estilos e helpers de interface
├── cadastro_clientes.py    # Cadastro unificado de clientes/fornecedores
├── cadastro_produtos.py    # Cadastro de produtos e estoque
├── cadastro_vendas.py      # PDV e checkout de vendas
├── gerenciar_despesas.py   # Lançamento e edição de despesas
├── gerenciar_receitas.py   # Pagamentos e contas a receber
├── populardb.py            # Import de dados de demonstração
├── test_sistema.py         # Testes funcionais
├── requirements.txt        # Dependências Python
├── secrets.local.json.example
└── AleSapatilhasVs4.8.2db   # Banco SQLite local (não versionar)
```

---

## Testes

```powershell
python test_sistema.py
```

O conjunto de testes cobre casos de cadastro de clientes, produtos, vendas, estoque, descontos e controle financeiro.

---

## Notas de portfólio

Este repositório demonstra habilidades em:

- desenvolvimento de aplicações desktop com Python/Tkinter;
- modelagem de dados e transações em SQLite;
- arquitetura de interface com separação entre UI e lógica de negócios;
- desenvolvimento de um fluxo comercial realista (PDV + financeiro);
- proteção de dados sensíveis em configuração local.

---

## Licença

Projeto de portfólio. Uso livre para demonstração de habilidades profissionais em desenvolvimento de aplicações comerciais.
