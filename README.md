# Mariana

Skill para emitir **parecer crítico de tese ou dissertação em História** a partir de um PDF, com página, trecho literal e identificador (M-001...) em cada ponto, e devolver uma cópia do PDF com destaques coloridos.

Concepção do protocolo: Itamar Freitas. Experimental; o julgamento final é do parecerista humano.

## Conteúdo

- `SKILL.md`: instruções operacionais.
- `references/protocolo.md`: protocolo completo (v1.2), com a estrutura de 14 partes do parecer e o padrão de evidência.
- `scripts/anotar_e_verificar.py`: verifica que cada trecho existe na página indicada e grava o PDF marcado.

## Uso do script

```
pip install pdfplumber pypdf
python3 scripts/anotar_e_verificar.py tese.pdf registro.json tese_marcada.pdf --offset 0
python3 scripts/anotar_e_verificar.py tese.pdf registro.json --so-verificar
```

Formato do `registro.json` no cabeçalho do script.

## Limites

Não substitui a leitura da tese. A verificação prova que o trecho existe na página, não que a interpretação está certa. PDFs digitalizados sem texto não são marcados.

## Licença

A definir pelo autor.
