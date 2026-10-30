"""Interface web (Streamlit) do Consultor Avançado de Carreiras em TI (Etapa 2).

Execução:  streamlit run etapa_2/app.py   (ou, dentro de etapa_2/:  streamlit run app.py)

Fluxo (wizard):
  Passo 1  Perfil pessoal          -> 1 tela
  Passo 2  Afinidades técnicas     -> 3 telas (escala de 1 a 5)
  Passo 3  Objetivos de carreira   -> 1 tela
  Resultado  Top 3, radar e justificativa
  Conhecimento atual  checklist da trilha escolhida
  Plano de ação  gaps, roadmap, certificações e projetos de portfólio

As telas, perguntas e textos vêm de base_conhecimento/regras_carreiras.json.
"""
from __future__ import annotations

import math
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from conhecimento import BaseConhecimentoInvalida, carregar_base
from gaps_roadmap import analisar_gaps, plano_para_markdown
from motor_pontuacao import avaliar

st.set_page_config(page_title="Consultor de Carreiras em TI", page_icon="🧭", layout="centered")
st.markdown(
    unsafe_allow_html=True,
)

try:
    REGRAS, TRILHAS = carregar_base()
except (BaseConhecimentoInvalida, OSError, ValueError) as erro:
    st.error("Não consegui carregar a base de conhecimento. Corrija o arquivo JSON e recarregue a página.")
    st.code(str(erro))
    st.stop()

def _versao() -> tuple:
    partes = []
    for p in st.__version__.split(".")[:2]:
        partes.append(int("".join(ch for ch in p if ch.isdigit()) or 0))
    return tuple(partes)


# `use_container_width` foi substituído por `width="stretch"` nas versões recentes do Streamlit.
LARGURA_TOTAL = {"width": "stretch"} if _versao() >= (1, 50) else {"use_container_width": True}

NOMES = {t: d["nome"] for t, d in TRILHAS["trilhas"].items()}
CURTOS = {t: d["curto"] for t, d in TRILHAS["trilhas"].items()}
PERGUNTAS = REGRAS["perguntas"]

# Achata os passos do JSON em uma lista de telas.
TELAS: list[dict] = []
for indice_passo, passo in enumerate(REGRAS["passos"], start=1):
    for indice_tela, tela in enumerate(passo["telas"], start=1):
        TELAS.append(
            {"passo": indice_passo, "total_passos": len(REGRAS["passos"]), "passo_titulo": passo["titulo"],
             "passo_descricao": passo.get("descricao", ""), "titulo": tela["titulo"], "perguntas": tela["perguntas"],
             "parte": indice_tela, "partes": len(passo["telas"])}
        )
N_TELAS = len(TELAS)
P_RESULTADO, P_CONHECIMENTO, P_PLANO = N_TELAS + 1, N_TELAS + 2, N_TELAS + 3
N_MARCOS = P_PLANO  # um marco no caminho por tela do wizard + resultado + conhecimento + plano

# ----------------------------------------------------------------------
# Estado e navegação
# ----------------------------------------------------------------------
estado = st.session_state
estado.setdefault("passo", 0)
estado.setdefault("respostas", {})
estado.setdefault("inicial", {})
estado.setdefault("editando", False)
estado.setdefault("trilha", None)
estado.setdefault("conhecidas", {})        # {trilha: [ids de competências]}
estado.setdefault("inicial_conhecidas", {})


def salvar_checklist() -> None:
    """Lê direto dos checkboxes, para não perder marcações em cliques rápidos."""
    trilha = estado.trilha
    if trilha:
        competencias = TRILHAS["trilhas"][trilha]["competencias_junior"]
        estado.conhecidas[trilha] = [c["id"] for c in competencias if estado.get(f"ck_{trilha}_{c['id']}")]


def ir_para(passo: int, editando: bool = False) -> None:
    if estado.passo == P_CONHECIMENTO:
        salvar_checklist()
    estado.passo = passo
    estado.editando = editando
    estado.inicial = dict(estado.respostas)
    estado.inicial_conhecidas = {t: list(v) for t, v in estado.conhecidas.items()}


