import requests
import zipfile
import csv
import io
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

from utils import RAW_DIR, PROCESSED_DIR, BASE_URL, ESTACAO_PADRAO, ANOS_PADRAO


def baixar_zip(ano: int, dest_dir: Path = RAW_DIR) -> Path:
    url = f"{BASE_URL}/{ano}.zip"
    dest_dir.mkdir(parents = True, exist_ok = True)
    caminho = dest_dir / f"{ano}.zip"

    if caminho.exists():
        print(f"[{ano}] ZIP ja existe, pulando download.")
        return caminho

    print(f"[{ano}] Baixando {url} ...")
    resp = requests.get(url, timeout = 300)
    resp.raise_for_status()
    with open(caminho, "wb") as f:
        for chunk in resp.iter_content(chunk_size = 8192):
            f.write(chunk)
    print(f"[{ano}] Salvo em {caminho}")
    return caminho


def _parse_metadata(linhas: List[str]) -> dict:
    meta = {}
    for linha in linhas[:8]:
        if ";" in linha:
            chave, valor = linha.strip().split(";", 1)
            chave = re.sub(r"[():]", "", chave.strip().lower()).strip().replace(" ", "_")
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


def extrair_estacao(caminho_zip: Path, codigo_estacao: str) -> Optional[pd.DataFrame]:
    with zipfile.ZipFile(caminho_zip, "r") as z:
        arquivos = [f for f in z.infolist() if not f.is_dir()]
        candidatos = [a for a in arquivos if f"_{codigo_estacao}_" in a.filename]
        if not candidatos:
            candidatos = [a for a in arquivos if codigo_estacao in a.filename]
        if not candidatos:
            print(f"  Nenhum candidato para {codigo_estacao} em {caminho_zip.name}. Abortando busca.")
            return None

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
                leitor = csv.reader(buf, delimiter = ";")
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

                df = pd.DataFrame(linhas_dados, columns = colunas_finais)
                for k in ("regiao", "uf", "estacao", "codigo_wmo", "latitude", "longitude", "altitude"):
                    if k in meta:
                        df[k] = meta[k]
                return df

    print(f"  Estacao {codigo_estacao} nao encontrada nos candidatos de {caminho_zip.name}")
    return None


