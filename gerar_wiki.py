"""
Gera a wiki do Magic & Blocks (paginas HTML + icones) a partir das texturas e receitas do proprio mod.
Rode de novo depois de mudar receitas ou texturas:  python gerar_wiki.py
Precisa do Pillow e do jar do Minecraft que o ForgeGradle baixa (texturas vanilla dos ingredientes).
"""
import html
import io
import json
import os
import zipfile

from PIL import Image

SITE = os.path.dirname(os.path.abspath(__file__))
MOD = os.path.join(os.path.dirname(SITE), 'src', 'main', 'resources')
MOD_TEX = os.path.join(MOD, 'assets', 'magicblocks', 'textures')
RECIPES = os.path.join(MOD, 'data', 'magicblocks', 'recipes')
JAR = os.path.join(os.path.expanduser('~'), '.gradle', 'caches', 'forge_gradle', 'minecraft_repo', 'versions', '1.21.1', 'client-extra.jar')
ICONS = os.path.join(SITE, 'img', 'icons')
os.makedirs(ICONS, exist_ok=True)
jar = zipfile.ZipFile(JAR)
LANG = json.load(open(os.path.join(MOD, 'assets', 'magicblocks', 'lang', 'pt_br.json'), encoding='utf-8'))

# ===================================================================== icones


def vtex(path):
    return Image.open(io.BytesIO(jar.read('assets/minecraft/textures/' + path + '.png'))).convert('RGBA').crop((0, 0, 16, 16))


def mtex(path):
    return Image.open(os.path.join(MOD_TEX, path + '.png')).convert('RGBA').crop((0, 0, 16, 16))


