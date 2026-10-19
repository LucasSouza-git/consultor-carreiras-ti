# Fase 1 — Engenharia de Conhecimento e Matriz de Decisão

Consultor Inteligente de Carreiras em TI · Sistema Especialista baseado em Regras (Experta)

## 1. Modelo de raciocínio

O sistema usa **encadeamento para frente** (forward chaining):

1. As respostas da entrevista viram o fato `Perfil`.
2. Cada regra `SE <condição sobre o Perfil> ENTÃO <soma/subtrai pontos de trilhas>` é disparada quando seu padrão casa.
3. Ao final, uma regra de baixa prioridade (`salience=-100`) apura o placar, desempata e declara o fato `Recomendacao`.

A pontuação por regra permite combinar várias evidências e **explicar** a decisão listando as regras que mais contribuíram.

## 2. Dimensões da entrevista (variáveis de entrada)

| Campo | Pergunta | Valores possíveis |
|---|---|---|
| `matematica` | Afinidade com matemática e estatística | `baixa`, `media`, `alta` |
| `atuacao` | Preferência de atuação diária | `algoritmos`, `layouts`, `apps_moveis`, `analise_dados`, `pipelines`, `seguranca`, `automacao`, `servidores`, `arquitetura`, `testes`, `produto` |
| `ferramenta` | Linguagem/ferramenta de maior afinidade | `python`, `javascript`, `sql`, `linux_redes`, `mobile`, `cloud_containers`, `nenhuma` |
| `entrega` | Tipo de valor preferido | `produto_usuario`, `infraestrutura`, `protecao`, `insights`, `dados_prontos`, `qualidade`, `fluxo_entrega`, `estrategia` |
| `plataforma` | Ambiente preferido | `web`, `mobile`, `dados`, `infra`, `indiferente` |
| `negocio` | Afinidade com conversar com clientes/negócio/times | `baixa`, `media`, `alta` |
| `objetivo` | Objetivo profissional | `construir`, `inovar`, `sustentar`, `liderar` |

## 3. Matriz resumida: sinais de cada trilha

`●` = sinal decisivo (regra núcleo) · `○` = sinal de reforço · `✕` = sinal que reduz a aderência

| Trilha | `atuacao` | `ferramenta` | `entrega` | `plataforma` | `matematica` / `negocio` / `objetivo` |
|---|---|---|---|---|---|
| Back-end | ● algoritmos | ● python / sql / javascript | — | ○ web ou indiferente | ○ matemática não-alta; ○ objetivo construir |
| Front-end & UI/UX | ● layouts | ● javascript | ● produto_usuario | ○ web | ✕ plataforma mobile |
| Ciência de Dados e ML | ● analise_dados | ○ python | ● insights | ○ dados | ● matemática alta; ○ objetivo inovar; ✕ matemática baixa |
| Engenharia de Dados | ● pipelines | ● python / sql | ● dados_prontos | ○ dados | ○ matemática não-alta |
| Cibersegurança | ● seguranca | ● linux_redes / python | ● protecao | — | ○ matemática média/alta (criptografia) |
| DevOps & SRE | ● automacao ○ servidores | ● linux_redes / cloud_containers | ● fluxo_entrega | — | — |
| Cloud Architecture | ● arquitetura ○ servidores | ● cloud_containers | ○ infraestrutura | ○ infra | — |
| Mobile | ● apps_moveis ○ layouts | ○ mobile | — | ● mobile | — |
| QA | ● testes | ○ python / javascript | ● qualidade | — | — |
| Gestão de Produtos | ● produto | — | ● estrategia | — | ● negocio alta; ○ objetivo liderar; ✕ negocio baixa |

## 4. Tabela de regras (R01–R33)