def limpar_dados(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    total_inicial = len(df)
    diag = {}

    cols_numericas = ["velocidade_vento", "direcao_vento", "rajada_vento"]

    for col in cols_numericas:
        if col in df.columns:
            antes = df[col].copy()
            diag[f"{col}_flag_-9999"] = (antes == "-9999").sum()
            diag[f"{col}_flag_vazio"] = (antes == "").sum()
            diag[f"{col}_flag_zero"] = (
                antes.str.replace(",", ".", regex=False)
                .pipe(pd.to_numeric, errors="coerce")
                .eq(0.0)
                .sum()
            )

            df[col] = (
                antes.str.replace(",", ".", regex=False)
                .replace("-9999", np.nan)
                .replace("", np.nan)
            )
            df[col] = pd.to_numeric(df[col], errors="coerce")

            diag[f"{col}_nan_pos_conversao"] = df[col].isna().sum()

    data_str = df["data"].str.replace("/", "-", regex=False)
    hora_str = df["hora"].str.extract(r"(\d{2}:\d{2}|\d{4})", expand=False)
    hora_str = hora_str.str.replace(r"(\d{2})(\d{2})", r"\1:\2", regex=True)
    df["data_hora"] = pd.to_datetime(
        data_str + " " + hora_str, format="%Y-%m-%d %H:%M", errors="coerce"
    )
    diag["data_hora_invalida"] = df["data_hora"].isna().sum()

    cols_saida = ["data_hora"] + [c for c in cols_numericas if c in df.columns]
    saida = df[cols_saida].copy()

    diag["veloc_vento_nan_antes_drop"] = saida["velocidade_vento"].isna().sum()
    saida = saida.dropna(subset=["velocidade_vento"])
    saida = saida.sort_values("data_hora").reset_index(drop=True)

    diag["total_inicial"] = total_inicial
    diag["total_final"] = len(saida)
    diag["linhas_descartadas"] = total_inicial - len(saida)

    diag["veloc_vento_zeros"] = (saida["velocidade_vento"] == 0.0).sum()
    diag["veloc_vento_positivos"] = (saida["velocidade_vento"] > 0.0).sum()
    diag["veloc_vento_negativos"] = (saida["velocidade_vento"] < 0.0).sum()
    if "direcao_vento" in saida.columns:
        diag["direcao_vento_nan"] = saida["direcao_vento"].isna().sum()
    if "rajada_vento" in saida.columns:
        diag["rajada_vento_nan"] = saida["rajada_vento"].isna().sum()

    if len(saida) > 1:
        diffs = saida["data_hora"].diff().dropna()
        gaps = diffs[diffs > pd.Timedelta(hours=1)]
        diag["gaps_temporais_qtde"] = len(gaps)
        if not gaps.empty:
            diag["maior_gap"] = gaps.max()
            diag["primeiros_gaps"] = []
            for idx, gap in list(gaps.head(10).items()):
                if idx > 0:
                    diag["primeiros_gaps"].append(
                        f"  {saida.loc[idx - 1, 'data_hora']} -> {saida.loc[idx, 'data_hora']}  "
                        f"({gap})"
                    )

    imprimir_diagnostico(diag)
    return saida


def imprimir_diagnostico(diag: dict):
    sep = "-" * 52
    p = print

    p(f"\n{sep}")
    p("  DIAGNOSTICO DA LIMPEZA DE DADOS")
    p(sep)

    total_ini = diag.get("total_inicial", 0)
    total_fim = diag.get("total_final", 0)
    desc = diag.get("linhas_descartadas", total_ini - total_fim)
    p(f"  Registros recebidos .............. {total_ini:>6}")
    p(f"  Registros apos limpeza ........... {total_fim:>6}")
    p(f"  Linhas descartadas ............... {desc:>6}")

    p(f"\n  --- Flags por coluna (antes da conversao) ---")
    for base in ["velocidade_vento", "direcao_vento", "rajada_vento"]:
        fl_9999 = diag.get(f"{base}_flag_-9999", None)
        fl_vaz = diag.get(f"{base}_flag_vazio", None)
        fl_zero = diag.get(f"{base}_flag_zero", None)
        fl_nan = diag.get(f"{base}_nan_pos_conversao", None)
        if any(v is not None for v in [fl_9999, fl_vaz, fl_zero]):
            p(f"  {base}:")
            if fl_9999 is not None:
                p(f"    -9999 (cod. INMET p/ ausente) ... {fl_9999:>5}")
            if fl_vaz is not None:
                p(f"    vazio .......................... {fl_vaz:>5}")
            if fl_zero is not None:
                p(f"    zero (mantido como 0.0) ........ {fl_zero:>5}")
            if fl_nan is not None:
                p(f"    NaN apos conversao ............. {fl_nan:>5}")

    dh_inv = diag.get("data_hora_invalida", 0)
    if dh_inv:
        p(f"\n  data_hora invalida ............... {dh_inv:>6}")
    p(f"\n  --- Valores finais ---")
    p(f"  velocidade_vento = 0.0 ........... {diag.get('veloc_vento_zeros', 0):>6}")
    p(f"  velocidade_vento > 0.0 ........... {diag.get('veloc_vento_positivos', 0):>6}")
    vel_neg = diag.get("veloc_vento_negativos", 0)
    if vel_neg:
        p(f"  (!) velocidade < 0 (suspeito) .... {vel_neg:>6}")
    dir_nan = diag.get("direcao_vento_nan", 0)
    raj_nan = diag.get("rajada_vento_nan", 0)
    if dir_nan:
        p(f"  (!) direcao_vento NaN ............. {dir_nan:>6}"
          "  (mantidos; descartar na rosa dos ventos)")
    if raj_nan:
        p(f"       rajada_vento NaN ............. {raj_nan:>6}"
          "  (mantidos; sem impacto nos calculos)")
    gaps = diag.get("gaps_temporais_qtde", 0)
    p(f"\n  --- Gaps temporais (>1h entre registros consecutivos) ---")
    p(f"  Total de gaps encontrados ........ {gaps:>6}")
    if gaps:
        p(f"  Maior gap ........................ {diag.get('maior_gap', 'N/A')}")
        p(f"  Primeiros gaps (ate 10):")
        for detalhe in diag.get("primeiros_gaps", []):
            p(detalhe)
    p(f"  ---")
    p(f"  RESUMO: {desc} linhas descartadas ({desc/total_ini*100:.1f}% do total)."
      if total_ini else "  RESUMO: 0 registros.")
    p(f"  Zeros preservados: {diag.get('veloc_vento_zeros', 0)} registros com"
      f" velocidade = 0.0 (calmaria legitima).")
    p(sep + "\n")


def filtrar_ultimos_meses(df: pd.DataFrame, meses: int) -> pd.DataFrame:
    agora = datetime.now()
    data_limite = agora - relativedelta(months = meses)
    df_filtrado = df[df["data_hora"] >= data_limite].copy()
    print(f"  Filtrado: {len(df_filtrado)} registros nos ultimos {meses} meses")
    return df_filtrado


def main(
    estacao: str = ESTACAO_PADRAO,
    anos: Optional[List[int]] = None,
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

    df_completo = pd.concat(dfs_brutos, ignore_index = True)
    df_completo = limpar_dados(df_completo)
    df_filtrado = filtrar_ultimos_meses(df_completo, meses)

    RAW_DIR.mkdir(parents = True, exist_ok = True)
    PROCESSED_DIR.mkdir(parents = True, exist_ok = True)

    if not df_filtrado.empty and df_filtrado["data_hora"].notna().any():
        periodo = f"{anos[0]}_{anos[-1]}"
        processed_path = PROCESSED_DIR / f"{estacao}_{periodo}_limpo.csv"
        df_filtrado.to_csv(processed_path, index = False)
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
        df_completo.to_csv(PROCESSED_DIR / f"{estacao}_debug_completo.csv", index=False)
        print(f"  Debug salvo: {PROCESSED_DIR / f'{estacao}_debug_completo.csv'} ({len(df_completo)} registros)")


if __name__ == "__main__":
    main()
