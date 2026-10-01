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
GAME_ICONS = os.path.join(SITE, 'img', 'game_icons')
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
    'magicblocks:nature_harvester': lambda: iso(mtex('block/nature_harvester_top'), mtex('block/nature_harvester_side')),
    'magicblocks:nature_breeder': lambda: iso(mtex('block/nature_breeder_top'), mtex('block/nature_breeder_side')),
    'magicblocks:mana_distiller': lambda: iso(mtex('block/mana_distiller_top'), mtex('block/mana_distiller_side')),
    'magicblocks:nature_shield': lambda: iso(mtex('block/nature_shield_top'), mtex('block/nature_shield_side')),
    'magicblocks:soul_generator': lambda: iso(mtex('block/soul_generator_top'), mtex('block/soul_generator_side')),
    'magicblocks:lunar_pillar': lambda: iso(mtex('block/lunar_pillar_top'), mtex('block/lunar_pillar_side')),
    'magicblocks:lightning_catcher': lambda: iso(mtex('block/lightning_catcher_top'), mtex('block/lightning_catcher_side')),
    'magicblocks:nature_furnace': lambda: iso(mtex('block/nature_furnace_top'), mtex('block/nature_furnace_front_on'), mtex('block/nature_furnace_side')),
    'minecraft:iron_hoe': lambda: flat(vtex('item/iron_hoe')),
    'minecraft:lead': lambda: flat(vtex('item/lead')),
    'minecraft:furnace': lambda: iso(vtex('block/furnace_top'), vtex('block/furnace_front'), vtex('block/furnace_side')),
    'minecraft:brewing_stand': lambda: flat(vtex('item/brewing_stand')),
    'minecraft:soul_lantern': lambda: flat(vtex('item/soul_lantern')),
    'minecraft:soul_soil': lambda: iso(vtex('block/soul_soil'), vtex('block/soul_soil')),
    'minecraft:amethyst_block': lambda: iso(vtex('block/amethyst_block'), vtex('block/amethyst_block')),
    'minecraft:copper_block': lambda: iso(vtex('block/copper_block'), vtex('block/copper_block')),
    'minecraft:lantern': lambda: flat(vtex('item/lantern')),
    'minecraft:clock': lambda: flat(vtex('item/clock_00')),
    'minecraft:shield': lambda: flat(Image.open(io.BytesIO(jar.read('assets/minecraft/textures/entity/shield_base_nopattern.png'))).convert('RGBA').crop((1, 1, 13, 23)).resize((16, 16))),
    'minecraft:glass': lambda: iso(vtex('block/glass'), vtex('block/glass')),
    'minecraft:lapis_block': lambda: iso(vtex('block/lapis_block'), vtex('block/lapis_block')),
    'minecraft:torch': lambda: flat(vtex('block/torch')),
    'magicblocks:quarry_marker': lambda: flat(mtex('block/quarry_marker')),
    'magicblocks:nature_battery': lambda: iso(mtex('block/nature_battery_fluid'), mtex('block/nature_battery')),
    'magicblocks:mastery_table': lambda: iso(mtex('block/mastery_table_top'), mtex('block/mastery_table_side')),
    'minecraft:polished_deepslate': lambda: iso(vtex('block/polished_deepslate'), vtex('block/polished_deepslate')),
    'magicblocks:elemental_helmet': lambda: flat(mtex('item/elemental_helmet_fire')),
    'magicblocks:elemental_chestplate': lambda: flat(mtex('item/elemental_chestplate_none')),
    'magicblocks:elemental_leggings': lambda: flat(mtex('item/elemental_leggings_ice')),
    'magicblocks:elemental_boots': lambda: flat(mtex('item/elemental_boots_thunder')),
    '#minecraft:planks': lambda: iso(vtex('block/oak_planks'), vtex('block/oak_planks')),
    '#minecraft:logs': lambda: iso(vtex('block/oak_log_top'), vtex('block/oak_log')),
    'minecraft:tnt': lambda: iso(vtex('block/tnt_top'), vtex('block/tnt_side')),
    'magicblocks:tnt_block': lambda: iso(vtex('block/tnt_top'), vtex('block/tnt_side')),
    'magicblocks:nature_charger': lambda: iso(mtex('block/nature_charger_top'), mtex('block/nature_charger_side')),
    'magicblocks:slime_block': lambda: iso(tint(vtex('block/slime_block'), (124, 203, 99)), tint(vtex('block/slime_block'), (124, 203, 99))),
    'minecraft:enchanting_table': lambda: iso(vtex('block/enchanting_table_top'), vtex('block/enchanting_table_side')),
    'minecraft:crying_obsidian': lambda: iso(vtex('block/crying_obsidian'), vtex('block/crying_obsidian')),
    'minecraft:anvil': lambda: iso(vtex('block/anvil_top'), vtex('block/anvil')),
    'magicblocks:nature_mana_well': lambda: iso(mtex('block/nature_mana_well_top'), mtex('block/nature_mana_well_side')),
    'minecraft:emerald_block': lambda: iso(vtex('block/emerald_block'), vtex('block/emerald_block')),
    'minecraft:stone_bricks': lambda: iso(vtex('block/stone_bricks'), vtex('block/stone_bricks')),
    'minecraft:sticky_piston': lambda: iso(vtex('block/piston_top_sticky'), vtex('block/piston_side')),
    'magicblocks:enchant_upgrader': lambda: iso(mtex('block/enchant_upgrader_top'), mtex('block/enchant_upgrader_side')),
    'magicblocks:redstone_block': lambda: iso(vtex('block/redstone_block'), vtex('block/redstone_block')),
    'magicblocks:nature_restorer': lambda: iso(mtex('block/nature_restorer_top'), mtex('block/nature_restorer_side')),
    'magicblocks:ruin_pedestal': lambda: iso(mtex('block/ruin_pedestal_top_fire'), mtex('block/ruin_pedestal_side')),
    'magicblocks:nature_grower': lambda: iso(mtex('block/nature_grower_top'), mtex('block/nature_grower_side')),
    'magicblocks:nature_cable': lambda: iso(mtex('block/nature_cable_core'), mtex('block/nature_cable')),
    'minecraft:diamond_block': lambda: iso(vtex('block/diamond_block'), vtex('block/diamond_block')),
    'minecraft:bone_block': lambda: iso(vtex('block/bone_block_top'), vtex('block/bone_block_side')),
    'magicblocks:vision_potion': lambda: flat(layered(vtex('item/potion'), vtex('item/potion_overlay'), (63, 169, 255))),
    'minecraft:potion': lambda: flat(layered(vtex('item/potion'), vtex('item/potion_overlay'), (56, 93, 198))),
    'minecraft:enchanted_golden_apple': lambda: flat(vtex('item/golden_apple')),
    'magicblocks:fire_spirit_spawn_egg': lambda: flat(layered(tint(vtex('item/spawn_egg'), (138, 42, 10)), vtex('item/spawn_egg_overlay'), (255, 176, 46))),
    'magicblocks:arcane_sentinel_spawn_egg': lambda: flat(layered(tint(vtex('item/spawn_egg'), (43, 36, 56)), vtex('item/spawn_egg_overlay'), (180, 92, 255))),
    'magicblocks:mana_log': lambda: iso(mtex('block/mana_log_top'), mtex('block/mana_log')),
    'magicblocks:mana_planks': lambda: iso(mtex('block/mana_planks'), mtex('block/mana_planks')),
    'magicblocks:mana_leaves': lambda: iso(mtex('block/mana_leaves'), mtex('block/mana_leaves')),
    'magicblocks:mana_sapling': lambda: flat(mtex('block/mana_sapling')),
    'magicblocks:ritual_altar': lambda: iso(mtex('block/ritual_altar_top'), mtex('block/ritual_altar_side')),
    'magicblocks:nature_quarry': lambda: iso(mtex('block/nature_quarry_top'), mtex('block/nature_quarry_side')),
    'minecraft:sunflower': lambda: flat(vtex('block/sunflower_front')),
    'minecraft:oak_sapling': lambda: flat(vtex('block/oak_sapling')),
    'minecraft:lightning_rod': lambda: flat(vtex('block/lightning_rod')),
    'minecraft:polished_blackstone_bricks': lambda: iso(vtex('block/polished_blackstone_bricks'), vtex('block/polished_blackstone_bricks')),
    'minecraft:hopper': lambda: flat(vtex('item/hopper')),
    'minecraft:zombie_spawn_egg': lambda: flat(layered(tint(vtex('item/spawn_egg'), (0, 175, 175)), vtex('item/spawn_egg_overlay'), (121, 156, 101))),
}
for piece in ['helmet', 'chestplate', 'leggings', 'boots']:
    ICON_BUILDERS['magicblocks:manilium_' + piece] = (lambda p: lambda: flat(layered(
        mtex('item/manilium_' + p), mtex('item/manilium_%s_overlay' % p), CYAN)))(piece)
for block in ['iron_block', 'obsidian', 'ice', 'sponge', 'moss_block', 'gold_block', 'smooth_stone', 'gilded_blackstone',
              'blue_ice', 'grass_block', 'spawner', 'beehive', 'redstone_block', 'slime_block']:
    if block == 'grass_block':
        ICON_BUILDERS['minecraft:grass_block'] = lambda: iso(tint(vtex('block/grass_block_top'), (124, 189, 107)),
                                                             vtex('block/grass_block_side'))
    elif block == 'beehive':
        ICON_BUILDERS['minecraft:beehive'] = lambda: iso(vtex('block/beehive_end'), vtex('block/beehive_front'), vtex('block/beehive_side'))
    else:
        ICON_BUILDERS['minecraft:' + block] = (lambda b: lambda: iso(vtex('block/' + b), vtex('block/' + b)))(block)
for _b in ['fire', 'leaf', 'gilded', 'spawner', 'water', 'ice', 'tnt']:
    if 'magicblocks:%s_block' % _b in ICON_BUILDERS:
        def _corrupt(base=ICON_BUILDERS['magicblocks:%s_block' % _b]):
            img = base().convert('RGBA')
            px = img.load()
            for yy in range(img.height):
                for xx in range(img.width):
                    r, g, b, a = px[xx, yy]
                    px[xx, yy] = (min(255, int(r * 0.55 + 40)), int(g * 0.35), int(b * 0.45), a)
            return img
        ICON_BUILDERS['magicblocks:corrupted_%s_block' % _b] = _corrupt

# Itens de Manilium: a borda (camada cosmica no jogo) volta para o icone em roxo-cosmico
def _with_border(name, base):
    def build():
        img = base().convert('RGBA')
        border = tint(mtex('item/%s_border' % name), (150, 90, 255)).convert('RGBA')
        if border.size != img.size:
            border = border.resize(img.size, Image.NEAREST)
        img.alpha_composite(border)
        return img
    return build


