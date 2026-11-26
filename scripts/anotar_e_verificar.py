#!/usr/bin/env python3
"""Verifica e anota uma tese em PDF a partir de um registro de achados.

Uso:
  python3 anotar_e_verificar.py tese.pdf registro.json saida.pdf [--offset N] [--so-verificar] [--legenda]

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
--so-verificar roda a checagem sem gravar PDF. --legenda acrescenta, AO FINAL do PDF
(sem alterar a paginacao citada), uma pagina com o significado de cada cor (protocolo, secao 18,
regra 9). Requer: pip install pdfplumber pypdf (e reportlab para --legenda)
"""
import argparse, json, re, sys
import pdfplumber
from pypdf import PdfReader, PdfWriter
from pypdf.annotations import Highlight
from pypdf.generic import ArrayObject, FloatObject, NameObject, TextStringObject

CORES = {'verde': '90EE90', 'amarelo': 'FFEB3B', 'vermelho': 'FF8A80',
         'laranja': 'FFB74D', 'azul': '81D4FA', 'roxo': 'CE93D8'}
CAMPOS = ('id', 'pdf', 'snippet', 'excerto', 'cor', 'pri')
LEGENDA = [  # protocolo, secao 18
    ('verde', 'Verde', 'Mérito: argumento bem demonstrado, fonte bem tratada, contribuição original', 'Ponto forte'),
    ('roxo', 'Roxo', 'Formulação-chave do autor usada na reconstrução (pergunta, hipótese, tese)', 'Chave'),
    ('vermelho', 'Vermelho', 'Problema de mérito: contradição, extrapolação, falha de método', 'P1'),
    ('laranja', 'Laranja', 'Consistência analítica: conceito ambíguo, repetição, articulação', 'P2'),
    ('amarelo', 'Amarelo', 'Afirmação sem sustentação suficiente, ou inferência frágil', 'P2'),
    ('azul', 'Azul', 'Revisão documental e editorial: referência, data, remissão', 'P3'),
]


def pagina_legenda(contagem):
    """Gera, em memoria, a pagina de legenda das cores (com a contagem de marcas por cor)."""
    import io, glob
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.colors import HexColor
    from reportlab.lib.utils import simpleSplit
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    reg, neg = 'Helvetica', 'Helvetica-Bold'
    fr = glob.glob('/usr/share/fonts/**/DejaVuSans.ttf', recursive=True)
    fb = glob.glob('/usr/share/fonts/**/DejaVuSans-Bold.ttf', recursive=True)
    if fr and fb:  # fonte com acentos garantidos
        pdfmetrics.registerFont(TTFont('DV', fr[0])); pdfmetrics.registerFont(TTFont('DVB', fb[0]))
        reg, neg = 'DV', 'DVB'
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4); W, H = A4; y = H - 80
    c.setFont(neg, 14); c.drawString(60, y, 'Legenda das marcas (protocolo Mariana, seção 18)'); y -= 22
    c.setFont(reg, 9.5)
    for t in ('Página acrescentada ao final da cópia anotada; não altera a paginação citada no parecer.',
              'Cada destaque traz um comentário com código (M-xxx), prioridade, diagnóstico e ação sugerida.'):
        c.drawString(60, y, t); y -= 14
    y -= 16
    for chave, nome, sig, pri in LEGENDA:
        linhas = simpleSplit(sig, reg, 10, 290); h = max(28, 14 * len(linhas) + 10)
        c.setFillColor(HexColor('#' + CORES[chave])); c.rect(60, y - h + 8, 90, h - 4, stroke=0, fill=1)
        c.setFillColor(HexColor('#000000')); c.setFont(neg, 10.5); c.drawString(66, y - 10, nome)
        c.setFont(reg, 10)
        for i, l in enumerate(linhas):
            c.drawString(160, y - 10 - 14 * i, l)
        c.setFont(neg, 10); c.drawString(460, y - 10, pri)
        c.setFont(reg, 10); c.drawRightString(535, y - 10, str(contagem.get(chave, 0)))
        y -= h + 4
    y -= 12; c.setFont(reg, 9.5)
    for t in simpleSplit('Ordem de leitura: vermelho (condições indispensáveis), laranja e amarelo '
                         '(recomendações desejáveis), azul (correções antes do depósito). Verde e roxo '
                         'indicam o que preservar. Última coluna: número de marcas por cor.', reg, 9.5, 475):
        c.drawString(60, y, t); y -= 13
    c.save(); buf.seek(0)
    return PdfReader(buf)


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
    ap.add_argument('--legenda', action='store_true',
                    help='acrescenta ao final do PDF uma pagina com o significado das cores')
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
    if a.legenda:
        try:
            from collections import Counter
            w.append(pagina_legenda(Counter(r['cor'] for r in reg)))
            print('pagina de legenda acrescentada ao final')
        except ImportError:
            print('AVISO: reportlab ausente; legenda nao acrescentada (pip install reportlab)')
    w.write(a.saida)
    print('gravado', a.saida)


if __name__ == '__main__':
    main()
