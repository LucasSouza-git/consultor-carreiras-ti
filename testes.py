"""Testes de robustez e casos limite da Etapa 2 (Fase 5).

Execução:
    python testes.py              # relatório resumido (bom para capturas de tela)
    python testes.py --detalhes   # inclui a justificativa de cada caso
    pytest testes.py              # também funciona com pytest (opcional)
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

import pandas as pd

from conhecimento import BaseConhecimentoInvalida, carregar_base, validar
from gaps_roadmap import analisar_gaps, plano_para_markdown
from motor_pontuacao import avaliar

REGRAS, TRILHAS = carregar_base()
LIKERTS = [q for q, d in REGRAS["perguntas"].items() if d["tipo"] == "likert"]


def perfil(base: int = 2, ferramenta="nenhuma", objetivo="construir", entrega="produto_usuario", ambiente="indiferente",
           experiencia="iniciando", horas_semana="10", **notas) -> dict:
    """Monta as respostas de um perfil. Afinidades não citadas recebem `base`."""
    desconhecidas = set(notas) - set(LIKERTS)
    assert not desconhecidas, f"afinidades inexistentes: {desconhecidas}"
    resp = {q: notas.get(q, base) for q in LIKERTS}
    resp.update(ferramenta=ferramenta, objetivo=objetivo, entrega=entrega, ambiente=ambiente,
                experiencia=experiencia, horas_semana=horas_semana)
    return resp


# ----------------------------------------------------------------------
# Personas típicas: uma por trilha
# ----------------------------------------------------------------------
PERSONAS = [
    ("Felipe (lógica e APIs)", "Gosta de resolver problemas com código, APIs e bancos de dados.",
     perfil(logica=5, apis_bd=5, matematica=3, infra=3, testes=3, ferramenta="sql", ambiente="web"), "backend"),
    ("Carla (visual)", "Adora interfaces bonitas e usáveis, em JavaScript, para a web.",
     perfil(design=5, logica=3, mobile=2, ferramenta="javascript", ambiente="web"), "frontend"),
    ("Ana (analítica)", "Estatística, Python e previsões a partir de dados.",
     perfil(matematica=5, analise_dados=5, logica=4, ferramenta="python", objetivo="inovar", entrega="insights", ambiente="dados"), "ciencia_dados"),
    ("Eduarda (pipelines)", "Gosta de mover, limpar e organizar dados para outros times.",
     perfil(pipelines=5, apis_bd=3, logica=4, analise_dados=3, matematica=3, ferramenta="sql", entrega="dados_prontos", ambiente="dados"), "eng_dados"),
    ("Bruno (segurança)", "Linux, redes e vulnerabilidades.",
     perfil(seguranca=5, infra=4, logica=4, matematica=3, ferramenta="linux_redes", objetivo="sustentar", entrega="protecao", ambiente="infra"), "ciberseguranca"),
    ("Gabriela (automação)", "CI/CD, contêineres e entregas frequentes.",
     perfil(automacao=5, infra=4, nuvem=3, logica=4, ferramenta="cloud_containers", objetivo="sustentar", entrega="fluxo_entrega", ambiente="infra"), "devops"),
    ("Henrique (arquitetura)", "Desenhar sistemas escaláveis e migrar para a nuvem.",
     perfil(nuvem=5, infra=4, automacao=3, logica=3, ferramenta="cloud_containers", objetivo="sustentar", entrega="infraestrutura", ambiente="infra"), "cloud"),
    ("Isabela (apps)", "Aplicativos de celular com boa interface.",
     perfil(mobile=5, design=4, logica=4, ferramenta="mobile", entrega="produto_usuario", ambiente="mobile"), "mobile"),
    ("João (qualidade)", "Caçar bugs e automatizar testes.",
     perfil(testes=5, logica=3, automacao=3, ferramenta="python", objetivo="sustentar", entrega="qualidade", ambiente="web"), "qa"),
    ("Diego (negócios)", "Conversar com clientes e definir o que construir.",
     perfil(gestao=5, design=3, analise_dados=3, logica=2, objetivo="liderar", entrega="estrategia"), "produto"),
]

# ----------------------------------------------------------------------
# Casos limite: perfis ambíguos, extremos e contraditórios
# ----------------------------------------------------------------------
HIBRIDO_DADOS_WEB = perfil(
    analise_dados=5, matematica=4, logica=5, apis_bd=5, design=4, pipelines=3,
    ferramenta="python", entrega="produto_usuario", ambiente="indiferente",
)
TUDO_1, TUDO_3, TUDO_5 = (perfil(base=n, ambiente="indiferente") for n in (1, 3, 5))
DADOS_SEM_MATEMATICA = perfil(analise_dados=5, matematica=1, pipelines=3, logica=3, ferramenta="sql", entrega="dados_prontos", ambiente="dados")
CLOUD_SEM_AUTOMACAO = perfil(nuvem=5, infra=5, automacao=1, logica=3, ferramenta="cloud_containers", entrega="infraestrutura", ambiente="infra")
DEVOPS_FORTE = perfil(automacao=5, infra=5, nuvem=3, logica=4, ferramenta="cloud_containers", entrega="fluxo_entrega", ambiente="infra")
BACKEND_SEM_LOGICA = perfil(apis_bd=5, logica=1, ferramenta="sql", ambiente="web")
BACKEND_COM_LOGICA = perfil(apis_bd=5, logica=5, ferramenta="sql", ambiente="web")
DESIGN_NO_CELULAR = perfil(design=5, mobile=5, logica=3, ferramenta="mobile", entrega="produto_usuario", ambiente="mobile")


def _pct(resp: dict, trilha: str) -> float:
    return avaliar(resp, REGRAS, TRILHAS).por_trilha(trilha).percentual


# ----------------------------------------------------------------------
# Testes (compatíveis com pytest)
# ----------------------------------------------------------------------
def test_base_de_conhecimento_valida():
    validar(REGRAS, TRILHAS)
    assert len(TRILHAS["trilhas"]) == 10
    assert len(REGRAS["regras_cruzadas"]) >= 20


def test_todas_as_trilhas_tem_conteudo_para_o_plano():
    for tid, t in TRILHAS["trilhas"].items():
        assert len(t["competencias_junior"]) >= 9, tid
        assert len(t["projetos"]) >= 3, tid
        assert len(t["certificacoes"]) >= 2, tid
        assert {c["fase"] for c in t["competencias_junior"]} == {1, 2, 3}, tid


def test_personas_recebem_a_trilha_esperada():
    for nome, _, resp, esperada in PERSONAS:
        r = avaliar(resp, REGRAS, TRILHAS)
        assert r.melhor.trilha == esperada, f"{nome}: esperado {esperada}, obtido {r.melhor.trilha}"
        assert r.melhor.percentual >= 60, f"{nome}: compatibilidade baixa demais ({r.melhor.percentual:.0f}%)"


def test_cobertura_das_10_trilhas():
    assert {esperada for *_, esperada in PERSONAS} == set(TRILHAS["trilhas"])


def test_ranking_completo_e_consistente():
    for _, _, resp, _ in PERSONAS:
        r = avaliar(resp, REGRAS, TRILHAS)
        assert len(r.ranking) == 10 and len(r.top3) == 3
        pcts = [c.percentual for c in r.ranking]
        assert pcts == sorted(pcts, reverse=True)
        assert all(0 <= p <= 100 for p in pcts)
        assert {c.trilha for c in r.ranking} == set(TRILHAS["trilhas"])


def test_resultado_e_deterministico():
    a = avaliar(PERSONAS[0][2], REGRAS, TRILHAS)
    b = avaliar(copy.deepcopy(PERSONAS[0][2]), REGRAS, TRILHAS)
    assert [(c.trilha, c.percentual) for c in a.ranking] == [(c.trilha, c.percentual) for c in b.ranking]


def test_caso_limite_hibrido_dados_e_web():
    r = avaliar(HIBRIDO_DADOS_WEB, REGRAS, TRILHAS)
    top = {c.trilha for c in r.top3}
    assert "ciencia_dados" in top and ({"backend", "frontend"} & top), "o top 3 deve refletir os dois interesses"
    assert r.leitura == "hibrida", "dados e web devem gerar empate técnico"
    assert len(r.empatadas) >= 2
    assert "Empate técnico" in r.mensagem
    assert r.justificar(r.melhor.trilha)["a_favor"], "o empate também precisa de justificativa coerente"


def test_caso_limite_notas_todas_iguais():
    for resp in (TUDO_1, TUDO_3, TUDO_5):
        r = avaliar(resp, REGRAS, TRILHAS)
        assert r.leitura == "indiferenciada"
        assert r.avisos and "mesma nota" in r.avisos[0]
        assert len(r.ranking) == 10  # nunca quebra


def test_caso_limite_tudo_1_nao_gera_compatibilidade_alta():
    assert avaliar(TUDO_1, REGRAS, TRILHAS).melhor.percentual < 45


def test_caso_limite_afinidade_alta_em_tudo_avisa():
    resp = perfil(base=5, ambiente="indiferente")
    resp["logica"] = 4  # deixa de ser "todas iguais" mas continua com média alta
    r = avaliar(resp, REGRAS, TRILHAS)
    assert any("afinidade alta" in a for a in r.avisos)


def test_penalidade_gosta_de_dados_mas_evita_matematica():
    r = avaliar(DADOS_SEM_MATEMATICA, REGRAS, TRILHAS)
    assert r.melhor.trilha == "eng_dados"
    assert r.posicao("ciencia_dados") > r.posicao("eng_dados")
    assert any(a.regra == "X02" for a in r.por_trilha("ciencia_dados").ajustes)


def test_cloud_x_devops_se_separam_pela_automacao():
    assert avaliar(CLOUD_SEM_AUTOMACAO, REGRAS, TRILHAS).melhor.trilha == "cloud"
    assert avaliar(DEVOPS_FORTE, REGRAS, TRILHAS).melhor.trilha == "devops"


def test_penalidade_baixa_logica_reduz_backend():
    assert _pct(BACKEND_COM_LOGICA, "backend") - _pct(BACKEND_SEM_LOGICA, "backend") >= 15


def test_front_x_mobile_design_no_celular():
    assert avaliar(DESIGN_NO_CELULAR, REGRAS, TRILHAS).melhor.trilha == "mobile"


def test_aumentar_afinidade_central_nunca_reduz_a_base():
    """Sem as regras cruzadas, mais afinidade só pode aumentar a pontuação base."""
    base = perfil(design=2, ferramenta="javascript", ambiente="web")
    mais = dict(base, design=5)
    assert avaliar(mais, REGRAS, TRILHAS).por_trilha("frontend").base > avaliar(base, REGRAS, TRILHAS).por_trilha("frontend").base


def test_respostas_invalidas_sao_recusadas():
    base = PERSONAS[0][2]
    for q in list(REGRAS["perguntas"]):
        incompleto = {k: v for k, v in base.items() if k != q}
        try:
            avaliar(incompleto, REGRAS, TRILHAS)
            assert False, f"deveria recusar resposta ausente: {q}"
        except ValueError:
            pass
    for invalido in (0, 6, "3", 3.5, True, None):
        try:
            avaliar(dict(base, logica=invalido), REGRAS, TRILHAS)
            assert False, f"deveria recusar nota {invalido!r}"
        except ValueError:
            pass
    try:
        avaliar(dict(base, objetivo="inexistente"), REGRAS, TRILHAS)
        assert False
    except ValueError:
        pass


def test_base_externa_realmente_governa_o_motor():
    """Muda um peso no JSON (sem tocar no código) e o resultado muda."""
    alterada = copy.deepcopy(REGRAS)
    for t in alterada["perguntas"]["design"]["pesos"]:
        alterada["perguntas"]["design"]["pesos"][t] = 0
    alterada["perguntas"]["design"]["pesos"]["backend"] = 10
    alterada["regras_cruzadas"] = [r for r in alterada["regras_cruzadas"] if r["id"] not in ("X08",)]
    resp = perfil(design=5, apis_bd=2, ferramenta="nenhuma", ambiente="indiferente")
    assert avaliar(resp, REGRAS, TRILHAS).por_trilha("backend").percentual != avaliar(resp, alterada, TRILHAS).por_trilha("backend").percentual
    with tempfile.TemporaryDirectory() as tmp:
        caminho = Path(tmp) / "regras_alternativas.json"
        caminho.write_text(json.dumps(alterada, ensure_ascii=False), encoding="utf-8")
        regras2, trilhas2 = carregar_base(caminho_regras=caminho)
        assert regras2["perguntas"]["design"]["pesos"]["backend"] == 10


def test_base_invalida_e_detectada():
    quebrada = copy.deepcopy(REGRAS)
    quebrada["perguntas"]["logica"]["pesos"]["trilha_que_nao_existe"] = 5
    quebrada["regras_cruzadas"][0]["se"][0]["pergunta"] = "pergunta_fantasma"
    try:
        validar(quebrada, TRILHAS)
        assert False, "deveria detectar a base inválida"
    except BaseConhecimentoInvalida as e:
        assert "trilha_que_nao_existe" in str(e) and "pergunta_fantasma" in str(e)


def test_gaps_sem_conhecimento_e_com_tudo():
    comps = {c["id"] for c in TRILHAS["trilhas"]["devops"]["competencias_junior"]}
    vazio = analisar_gaps("devops", set(), horas_semana=10)
    assert vazio.prontidao == 0 and len(vazio.lacunas) == len(comps) and vazio.semanas_total > 0
    cheio = analisar_gaps("devops", comps, horas_semana=10)
    assert cheio.prontidao == 100 and not cheio.lacunas and cheio.semanas_total == 0 and not cheio.etapas


def test_gaps_prontidao_e_ordem_de_estudo():
    t = TRILHAS["trilhas"]["backend"]["competencias_junior"]
    plano = analisar_gaps("backend", {t[0]["id"]}, horas_semana=10)
    assert 0 < plano.prontidao < 100
    fases = [c.fase for c in plano.lacunas]
    assert fases == sorted(fases), "fundamentos devem vir antes"
    assert t[0]["id"] not in {c.id for c in plano.lacunas}
    assert plano.etapas[0].semana_inicio == 1


def test_gaps_horas_semanais_mudam_o_prazo():
    lento = analisar_gaps("qa", set(), horas_semana=5)
    rapido = analisar_gaps("qa", set(), horas_semana=20)
    assert lento.semanas_total > rapido.semanas_total
    assert lento.horas_total == rapido.horas_total


def test_gaps_certificacoes_seguem_a_prontidao():
    todos = {c["id"] for c in TRILHAS["trilhas"]["ciberseguranca"]["competencias_junior"]}
    iniciante = analisar_gaps("ciberseguranca", set(), 10)
    pronto = analisar_gaps("ciberseguranca", todos, 10)
    assert 0 < sum(c.agora for c in iniciante.certificacoes) < len(iniciante.certificacoes)
    assert all(c.agora for c in pronto.certificacoes if c.a_partir_de <= 100)


def test_gaps_projeto_inicial_depende_da_prontidao():
    comps = [c["id"] for c in TRILHAS["trilhas"]["frontend"]["competencias_junior"]]
    assert analisar_gaps("frontend", set(), 10).projetos[0].comecar_aqui
    avancado = analisar_gaps("frontend", set(comps[:8]), 10)
    assert avancado.prontidao >= 50 and not avancado.projetos[0].comecar_aqui and avancado.projetos[1].comecar_aqui


def test_gaps_entradas_invalidas():
    for args in (("trilha_inexistente", set(), 10), ("devops", {"skill_que_nao_existe"}, 10), ("devops", set(), 0)):
        try:
            analisar_gaps(*args)
            assert False, f"deveria recusar {args}"
        except ValueError:
            pass


def test_markdown_do_plano():
    md = plano_para_markdown(analisar_gaps("produto", set(), 10, "nenhuma"))
    assert md.startswith("# Plano de ação: Gestão de Produtos")
    assert "## Roadmap" in md and "## Certificações" in md and "## Projetos para o portfólio no GitHub" in md


def test_certificacoes_descontinuadas_nao_aparecem():
    texto = json.dumps(TRILHAS, ensure_ascii=False)
    assert "Associate Android Developer" in TRILHAS["trilhas"]["mobile"]["nota_certificacoes"]
    nomes = [c["nome"] for t in TRILHAS["trilhas"].values() for c in t["certificacoes"]]
    assert not any("DP-203" in n or "Associate Android Developer" in n for n in nomes), "certificação já descontinuada na lista"
    assert "DP-700" in texto


# ----------------------------------------------------------------------
# Relatório
# ----------------------------------------------------------------------
def _linha_top3(r) -> str:
    return " | ".join(f"{i}º {TRILHAS['trilhas'][c.trilha]['curto']} {c.percentual:.0f}%" for i, c in enumerate(r.top3, 1))


def main(detalhes: bool = False) -> int:
    falhas = 0
    largura = 118
    print("=" * largura + "\nVALIDAÇÃO DO SISTEMA ESPECIALISTA (ETAPA 2)\n" + "=" * largura)

    print("\nPersonas típicas (uma por trilha):")
    linhas = []
    for nome, desc, resp, esperada in PERSONAS:
        r = avaliar(resp, REGRAS, TRILHAS)
        ok = r.melhor.trilha == esperada
        falhas += not ok
        linhas.append({"": "OK" if ok else "ERRO", "Persona": nome, "Esperada": TRILHAS["trilhas"][esperada]["curto"], "Top 3": _linha_top3(r), "Leitura": r.leitura})
        if detalhes:
            print(f"\n  {nome}: {desc}\n  {r.mensagem}")
    print(pd.DataFrame(linhas).to_string(index=False))

    print("\nCasos limite:")
    casos = [
        ("Híbrido: dados + desenvolvimento web", HIBRIDO_DADOS_WEB, "hibrida"),
        ("Gosta de dados, mas evita matemática", DADOS_SEM_MATEMATICA, "clara"),
        ("Cloud sem gosto por automação", CLOUD_SEM_AUTOMACAO, None),
        ("Design + celular", DESIGN_NO_CELULAR, None),
        ("Back-end com lógica 1 (conflito)", BACKEND_SEM_LOGICA, None),
        ("Todas as notas 1", TUDO_1, "indiferenciada"),
        ("Todas as notas 3", TUDO_3, "indiferenciada"),
        ("Todas as notas 5", TUDO_5, "indiferenciada"),
    ]
    linhas = []
    for nome, resp, leitura_esperada in casos:
        r = avaliar(resp, REGRAS, TRILHAS)
        ok = leitura_esperada is None or r.leitura == leitura_esperada
        falhas += not ok
        linhas.append({"": "OK" if ok else "ERRO", "Caso": nome, "Top 3": _linha_top3(r), "Leitura": r.leitura})
        if detalhes:
            j = r.justificar(r.melhor.trilha)
            print(f"\n  {nome}\n  {r.mensagem}")
            for av in r.avisos:
                print(f"  Aviso: {av}")
            for f in j["a_favor"]:
                print(f"  + {f.texto}: {f.resposta}")
            for a in j["ajustes"]:
                print(f"  {a.pontos:+.0f} pp [{a.regra}] {a.descricao}")
    print(pd.DataFrame(linhas).to_string(index=False))

    total = len(PERSONAS) + len(casos)
    print("\n" + "=" * largura)
    print(f"Resultado: {total - falhas}/{total} casos corretos | trilhas: {len(TRILHAS['trilhas'])} | regras cruzadas: {len(REGRAS['regras_cruzadas'])} | perguntas: {len(REGRAS['perguntas'])}")
    print("=" * largura)
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main(detalhes="--detalhes" in sys.argv))
