# Fase 1: Engenharia do Conhecimento e Modelagem JSON (Etapa 2)

_Documento gerado por `gerar_matriz.py` a partir de `base_conhecimento/`. Não edite à mão: altere o JSON e gere de novo._

## 1. Arquivos da base de conhecimento

| Arquivo | Conteúdo |
|---|---|
| `base_conhecimento/regras_carreiras.json` | Parâmetros, telas do wizard, perguntas com pesos por trilha e regras cruzadas (penalidades e bônus) |
| `base_conhecimento/trilhas.json` | Características das 10 trilhas: competências de nível Júnior, certificações, projetos de portfólio e fases do roadmap |

O código Python (`conhecimento.py`, `motor_pontuacao.py`, `gaps_roadmap.py`, `app.py`) **não contém** perguntas, pesos nem conteúdo de trilhas. Ao carregar, `conhecimento.validar` confere a consistência da base e lista todos os problemas encontrados.

## 2. Estrutura do `regras_carreiras.json`

```text
parametros           limiares de empate e de compatibilidade fraca, faixas de rótulo e escala Likert
passos[]             passos do wizard, cada um com telas[] que listam os ids das perguntas
perguntas{id}        tipo (likert | escolha), texto, ajuda, importancia e pesos (por trilha)
  likert             pesos: {trilha: 0 a 10}
  escolha            opcoes: {opcao: {rotulo, pesos: {trilha: 0 a 10}}}
regras_cruzadas[]    id, descricao, se[] (pergunta, op, valor) e efeito {trilha: pontos percentuais}
```

## 3. Modelo de cálculo

Intensidade da resposta: Likert `(nota − 1) / 4`; escolha, `1` para a opção marcada.

```text
pontos(trilha)   = Σ importância × peso(trilha) × intensidade
máximo(trilha)   = Σ importância × maior peso possível da trilha
base(trilha)     = 100 × pontos / máximo
final(trilha)    = limitar(base + Σ ajustes das regras cruzadas, 0, 100)
```

Empate técnico: trilhas a até **5 pp** do 1º lugar. Compatibilidade fraca: 1º lugar abaixo de **45%**.

Faixas: ≥ 80%: Muito compatível; ≥ 60%: Compatível; ≥ 40%: Parcialmente compatível; ≥ 0%: Pouco compatível.

## 4. Telas do wizard

| Passo | Tela | Perguntas |
|---|---|---|
| 1. Perfil pessoal | Seu ponto de partida | `experiencia`, `horas_semana`, `ferramenta` |
| 2. Afinidades técnicas | Raciocínio e dados | `matematica`, `logica`, `analise_dados`, `pipelines` |
| 2. Afinidades técnicas | Construção de produtos | `apis_bd`, `design`, `mobile`, `gestao` |
| 2. Afinidades técnicas | Infraestrutura, qualidade e segurança | `infra`, `nuvem`, `automacao`, `seguranca`, `testes` |
| 3. Objetivos de carreira | Para onde você quer ir | `objetivo`, `entrega`, `ambiente` |

## 5. Matriz de pesos: afinidades (escala de 1 a 5)

Peso de 0 a 10 de cada afinidade em cada trilha. Célula vazia = sem influência.

| Pergunta | Back-end | Front-end | Ciência de Dados | Eng. de Dados | Segurança | DevOps | Cloud | Mobile | QA | Produto |
|---|---|---|---|---|---|---|---|---|---|---|
| Matemática e estatística (`matematica`) | 2 |  | 9 | 3 | 3 |  |  |  | 1 | 1 |
| Lógica de programação e resolução de problemas (`logica`) | 9 | 5 | 5 | 6 | 5 | 4 | 3 | 6 | 5 | 2 |
| Descobrir padrões e fazer previsões com dados (`analise_dados`) | 1 |  | 10 | 5 |  |  |  |  |  | 3 |
| Organizar e mover grandes volumes de dados (`pipelines`) | 3 |  | 3 | 10 |  | 2 | 2 |  |  |  |
| Construir a parte invisível dos sistemas (`apis_bd`) | 10 | 1 | 1 | 5 |  | 2 | 1 | 3 | 2 |  |
| Design visual e experiência do usuário (`design`) |  | 10 |  |  |  |  |  | 6 |  | 4 |
| Criar aplicativos para celular (`mobile`) |  | 2 |  |  |  |  |  | 10 |  | 1 |
| Definir prioridades e alinhar pessoas (`gestao`) |  | 1 |  |  |  |  |  |  | 2 | 10 |
| Servidores, redes e sistemas operacionais (`infra`) | 2 |  |  | 2 | 6 | 8 | 8 |  | 1 |  |
| Nuvem e arquiteturas escaláveis (`nuvem`) | 2 |  |  | 3 | 2 | 6 | 10 |  |  |  |
| Automatizar processos e entregas (`automacao`) | 2 |  |  | 2 | 2 | 10 | 3 |  | 6 |  |
| Segurança da informação (`seguranca`) | 2 |  |  |  | 10 | 2 | 2 |  | 2 |  |
| Testar software e caçar bugs (`testes`) | 1 | 1 |  |  |  | 2 |  | 1 | 10 |  |

