<h2>O que é arquivo wsq? </h2>
Ícone de tipo de arquivo de imagem bitmap Tipo de arquivo de imagem bitmap

A extensão do arquivo wsq está relacionada ao formato de arquivo bitmap de quantização escalar do pacote Wavelet .

O algoritmo Wavelet Scalar Quantization (WSQ) é um algoritmo de compressão usado para imagens de impressão digital em escala de cinza. É baseado na teoria da wavelet e se tornou um padrão para troca e armazenamento de imagens de impressões digitais. WSQ foi desenvolvido pelo FBI, o Laboratório Nacional de Los Alamos e o Instituto Nacional de Padrões e Tecnologia (NIST).

Este método de compressão é preferível a algoritmos de compressão padrão como JPEG porque nas mesmas taxas de compressão WSQ não apresenta os "artefatos de bloqueio" e perda de recursos de escala fina que não são aceitáveis ​​para identificação em ambientes financeiros e justiça criminal.

<h2>Uma das principais funcionalidades da API é converter digtais no formato WSQ para o formato PNG;</h2>
Porém, ela não se limita a fazer somente isso, foram adicioandos metodos extras como:<p/>
  Função que recebe uma WSQ em base64, rotaciona 90º e converte em PNG; <br>
  Função que remove o fundo de imagem. Ajustado para remover fundo de digital e assina;<br>
  Função que carrega um arquivo e transforma em base64 (JPEG, PNG, WSQ);<br>
  Função que recebe uma lista de WSQ em base64 e converte em PNG;<br>
  Além de um método que busca em uma base de dados o BLOB do WSQ para converter em PNG.<br>

Antes de executar a API instale as dependencias que está no arquivo REQUIREMENTS.txt.

<h2>Como Executar a API?</h2>
Para Executar a API, vá até a pasta do clone, via terminal e execute:

python3 appWSQ.py

Para acessar a API, no navegador acesse:

http://localhost:8080/doc