| Regra | SE (condições cruzadas) | ENTÃO (pontos) |
|---|---|---|
| R01 | atuacao = algoritmos **E** ferramenta ∈ {python, sql, javascript} | Back-end +4 |
| R02 | atuacao = algoritmos **E** plataforma ∈ {web, indiferente} **E** matematica ≠ alta | Back-end +3 |
| R03 | atuacao = algoritmos **E** objetivo = construir | Back-end +2 |
| R04 | atuacao = algoritmos **E** ferramenta = sql | Back-end +2 |
| R05 | atuacao = layouts **E** ferramenta = javascript | Front-end +6 |
| R06 | atuacao = layouts **E** entrega = produto_usuario | Front-end +4 |
| R07 | atuacao = layouts **E** plataforma = web | Front-end +2 |
| R08 | atuacao = apps_moveis | Mobile +6 |
| R09 | plataforma = mobile **E** ferramenta = mobile | Mobile +4 |
| R10 | atuacao = layouts **E** plataforma = mobile | Mobile +4, Front-end −3 |
| R11 | matematica = alta **E** atuacao = analise_dados | Ciência de Dados +6 |
| R12 | entrega = insights **E** ferramenta = python | Ciência de Dados +4 |
| R13 | objetivo = inovar **E** matematica ∈ {media, alta} **E** plataforma = dados | Ciência de Dados +3 |
| R14 | matematica = baixa **E** atuacao = analise_dados | Ciência de Dados −4, Eng. de Dados +2 |
| R15 | atuacao = pipelines **E** ferramenta ∈ {python, sql} | Eng. de Dados +6 |
| R16 | entrega = dados_prontos **E** plataforma = dados | Eng. de Dados +4 |
| R17 | atuacao = pipelines **E** matematica ≠ alta | Eng. de Dados +2, Ciência de Dados −2 |
| R18 | atuacao = analise_dados **E** entrega = dados_prontos | Eng. de Dados +3, Ciência de Dados −2 |
| R19 | atuacao = seguranca **E** ferramenta ∈ {linux_redes, python} | Cibersegurança +6 |
| R20 | entrega = protecao | Cibersegurança +5 |
| R21 | atuacao = seguranca **E** matematica ∈ {media, alta} | Cibersegurança +2 |
| R22 | atuacao = automacao **E** ferramenta ∈ {linux_redes, cloud_containers} | DevOps +6 |
| R23 | entrega = fluxo_entrega | DevOps +5 |
| R24 | atuacao = servidores **E** ferramenta ∈ {linux_redes, cloud_containers} | DevOps +3, Cloud +1 |
| R25 | atuacao = arquitetura **E** ferramenta = cloud_containers | Cloud +6 |
| R26 | plataforma = infra **E** entrega = infraestrutura **E** atuacao ∈ {arquitetura, servidores} | Cloud +4 |
| R27 | atuacao = testes | QA +6 |
| R28 | entrega = qualidade | QA +5 |
| R29 | atuacao = testes **E** ferramenta ∈ {python, javascript} | QA +3 |
| R30 | atuacao = produto | Gestão de Produtos +6 |
| R31 | entrega = estrategia **E** negocio = alta | Gestão de Produtos +5 |
| R32 | objetivo = liderar **E** negocio ∈ {media, alta} | Gestão de Produtos +3 |
| R33 | atuacao = produto **E** negocio = baixa | Gestão de Produtos −4 |

## 5. Regras de desambiguação (pontos críticos)

| Par ambíguo | Como o sistema diferencia | Regras |
|---|---|---|
| **Ciência de Dados × Eng. de Dados** | Ciência exige matemática alta e foco em *insights*/modelos. Engenharia prioriza pipelines e dados prontos. Quem analisa dados mas quer entregar dados organizados, ou tem matemática baixa, é empurrado para Eng. de Dados. | R11, R12, R14, R15, R17, R18 |
| **Front-end × Mobile** | Interfaces visuais no ambiente móvel dão pontos a Mobile e tiram de Front-end. | R05, R07, R08, R10 |
| **DevOps × Cloud** | DevOps = automação, CI/CD e operação (`automacao`, `fluxo_entrega`). Cloud = planejamento/arquitetura escalável (`arquitetura`, `infraestrutura`). `servidores` favorece DevOps (mais operacional). | R22–R26 |
| **Back-end × Ciência de Dados** | Lógica de programação sem matemática avançada favorece Back-end. | R01, R02 |
| **Gestão de Produtos × perfis técnicos** | Exige afinidade com negócio. Interesse em produto com `negocio = baixa` perde pontos. | R30–R33 |

## 6. Critérios de decisão

1. **Maior pontuação** no placar.
2. Empate: trilha com **mais regras positivas** disparadas.
3. Persistindo o empate: ordem fixa do catálogo (`motor_inferencia.py` (dicionário `TRILHAS`)).

**Confiança:** `alta` (margem ≥ 5 sobre a 2ª colocada), `media` (margem 2–4) e `baixa` (margem < 2 ou pontuação do vencedor < 6, comum em perfis iniciantes sem preferências marcantes). Em confiança baixa, a interface deve exibir também a segunda opção.

## 7. Verificação preliminar (14 perfis)

| Perfil de teste | Esperada | Obtida | Pontos | Confiança |
|---|---|---|---|---|
| Lógica + Python + web | Back-end | Back-end | 9 | alta |
| Layouts + JavaScript + produto ao usuário | Front-end | Front-end | 12 | alta |
| Matemática alta + análise + Python + insights | Ciência de Dados | Ciência de Dados | 13 | alta |
| Pipelines + SQL + dados prontos | Eng. de Dados | Eng. de Dados | 12 | alta |
| Segurança + Linux/Redes + proteção | Cibersegurança | Cibersegurança | 13 | alta |
| Automação + contêineres + entrega contínua | DevOps | DevOps | 11 | alta |
| Arquitetura + nuvem + infraestrutura | Cloud | Cloud | 10 | alta |
| Apps móveis + Flutter/Kotlin | Mobile | Mobile | 10 | alta |
| Testes + Python + qualidade | QA | QA | 14 | alta |
| Produto + negócio alto + estratégia | Gestão de Produtos | Gestão de Produtos | 14 | alta |
| *Ambíguo:* analisa dados, mas quer dados prontos (mat. média) | Eng. de Dados | Eng. de Dados | 7 | alta |
| *Ambíguo:* gosta de layouts, mas para celular | Mobile | Mobile | 8 | alta |
| *Ambíguo:* servidores + Linux + entrega rápida | DevOps | DevOps | 8 | alta |
| *Ambíguo:* iniciante sem preferências marcantes | (qualquer) | Back-end | 5 | **baixa** |

As personas formais da Fase 4 ainda devem ser definidas e automatizadas em testes.