def tint(img, rgb):
    out = img.copy()
    p = out.load()
    for y in range(out.height):
        for x in range(out.width):
            r, g, b, a = p[x, y]
            p[x, y] = (r * rgb[0] // 255, g * rgb[1] // 255, b * rgb[2] // 255, a)
    return out


def layered(base, overlay, rgb):
    out = base.copy()
    out.alpha_composite(tint(overlay, rgb))
    return out


def shade(c, f):
    return (int(c[0] * f), int(c[1] * f), int(c[2] * f), c[3])


def iso(top, left, right=None):
    """Cubo isometrico 32x32 (como o icone de bloco no inventario)."""
    right = right or left
    out = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    o = out.load()
    faces = [  # (origem, eixo u, eixo v, textura, brilho)
        ((0, 8), (16, -8), (16, 8), top, 1.0),
        ((0, 8), (16, 8), (0, 16), left, 0.8),
        ((16, 16), (16, -8), (0, 16), right, 0.62),
    ]
    for (ox, oy), (ax, ay), (bx, by), tex, light in faces:
        t = tex.load()
        det = ax * by - ay * bx
        for py in range(32):
            for px in range(32):
                dx, dy = px + 0.5 - ox, py + 0.5 - oy
                u = (dx * by - dy * bx) / det
                v = (ax * dy - ay * dx) / det
                if 0 <= u < 1 and 0 <= v < 1:
                    c = t[int(u * 16), int(v * 16)]
                    if c[3] > 0:
                        o[px, py] = shade(c, light)
    return out


def chest_icon(entity_tex):
    t = Image.open(io.BytesIO(jar.read('assets/minecraft/textures/entity/chest/%s.png' % entity_tex))).convert('RGBA')
    top = t.crop((14, 0, 28, 14)).resize((16, 16), Image.NEAREST)
    side = Image.new('RGBA', (14, 15))
    side.paste(t.crop((14, 14, 28, 19)), (0, 0))
    side.paste(t.crop((14, 33, 28, 43)), (0, 5))
    side = side.resize((16, 16), Image.NEAREST)
    return iso(top, side)


def flat(img):
    return img.resize((32, 32), Image.NEAREST)


LEAF = (72, 181, 24)
CYAN = (127, 230, 255)

ICON_BUILDERS = {
    # --- blocos magicos (o bloco que flutua na mao) ---
    'magicblocks:fire_block': lambda: iso(vtex('block/magma'), vtex('block/magma')),
    'magicblocks:soul_egg': lambda: flat(layered(tint(vtex('item/spawn_egg'), (58, 26, 85)), vtex('item/spawn_egg_overlay'), (127, 230, 255))),
    'magicblocks:sculk_block': lambda: iso(vtex('block/sculk'), vtex('block/sculk')),
    'magicblocks:leaf_block': lambda: iso(tint(vtex('block/oak_leaves'), LEAF), tint(vtex('block/oak_leaves'), LEAF)),
    'magicblocks:gilded_block': lambda: iso(vtex('block/gilded_blackstone'), vtex('block/gilded_blackstone')),
    'magicblocks:spawner_block': lambda: iso(vtex('block/spawner'), vtex('block/spawner')),
    'magicblocks:chest_block': lambda: chest_icon('normal'),
    'magicblocks:void_block': lambda: iso(mtex('block/void_core'), mtex('block/void_core')),
    'magicblocks:water_block': lambda: iso(mtex('block/water_core'), mtex('block/water_core')),
    'magicblocks:ice_block': lambda: iso(vtex('block/blue_ice'), vtex('block/blue_ice')),
    # --- blocos colocaveis do mod ---
    'magicblocks:mana_ore': lambda: iso(mtex('block/mana_ore'), mtex('block/mana_ore')),
    'magicblocks:nature_workbench': lambda: iso(mtex('block/nature_workbench_top'), mtex('block/nature_workbench_side')),
    'magicblocks:pedestal': lambda: iso(vtex('block/smooth_stone'), vtex('block/smooth_stone')),
    'magicblocks:arcane_pedestal': lambda: iso(mtex('block/arcane_pedestal_top'), mtex('block/arcane_pedestal_rune')),
    'magicblocks:manilium_spawner': lambda: iso(mtex('block/manilium_spawner'), mtex('block/manilium_spawner')),
    # --- manilium pintavel (cor padrao) ---
    'magicblocks:manilium_sword': lambda: flat(layered(mtex('item/manilium_sword'), mtex('item/manilium_sword_overlay'), CYAN)),
    # --- vanilla ---
    'minecraft:chest': lambda: chest_icon('normal'),
    'minecraft:ender_chest': lambda: chest_icon('ender'),
    'minecraft:barrel': lambda: iso(vtex('block/barrel_top'), vtex('block/barrel_side')),
    'minecraft:shulker_box': lambda: iso(vtex('block/shulker_box'), vtex('block/shulker_box')),
    'minecraft:cactus': lambda: iso(vtex('block/cactus_top'), vtex('block/cactus_side')),
    'minecraft:lily_pad': lambda: flat(tint(vtex('block/lily_pad'), (32, 128, 48))),
    'minecraft:iron_bars': lambda: flat(vtex('block/iron_bars')),
    'minecraft:smooth_stone_slab': lambda: iso(vtex('block/smooth_stone'), vtex('block/smooth_stone_slab_side')),
    '#minecraft:leaves': lambda: iso(tint(vtex('block/oak_leaves'), LEAF), tint(vtex('block/oak_leaves'), LEAF)),
    '#minecraft:flowers': lambda: flat(vtex('block/poppy')),
    '#minecraft:planks': lambda: iso(vtex('block/oak_planks'), vtex('block/oak_planks')),
    'minecraft:enchanted_golden_apple': lambda: flat(vtex('item/golden_apple')),
    'minecraft:zombie_spawn_egg': lambda: flat(layered(tint(vtex('item/spawn_egg'), (0, 175, 175)), vtex('item/spawn_egg_overlay'), (121, 156, 101))),
}
for piece in ['helmet', 'chestplate', 'leggings', 'boots']:
    ICON_BUILDERS['magicblocks:manilium_' + piece] = (lambda p: lambda: flat(layered(
        mtex('item/manilium_' + p), mtex('item/manilium_%s_overlay' % p), CYAN)))(piece)
for block in ['iron_block', 'obsidian', 'ice', 'sponge', 'moss_block', 'gold_block', 'smooth_stone', 'gilded_blackstone',
              'blue_ice', 'grass_block', 'spawner', 'beehive', 'redstone_block']:
    if block == 'grass_block':
        ICON_BUILDERS['minecraft:grass_block'] = lambda: iso(tint(vtex('block/grass_block_top'), (124, 189, 107)),
                                                             vtex('block/grass_block_side'))
    elif block == 'beehive':
        ICON_BUILDERS['minecraft:beehive'] = lambda: iso(vtex('block/beehive_end'), vtex('block/beehive_front'), vtex('block/beehive_side'))
    else:
        ICON_BUILDERS['minecraft:' + block] = (lambda b: lambda: iso(vtex('block/' + b), vtex('block/' + b)))(block)


def icon(item_id):
    """Caminho (relativo ao site) do icone do item; gera o arquivo na primeira vez."""
    if item_id.endswith('_shulker_box'):
        item_id = 'minecraft:shulker_box'
    name = item_id.replace('#', 'tag_').replace(':', '_')
    path = os.path.join(ICONS, name + '.png')
    if not os.path.exists(path):
        if item_id in ICON_BUILDERS:
            img = ICON_BUILDERS[item_id]()
        else:
            ns, p = item_id.split(':')
            img = flat(mtex('item/' + p) if ns == 'magicblocks' else vtex('item/' + p))
        img.save(path)
    return 'img/icons/%s.png' % name


VANILLA_PT = {
    'minecraft:barrel': 'Barril', 'minecraft:shulker_box': 'Caixa de Shulker (qualquer cor)', 'minecraft:bone': 'Osso',
    'minecraft:bow': 'Arco', 'minecraft:cactus': 'Cacto', 'minecraft:chest': 'Baú', 'minecraft:comparator': 'Comparador',
    'minecraft:diamond': 'Diamante', 'minecraft:diamond_sword': 'Espada de Diamante', 'minecraft:echo_shard': 'Fragmento de Eco',
    'minecraft:enchanted_golden_apple': 'Maçã Dourada Encantada', 'minecraft:ender_chest': 'Baú do Ender',
    'minecraft:ender_eye': 'Olho do Ender', 'minecraft:experience_bottle': 'Frasco de Experiência',
    'minecraft:gilded_blackstone': 'Blackstone Dourada', 'minecraft:gold_block': 'Bloco de Ouro', 'minecraft:ice': 'Gelo',
    'minecraft:iron_bars': 'Grade de Ferro', 'minecraft:iron_block': 'Bloco de Ferro', 'minecraft:iron_ingot': 'Barra de Ferro',
    'minecraft:lily_pad': 'Vitória-régia', 'minecraft:moss_block': 'Bloco de Musgo', 'minecraft:nether_star': 'Estrela do Nether',
    'minecraft:netherite_ingot': 'Barra de Netherita', 'minecraft:obsidian': 'Obsidiana', 'minecraft:rotten_flesh': 'Carne Podre',
    'minecraft:smooth_stone': 'Pedra Lisa', 'minecraft:smooth_stone_slab': 'Laje de Pedra Lisa', 'minecraft:sponge': 'Esponja',
    'minecraft:water_bucket': 'Balde de Água', 'minecraft:blaze_powder': 'Pó de Blaze', 'minecraft:book': 'Livro',
    'minecraft:egg': 'Ovo', 'minecraft:blue_ice': 'Gelo Azul', 'minecraft:netherite_sword': 'Espada de Netherita',
    'minecraft:netherite_helmet': 'Capacete de Netherita', 'minecraft:netherite_chestplate': 'Peitoral de Netherita',
    'minecraft:netherite_leggings': 'Calças de Netherita', 'minecraft:netherite_boots': 'Botas de Netherita',
    'minecraft:netherite_upgrade_smithing_template': 'Molde de Melhoria de Netherita', 'minecraft:spawner': 'Spawner',
    'minecraft:grass_block': 'Bloco de Grama', 'minecraft:redstone_block': 'Bloco de Redstone', 'minecraft:beehive': 'Colmeia', '#minecraft:leaves': 'Folhas (qualquer)',
    '#minecraft:flowers': 'Flor (qualquer)', '#minecraft:planks': 'Tábuas (qualquer)',
}


def strip_codes(text):
    out, skip = [], False
    for ch in text:
        if skip:
            skip = False
        elif ch == '§':
            skip = True
        else:
            out.append(ch)
    return ''.join(out)


def name(item_id):
    if item_id.endswith('_shulker_box'):
        item_id = 'minecraft:shulker_box'
    if item_id in VANILLA_PT:
        return VANILLA_PT[item_id]
    ns, p = item_id.split(':')
    for kind in ('item', 'block'):
        key = '%s.magicblocks.%s' % (kind, p)
        if key in LANG:
            return strip_codes(LANG[key])
    return p


# ===================================================================== receitas


def slot(item_id, big=False):
    if not item_id:
        return '<span class="slot%s"></span>' % (' big' if big else '')
    n = html.escape(name(item_id))
    return '<span class="slot%s" title="%s"><img src="%s" alt="%s"></span>' % (' big' if big else '', n, icon(item_id), n)


def crafting(recipe_file):
    d = json.load(open(os.path.join(RECIPES, recipe_file + '.json'), encoding='utf-8'))
    key = {}
    for k, v in d.get('key', {}).items():
        first = v[0] if isinstance(v, list) else v
        key[k] = first.get('item') or '#' + first['tag']
    if d['type'] == 'minecraft:crafting_shapeless':
        items = [(i.get('item') or '#' + i['tag']) for i in d['ingredients']]
        rows = [items[i:i + 3] for i in range(0, 9, 3)]
    else:
        rows = [[key.get(ch) if ch != ' ' else None for ch in row.ljust(3)] for row in d['pattern']]
    while len(rows) < 3:
        rows.append([])
    grid = ''.join(slot(rows[r][c] if c < len(rows[r]) else None) for r in range(3) for c in range(3))
    result = d['result']['item']
    count = d['result'].get('count', 1)
    return ('<div class="recipe"><div class="label">Bancada de trabalho</div><div class="craft"><div class="grid3">%s</div>'
            '<span class="arrow">&#10140;</span>%s%s</div></div>') % (grid, slot(result, True),
                                                                     '<span class="count">x%d</span>' % count if count > 1 else '')


def infuser(inp, catalyst, out):
    return ('<div class="recipe"><div class="label">Nature Infuser</div><div class="craft infuse">'
            '<div class="col">%s<span class="plus">+</span>%s</div>'
            '<img class="machine" src="%s" title="Nature Infuser" alt="">'
            '<span class="arrow">&#10140;</span>%s</div>'
            '<div class="hint">em cima: entrada &middot; embaixo: alimentação</div></div>') % (
        slot(inp), slot(catalyst), icon('magicblocks:nature_workbench'), slot(out, True))


def smithing(base, out):
    return ('<div class="recipe"><div class="label">Mesa de ferraria</div><div class="craft">%s%s%s'
            '<span class="arrow">&#10140;</span>%s</div></div>') % (
        slot('magicblocks:manilium_upgrade_smithing_template'), slot(base), slot('magicblocks:manilium_ingot'), slot(out, True))


def note(text):
    return '<div class="recipe"><div class="label">Como obter</div><p class="obtain">%s</p></div>' % text


def table(rows, head=('Ação', 'Efeito', 'Mana')):
    body = ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % c for c in row) for row in rows)
    return '<table class="abil"><tr>%s</tr>%s</table>' % (''.join('<th>%s</th>' % h for h in head), body)


