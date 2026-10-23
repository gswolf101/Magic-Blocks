# Textos detalhados das versões (usados por gerar_versoes.py)

## 1.0.139
Versão intermediária da atualização do Herfestus. Tudo o que começou aqui foi concluído e está descrito na [1.0.141](1.0.141.md).

## 1.0.140
Versão intermediária da atualização do Herfestus. Tudo o que começou aqui foi concluído e está descrito na [1.0.141](1.0.141.md).

## 1.0.141
### Herfestus refeito
- **Modelo novo:** forma humana com 2,5 blocos de altura, armadura completa e textura própria. Antes ele era montado com blocos do jogo.
  - Elmo com chifres de ponta dourada, viseira com olhos de brasa, penacho e barba de fogo.
  - Ombreiras com espinhos, peitoral com o núcleo da forja pulsando, faldas, manoplas e grevas com veios de magma e capa carmesim.
- **Marreta 3D:** cabeça octogonal com bandas douradas, runas acesas e cabo de couro.
- **Bigorna nova:** uma peça única de 3x3x3 com runas acesas, onde dá para subir e clicar em qualquer parte. Arenas antigas ficam com a bigorna antiga; `/magicblocks structure herfestus` refaz a arena.

### Novos drops do Herfestus
- **Marreta de Herfestus (10%):** dano alto, lenta, põe fogo no alvo. Botão direito no chão solta uma onda de fogo de 5 blocos (recarga de 8s).
- **Coração da Forja:** bloco de magma animado com aura de fogo e faíscas.
- **Diário de Herfestus:** livro de 7 páginas com a história do ferreiro e da Espada do Apocalipse.

### Mesa de Herfestus
- **Receita:** Diário em cima, mesa de encantamento no meio entre 2 barras de ouro e 3 pedras-negras polidas embaixo.
- **Uso:** coloque um item ou livro, escolha o encantamento e o nível e clique em "Encantar". Custa níveis de XP; se o item já tem o encantamento, paga só a diferença.
- Não oferece maldições nem encantamentos incompatíveis com os que o item já tem.

### Joias
- **Opala:** −12% de recarga da esquiva por joia (até −50%). Feita no Infusor com Diamante + Membrana de Phantom.
- **Minério de Joias:** só na Forja Primordial, em veios de 1 a 3 blocos. Solta uma joia aleatória (toque de seda pega o bloco).
- Monstros comuns mortos por jogador têm 5% de chance de soltar uma joia (chefes não).

## 1.0.142
### Mímico das Sombras (chefe)
- 5% de chance de surgir quando um jogador mata um Mímico, com explosão de sombras e tremida de tela.
- Mímico de obsidiana roxa, 35% maior, com 600 de vida e barra de chefe roxa.
- Usa os golpes do Mímico e, a cada 7–11s, vira uma criatura hostil do mod de verdade, com a IA e os ataques dela. O dano que essa forma leva sai da vida do chefe. Volta ao normal depois de 12s ou ao perder 15% da vida.
- **Drop:** Núcleo das Sombras e 4 a 8 Fragmentos de Espelho das Almas.

### Manequim das Sombras
- **Receita:** no Infusor, Boneco de Slime + Núcleo das Sombras.
- Boneco de treino de pano costurado com olhos de botão e alvo no peito.
- Shift + direito equipa armadura e itens. Direito abre a tela de treino: escolha a criatura e a vida (10 a 5000) e clique em Começar.
- Ele vira a criatura escolhida, com os itens dele, e ataca você. Ao zerar a vida aparece "Treino vencido em X s!" e ele volta ao lugar; ele nunca morre. O treino acaba se você morrer ou se afastar mais de 48 blocos.

## 1.0.143
- **Correção:** servidores dedicados caíam ao carregar o mod por causa do texto de dica do Espelho da Alma, que usava uma classe que só existe no cliente. Corrigido também num ponto do armazenamento com o mesmo risco.

## 1.0.144
- **Avisos de ataque com shaders:** com um shaderpack ligado, cada aviso no chão também é desenhado com poeira colorida (círculos, áreas, faixas, quadrados e linhas de mira), que os shaders mostram normalmente. Sem shader nada muda.
- **Manequim das Sombras:** só imita criaturas que têm aviso de ataque (Lobisomem, Lobisomem Alfa, Sentinela Arcana, Orc, Anão, Ronin, Rei Goblin e Mímico). O Mímico das Sombras vira as mesmas, menos ele próprio.

## 1.0.145
- **Shaders:** os avisos de ataque agora reconhecem também os shaders do OptiFine (antes só Oculus/Iris).
- **Sombras Errantes (Vazio):** seguram a Adaga dos Viajantes, saltam e investem com aviso no chão e dropam Cristais do Vazio.
  - **Adaga dos Viajantes:** 15 de dano, durabilidade de ferro.