def avancar() -> None:
    ir_para(P_RESULTADO if estado.editando else estado.passo + 1)


def voltar() -> None:
    ir_para(estado.passo - 1)


def escolher_trilha(trilha: str) -> None:
    estado.trilha = trilha
    ir_para(P_CONHECIMENTO)


def recomecar() -> None:
    for chave in [c for c in estado if c.startswith(("lk_", "ch_", "ck_"))]:
        del estado[chave]
    estado.respostas, estado.conhecidas, estado.trilha = {}, {}, None
    ir_para(0)


# ----------------------------------------------------------------------
# Utilidades de formatação e componentes visuais
# ----------------------------------------------------------------------
def pct(x: float) -> str:
    return f"{x:.0f}%"


def pp(x: float) -> str:
    return f"{x:+.0f}".replace("-", "−") + " pp"


def marca() -> None:
    st.html('<div class="marca"><span class="blaze" aria-hidden="true"></span>Consultor de Carreiras em TI</div>')


def caminho(atual: int) -> None:
    """Caminho de progresso com um marco por tela. 0 = não iniciado."""
    largura, margem = 440, 20
    passo_x = (largura - 2 * margem) / (N_MARCOS - 1)
    pontos = [(margem + i * passo_x, 34 if i % 2 == 0 else 22) for i in range(N_MARCOS)]
    segmentos, marcos = [], []
    for i in range(N_MARCOS - 1):
        (x1, y1), (x2, y2) = pontos[i], pontos[i + 1]
        meio = (x1 + x2) / 2
        classe = "seg-feito" if i + 2 <= atual else "seg-falta"
        segmentos.append(f'<path class="{classe}" d="M{x1:.1f},{y1} C{meio:.1f},{y1} {meio:.1f},{y2} {x2:.1f},{y2}"/>')
    for i, (x, y) in enumerate(pontos, start=1):
        situacao = "feito" if i < atual else "atual" if i == atual else "falta"
        marcos.append(f'<circle class="pt-{situacao}" cx="{x:.1f}" cy="{y}" r="12"/><text class="tx-{situacao}" x="{x:.1f}" y="{y}">{"✓" if situacao == "feito" else i}</text>')
    descricao = "Caminho ainda não iniciado" if atual == 0 else f"Etapa {atual} de {N_MARCOS}"
    svg = f'<div class="trilha"><svg viewBox="0 0 {largura} 56" role="img" aria-label="{descricao}">{"".join(segmentos)}{"".join(marcos)}</svg></div>'
    st.markdown(svg, unsafe_allow_html=True)  # st.html remove SVG; markdown mantém


def radar(resultado) -> str:
    ordem = TRILHAS.get("ordem_radar") or list(NOMES)
    cx, cy, raio = 320, 225, 130
    n = len(ordem)
    angulo = lambda i: -math.pi / 2 + i * 2 * math.pi / n
    ponto = lambda i, r: (cx + r * math.cos(angulo(i)), cy + r * math.sin(angulo(i)))
    partes = []
    for nivel in (25, 50, 75, 100):
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (ponto(i, raio * nivel / 100) for i in range(n)))
        partes.append(f'<polygon class="anel" points="{pts}"/>')
        partes.append(f'<text class="escala-anel" x="{cx + 4}" y="{cy - raio * nivel / 100 + 12:.1f}">{nivel}</text>')
    for i in range(n):
        x, y = ponto(i, raio)
        partes.append(f'<line class="eixo" x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}"/>')
    valores = {c.trilha: c.percentual for c in resultado.ranking}
    area = " ".join(f"{x:.1f},{y:.1f}" for x, y in (ponto(i, raio * valores[t] / 100) for i, t in enumerate(ordem)))
    partes.append(f'<polygon class="area" points="{area}"/>')
    top3 = [c.trilha for c in resultado.top3]
    for i, t in enumerate(ordem):
        x, y = ponto(i, raio * valores[t] / 100)
        partes.append(f'<circle class="{"ponto-top" if t == top3[0] else "ponto"}" cx="{x:.1f}" cy="{y:.1f}" r="{6 if t == top3[0] else 4}"/>')
        lx, ly = ponto(i, raio + 16)
        cos = math.cos(angulo(i))
        ancora = "middle" if abs(cos) < 0.25 else ("start" if cos > 0 else "end")
        forte = ' class="forte"' if t in top3 else ""
        if ly < cy - raio * 0.9:      # rótulos do topo sobem, para não cobrir o gráfico
            ly -= 22
        elif ly > cy + raio * 0.9:    # rótulos da base descem
            ly += 8
        else:
            ly -= 6
        partes.append(
            f'<text{forte} text-anchor="{ancora}"><tspan x="{lx:.1f}" y="{ly:.1f}">{escape(CURTOS[t])}</tspan>'
            f'<tspan x="{lx:.1f}" dy="1.15em">{valores[t]:.0f}%</tspan></text>'
        )
    resumo = ", ".join(f"{CURTOS[c.trilha]} {c.percentual:.0f}%" for c in resultado.top3)
    return f'<div class="radar"><svg viewBox="0 0 640 450" role="img" aria-label="Radar de compatibilidade. Três primeiras: {escape(resumo)}">{"".join(partes)}</svg></div>'