# ===================================================================== conteudo

# Cada entrada: (id do item, texto de introducao, [blocos de html extras])
RECURSOS = [
    ('magicblocks:mana_orb', 'O coração de todas as receitas mágicas. Também serve de alimentação no Nature Infuser para fortalecer a armadura e a espada de Manilium.',
     [note('Minere o Minério de Mana com picareta de diamante ou melhor (Fortuna aumenta). Ou faça com Essência de Mana:'), crafting('mana_orb')]),
    ('magicblocks:mana_essence', 'Energia de mana pura, usada para criar Orbes de Mana, o Coletor da Alma e o molde de Manilium.',
     [note('Todo mago (zumbis magos, Zumbi Necromante e Mago Midas) tem <b>10%</b> de chance de soltar uma.')]),
    ('magicblocks:void_essence', 'Um pedaço do nada. Ingrediente do Bloco de Void.',
     [note('Jogue uma <b>Orbe de Mana</b> no void (abaixo do fundo do mundo ou fora da ilha do End). Quem jogou recebe uma essência por orbe.')]),
    ('magicblocks:elemental_diamond', 'O Cristal Instável: um diamante carregado pela natureza. Aparece em quase todas as receitas do mod.',
     [infuser('minecraft:diamond', 'minecraft:moss_block', 'magicblocks:elemental_diamond').replace(
         slot('minecraft:moss_block'), '<span class="slot" title="Combustível vegetal (folhas, flores, plantações...)"><img src="%s" alt=""></span>' % icon('#minecraft:leaves'))]),
    ('magicblocks:manilium_ingot', 'Netherita reforçada com mana. Mais escura, com veios azul-claros. Base de todo o equipamento de Manilium.',
     [crafting('manilium_ingot')]),
    ('magicblocks:manilium_upgrade_smithing_template', 'Molde da mesa de ferraria que transforma equipamento de netherita em Manilium.',
     [infuser('minecraft:netherite_upgrade_smithing_template', 'magicblocks:mana_essence', 'magicblocks:manilium_upgrade_smithing_template')]),
    ('magicblocks:soul_converter', 'Quando falta mana, paga a diferença com o seu XP: <b>10 pontos de XP = 1 de mana</b>. Funciona no inventário, no slot de amuleto do <b>Curios</b> (aparece no peito, estilo reator) ou embutido em qualquer peitoral.',
     [crafting('soul_converter'), infuser('minecraft:netherite_chestplate', 'magicblocks:soul_converter', 'minecraft:netherite_chestplate').replace(
         '<div class="hint">', '<div class="hint">qualquer peitoral recebe o conversor embutido &middot; ')]),
    ('magicblocks:soul_collector', 'Clique com o botão direito em <b>qualquer criatura</b> (do jogo, deste mod ou de outros mods) para guardar o DNA dela. Cada coletor guarda <b>um só</b> DNA. Depois junte o coletor com um ovo e um frasco de XP em qualquer bancada para criar o ovo gerador daquela criatura. Se ela não tiver ovo próprio, sai um <b>Ovo de Alma</b>, que funciona igual. O coletor volta para você.',
     [crafting('soul_collector'), '<div class="recipe"><div class="label">Ovo gerador</div><div class="craft">%s<span class="plus">+</span>%s<span class="plus">+</span>%s<span class="arrow">&#10140;</span><span class="slot big" title="Ovo gerador da criatura"><img src="%s" alt=""></span></div></div>' % (
         slot('magicblocks:soul_collector'), slot('minecraft:egg'), slot('minecraft:experience_bottle'), icon('minecraft:zombie_spawn_egg'))]),
    ('magicblocks:soul_egg', 'Ovo gerador feito pelo Coletor da Alma para criaturas que não têm ovo próprio. Funciona como um ovo gerador comum, inclusive para escolher a criatura do Spawner de Manilium.',
     [note('Coletor da Alma com o DNA de uma criatura sem ovo + ovo + frasco de XP.')]),
    ('magicblocks:broken_spawner', 'O que sobra de um spawner quebrado. Pode ser consertado.',
     [note('Quebre um <b>spawner</b> comum (fora do criativo).'), crafting('lifeless_spawner')]),
    ('magicblocks:lifeless_spawner', 'Um spawner consertado, mas ainda sem vida. Precisa de Manilium para despertar.',
     [infuser('magicblocks:lifeless_spawner', 'magicblocks:manilium_ingot', 'magicblocks:manilium_spawner')]),
    ('magicblocks:guide_book', 'O livro com as receitas e explicações de tudo. Você ganha um ao entrar no mundo pela primeira vez.',
     [crafting('guide_book')]),
]

