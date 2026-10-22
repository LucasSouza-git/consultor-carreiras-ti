# Consultor Inteligente de Carreiras em TI

Sistema especialista baseado em regras que entrevista o usuário e recomenda a trilha de carreira em TI mais adequada entre **10 opções**, explicando a decisão com base nas regras disparadas.

Projeto da disciplina de **Inteligência Artificial** — Ciência da Computação, UNIPAC Barbacena (Prof. Felipe Roncalli de Paula Carneiro).

## Funcionalidades

- **Entrevista dinâmica** com 7 perguntas objetivas: afinidade com matemática, preferência de atuação diária, linguagem/ferramenta, tipo de valor a entregar, ambiente preferido, afinidade com negócios e objetivo profissional.
- **Motor de inferência** com a biblioteca [Experta](https://github.com/nilp0inter/experta) (encadeamento para frente) e **33 regras** cruzadas.
- **Justificativa transparente:** exibe a trilha recomendada, as regras que mais pesaram, a segunda opção e a pontuação de todas as trilhas.
- **Nível de confiança** (alta, média ou baixa) para sinalizar quando o perfil é pouco definido.
- **Interface web** em Streamlit.

## As 10 trilhas

Back-end · Front-end & UI/UX · Ciência de Dados e Machine Learning · Engenharia de Dados · Cibersegurança · DevOps & SRE · Computação em Nuvem · Mobile · Engenharia de Qualidade e Testes (QA) · Gestão de Produtos

## Estrutura do repositório

```
consultor-carreiras-ti/
├── evidencias/            # capturas de tela da aplicação (prints)
├── .gitignore             # arquivos ignorados pelo Git
├── Mtriz-decisao.MD       # engenharia de conhecimento e tabela de regras
├── README.md              # documentação do projeto
├── app.py                 # interface web Streamlit
├── motor_inferencia.py    # motor de inferência (catálogo de trilhas, fatos e regras)
├── perguntas.py           # perguntas e opções da entrevista
├── requirements.txt       # dependências
└── testes.py              # testes das regras com personas
```

## Requisitos

- Python **3.10 ou superior**
- pip

## Instalação e execução

```bash
# 1. Clonar o repositório
git clone https://github.com/LucasSouza-git/consultor-carreiras-ti.git
cd consultor-carreiras-ti

# 2. (Opcional) criar e ativar um ambiente virtual
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

# 3. Instalar as dependências
pip install -r requirements.txt

# 4. Executar a aplicação web
streamlit run app.py
```

O Streamlit abre o app em `http://localhost:8501`.

### Usando o GitHub Codespaces (sem instalar nada)

1. No repositório, clique em **Code → Codespaces → Create codespace on main**.
2. No terminal do Codespace, rode `pip install -r requirements.txt` e `streamlit run app.py`.
3. Abra a porta **8501** quando o aviso aparecer.

## Executando os testes

```bash
python testes.py              # relatório com as 14 personas
python testes.py --detalhes   # inclui a justificativa de cada persona
pytest testes.py              # opcional: requer `pip install pytest`
```

A validação usa **14 personas** (as 4 do enunciado: analítica, infra/segurança, visual/front-end e negócios/produto, mais perfis para cobrir as 10 trilhas e casos de ambiguidade). Todas recebem a trilha esperada. Os detalhes estão em [`matriz_decisao.md`](matriz_decisao.md), e as capturas de tela, em [`evidencias/`](evidencias/).

## Como funciona

1. As respostas do usuário viram o fato `Perfil`.
2. Cada regra `@Rule` casa com o `Perfil` e, ao disparar, **soma ou subtrai pontos** de uma ou mais trilhas, registrando o motivo.
3. Uma regra final de baixa prioridade (`salience=-100`) apura o placar, desempata e declara o fato `Recomendacao`.

**Exemplo de regra (R11):** `SE matematica = alta E atuacao = analise_dados ENTÃO Ciência de Dados +6`.

**Evitando ambiguidades.** Regras cruzadas e regras com pontuação negativa separam trilhas parecidas:

| Par | Como é diferenciado |
|---|---|
| Ciência de Dados × Eng. de Dados | Ciência exige matemática alta e foco em *insights*. Engenharia prioriza pipelines e dados prontos (R11–R18). |
| Front-end × Mobile | Interfaces visuais em ambiente móvel favorecem Mobile (R10). |
| DevOps × Cloud | DevOps é automação e operação. Cloud é arquitetura e planejamento escalável (R22–R26). |
| Produto × perfis técnicos | Interesse em produto sem afinidade com negócio perde pontos (R33). |

**Desempate:** maior pontuação, depois mais regras positivas disparadas, depois ordem fixa do catálogo.
**Confiança:** `alta` (margem ≥ 5 sobre a 2ª colocada), `média` (2 a 4) e `baixa` (margem < 2 ou pontuação < 6).

A tabela completa das 33 regras está em [`matriz_decisao.md`](matriz_decisao.md).

## Nota técnica: compatibilidade do Experta

O Experta 1.9.x usa `collections.Mapping`, removido no Python 3.10+. O topo do `motor_inferencia.py` contém um pequeno ajuste de compatibilidade que resolve isso. **Não remova esse trecho.**

## Tecnologias

Python 3.10+ · Experta · Streamlit · GitHub

## Autor

[Seu nome] — Ciência da Computação, UNIPAC Barbacena
