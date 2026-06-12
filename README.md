# Estimativa da Densidade de Potência Eólica a partir de Dados do INMET

Este projeto é desenvolvido com a finalidade de compor a nota da disciplina de Cálculo Diferencial e Integral 2 no curso de Engenharia Civil da Universidade Federal de Alagoas; com inteção de protagozinar uma atividade extracurricular.

## Objetivo

Utilizar dados públicos de velocidade e direção do vento fornecidos pelo **INMET** (Instituto Nacional de Meteorologia) para estimar o potencial eólico de uma região, aplicando conceitos de cálculo integral (soma de Riemann, regra do trapézio, regra de Simpson) e séries de Taylor.

## Fluxo do Projeto

```
INMET (BDMEP)
    │
    ▼
[src/download_inmet.py] ──── Baixa, limpa e organiza dados horários
    │
    ▼
dados/raw/ ───────────────── Dados brutos (originais)
    │
    ▼
dados/processed/ ────────── Dados prontos para análise
    │
    ├──► [src/calculo_densidade.py] ──► Densidade de potência (P/A)
    │         ├──► Soma de Riemann
    │         ├──► Regra do Trapézio
    │         └──► Regra de Simpson
    │
    ├──► [src/taylor_expansao.py] ───► Expansão em Série de Taylor
    │
    ├──► [src/potencial_total.py] ───► P = (P/A) × Área do rotor
    │
    ├──► [src/rosa_dos_ventos.py] ───► Gráfico polar da direção do vento
    │
    └──► [src/graficos.py] ─────────► Visualizações finais
```

## Estrutura do Repositório

```
├── dados/
│   ├── raw/              # CSVs originais do INMET
│   └── processed/        # Dados limpos e organizados
├── src/
│   ├── download_inmet.py     # Download, limpeza e organização dos dados
│   ├── calculo_densidade.py  # ⟨v³⟩ e P/A = ½ρ⟨v³⟩ (Riemann, Trapézio, Simpson)
│   ├── taylor_expansao.py    # Expansão de v³ em série de Taylor
│   ├── potencial_total.py    # A = πR², P = (P/A) · A
│   ├── rosa_dos_ventos.py    # Coordenadas polares (frequência × direção)
│   ├── graficos.py           # Visualizações auxiliares
│   └── utils.py              # Constantes e helpers
├── test/
│   ├── test_densidade.py     # Testes para cálculo de densidade
│   └── test_taylor.py        # Testes para expansão de Taylor
├── docs/
│   └── relatorio_final.pdf   # Relatório do projeto
└── README.md
```

## Metodologia

1. **Coleta dos dados** — download de dados horários de velocidade e direção do vento de estações do INMET via BDMEP.
2. **Integração numérica** — cálculo de ∫₀^∞ v³ f(v) dv por três métodos: soma de Riemann, regra do trapézio e regra de Simpson, usando a distribuição de Weibull como função densidade de probabilidade.
3. **Série de Taylor** — expansão de v³ em torno da velocidade média e integração termo a termo, comparando o resultado com a integração numérica.
4. **Potência total** — P = (P/A) × A_rotor, utilizando a área varrida por uma turbina comercial (ex.: Vestas V120-2.2 MW).
5. **Rosa dos Ventos** — gráfico polar que mostra a frequência e intensidade do vento por direção.

## Tecnologias

- Python 3
- NumPy, SciPy, Matplotlib

## ODS 7

O projeto está alinhado ao **Objetivo de Desenvolvimento Sustentável 7 (Energia Limpa e Acessível)**: com dados abertos, qualquer pessoa pode identificar locais viáveis para instalação de parques eólicos.

## Licença

Este projeto está sob a licença MIT.