BLOCOS = [
    ('magicblocks:mana_ore', 'Minério raro que aparece sozinho nas profundezas (camada -64 a -50). Precisa de picareta de ferro; com picareta de diamante solta Orbes de Mana (Fortuna aumenta). Com Toque Suave, solta o próprio bloco.',
     [note('Encontrado nas profundezas do mundo.')]),
    ('magicblocks:nature_workbench', 'Transforma itens com a força da natureza ao redor. Entrada em cima, alimentação embaixo (combustível vegetal ou o catalisador da infusão) e saída à direita. Funis: entrada por cima, alimentação pelos lados, saída por baixo.',
     [crafting('nature_workbench'),
      '<h4>Força da natureza</h4><p>Conta os blocos num raio de 5 (inclusive acima e abaixo). Cada tipo soma até um limite; terra comum não conta. Sem natureza nenhuma, o infusor não funciona.</p>' +
      table([('<img class="mini" src="%s">Grama' % icon('minecraft:grass_block'), '25', '1x'),
             ('<img class="mini" src="%s">Flores' % icon('#minecraft:flowers'), '5', '+0,25x'),
             ('<img class="mini" src="%s">Folhas de árvore' % icon('#minecraft:leaves'), '15', '+0,25x'),
             ('<img class="mini" src="%s">Pedestal com folhas' % icon('magicblocks:pedestal'), '1', '+0,5x'),
             ('<img class="mini" src="%s">Colmeia' % icon('minecraft:beehive'), '1', '+0,25x')],
            head=('Bloco', 'Limite', 'Força máxima')),
      '<h4>Todas as infusões</h4>' +
      table([('Diamante', 'combustível vegetal', 'Cristal Instável'),
             ('Molde de melhoria de netherita', 'Essência de Mana', 'Molde de Manilium'),
             ('Peça de Manilium', 'Orbe de Mana', '+1 de defesa (até +5)'),
             ('Espada de Manilium', 'Orbe de Mana', '+1 de dano (sem limite)'),
             ('Espada de Manilium (vazia)', 'Bloco Mágico', 'bloco na guarda da espada'),
             ('Qualquer peitoral', 'Conversor de Almas', 'peitoral com conversor'),
             ('Spawner sem Vida', 'Barra de Manilium', 'Spawner de Manilium'),
             ('Bloco de Água', 'Gelo Azul', 'Bloco de Gelo'),
             ('Bloco de Fogo', 'Bloco de Redstone', 'Bloco de Fogo Vermelho')], head=('Entrada', 'Alimentação', 'Resultado'))]),
    ('magicblocks:pedestal', 'Expõe um item: clique com o item para colocar e com a mão vazia para pegar. Espadas ficam cravadas. Com folhas (ou o Bloco de Folha) em cima, fortalece o Nature Infuser.',
     [crafting('pedestal')]),
    ('magicblocks:arcane_pedestal', 'A melhoria do pedestal. Por enquanto é decorativo e solta partículas encantadas.',
     [crafting('arcane_pedestal')]),
    ('magicblocks:manilium_spawner', 'Um spawner melhorado: cria as criaturas <b>mesmo com luz</b>, mas só enquanto recebe <b>sinal de redstone</b>. Clique nele com um ovo gerador para escolher a criatura. Quebra com qualquer picareta e guarda a criatura escolhida.',
     [infuser('magicblocks:lifeless_spawner', 'magicblocks:manilium_ingot', 'magicblocks:manilium_spawner')]),
]

