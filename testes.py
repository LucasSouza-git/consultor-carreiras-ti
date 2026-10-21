"""Validação do motor de inferência com personas de teste (Fase 4).

Execução:
    python testes.py              # relatório resumido (bom para capturas de tela)
    python testes.py --detalhes   # inclui a justificativa de cada persona
    pytest testes.py              # também funciona com pytest (opcional)
"""
import sys

from motor_inferencia import TRILHAS, ConsultorCarreiras, diagnosticar
from perguntas import CAMPOS, OPCOES_VALIDAS


def perfil(matematica, atuacao, ferramenta, entrega, plataforma, negocio, objetivo):
    return dict(
        matematica=matematica, atuacao=atuacao, ferramenta=ferramenta, entrega=entrega,
        plataforma=plataforma, negocio=negocio, objetivo=objetivo,
    )


# Cada persona: (nome, descrição, respostas, trilha esperada)
# As 4 primeiras seguem os perfis pedidos no enunciado.
PERSONAS = [
    (
        "Ana (analítica)",
        "Adora estatística, trabalha com Python e quer prever comportamentos a partir de dados.",
        perfil("alta", "analise_dados", "python", "insights", "dados", "media", "inovar"),
        "ciencia_dados",
    ),
    (
        "Bruno (infra/segurança)",
        "Domina Linux e redes e gosta de procurar vulnerabilidades para proteger sistemas.",
        perfil("media", "seguranca", "linux_redes", "protecao", "infra", "baixa", "sustentar"),
        "ciberseguranca",
    ),
    (
        "Carla (visual/front-end)",
        "Gosta de criar interfaces bonitas em JavaScript, para a web, usadas direto pelo usuário.",
        perfil("baixa", "layouts", "javascript", "produto_usuario", "web", "media", "construir"),
        "frontend",
    ),
    (
        "Diego (negócios/produto)",
        "Sem experiência em código, ama conversar com clientes e definir prioridades e estratégia.",
        perfil("baixa", "produto", "nenhuma", "estrategia", "indiferente", "alta", "liderar"),
        "produto",
    ),
    (
        "Eduarda (pipelines)",
        "Usa SQL e Python para mover, limpar e organizar dados para outros times.",
        perfil("media", "pipelines", "sql", "dados_prontos", "dados", "baixa", "construir"),
        "eng_dados",
    ),
    (
        "Felipe (servidores/APIs)",
        "Curte lógica de programação em Python, APIs e regras de negócio na web.",
        perfil("media", "algoritmos", "python", "produto_usuario", "web", "media", "construir"),
        "backend",
    ),
    (
        "Gabriela (automação)",
        "Gosta de automatizar build e deploy com contêineres e entregas frequentes.",
        perfil("media", "automacao", "cloud_containers", "fluxo_entrega", "infra", "media", "sustentar"),
        "devops",
    ),
    (
        "Henrique (arquitetura)",
        "Quer desenhar infraestruturas escaláveis e migrações em AWS/Azure/GCP.",
        perfil("media", "arquitetura", "cloud_containers", "infraestrutura", "infra", "media", "sustentar"),
        "cloud",
    ),
    (
        "Isabela (apps)",
        "Quer criar aplicativos para celular usando Flutter ou Kotlin.",
        perfil("baixa", "apps_moveis", "mobile", "produto_usuario", "mobile", "media", "construir"),
        "mobile",
    ),
    (
        "João (qualidade)",
        "Gosta de caçar bugs, automatizar testes e garantir software confiável.",
        perfil("media", "testes", "python", "qualidade", "web", "media", "sustentar"),
        "qa",
    ),
]

# Casos de ambiguidade: o sistema precisa separar trilhas parecidas.
CASOS_AMBIGUOS = [
    (
        "Karina (analisa dados, mas quer dados prontos)",
        "Gosta de mexer em dados brutos, mas prefere entregar bases organizadas a criar modelos.",
        perfil("media", "analise_dados", "sql", "dados_prontos", "dados", "baixa", "construir"),
        "eng_dados",  # e não Ciência de Dados
    ),
    (
        "Lucas (layouts no celular)",
        "Gosta de criar interfaces, mas para aplicativos de celular.",
        perfil("media", "layouts", "mobile", "produto_usuario", "mobile", "media", "construir"),
        "mobile",  # e não Front-end
    ),
    (
        "Marina (servidores e entrega rápida)",
        "Mexe com servidores Linux e quer entregas rápidas e automatizadas.",
        perfil("media", "servidores", "linux_redes", "fluxo_entrega", "infra", "baixa", "sustentar"),
        "devops",  # e não Cloud
    ),
    (
        "Nando (matemática baixa, análise de dados)",
        "Gosta de analisar dados brutos, mas tem pouca afinidade com matemática e quer dados prontos.",
        perfil("baixa", "analise_dados", "sql", "dados_prontos", "dados", "baixa", "construir"),
        "eng_dados",  # e não Ciência de Dados
    ),
]

