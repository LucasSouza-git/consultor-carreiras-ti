"""Motor de inferência do Consultor Inteligente de Carreiras em TI.

Arquitetura (encadeamento para frente com Experta):

  1. O usuário responde à entrevista  ->  vira um fato `Perfil`.
  2. As regras @Rule (R01..R33) casam com o `Perfil`. Cada regra disparada
     soma (ou subtrai) pontos de uma ou mais trilhas e registra o motivo.
  3. Uma regra final de baixa prioridade (salience=-100) roda por último,
     apura o placar, desempata e declara o fato `Recomendacao`.

Regras que combinam 2 ou 3 respostas ("cruzadas") e regras com pontuação
negativa existem para desfazer ambiguidades, por exemplo Ciência de Dados
x Engenharia de Dados, Front-end x Mobile e DevOps x Cloud.
"""
from __future__ import annotations

# --- Compatibilidade: Experta 1.9.x usa collections.Mapping (removido no Python 3.10+)
import collections
import collections.abc

for _nome in ("Mapping", "MutableMapping", "Sequence", "Iterable", "Callable", "Hashable"):
    if not hasattr(collections, _nome):
        setattr(collections, _nome, getattr(collections.abc, _nome))
# ---------------------------------------------------------------------------------

from dataclasses import dataclass, field

from experta import Fact, Field, KnowledgeEngine, P, Rule

from perguntas import CAMPOS, OPCOES_VALIDAS


# ======================================================================
# Catálogo das 10 trilhas
# ======================================================================
TRILHAS = {
    "backend": {
        "nome": "Desenvolvimento Back-end",
        "descricao": "Lógica de servidores, construção de APIs, regras de negócio e bancos de dados.",
    },
    "frontend": {
        "nome": "Desenvolvimento Front-end & UI/UX",
        "descricao": "Interfaces web responsivas, experiência do usuário e frameworks reativos.",
    },
    "ciencia_dados": {
        "nome": "Ciência de Dados e Machine Learning",
        "descricao": "Estatística, modelagem preditiva, análise de grandes massas de dados e IA.",
    },
    "eng_dados": {
        "nome": "Engenharia de Dados",
        "descricao": "Arquitetura de dados, pipelines (ETL/ELT) e infraestrutura para Data Lakes.",
    },
    "ciberseguranca": {
        "nome": "Cibersegurança (Security / Pentesting)",
        "descricao": "Defesa cibernética, análise de vulnerabilidades, criptografia e redes seguras.",
    },
    "devops": {
        "nome": "DevOps & SRE",
        "descricao": "Automação de processos, integração e entrega contínua (CI/CD) e contêineres.",
    },
    "cloud": {
        "nome": "Computação em Nuvem (Cloud Architecture)",
        "descricao": "Planejamento, migração e gestão de infraestruturas escaláveis (AWS/Azure/GCP).",
    },
    "mobile": {
        "nome": "Desenvolvimento Mobile",
        "descricao": "Ecossistema de dispositivos móveis (nativo ou multiplataforma com Flutter/React Native).",
    },
    "qa": {
        "nome": "Engenharia de Qualidade e Testes (QA)",
        "descricao": "Testes automatizados, confiabilidade de software e processos de qualidade.",
    },
    "produto": {
        "nome": "Gestão de Produtos (Product Management)",
        "descricao": "Ponte entre negócio, design e desenvolvimento, metodologias ágeis e priorização de produto.",
    },
}

# Ordem fixa usada como último critério de desempate.
ORDEM = list(TRILHAS.keys())


# ======================================================================
# Fatos
# ======================================================================
class Perfil(Fact):
    """Respostas da entrevista (um campo por pergunta)."""

    matematica = Field(str, mandatory=True)   # baixa | media | alta
    atuacao = Field(str, mandatory=True)      # preferência de atuação diária
    ferramenta = Field(str, mandatory=True)   # linguagem/ferramenta de maior afinidade
    entrega = Field(str, mandatory=True)      # tipo de valor preferido
    plataforma = Field(str, mandatory=True)   # web | mobile | dados | infra | indiferente
    negocio = Field(str, mandatory=True)      # baixa | media | alta
    objetivo = Field(str, mandatory=True)     # construir | inovar | sustentar | liderar