- **Devoradores:** miram por 1s e disparam um laser roxo, com bem menos frequência. Dropam o Catalisador do Vazio.
  - **Rifle do Vazio:** feito com Cristais do Vazio, Catalisador e um botão; dispara lasers.
- **Águas-vivas:** aparecem no céu do Vazio, perto de quem está lá.
- **Livro-guia novo:** duas páginas abertas, com as novidades à esquerda e 8 ícones de seções à direita (armas, armaduras, minérios, bancadas, criaturas, chefes, blocos mágicos e máquinas da natureza).
- **Armazenamento:** tela menor, com a pesquisa visível e a mesa de criação ao lado. O corante agora pinta só a moldura.

## 1.0.146
- **Ronin mais épico:** entrada com pétalas, segunda postura com 50% da vida, Dança das Pétalas e Postura de Contra-ataque (revida quem bate nele na hora errada). Barra de chefe própria.
- **Herfestus mais épico:** Arsenal da Forja (armas flutuando que são lançadas em você), Queda da Bigorna, colunas de fogo na fúria e aura de chamas na fase 3.
- **Rei Goblin mais épico:** rugido de abertura, leque de lâminas, bumerangue e fúria com 40% da vida.
- **Anões novos:** Guerreiro, Mineiro (com lanterna e mochila) e Mercador (troca itens por barras de ouro), com barbas de cores diferentes e machado arremessado.
- **Aldeias goblins:** paliçada com 4 portões, torres de vigia, praça com fogueira e casebres decorados.
- **Grupos de goblins exploradores:** agora aparecem em qualquer bioma de terra.

## 1.0.147
### Jonkey refeito
- **Modelo novo de gorila:** corcunda alta nos ombros, peito largo de couro, braços compridos com cotovelo e antebraços grossos, pernas curtas, cabeça baixa com crista, testa saliente, focinho, orelhas, dentes com caninos e uma cicatriz de garra no ombro.
- **Textura nova:** pelo em fios, sela prateada nas costas, couro enrugado no rosto, peito e mãos, olhos âmbar (vermelhos quando enfurecido).
- **Animações:** bate no peito com os cotovelos dobrados, puxa o ar antes do Berro, galopa na Investida, coça a cabeça quando cai tonto e ronca dormindo.
- **Efeitos dos ataques:** saem as luzes laranja; entram efeitos de terra.
  - Golpe Sísmico: rochas brotando do chão pela faixa inteira.
  - Investida: terra arrancada e poeira; ao bater numa árvore, um anel de rochas.
  - Arremesso: o chão racha em volta do bloco arrancado, e o impacto estoura em rochas.
  - Berro: ondas sônicas pela faixa e a fumaça verde sendo sugada antes.
  - Giro: cortes de vento e redemoinho de poeira e folhas.
  - Fúria: anéis de rochas musgosas.

### Arenas maiores
- **Pantan0:** o tablado agora tem raio 28, o mesmo da arena do Leviatã, com os anéis, postes e velas proporcionais.
- **Ronin:** novo pátio-arena de 57x57 na frente do dojo, com cascalho rastelado, caminho de pedra, cerca com portão, lanternas de pedra e cerejeiras. O Ronin fica no meio do pátio.
- As arenas já geradas não mudam; só as novas.

### Servidores
- **Animações dos chefes travando em servidor:** o cliente agora marca o início de cada golpe com o próprio relógio. Vale para os golens (inclusive o de fogo), Esmeralda Colossal, Ronin, Herfestus, Kraken, Jonkey, Wyrm do Eclipse, Rei Goblin, Pantan0, Mímico, Lobisomem, Orc e Anão.
- **Movimento aos solavancos:** pulos, investidas e quedas dos chefes são enviados a cada tick.
- **Giro e Dança das Adagas engasgando:** a animação usa um relógio local que não pula, e quem move o jogador durante o giro é o próprio cliente. O mesmo relógio vale para espada, rolagem, lobisomem, raios e anéis.
- **OptiFine:** detecção dos shaders mais confiável (duas formas de perguntar ao OptiFine).

## 1.0.148
- **Forja de Herfestus:** agora nasce na superfície, na altura média do terreno em volta. Antes a altura era limitada a 20 blocos acima do mar e, em terreno alto, a arena ficava enterrada num buraco dentro do morro. Ela também passou a ser gerada depois da floresta, então as árvores vermelhas não crescem mais por cima do piso. Só forjas geradas daqui para a frente mudam.
- **Rubi:** +5% de dano por joia (antes era +2 de dano fixo). Continua incendiando o alvo.
- **Lobisomem:** volta ao normal assim que a barra de mana chega a zero (antes só conferia na cobrança de 15 em 15 segundos). Também não dá para se transformar com a barra de mana vazia.