for _n in ['manilium_sword', 'manilium_helmet', 'manilium_chestplate', 'manilium_leggings', 'manilium_boots', 'manilium_ingot']:
    _base = ICON_BUILDERS.get('magicblocks:' + _n, (lambda n: lambda: flat(mtex('item/' + n)))(_n))
    ICON_BUILDERS['magicblocks:' + _n] = _with_border(_n, _base)



def icon(item_id):
    """Caminho (relativo ao site) do icone do item; gera o arquivo na primeira vez."""
    if item_id.endswith('_shulker_box'):
        item_id = 'minecraft:shulker_box'
    name = item_id.replace('#', 'tag_').replace(':', '_')
    path = os.path.join(ICONS, name + '.png')
    # icone tirado do proprio jogo (DevIconExport: modelos 3D, cores, tudo igual ao inventario); sempre atualizado
    game = os.path.join(GAME_ICONS, name + '.png')
    if not item_id.startswith('#') and os.path.exists(game):
        Image.open(game).convert('RGBA').save(path)
        return 'img/icons/%s.png' % name
    if True:
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
    'minecraft:heart_of_the_sea': 'Coração do Mar', 'minecraft:gunpowder': 'Pólvora', 'minecraft:tnt': 'TNT',
    'minecraft:diamond_block': 'Bloco de Diamante', 'minecraft:potion': 'Garrafa de Água', '#minecraft:logs': 'Tronco (qualquer)',
    'magicblocks:vision_potion': 'Poções de Visão de Minério',
    'minecraft:slime_block': 'Bloco de Slime (vanilla)', 'minecraft:diamond_axe': 'Machado de Diamante', 'minecraft:diamond_shovel': 'Pá de Diamante',
    'minecraft:diamond_pickaxe': 'Picareta de Diamante', 'minecraft:diamond_hoe': 'Enxada de Diamante', 'minecraft:shield': 'Escudo', 'minecraft:slime_ball': 'Bola de Slime',
    'minecraft:golden_apple': 'Maçã Dourada', 'minecraft:emerald_block': 'Bloco de Esmeralda', 'minecraft:stone_bricks': 'Tijolos de Pedra', 'minecraft:anvil': 'Bigorna', 'minecraft:iron_block': 'Bloco de Ferro', 'minecraft:emerald': 'Esmeralda', 'minecraft:enchanting_table': 'Mesa de Encantamento', 'minecraft:crying_obsidian': 'Obsidiana Chorona', 'minecraft:comparator': 'Comparador', 'minecraft:sticky_piston': 'Pistão Grudento', 'minecraft:redstone_block': 'Bloco de Redstone',
    'minecraft:bone_block': 'Bloco de Osso', 'minecraft:emerald': 'Esmeralda', 'minecraft:wheat_seeds': 'Sementes de Trigo',
    'minecraft:egg': 'Ovo','minecraft:leather': 'Couro','minecraft:blue_ice': 'Gelo Azul', 'minecraft:netherite_sword': 'Espada de Netherita',
    'minecraft:netherite_helmet': 'Capacete de Netherita', 'minecraft:netherite_chestplate': 'Peitoral de Netherita',
    'minecraft:netherite_leggings': 'Calças de Netherita', 'minecraft:netherite_boots': 'Botas de Netherita',
    'minecraft:netherite_upgrade_smithing_template': 'Molde de Melhoria de Netherita', 'minecraft:spawner': 'Spawner',
    'minecraft:grass_block': 'Bloco de Grama', 'minecraft:redstone_block': 'Bloco de Redstone', 'minecraft:beehive': 'Colmeia', '#minecraft:leaves': 'Folhas (qualquer)',
    '#minecraft:flowers': 'Flor (qualquer)', '#minecraft:planks': 'Tábuas (qualquer)', 'minecraft:stick': 'Graveto', 'minecraft:iron_hoe': 'Enxada de Ferro', 'minecraft:lead': 'Laço', 'minecraft:furnace': 'Fornalha', 'minecraft:brewing_stand': 'Suporte de Poções', 'minecraft:soul_lantern': 'Lanterna das Almas', 'minecraft:soul_soil': 'Terra das Almas', 'minecraft:amethyst_block': 'Bloco de Ametista', 'minecraft:copper_block': 'Bloco de Cobre', 'minecraft:lantern': 'Lanterna', 'minecraft:clock': 'Relógio', 'minecraft:paper': 'Papel', 'minecraft:gold_nugget': 'Pepita de Ouro', 'minecraft:string': 'Linha', 'minecraft:copper_ingot': 'Barra de Cobre', 'minecraft:wheat': 'Trigo', 'minecraft:iron_ingot': 'Barra de Ferro', 'minecraft:oak_sapling': 'Muda (qualquer)', 'minecraft:sunflower': 'Girassol', 'minecraft:lightning_rod': 'Para-raios', 'minecraft:gunpowder': 'Pólvora', 'minecraft:prismarine_crystals': 'Cristais de Prismarinho', 'minecraft:glowstone_dust': 'Pó de Pedra Luminosa', 'minecraft:amethyst_shard': 'Fragmento de Ametista', 'minecraft:ender_pearl': 'Pérola do Ender', 'minecraft:hopper': 'Funil', 'minecraft:polished_blackstone_bricks': 'Tijolos de Blackstone Polida',
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
    ('magicblocks:unstable_shard', 'Um pedaço de Diamante Instável. Junte 4 na bancada para formar um Diamante Instável inteiro: um jeito de conseguir diamantes instáveis lutando, sem precisar do Nature Infuser.',
     [note('Cai dos <b>Espíritos Elementais</b> (8%, mais com Pilhagem), da <b>Sentinela Arcana</b> (2 a 4) e do baú da <b>Torre Arcana</b>.'), crafting('elemental_diamond_from_shards')]),
    ('magicblocks:mana_fruit', 'Cai das folhas da Árvore de Mana (6%, mais com Fortuna). Comer devolve <b>2 de mana</b> na hora (e mata a fome como uma maçã).',
     [note('Quebre as Folhas de Mana.')]),
    ('magicblocks:teleport_crystal', '<b>Shift + direito</b> marca o lugar onde você está. Depois, <b>segure direito</b> por 1,5s para voltar até lá, gastando mana: 1 + 1 a cada 250 blocos (no máximo 8). Só funciona na mesma dimensão; recarga de 5s.',
     [crafting('teleport_crystal'), '<h4>Cristal de Teleporte Estabilizado</h4><p>Também viaja <b>entre dimensões</b> (Nether, End...), por +2 de mana.</p>', crafting('stable_teleport_crystal')]),
    ('magicblocks:lunar_fragment', 'Um pedaço da Lua Roxa. Faz o Cristal de Teleporte Estabilizado e o Ritual do Conhecimento.',
     [note('Monstros da <b>Lua Roxa</b> soltam (35%); o Arauto da Lua Roxa solta 4 a 6.')]),
    ('magicblocks:apprentice_wand', 'A primeira arma mágica (modelo 3D com cristal que brilha): lança um <b>Míssil Arcano</b>, uma esfera de energia roxa com cauda de luz, de 4 de dano mágico por 1 de mana. Ele <b>curva de leve até o monstro mais perto</b> na frente (recarga 0,6s, 250 usos). Feita com graveto, ametista e lápis.',
     [crafting('apprentice_wand')]),
    ('magicblocks:mana_lantern', 'Lanterna 3D de vidro com moldura dourada e um cristal de mana brilhando dentro; na mão fica <b>pendurada pela alça</b>, na principal ou na secundária. Na mão (qualquer uma) ou <b>no cinto do Curios</b> (fica pendurada na cintura, balançando) <b>ilumina em volta de você</b> por onde anda e faz os <b>Minérios de Mana</b> a até 10 blocos brilharem (só você vê).',
     [crafting('mana_lantern')]),
    ('magicblocks:return_scroll', 'Segure o botão direito por <b>5 segundos parado</b> para voltar à sua <b>cama</b> (ou ao spawn do mundo). Se você se mexer, cancela. Uso único; a receita faz 2.',
     [crafting('return_scroll')]),
    ('magicblocks:lightning_hook', 'Gancho 3D de cobre com bobina que brilha. Direito: um raio sai da mão e <b>puxa você até onde a mira acertar</b> (até 32 blocos). Custa 1 de mana + 1 a cada 16 blocos, e você não leva dano de queda logo depois. Recarga 1,5s.',
     [crafting('lightning_hook')]),
    ('magicblocks:arcane_crown', 'Coroa 3D de ouro com pontas e joias (vestida aparece na cabeça). Capacete de fim de jogo (3 de armadura, igual ao de netherita, e 3 de resistência): todas as <b>recargas de itens passam 20% mais rápido</b> e, no <b>canto de cima da tela</b> (longe da mira), aparecem o <b>nome, a vida e o elemento</b> da criatura que você olha (até 32 blocos).',
     [crafting('arcane_crown')]),
    ('magicblocks:temporal_orb', 'Estilo "Time in a Bottle", mas com mana: clique num bloco que trabalha (fornalha, máquina, muda, plantação, spawner...) para <b>acelerar o tempo dele por 30s</b>. Clicar de novo no <b>mesmo</b> bloco enquanto está acelerado sobe a velocidade e renova os 30s. Só acelera um bloco por vez; para acelerar <b>outro</b> bloco, espere 2 minutos. <b>Não acelera fontes de energia</b> (geradores, Chargers e baterias). O bloco acelerado ganha <b>anéis girando</b> em volta (verde 2x, ciano 4x, azul 16x, roxo 64x, dourado 128x; giram mais rápido quanto maior a velocidade), um anel branco que diminui conforme o tempo acaba e o texto <b>x16</b> com os segundos que faltam em cima.',
     [crafting('temporal_orb'), table([('2x', '1'), ('4x', '+1'), ('16x', '+2'), ('64x', '+3'), ('128x', '+5')], head=('Velocidade', 'Mana'))]),
    ('magicblocks:manilium_ingot', 'Netherita reforçada com mana. Mais escura, com veios azul-claros. Base de todo o equipamento de Manilium.',
     [crafting('manilium_ingot')]),
    ('magicblocks:manilium_block', 'Guarda 9 Barras de Manilium. Feito como o bloco de slime: uma <b>casca translúcida de galáxia</b> que se mexe e brilha no escuro, com um <b>núcleo grande de Manilium negro</b> no meio. Serve de base de <b>sinalizador</b> (e a barra pode pagar o sinalizador). Precisa de picareta de diamante.',
     [crafting('manilium_block'), crafting('manilium_ingot_from_block')]),
    ('magicblocks:manilium_upgrade_smithing_template', 'Molde da mesa de ferraria que transforma equipamento de netherita em Manilium.',
     [infuser('minecraft:netherite_upgrade_smithing_template', 'magicblocks:mana_essence', 'magicblocks:manilium_upgrade_smithing_template')]),
    ('magicblocks:soul_converter', 'Quando falta mana, paga a diferença com o seu XP: <b>10 pontos de XP = 1 de mana</b>. Funciona no inventário, no slot de amuleto do <b>Curios</b> (aparece no peito, estilo reator) ou embutido em qualquer peitoral.',
     [crafting('soul_converter'), infuser('minecraft:netherite_chestplate', 'magicblocks:soul_converter', 'minecraft:netherite_chestplate').replace(
         '<div class="hint">', '<div class="hint">qualquer peitoral recebe o conversor embutido &middot; ')]),
    ('magicblocks:unstable_condensed_mana_orb', 'Item de combate que guarda <b>10 de mana extra</b>. Não precisa segurar: basta estar no inventário, e ela é gasta sozinha quando a sua mana acaba (antes do XP do Conversor de Almas). Quando esvazia, <b>se desfaz</b>.',
     [crafting('unstable_condensed_mana_orb')]),
    ('magicblocks:stable_condensed_mana_orb', 'A versão estabilizada: também guarda <b>10 de mana</b> usada direto do inventário (as instáveis são gastas primeiro), mas <b>não quebra</b>. Jogue-a no chão em cima de um <a href="#nature-mana-well">Poço de Mana</a> com energia para recarregar: +1 de mana por segundo, 3.000 de energia cada.',
     [crafting('stable_condensed_mana_orb')]),
    ('magicblocks:soul_collector', 'Clique com o botão direito em <b>qualquer criatura</b> (do jogo, deste mod ou de outros mods) para guardar o DNA dela. Cada coletor guarda <b>um só</b> DNA. Depois junte o coletor com um ovo e um frasco de XP em qualquer bancada para criar o ovo gerador daquela criatura. Se ela não tiver ovo próprio, sai um <b>Ovo de Alma</b>, que funciona igual. O coletor volta para você.',
     [crafting('soul_collector'), '<div class="recipe"><div class="label">Ovo gerador</div><div class="craft">%s<span class="plus">+</span>%s<span class="plus">+</span>%s<span class="arrow">&#10140;</span><span class="slot big" title="Ovo gerador da criatura"><img src="%s" alt=""></span></div></div>' % (
         slot('magicblocks:soul_collector'), slot('minecraft:egg'), slot('minecraft:experience_bottle'), icon('minecraft:zombie_spawn_egg'))]),
    ('magicblocks:soul_egg', 'Ovo gerador feito pelo Coletor da Alma para criaturas que não têm ovo próprio. Funciona como um ovo gerador comum, inclusive para escolher a criatura do Spawner de Manilium.',
     [note('Coletor da Alma com o DNA de uma criatura sem ovo + ovo + frasco de XP.')]),
    ('magicblocks:broken_spawner', 'O que sobra de um spawner quebrado. Pode ser consertado.',
     [note('Quebre um <b>spawner</b> comum (fora do criativo).'), crafting('lifeless_spawner')]),
    ('magicblocks:lifeless_spawner', 'Um spawner consertado, mas ainda sem vida. Precisa de Manilium para despertar.',
     [infuser('magicblocks:lifeless_spawner', 'magicblocks:manilium_ingot', 'magicblocks:manilium_spawner')]),
    ('magicblocks:vision_potion', 'Na barra de fermentação, uma <b>garrafa de água</b> com o ingrediente vira uma poção de <b>3 minutos</b>: todos os blocos daquele minério a até 50 blocos ficam contornados e visíveis através das paredes. <b>Redstone</b> prolonga para 8 minutos, <b>pólvora</b> deixa arremessável e <b>bafo do dragão</b>, persistente. Todas aparecem na aba criativa do mod.',
     [table([('<img class="mini" src="%s">Orbe de Mana' % icon('magicblocks:mana_orb'), 'Minério de Mana', '3 min'),
             ('<img class="mini" src="%s">Bloco de Diamante' % icon('minecraft:diamond_block'), 'Diamante', '3 min'),
             ('<img class="mini" src="%s">Bloco de Ferro' % icon('minecraft:iron_block'), 'Ferro', '3 min'),
             ('<img class="mini" src="%s">Bloco de Ouro' % icon('minecraft:gold_block'), 'Ouro', '3 min'),
             ('<img class="mini" src="%s">Barra de Netherita' % icon('minecraft:netherite_ingot'), 'Detritos Ancestrais', '3 min')],
            head=('Ingrediente', 'Minério visível', 'Duração'))]),
    ('magicblocks:mage_cloth', 'Couro reforçado com ferro e mana. Material do Talismã dos Blocos.',
     [crafting('mage_cloth')]),
    ('magicblocks:guide_book', 'O livro com as receitas e explicações de tudo. Você ganha um ao entrar no mundo pela primeira vez.',
     [crafting('guide_book')]),
]

