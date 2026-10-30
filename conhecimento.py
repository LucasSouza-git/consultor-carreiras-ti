"""Carregamento e validação da base de conhecimento (arquivos JSON externos).

A base NÃO fica no código: perguntas, pesos, regras cruzadas e características das
trilhas vêm de `base_conhecimento/regras_carreiras.json` e `trilhas.json`.
Antes de o motor usar a base, `validar` confere se ela é consistente e devolve
todos os problemas encontrados de uma vez, em português.
"""
from __future__ import annotations

import json
from pathlib import Path

PASTA_KB = Path(__file__).parent
ARQUIVO_REGRAS = PASTA_KB / "regras_carreiras.json"
ARQUIVO_TRILHAS = PASTA_KB / "trilhas.json"

OPERADORES = {"<=", ">=", "<", ">", "==", "!=", "in"}
ESCALA_MIN, ESCALA_MAX = 1, 5


class BaseConhecimentoInvalida(ValueError):
    """A base de conhecimento tem problemas. A mensagem lista todos eles."""


def _ler_json(caminho: Path, mtime: float) -> dict:
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


# Cache simples que se renova quando o arquivo muda (útil durante a edição da base).
_cache: dict[tuple[str, float], dict] = {}


def _carregar(caminho: str | Path) -> dict:
    caminho = Path(caminho)
    chave = (str(caminho.resolve()), caminho.stat().st_mtime)
    if chave not in _cache:
        _cache[chave] = _ler_json(caminho, chave[1])
    return _cache[chave]


def carregar_regras(caminho: str | Path | None = None) -> dict:
    return _carregar(caminho or ARQUIVO_REGRAS)


def carregar_trilhas(caminho: str | Path | None = None) -> dict:
    return _carregar(caminho or ARQUIVO_TRILHAS)


def carregar_base(caminho_regras=None, caminho_trilhas=None, validar_base: bool = True) -> tuple[dict, dict]:
    regras, trilhas = carregar_regras(caminho_regras), carregar_trilhas(caminho_trilhas)
    if validar_base:
        validar(regras, trilhas)
    return regras, trilhas