## 6. Matriz de pesos: perguntas de escolha

### `experiencia`: Qual é a sua experiência com TI hoje?

Importância: **0** (não pontua: só ajusta o plano de estudos).

| Opção | Valor |
|---|---|
| Ainda não programo nem trabalho com TI | 0 |
| Estou começando (faculdade, curso ou estudo por conta própria) | 1 |
| Já fiz projetos por conta própria | 2 |
| Já trabalho ou estagio na área | 3 |

### `horas_semana`: Quantas horas por semana você consegue dedicar aos estudos?

Importância: **0** (não pontua: só ajusta o plano de estudos).

| Opção | Valor |
|---|---|
| Até 5 horas | 5 |
| Cerca de 10 horas | 10 |
| Cerca de 20 horas | 20 |
| 30 horas ou mais | 30 |

### `ferramenta`: Com qual linguagem ou ferramenta você tem mais afinidade hoje?

Importância: **0.6**

| Opção | Back-end | Front-end | Ciência de Dados | Eng. de Dados | Segurança | DevOps | Cloud | Mobile | QA | Produto |
|---|---|---|---|---|---|---|---|---|---|---|
| Python | 6 |  | 8 | 7 | 5 | 4 | 1 |  | 5 |  |
| JavaScript / TypeScript | 5 | 9 |  |  |  |  |  | 4 | 5 |  |
| SQL / Bancos de dados | 7 |  | 5 | 8 |  |  |  |  | 2 |  |
| Linux / Redes | 2 |  |  | 1 | 8 | 8 | 5 |  |  |  |
| Kotlin / Swift / Dart (Flutter) / React Native |  | 2 |  |  |  |  |  | 10 |  |  |
| Docker / Kubernetes / AWS-Azure-GCP |  |  |  | 2 | 1 | 9 | 8 |  |  |  |
| Nenhuma / Iniciante |  | 2 |  |  |  |  |  |  | 3 | 3 |

### `objetivo`: Qual é o seu principal objetivo profissional?

Importância: **0.4**

| Opção | Back-end | Front-end | Ciência de Dados | Eng. de Dados | Segurança | DevOps | Cloud | Mobile | QA | Produto |
|---|---|---|---|---|---|---|---|---|---|---|
| Construir sistemas e funcionalidades | 6 | 6 |  | 4 |  |  |  | 6 | 1 |  |
| Pesquisar e inovar com dados e IA | 1 |  | 8 | 3 |  |  |  |  |  |  |
| Proteger, manter e garantir a estabilidade dos sistemas | 1 |  |  | 2 | 7 | 7 | 6 |  | 6 |  |
| Liderar produtos e decisões estratégicas |  |  |  |  |  |  | 2 |  | 1 | 9 |

### `entrega`: Que tipo de valor você mais gostaria de entregar?

Importância: **0.6**

| Opção | Back-end | Front-end | Ciência de Dados | Eng. de Dados | Segurança | DevOps | Cloud | Mobile | QA | Produto |
|---|---|---|---|---|---|---|---|---|---|---|
| O produto final que o usuário utiliza | 5 | 8 |  |  |  |  |  | 8 |  | 3 |
| A infraestrutura que sustenta o sistema |  |  |  | 3 | 2 | 6 | 8 |  |  |  |
| A segurança contra invasões |  |  |  |  | 10 |  |  |  |  |  |
| Previsões e decisões baseadas em modelos |  |  | 10 | 2 |  |  |  |  |  | 2 |
| Dados limpos, organizados e disponíveis para todos | 1 |  | 3 | 10 |  |  |  |  |  |  |
| Software confiável e sem falhas | 1 |  |  |  |  | 1 |  |  | 10 |  |
| Entregas rápidas, frequentes e automatizadas |  |  |  |  |  | 10 | 2 |  | 3 |  |
| O produto certo, no momento certo, para o negócio |  | 1 |  |  |  |  |  |  |  | 10 |

### `ambiente`: Em qual ambiente você prefere atuar?

Importância: **0.3**

| Opção | Back-end | Front-end | Ciência de Dados | Eng. de Dados | Segurança | DevOps | Cloud | Mobile | QA | Produto |
|---|---|---|---|---|---|---|---|---|---|---|
| Web | 6 | 8 |  |  |  |  |  |  | 3 | 2 |
| Dispositivos móveis |  |  |  |  |  |  |  | 9 | 2 | 1 |
| Dados e analytics | 1 |  | 8 | 8 |  |  |  |  |  |  |
| Infraestrutura e nuvem |  |  |  | 1 | 6 | 7 | 8 |  |  |  |
| Tanto faz |  |  |  |  |  |  |  |  |  |  |

## 7. Regras cruzadas (penalidades e bônus)

Efeitos em pontos percentuais (pp) somados à compatibilidade base. Valores negativos são penalidades para perfis conflitantes.

