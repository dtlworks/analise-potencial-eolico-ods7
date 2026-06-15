import requests
import zipfile
import csv
import io
import re
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

RAW_DIR = Path("dados/raw")
PROCESSED_DIR = Path("dados/processed")
BASE_URL = "https://portal.inmet.gov.br/uploads/dadoshistoricos"
ESTACAO_PADRAO = "A303"
ANOS_PADRAO = [2025, 2026]


def baixar_zip(ano: int, dest_dir: Path = RAW_DIR) -> Path:
    url = f"{BASE_URL}/{ano}.zip"
    dest_dir.mkdir(parents=True, exist_ok=True)
    caminho = dest_dir / f"{ano}.zip"

    if caminho.exists():
        print(f"[{ano}] ZIP ja existe, pulando download.")
        return caminho

    print(f"[{ano}] Baixando {url} ...")
    resp = requests.get(url, timeout=300)
    resp.raise_for_status()
    with open(caminho, "wb") as f:
        f.write(resp.content)
    print(f"[{ano}] Salvo em {caminho}")
    return caminho


def _parse_metadata(linhas: list[str]) -> dict:
    meta = {}
    for linha in linhas[:8]:
        if ";" in linha:
            chave, valor = linha.strip().split(";", 1)
            chave = chave.strip().lower().replace(" ", "_").replace("(", "").replace(")", "").rstrip(":")
            meta[chave] = valor.strip()
    return meta


def _renomear_coluna(nome: str) -> str:
    nome_lower = nome.lower()
    padroes = [
        (r"^data$", "data"),
        (r"^hora", "hora"),
        (r"vento.*velocidade", "velocidade_vento"),
        (r"vento.*rajada", "rajada_vento"),
        (r"vento.*direc", "direcao_vento"),
        (r"vento.*direç", "direcao_vento"),
    ]
    for regex, substituicao in padroes:
        if re.search(regex, nome_lower):
            return substituicao
    return nome_lower


def extrair_estacao(caminho_zip: Path, codigo_estacao: str) -> pd.DataFrame | None:
    with zipfile.ZipFile(caminho_zip, "r") as z:
        arquivos = [f for f in z.infolist() if not f.is_dir()]

        candidatos = [a for a in arquivos if f"_{codigo_estacao}_" in a.filename]
        if not candidatos:
            candidatos = [a for a in arquivos if codigo_estacao in a.filename]
        if not candidatos:
            candidatos = arquivos

        for arq in candidatos:
            conteudo = z.read(arq.filename).decode("latin-1")
            linhas = conteudo.strip().split("\n")
            if len(linhas) < 9:
                continue
            meta = _parse_metadata(linhas)
            codigo_wmo = meta.get("codigo_wmo", "").strip()
            if codigo_wmo == codigo_estacao:
                print(f"  Estacao {codigo_estacao} encontrada em {arq.filename}")
                dados_raw = "\n".join(linhas[8:])
                buf = io.StringIO(dados_raw)
                leitor = csv.reader(buf, delimiter=";")
                colunas_originais = next(leitor)
                colunas_renomeadas = [_renomear_coluna(c) for c in colunas_originais]

                colunas_finais = []
                indices_manter = []
                for i, (orig, renomeada) in enumerate(zip(colunas_originais, colunas_renomeadas)):
                    if renomeada in ("data", "hora", "velocidade_vento", "direcao_vento", "rajada_vento"):
                        indices_manter.append(i)
                        colunas_finais.append(renomeada)

                linhas_dados = []
                for row in leitor:
                    linha_filtrada = [row[i] for i in indices_manter if i < len(row)]
                    linhas_dados.append(linha_filtrada)

                df = pd.DataFrame(linhas_dados, columns=colunas_finais)
                for k in ("regiao", "uf", "estacao", "codigo_wmo", "latitude", "longitude", "altitude"):
                    if k in meta:
                        df[k] = meta[k]
                return df

    print(f"  Estacao {codigo_estacao} nao encontrada em {caminho_zip.name}")
    return None