# ----------------------------------------------------------------------
# Validação
# ----------------------------------------------------------------------
def validar(regras: dict, trilhas: dict) -> None:
    erros: list[str] = []
    for chave in ("parametros", "passos", "perguntas", "regras_cruzadas"):
        if chave not in regras:
            erros.append(f"regras_carreiras.json: falta a seção '{chave}'.")
    for chave in ("trilhas", "fases"):
        if chave not in trilhas:
            erros.append(f"trilhas.json: falta a seção '{chave}'.")
    if erros:
        raise BaseConhecimentoInvalida("\n".join(erros))

    ids = set(trilhas["trilhas"])
    perguntas = regras["perguntas"]

    # --- perguntas e pesos
    for qid, q in perguntas.items():
        tipo = q.get("tipo")
        if tipo not in ("likert", "escolha"):
            erros.append(f"Pergunta '{qid}': tipo deve ser 'likert' ou 'escolha'.")
            continue
        if q.get("importancia", 1) < 0:
            erros.append(f"Pergunta '{qid}': importância não pode ser negativa.")
        pesos_lista = []
        if tipo == "likert":
            pesos_lista.append(q.get("pesos"))
            if q.get("pesos") is None:
                erros.append(f"Pergunta '{qid}': falta o campo 'pesos'.")
        else:
            if not q.get("opcoes"):
                erros.append(f"Pergunta '{qid}': falta o campo 'opcoes'.")
            for oid, o in q.get("opcoes", {}).items():
                if "rotulo" not in o:
                    erros.append(f"Pergunta '{qid}', opção '{oid}': falta o 'rotulo'.")
                pesos_lista.append(o.get("pesos", {}))
        for pesos in pesos_lista:
            for t, valor in (pesos or {}).items():
                if t not in ids:
                    erros.append(f"Pergunta '{qid}': peso para trilha desconhecida '{t}'.")
                if not isinstance(valor, (int, float)) or valor < 0:
                    erros.append(f"Pergunta '{qid}': peso inválido para '{t}' (use número >= 0).")

    # --- telas do wizard: toda pergunta aparece exatamente uma vez
    vistas: list[str] = []
    for passo in regras["passos"]:
        for tela in passo.get("telas", []):
            for qid in tela.get("perguntas", []):
                if qid not in perguntas:
                    erros.append(f"Passo '{passo.get('id')}': pergunta '{qid}' não existe.")
                vistas.append(qid)
    for qid in perguntas:
        if vistas.count(qid) != 1:
            erros.append(f"Pergunta '{qid}' deve aparecer exatamente uma vez nos passos (aparece {vistas.count(qid)}).")

    # --- regras cruzadas
    vistos_ids: set[str] = set()
    for r in regras["regras_cruzadas"]:
        rid = r.get("id", "?")
        if rid in vistos_ids:
            erros.append(f"Regra cruzada '{rid}' repetida.")
        vistos_ids.add(rid)
        for cond in r.get("se", []):
            q = perguntas.get(cond.get("pergunta"))
            if q is None:
                erros.append(f"Regra '{rid}': pergunta '{cond.get('pergunta')}' não existe.")
                continue
            if cond.get("op") not in OPERADORES:
                erros.append(f"Regra '{rid}': operador '{cond.get('op')}' inválido.")
            if q["tipo"] == "likert" and cond.get("op") != "in":
                v = cond.get("valor")
                if not isinstance(v, int) or not ESCALA_MIN <= v <= ESCALA_MAX:
                    erros.append(f"Regra '{rid}': valor deve ser inteiro de {ESCALA_MIN} a {ESCALA_MAX}.")
            if q["tipo"] == "escolha":
                alvo = cond.get("valor") if cond.get("op") == "in" else [cond.get("valor")]
                for v in alvo or []:
                    if v not in q["opcoes"]:
                        erros.append(f"Regra '{rid}': opção '{v}' não existe na pergunta '{cond['pergunta']}'.")
        for t in r.get("efeito", {}):
            if t not in ids:
                erros.append(f"Regra '{rid}': efeito em trilha desconhecida '{t}'.")

    # --- cada trilha precisa ser alcançável (máximo > 0)
    for t in ids:
        maximo = 0.0
        for q in perguntas.values():
            imp = q.get("importancia", 1)
            if q["tipo"] == "likert":
                maximo += imp * q["pesos"].get(t, 0)
            else:
                maximo += imp * max([o.get("pesos", {}).get(t, 0) for o in q["opcoes"].values()] or [0])
        if maximo <= 0:
            erros.append(f"Trilha '{t}': nenhuma pergunta pontua para ela.")

    # --- ordem dos eixos do radar (opcional, mas se existir deve listar todas as trilhas)
    ordem = trilhas.get("ordem_radar")
    if ordem is not None and sorted(ordem) != sorted(ids):
        erros.append("trilhas.json: 'ordem_radar' deve listar cada trilha exatamente uma vez.")

    # --- conteúdo das trilhas
    fases = set(trilhas["fases"])
    for tid, t in trilhas["trilhas"].items():
        for campo in ("nome", "curto", "descricao"):
            if not t.get(campo):
                erros.append(f"Trilha '{tid}': falta '{campo}'.")
        comps = t.get("competencias_junior", [])
        if len(comps) < 5:
            erros.append(f"Trilha '{tid}': defina pelo menos 5 competências de nível Júnior.")
        comp_ids = [c.get("id") for c in comps]
        for c in comps:
            if comp_ids.count(c.get("id")) > 1:
                erros.append(f"Trilha '{tid}': competência '{c.get('id')}' repetida.")
            if str(c.get("fase")) not in fases:
                erros.append(f"Trilha '{tid}', competência '{c.get('id')}': fase inválida.")
            if c.get("peso") not in (1, 2, 3):
                erros.append(f"Trilha '{tid}', competência '{c.get('id')}': peso deve ser 1, 2 ou 3.")
            if not isinstance(c.get("horas"), (int, float)) or c["horas"] <= 0:
                erros.append(f"Trilha '{tid}', competência '{c.get('id')}': horas deve ser > 0.")
        if not t.get("projetos"):
            erros.append(f"Trilha '{tid}': defina pelo menos um projeto de portfólio.")
        for cert in t.get("certificacoes", []):
            if not 0 <= cert.get("a_partir_de_prontidao", -1) <= 100:
                erros.append(f"Trilha '{tid}', certificação '{cert.get('nome')}': 'a_partir_de_prontidao' deve ficar entre 0 e 100.")

    if erros:
        raise BaseConhecimentoInvalida("Base de conhecimento inválida:\n- " + "\n- ".join(erros))
