# Consultor Inteligente de Carreiras em TI Etapa I

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



# Etapa 2: Consultor Avançado de Carreiras em TI

Sistema especialista com **tratamento de incerteza e pontuação ponderada**. Em vez de indicar uma única trilha, ele analisa o perfil gradual do usuário, calcula a **compatibilidade percentual** das 10 trilhas, mostra as **3 mais compatíveis**, identifica as **lacunas de competência (skill gaps)** até o nível Júnior e gera um **roadmap personalizado** com estudos, certificações e projetos para o portfólio no GitHub.

Projeto da disciplina de Inteligência Artificial, Ciência da Computação, UNIPAC Barbacena. A Etapa 1 (motor com Experta) continua intacta na raiz do repositório.

## Requisitos do trabalho e onde estão

| Requisito | Onde está |
|---|---|
| Entrada gradual (Likert de 1 a 5) | 13 afinidades em escala de 1 a 5, mais perguntas de perfil e objetivos (`regras_carreiras.json`) |
| Ranking multi-trilha com % | `motor_pontuacao.avaliar`, com Top 3, radar e tabela completa |
| Análise de gaps até o nível Júnior | `gaps_roadmap.analisar_gaps`, com checklist de competências da trilha escolhida |
| Roadmap personalizado | Fases com semanas estimadas, certificações e projetos de portfólio (`trilhas.json`) |
| Base de conhecimento desacoplada | `base_conhecimento/*.json`, validada por `conhecimento.py` |
| Mecanismo de ponderação e penalidades | Peso × resposta, somado por trilha, mais 22 regras cruzadas |
| Interface em etapas (wizard) | `app.py`: Passo 1 Perfil pessoal, Passo 2 Afinidades técnicas, Passo 3 Objetivos de carreira |
| Testes de robustez e casos limite | `testes.py`, com 26 testes |

## Estrutura

```
etapa_2/
├── app.py                      # interface Streamlit (wizard)
├── motor_pontuacao.py          # motor de inferência com soma ponderada
├── gaps_roadmap.py             # análise de gaps e geração do roadmap
├── conhecimento.py             # carregamento e validação do JSON
├── base_conhecimento/
│   ├── regras_carreiras.json   # perguntas, pesos e regras cruzadas
│   └── trilhas.json            # competências, certificações e projetos
├── gerar_matriz.py             # gera matriz_pesos.md a partir do JSON
├── matriz_pesos.md             # Fase 1: matriz de pesos e estrutura do JSON
├── estilo.css                  # identidade visual
├── .streamlit/config.toml      # tema
├── testes.py                   # Fase 5: personas e casos limite
└── requirements.txt
```

## Instalação e execução

```bash
# na raiz do repositório
pip install -r etapa_2/requirements.txt
streamlit run etapa_2/app.py
```

Também funciona de dentro da pasta (`cd etapa_2` e depois `streamlit run app.py`). Requer Python 3.10 ou superior. No GitHub Codespaces, abra a porta 8501 quando o aviso aparecer.

## Testes

```bash
python etapa_2/testes.py              # relatório (útil para capturas de tela)
python etapa_2/testes.py --detalhes   # inclui a justificativa de cada caso
pytest etapa_2/testes.py              # opcional: pip install pytest
```

Cobertura: 10 personas (uma por trilha), perfil híbrido dados × web (empate técnico), "gosta de dados mas evita matemática", Cloud × DevOps, Front-end × Mobile, notas todas iguais (1, 3 e 5), conflito lógica baixa × Back-end, respostas inválidas, base de conhecimento inválida, troca de base sem alterar o código, e gaps, prazos, certificações e projetos do plano.

## Como o cálculo funciona

1. Cada resposta vira uma **intensidade** de 0 a 1. Likert: `(nota − 1) / 4`. Escolha: `1` para a opção marcada.
2. A intensidade é multiplicada pela **importância da pergunta** e pelo **peso da trilha** (JSON): `pontos = importância × peso × intensidade`.
3. A **base** é percentual: `100 × soma(pontos) / soma(máximos)`.
4. As **regras cruzadas** somam bônus ou penalidades, em pontos percentuais, quando combinações de respostas são conflitantes ou sinérgicas. Exemplo: lógica ≤ 2 tira pontos de Back-end, e matemática ≤ 2 com gosto por análise de dados empurra para Engenharia de Dados.
5. O percentual final fica entre 0 e 100. O ranking desempata por pontos brutos e depois pela ordem do catálogo.
6. O motor classifica a leitura do resultado: **clara**, **híbrida** (trilhas a até 5 pp do 1º lugar), **fraca** (1º lugar abaixo de 45%) ou **indiferenciada** (todas as notas iguais). Quando há empate parcial ou respostas pouco informativas, o app avisa e explica.

A tela de resultado justifica o 1º lugar com os fatores a favor, os pontos de atenção e as regras que somaram ou tiraram pontos, sempre em pontos percentuais.

## Gaps e roadmap

Depois do resultado, o usuário escolhe uma das três trilhas e marca no checklist o que já domina. O sistema calcula:

- **Prontidão para Júnior:** soma dos pesos das competências marcadas dividida pela soma total (essencial = 3, importante = 2, desejável = 1).
- **Lacunas em ordem de estudo:** fundamentos primeiro e, dentro de cada fase, as mais importantes.
- **Roadmap em 3 fases** (Fundamentos, Ferramentas e prática, Consolidação), com semanas estimadas conforme as horas semanais informadas.
- **Certificações** adequadas ao momento (as avançadas ficam marcadas como "para depois").
- **Projetos de portfólio**, com indicação de por qual começar, e boas práticas para o repositório.
- **Download** do plano em Markdown.

## Como editar a base de conhecimento

Tudo o que muda o resultado está nos JSON, sem tocar no código:

- Mudar o peso de uma afinidade: `perguntas` → `<pergunta>` → `pesos` em `regras_carreiras.json`.
- Criar uma regra de penalidade: acrescente um item em `regras_cruzadas`, com `se` (condições) e `efeito` (pontos percentuais por trilha).
- Atualizar competências, certificações ou projetos: `trilhas.json`.

Ao iniciar, `conhecimento.validar` confere a base (trilhas e perguntas existentes, pesos válidos, telas completas) e mostra todos os erros em português. Depois de editar, rode `python etapa_2/gerar_matriz.py` para atualizar `matriz_pesos.md`.

## Limitações

- Os **pesos e penalidades** foram definidos manualmente, com base em conhecimento do domínio, e validados com personas. Não foram ajustados com dados reais de usuários.
- As **horas estimadas** e os prazos são referências médias, e o ritmo real varia de pessoa para pessoa.
- **Certificações** mudam com frequência (exames são descontinuados e substituídos). Confira sempre o site do emissor antes de se inscrever. Esta base já considera, por exemplo, que o Azure Data Engineer (DP-203) foi substituído pelo Fabric Data Engineer (DP-700).
- O sistema orienta, mas não substitui conversar com profissionais da área.

## Tecnologias

Python 3.10+ · Streamlit · Pandas · JSON · GitHub

## Nota técnica: compatibilidade do Experta

O Experta 1.9.x usa `collections.Mapping`, removido no Python 3.10+. O topo do `motor_inferencia.py` contém um pequeno ajuste de compatibilidade que resolve isso. **Não remova esse trecho.**

## Autor

Lucas de Souza Carmo — Ciência da Computação, UNIPAC Barbacena
