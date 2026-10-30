# Consultor Avançado de Carreiras em TI

Sistema especialista com **tratamento de incerteza e pontuação ponderada**. Em vez de indicar uma única trilha, ele analisa o perfil gradual do usuário, calcula a **compatibilidade percentual** das 10 trilhas de TI, mostra as **3 mais compatíveis**, identifica as **lacunas de competência (skill gaps)** até o nível Júnior e gera um **roadmap personalizado** com estudos, certificações e projetos para o portfólio no GitHub.

Projeto da disciplina de **Inteligência Artificial**, Ciência da Computação, UNIPAC Barbacena (Prof. Felipe Roncalli de Paula Carneiro).

## Sumário

- [O que o sistema faz](#o-que-o-sistema-faz)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Instalação e execução](#instalação-e-execução)
- [Testes](#testes)
- [Como o cálculo funciona](#como-o-cálculo-funciona)
- [Gaps e roadmap](#gaps-e-roadmap)
- [Como editar a base de conhecimento](#como-editar-a-base-de-conhecimento)
- [Interface](#interface)
- [Evidências](#evidências)
- [Histórico: Etapa 1](#histórico-etapa-1)
- [Limitações](#limitações)

## O que o sistema faz

1. **Entrevista em 3 passos** (wizard): Perfil pessoal, Afinidades técnicas e Objetivos de carreira. São 19 perguntas: 13 afinidades em escala de 1 a 5 e 6 perguntas de escolha.
2. **Ranking multi-trilha**: Top 3 com a compatibilidade em %, radar com as 10 trilhas e tabela completa.
3. **Justificativa transparente**: mostra os fatores a favor, os pontos de atenção e as regras que somaram ou tiraram pontos, em pontos percentuais.
4. **Tratamento de casos ambíguos**: avisa quando há empate técnico (perfil híbrido), compatibilidade fraca ou notas todas iguais.
5. **Análise de gaps**: o usuário marca o que já domina na trilha escolhida, e o sistema calcula a prontidão para vagas Júnior.
6. **Plano de ação**: lacunas em ordem de estudo, roadmap em 3 fases com prazo estimado, certificações, projetos de portfólio e download em Markdown.

As 10 trilhas: Back-end · Front-end & UI/UX · Ciência de Dados e Machine Learning · Engenharia de Dados · Cibersegurança · DevOps & SRE · Computação em Nuvem · Mobile · Engenharia de Qualidade e Testes (QA) · Gestão de Produtos.

### Requisitos do trabalho e onde estão

| Requisito | Onde está |
|---|---|
| Entrada gradual (Likert de 1 a 5) | `regras_carreiras.json` (perguntas e telas) e `app.py` (interface) |
| Ranking multi-trilha com % | `motor_inferencia.py` (`avaliar`) |
| Análise de gaps até o nível Júnior | `gaps_roadmap.py` (`analisar_gaps`) |
| Roadmap personalizado | `gaps_roadmap.py`, com o conteúdo em `trilhas.json` |
| Base de conhecimento desacoplada | `regras_carreiras.json` e `trilhas.json`, validados por `conhecimento.py` |
| Ponderação e penalidades | `motor_inferencia.py`, com 22 regras cruzadas em `regras_carreiras.json` |
| Interface em etapas (wizard) | `app.py` |
| Testes de robustez e casos limite | `testes.py` (26 testes) |

## Estrutura do repositório

```
consultor-carreiras-ti/
├── app.py                  # interface Streamlit (wizard em etapas)
├── motor_inferencia.py     # motor de inferência: soma ponderada, penalidades e ranking
├── gaps_roadmap.py         # análise de gaps e geração do roadmap
├── conhecimento.py         # carregamento e validação dos arquivos JSON
├── regras_carreiras.json   # base de conhecimento: perguntas, pesos e regras cruzadas
├── trilhas.json            # base de conhecimento: competências, certificações e projetos
├── testes.py               # personas, casos limite e testes de robustez
├── gerar_matriz.py         # gera matriz_decisao.md a partir dos JSON
├── matriz_decisao.md       # Fase 1: matriz de pesos e estrutura do JSON
├── estilo.css              # identidade visual da interface
├── .streamlit/
│   └── config.toml         # tema do Streamlit
├── evidencias/             # capturas de tela da aplicação e dos testes
├── requirements.txt        # dependências
├── .gitignore              # arquivos ignorados pelo Git
└── README.md               # este arquivo
```

O fluxo entre os módulos:

```
regras_carreiras.json ─┐
trilhas.json ──────────┴─> conhecimento.py ─┬─> motor_inferencia.py ─┐
                                            └─> gaps_roadmap.py ─────┴─> app.py (Streamlit)
```

Nenhum módulo Python contém perguntas, pesos ou conteúdo das trilhas: tudo vem dos dois arquivos JSON.

## Instalação e execução

Requer **Python 3.10 ou superior**.

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

## Testes

```bash
python testes.py              # relatório com as personas e os casos limite
python testes.py --detalhes   # inclui a justificativa de cada caso
pytest testes.py              # opcional: pip install pytest
```

O relatório valida **18 casos**: 10 personas típicas (uma por trilha) e 8 casos limite. Os 26 testes automatizados cobrem ainda:

- perfil híbrido dados × web (empate técnico);
- quem gosta de dados, mas evita matemática;
- separação entre Cloud × DevOps e Front-end × Mobile;
- notas todas iguais (1, 3 e 5);
- conflito entre lógica baixa e interesse em Back-end;
- respostas inválidas e base de conhecimento inválida;
- troca de pesos no JSON sem alterar o código;
- gaps, prazos, certificações e projetos do plano.

A matriz completa de pesos e regras está em [`matriz_decisao.md`](matriz_decisao.md).

## Como o cálculo funciona

1. Cada resposta vira uma **intensidade** de 0 a 1. Likert: `(nota − 1) / 4`. Escolha: `1` para a opção marcada.
2. A intensidade é multiplicada pela **importância da pergunta** e pelo **peso da trilha** (vindo do JSON):
   `pontos = importância × peso × intensidade`
3. A **base** é percentual: `100 × soma(pontos) / soma(máximos)`.
4. As **regras cruzadas** somam bônus ou penalidades, em pontos percentuais, quando combinações de respostas são conflitantes ou sinérgicas. Exemplos: lógica ≤ 2 tira pontos de Back-end, e matemática ≤ 2 com gosto por análise de dados empurra para Engenharia de Dados.
5. O percentual final fica entre 0 e 100. O ranking desempata por pontos brutos e depois pela ordem do catálogo.
6. O motor classifica a **leitura** do resultado:

| Leitura | Quando acontece |
|---|---|
| Clara | O 1º lugar se destaca das demais trilhas |
| Híbrida | Trilhas a até 5 pontos percentuais do 1º lugar (empate técnico) |
| Fraca | O 1º lugar fica abaixo de 45% |
| Indiferenciada | Todas as afinidades receberam a mesma nota |

Esse motor é próprio (soma ponderada), sem a biblioteca Experta. O enunciado permitia as duas abordagens.

## Gaps e roadmap

Depois do resultado, o usuário escolhe uma das três trilhas e marca no checklist o que já domina. O sistema calcula:

- **Prontidão para Júnior:** soma dos pesos das competências marcadas dividida pela soma total (essencial = 3, importante = 2, desejável = 1).
- **Lacunas em ordem de estudo:** fundamentos primeiro e, dentro de cada fase, as mais importantes.
- **Roadmap em 3 fases** (Fundamentos, Ferramentas e prática, Consolidação), com semanas estimadas conforme as horas semanais informadas.
- **Certificações** adequadas ao momento. As avançadas ficam marcadas como "para depois".
- **Projetos de portfólio**, com indicação de por qual começar, e boas práticas para o repositório.

A base tem 113 competências de nível Júnior, 42 certificações e 30 projetos de portfólio distribuídos pelas 10 trilhas.

## Como editar a base de conhecimento

Tudo o que muda o resultado está nos arquivos JSON, sem tocar no código:

| Para... | Edite |
|---|---|
| Mudar o peso de uma afinidade | `regras_carreiras.json` → `perguntas` → pergunta → `pesos` |
| Criar uma penalidade ou bônus | `regras_carreiras.json` → `regras_cruzadas` (campos `se` e `efeito`, em pontos percentuais) |
| Mudar perguntas ou telas do wizard | `regras_carreiras.json` → `perguntas` e `passos` |
| Atualizar competências, certificações ou projetos | `trilhas.json` |

Ao iniciar, `conhecimento.py` valida a base (trilhas e perguntas existentes, pesos válidos, telas completas) e mostra todos os erros em português. Depois de editar, atualize a documentação com:

```bash
python gerar_matriz.py
```

## Interface

A interface segue a metáfora de **trilha sinalizada**: o progresso é um caminho com marcos numerados. As decisões de usabilidade se apoiam nas [10 heurísticas de Nielsen](https://www.nngroup.com/articles/ten-usability-heuristics/):

| Heurística | Como aparece no app |
|---|---|
| Visibilidade do estado do sistema | Caminho com marcos mostra a etapa atual, as concluídas e as que faltam |
| Correspondência com o mundo real | Linguagem simples e dicas sob cada pergunta |
| Controle e liberdade do usuário | Botões Voltar e Recomeçar, e "Alterar" no resultado |
| Consistência e padrões | Mesmos nomes para as mesmas ações e um único estilo de botão e cartão |
| Prevenção de erros | O botão Continuar só ativa depois de responder tudo na tela |
| Reconhecer em vez de lembrar | Respostas preservadas ao voltar e checklist com as marcações mantidas |
| Ajuda a reconhecer e corrigir erros | Se faltar resposta, o app leva à tela pendente |
| Ajuda e documentação | Seção "Como funciona" na barra lateral |

Acessibilidade: contraste alto, fonte de leitura facilitada (Atkinson Hyperlegible), foco visível no teclado e estados indicados por texto e forma, não só por cor. O visual fica em `estilo.css` e o tema base em `.streamlit/config.toml`.

## Evidências

A pasta [`evidencias/`](evidencias/) reúne capturas de tela da aplicação e dos testes. As quatro primeiras (`Tela1.png`, `Tela_Respondida.png`, `Tela_resultado.png` e `Pontuação_trila.png`) são da Etapa 1.

## Histórico: Etapa 1

A primeira etapa do projeto era um sistema especialista com a biblioteca [Experta](https://github.com/nilp0inter/experta): 7 perguntas categóricas, 33 regras `SE-ENTÃO` com encadeamento para frente e uma única trilha recomendada, com justificativa pelas regras disparadas. Ela foi substituída por esta versão, mas continua disponível no histórico do Git, no commit [`7afa3c5`](https://github.com/LucasSouza-git/consultor-carreiras-ti/tree/7afa3c5).

Para executá-la:

```bash
git checkout 7afa3c5
pip install -r requirements.txt      # inclui experta==1.9.4
streamlit run app.py
git checkout main                    # para voltar à versão atual
```

## Limitações

- Os **pesos e penalidades** foram definidos manualmente, com base em conhecimento do domínio, e validados com personas. Não foram ajustados com dados reais de usuários.
- As **horas estimadas** e os prazos são referências médias, e o ritmo real varia de pessoa para pessoa.
- **Certificações** mudam com frequência (exames são descontinuados e substituídos). Confira sempre o site do emissor antes de se inscrever. A base já considera, por exemplo, que o Azure Data Engineer (DP-203) foi substituído pelo Fabric Data Engineer (DP-700).
- O sistema orienta, mas não substitui conversar com profissionais da área.

## Tecnologias

Python 3.10+ · Streamlit · Pandas · JSON · GitHub

## Autor

Lucas de Souza Carmo, Ciência da Computação, UNIPAC Barbacena