def frase_resposta(f) -> str:
    """Frase natural para uma resposta: afinidades viram 'Tema: você respondeu 5 (muita).', perguntas viram 'Pergunta? Você respondeu: opção.'"""
    if f.tipo == "escolha":
        return f"{f.texto} Você respondeu: {f.resposta}."
    return f"{f.texto}: você respondeu {f.resposta}."


def lista_fatores(comp, justificativa: dict) -> str:
    itens = []
    for f in justificativa["a_favor"]:
        itens.append(
            f'<li class="regra"><span class="pts pos">{pp(f.pontos / comp.maximo * 100)}</span>'
            f'<span class="txt">{escape(frase_resposta(f))}<small>Ponto a favor</small></span></li>'
        )
    for f in justificativa["atencao"]:
        itens.append(
            f'<li class="regra"><span class="pts neg">{pp(-(f.maximo - f.pontos) / comp.maximo * 100)}</span>'
            f'<span class="txt">{escape(frase_resposta(f))} Isso pesa bastante nesta trilha.<small>Ponto de atenção</small></span></li>'
        )
    for a in justificativa["ajustes"]:
        itens.append(
            f'<li class="regra"><span class="pts {"pos" if a.pontos > 0 else "neg"}">{pp(a.pontos)}</span>'
            f'<span class="txt">{escape(a.descricao)}<small>Regra {a.regra}</small></span></li>'
        )
    if not itens:
        return '<p class="legenda">Nenhum fator se destacou para esta trilha.</p>'
    return f'<ul class="regras">{"".join(itens)}</ul>'


# ----------------------------------------------------------------------
# Telas
# ----------------------------------------------------------------------
def tela_introducao() -> None:
    caminho(0)
    st.html(
        '<h1 class="hero">Mapeie sua carreira em TI</h1>'
        f'<p class="lead">Responda a {len(PERGUNTAS)} perguntas em 3 passos. Você recebe as 3 trilhas mais compatíveis com o seu perfil, '
        "o que falta para chegar ao nível Júnior e um plano de estudos com certificações e projetos para o GitHub.</p>"
        '<p class="nota">Leva de 5 a 8 minutos. Suas respostas ficam só nesta sessão, sem cadastro.</p>'
    )
    st.button("Começar", type="primary", on_click=ir_para, args=(1,))
    st.write("")
    with st.expander("Como o resultado é calculado"):
        st.write(
            "Cada resposta é multiplicada pelo peso que ela tem em cada trilha. Os pontos são somados e comparados com o máximo possível, "
            "o que gera a porcentagem de compatibilidade. Regras extras somam ou subtraem pontos quando as respostas se contradizem. "
            "Tudo isso vem de um arquivo externo, e a tela de resultado mostra o que pesou."
        )