INICIANTE = perfil("media", "algoritmos", "nenhuma", "produto_usuario", "indiferente", "media", "construir")


# ----------------------------------------------------------------------
# Testes (compatíveis com pytest)
# ----------------------------------------------------------------------
def test_quantidade_de_regras():
    # get_rules() inclui a regra final de decisão
    assert len(ConsultorCarreiras().get_rules()) - 1 >= 25


def test_personas_principais():
    for nome, _, respostas, esperada in PERSONAS:
        assert diagnosticar(respostas).trilha == esperada, nome


def test_cobertura_das_10_trilhas():
    cobertas = {esperada for _, _, _, esperada in PERSONAS}
    assert cobertas == set(TRILHAS)


def test_casos_ambiguos():
    for nome, _, respostas, esperada in CASOS_AMBIGUOS:
        assert diagnosticar(respostas).trilha == esperada, nome


def test_iniciante_tem_confianca_baixa():
    assert diagnosticar(INICIANTE).confianca == "baixa"


def test_justificativa_cita_regras():
    for nome, _, respostas, _ in PERSONAS:
        r = diagnosticar(respostas)
        assert r.regras_da_trilha(), nome
        assert "[R" in r.justificativa(), nome


def test_respostas_invalidas():
    base = PERSONAS[0][2]
    for campo in CAMPOS:
        incompleto = {k: v for k, v in base.items() if k != campo}
        try:
            diagnosticar(incompleto)
            assert False, f"deveria rejeitar resposta ausente: {campo}"
        except ValueError:
            pass
    try:
        diagnosticar({**base, "atuacao": "inexistente"})
        assert False, "deveria rejeitar valor inválido"
    except ValueError:
        pass


def test_todas_as_opcoes_sao_aceitas():
    # Garante que nenhuma opção da interface quebra o motor.
    base = PERSONAS[0][2]
    for campo, valores in OPCOES_VALIDAS.items():
        for v in valores:
            diagnosticar({**base, campo: v})


# ----------------------------------------------------------------------
# Relatório
# ----------------------------------------------------------------------
def _linha(nome, esperada, r):
    ok = "OK  " if r.trilha == esperada else "ERRO"
    return f"[{ok}] {nome:46s} esperada={esperada:15s} obtida={r.trilha:15s} {r.pontuacao:2d} pts  conf={r.confianca}"


def main(detalhes: bool = False) -> int:
    falhas = 0
    print("=" * 118)
    print("VALIDAÇÃO COM PERSONAS DE TESTE")
    print("=" * 118)
    for titulo, grupo in (("Personas principais", PERSONAS), ("Casos de ambiguidade", CASOS_AMBIGUOS)):
        print(f"\n{titulo}:")
        for nome, descricao, respostas, esperada in grupo:
            r = diagnosticar(respostas)
            falhas += r.trilha != esperada
            print(_linha(nome, esperada, r))
            if detalhes:
                print(f"    Perfil: {descricao}")
                print("    " + r.justificativa().replace("\n", "\n    "))

    r = diagnosticar(INICIANTE)
    print("\nPerfil sem preferências marcantes (iniciante):")
    print(f"    recomendação={r.nome}, pts={r.pontuacao}, confiança={r.confianca} (esperado: baixa)")
    falhas += r.confianca != "baixa"

    total = len(PERSONAS) + len(CASOS_AMBIGUOS)
    print("\n" + "=" * 118)
    print(f"Resultado: {total - falhas}/{total} personas corretas | regras na base: {len(ConsultorCarreiras().get_rules()) - 1}")
    print("=" * 118)
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main(detalhes="--detalhes" in sys.argv))