MAGICOS = [
    ('magicblocks:fire_block', 'Um bloco de magma que gira sobre a mão. Dá resistência ao fogo enquanto está na mão.',
     [crafting('fire_block'), '<h4>Variante vermelha</h4><p>Coloque o bloco no Nature Infuser com um <b>Bloco de Redstone</b> na alimentação: o bloco vira magma vermelho e todos os ataques (chamas, bola de fogo, cogubrilho) ficam vermelhos.</p>',
      infuser('magicblocks:fire_block', 'minecraft:redstone_block', 'magicblocks:fire_block'), table([
         ('Segurar direito', 'Lança-chamas em cone (12 blocos, abre até 3x3)', '1 a cada 5s'),
         ('Bater', 'Bola de fogo explosiva que não quebra blocos', '1'),
         ('Shift + bater', 'Explosão de chamas em volta que empurra forte', '1'),
         ('Shift + segurar direito', 'Carrega um cogubrilho gigante; solte para lançar', '3')])]),
    ('magicblocks:sculk_block', 'O poder do Warden na sua mão.',
     [crafting('sculk_block'), table([
         ('Bater', 'Estrondo sônico: 12 de dano que ignora armadura', '1'),
         ('Segurar direito', 'Mostra o contorno das criaturas (só para você)', '—'),
         ('Shift + segurar direito', 'Invoca um Warden aliado (some se o bloco sair do inventário)', '5'),
         ('Shift + bater', 'Escuridão nos outros, você fica invisível e o sculk se espalha', '3'),
         ('Na segunda mão', 'Matar uma criatura espalha sculk onde ela morreu', '—')])]),
    ('magicblocks:leaf_block', 'Cura e proteção. Combine com qualquer folha, verruga do Nether ou cogumelo para mudar a aparência (o muro de troncos muda junto).',
     [crafting('leaf_block'), table([
         ('Segurar direito', 'Cura quem você olha (ou você)', '1 a cada 5s'),
         ('Shift + segurar direito', 'Área de cura 5x5 cercada por um muro de troncos', '2 a cada 5s'),
         ('Bater', 'Folha que causa Lentidão III (e age como farinha de osso)', '—')])]),
    ('magicblocks:gilded_block', 'O Bloco de Blackstone Dourado.',
     [crafting('gilded_block'), table([
         ('Segurar direito', 'Restaura a fome com muita saturação', '1 por uso'),
         ('Shift + segurar direito', 'Forma dourada: Resistência II, +5 corações, Regeneração e Resistência ao Fogo', '1 a cada 10s'),
         ('No inventário', 'Ferramentas e armaduras viram de ouro; espada de ouro dá 15 de dano', '—'),
         ('Na segunda mão', 'Machado de ouro 10, armadura de ouro = netherita +1, dobro de durabilidade', '—')])]),
    ('magicblocks:spawner_block', 'Invoca aliados. Combine com uma tinta para mudar a cor do concreto que gira dentro dele.',
     [crafting('spawner_block'), table([
         ('Bater olhando uma criatura', 'Marca o alvo das invocações', '—'),
         ('Direito', 'Cabeça de esqueleto que invoca um esqueleto', '1'),
         ('Shift + bater', 'Cabeça de zumbi que invoca um zumbi', '1'),
         ('Shift + direito', 'Esqueleto campeão com cópia da sua armadura e da sua arma', '3')]),
      '<p class="tip">Máximo de 8 invocações, que duram 90 segundos.</p>']),
    ('magicblocks:chest_block', 'Um armazenamento mágico de 54 espaços. Não gasta mana. Funciona em baús, baús com armadilha, barris, caixas de shulker e ejetores. Combine com um recipiente para mudar a aparência (shulkers mantêm a cor).',
     [crafting('chest_block'), table([
         ('Bater num recipiente', 'Guarda tudo o que tem nele', '—'),
         ('Shift + bater num recipiente', 'Despeja tudo o que está guardado', '—'),
         ('Shift + direito num recipiente', 'Despeja só os itens que ele já tem', '—'),
         ('Direito (fora de recipiente)', 'Abre o armazenamento', '—')])]),
    ('magicblocks:void_block', 'O poder do nada. Em qualquer mão dá um voo instável (nunca fica parado no ar).',
     [crafting('void_block'), table([
         ('Segurar direito', 'Buraco negro sobre a cabeça que puxa tudo e explode ao soltar', '—'),
         ('Shift + segurar direito', 'Lança o buraco negro, arrastando criaturas e corrompendo blocos', '—'),
         ('Bater', 'Projétil que corrompe os blocos atingidos', '—'),
         ('Shift + bater', 'Agarra uma criatura; ela segue a sua mira. Bata de novo para arremessar', '—')]),
      '<p class="tip">Blocos corrompidos ficam intangíveis por 15 segundos e depois voltam ao normal.</p>']),
    ('magicblocks:water_block', 'Domínio da água. Na mão: Respiração Aquática e voo igual ao do criativo enquanto estiver embaixo da água.',
     [crafting('water_block'), table([
         ('Bater', 'Bola de água: a cabeça do atingido fica num bloco de água por 20s', '1'),
         ('Segurar direito', 'Jato de água (17 blocos) que empurra e apaga fogo', '1 a cada 10s')])]),
    ('magicblocks:ice_block', 'Domínio do gelo. Em qualquer mão: desliza em todos os blocos como no gelo e anda sobre água e lava.',
     [infuser('magicblocks:water_block', 'minecraft:blue_ice', 'magicblocks:ice_block'), table([
         ('Segurar direito', 'Jato congelante que deixa lento', '1 a cada 5s'),
         ('Shift + direito', 'Tempestade de neve (10s): atrapalha a visão dos outros, deixa lento e congela', '3')])]),
]