def pergunta_escolha(qid: str, q: dict) -> str | None:
    opcoes = list(q["opcoes"])
    inicial = estado.inicial.get(qid)
    st.html(f'<p class="q-texto">{escape(q["texto"])}</p><p class="q-ajuda">{escape(q["ajuda"])}</p>')
    valor = st.radio(q["texto"], opcoes, index=opcoes.index(inicial) if inicial in opcoes else None,
                     format_func=lambda o, q=q: q["opcoes"][o]["rotulo"], key=f"ch_{qid}", label_visibility="collapsed")
    return valor


def pergunta_likert(qid: str, q: dict) -> int | None:
    escala = REGRAS["parametros"]["escala_likert"]
    inicial = estado.inicial.get(qid)
    st.html(f'<p class="q-texto">{escape(q["texto"])}</p><p class="q-ajuda">{escape(q["ajuda"])}</p>')
    valor = st.radio(q["texto"], [1, 2, 3, 4, 5], index=inicial - 1 if inicial else None, horizontal=True,
                     key=f"lk_{qid}", label_visibility="collapsed")
    st.html(f'<div class="escala"><span>1: {escape(escala["1"])}</span><span>5: {escape(escala["5"])}</span></div>')
    return valor


def tela_pergunta(numero: int) -> None:
    tela = TELAS[numero - 1]
    caminho(numero)
    rotulo = f"Passo {tela['passo']} de {tela['total_passos']}: {tela['passo_titulo']}"
    if tela["partes"] > 1:
        rotulo += f" (parte {tela['parte']} de {tela['partes']})"
    st.html(f'<p class="passo-rotulo">{escape(rotulo)}</p><h2 class="pergunta">{escape(tela["titulo"])}</h2>'
            + (f'<p class="ajuda">{escape(tela["passo_descricao"])}</p>' if tela["parte"] == 1 else ""))

    respondidas = 0
    for qid in tela["perguntas"]:
        q = PERGUNTAS[qid]
        valor = pergunta_likert(qid, q) if q["tipo"] == "likert" else pergunta_escolha(qid, q)
        if valor is not None:
            estado.respostas[qid] = valor
            respondidas += 1
    completa = respondidas == len(tela["perguntas"])
    total_tela = len(tela["perguntas"])
    status = "Tudo respondido nesta tela." if completa else f"Respondidas: {respondidas} de {total_tela}. Responda todas para continuar."
    st.html(f'<p class="ok-tela">{status}</p>')
    st.write("")

    if estado.editando:
        st.button("Atualizar resultado", type="primary", disabled=not completa, on_click=avancar)
        return
    col_voltar, col_avancar = st.columns(2)
    col_voltar.button("Voltar", on_click=voltar, **LARGURA_TOTAL)
    texto = "Ver minhas trilhas" if numero == N_TELAS else "Continuar"
    col_avancar.button(texto, type="primary", disabled=not completa, on_click=avancar, **LARGURA_TOTAL)