class Recomendacao(Fact):
    """Conclusão do motor: trilha vencedora e sua pontuação."""

    trilha = Field(str, mandatory=True)
    pontuacao = Field(int, mandatory=True)


# ======================================================================
# Estruturas de saída
# ======================================================================
@dataclass
class Disparo:
    """Uma regra que foi disparada, com seu motivo e o efeito no placar."""

    regra: str
    motivo: str
    pesos: dict[str, int]


@dataclass
class Resultado:
    trilha: str
    pontuacao: int
    confianca: str                       # alta | media | baixa
    ranking: list[tuple[str, int]]       # (trilha, pontos) em ordem decrescente
    disparos: list[Disparo] = field(default_factory=list)

    @property
    def nome(self) -> str:
        return TRILHAS[self.trilha]["nome"]

    @property
    def alternativa(self) -> str | None:
        """Segunda colocada, quando houver pontuação positiva."""
        if len(self.ranking) > 1 and self.ranking[1][1] > 0:
            return self.ranking[1][0]
        return None

    def regras_da_trilha(self, trilha: str | None = None) -> list[Disparo]:
        """Regras que influenciaram uma trilha, da mais para a menos relevante."""
        t = trilha or self.trilha
        relevantes = [d for d in self.disparos if d.pesos.get(t, 0) != 0]
        return sorted(relevantes, key=lambda d: -abs(d.pesos[t]))

    def justificativa(self) -> str:
        """Texto explicando a recomendação com base nas regras disparadas."""
        linhas = [
            f"Trilha recomendada: {self.nome} ({self.pontuacao} pontos, confiança {self.confianca}).",
            "Principais regras disparadas:",
        ]
        for d in self.regras_da_trilha():
            linhas.append(f"  [{d.regra}] {d.motivo} ({d.pesos[self.trilha]:+d})")
        if self.alternativa:
            alt = TRILHAS[self.alternativa]["nome"]
            pts = dict(self.ranking)[self.alternativa]
            linhas.append(f"Segunda opção: {alt} ({pts} pontos).")
        return "\n".join(linhas)


# ======================================================================
# Helpers de padrão
# ======================================================================
def em(*valores: str):
    """Casa se o campo estiver entre os valores."""
    conjunto = frozenset(valores)
    return P(lambda x: x in conjunto)


def fora(*valores: str):
    """Casa se o campo NÃO estiver entre os valores."""
    conjunto = frozenset(valores)
    return P(lambda x: x not in conjunto)


