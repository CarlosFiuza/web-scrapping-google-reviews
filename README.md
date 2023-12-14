# web-scrapping-google-reviews

## O que é?

Projeto criado como parte de um desafio técnico de um processo seletivo para desenvolvedor full-stack. Desenvolvido no período de uma semana.

## O que faz?

O projeto tem como objetivo extrair as avaliações criadas pelo clientes de lojas cadastradas no google.

## Tecnologias

- Selenium
- Selenium Wire
- lxml
- SqlAlchemy
- requests
- datetime
- serverless framework
- docker
- PostgreSQL
- aws ecr

## Como faz?

- Uso do framework Selenium e Selenium Wire que reproduzem o acesso a página web de avaliações de determinada loja.
- A partir do conteúdo HTML os dados são extraídos e persistidos, em lotes, em uma banco de dados PostgreSQL.
- A página web de avaliações do google apresenta apenas dez avaliações por vez, carregando mais itens assim que realizado um scroll.
- A "sacada" encontrada foi reproduzir as requisições HTTP que são realizadas na API do google assim que novos itens são carregados.

### Passo a passo:

1. Recupera string de busca no banco de dados de acordo com o id da loja passado para a função principal.
2. Carrega página web com o Selenium webdriver.
3. Clica no link que abre uma modal com as avaliações da loja.
4. Extrai dados usando Selenium.
5. Persiste dados
6. Busca por token que indica que existem mais avaliações a serem carregadas.
7. Se não existe encerra programa.
8. Se existe faz scroll na página para disparar requisição que retorna novas avaliações.
9. Captura requisições realizadas pelo webdriver utilizando o Selenium Wire.
10. Filtra por requisição de carregamento de novos itens.
11. Fecha webdriver pois seu uso não é mais necessário.
12. A partir disso é feito um loop que:
    - Baixa conteúdo HTML a partir da requisição HTTP com último token recuperado.
    - Extraí dados e token de novos comentários a serem carregados.
    - Persiste dados.
    - Se token encontrado executa outra iteração do loop.

## Prós

- Nos testes realizados em localhost o código performa todo o scraping em média de 60 segundos para uma loja com 601 avaliações.
- Isolamento de ambiente com uso do docker. Com isso é feito donwload do Chromium e webdriver em versões especificadas no Dockerfile.
- Scraping, manipulação e persistência de dados feita em lotes, para não sobrecarregar mémoria e transação do banco de dados.

## Contras

- Solução não funciona quando executada no lambda AWS, devido ao fato da página WEB carregada ser diferente da página usada como referência para o scraping.
- Dependência quase total do web-scraping, o que implica que alterações no layout do google irão tornar o programa obsoleto.

## Alternativas

- Acessar as avaliações através da página do google maps. Nesse sentido uma outra análise do contéudo HTML é necessária para realizar o scraping.
- Pagar pela extração dos dados. Softwares como o Outscraper realizam o scraping e cobram pela quantidade de avaliações.
- Utilizar apenas API do google. Ao inspecionar a página web de avaliações é possível notar que os dados são obtidos a partir de requisições HTTP, mas a resposta retornada é constituida de um json nada amigável de ser interpretado. Apesar disso, existe certa padronização nas chaves - valores, que se entendida pode ser utilizada.
