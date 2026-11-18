#!/usr/bin/env python3
"""Verifica e anota uma tese em PDF a partir de um registro de achados.

Uso:
  python3 anotar_e_verificar.py tese.pdf registro.json saida.pdf [--offset N] [--so-verificar]

registro.json = lista de objetos com:
  id          "M-001"
  pdf         numero da pagina no PDF (1 = primeira pagina)
  snippet     trecho LITERAL, de UMA linha do PDF, a destacar; aparece 1 vez na pagina
  excerto     trecho literal maior (1 a 2 frases) que contem o snippet; "[...]" marca cortes
  cor         verde | roxo | vermelho | laranja | amarelo | azul
  pri         "Mérito" | "Chave" | "P1" | "P2" | "P3"
  tipo        "ponto forte" | "fragilidade" | ...
  comentario  diagnostico + acao

Regras: se algum snippet ou excerto nao for achado na pagina, o script FALHA (exit 1)
e nao grava o PDF. --offset = (numero impresso) - (numero do PDF); padrao 0.
--so-verificar roda a checagem sem gravar PDF. Requer: pip install pdfplumber pypdf
"""
import argparse, json, re, sys
import pdfplumber
from pypdf import PdfReader, PdfWriter
from pypdf.annotations import Highlight
from pypdf.generic import ArrayObject, FloatObject, NameObject, TextStringObject

CORES = {'verde': '90EE90', 'amarelo': 'FFEB3B', 'vermelho': 'FF8A80',
         'laranja': 'FFB74D', 'azul': '81D4FA', 'roxo': 'CE93D8'}
CAMPOS = ('id', 'pdf', 'snippet', 'excerto', 'cor', 'pri')


def norm(s):
    s = s.replace('­', '').replace('-\n', '').replace('\n', ' ')
    s = s.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    s = s.replace('–', '-').replace('—', '-')
    return re.sub(r'\s+', ' ', s).strip()


def alnum(s):
    return re.sub(r'[^0-9a-zà-ú]', '', norm(s).lower())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('pdf')
    ap.add_argument('registro')
    ap.add_argument('saida', nargs='?')
    ap.add_argument('--offset', type=int, default=0)
    ap.add_argument('--so-verificar', action='store_true')
    a = ap.parse_args()
    if not a.so_verificar and not a.saida:
        ap.error('informe o PDF de saida ou use --so-verificar')

    reg = json.load(open(a.registro, encoding='utf8'))
    erros, ok, ids = [], [], set()
    sem_texto = set()
    reader = PdfReader(a.pdf)
    w = PdfWriter()
    w.append(reader)
    with pdfplumber.open(a.pdf) as pl:
        n = len(pl.pages)
        for r in reg:
            rid = r.get('id', '?')
            faltam = [c for c in CAMPOS if c not in r]
            if faltam:
                erros.append((rid, 'campos ausentes', faltam)); continue
            if rid in ids:
                erros.append((rid, 'id duplicado')); continue
            ids.add(rid)
            if r['cor'] not in CORES:
                erros.append((rid, 'cor invalida', r['cor'])); continue
            if not 1 <= r['pdf'] <= n:
                erros.append((rid, f'pagina {r["pdf"]} fora do PDF (1 a {n})')); continue
            page = pl.pages[r['pdf'] - 1]
            bruto = page.extract_text() or ''
            if not bruto.strip():
                sem_texto.add(r['pdf'])
                erros.append((rid, 'pagina sem camada de texto (digitalizacao?)')); continue
            txt = alnum(bruto)
            partes = [p for p in re.split(r'\[\.\.\.\]|\.\.\.|…', r['excerto']) if len(p.strip()) > 2]
            for p in partes:
                if alnum(p) not in txt:
                    erros.append((rid, 'excerto nao esta na pagina', p[:60]))
            if alnum(r['snippet']) not in alnum(r['excerto']):
                erros.append((rid, 'snippet fora do excerto'))
            hits = page.search(r['snippet'], regex=False, case=True)
            if len(hits) != 1:
                erros.append((rid, f'snippet achado {len(hits)}x na pagina (precisa ser 1)', r['snippet'][:50])); continue
            m = hits[0]
            H = float(page.height)
            x0, x1, t, b = m['x0'], m['x1'], m['top'], m['bottom']
            quad = ArrayObject([FloatObject(v) for v in (x0, H - t, x1, H - t, x0, H - b, x1, H - b)])
            ann = Highlight(rect=(x0, H - b, x1, H - t), quad_points=quad, highlight_color=CORES[r['cor']])
            ann[NameObject('/Contents')] = TextStringObject(
                f"[{rid} | {r['pri']} | {r.get('tipo', '')} | p. {r['pdf'] + a.offset} (PDF {r['pdf']})] {r.get('comentario', '')}")
            ann[NameObject('/T')] = TextStringObject('Parecer')
            w.add_annotation(page_number=r['pdf'] - 1, annotation=ann)
            ok.append(rid)
    print(f"{len(ok)} de {len(reg)} marcas verificadas")
    for e in erros:
        print('ERRO', e)
    if erros:
        sys.exit(1)
    if a.so_verificar:
        print('verificacao concluida; nada gravado'); return
    w.write(a.saida)
    print('gravado', a.saida)


if __name__ == '__main__':
    main()