BLOCOS = [
    ('magicblocks:mana_ore', 'Minério raro que aparece sozinho nas profundezas (camada -64 a -50). Precisa de picareta de ferro; com picareta de diamante solta Orbes de Mana (Fortuna aumenta). Com Toque Suave, solta o próprio bloco.',
     [note('Encontrado nas profundezas do mundo.')]),
    ('magicblocks:nature_workbench', 'Transforma itens usando <b>energia de natureza</b>: ligue com <b>Cabos de Natureza</b> num <b>Nature Charger</b> ou numa bateria. <b>Sem energia não funciona</b> (a tela mostra "Sem energia!"). Gasta 60 de energia por tick de trabalho (guarda 30.000). Entrada em cima, alimentação embaixo (o catalisador da infusão) e saída à direita. Funis: entrada por cima, alimentação pelos lados, saída por baixo.',
     [crafting('nature_workbench'),
      '<h4>Bônus da natureza</h4><p>Com energia, a força base é <b>1x</b>. A natureza num raio de 5 blocos (inclusive acima e abaixo) <b>acelera</b>: cada tipo soma até um limite; terra comum não conta.</p>' +
      table([('<img class="mini" src="%s">Grama' % icon('minecraft:grass_block'), '25', '+1x'),
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
             ('Bloco de Fogo', 'Bloco de Redstone', 'Bloco de Fogo Vermelho'),
             ('Bloco de TNT', 'TNT', 'Bloco de TNT Ativo')], head=('Entrada', 'Alimentação', 'Resultado')),
      '<h4>Energia</h4><p>A barra à direita guarda energia de natureza vinda de um <a href="#nature-charger">Nature Charger</a>. O infusor <b>só trabalha com energia</b>; a natureza em volta deixa mais rápido. Sem energia ele pausa (não perde o progresso).</p>']),
    ('magicblocks:nature_charger', 'Um ninho de raízes e troncos com um <b>grande cristal verde</b> que pulsa no meio e uma copa de folhas em cima. Gera <b>energia de natureza</b> só de estar no ambiente: <b>não precisa de itens</b>, basta ter natureza (grama, flores, folhas, colmeias...) <b>2 blocos para cada lado</b> (um cubo de 5x5x5 com ele no meio; 25 blocos de grama já dão o máximo da grama). As áreas de dois carregadores <b>não podem se sobrepor</b>, mas podem <b>encostar</b>: 5 blocos de centro a centro (X X C X X X X C X X). Segurando um Charger, as áreas dos que estão por perto aparecem em verde e a do novo, onde você vai colocar, em amarelo (vermelho se invadiria outra). Olhar para um Charger, Infuser, Grower, Poço de Mana, Minerador ou máquina nova também mostra a área dele. Quanto mais natureza, mais rápido gera (o cristal no meio da tela acende enquanto gera). Guarda até 20.000. A energia vai pelos Cabos de Natureza (ou direto para um infusor encostado).',
     ['<div class="prints"><figure><img src="img/prints/maquinas.jpg" alt="Um jardim de máquinas de natureza ligadas pelos cabos" loading="lazy"><figcaption>Um jardim de máquinas de natureza ligadas pelos cabos</figcaption></figure></div>', crafting('nature_charger'),
      '<h4>Infusor com energia</h4><p>O Nature Infuser <b>precisa de energia</b> para funcionar: com energia trabalha a <b>1x</b>, mais o bônus da natureza em volta. Gasta <b>60</b> de energia por tick de trabalho e guarda até 30.000. Sem energia ele só pausa (não perde o progresso).</p>']),
    ('magicblocks:nature_cable', 'Leva a <b>energia de natureza</b> dos Chargers, geradores (Almas, Pilar Lunar, Captador de Raios) e Baterias até as máquinas: Infuser, Grower, Minerador, Altar de Rituais, Mesa de Maestria, Aprimorador de Encantamentos, Fornalha Natural e as máquinas de natureza. Conecta sozinho em qualquer direção (até 256 cabos por rede).',
     [crafting('nature_cable')]),
    ('magicblocks:nature_grower', 'Usa a <b>energia de natureza</b> (vinda do Nature Charger pelos cabos) para <b>acelerar as plantas</b> num raio de 4 blocos: plantações, mudas, cana, cacto, bambu, fungos, flores... A cada meio segundo cada planta tem 50% de chance de crescer um passo, e às vezes ganha farinha de osso de graça. Gasta 40 de energia por tick, só quando há plantas em volta. Clique nele para ver a energia.',
     [crafting('nature_grower')]),
    ('magicblocks:enchant_upgrader', 'Uma mesa de encantamento melhorada que <b>aumenta o nível dos encantamentos</b> com MUITA energia de natureza (pelos Cabos de Natureza). Coloque um item ou livro encantado, clique no encantamento na lista e espere: o livro abre e vira as páginas enquanto trabalha. Ele continua subindo o nível enquanto houver energia.',
     [crafting('enchant_upgrader'), table([
         ('Até o máximo do Minecraft', '4.000 × nível²', '—'),
         ('Acima do máximo (até 10)', '7.000 × nível²', '1 Orbe de Mana + 1 Essência do Void por nível')], head=('Nível', 'Energia', 'Extra')),
      '<p class="tip">Leva pelo menos 20s + 10s por nível; sem energia ele pausa. Exemplo: Afiação V → VI custa 252.000 de energia. Encantamentos de 1 nível só (Remendo, Toque Suave...) não sobem.</p>']),
    ('magicblocks:nature_restorer', 'Conserta sozinho as ferramentas, armas e armaduras colocadas nos seus <b>9 espaços</b> usando energia de natureza (pelos cabos): 20 de energia por ponto de durabilidade, <b>um item por vez</b> (na ordem dos espaços). Shift + clique mostra a energia guardada.',
     [crafting('nature_restorer')]),
    ('magicblocks:nature_mana_well', 'Com energia de natureza (pelos cabos), a cada 6 segundos devolve <b>1 de mana</b> aos jogadores a até 6 blocos que não estão cheios. Custa 4.000 de energia por ponto. Também <b>recarrega as Orbes de Mana Condensada Estabilizadas</b> jogadas em cima dele: +1 de mana por segundo, 3.000 de energia cada. Clique para ver a energia.',
     [crafting('nature_mana_well')]),
    ('magicblocks:ritual_altar', 'O centro dos <b>rituais</b>. Monte 4 <b>Pedestais</b> a 3 blocos do altar (norte, sul, leste e oeste, na mesma altura) e ligue o altar à energia de natureza pelos cabos (guarda 40.000). Clique no altar com o <b>catalisador</b>, coloque os 4 itens nos pedestais (em qualquer ordem) e clique no altar de <b>mão vazia</b>. Por 5 segundos, raios de luz saem dos pedestais até o altar; no fim, os itens são gastos e um raio (sem dano) cai no altar. Shift + direito de mão vazia tira o catalisador.',
     [crafting('ritual_altar'), '<h4>Como montar</h4><ol class="steps"><li>Coloque o <b>Altar</b> e ligue-o à energia (cabos de um Charger, gerador ou bateria).</li><li>Coloque <b>4 Pedestais</b> (comuns ou Arcanos) a <b>3 blocos</b> do altar: norte, sul, leste e oeste, <b>na mesma altura</b> do altar (2 blocos vazios entre o altar e cada pedestal).</li><li>Clique no altar segurando o <b>catalisador</b> (ele fica flutuando em cima).</li><li>Clique em cada pedestal segurando um dos 4 itens do ritual (qualquer ordem).</li><li>Clique no altar de <b>mão vazia</b>. Se aparecer "nenhum ritual usa esses itens", confira os itens; "faltam pedestais" = algum pedestal fora do lugar.</li></ol><div class="prints"><figure><img src="img/prints/altar_angulo.jpg" alt="Altar com os 4 pedestais" loading="lazy"><figcaption>Altar com os 4 pedestais</figcaption></figure><figure><img src="img/prints/altar_cima.jpg" alt="Visto de cima: pedestais a 3 blocos, em cruz" loading="lazy"><figcaption>Visto de cima: pedestais a 3 blocos, em cruz</figcaption></figure><figure><img src="img/prints/altar_ritual.jpg" alt="Ritual em andamento" loading="lazy"><figcaption>Ritual em andamento</figcaption></figure></div>', table([
         ('Chuva', 'Orbe de Mana', '2 Baldes de Água + 2 Cristais de Prismarinho', '5.000', 'Chove por 10 minutos (os baldes voltam vazios)'),
         ('Céu Limpo', 'Orbe de Mana', '2 Girassóis + 2 Pó de Pedra Luminosa', '5.000', 'Para a chuva e, se for noite, pula para a manhã'),
         ('Tempestade', 'Orbe de Mana', '2 Para-raios + 2 Pólvoras', '8.000', 'Tempestade com raios por 5 minutos'),
         ('Lua Roxa', 'Olho do Ender', '2 Fragmentos de Ametista + 2 Essências de Mana', '15.000', 'Chama a Lua Roxa agora (se for noite) ou na próxima noite'),
         ('Eclipse Solar', 'Fragmento Lunar', '2 Girassóis + 2 Obsidianas', '15.000', 'Chama o Eclipse Solar agora (se for dia) ou no próximo meio-dia'),
         ('Transmutação', 'Diamante', '2 Essências de Mana + 2 Esmeraldas', '6.000', '2 Diamantes Instáveis'),
         ('Bênção', 'Maçã Dourada', 'Essência de Mana + Pó de Blaze + Pena + Açúcar', '8.000', 'Força II, Velocidade II, Regeneração e Resistência por 5 min para todos a até 12 blocos'),
         ('Conhecimento', 'Livro', '2 Fragmentos Lunares + 2 Orbes de Mana', '20.000', '<b>+1 ponto de habilidade</b> para quem começou o ritual'),
         ('Invocação do Golem', 'Um Bloco Mágico (não é gasto)', '2 Orbes de Mana + 2 Diamantes Instáveis', '20.000', 'Cria o <b>Invocador</b> do golem daquele elemento: coloque onde quiser para lutar com ele')],
         head=('Ritual', 'Catalisador (no altar)', 'Pedestais', 'Energia', 'Efeito'))]),
    ('magicblocks:nature_quarry', 'Uma máquina movida a <b>energia de natureza</b> (pelos cabos, guarda 40.000) que minera uma área de <b>9x9</b> embaixo dela, ou o <b>retângulo formado pelos Marcadores de Área</b> (até <b>64x64</b>), camada por camada, até o fundo do mundo: um bloco a cada 0,2s, 250 de energia por bloco, como uma picareta de diamante. Pula líquidos, blocos inquebráveis e blocos com inventário (baús, spawners...). Os itens vão para um <b>baú encostado</b> em qualquer lado; sem baú, ela guarda até 27 pilhas e pausa. Só trabalha com <b>sinal de redstone</b> (alavanca, tocha de redstone, botão... encostado). A <b>área que vai ser minerada aparece sempre</b>: uma caixa 9x9 do Minerador até a camada atual, com a camada sendo minerada destacada (verde = minerando, laranja = parado sem sinal ou sem energia, cinza = terminou). Não mina dentro da arena de um golem vivo.',
     [crafting('nature_quarry'), '<div class="prints"><figure><img src="img/prints/minerador.jpg" alt="Minerador ligado na redstone: a área aparece no chão" loading="lazy"><figcaption>Minerador ligado na redstone: a área aparece no chão</figcaption></figure></div>', table([('Direito', 'Mostra o estado, a camada e a energia; entrega os itens guardados'), ('Sinal de redstone', 'Liga (sem sinal fica parado)'), ('Shift + direito (mão vazia)', 'Recalcula a área pelos marcadores e recomeça do topo')], head=('Ação', 'Efeito'))]),
    ('magicblocks:quarry_marker', 'Uma tocha com cristal verde que <b>marca a área do Minerador da Natureza</b>. Coloque nos <b>cantos</b> da área (até 64 blocos do Minerador e na mesma altura, até 2 acima ou abaixo): o Minerador usa o <b>retângulo formado pelos marcadores</b>, até 64x64 (com um só marcador, o retângulo entre ele e o Minerador). A área é escolhida quando ele começa a minerar e aparece sempre no mundo; os marcadores não são minerados. Se passar de 64x64, ele avisa e usa a área padrão 9x9. A área começa na altura do Minerador e desce.',
     [crafting('quarry_marker')]),
    ('magicblocks:mana_sapling', 'Infunda <b>qualquer muda</b> com <b>Essência de Mana</b> no Nature Infuser. Plante e use farinha de osso: cresce uma árvore grande de <b>madeira azul</b> e folhas que brilham e soltam faíscas de mana. As folhas dão mudas e <b>Frutas de Mana</b>; o tronco vira Tábuas de Mana (valem como tábuas em qualquer receita).',
     [infuser('minecraft:oak_sapling', 'magicblocks:mana_essence', 'magicblocks:mana_sapling'), crafting('mana_planks')]),
    ('magicblocks:nature_harvester', 'Colhe e <b>replanta</b> sozinho tudo o que estiver maduro num raio de 5 (de 2 abaixo até 2 acima): plantações, verrugas do Nether, cacau, frutas vermelhas, melancias, abóboras, cana, cacto e bambu (a base fica). A semente do replantio sai da própria colheita. Os itens vão para um baú encostado. 150 de energia por colheita.',
     [crafting('nature_harvester')]),
    ('magicblocks:nature_breeder', 'Alimenta os animais adultos num raio de 5 com a comida de um <b>baú encostado</b> (trigo, cenoura, sementes... o que cada animal come) para eles cruzarem sozinhos. Para quando houver 24 animais na área. 250 de energia por animal.',
     [crafting('nature_breeder')]),
    ('magicblocks:nature_furnace', 'Uma fornalha com a <b>mesma tela</b> da comum. Com energia de natureza pelos cabos ela fica acesa <b>sem combustível</b> e cozinha <b>2x mais rápido</b> (12 de energia por tick = 1.200 por item, só quando tem algo para cozinhar). Sem energia funciona com combustível normal.',
     [crafting('nature_furnace')]),
    ('magicblocks:mana_distiller', 'Transforma energia de natureza em <b>Essência de Mana</b>: 20.000 de energia (40 segundos) por essência. Manda para um baú encostado ou guarda até você clicar.',
     [crafting('mana_distiller')]),
    ('magicblocks:nature_shield', 'Protege uma <b>área quadrada</b> de 25x25 (12 blocos para cada lado). A borda aparece no chão como uma faixa de luz, acompanhando o terreno, igual aos anéis de fogo do golem. Escudos com áreas que se encostam ou se cruzam <b>se fundem</b>: aparece só o contorno de fora e os monstros são empurrados para fora do conjunto inteiro. Clique no bloco com um <b>corante</b> para mudar a cor do emblema e da área. O escudo <b>destrói projéteis</b> que não são de jogadores (flechas de esqueleto, bolas de fogo, disparos dos espíritos...) e <b>empurra os monstros</b> para fora. Não afeta chefes. 150 de energia por projétil e 20 por empurrão.',
     [crafting('nature_shield')]),
    ('magicblocks:soul_generator', '<b>Fonte de energia</b>: cada criatura que morre a até 10 blocos gera 40 de energia por ponto de vida máxima (até 3.000 por morte; um zumbi dá 800). Ótimo embaixo de uma fazenda de monstros. Manda a energia pelos cabos (até 800 por tick) para máquinas e baterias.',
     [crafting('soul_generator')]),
    ('magicblocks:lunar_pillar', '<b>Fonte de energia</b> noturna: com céu aberto, gera 20 por tick à noite e <b>60 na Lua Roxa</b>. De dia não gera.',
     [crafting('lunar_pillar')]),
    ('magicblocks:lightning_catcher', '<b>Fonte de energia</b> de tempestade: guarda <b>60.000</b> de energia cada vez que um <b>raio natural</b> de tempestade cai a até 4 blocos (raios do Bloco do Trovão e de tridentes com Canalização não contam). Coloque um para-raios em cima para atrair os raios (o Ritual da Tempestade ajuda). Guarda até 200.000.',
     [crafting('lightning_catcher')]),
    ('magicblocks:crystal_tower', 'Uma <b>defesa movida a natureza</b>: base de pedra escura com ouro, coluna de obsidiana e garras douradas segurando um <b>cristal que flutua e gira</b>. A cada segundo dispara um <b>Míssil Arcano</b> no monstro mais perto que ela enxerga (até 16 blocos): 5 de dano mágico. 300 de energia por tiro (guarda 30.000). Os mísseis da torre <b>nunca acertam jogadores, animais nem aldeões</b>. <b>Indicador de energia:</b> 4 runas no degrau da base ficam <b>verdes pulsando</b> com energia e <b>vermelhas piscando</b> sem energia (o cristal também fica avermelhado e fraco).',
     [crafting('crystal_tower')]),
    ('magicblocks:mana_elevator', 'Bloco de madeira de mana com setas que brilham e um círculo de runas em cima. Coloque <b>vários na mesma coluna</b> (até 32 blocos entre eles). Em cima de um, <b>pule para subir</b> até o próximo acima ou <b>agache para descer</b> até o próximo abaixo, num rastro de luz. Precisa de 2 blocos livres em cima do destino. Cada viagem gasta <b>150 de energia de natureza</b> do elevador de onde você sai (ligue nos cabos; guarda 20.000). Clique de mão vazia para ver a energia.',
     [crafting('mana_elevator')]),
    ('magicblocks:nature_battery', 'Um bloco de vidro que <b>guarda energia de natureza</b> (até 250.000). Ligue nos cabos: ele recebe do Nature Charger e <b>devolve para as máquinas</b> ligadas nos mesmos cabos (até 600 por tick, dividido entre elas; nunca para outras baterias). O vidro <b>enche de líquido verde</b> brilhante conforme carrega. Clique para ver a energia; um comparador ao lado dá sinal de 0 a 15 conforme o nível. <b>Quebrada, guarda a energia</b>: o item mostra o líquido na altura do nível, uma barra verde embaixo e a energia na dica; colocada de novo, volta com tudo.',
     [crafting('nature_battery')]),
    ('magicblocks:mastery_table', 'A <b>árvore de cada Bloco Mágico</b>. Todas as ações dos blocos continuam liberadas; a mesa serve para <b>melhorar</b> cada bloco e para <b>desligar ações</b> que você não quer usar (ex.: desligar o Shift + Bater do Bloco de Fogo). Clique na mesa: à esquerda escolha o bloco; em cima ligue/desligue as ações (de graça); embaixo escolha uma melhoria para ver o que o ritual pede e clique em <b>Iniciar Ritual</b>.',
     [crafting('mastery_table'),
      '<h4>O ritual (8 pedestais)</h4><p>Coloque <b>8 Pedestais</b> em anel em volta da mesa, na mesma altura: 4 a 3 blocos em linha reta (norte, sul, leste, oeste) e 4 nas diagonais (2 blocos em cada eixo). Ligue a mesa à energia de natureza pelos cabos (guarda 60.000).</p><pre class="ring">      P\n  P       P\nP     M     P\n  P       P\n      P</pre><div class="prints"><figure><img src="img/prints/mesa_angulo.jpg" alt="Mesa com os 8 pedestais" loading="lazy"><figcaption>Mesa com os 8 pedestais</figcaption></figure><figure><img src="img/prints/mesa_cima.jpg" alt="Visto de cima: 4 em cruz a 3 blocos e 4 nas diagonais" loading="lazy"><figcaption>Visto de cima: 4 em cruz a 3 blocos e 4 nas diagonais</figcaption></figure><figure><img src="img/prints/mesa_ritual.jpg" alt="Ritual de melhoria em andamento" loading="lazy"><figcaption>Ritual de melhoria em andamento</figcaption></figure></div>',
      table([('Dano', '+15% de dano por nível em tudo que você causa segurando o bloco', 'Quartzo'),
             ('Alcance', '+15% de alcance / raio por nível (jatos, raios, feixes, explosões em área...)', 'Fragmento de Ametista'),
             ('Economia', '-20% de mana gasta por nível (a parte quebrada vira chance)', 'Lápis-lazúli')], head=('Melhoria', 'Efeito', 'Item do atributo')),
      table([('1', '4 do elemento + 2 do atributo + 2 Essências de Mana', '5', '5.000'),
             ('2', '4 do elemento + 2 do atributo + 2 Orbes de Mana', '10', '10.000'),
             ('3', '4 do elemento + 2 do atributo + 2 Diamantes Instáveis', '20', '20.000')], head=('Nível', 'Itens nos 8 pedestais', 'Níveis de XP', 'Energia')),
      '<p class="tip">Item do elemento: Fogo = Pó de Blaze, Água = Fragmento de Prismarinho, Gelo = Gelo Compactado, Trovão = Barra de Cobre, Redstone = Redstone, TNT = Pólvora, Void = Pérola do Ender, Sculk = Sculk, Folha = qualquer folha, Blackstone Dourado = Barra de Ouro (só Economia), Spawner = Osso (Alcance e Economia). O Bloco de Baú só tem as ações para desligar. As melhorias ficam no <b>jogador</b> (valem para qualquer cópia do bloco, até dentro da Espada de Manilium) e não se perdem ao morrer. Se tirarem um item no meio do ritual, ele falha e o XP volta.</p>']),
    ('magicblocks:pedestal', 'Expõe um item: clique com o item para colocar e com a mão vazia para pegar. Espadas ficam cravadas. É a peça dos <b>rituais</b>: 4 em volta do Altar de Rituais e 8 em volta da Mesa de Maestria (veja as montagens com fotos nesses blocos). Com folhas (ou o Bloco de Folha) em cima, fortalece o Nature Infuser.',
     [crafting('pedestal')]),
    ('magicblocks:arcane_pedestal', 'A melhoria do pedestal, mais alto e com cristal: <b>funciona igual ao Pedestal</b> (guarda um item e conta nos rituais do Altar e da Mesa de Maestria e no Nature Infuser) e solta partículas encantadas. Dá para misturar pedestais comuns e arcanos no mesmo ritual.',
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
    ('magicblocks:tnt_block', 'Explosões controladas. Em qualquer mão você fica <b>imune a explosões</b> (sem dano e sem ser arremessado).',
     [crafting('tnt_block'), table([
         ('Bater', 'Explosão onde a mira acerta; não te fere e nunca quebra blocos', '—'),
         ('Segurar direito', 'Acende uma TNT na mão; a barra acima da fome mostra o tempo até explodir. Solte para arremessar', '3'),
         ('Shift + segurar direito', '10s de carga com sirene (a TNT sobe girando sobre a cabeça); ao soltar, explosão nuclear com alcance de 30 blocos e um cogumelo de fumaça de 30 blocos de altura que fica no céu', '5')]),
      '<h4>TNT Ativa</h4><p>Coloque o Bloco de TNT no Nature Infuser com uma <b>TNT</b> comum na alimentação: a versão ativa é igual ao bloco normal, só que a TNT arremessada e a explosão nuclear quebram blocos (bater continua sem quebrar). A nuclear abre uma <b>cratera de 30 blocos de raio e 18 de profundidade</b>, limpando tudo até 28 blocos acima, com a borda chamuscada (pedra-negra, basalto, magma) e fogo. Baús atingidos soltam os itens.</p>',
      infuser('magicblocks:tnt_block', 'minecraft:tnt', 'magicblocks:tnt_block')]),
    ('magicblocks:slime_block', 'Um cubo de slime translúcido que <b>flutua girando sobre a mão</b> e vira a <b>ferramenta que você precisa</b>, todas de slime translúcido e com a força do diamante (ao se transformar ele vira uma gota que chacoalha, com partículas e som de slime). Depois de uns 3 segundos sem uso volta ao formato padrão.',
     [crafting('slime_block'), table([
         ('Bater numa criatura', 'Vira espada (7 de dano, como a de diamante)', '—'),
         ('Quebrar pedra / madeira / terra / folhas', 'Vira picareta / machado / pá / enxada', '—'),
         ('Direito numa terra ou grama', 'Ara (enxada)', '—'),
         ('Direito num tronco ou cobre', 'Descasca, raspa ou tira a cera (machado)', '—'),
         ('Shift + direito na grama', 'Faz caminho (pá)', '—'),
         ('Segurar direito (olhando para uma criatura ou para o nada)', 'Escudo levantado: bloqueia como um escudo', '—')], head=('Ação', 'Forma', 'Mana')),
      '<h4>Formato padrão</h4><p>Na bancada, junte o Bloco de Slime com uma <b>ferramenta de diamante</b> (espada, picareta, machado, pá ou enxada) ou um <b>escudo</b>: esse vira o formato padrão, e a ferramenta volta para você. Uma <b>bola de slime</b> volta o padrão para o bloco. Ele continua mudando conforme a necessidade.</p>'
      '<p class="tip">Aceita os encantamentos de espada, ferramentas e escudo (Afiação, Eficiência, Fortuna, Toque Suave, Saque, Inquebrável, Remendo...). Pode ser tingido como a armadura de couro e é consertado com bolas de slime. Não tem versão corrompida.</p>']),
    ('magicblocks:redstone_block', 'Circuitos acesos que pulsam como um relógio de redstone.',
     [crafting('redstone_block'), table([
         ('Bater', 'Faísca de redstone em linha reta (16 blocos): 5 de dano e Lentidão II', '1'),
         ('Direito', '<b>Corrente Carmesim</b>: um raio de redstone acerta a criatura na mira (até 20 blocos) e salta em ziguezague para até 4 monstros perto (8 blocos entre eles): 6 de dano em cada e Lentidão II por 2s. Recarga 4s. Sem alvo não gasta mana. No Verdadeiro: 6 saltos e 9 de dano', '3'),
         ('Shift + segurar direito', '<b>Kamehameha</b>: carrega uma esfera de energia 3D nas mãos por 4 segundos (barra de carga acima da fome) e, ao soltar, dispara um feixe 3D brilhante que segue a mira. Disparar custa de 1 (carga fraca) a 4 de mana (carga cheia), e o feixe gasta mais 1 por segundo. Quanto mais carga, mais largo, longo e forte (até 10 de dano a cada meio segundo); cada acerto cura 1 coração', '1 a cada 3s')])]),
    ('magicblocks:ruin_pedestal', 'Pelo mundo existem <b>Ruínas</b> de seis elementos, cada uma com um <b>Pedestal</b> no meio. Clique no pedestal segurando o Bloco Mágico do elemento (ele não é gasto): o chão treme, o golem <b>sobe da terra</b> e ruge com uma onda de choque; uma <b>arena</b> de 20 blocos de raio é erguida e o <b>Golem</b> do elemento desperta, com barra de vida, padrões de ataque e <b>música de luta própria</b>. Todo ataque tem um <b>aviso</b> antes: áreas vermelhas no chão (círculos, faixas com setas, quadrados) e linhas de mira brilhantes; a área VERDE é segura.' + ' <h4>Fase 2</h4><p>Com metade da vida o golem se <b>transforma</b> (fica invulnerável por 3 segundos, com ondas de choque e uma explosão que empurra todos): fica maior, ganha cristais brilhando e uma aura de energia, a música muda para a versão da fase 2, ele ataca mais rápido, machuca quem fica colado e ganha um <b>ataque supremo</b> que junta dois ataques ao mesmo tempo.</p>',
     ['<div class="prints"><figure><img src="img/prints/golem.jpg" alt="O Golem de Fogo na arena dele" loading="lazy"><figcaption>O Golem de Fogo na arena dele</figcaption></figure></div>', table([
         ('Fogo (deserto, savana)', 'Bloco de Fogo', '<b>Anéis de Chamas</b>: paredes baixas de fogo que se espalham devagar pelo chão, PULE por cima; Chuva de Meteoros; Sopro de Fogo; Cruz de Magma'),
         ('Água (praia, pântano)', 'Bloco de Água', 'Tsunami numa faixa marcada; Gêiseres sob você; Redemoinho que puxa; Bolha Prisão (saia do círculo!)'),
         ('Trovão (planícies, colinas)', 'Bloco de Trovão', '<b>Laser Elétrico</b>: esconda-se atrás dos pilares da arena; Raios Marcados; Investida Elétrica; Laser Giratório de 360°'),
         ('Ouro (badlands)', 'Bloco de Blackstone Dourado', 'Espinhos de Ouro em xadrez (duas ondas); Chuva de Moedas; Investida; Zona de Midas (fique no círculo VERDE)'),
         ('Gelo (neve)', 'Bloco de Gelo', 'Linhas de Estacas de gelo; Sopro Congelante; Granizo; Prisão de Gelo'),
         ('Redstone (florestas, taiga)', 'Bloco de Redstone', '<b>Laser Vermelho</b>: os pilares de cobertura SOBEM do chão (lâmpadas acesas) na hora; Minas; Circuito; Torretas (3 torretas de verdade sobem do chão e giram a cabeça para você; linha de mira antes de cada tiro; cada torreta <b>quebra com 3 golpes</b> ou flechadas)'),
         ('TNT (selvas)', 'Bloco de TNT', 'Bombardeio em fileira marcada; TNTs arremessadas em círculos marcados; <b>Mega Bomba</b> com bipe cada vez mais rápido: saia do disco; Chuva de TNT')],
         head=('Golem (onde fica a ruína)', 'Desperta com', 'Ataques')),
      '<h4>Blocos Verdadeiros</h4><p>O Bloco Mágico colocado no pedestal <b>fica guardado</b>. Quando o golem cai, ele volta como <b>Verdadeiro</b> (nome dourado e brilho de encantado), com habilidades melhores e um <b>ATAQUE NOVO</b>:</p>' + table([('Verdadeiro Bloco de Fogo', '<b>Bater: Meteoro</b> que cai do céu onde você mira (40 blocos). Lança-chamas de 16 blocos com o dobro de dano; explosão de chamas de 7 blocos'),('Verdadeiro Bloco de Água', '<b>Shift + direito: Tsunami</b>, uma parede de água que avança 24 blocos. Jato de 26 blocos que empurra mais e fere'),('Verdadeiro Bloco de Trovão', '<b>Shift + bater: Tempestade</b>, raios caem sozinhos nos monstros perto por 8s. Cadeia em 8 alvos; 3 raios; salto de 15 blocos'),('Verdadeiro Blackstone Dourado', '<b>Bater: Toque de Midas</b>, o alvo fica lento e fraco, leva +50% de dano e solta pepitas. Forma dourada com Resistência III, Regeneração II e Força'),('Verdadeiro Bloco de Gelo', '<b>Bater: Linha de Estacas</b> de cristais de gelo pontudos que brotam para a frente (16 blocos) e terminam num leque de cristais. Jato de 26 blocos que fere; nevasca de raio 14'),('Verdadeiro Bloco de Redstone', '<b>Shift + bater: Torreta</b> de redstone (sobe do chão, gira mirando e atira lasers nos monstros por 10s). Kamehameha carrega em 3s, mais grosso, mais longo, +50% de dano e cura 1,5 coração; faísca de 8; Sobrecarga um nível acima por 15s'),('Verdadeiro Bloco de TNT', 'A explosão nuclear cai <b>onde você mira, até 75 blocos</b>; a TNT arremessada vira <b>bomba de fragmentação</b> (4 explosões extras)')], head=('Bloco', 'Melhorias')),
      '<p class="tip">A arena <b>não pode ser quebrada</b> enquanto o golem estiver vivo: nem na mão, nem por explosões, nem pela cratera da nuclear do Bloco de TNT, pela corrupção do Void ou pelo Minerador da Natureza. Na aba criativa há os <b>Invocadores</b> (um pedestal de cada golem) para colocar onde quiser. Todos também dão um <b>Esmagar</b> quando você está colado (disco vermelho em volta dele). Cada golem tem 175 corações, armadura, e deixa 500 de experiência, Essência e Orbes de Mana, diamantes e itens do elemento (Coração do Mar, Maçã Dourada Encantada, sucata de Netherita...).</p>']),
    ('magicblocks:corrupted_fire_block', 'Os Blocos de Fogo, Folha, Blackstone Dourado, Spawner, Água, Gelo e TNT têm uma <b>versão corrompida</b> (escurecida e avermelhada), achada em baús de estruturas que combinam com ele. Funciona como o bloco normal, mas é <b>mais fraca</b> (quem segura causa 40% menos dano e se cura 40% menos) e aguenta só <b>2 usos</b>: cada habilidade usada gasta 1. Não pode ser consertada, encantada (nada de Remendo) nem colocada na Espada de Manilium.',
     [table([
         ('Bloco de Fogo Corrompido', 'Fortaleza do Nether', '30%'),
         ('Bloco de Folha Corrompido', 'Templo da Selva / Mansão da Floresta', '35% / 30%'),
         ('Bloco de Blackstone Dourado Corrompido', 'Bastião (tesouro / outros baús)', '50% / 15%'),
         ('Bloco de Spawner Corrompido', 'Masmorra', '25%'),
         ('Bloco de Água Corrompido', 'Ruínas Submersas (grande / pequena)', '30% / 15%'),
         ('Bloco de Gelo Corrompido', 'Iglu', '50%'),
         ('Bloco de TNT Corrompido', 'Pirâmide do Deserto', '30%')], head=('Bloco', 'Onde achar', 'Chance por baú'))]),
]

ARMAS = [
    ('magicblocks:manilium_chestplate', 'A armadura de Manilium tem a proteção da netherita e pode ficar ainda mais forte. Vestida, ela tem um <b>modelo 3D de cavaleiro</b>: viseira, bochechas e guarda de nuca no capacete; placa peitoral, cinto largo, saiote de placas, ombreiras de duas camadas, manoplas e uma capa vermelho-escura no peitoral; joelheiras nas calças; cano reforçado e biqueiras nas botas (as molduras pintam junto com a tinta). Todos os itens de Manilium têm <b>bordas cósmicas</b>: um céu de estrelas que se mexe conforme você move a câmera ou o item.',
     ['<div class="pieces">%s</div>' % ''.join(slot('magicblocks:manilium_' + p) for p in ['helmet', 'chestplate', 'leggings', 'boots']),
      smithing('minecraft:netherite_chestplate', 'magicblocks:manilium_chestplate'),
      '<h4>Fortalecer</h4><p>No Nature Infuser, coloque a peça na entrada e uma <b>Orbe de Mana</b> na alimentação: +1 de defesa por orbe, até <b>+5</b> em cada peça.</p>',
      infuser('magicblocks:manilium_chestplate', 'magicblocks:mana_orb', 'magicblocks:manilium_chestplate'),
      '<p class="tip">Os itens de Manilium <b>não podem mais ser pintados</b> (os que já tinham cor continuam com ela).</p>',
      '<h4>Enfeite de Manilium</h4><p>A Barra de Manilium também é um <b>material de enfeite</b>: na mesa de ferraria, junte <b>qualquer molde de enfeite</b> + <b>qualquer armadura</b> (de ferro, diamante, Elemental, de Mago...) + Barra de Manilium. Cada peça ganha <b>+1 de armadura</b> (+4 com as 4 peças) e o desenho do enfeite fica com o <b>céu cósmico</b> se mexendo, igual às bordas do Manilium.</p>',
      '<h4>Conversor de Almas</h4><p>Qualquer peitoral pode receber um Conversor de Almas embutido no Nature Infuser.</p>']),
    ('magicblocks:manilium_sword', 'Uma espada que cresce com você e carrega um Bloco Mágico na guarda.',
     [smithing('minecraft:netherite_sword', 'magicblocks:manilium_sword'),
      '<h4>Dano sem limite</h4><p>Cada <b>Orbe de Mana</b> infundida no Nature Infuser dá <b>+1 de dano</b>, sem limite.</p>',
      infuser('magicblocks:manilium_sword', 'magicblocks:mana_orb', 'magicblocks:manilium_sword'),
      '<h4>Bloco na guarda</h4><p>Coloque a espada vazia na entrada e um <b>Bloco Mágico</b> na alimentação: o bloco aparece na guarda e a espada passa a usar todas as habilidades dele, além de cortar normalmente. Para tirar o bloco, coloque a espada sozinha na bancada.</p>',
      infuser('magicblocks:manilium_sword', 'magicblocks:fire_block', 'magicblocks:manilium_sword')]),
    ('magicblocks:mage_robe', 'Uma armadura de pano mágico no estilo de mago: <b>chapéu pontudo</b> de aba larga com faixa dourada e a ponta dobrada para trás, <b>manto longo</b> azul até os pés com gola, abertura e barra douradas, faixa na cintura, mangas largas, calças escuras e sapatos de bico virado. Protege como <b>ferro</b> e é ótima para encantar.',
     ['<div class="pieces">%s</div>' % ''.join(slot('magicblocks:mage_' + p) for p in ['hat', 'robe', 'pants', 'boots']),
      crafting('mage_robe'),
      table([('0 peças', '1 de mana a cada 120s'), ('1 peça', 'a cada ~96s'), ('2 peças', 'a cada ~72s'), ('3 peças', 'a cada ~49s'),
             ('4 peças', '<b>1 de mana a cada 25s</b>')], head=('Vestindo', 'A mana volta')),
      '<p class="tip">Feita com Tecido Mágico (as receitas seguem o formato das armaduras normais; o manto leva um Bloco de Lápis no meio). A Sabedoria dos Atributos acelera ainda mais.</p>']),
]

ARMAS.extend([
    ('magicblocks:mage_cloth', 'Os conjuntos de armadura do mod lado a lado.', ['<div class="prints"><figure><img src="img/prints/armaduras.jpg" alt="Mago, Elementais (fogo, água, gelo, trovão) e Manilium" loading="lazy"><figcaption>Mago, Elementais (fogo, água, gelo, trovão) e Manilium</figcaption></figure></div>']),
    ('magicblocks:elemental_chestplate', 'A <b>Armadura de Mago melhorada</b>: o mesmo modelo (chapéu, manto, calças e sapatos), com as cores do elemento. Receita: a peça de mago no meio com <b>Diamantes Elementais</b> em volta (chapéu 3, manto 7, calças 6, sapatos 2). Defesa de diamante, durabilidade quase de netherita, 2,5 de resistência e <b>conta como peça de mago</b> para a volta da mana. No <b>Nature Infuser</b>, coloque a peça na entrada e o item do elemento na alimentação para dar um <b>elemento</b> a ela (as cores mudam; dá para trocar depois). Os bônus contam as peças do <b>mesmo elemento</b> vestidas.',
     ['<div class="pieces">%s</div>' % ''.join(slot('magicblocks:elemental_' + p) for p in ['helmet', 'chestplate', 'leggings', 'boots']),
      crafting('elemental_chestplate'),
      table([('Fogo', 'Pó de Blaze', '-40% de dano de fogo', 'Resistência ao Fogo permanente'),
             ('Água', 'Cristais de Prismarinho', 'Respira debaixo d\'água', 'Graça do Golfinho e Poder do Conduto na água'),
             ('Gelo', 'Gelo Azul', 'Não congela na neve fofa e não fica lento', 'Congela a água por onde anda'),
             ('Trovão', 'Para-raios', 'Velocidade I', 'Velocidade II e 30% de chance de dar um choque (4 de dano) em quem te bater')],
            head=('Elemento', 'Infusão', '2 peças', '4 peças')),
      '<p class="tip">Peças com elemento também aparecem nos baús da <a href="criaturas.html#spawner">Masmorra Elemental</a>.</p>']),
    ('magicblocks:unstable_pickaxe', 'O degrau entre o diamante e o Manilium, feito com <b>Diamante Instável</b> e gravetos (receitas iguais às de diamante). Minera o mesmo que o diamante, mas tem <b>2.000 de durabilidade</b>, é mais rápido e cada ferramenta tem uma habilidade. Conserta na bigorna com Diamante Instável.',
     ['<div class="pieces">%s</div>' % ''.join(slot('magicblocks:unstable_' + p) for p in ['sword', 'pickaxe', 'axe', 'shovel', 'hoe']),
      table([
         ('Espada Instável', '7 de dano. <b>25%</b> de chance de um golpe elemental: fogo (queima 4s), gelo (Lentidão II e congela), água (empurra e Fraqueza) ou raio (+3 de dano)'),
         ('Picareta Instável', '<b>Agachado</b>: quebra 3x3 na face que você está minerando'),
         ('Machado Instável', 'Derruba a <b>árvore inteira</b> de uma vez (só árvores com folhas naturais). Agachado corta um tronco só'),
         ('Pá Instável', '<b>Agachado</b>: cava 3x3'),
         ('Enxada Instável', 'Ara <b>3x3</b> de uma vez. Agachado ara um bloco só')], head=('Ferramenta', 'Habilidade')),
      crafting('unstable_pickaxe'), crafting('unstable_sword')]),
    ('magicblocks:block_talisman', 'Um cinto mágico que guarda até <b>9 Blocos Mágicos</b>. Os blocos guardados giram num círculo atrás de você e o talismã aparece nas costas.',
     [crafting('block_talisman'), table([
         ('Direito com o talismã na mão', 'Abre o armazenamento (só aceita Blocos Mágicos)', '—'),
         ('Equipar', 'Slot de <b>cinto</b> do Curios (sem o Curios, funciona no inventário)', '—'),
         ('Tecla G (mão livre)', 'Abre a roda de blocos: aponte e clique (ou solte a tecla) para pegar o bloco', '—'),
         ('Tirar o bloco da mão', 'Trocar de slot ou jogar no chão devolve o bloco ao talismã', '—')]),
      '<p class="tip">A tecla pode ser trocada em Opções &rarr; Controles &rarr; Magic &amp; Blocks.</p>',
      '<h4>Rolar para desviar (tecla R)</h4><p>Com qualquer item (ou mão vazia), aperte <b>R</b> no chão para dar uma cambalhota na direção em que está andando (para frente se estiver parado). Durante a rolagem você fica <b>invulnerável por 0,4s</b> e desvia de qualquer ataque, inclusive dos golens. Recarga de <b>2 segundos</b>: um ícone ao lado direito da hotbar mostra quando dá para rolar de novo (apagado enquanto recarrega, pisca quando fica pronto). Gasta um pouco de fome. Não funciona na água, voando ou montado.</p>'])])

CRIATURAS = [
    ('magicblocks:fire_spirit_spawn_egg', 'Espíritos que flutuam como blazes e aparecem (não muito comuns) <b>à noite</b> nos biomas do seu elemento. Cada elemento tem seu próprio corpo: o de Fogo tem coroa de chamas e punhos grandes, o de Água um rabo ondulante e um anel de água girando, o de Gelo espinhos de cristal translúcido e o de Trovão chifres em zigue-zague e um corpo de nuvem com um raio pendurado. Carregam por um instante (brilhando) e atiram <b>dois disparos</b> do elemento; colados em você, batem. Têm 13 corações.',
     [table([
         ('Espírito do Fogo', 'Deserto, savana, badlands e Nether', 'Queima por 4s', 'Pó de Blaze'),
         ('Espírito da Água', 'Praias, rios, pântanos e ilhas no oceano', 'Empurra forte e apaga o fogo', 'Cristais de Prismarinho'),
         ('Espírito do Gelo', 'Biomas de neve e picos gelados', 'Lentidão II e congela', 'Bolas de neve e Gelo Compactado'),
         ('Espírito do Trovão', 'Montanhas, ou <b>qualquer lugar durante tempestades</b>', 'Choque com dano extra', 'Pó de Pedra Luminosa e Cobre')],
         head=('Espírito', 'Onde aparece', 'Disparo', 'Solta')),
      '<div class="prints"><figure><img src="img/prints/criaturas_1.jpg" alt="Zumbi de Fogo e Zumbi Contaminado" loading="lazy"><figcaption>Zumbi de Fogo e Zumbi Contaminado</figcaption></figure><figure><img src="img/prints/criaturas_2.jpg" alt="Mago Midas, Espírito do Fogo e da Água" loading="lazy"><figcaption>Mago Midas, Espírito do Fogo e da Água</figcaption></figure><figure><img src="img/prints/criaturas_3.jpg" alt="Espíritos do Gelo e do Trovão e a Sombra" loading="lazy"><figcaption>Espíritos do Gelo e do Trovão e a Sombra</figcaption></figure><figure><img src="img/prints/criaturas_4.jpg" alt="Sentinela Arcana e a Torre Arcana ao fundo" loading="lazy"><figcaption>Sentinela Arcana e a Torre Arcana ao fundo</figcaption></figure></div>',
      '<p class="tip">Todos podem soltar <b>Essência de Mana</b> (15%) e, se você matar, o <b>Estilhaço Instável</b> (8%, mais com Pilhagem). O de fogo se machuca na água; o de água respira debaixo dela.</p>']),
    ('magicblocks:arcane_sentinel_spawn_egg', 'Uma <b>torre arcana</b> de três andares aparece (rara) em <b>florestas e planícies</b>. Entre pela porta ao sul e suba pela escada de mão da parede norte: há zumbis e esqueletos no térreo, esqueletos e um Mago da Folha no segundo andar e um Espírito Elemental no terceiro. No topo aberto, a <b>Sentinela Arcana</b> guarda um baú com loot de meio de jogo.',
     [table([
         ('Rajada Arcana', 'Antes, <b>linhas roxas de mira</b> ligam ela até você por 1 segundo; depois, 3 disparos roxos que <b>perseguem</b> você de leve (6 de dano mágico e Fraqueza). Com o escudo, 5 disparos'),
         ('Nova Arcana', 'Se você chega perto, ela marca um <b>disco roxo</b> no chão e, 1 segundo depois, explode em volta (9 de dano e empurrão). Saia do círculo ou role (R)!'),
         ('Escudo', 'Abaixo de 75% da vida, a cada 20s fica 5s com um escudo de cristais: <b>corta 80% do dano</b>'),
         ('Reforços', 'Na metade da vida marca <b>2 anéis roxos</b> no chão e, 1 segundo depois, surgem neles <b>2 Espíritos Elementais</b> (uma vez só)')], head=('Ataque', 'Como funciona')),
      '<div class="prints"><figure><img src="img/prints/torre_arcana.jpg" alt="A Torre Arcana vista de cima" loading="lazy"><figcaption>A Torre Arcana vista de cima</figcaption></figure></div>',
      '<p class="tip">A Sentinela tem 100 corações, armadura e barra de chefe roxa, não leva dano de queda e não some. Derrotada, solta <b>1 Diamante Instável</b>, 2 a 4 Estilhaços, Essência de Mana e uma Orbe de Mana. O baú pode ter Estilhaços, Diamante Instável, diamantes, livros encantados, Orbe de Mana e até uma Orbe de Mana Condensada ou uma ferramenta instável.</p>']),
    ('minecraft:spawner', 'Uma masmorra <b>subterrânea e rara</b> (entre as camadas -30 e 20, em qualquer bioma da Superfície). No centro, um salão com o <b>baú final</b> e um spawner de zumbi ou esqueleto; dele saem 4 corredores com <b>armadilhas de flechas</b> (placas de pressão atravessando o corredor) até 4 salas, uma por elemento. Cada sala tem o seu <b>Guardião</b>: um Espírito Elemental com 40 corações e mais dano, que não sai da sala, e um baú do elemento.',
     [table([('Fogo (norte)', 'Tijolos do Nether, blocos de magma e poços de lava', 'Varas de Blaze, Creme de Magma'),
             ('Água (sul)', 'Prismarinho, lanternas do mar e uma piscina', 'Fragmentos de Prismarinho, às vezes Coração do Mar'),
             ('Gelo (leste)', 'Gelo compactado e azul, buracos de neve fofa', 'Gelo Azul, Gelo Compactado'),
             ('Trovão (oeste)', 'Cobre e para-raios', 'Barras de Cobre, Para-raios')], head=('Sala', 'Como é', 'Baú do elemento')),
      '<p class="tip">Os baús das salas podem ter o <b>Bloco Corrompido</b> do elemento e peças da <b>Armadura Elemental</b> já com o elemento. O baú final tem estilhaços, Diamantes Instáveis, Orbes, diamantes, livros encantados e às vezes um Bloco Corrompido, uma ferramenta instável ou um Peitoral Elemental. Cada Guardião solta 2 ou mais Estilhaços Instáveis e Essência de Mana.</p>']),
    ('magicblocks:lunar_fragment', 'Em uma noite rara (<b>1 em 10</b>, a partir do 4º dia) ou chamada pelo <b>Ritual da Lua Roxa</b>, a lua fica roxa, o céu e a neblina ficam roxos e ninguém consegue dormir. Vêm <b>5 ondas</b> de monstros, uma por minuto, em volta de cada jogador na Superfície: zumbis, esqueletos, bruxas, magos e Espíritos Elementais (brilhando), cada onda maior. Depois da última chega o <b>Arauto da Lua Roxa</b>: uma Sentinela Arcana com 150 corações. Todos os monstros das ondas têm <b>contorno roxo brilhante</b> (dá para ver através das paredes) e não somem sozinhos. Se a meia-noite chegar antes de você vencer, <b>a lua para no meio do céu</b> até todos os monstros roxos e o Arauto caírem (a barra mostra quantos faltam); depois o tempo volta a correr.',
     ['<div class="prints"><figure><img src="img/prints/lua_roxa.jpg" alt="A lua roxa no alto do céu" loading="lazy"><figcaption>A lua roxa no alto do céu</figcaption></figure><figure><img src="img/prints/lua_roxa_monstros.jpg" alt="A noite da Lua Roxa" loading="lazy"><figcaption>A noite da Lua Roxa</figcaption></figure></div>',
      '<p class="tip">Os monstros da Lua Roxa soltam <b>Fragmentos Lunares</b> (35%). O Arauto solta 4 a 6 fragmentos, Diamante Instável e dá 1 ponto de habilidade. A Lua Roxa acaba quando amanhece.</p>']),
    ('minecraft:enchanted_book', 'Aperte <b>K</b> para abrir os <b>Atributos</b>, no estilo de D&amp;D. A cada <b>5 níveis de XP</b> que você <b>alcança pela primeira vez</b> ganha 1 ponto (nível 5, 10, 15... até o 100 = 20 pontos; gastar níveis encantando não tira pontos). Chefes dão pontos bônus (golem: 2; Sentinela Arcana e Arauto da Lua Roxa: 1) e o Ritual do Conhecimento dá 1. Cada atributo vai de <b>0 a 10</b>. Redistribuir tudo custa 10 níveis de XP. Os pontos não se perdem ao morrer.',
     [table([('Força', '+0,3 de dano corpo a corpo'), ('Destreza', '+1% de velocidade, +2% de velocidade de ataque e a rolagem recarrega 0,1s mais rápido'),
             ('Constituição', '+1 de vida máxima (meio coração) e +2% de resistência a empurrão'),
             ('Inteligência', '+1 de mana máxima a cada 2 pontos e +2% de dano das habilidades dos Blocos Mágicos'),
             ('Sabedoria', 'A mana volta 5% mais rápido e -2% de dano mágico/elemental recebido'),
             ('Carisma', '+0,1 de sorte e 1% de chance de uma habilidade não gastar mana')], head=('Atributo', 'Por ponto')),
      '<div class="prints"><figure><img src="img/prints/atributos.jpg" alt="A tela de Atributos (tecla K)" loading="lazy"><figcaption>A tela de Atributos (tecla K)</figcaption></figure></div>']),
    ('magicblocks:eclipse_shard', 'Em um dia raro (<b>1 em 12</b>, ao meio-dia, a partir do 5º dia) ou chamado pelo <b>Ritual do Eclipse</b>, a lua cobre o sol: o céu escurece, o horizonte fica alaranjado e um <b>disco negro com coroa de fogo</b> toma o lugar do sol por <b>2 minutos</b>. Enquanto dura, <b>Sombras</b> surgem da fumaça em volta de cada jogador na Superfície (2 a 3 a cada 10s, até 8 perto de você).',
     [table([('Sombra', 'Espectro encapuzado de olhos laranja que flutua com uma cauda de fumaça. 12 corações, golpe de 5 que <b>cega por 2s</b>.'),
             ('Só morre perto de luz', 'Sem luz, os golpes <b>atravessam</b> a Sombra. Ela só toma dano com luz de bloco 7+ onde está, se alguém a até 6 blocos segura uma <b>tocha, lanterna ou a Lanterna de Mana</b> (na mão ou no cinto), ou com <b>fogo</b>.'),
             ('Fragmento do Eclipse', 'As Sombras soltam (40%, mais com Pilhagem). Faz a <b>Torre de Cristal</b>.'),
             ('Fim', 'Quando o eclipse acaba, as Sombras se desfazem na luz do sol.')], head=('', 'Como é')),
      '<div class="prints"><figure><img src="img/prints/eclipse_sol.jpg" alt="O sol coberto" loading="lazy"><figcaption>O sol coberto</figcaption></figure><figure><img src="img/prints/eclipse_sombras.jpg" alt="Sombras no eclipse" loading="lazy"><figcaption>Sombras no eclipse</figcaption></figure></div>']),
]

PAGES = [
    ('recursos', 'Recursos', 'Materiais, essências e itens úteis.', RECURSOS),
    ('blocos', 'Blocos', 'Blocos que você coloca no mundo.', BLOCOS),
    ('blocos-magicos', 'Blocos Mágicos', 'Blocos que flutuam na mão e dão poderes elementais.', MAGICOS),
    ('armas-e-armaduras', 'Armas e Armaduras', 'Ferramentas Instáveis, o equipamento de Manilium e o Talismã dos Blocos.', ARMAS),
    ('criaturas', 'Criaturas', 'Espíritos Elementais, a Torre Arcana, a Masmorra, a Lua Roxa e os Atributos.', CRIATURAS),
]

# ===================================================================== html

SUPPORT = 'https://livepix.gg/newgswolf101'


def anchor(item_id):
    return item_id.split(':')[1].replace('_', '-')


DISPLAY = {
    'magicblocks:fire_spirit_spawn_egg': 'Espíritos Elementais',
    'magicblocks:arcane_sentinel_spawn_egg': 'Torre Arcana e Sentinela Arcana',
    'magicblocks:unstable_pickaxe': 'Ferramentas Instáveis',
    'magicblocks:mana_sapling': 'Árvore de Mana',
    'magicblocks:lunar_fragment': 'Lua Roxa',
    'minecraft:enchanted_book': 'Atributos (tecla K)',
    'magicblocks:mage_robe': 'Armadura de Mago',
    'minecraft:spawner': 'Masmorra Elemental',
    'magicblocks:elemental_chestplate': 'Armadura Elemental',
}


def display_name(item_id):
    if item_id == 'magicblocks:manilium_chestplate':
        return 'Armadura de Manilium'
    if item_id == 'magicblocks:nature_workbench':
        return 'Nature Infuser'
    if item_id in DISPLAY:
        return DISPLAY[item_id]
    return name(item_id)


def topbar(active):
    tabs = ''.join('<a href="%s.html"%s>%s</a>' % (slug, ' class="on"' if slug == active else '', title)
                   for slug, title, _, _ in PAGES) + ('<a href="balanceamento.html"%s>Balanceamento</a>' % (' class="on"' if active == 'balanceamento' else ''))
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


# ===================================================================== balanceamento (aba propria)

def balance_page():
    rows = ''.join('<tr><td>%s</td><td>%s</td></tr>' % r for r in [
        ('<code>/apelar</code>', 'Mostra a dificuldade atual (o padrão é <b>x1</b>).'),
        ('<code>/apelar 2</code>', 'Deixa tudo <b>2x mais difícil</b>. Aceita de <b>0.25</b> a <b>10</b>, com decimais (ex.: <code>/apelar 1.5</code>).'),
        ('<code>/apelar 1</code>', 'Volta ao normal.'),
        ('<code>/apelar 0.5</code>', 'Abaixo de 1 deixa <b>mais fácil</b>: monstros mais fracos e materiais caindo mais.')])
    eff = ''.join('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' % r for r in [
        ('Vida dos monstros', 'x multiplicador', 'Todos os monstros: do jogo, do mod e os chefes (golens, Sentinela, Arauto).'),
        ('Dano dos monstros', 'x multiplicador', 'Golpes e ataques que usam o dano do monstro.'),
        ('Velocidade', 'não muda', 'Os monstros andam e atacam na mesma velocidade de sempre, em qualquer dificuldade.'),
        ('Armadura (só do mod)', '+2 por ponto acima de 1', 'Monstros e chefes do Magic &amp; Blocks ficam mais duros.'),
        ('Drops raros do mod', 'caem multiplicador vezes menos', 'Fragmentos Lunares e do Eclipse, Diamante Instável, Essência de Mana e do Void, Orbes de Mana, Estilhaços Instáveis e Barras de Manilium. Com x2 cai metade (a parte quebrada vira chance).')])
    body = ('<main class="page-text"><h1>Balanceamento</h1>'
            '<p class="sub">Achou fácil demais? Use o comando <b>/apelar</b> para deixar o mundo mais difícil (ou mais fácil).</p>'
            '<div class="callout">O comando é de <b>operador</b> (precisa de cheats no singleplayer ou ser OP no servidor). '
            'Vale para o <b>mundo inteiro</b>, fica salvo no mundo e muda <b>na hora</b> os monstros que já existem.</div>'
            '<h2>Como usar</h2><table class="abil tbl"><tr><th>Comando</th><th>O que faz</th></tr>%s</table>'
            '<h2>O que muda</h2><table class="abil tbl"><tr><th>O quê</th><th>Quanto</th><th>Detalhes</th></tr>%s</table>'
            '<h2>Exemplos</h2><ul class="steps">'
            '<li><b>x1</b> (padrão): o mod como foi pensado.</li>'
            '<li><b>x1.5</b>: um pouco mais de desafio, bom para quem já conhece o mod.</li>'
            '<li><b>x2</b>: monstros com o dobro de vida e dano; materiais do mod caem metade.</li>'
            '<li><b>x3 ou mais</b>: para servidores e grupos que querem sofrer. Golens com 3x vida (525 corações!).</li></ul>'
            '<p class="tip">Os itens únicos dos chefes (como o Bloco Mágico que o golem devolve como Verdadeiro) <b>nunca</b> ficam mais raros.</p>'
            '</main>') % (rows, eff)
    return page('Balanceamento', body, 'balanceamento')


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
write('balanceamento.html', balance_page())