# ======================================================================
# Base de conhecimento
# ======================================================================
class ConsultorCarreiras(KnowledgeEngine):
    def __init__(self):
        super().__init__()
        self.placar: dict[str, int] = {t: 0 for t in TRILHAS}
        self.disparos: list[Disparo] = []
        self.resultado: Resultado | None = None

    def _pontuar(self, regra: str, motivo: str, pesos: dict[str, int]) -> None:
        for trilha, pts in pesos.items():
            self.placar[trilha] += pts
        self.disparos.append(Disparo(regra, motivo, dict(pesos)))

    # ------------------------------------------------------------------
    # BACK-END
    # ------------------------------------------------------------------
    @Rule(Perfil(atuacao="algoritmos", ferramenta=em("python", "sql", "javascript")))
    def r01_backend_nucleo(self):
        self._pontuar("R01", "Gosta de escrever lógica/algoritmos e já usa linguagem de servidor ou banco de dados", {"backend": 4})

    @Rule(Perfil(atuacao="algoritmos", plataforma=em("web", "indiferente"), matematica=fora("alta")))
    def r02_backend_sem_matematica_pesada(self):
        self._pontuar("R02", "Prefere lógica de programação sem exigência de matemática avançada (afasta de Ciência de Dados)", {"backend": 3})

    @Rule(Perfil(atuacao="algoritmos", objetivo="construir"))
    def r03_backend_construir(self):
        self._pontuar("R03", "Objetivo de construir sistemas a partir de regras de negócio", {"backend": 2})

    @Rule(Perfil(atuacao="algoritmos", ferramenta="sql"))
    def r04_backend_banco_de_dados(self):
        self._pontuar("R04", "Lógica de programação combinada com afinidade em bancos de dados", {"backend": 2})

    # ------------------------------------------------------------------
    # FRONT-END & UI/UX
    # ------------------------------------------------------------------
    @Rule(Perfil(atuacao="layouts", ferramenta="javascript"))
    def r05_frontend_nucleo(self):
        self._pontuar("R05", "Gosta de criar interfaces visuais e domina JavaScript/TypeScript", {"frontend": 6})

    @Rule(Perfil(atuacao="layouts", entrega="produto_usuario"))
    def r06_frontend_entrega_usuario(self):
        self._pontuar("R06", "Quer entregar o produto final que o usuário utiliza, por meio de interfaces", {"frontend": 4})

    @Rule(Perfil(atuacao="layouts", plataforma="web"))
    def r07_frontend_web(self):
        self._pontuar("R07", "Interfaces visuais voltadas para o ambiente web", {"frontend": 2})

    # ------------------------------------------------------------------
    # MOBILE
    # ------------------------------------------------------------------
    @Rule(Perfil(atuacao="apps_moveis"))
    def r08_mobile_nucleo(self):
        self._pontuar("R08", "Quer criar aplicativos para celular no dia a dia", {"mobile": 6})

    @Rule(Perfil(plataforma="mobile", ferramenta="mobile"))
    def r09_mobile_ferramenta(self):
        self._pontuar("R09", "Prefere o ambiente móvel e já tem afinidade com ferramentas mobile", {"mobile": 4})

    @Rule(Perfil(atuacao="layouts", plataforma="mobile"))
    def r10_mobile_x_frontend(self):
        self._pontuar("R10", "Interfaces visuais em ambiente móvel: favorece Mobile e reduz Front-end web", {"mobile": 4, "frontend": -3})

    # ------------------------------------------------------------------
    # CIÊNCIA DE DADOS E ML
    # ------------------------------------------------------------------
    @Rule(Perfil(matematica="alta", atuacao="analise_dados"))
    def r11_ds_nucleo(self):
        self._pontuar("R11", "Alta afinidade com matemática/estatística e gosto por analisar dados brutos", {"ciencia_dados": 6})

    @Rule(Perfil(entrega="insights", ferramenta="python"))
    def r12_ds_insights_python(self):
        self._pontuar("R12", "Quer gerar previsões/insights e já usa Python (linguagem padrão de ML)", {"ciencia_dados": 4})

    @Rule(Perfil(objetivo="inovar", matematica=em("media", "alta"), plataforma="dados"))
    def r13_ds_inovacao(self):
        self._pontuar("R13", "Objetivo de inovar com dados/IA, com base matemática suficiente e foco em analytics", {"ciencia_dados": 3})

    @Rule(Perfil(matematica="baixa", atuacao="analise_dados"))
    def r14_ds_sem_matematica(self):
        self._pontuar("R14", "Baixa afinidade matemática reduz aderência a modelagem estatística e favorece Engenharia de Dados", {"ciencia_dados": -4, "eng_dados": 2})

    # ------------------------------------------------------------------
    # ENGENHARIA DE DADOS
    # ------------------------------------------------------------------
    @Rule(Perfil(atuacao="pipelines", ferramenta=em("python", "sql")))
    def r15_de_nucleo(self):
        self._pontuar("R15", "Gosta de construir fluxos de dados e usa Python/SQL (ferramentas de ETL/ELT)", {"eng_dados": 6})

    @Rule(Perfil(entrega="dados_prontos", plataforma="dados"))
    def r16_de_dados_prontos(self):
        self._pontuar("R16", "Quer entregar dados limpos e disponíveis no ambiente de dados", {"eng_dados": 4})

    @Rule(Perfil(atuacao="pipelines", matematica=fora("alta")))
    def r17_de_x_ds_pipelines(self):
        self._pontuar("R17", "Foco em pipelines sem exigir modelagem estatística avançada: favorece Eng. de Dados sobre Ciência de Dados", {"eng_dados": 2, "ciencia_dados": -2})

    @Rule(Perfil(atuacao="analise_dados", entrega="dados_prontos"))
    def r18_de_x_ds_dados_prontos(self):
        self._pontuar("R18", "Prefere preparar e disponibilizar dados a modelá-los: favorece Eng. de Dados sobre Ciência de Dados", {"eng_dados": 3, "ciencia_dados": -2})

    # ------------------------------------------------------------------
    # CIBERSEGURANÇA
    # ------------------------------------------------------------------
    @Rule(Perfil(atuacao="seguranca", ferramenta=em("linux_redes", "python")))
    def r19_sec_nucleo(self):
        self._pontuar("R19", "Quer atuar com segurança e domina Linux/Redes ou Python (base de pentest e automação de ataques/defesa)", {"ciberseguranca": 6})

    @Rule(Perfil(entrega="protecao"))
    def r20_sec_entrega(self):
        self._pontuar("R20", "O valor que quer entregar é a proteção contra invasões", {"ciberseguranca": 5})

    @Rule(Perfil(atuacao="seguranca", matematica=em("media", "alta")))
    def r21_sec_criptografia(self):
        self._pontuar("R21", "Interesse em segurança com base matemática para criptografia", {"ciberseguranca": 2})

    # ------------------------------------------------------------------
    # DEVOPS & SRE
    # ------------------------------------------------------------------
    @Rule(Perfil(atuacao="automacao", ferramenta=em("linux_redes", "cloud_containers")))
    def r22_devops_nucleo(self):
        self._pontuar("R22", "Gosta de automatizar build/deploy e usa Linux, contêineres ou ferramentas de nuvem", {"devops": 6})

    @Rule(Perfil(entrega="fluxo_entrega"))
    def r23_devops_entrega(self):
        self._pontuar("R23", "Valoriza entregas rápidas, frequentes e automatizadas (CI/CD)", {"devops": 5})

    @Rule(Perfil(atuacao="servidores", ferramenta=em("linux_redes", "cloud_containers")))
    def r24_devops_servidores(self):
        self._pontuar("R24", "Atuação prática com servidores e domínio de Linux/contêineres (mais operacional que arquitetural)", {"devops": 3, "cloud": 1})

    # ------------------------------------------------------------------
    # COMPUTAÇÃO EM NUVEM
    # ------------------------------------------------------------------
    @Rule(Perfil(atuacao="arquitetura", ferramenta="cloud_containers"))
    def r25_cloud_nucleo(self):
        self._pontuar("R25", "Quer planejar infraestruturas escaláveis e já tem afinidade com AWS/Azure/GCP", {"cloud": 6})

    @Rule(Perfil(plataforma="infra", entrega="infraestrutura", atuacao=em("arquitetura", "servidores")))
    def r26_cloud_infra(self):
        self._pontuar("R26", "Ambiente de infraestrutura, entregando a base que sustenta os sistemas, com perfil de planejamento/servidores", {"cloud": 4})

    # ------------------------------------------------------------------
    # QA
    # ------------------------------------------------------------------
    @Rule(Perfil(atuacao="testes"))
    def r27_qa_nucleo(self):
        self._pontuar("R27", "Gosta de testar software e caçar bugs no dia a dia", {"qa": 6})

    @Rule(Perfil(entrega="qualidade"))
    def r28_qa_entrega(self):
        self._pontuar("R28", "O valor que quer entregar é software confiável e sem falhas", {"qa": 5})

    @Rule(Perfil(atuacao="testes", ferramenta=em("python", "javascript")))
    def r29_qa_automacao_testes(self):
        self._pontuar("R29", "Testes combinados com linguagem de programação (automação de testes)", {"qa": 3})

    # ------------------------------------------------------------------
    # GESTÃO DE PRODUTOS
    # ------------------------------------------------------------------
    @Rule(Perfil(atuacao="produto"))
    def r30_pm_nucleo(self):
        self._pontuar("R30", "Quer definir o que será construído, priorizar e alinhar pessoas", {"produto": 6})

    @Rule(Perfil(entrega="estrategia", negocio="alta"))
    def r31_pm_estrategia(self):
        self._pontuar("R31", "Foco em estratégia de negócio e alta afinidade com conversas com clientes/times", {"produto": 5})

    @Rule(Perfil(objetivo="liderar", negocio=em("media", "alta")))
    def r32_pm_lideranca(self):
        self._pontuar("R32", "Objetivo de liderar produtos, com afinidade com negócio e pessoas", {"produto": 3})

    @Rule(Perfil(atuacao="produto", negocio="baixa"))
    def r33_pm_inconsistencia(self):
        self._pontuar("R33", "Interesse em gestão de produto, mas pouca afinidade com negócio e pessoas (reduz aderência)", {"produto": -4})

    # ------------------------------------------------------------------
    # DECISÃO FINAL (roda por último: salience muito baixa)
    # ------------------------------------------------------------------
    @Rule(Perfil(), salience=-100)
    def decidir(self):
        def positivas(trilha: str) -> int:
            return sum(1 for d in self.disparos if d.pesos.get(trilha, 0) > 0)

        # Critérios: maior pontuação > mais regras positivas > ordem fixa
        ranking = sorted(
            self.placar.items(),
            key=lambda kv: (-kv[1], -positivas(kv[0]), ORDEM.index(kv[0])),
        )
        (vencedora, pts), (_, pts2) = ranking[0], ranking[1]
        margem = pts - pts2
        if pts < 6 or margem < 2:
            confianca = "baixa"
        elif margem < 5:
            confianca = "media"
        else:
            confianca = "alta"

        self.declare(Recomendacao(trilha=vencedora, pontuacao=pts))
        self.resultado = Resultado(vencedora, pts, confianca, ranking, list(self.disparos))


# ======================================================================
# API de alto nível (usada pela interface Streamlit e pelos testes)
# ======================================================================
def validar_respostas(respostas: dict[str, str]) -> None:
    faltando = [c for c in CAMPOS if c not in respostas]
    if faltando:
        raise ValueError(f"Respostas ausentes: {', '.join(faltando)}")
    for campo, valor in respostas.items():
        if campo in OPCOES_VALIDAS and valor not in OPCOES_VALIDAS[campo]:
            raise ValueError(f"Valor inválido para '{campo}': {valor!r}")


def diagnosticar(respostas: dict[str, str]) -> Resultado:
    """Executa o motor de inferência e devolve o resultado."""
    validar_respostas(respostas)
    motor = ConsultorCarreiras()
    motor.reset()
    motor.declare(Perfil(**{c: respostas[c] for c in CAMPOS}))
    motor.run()
    assert motor.resultado is not None
    return motor.resultado


if __name__ == "__main__":
    exemplo = {
        "matematica": "alta",
        "atuacao": "analise_dados",
        "ferramenta": "python",
        "entrega": "insights",
        "plataforma": "dados",
        "negocio": "media",
        "objetivo": "inovar",
    }
    print(diagnosticar(exemplo).justificativa())