ARMAS = [
    ('magicblocks:manilium_chestplate', 'A armadura de Manilium tem a proteção da netherita e pode ficar ainda mais forte.',
     ['<div class="pieces">%s</div>' % ''.join(slot('magicblocks:manilium_' + p) for p in ['helmet', 'chestplate', 'leggings', 'boots']),
      smithing('minecraft:netherite_chestplate', 'magicblocks:manilium_chestplate'),
      '<h4>Fortalecer</h4><p>No Nature Infuser, coloque a peça na entrada e uma <b>Orbe de Mana</b> na alimentação: +1 de defesa por orbe, até <b>+5</b> em cada peça.</p>',
      infuser('magicblocks:manilium_chestplate', 'magicblocks:mana_orb', 'magicblocks:manilium_chestplate'),
      '<h4>Pintar</h4><p>Junte a peça com tintas na bancada (como a armadura de couro). Só os detalhes azul-claros mudam de cor.</p>',
      '<h4>Conversor de Almas</h4><p>Qualquer peitoral pode receber um Conversor de Almas embutido no Nature Infuser.</p>']),
    ('magicblocks:manilium_sword', 'Uma espada que cresce com você e carrega um Bloco Mágico na guarda.',
     [smithing('minecraft:netherite_sword', 'magicblocks:manilium_sword'),
      '<h4>Dano sem limite</h4><p>Cada <b>Orbe de Mana</b> infundida no Nature Infuser dá <b>+1 de dano</b>, sem limite.</p>',
      infuser('magicblocks:manilium_sword', 'magicblocks:mana_orb', 'magicblocks:manilium_sword'),
      '<h4>Bloco na guarda</h4><p>Coloque a espada vazia na entrada e um <b>Bloco Mágico</b> na alimentação: o bloco aparece na guarda e a espada passa a usar todas as habilidades dele, além de cortar normalmente. Para tirar o bloco, coloque a espada sozinha na bancada.</p>',
      infuser('magicblocks:manilium_sword', 'magicblocks:fire_block', 'magicblocks:manilium_sword'),
      '<h4>Pintar</h4><p>Como a armadura: espada + tintas na bancada muda a cor dos detalhes.</p>']),
]

