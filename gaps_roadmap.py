"""Análise de gaps (skill gap) e geração de roadmap personalizado (Etapa 2, Fase 3).

Entrada:  a trilha escolhida, as competências que o usuário já domina (checklist),
          as horas semanais disponíveis e a experiência atual.
Saída:    um `PlanoAcao` com a prontidão para o nível Júnior, as lacunas em ordem de
          prioridade, o roadmap por fases com prazo estimado, as certificações
          adequadas ao momento e os projetos de portfólio para o GitHub.

Todo o conteúdo (competências, horas, certificações, projetos) vem de `trilhas.json`.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from conhecimento import carregar_trilhas

LIMIAR_PRONTO = 85  # prontidão a partir da qual o usuário já cobre quase todo o nível Júnior

PONTO_DE_PARTIDA = {
    "nenhuma": "Como você ainda não programa, siga a ordem do roadmap sem pular etapas. Os fundamentos da fase 1 vão sustentar todo o resto.",
    "iniciando": "Você está começando, então foque em concluir a fase 1 antes de buscar certificações.",
    "projetos": "Você já tem prática com projetos. Use isso a seu favor e transforme o que já fez em itens de portfólio.",
    "trabalho": "Você já atua na área. Priorize as lacunas essenciais e use o seu dia a dia como laboratório para os projetos.",
}


@dataclass
class Competencia:
    id: str
    nome: str
    fase: int
    peso: int
    horas: float
    dica: str
    conhecida: bool

    def prioridade(self, rotulos: dict) -> str:
        return rotulos[str(self.peso)]


@dataclass
class Etapa:
    fase: int
    titulo: str
    competencias: list[Competencia]
    horas: float
    semana_inicio: int
    semana_fim: int


@dataclass
class CertificacaoRecomendada:
    nome: str
    emissor: str
    nivel: str
    nota: str
    a_partir_de: int
    agora: bool


@dataclass
class ProjetoRecomendado:
    titulo: str
    nivel: str
    descricao: str
    tecnologias: list[str]
    comecar_aqui: bool


@dataclass
class PlanoAcao:
    trilha: str
    nome: str
    prontidao: float                      # 0 a 100, ponderada pela prioridade das competências
    leitura_prontidao: str
    horas_semana: int
    conhecidas: list[Competencia]
    lacunas: list[Competencia]            # em ordem de estudo
    etapas: list[Etapa]
    horas_total: float
    semanas_total: int
    estudar_primeiro: list[Competencia]
    certificacoes: list[CertificacaoRecomendada]
    nota_certificacoes: str
    aviso_certificacoes: str
    projetos: list[ProjetoRecomendado]
    boas_praticas: list[str]
    ponto_de_partida: str
    rotulos_prioridade: dict = field(default_factory=dict)


def _leitura_prontidao(p: float) -> str:
    if p >= LIMIAR_PRONTO:
        return "Você já cobre quase tudo do nível Júnior. Falta pouco para se candidatar."
    if p >= 60:
        return "Você tem uma boa base. Fechar as lacunas essenciais deixa você competitivo para vagas Júnior."
    if p >= 30:
        return "Você já tem parte da base. Com consistência, chega ao nível Júnior nos próximos meses."
    return "Você está no começo da trilha, e tudo bem. O roadmap abaixo mostra o caminho em ordem."


def analisar_gaps(
    trilha: str,
    conhecidas: set[str] | list[str],
    horas_semana: int = 10,
    experiencia: str = "iniciando",
    trilhas: dict | None = None,
) -> PlanoAcao:
    """Cruza a trilha escolhida com o conhecimento atual e monta o plano de ação."""
    trilhas = trilhas or carregar_trilhas()
    if trilha not in trilhas["trilhas"]:
        raise ValueError(f"Trilha desconhecida: {trilha!r}")
    if not isinstance(horas_semana, (int, float)) or horas_semana <= 0:
        raise ValueError("horas_semana deve ser um número maior que zero.")

    dados = trilhas["trilhas"][trilha]
    ids_validos = {c["id"] for c in dados["competencias_junior"]}
    conhecidas = set(conhecidas)
    desconhecidas = conhecidas - ids_validos
    if desconhecidas:
        raise ValueError(f"Competências inexistentes na trilha '{trilha}': {sorted(desconhecidas)}")

    todas = [
        Competencia(c["id"], c["nome"], int(c["fase"]), c["peso"], c["horas"], c["dica"], c["id"] in conhecidas)
        for c in dados["competencias_junior"]
    ]
    total_peso = sum(c.peso for c in todas)
    prontidao = 100 * sum(c.peso for c in todas if c.conhecida) / total_peso

    # Ordem de estudo: fase (fundamentos primeiro), depois prioridade, depois a ordem do catálogo.
    ordem_catalogo = {c.id: i for i, c in enumerate(todas)}
    lacunas = sorted((c for c in todas if not c.conhecida), key=lambda c: (c.fase, -c.peso, ordem_catalogo[c.id]))

    # Roadmap por fase, com semanas acumuladas.
    etapas, acumulado = [], 0.0
    for fase, titulo in sorted(trilhas["fases"].items(), key=lambda kv: int(kv[0])):
        itens = [c for c in lacunas if c.fase == int(fase)]
        if not itens:
            continue
        horas = sum(c.horas for c in itens)
        inicio = int(acumulado // horas_semana) + 1
        fim = max(inicio, math.ceil((acumulado + horas) / horas_semana))
        etapas.append(Etapa(int(fase), titulo, itens, horas, inicio, fim))
        acumulado += horas
    semanas_total = math.ceil(acumulado / horas_semana) if acumulado else 0

    certificacoes = sorted(
        (
            CertificacaoRecomendada(c["nome"], c["emissor"], c["nivel"], c["nota"], c["a_partir_de_prontidao"], prontidao >= c["a_partir_de_prontidao"])
            for c in dados.get("certificacoes", [])
        ),
        key=lambda c: (not c.agora, c.a_partir_de),
    )

    inicio_projeto = 0 if prontidao < 50 else min(1, len(dados["projetos"]) - 1)
    projetos = [
        ProjetoRecomendado(p["titulo"], p["nivel"], p["descricao"], p["tecnologias"], i == inicio_projeto)
        for i, p in enumerate(dados["projetos"])
    ]

    return PlanoAcao(
        trilha=trilha,
        nome=dados["nome"],
        prontidao=prontidao,
        leitura_prontidao=_leitura_prontidao(prontidao),
        horas_semana=int(horas_semana),
        conhecidas=[c for c in todas if c.conhecida],
        lacunas=lacunas,
        etapas=etapas,
        horas_total=acumulado,
        semanas_total=semanas_total,
        estudar_primeiro=lacunas[:4],
        certificacoes=certificacoes,
        nota_certificacoes=dados.get("nota_certificacoes", ""),
        aviso_certificacoes=trilhas.get("aviso_certificacoes", ""),
        projetos=projetos,
        boas_praticas=trilhas.get("boas_praticas_github", []),
        ponto_de_partida=PONTO_DE_PARTIDA.get(experiencia, ""),
        rotulos_prioridade=trilhas.get("pesos_competencia", {"3": "Essencial", "2": "Importante", "1": "Desejável"}),
    )


def plano_para_markdown(plano: PlanoAcao) -> str:
    """Versão do plano em Markdown, para baixar e guardar no repositório."""
    rot = plano.rotulos_prioridade
    linhas = [
        f"# Plano de ação: {plano.nome}",
        "",
        f"**Prontidão para vagas Júnior:** {plano.prontidao:.0f}%. {plano.leitura_prontidao}",
        f"**Prazo estimado:** cerca de {plano.semanas_total} semanas, estudando {plano.horas_semana} h por semana ({plano.horas_total:.0f} h no total).",
        "",
        plano.ponto_de_partida,
        "",
    ]
    if plano.estudar_primeiro:
        linhas += ["## Estude primeiro", ""] + [f"{i}. {c.nome} ({c.prioridade(rot).lower()})" for i, c in enumerate(plano.estudar_primeiro, 1)] + [""]
    linhas += ["## Roadmap", ""]
    if not plano.etapas:
        linhas += ["Você já domina todas as competências de nível Júnior desta trilha. Foque em projetos e candidaturas.", ""]
    for e in plano.etapas:
        linhas += [f"### Fase {e.fase}: {e.titulo} (semanas {e.semana_inicio} a {e.semana_fim})", ""]
        linhas += [f"- [ ] **{c.nome}** ({c.prioridade(rot).lower()}, ~{c.horas:.0f} h). {c.dica}" for c in e.competencias] + [""]
    if plano.conhecidas:
        linhas += ["## Competências que você já domina", ""] + [f"- [x] {c.nome}" for c in plano.conhecidas] + [""]
    linhas += ["## Certificações", ""]
    if plano.nota_certificacoes:
        linhas += [f"> {plano.nota_certificacoes}", ""]
    for c in plano.certificacoes:
        momento = "faz sentido agora" if c.agora else f"para depois (prontidão a partir de {c.a_partir_de}%)"
        linhas.append(f"- **{c.nome}** ({c.emissor}, {c.nivel.lower()}): {momento}. {c.nota}")
    linhas += ["", f"_{plano.aviso_certificacoes}_", "", "## Projetos para o portfólio no GitHub", ""]
    for p in plano.projetos:
        marca = " **(comece por este)**" if p.comecar_aqui else ""
        linhas.append(f"- **{p.titulo}** ({p.nivel.lower()}){marca}: {p.descricao} Tecnologias: {', '.join(p.tecnologias)}.")
    linhas += ["", "### Boas práticas para o repositório", ""] + [f"- {b}" for b in plano.boas_praticas] + [""]
    return "\n".join(linhas)


if __name__ == "__main__":
    plano = analisar_gaps("devops", {"linux_base", "git_github"}, horas_semana=10, experiencia="iniciando")
    print(f"{plano.nome}: prontidão {plano.prontidao:.0f}%, {plano.semanas_total} semanas")
    for e in plano.etapas:
        print(f"  Fase {e.fase} ({e.titulo}) semanas {e.semana_inicio}-{e.semana_fim}: {[c.nome for c in e.competencias][:2]}...")
