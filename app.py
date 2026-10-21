"""Interface web (Streamlit) do Consultor Inteligente de Carreiras em TI.

Execução:  streamlit run app.py
"""
import pandas as pd
import streamlit as st

from motor_inferencia import TRILHAS, ConsultorCarreiras, diagnosticar
from perguntas import PERGUNTAS

st.set_page_config(page_title="Consultor de Carreiras em TI", page_icon="🧭", layout="centered")


@st.cache_data
def total_de_regras() -> int:
    # get_rules() inclui a regra final de decisão, que não pontua nenhuma trilha.
    return len(ConsultorCarreiras().get_rules()) - 1


def reiniciar() -> None:
    """Limpa respostas e resultado (usado como callback do botão)."""
    for chave in list(st.session_state.keys()):
        if chave.startswith("q_") or chave == "resultado":
            del st.session_state[chave]


# ----------------------------------------------------------------------
# Barra lateral
# ----------------------------------------------------------------------
with st.sidebar:
    st.header("Sobre o sistema")
    st.write(
        "Sistema especialista baseado em regras (encadeamento para frente) que "
        "recomenda a trilha de carreira em TI mais adequada ao seu perfil."
    )
    st.metric("Regras na base de conhecimento", total_de_regras())
    st.metric("Trilhas possíveis", len(TRILHAS))
    with st.expander("Ver as 10 trilhas"):
        for info in TRILHAS.values():
            st.markdown(f"**{info['nome']}**  \n{info['descricao']}")

# ----------------------------------------------------------------------
# Entrevista
# ----------------------------------------------------------------------
st.title("🧭 Consultor Inteligente de Carreiras em TI")
st.write("Responda às perguntas abaixo e descubra qual trilha combina mais com você.")

with st.form("entrevista"):
    respostas: dict[str, str | None] = {}
    for numero, p in enumerate(PERGUNTAS, start=1):
        opcoes = list(p["opcoes"])
        rotulo = f"{numero}. {p['titulo']}"
        if len(opcoes) <= 5:
            respostas[p["campo"]] = st.radio(
                rotulo, opcoes, index=None, format_func=p["opcoes"].get, key=f"q_{p['campo']}"
            )
        else:
            respostas[p["campo"]] = st.selectbox(
                rotulo,
                opcoes,
                index=None,
                format_func=p["opcoes"].get,
                placeholder="Selecione uma opção",
                key=f"q_{p['campo']}",
            )
    enviado = st.form_submit_button("Descobrir minha trilha", type="primary")

if enviado:
    faltando = [p["titulo"] for p in PERGUNTAS if respostas[p["campo"]] is None]
    if faltando:
        st.session_state.pop("resultado", None)
        st.error("Responda todas as perguntas para receber a recomendação. Faltam:")
        for titulo in faltando:
            st.markdown(f"- {titulo}")
    else:
        st.session_state["resultado"] = diagnosticar(respostas)

# ----------------------------------------------------------------------
# Resultado e justificativa
# ----------------------------------------------------------------------
resultado = st.session_state.get("resultado")
if resultado is not None:
    st.divider()
    st.header("🎯 Sua trilha recomendada")
    st.subheader(resultado.nome)
    st.write(TRILHAS[resultado.trilha]["descricao"])

    col1, col2 = st.columns(2)
    col1.metric("Pontuação", resultado.pontuacao)
    col2.metric("Confiança", resultado.confianca.capitalize().replace("Media", "Média"))

    if resultado.confianca == "alta":
        st.success("As suas respostas apontam com clareza para esta trilha.")
    elif resultado.confianca == "media":
        st.info("Esta é a melhor opção, mas há outra trilha relativamente próxima. Veja a segunda opção abaixo.")
    else:
        st.warning(
            "Seu perfil não tem preferências muito marcantes, então a recomendação tem confiança baixa. "
            "Considere também a segunda opção abaixo."
        )

    st.markdown("### Por que esta trilha?")
    st.caption("Regras disparadas que mais pesaram na decisão (pontos somados ou subtraídos desta trilha).")
    for d in resultado.regras_da_trilha():
        st.markdown(f"- **{d.regra}**: {d.motivo}  \n  `{d.pesos[resultado.trilha]:+d} pontos`")

    if resultado.alternativa:
        alt = resultado.alternativa
        pontos_alt = dict(resultado.ranking)[alt]
        st.markdown("### Segunda opção")
        st.write(f"**{TRILHAS[alt]['nome']}** ({pontos_alt} pontos)")
        with st.expander("Por que esta também aparece?"):
            for d in resultado.regras_da_trilha(alt):
                st.markdown(f"- **{d.regra}**: {d.motivo} (`{d.pesos[alt]:+d}`)")

    with st.expander("Pontuação de todas as trilhas"):
        tabela = pd.DataFrame(
            {"Pontos": [pts for _, pts in resultado.ranking]},
            index=[TRILHAS[t]["nome"] for t, _ in resultado.ranking],
        )
        st.bar_chart(tabela, horizontal=True)

    st.button("Refazer entrevista", on_click=reiniciar)