PAGES = [
    ('recursos', 'Recursos', 'Materiais, essências e itens úteis.', RECURSOS),
    ('blocos', 'Blocos', 'Blocos que você coloca no mundo.', BLOCOS),
    ('blocos-magicos', 'Blocos Mágicos', 'Blocos que flutuam na mão e dão poderes elementais.', MAGICOS),
    ('armas-e-armaduras', 'Armas e Armaduras', 'O equipamento de Manilium.', ARMAS),
]

# ===================================================================== html

SUPPORT = 'https://livepix.gg/newgswolf101'


def anchor(item_id):
    return item_id.split(':')[1].replace('_', '-')


def display_name(item_id):
    if item_id == 'magicblocks:manilium_chestplate':
        return 'Armadura de Manilium'
    if item_id == 'magicblocks:nature_workbench':
        return 'Nature Infuser'
    return name(item_id)


def topbar(active):
    tabs = ''.join('<a href="%s.html"%s>%s</a>' % (slug, ' class="on"' if slug == active else '', title)
                   for slug, title, _, _ in PAGES)
    return ('<header class="top"><a class="brand" href="index.html"><img src="img/logo.png" alt="">Magic &amp; Blocks <small>wiki</small></a>'
            '<nav class="tabs">%s</nav><a class="btn small" href="%s" target="_blank" rel="noopener">&#10084; Apoiar</a></header>') % (tabs, SUPPORT)