| Regra | Condição | Efeito | Motivo |
|---|---|---|---|
| X01 | `logica` ≤ 2 | Back-end -20, Mobile -12, Eng. de Dados -12, Ciência de Dados -10, Segurança -10, Front-end -8, DevOps -8, QA -6 | Pouca afinidade com lógica reduz a aderência às trilhas que programam o dia todo. |
| X02 | `matematica` ≤ 2 | Ciência de Dados -14 | Ciência de Dados exige base em matemática e estatística. |
| X03 | `matematica` ≤ 2 **e** `analise_dados` ≥ 4 | Eng. de Dados +6 | Gosta de dados, mas evita matemática: Engenharia de Dados costuma ser um caminho melhor. |
| X04 | `matematica` ≥ 4 **e** `analise_dados` ≥ 4 | Ciência de Dados +8 | Matemática forte combinada com gosto por análise de dados favorece Ciência de Dados. |
| X05 | `pipelines` ≥ 4 **e** `analise_dados` ≤ 2 | Eng. de Dados +6, Ciência de Dados -8 | Quer organizar dados, não modelá-los: favorece Engenharia de Dados sobre Ciência de Dados. |
| X06 | `analise_dados` ≤ 2 | Ciência de Dados -12 | Pouco interesse em análise de dados reduz a aderência a Ciência de Dados. |
| X07 | `pipelines` ≤ 2 | Eng. de Dados -12 | Pouco interesse em pipelines reduz a aderência a Engenharia de Dados. |
| X08 | `design` ≤ 2 | Front-end -18, Mobile -8 | Pouca afinidade com design reduz a aderência a Front-end e Mobile. |
| X09 | `mobile` ≤ 2 | Mobile -15 | Sem interesse em apps de celular, Mobile perde aderência. |
| X10 | `mobile` ≥ 4 **e** `design` ≥ 4 | Mobile +5 | Interesse em apps de celular combinado com design favorece Mobile. |
| X11 | `gestao` ≤ 2 | Produto -20 | Pouco interesse em definir prioridades e alinhar pessoas reduz a aderência a Gestão de Produtos. |
| X12 | `design` ≥ 4 **e** `gestao` ≥ 4 | Produto +4 | Design e visão de negócio juntos favorecem Gestão de Produtos. |
| X13 | `ferramenta` = nenhuma **e** `objetivo` = liderar | Produto +4 | Sem base técnica, mas com desejo de liderar: Gestão de Produtos é uma boa porta de entrada. |
| X14 | `seguranca` ≤ 2 | Segurança -18 | Pouco interesse em segurança reduz a aderência a Cibersegurança. |
| X15 | `seguranca` ≥ 4 **e** `infra` ≥ 4 | Segurança +5 | Segurança combinada com infraestrutura favorece Cibersegurança. |
| X16 | `testes` ≤ 2 | QA -18 | Pouco interesse em testes reduz a aderência a QA. |
| X17 | `apis_bd` ≤ 2 | Back-end -18, Eng. de Dados -4 | Pouco interesse em construir APIs e bancos de dados reduz a aderência a Back-end. |
| X18 | `infra` ≤ 2 **e** `nuvem` ≤ 2 | Cloud -15, DevOps -12 | Pouco interesse em servidores e em nuvem reduz a aderência a Cloud e DevOps. |
| X19 | `nuvem` ≤ 2 | Cloud -12 | Pouco interesse em nuvem reduz a aderência a Cloud Architecture. |
| X20 | `automacao` ≤ 2 | DevOps -12 | Pouco interesse em automação reduz a aderência a DevOps. |
| X21 | `automacao` ≥ 4 **e** `infra` ≥ 4 | DevOps +6 | Automação combinada com infraestrutura favorece DevOps. |
| X22 | `nuvem` ≥ 4 **e** `automacao` ≤ 2 | Cloud +4, DevOps -8 | Quer desenhar arquiteturas na nuvem, mas não automatizar: favorece Cloud sobre DevOps. |

## 8. Conteúdo das trilhas (gaps e roadmap)

| Trilha | Competências Júnior | Horas estimadas | Certificações | Projetos |
|---|---|---|---|---|
| Desenvolvimento Back-end | 11 | 337 | 4 | 3 |
| Desenvolvimento Front-end & UI/UX | 11 | 317 | 4 | 3 |
| Ciência de Dados e Machine Learning | 11 | 367 | 4 | 3 |
| Engenharia de Dados | 12 | 372 | 5 | 3 |
| Cibersegurança (Security / Pentesting) | 11 | 340 | 5 | 3 |
| DevOps & SRE | 11 | 322 | 5 | 3 |
| Computação em Nuvem (Cloud Architecture) | 11 | 375 | 5 | 3 |
| Desenvolvimento Mobile | 11 | 362 | 2 | 3 |
| Engenharia de Qualidade e Testes (QA) | 12 | 307 | 4 | 3 |
| Gestão de Produtos (Product Management) | 12 | 270 | 4 | 3 |

Cada competência tem fase (1 Fundamentos, 2 Ferramentas e prática, 3 Consolidação), prioridade (3 essencial, 2 importante, 1 desejável), horas estimadas e uma dica de estudo. A prontidão para Júnior é a soma dos pesos das competências marcadas dividida pela soma total.
