"""Perguntas da entrevista.

Cada pergunta alimenta um campo do fato `Perfil` no motor de inferência.
A interface (Streamlit) deve apenas percorrer PERGUNTAS e montar um dict
{campo: codigo_da_opcao}.
"""

PERGUNTAS = [
    {
        "campo": "matematica",
        "titulo": "Qual é a sua afinidade com matemática e estatística?",
        "opcoes": {
            "baixa": "Baixa — prefiro evitar cálculos e estatística",
            "media": "Média — me viro bem quando preciso",
            "alta": "Alta — gosto de probabilidade, álgebra e estatística",
        },
    },
    {
        "campo": "atuacao",
        "titulo": "O que você gostaria de fazer no seu dia a dia de trabalho?",
        "opcoes": {
            "algoritmos": "Escrever algoritmos e lógica de programação (regras de negócio)",
            "layouts": "Criar layouts e interfaces visuais",
            "apps_moveis": "Criar aplicativos para celular",
            "analise_dados": "Analisar dados brutos e descobrir padrões",
            "pipelines": "Construir fluxos que coletam, transformam e organizam dados",
            "seguranca": "Garantir segurança e procurar vulnerabilidades",
            "automacao": "Automatizar build, deploy e monitoramento",
            "servidores": "Lidar com servidores e configuração de ambientes",
            "arquitetura": "Planejar e desenhar infraestruturas escaláveis / migrações",
            "testes": "Testar software e caçar bugs",
            "produto": "Definir o que será construído, priorizar e alinhar pessoas",
        },
    },
    {
        "campo": "ferramenta",
        "titulo": "Qual linguagem/ferramenta você tem maior afinidade hoje?",
        "opcoes": {
            "python": "Python",
            "javascript": "JavaScript / TypeScript",
            "sql": "SQL / Bancos de dados",
            "linux_redes": "Linux / Redes",
            "mobile": "Kotlin / Swift / Dart (Flutter) / React Native",
            "cloud_containers": "Docker / Kubernetes / AWS-Azure-GCP",
            "nenhuma": "Nenhuma / Iniciante",
        },
    },
    {
        "campo": "entrega",
        "titulo": "Que tipo de valor você mais gostaria de entregar?",
        "opcoes": {
            "produto_usuario": "O produto final que o usuário utiliza",
            "infraestrutura": "A infraestrutura que sustenta o sistema",
            "protecao": "A segurança contra invasões",
            "insights": "Previsões e decisões baseadas em modelos",
            "dados_prontos": "Dados limpos, organizados e disponíveis para todos",
            "qualidade": "Software confiável e sem falhas",
            "fluxo_entrega": "Entregas rápidas, frequentes e automatizadas",
            "estrategia": "O produto certo, no momento certo, para o negócio",
        },
    },
    {
        "campo": "plataforma",
        "titulo": "Em qual ambiente você prefere atuar?",
        "opcoes": {
            "web": "Web",
            "mobile": "Dispositivos móveis",
            "dados": "Dados e analytics",
            "infra": "Infraestrutura / nuvem",
            "indiferente": "Tanto faz",
        },
    },
    {
        "campo": "negocio",
        "titulo": "Quanto você gosta de conversar com clientes, negócio e times?",
        "opcoes": {
            "baixa": "Pouco — prefiro trabalho técnico focado",
            "media": "Moderadamente",
            "alta": "Muito — gosto de alinhar pessoas e decisões",
        },
    },
    {
        "campo": "objetivo",
        "titulo": "Qual é o seu principal objetivo profissional?",
        "opcoes": {
            "construir": "Construir sistemas e funcionalidades",
            "inovar": "Pesquisar e inovar com dados / IA",
            "sustentar": "Proteger, manter e garantir a estabilidade dos sistemas",
            "liderar": "Liderar produtos e decisões estratégicas",
        },
    },
]

CAMPOS = [p["campo"] for p in PERGUNTAS]
OPCOES_VALIDAS = {p["campo"]: set(p["opcoes"]) for p in PERGUNTAS}