def page(title, body, active=''):
    return ('<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>%s — Magic &amp; Blocks Wiki</title><link rel="icon" href="img/logo.png">'
            '<link rel="preconnect" href="https://fonts.googleapis.com">'
            '<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&family=Nunito:wght@400;700;900&display=swap" rel="stylesheet">'
            '<link rel="stylesheet" href="style.css"></head><body>%s%s'
            '<footer>Magic &amp; Blocks — mod para Minecraft 1.20.1 (Forge). Minecraft é marca da Mojang; este mod não é oficial. '
            '<a href="%s" target="_blank" rel="noopener">Apoie o mod</a>.</footer>'
            '<script src="wiki.js"></script></body></html>') % (html.escape(title), topbar(active), body, SUPPORT)


def category_page(slug, title, subtitle, entries):
    side = ''.join('<a href="#%s"><img src="%s" alt="">%s</a>' % (anchor(i), icon(i), html.escape(display_name(i)))
                   for i, _, _ in entries)
    cards = ''
    for item_id, intro, extras in entries:
        cards += ('<article class="entry" id="%s" data-name="%s"><div class="head"><span class="slot big"><img src="%s" alt=""></span>'
                  '<div><h3>%s</h3><p>%s</p></div></div>%s</article>') % (
            anchor(item_id), html.escape(display_name(item_id).lower()), icon(item_id), html.escape(display_name(item_id)),
            intro, ''.join(extras))
    extra_top = ''
    if slug == 'blocos-magicos':
        extra_top = ('<div class="callout"><b>Mana:</b> você tem 10 de mana (o orbe entre a vida e a fome), que recupera 1 a cada '
                     '2 minutos. Cada poder gasta um pouco (veja a coluna "Mana"). Sem mana, o '
                     '<a href="recursos.html#soul-converter">Conversor de Almas</a> paga com XP.</div>')
    body = ('<div class="layout"><aside class="side"><input id="busca" type="search" placeholder="Buscar..." aria-label="Buscar">'
            '<div class="side-list">%s</div></aside><main><h1>%s</h1><p class="sub">%s</p>%s%s</main></div>') % (
        side, title, subtitle, extra_top, cards)
    return page(title, body, slug)


def home():
    cards = ''
    for slug, title, sub, entries in PAGES:
        icons = ''.join('<img src="%s" alt="">' % icon(i) for i, _, _ in entries[:5])
        cards += '<a class="topic" href="%s.html"><div class="icons">%s</div><h3>%s</h3><p>%s</p><span>%d páginas &rarr;</span></a>' % (
            slug, icons, title, sub, len(entries))
    body = ('<main class="home"><img class="logo" src="img/logo.png" alt="Magic & Blocks">'
            '<p class="lead">A wiki oficial do <b>Magic &amp; Blocks</b>: blocos mágicos que flutuam na mão, mana, o Nature Infuser, '
            'equipamento de Manilium, magos e muito mais para Minecraft 1.20.1 (Forge).</p>'
            '<div class="pills"><span>Minecraft 1.20.1</span><span>Forge 47</span><span>Curios (opcional)</span><span>PT-BR / EN</span></div>'
            '<div class="topics">%s</div>'
            '<section class="support"><h2>Apoie o mod</h2><p>Curtiu? Seu apoio ajuda a criar novos blocos, criaturas e atualizações.</p>'
            '<a class="btn" href="%s" target="_blank" rel="noopener">&#10084; Apoiar pelo LivePix</a></section></main>') % (cards, SUPPORT)
    return page('Início', body)


def write(fname, text):
    with open(os.path.join(SITE, fname), 'w', encoding='utf-8') as f:
        f.write(text)
    print('ok', fname)


write('index.html', home())
for slug, title, sub, entries in PAGES:
    write(slug + '.html', category_page(slug, title, sub, entries))