def tela_resultado() -> None:
    faltando = [i for i, t in enumerate(TELAS, 1) if any(q not in estado.respostas for q in t["perguntas"])]
    if faltando:
        ir_para(faltando[0])
        st.rerun()
    r = avaliar(estado.respostas, REGRAS, TRILHAS)
    melhor = r.melhor
    caminho(P_RESULTADO)

    titulos = {"clara": "Resultado claro", "hibrida": "Perfil híbrido", "fraca": "Compatibilidade baixa", "indiferenciada": "Notas iguais"}
    st.html(f'<div class="leitura {r.leitura}"><strong>{titulos[r.leitura]}</strong><p>{escape(r.mensagem)}</p></div>')
    if r.avisos:
        st.html('<ul class="avisos">' + "".join(f"<li>{escape(a)}</li>" for a in r.avisos) + "</ul>")

    # 1º lugar
    st.html(
        '<section class="placa"><div class="placa-topo"><div>'
        '<p class="placa-sup">Trilha mais compatível</p>'
        f'<h1 class="placa-nome">{escape(NOMES[melhor.trilha])}</h1></div>'
        f'<p class="placa-pct">{pct(melhor.percentual)}<small>{escape(r.faixa(melhor.percentual))}</small></p></div>'
        f'<p class="placa-desc">{escape(TRILHAS["trilhas"][melhor.trilha]["descricao"])}</p>'
        f'<div class="barra" role="img" aria-label="{pct(melhor.percentual)} de compatibilidade"><i style="--w:{melhor.percentual:.0f}%"></i></div></section>'
    )
    st.write("")
    st.button(f"Montar meu plano para {CURTOS[melhor.trilha]}", type="primary", key=f"escolher_{melhor.trilha}",
              on_click=escolher_trilha, args=(melhor.trilha,))

    # 2º e 3º lugares
    colunas = st.columns(2)
    for coluna, comp, pos in zip(colunas, r.top3[1:], (2, 3)):
        with coluna:
            st.html(
                f'<div class="cartao"><p class="pos">{pos}º lugar</p><p class="nome">{escape(CURTOS[comp.trilha])}</p>'
                f'<p class="pct">{pct(comp.percentual)}</p><p class="faixa">{escape(r.faixa(comp.percentual))}</p>'
                f'<div class="barra" role="img" aria-label="{pct(comp.percentual)} de compatibilidade"><i style="--w:{comp.percentual:.0f}%"></i></div></div>'
            )
            st.button(f"Plano para {CURTOS[comp.trilha]}", key=f"escolher_{comp.trilha}", on_click=escolher_trilha,
                      args=(comp.trilha,), **LARGURA_TOTAL)

    st.html('<h2 class="secao">Mapa de compatibilidade</h2><p class="legenda">As 10 trilhas no mesmo gráfico. Quanto mais longe do centro, maior a compatibilidade.</p>')
    st.markdown(radar(r), unsafe_allow_html=True)
    with st.expander("Ver ranking completo em tabela"):
        st.dataframe(r.tabela(), hide_index=True, **LARGURA_TOTAL)

    st.html(f'<h2 class="secao">Por que {escape(CURTOS[melhor.trilha])} ficou em 1º?</h2>'
            '<p class="legenda">O número mostra quantos pontos percentuais (pp) cada fator somou ou tirou da compatibilidade.</p>'
            + lista_fatores(melhor, r.justificar(melhor.trilha)))
    for comp in r.top3[1:]:
        with st.expander(f"Por que {CURTOS[comp.trilha]} ficou em {r.posicao(comp.trilha)}º?"):
            st.html(lista_fatores(comp, r.justificar(comp.trilha)))

    st.html('<h2 class="secao">Suas respostas</h2><p class="legenda">Altere qualquer tela e o ranking é recalculado.</p>')
    with st.expander("Ver e alterar respostas"):
        for i, t in enumerate(TELAS, 1):
            col_texto, col_botao = st.columns([3, 1], vertical_alignment="center")
            col_texto.html(f'<p class="resp-rotulo">Passo {t["passo"]}: {escape(t["passo_titulo"])}</p><p class="resp-valor">{escape(t["titulo"])}</p>')
            col_botao.button("Alterar", key=f"alterar_{i}", on_click=ir_para, args=(i, True), **LARGURA_TOTAL)
    st.write("")
    st.button("Recomeçar", on_click=recomecar)


def tela_conhecimento() -> None:
    trilha = estado.trilha
    if trilha is None:
        ir_para(P_RESULTADO)
        st.rerun()
    dados = TRILHAS["trilhas"][trilha]
    caminho(P_CONHECIMENTO)
    st.html(
        '<p class="passo-rotulo">Conhecimento atual</p>'
        f'<h2 class="pergunta">O que você já sabe de {escape(CURTOS[trilha])}?</h2>'
        '<p class="ajuda">Marque o que você consegue usar sem seguir um tutorial passo a passo. O sistema compara com o nível Júnior e monta o seu plano. '
        "Se não marcar nada, tudo bem: o plano começa do início.</p>"
    )
    inicial = set(estado.inicial_conhecidas.get(trilha, []))
    marcadas = []
    fases = TRILHAS["fases"]
    for fase, titulo in sorted(fases.items(), key=lambda kv: int(kv[0])):
        itens = [c for c in dados["competencias_junior"] if str(c["fase"]) == fase]
        if not itens:
            continue
        st.html(f'<h3 class="grupo-fase">Fase {fase}: {escape(titulo)}</h3>')
        for c in itens:
            if st.checkbox(c["nome"], value=c["id"] in inicial, key=f"ck_{trilha}_{c['id']}"):
                marcadas.append(c["id"])
            st.html(f'<p class="dica-comp">{escape(c["dica"])}</p>')
    estado.conhecidas[trilha] = marcadas
    total = len(dados["competencias_junior"])
    st.html(f'<p class="ok-tela">Marcadas: {len(marcadas)} de {total}.</p>')
    st.write("")
    col_voltar, col_avancar = st.columns(2)
    col_voltar.button("Voltar ao resultado", on_click=ir_para, args=(P_RESULTADO,), **LARGURA_TOTAL)
    col_avancar.button("Ver meu plano", type="primary", on_click=ir_para, args=(P_PLANO,), **LARGURA_TOTAL)


