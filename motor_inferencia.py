"""Motor de inferência com soma ponderada e penalidades (Etapa 2).

Como o motor calcula a compatibilidade de cada trilha:

1. Cada resposta vira uma intensidade entre 0 e 1.
   - Likert (1 a 5):  intensidade = (nota - 1) / 4
   - Escolha:         a opção marcada tem intensidade 1
2. Cada resposta multiplica o peso da pergunta para a trilha (vindo do JSON):
       pontos = importância da pergunta x peso da trilha x intensidade
3. A pontuação base é percentual, em relação ao máximo que a trilha poderia somar:
       base = 100 x soma(pontos) / soma(máximos)
4. As regras cruzadas do JSON somam bônus ou penalidades, em pontos percentuais,
   quando combinações de respostas indicam perfis conflitantes ou sinérgicos:
       final = limitar(base + soma(ajustes), 0, 100)
5. O ranking ordena as 10 trilhas pelo percentual final e o motor avalia se o
   resultado é claro, híbrido (empate técnico), fraco ou indiferenciado.

Nada disso depende do conteúdo das trilhas: perguntas, pesos e regras vêm do JSON.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean

from conhecimento import carregar_base, ESCALA_MAX, ESCALA_MIN


# ----------------------------------------------------------------------
# Estruturas de resultado
# ----------------------------------------------------------------------
@dataclass
class Fator:
    """Contribuição de uma pergunta para a pontuação de uma trilha."""

    pergunta: str
    texto: str            # enunciado da pergunta
    resposta: str         # resposta do usuário, em texto legível
    pontos: float
    maximo: float
    intensidade: float    # 0 a 1
    tipo: str             # likert | escolha

    @property
    def peso_efetivo(self) -> float:
        return self.maximo


@dataclass
class Ajuste:
    """Bônus ou penalidade de uma regra cruzada, em pontos percentuais."""

    regra: str
    descricao: str
    pontos: float


@dataclass
class Compatibilidade:
    trilha: str
    percentual: float     # final, de 0 a 100
    base: float           # antes dos ajustes
    pontos: float
    maximo: float
    fatores: list[Fator] = field(default_factory=list)
    ajustes: list[Ajuste] = field(default_factory=list)

    @property
    def total_ajustes(self) -> float:
        return sum(a.pontos for a in self.ajustes)


@dataclass
class Resultado:
    ranking: list[Compatibilidade]          # as 10 trilhas, da mais para a menos compatível
    leitura: str                            # clara | hibrida | fraca | indiferenciada
    mensagem: str                           # explicação da leitura, em linguagem simples
    avisos: list[str]
    empatadas: list[str]                    # trilhas dentro do limiar de empate do 1º lugar
    respostas: dict
    nomes: dict[str, str]
    faixas: list[dict]

    @property
    def top3(self) -> list[Compatibilidade]:
        return self.ranking[:3]

    @property
    def melhor(self) -> Compatibilidade:
        return self.ranking[0]

    def por_trilha(self, trilha: str) -> Compatibilidade:
        for c in self.ranking:
            if c.trilha == trilha:
                return c
        raise KeyError(trilha)

    def posicao(self, trilha: str) -> int:
        return [c.trilha for c in self.ranking].index(trilha) + 1

    def faixa(self, percentual: float) -> str:
        for f in sorted(self.faixas, key=lambda f: -f["min"]):
            if percentual >= f["min"]:
                return f["rotulo"]
        return self.faixas[-1]["rotulo"]

    def justificar(self, trilha: str, limite: int = 4) -> dict:
        """Explica por que a trilha pontuou assim: fatores a favor, pontos de atenção e ajustes."""
        comp = self.por_trilha(trilha)
        a_favor = sorted(
            (f for f in comp.fatores if f.maximo >= 3 and f.pontos / f.maximo >= 0.75 and f.intensidade > 0),
            key=lambda f: -f.pontos,
        )[:limite]
        atencao = sorted(
            (f for f in comp.fatores if f.maximo >= 5 and f.pontos / f.maximo <= 0.25),
            key=lambda f: -f.maximo,
        )[:limite]
        return {"a_favor": a_favor, "atencao": atencao, "ajustes": list(comp.ajustes)}

    def tabela(self):
        """Ranking completo como DataFrame do Pandas."""
        import pandas as pd

        return pd.DataFrame(
            {
                "Posição": range(1, len(self.ranking) + 1),
                "Trilha": [self.nomes[c.trilha] for c in self.ranking],
                "Compatibilidade (%)": [round(c.percentual) for c in self.ranking],
                "Base (%)": [round(c.base, 1) for c in self.ranking],
                "Ajustes (pp)": [round(c.total_ajustes, 1) for c in self.ranking],
            }
        )


# ----------------------------------------------------------------------
# Validação das respostas
# ----------------------------------------------------------------------
def validar_respostas(respostas: dict, regras: dict) -> None:
    erros = []
    for qid, q in regras["perguntas"].items():
        if qid not in respostas:
            erros.append(f"Falta responder: {q['texto']}")
            continue
        valor = respostas[qid]
        if q["tipo"] == "likert":
            if isinstance(valor, bool) or not isinstance(valor, int) or not ESCALA_MIN <= valor <= ESCALA_MAX:
                erros.append(f"Resposta inválida em '{qid}': use um número inteiro de {ESCALA_MIN} a {ESCALA_MAX}.")
        elif valor not in q["opcoes"]:
            erros.append(f"Resposta inválida em '{qid}': a opção {valor!r} não existe.")
    if erros:
        raise ValueError("\n".join(erros))


# ----------------------------------------------------------------------
# Cálculo
# ----------------------------------------------------------------------
def _resposta_legivel(q: dict, valor, escala: dict) -> str:
    if q["tipo"] == "likert":
        return f"{valor} ({escala.get(str(valor), '').lower()})"
    return q["opcoes"][valor]["rotulo"]


def _condicao_vale(cond: dict, q: dict, valor) -> bool:
    op, ref = cond["op"], cond["valor"]
    if op == "<=":
        return valor <= ref
    if op == ">=":
        return valor >= ref
    if op == "<":
        return valor < ref
    if op == ">":
        return valor > ref
    if op == "==":
        return valor == ref
    if op == "!=":
        return valor != ref
    return valor in ref  # "in"


def _compatibilidade_base(trilha: str, respostas: dict, regras: dict) -> Compatibilidade:
    escala = regras["parametros"].get("escala_likert", {})
    pontos_total = maximo_total = 0.0
    fatores: list[Fator] = []
    for qid, q in regras["perguntas"].items():
        imp = q.get("importancia", 1)
        if imp <= 0:
            continue  # perguntas de perfil, que só alimentam o roadmap
        valor = respostas[qid]
        if q["tipo"] == "likert":
            peso = q["pesos"].get(trilha, 0)
            maximo = imp * peso
            intensidade = (valor - ESCALA_MIN) / (ESCALA_MAX - ESCALA_MIN)
            pontos = maximo * intensidade
        else:
            peso = q["opcoes"][valor].get("pesos", {}).get(trilha, 0)
            maximo = imp * max(o.get("pesos", {}).get(trilha, 0) for o in q["opcoes"].values())
            intensidade = 1.0
            pontos = imp * peso
        if maximo <= 0:
            continue
        pontos_total += pontos
        maximo_total += maximo
        fatores.append(Fator(qid, q["texto"], _resposta_legivel(q, valor, escala), pontos, maximo, intensidade, q["tipo"]))
    base = 100 * pontos_total / maximo_total if maximo_total else 0.0
    return Compatibilidade(trilha, base, base, pontos_total, maximo_total, fatores)


def _aplicar_regras_cruzadas(compat: dict[str, Compatibilidade], respostas: dict, regras: dict) -> None:
    for regra in regras["regras_cruzadas"]:
        if all(_condicao_vale(c, regras["perguntas"][c["pergunta"]], respostas[c["pergunta"]]) for c in regra["se"]):
            for trilha, pp in regra["efeito"].items():
                compat[trilha].ajustes.append(Ajuste(regra["id"], regra["descricao"], pp))
    for c in compat.values():
        c.percentual = max(0.0, min(100.0, c.base + c.total_ajustes))


def _ler_resultado(ranking: list[Compatibilidade], respostas: dict, regras: dict, nomes: dict) -> tuple:
    par = regras["parametros"]
    limiar, fraco = par["limiar_empate_pp"], par["limiar_fraco_pct"]
    notas = [respostas[q] for q, d in regras["perguntas"].items() if d["tipo"] == "likert"]
    media = mean(notas) if notas else 0
    todas_iguais = bool(notas) and len(set(notas)) == 1

    topo = ranking[0]
    empatadas = [c.trilha for c in ranking if topo.percentual - c.percentual <= limiar]

    avisos = []
    if todas_iguais:
        avisos.append(
            f"Você deu a mesma nota ({notas[0]}) para todas as afinidades, então elas não ajudam a separar as trilhas. "
            "O resultado depende só das perguntas de escolha."
        )
    elif media >= par["media_alta_geral"]:
        avisos.append(
            "Você marcou afinidade alta com quase tudo, e isso aproxima as trilhas. "
            "Se puder, reserve as notas 4 e 5 para o que você mais gosta de fazer."
        )
    elif media <= par["media_baixa_geral"]:
        avisos.append(
            "Você marcou pouca afinidade com quase todas as atividades. "
            "Vale explorar projetos pequenos em algumas áreas antes de escolher uma trilha."
        )

    if todas_iguais:
        leitura = "indiferenciada"
        mensagem = "As notas iguais não permitem separar as trilhas. O ranking se baseia apenas nas perguntas de escolha."
    elif topo.percentual < fraco:
        leitura = "fraca"
        mensagem = (
            f"Nenhuma trilha passou de {fraco}% de compatibilidade. "
            "Suas respostas indicam pouca afinidade com as atividades listadas."
        )
    elif len(empatadas) >= 2:
        leitura = "hibrida"
        outras = [c for c in ranking if c.trilha in empatadas]
        lista = ", ".join(f"{nomes[c.trilha]} ({c.percentual:.0f}%)" for c in outras[:-1]) + f" e {nomes[outras[-1].trilha]} ({outras[-1].percentual:.0f}%)"
        mensagem = (
            f"Empate técnico: {lista} ficaram a menos de {limiar} pontos percentuais uma da outra. "
            "Seu perfil combina essas trilhas, e a escolha depende do que você quer fazer no dia a dia."
        )
    else:
        leitura = "clara"
        margem = topo.percentual - ranking[1].percentual
        mensagem = f"{nomes[topo.trilha]} se destaca, com {margem:.0f} pontos percentuais à frente da segunda colocada."
    return leitura, mensagem, avisos, empatadas


def avaliar(respostas: dict, regras: dict | None = None, trilhas: dict | None = None) -> Resultado:
    """Calcula o ranking de compatibilidade das 10 trilhas a partir das respostas."""
    if regras is None or trilhas is None:
        regras, trilhas = carregar_base()
    validar_respostas(respostas, regras)

    ordem = list(trilhas["trilhas"])
    nomes = {t: dados["nome"] for t, dados in trilhas["trilhas"].items()}
    compat = {t: _compatibilidade_base(t, respostas, regras) for t in ordem}
    _aplicar_regras_cruzadas(compat, respostas, regras)

    # Desempate: percentual final, depois pontos brutos, depois a ordem do catálogo.
    ranking = sorted(compat.values(), key=lambda c: (-c.percentual, -c.pontos, ordem.index(c.trilha)))
    leitura, mensagem, avisos, empatadas = _ler_resultado(ranking, respostas, regras, nomes)
    return Resultado(ranking, leitura, mensagem, avisos, empatadas, dict(respostas), nomes, regras["parametros"]["faixas_compatibilidade"])


if __name__ == "__main__":
    exemplo = dict(
        experiencia="iniciando", horas_semana="10", ferramenta="linux_redes",
        matematica=3, logica=4, analise_dados=2, pipelines=2, apis_bd=3, design=1, mobile=1, gestao=2,
        infra=5, nuvem=3, automacao=5, seguranca=3, testes=2,
        objetivo="sustentar", entrega="fluxo_entrega", ambiente="infra",
    )
    r = avaliar(exemplo)
    print(r.tabela().to_string(index=False))
    print(r.leitura, "-", r.mensagem)
