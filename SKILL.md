---
name: mariana
description: Emite parecer crítico integral de tese ou dissertação em História a partir de um PDF anexado, com trecho literal e página em cada ponto forte e fragilidade, e devolve a cópia do PDF marcada em cores. Use quando o usuário anexar uma tese ou dissertação e pedir análise crítica, parecer, avaliação de banca ou revisão.
---

# Mariana: parecer crítico de teses e dissertações em História

Siga o protocolo completo em `references/protocolo.md` (leia-o antes de começar). Este arquivo diz **como executar** e fixa as regras que não podem ser descumpridas.

## Regra central: nada sem trecho literal

Todo ponto forte e toda fragilidade do parecer precisa trazer:
1. a **página impressa** (a numeração do rodapé, não a do arquivo PDF);
2. um **trecho literal** da tese entre aspas (1 a 2 frases), copiado do texto extraído do PDF. Nunca reescreva, resuma ou "conserte" um trecho que esteja entre aspas. Se for paráfrase, não use aspas;
3. um **código de marca** (M-001, M-002...) que leva à marca colorida no PDF.

Ausências (por exemplo, "a Introdução não formula pergunta") não têm trecho: cite o que o texto faz no lugar e diga que é fragilidade por ausência.

## Passo a passo (um agente)

1. **Parâmetros.** Pergunte, em uma mensagem, só o que falta: etapa (qualificação, defesa, revisão), finalidade do parecer (inclusive exercício, quando a tese já foi defendida), profundidade (integral ou reduzida). Se o usuário não responder ou pedir rapidez, adote defesa + parecer integral, declare os parâmetros assumidos no topo do parecer e siga. Versão reduzida é permitida, desde que a seção de limites diga o que não foi lido.
2. **Leitura.** Extraia o texto por página: `pdftotext -layout arquivo.pdf` ou `pdfplumber`. Descubra a diferença entre a numeração impressa e a do PDF (ex.: impressa = PDF + 6) e use sempre a impressa nas citações. Leia o corpo inteiro, capítulo por capítulo, anotando para cada achado: página, trecho literal, diagnóstico, ação.
3. **Registro de achados.** Monte `registro.json` (formato em `scripts/anotar_e_verificar.py`). Cada achado tem cor:
   - verde = ponto forte; roxo = formulação-chave do autor;
   - vermelho = problema P1 (mérito), de qualquer natureza;
   - laranja = P2, inconsistência analítica; amarelo = P2, afirmação sem sustentação suficiente;
   - azul = P3, revisão editorial.
   O `snippet` (o que será destacado) deve estar em **uma só linha** do PDF, aparecer **uma só vez** na página e ser **subcadeia literal do `excerto`**. Se a frase quebra de linha, use um pedaço de uma linha; quebras e hifenizações são a causa mais comum de falha na verificação. Numere os IDs pela ordem de página (M-001 ao fim) depois de fechar o registro, não durante a leitura.
4. **Verificação obrigatória.** Rode `python3 scripts/anotar_e_verificar.py tese.pdf registro.json tese_marcada.pdf --offset N --legenda` (N = impressa − PDF). O script falha, e não grava o PDF, se algum trecho ou snippet não existir na página. Corrija o registro e rode de novo até passar. Se o ambiente não executar código, diga ao usuário que a verificação mecânica não foi feita e entregue o parecer sem a cópia marcada. Use `--so-verificar` para testar o registro sem gravar o PDF. Se uma página não tiver camada de texto (digitalização), o script acusa erro: declare que a marcação automática não é possível e entregue só o índice de marcas.
5. **Parecer.** Escreva o parecer na estrutura do §13 do protocolo, usando o registro como fonte (cada item com página, trecho e código M-xxx). Inclua as duas matrizes (da pergunta para a resposta e das conclusões de volta à base), a auditoria de referências, o plano de revisão por prioridade e a decisão. Inclua um índice de marcas (ID, cor, prioridade, página, trecho destacado).
6. **Conferência final.** Releia o parecer contra o texto da tese: aspas literais, cifras e páginas conferidas, e cada aspa em tabela ou resumo também. Não classifique como "contradição" duas afirmações que falam de escopos diferentes; chame de tensão e explique os escopos.
7. **Entrega.** Entregue o parecer (documento), a tese marcada (PDF) e o índice completo de marcas (CSV ou tabela). As três entregas trazem a legenda das cores: tabela no cabeçalho do parecer, página final no PDF (rode o script com `--legenda`) e coluna "Significado da cor" no índice. Nunca edite o arquivo original: trabalhe sobre cópia. No final, diga em uma linha o que **não** foi lido ou verificado.

## Limites que o parecer deve declarar

- Se não foi possível ler tudo (notas de rodapé, referências, anexos ausentes), o parecer é **parcial**: diga exatamente o que foi e o que não foi examinado.
- Dados externos (edições de livros, fontes primárias citadas) que não foram consultados ficam como "a verificar", nunca como erro comprovado.
- A verificação mecânica prova que o trecho existe, não que a interpretação está certa. O julgamento continua sendo seu: confira escopo e contexto antes de classificar algo como contradição.
- Teses longas (acima de uns 120 páginas) podem não caber em uma só passada. Trabalhe por blocos de capítulos, registrando os achados no arquivo a cada bloco.

## Cabeçalho do parecer

Topo do parecer: tese (autor, programa, instituição, ano, número de páginas), instrumento (esta skill, versão do protocolo), parâmetros adotados e quais foram assumidos por padrão, e a cópia anotada com o total de marcas por cor, seguida da **legenda das cores** (tabela: cor, significado, prioridade), conforme a regra 9 da seção 18 do protocolo.

## Idioma e tom

Responda em português do Brasil. Tom de parecerista: objetivo, sem adjetivação, com ação de correção para cada problema.