def tela_plano() -> None:
    trilha = estado.trilha
    if trilha is None:
        ir_para(P_RESULTADO)
        st.rerun()
    opcao_horas = PERGUNTAS["horas_semana"]["opcoes"][estado.respostas["horas_semana"]]["valor"]
    plano = analisar_gaps(trilha, estado.conhecidas.get(trilha, []), opcao_horas, estado.respostas["experiencia"], TRILHAS)
    rot = plano.rotulos_prioridade
    caminho(P_PLANO)

    st.html(
        '<section class="placa"><div class="placa-topo"><div><p class="placa-sup">Plano de ação</p>'
        f'<h1 class="placa-nome">{escape(plano.nome)}</h1></div>'
        f'<p class="placa-pct">{pct(plano.prontidao)}<small>prontidão para Júnior</small></p></div>'
        f'<p class="placa-desc">{escape(plano.leitura_prontidao)}</p>'
        f'<div class="barra" role="img" aria-label="{pct(plano.prontidao)} de prontidão"><i style="--w:{plano.prontidao:.0f}%"></i></div></section>'
    )
    st.html(
        '<div class="metricas" style="margin-top:1rem">'
        f'<div class="metrica"><p class="valor">{plano.semanas_total}</p><p class="rotulo">semanas estimadas</p></div>'
        f'<div class="metrica"><p class="valor">{plano.horas_total:.0f} h</p><p class="rotulo">de estudo no total</p></div>'
        f'<div class="metrica"><p class="valor">{len(plano.lacunas)}</p><p class="rotulo">competências a desenvolver</p></div></div>'
        f'<p class="legenda">Estimativa para {plano.horas_semana} horas por semana. {escape(plano.ponto_de_partida)}</p>'
    )

    if not plano.lacunas:
        st.success("Você já domina todas as competências de nível Júnior desta trilha. Foque nos projetos de portfólio e nas candidaturas.")
    else:
        st.html('<h2 class="secao">Estude primeiro</h2><p class="legenda">As competências mais importantes e mais básicas que ainda faltam.</p>'
                '<ol class="lista-num">' + "".join(f"<li><strong>{escape(c.nome)}</strong> ({escape(c.prioridade(rot).lower())})</li>" for c in plano.estudar_primeiro) + "</ol>")

        tabela = pd.DataFrame(
            [{"Competência": c.nome, "Prioridade": c.prioridade(rot), "Fase": c.fase, "Horas": c.horas} for c in plano.lacunas]
        )
        linhas = "".join(
            f'<tr><td>{escape(r["Competência"])}</td><td>{r["Prioridade"]}</td><td class="num">{r["Fase"]}</td><td class="num">{r["Horas"]:.0f}</td></tr>'
            for _, r in tabela.iterrows()
        )
        st.html('<h2 class="secao">Lacunas até o nível Júnior</h2>'
                '<div class="tabela-rolavel"><table class="tabela"><thead><tr><th>Competência</th><th>Prioridade</th><th class="num">Fase</th><th class="num">Horas</th></tr></thead>'
                f"<tbody>{linhas}</tbody></table></div>")

        blocos = ['<h2 class="secao">Roadmap</h2>']
        for e in plano.etapas:
            itens = "".join(f'<li><strong>{escape(c.nome)}</strong> ({escape(c.prioridade(rot).lower())}, cerca de {c.horas:.0f} h)<small>{escape(c.dica)}</small></li>' for c in e.competencias)
            semanas = f"semana {e.semana_inicio}" if e.semana_inicio == e.semana_fim else f"semanas {e.semana_inicio} a {e.semana_fim}"
            blocos.append(f'<div class="fase"><h3>Fase {e.fase}: {escape(e.titulo)}</h3><p class="prazo">{semanas}, cerca de {e.horas:.0f} h</p><ul>{itens}</ul></div>')
        st.html("".join(blocos))

    if plano.conhecidas:
        with st.expander(f"Competências que você já domina ({len(plano.conhecidas)})"):
            st.html('<ul class="regras">' + "".join(f'<li class="regra"><span class="pts pos">✓</span><span class="txt">{escape(c.nome)}</span></li>' for c in plano.conhecidas) + "</ul>")

    partes = ['<h2 class="secao">Certificações</h2>']
    if plano.nota_certificacoes:
        partes.append(f'<p class="nota-box">{escape(plano.nota_certificacoes)}</p>')
    for c in plano.certificacoes:
        chip = '<span class="chip agora">Faz sentido agora</span>' if c.agora else f'<span class="chip">Para depois (prontidão a partir de {c.a_partir_de}%)</span>'
        partes.append(f'<div class="item-cartao"><h4>{escape(c.nome)}</h4><span class="chip">{escape(c.nivel)}</span>{chip}<p>{escape(c.emissor)}. {escape(c.nota)}</p></div>')
    partes.append(f'<p class="rodape-nota">{escape(plano.aviso_certificacoes)}</p>')
    st.html("".join(partes))

    partes = ['<h2 class="secao">Projetos para o seu portfólio no GitHub</h2>']
    for p in plano.projetos:
        marca_inicio = '<span class="chip agora">Comece por este</span>' if p.comecar_aqui else ""
        techs = "".join(f'<span class="chip tech">{escape(t)}</span>' for t in p.tecnologias)
        classe = "item-cartao destaque" if p.comecar_aqui else "item-cartao"
        partes.append(f'<div class="{classe}"><h4>{escape(p.titulo)}</h4><span class="chip">{escape(p.nivel)}</span>{marca_inicio}<p>{escape(p.descricao)}</p><p>{techs}</p></div>')
    st.html("".join(partes))
    with st.expander("Boas práticas para deixar o repositório profissional", expanded=True):
        st.html('<ul class="regras">' + "".join(f'<li class="regra"><span class="txt">{escape(b)}</span></li>' for b in plano.boas_praticas) + "</ul>")

    st.write("")
    st.download_button("Baixar plano em Markdown", data=plano_para_markdown(plano), file_name=f"plano_{trilha}.md", mime="text/markdown", type="primary")
    col1, col2 = st.columns(2)
    col1.button("Ajustar o que já sei", on_click=ir_para, args=(P_CONHECIMENTO,), **LARGURA_TOTAL)
    col2.button("Escolher outra trilha", on_click=ir_para, args=(P_RESULTADO,), **LARGURA_TOTAL)
    st.button("Recomeçar", on_click=recomecar, key="recomecar_fim")


# ----------------------------------------------------------------------
# Barra lateral (ajuda) e roteador
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Como funciona")
    st.write(
        f"O sistema multiplica cada resposta pelo peso dela em cada uma das {len(NOMES)} trilhas, soma os pontos e compara com o máximo possível. "
        f"{len(REGRAS['regras_cruzadas'])} regras extras somam ou tiram pontos quando as respostas se contradizem. "
        "Perguntas, pesos e trilhas ficam em arquivos JSON, separados do código."
    )
    if estado.passo > 0:
        st.button("Recomeçar", key="recomecar_lateral", on_click=recomecar)

marca()
passo = estado.passo
if passo == 0:
    tela_introducao()
elif passo <= N_TELAS:
    tela_pergunta(passo)
elif passo == P_RESULTADO:
    tela_resultado()
elif passo == P_CONHECIMENTO:
    tela_conhecimento()
else:
    tela_plano()