def limpar_dados(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    cols_numericas = ["velocidade_vento", "direcao_vento", "rajada_vento"]
    for col in cols_numericas:
        if col in df.columns:
            df[col] = (
                df[col]
                .str.replace(",", ".", regex=False)
                .replace("-9999", np.nan)
                .replace("", np.nan)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

    data_str = df["data"].str.replace("/", "-", regex=False)
    hora_str = df["hora"].str.extract(r"(\d{2}:\d{2}|\d{4})", expand=False)
    hora_str = hora_str.str.replace(r"(\d{2})(\d{2})", r"\1:\2", regex=True)
    df["data_hora"] = pd.to_datetime(
        data_str + " " + hora_str, format="%Y-%m-%d %H:%M", errors="coerce"
    )

    cols_saida = ["data_hora"] + [c for c in cols_numericas if c in df.columns]
    saida = df[cols_saida].copy()
    saida = saida.dropna(subset=["velocidade_vento"])
    saida = saida.sort_values("data_hora").reset_index(drop=True)
    return saida


def filtrar_ultimos_meses(df: pd.DataFrame, meses: int) -> pd.DataFrame:
    agora = datetime.now()
    data_limite = agora - timedelta(days=30 * meses)
    df_filtrado = df[df["data_hora"] >= data_limite].copy()
    print(f"  Filtrado: {len(df_filtrado)} registros nos ultimos {meses} meses")
    return df_filtrado


def main(
    estacao: str = ESTACAO_PADRAO,
    anos: list[int] | None = None,
    meses: int = 12,
):
    if anos is None:
        anos = ANOS_PADRAO

    print(f"=== Download INMET - Estacao {estacao} ===")
    dfs_brutos = []
    for ano in anos:
        zip_path = baixar_zip(ano)
        df_estacao = extrair_estacao(zip_path, estacao)
        if df_estacao is not None and not df_estacao.empty:
            dfs_brutos.append(df_estacao)

    if not dfs_brutos:
        print("Nenhum dado encontrado para a estacao especificada.")
        return

    df_completo = pd.concat(dfs_brutos, ignore_index=True)
    df_completo = limpar_dados(df_completo)
    df_filtrado = filtrar_ultimos_meses(df_completo, meses)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if not df_filtrado.empty and df_filtrado["data_hora"].notna().any():
        for ano in anos:
            df_ano = df_completo[df_completo["data_hora"].dt.year == ano]
            if not df_ano.empty:
                raw_path = RAW_DIR / f"{estacao}_{ano}.csv"
                df_ano.to_csv(raw_path, index=False)
                print(f"  Bruto salvo: {raw_path} ({len(df_ano)} registros)")

        periodo = f"{anos[0]}_{anos[-1]}"
        processed_path = PROCESSED_DIR / f"{estacao}_{periodo}_limpo.csv"
        df_filtrado.to_csv(processed_path, index=False)
        print(f"  Limpo salvo: {processed_path} ({len(df_filtrado)} registros)")

        print(f"\nResumo:")
        print(f"  Estacao:     {estacao} (Maceio-AL)")
        print(f"  Periodo:     {df_filtrado['data_hora'].min()} a {df_filtrado['data_hora'].max()}")
        print(f"  Registros:   {len(df_filtrado)}")
        print(f"  Velocidade media: {df_filtrado['velocidade_vento'].mean():.2f} m/s")
        if "rajada_vento" in df_filtrado.columns:
            print(f"  Rajada maxima:   {df_filtrado['rajada_vento'].max():.2f} m/s")
    else:
        print("  Nenhum registro valido apos limpeza.")
        # save all data anyway so user can inspect
        df_completo.to_csv(PROCESSED_DIR / f"{estacao}_debug_completo.csv", index=False)
        print(f"  Debug salvo: {PROCESSED_DIR / f'{estacao}_debug_completo.csv'} ({len(df_completo)} registros)")


if __name__ == "__main__":
    main()
