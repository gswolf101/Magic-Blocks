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
    'minecraft:beacon': lambda: iso(vtex('block/beacon'), vtex('block/beacon')),
    'magicblocks:ancestral_sapling': lambda: flat(mtex('block/ancestral_sapling')),
    'magicblocks:stripped_ancestral_log': lambda: iso(mtex('block/stripped_ancestral_log_top'), mtex('block/stripped_ancestral_log')),
    'minecraft:smooth_stone': lambda: iso(vtex('block/smooth_stone'), vtex('block/smooth_stone_slab_side')),
    'minecraft:zombie_head': lambda: Image.open(io.BytesIO(jar.read('assets/minecraft/textures/entity/zombie/zombie.png'))).convert('RGBA').crop((8, 8, 16, 16)).resize((16, 16), Image.NEAREST),
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
    '#minecraft:wool': lambda: iso(vtex('block/white_wool'), vtex('block/white_wool')),
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
    'magicblocks:fractured_colossus_spawn_egg': lambda: flat(layered(tint(vtex('item/spawn_egg'), (36, 32, 44)), vtex('item/spawn_egg_overlay'), (180, 106, 240))),
    'magicblocks:solar_empress_spawn_egg': lambda: flat(layered(tint(vtex('item/spawn_egg'), (244, 238, 220)), vtex('item/spawn_egg_overlay'), (255, 210, 74))),
    'magicblocks:star_slug_spawn_egg': lambda: flat(layered(tint(vtex('item/spawn_egg'), (42, 74, 140)), vtex('item/spawn_egg_overlay'), (159, 240, 255))),
    'magicblocks:ember_boar_spawn_egg': lambda: flat(layered(tint(vtex('item/spawn_egg'), (42, 34, 32)), vtex('item/spawn_egg_overlay'), (255, 106, 30))),
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
# blocos da Forja (1.0.152): cubos com as texturas do mod
for _blk in ['mithril_ore', 'refined_forgestone', 'refined_forgestone_bricks', 'chiseled_refined_forgestone_bricks']:
    ICON_BUILDERS['magicblocks:' + _blk] = (lambda b: lambda: iso(mtex('block/' + b), mtex('block/' + b)))(_blk)
for _f in ['forge_furnace', 'herfestus_furnace']:
    ICON_BUILDERS['magicblocks:' + _f] = (lambda f: lambda: iso(mtex('block/%s_top' % f), mtex('block/%s_front_on' % f), mtex('block/%s_side' % f)))(_f)
for _base, _pre in [('refined_forgestone', 'refined_forgestone'), ('refined_forgestone_bricks', 'refined_forgestone_brick')]:
    for _suf in ['_stairs', '_slab', '_wall']:
        ICON_BUILDERS['magicblocks:' + _pre + _suf] = (lambda b: lambda: iso(mtex('block/' + b), mtex('block/' + b)))(_base)
ICON_BUILDERS['magicblocks:forge_pedestal'] = lambda: iso(mtex('block/forge_pedestal_top'), mtex('block/forge_pedestal_rune'))
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
    if item_id.startswith('#magicblocks:'):   # tag do mod: icone do primeiro item da tag
        tag_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src', 'main', 'resources', 'data', 'magicblocks', 'tags',
                                'items', item_id.split(':', 1)[1] + '.json')
        if os.path.exists(tag_file):
            return icon(json.load(open(tag_file, encoding='utf-8'))['values'][0])
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
    'minecraft:diamond_block': 'Bloco de Diamante', 'minecraft:potion': 'Garrafa de Água', '#minecraft:logs': 'Tronco (qualquer)', '#minecraft:wool': 'Lã (qualquer)',
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


MISSING_RECIPES = []


def crafting(recipe_file):
    path = os.path.join(RECIPES, recipe_file + '.json')
    if not os.path.exists(path):
        MISSING_RECIPES.append(recipe_file)   # receita tirada do mod: a wiki so nao mostra
        return ''
    d = json.load(open(path, encoding='utf-8'))
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


def smithing3(template, base, addition, out):
    return ('<div class="recipe"><div class="label">Mesa de ferraria</div><div class="craft">%s%s%s'
            '<span class="arrow">&#10140;</span>%s</div></div>') % (slot(template), slot(base), slot(addition), slot(out, True))


def note(text):
    return '<div class="recipe"><div class="label">Como obter</div><p class="obtain">%s</p></div>' % text


def table(rows, head=('Ação', 'Efeito', 'Mana')):
    body = ''.join('<tr>%s</tr>' % ''.join('<td>%s</td>' % c for c in row) for row in rows)
    return '<table class="abil"><tr>%s</tr>%s</table>' % (''.join('<th>%s</th>' % h for h in head), body)


# ===================================================================== conteudo

# Cada entrada: (id do item, texto de introducao, [blocos de html extras])
RECURSOS = [
    ('magicblocks:mana_orb', 'O coração de todas as receitas mágicas. Também serve de alimentação no Nature Infuser para fortalecer a armadura e a espada de Manilium.',
     [note('Minere o Minério de Mana com picareta de diamante ou melhor (Fortuna aumenta).')]),
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
    ('magicblocks:teleport_crystal', '<b>Shift + direito</b> marca o lugar onde você está. Depois, <b>segure direito</b> por 1,5s para voltar até lá, gastando mana: 1 + 1 a cada 250 blocos (no máximo 8). Só funciona na mesma dimensão; recarga de 5s. Num <b>Pedestal Arcano</b>, um cristal marcado abre um <b>mini portal</b> em cima do pedestal: entre nele para ir ao lugar marcado, <b>sem gastar mana</b> (o Estabilizado também atravessa dimensões).',
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
    ('magicblocks:emerald_heart', 'O coração da <b>Esmeralda Colossal</b>: cai quando você derrota o chefe da Caverna de Esmeralda (1 por vitória). Serve para fazer a Picareta de Esmeralda.',
     [note('Derrote a Esmeralda Colossal (só picaretas ferem ela).')]),
    ('magicblocks:emerald_pickaxe', '<b>Inquebrável</b> (nunca gasta) e com <b>12 de dano</b>. Minera como netherita e mais rápido e <b>aceita encantamentos</b> na mesa de encantamentos (menos Inquebrável e Remendo). <b>Shift + segurar o botão direito</b> carrega um ataque de mineração (1s); ao soltar gasta <b>6 de mana</b> e abre um <b>túnel 8x8 de 100 blocos</b> para onde você olha (ou para baixo, olhando o chão): só pedra, terra e parecidos somem, os <b>minérios ficam no lugar, expostos</b> (estilo Miner\'s Dream), e a <b>lava</b> dentro e nas paredes do túnel <b>vira pedra</b>. Blocos <b>colocados por jogadores</b> (construções) nunca são apagados. Como é uma picareta, também serve para enfrentar a Esmeralda Colossal de novo.',
     [crafting('emerald_pickaxe')]),
    ('magicblocks:ancestral_staff', 'Cajado de madeira ancestral com um Cristal Instável preso em garras douradas. Receita: 3 Troncos Ancestrais Descascados, 1 Cristal Instável e a Varinha do Aprendiz. No <b>Nature Infuser</b>, coloque um Bloco Mágico para equipar (tira igual à espada: sozinho ou com um Cristal Instável na bancada). O cajado usa as habilidades do bloco e ganha um <b>poder segurando o botão esquerdo</b>. <b>Baú e Slime não encaixam.</b>',
     [crafting('ancestral_staff'),
      table([('Fogo', 'Passivo', 'Os ataques de fogo chegam 60% mais longe'),
             ('Água', 'Shift + segurar esquerdo', 'Redemoinho em volta: gira e fere os monstros (1 de mana/s)'),
             ('Gelo', 'Shift + segurar esquerdo', 'Espinho de Gelo carregável: até 10s e 50 de dano (1 de mana até 4s, 3 até 8s, 6 até 10s)'),
             ('Redstone', 'Segurar esquerdo', 'Explosão Carmesim posicionável: círculos mágicos onde você mira; solte para explodir (raio 15, 10 de mana, carrega 2s; não quebra blocos)'),
             ('TNT', 'Segurar esquerdo', 'TNT sem pavio que explode no impacto, bem forte (3 de mana)'),
             ('Void', 'Segurar esquerdo 6s', 'Buraco negro 4x maior (8 de mana)'),
             ('Folha', 'Segurar esquerdo', 'Abraço da Floresta: vinhas prendem os monstros em volta (lentidão, veneno, dano) e você regenera (1 de mana/s)'),
             ('Sculk', 'Segurar esquerdo', 'Eco: os monstros à frente brilham; ao soltar, ondas sônicas acertam até 6 deles (4 de mana)')],
            head=('Bloco', 'Como', 'Poder'))]),
    ('magicblocks:small_colossus', 'Um bloquinho de esmeralda que cai da <b>Esmeralda Colossal (5%)</b> e do <b>Príncipe das Esmeraldas (20%)</b>. Coloque no chão: vira o <b>Mini Colosso</b>, a Colossal em miniatura (45% de um bloco). Dê <b>Esmeraldas</b> para domar (1 chance em 3 por esmeralda). Ele cresce em <b>150 dias</b> (75 por estágio), ou mais rápido com <b>Blocos de Esmeralda</b> (cada um = 10 dias); um <b>Minério de Esmeralda de Ardósia</b> trava/destrava o crescimento. <b>Estágio 1</b>: só segue você. <b>Estágio 2</b>: atira estilhaços de esmeralda nos monstros que lutam com você (1 a cada 7s). <b>Estágio 3</b> (2x2x2): monte com a mão vazia — você fica <b>de pé</b> em cima dele, como num tronco rolando; a <b>barra de pulo</b> carrega uma investida (a faixa verde no chão mostra o caminho), quem estiver no caminho leva dano, e no fim ele fica parado 1,5s. Sobe degraus de 2 blocos. Em todos os estágios: <b>Shift + clique direito</b> faz ele repousar (dorme com Zzz, no centro do bloco) ou acordar; clique com a mão vazia mostra o crescimento; esmeraldas o curam.',
     [note('Esmeralda Colossal (5%) ou Príncipe das Esmeraldas (20%).')]),
    ('magicblocks:awakened_mana_star', 'A Estrela de Mana levada ao limite. Feita no <b>Altar de Rituais</b>: a Estrela de Mana no altar e, nos pedestais, um <b>Fragmento Lunar</b>, um <b>Bloco Mágico</b> qualquer (30% de chance de sumir), uma <b>Essência do Void</b> e uma <b>Estrela do Nether</b> (25.000 de energia). A Estrela de Mana comum para em <b>+5 de armadura</b> e <b>+50 de dano</b> na espada; daí em diante só a Despertada: no Nature Infuser, <b>+1 de armadura</b> por estrela (até +10) e <b>+1 de dano</b> por estrela na Espada de Manilium (até +120). Depois vem a <a href="o-vazio.html#void-star">Estrela do Vazio</a>.',
     [note('Altar de Rituais: Estrela de Mana + Fragmento Lunar, Bloco Mágico, Essência do Void e Estrela do Nether.')]),
    ('magicblocks:miner_essence', 'Cai do <b>Príncipe das Esmeraldas</b> (1 por vitória). Serve para fazer a Picareta de Esmeralda Real.',
     [note('Derrote o Príncipe das Esmeraldas: desperte uma Caverna de Esmeralda tendo a Picareta de Esmeralda no inventário.')]),
    ('magicblocks:royal_emerald_template', 'Molde para a mesa de ferraria. Feito no <b>Nature Infuser</b>: Molde de Melhoria de Netherita na entrada e o <b>Coração de Esmeralda</b> na alimentação.',
     [infuser('minecraft:netherite_upgrade_smithing_template', 'magicblocks:emerald_heart', 'magicblocks:royal_emerald_template')]),
    ('magicblocks:royal_emerald_pickaxe', 'A Picareta de Esmeralda melhorada (mesa de ferraria: <b>Molde de Esmeralda Real + Picareta de Esmeralda + Essência do Minerador</b>; mantém os encantamentos). Faz tudo o que a de esmeralda faz e mais: <b>Shift + bater num bloco</b> gasta <b>12 de mana</b> e deixa o bloco <b>energizado</b> (faíscas verdes); depois de <b>30s</b> ele quebra sozinho e solta o item — funciona até na <b>bedrock</b>. Respeita áreas protegidas.',
     [note('Mesa de ferraria: Molde de Esmeralda Real + Picareta de Esmeralda + Essência do Minerador.')]),
    ('magicblocks:manilium_upgrade_smithing_template', 'Molde da mesa de ferraria que transforma equipamento de netherita em Manilium.',
     [infuser('minecraft:netherite_upgrade_smithing_template', 'magicblocks:mana_essence', 'magicblocks:manilium_upgrade_smithing_template')]),
    ('magicblocks:soul_converter', 'Quando falta mana, paga a diferença com o seu XP: <b>120 pontos de XP = 1 de mana</b>. Funciona no inventário, no slot de amuleto do <b>Curios</b> (aparece no peito, estilo reator) ou embutido em qualquer peitoral.',
     [crafting('soul_converter'), infuser('minecraft:netherite_chestplate', 'magicblocks:soul_converter', 'minecraft:netherite_chestplate').replace(
         '<div class="hint">', '<div class="hint">qualquer peitoral recebe o conversor embutido &middot; ')]),
    ('magicblocks:unstable_condensed_mana_orb', 'Item de combate que guarda <b>10 de mana extra</b>. Não precisa segurar: basta estar no inventário, e ela é gasta sozinha quando a sua mana acaba (antes do XP do Conversor de Almas). Quando esvazia, <b>se desfaz</b>.',
     [crafting('unstable_condensed_mana_orb')]),
    ('magicblocks:stable_condensed_mana_orb', 'A versão estabilizada: também guarda <b>10 de mana</b> usada direto do inventário (as instáveis são gastas primeiro), mas <b>não quebra</b>. Jogue-a no chão em cima de um <a href="#nature-mana-well">Poço de Mana</a> com energia para recarregar: +1 de mana por segundo, 3.000 de energia cada.',
     [crafting('stable_condensed_mana_orb')]),
    ('magicblocks:mana_totem', 'O <b>Totem da Imortalidade de Mana</b> sai do <a href="rituais.html">ritual do Altar</a> (8 pedestais) com um Totem da Imortalidade no altar. Ele <b>não se gasta</b>: se você for morrer com ele no inventário (ou no slot de <b>amuleto/charm do Curios</b>) e tiver pelo menos <b>10 de mana</b> (contando orbes e o Conversor de Almas), ele gasta os 10 e te salva igual a um totem comum (volta com vida, Regeneração, Absorção e Resistência ao Fogo). Recarga de <b>1 minuto</b>. Não salva do /kill.',
     [table([('Salvar da morte', 'Precisa de 10 de mana; recarga de 1 minuto; funciona no inventário ou no Curios'),
             ('Vincular à Alma', 'No <b>Nature Infuser</b>: uma ferramenta, arma, armadura ou bloco + o Totem de Mana (o totem é gasto). O item ganha <b>✦ Vinculado à Alma</b> e não cai quando você morre: volta com você'),
             ('Curios', 'O Totem de Mana e também o <b>Totem da Imortalidade comum</b> vão no slot de amuleto (charm) e funcionam de lá')], head=('', 'Como funciona'))]),
    ('magicblocks:mana_battery', 'A <b>Bateria de Mana</b> guarda até <b>20 de mana</b>. Ela carrega em cima de um <b>Poço de Mana</b> com energia, ou ligada a ele por <b>Cabos de Mana</b> (até 64 cabos): +1 de mana por segundo (3.000 de energia do poço). Clique nela com uma <b>Orbe de Mana Estabilizada</b> ou com a <b>Bolsa de Orbes</b> para encher as orbes <b>na hora</b>; com a mão vazia, mostra quanto tem. O vidro sobe conforme a carga.',
     [crafting('mana_battery'), crafting('mana_cable')]),
    ('magicblocks:mana_pouch', 'Uma bolsa de Tecido de Mago com <b>3 espaços</b> para Orbes de Mana Condensada (instáveis e estabilizadas). A mana das orbes dentro dela é gasta sozinha, igual a das orbes soltas no inventário, com a bolsa no <b>inventário</b> ou no slot de <b>cinto do Curios</b>. Botão direito com ela na mão para abrir e colocar/tirar orbes.',
     [crafting('mana_pouch'), '<p class="tip">O <b>ferreiro goblin</b> transforma a bolsa na <b>Bolsa Mágica Melhorada</b>, com <b>5 espaços</b> (5 Tecidos de Mago + a bolsa + 2 linhas + 1 ouro).</p>']),
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
     [table([('<img class="mini" src="%s">Orbe de Mana' % icon('magicblocks:mana_orb'), 'Minério de Mana (e o Minério de Mana do Vazio)', '3 min'),
             ('<img class="mini" src="%s">Bloco de Diamante' % icon('minecraft:diamond_block'), 'Diamante', '3 min'),
             ('<img class="mini" src="%s">Bloco de Ferro' % icon('minecraft:iron_block'), 'Ferro', '3 min'),
             ('<img class="mini" src="%s">Bloco de Ouro' % icon('minecraft:gold_block'), 'Ouro', '3 min'),
             ('<img class="mini" src="%s">Barra de Netherita' % icon('minecraft:netherite_ingot'), 'Detritos Ancestrais', '3 min'),
             ('<img class="mini" src="%s">Barra do Vazio' % icon('magicblocks:void_bar'), 'Minério do Vazio e do Vazio Profundo', '3 min'),
             ('<img class="mini" src="%s">Cristal Abissal' % icon('magicblocks:abyssal_crystal'), 'Minério de Cristal Abissal', '3 min'),
             ('<img class="mini" src="%s">Barra de Metal Solar' % icon('magicblocks:sunsteel_ingot'), 'Minério de Metal Solar', '3 min')],
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
             ('Bloco de TNT', 'TNT', 'Bloco de TNT Ativo'),
             ('Bloco de Redstone', 'Bloco de TNT Ativo', 'Bloco de Redstone Instável')], head=('Entrada', 'Alimentação', 'Resultado')),
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
    ('magicblocks:ritual_altar', 'O centro dos <b>rituais</b>. Monte 4 <b>Pedestais</b> a 3 blocos do altar (norte, sul, leste e oeste, na mesma altura) e ligue o altar à energia de natureza pelos cabos (guarda 40.000). Clique no altar com o <b>catalisador</b>, coloque os 4 itens nos pedestais (em qualquer ordem) e clique no altar de <b>mão vazia</b>. Por 5 segundos, raios de luz saem dos pedestais até o altar; no fim, os itens são gastos e um raio (sem dano) cai no altar. Shift + direito de mão vazia tira o catalisador. Um <b>funil ou baú embaixo do altar</b> recebe o resultado do ritual (senão ele pula em cima do altar), e um funil pode colocar o catalisador.',
     [crafting('ritual_altar'), '<p class="tip">Todos os rituais vistos de cima, com cada item no seu pedestal, estão na aba <a href="rituais.html"><b>Rituais</b></a>.</p><h4>Como montar</h4><ol class="steps"><li>Coloque o <b>Altar</b> e ligue-o à energia (cabos de um Charger, gerador ou bateria).</li><li>Coloque <b>4 Pedestais</b> (comuns ou Arcanos) a <b>3 blocos</b> do altar: norte, sul, leste e oeste, <b>na mesma altura</b> do altar (2 blocos vazios entre o altar e cada pedestal).</li><li>Clique no altar segurando o <b>catalisador</b> (ele fica flutuando em cima).</li><li>Clique em cada pedestal segurando um dos 4 itens do ritual (qualquer ordem).</li><li>Clique no altar de <b>mão vazia</b>. Se aparecer "nenhum ritual usa esses itens", confira os itens; "faltam pedestais" = algum pedestal fora do lugar.</li></ol><div class="prints"><figure><img src="img/prints/altar_angulo.jpg" alt="Altar com os 4 pedestais" loading="lazy"><figcaption>Altar com os 4 pedestais</figcaption></figure><figure><img src="img/prints/altar_cima.jpg" alt="Visto de cima: pedestais a 3 blocos, em cruz" loading="lazy"><figcaption>Visto de cima: pedestais a 3 blocos, em cruz</figcaption></figure><figure><img src="img/prints/altar_ritual.jpg" alt="Ritual em andamento" loading="lazy"><figcaption>Ritual em andamento</figcaption></figure></div>', table([
         ('Chuva', 'Orbe de Mana', '2 Baldes de Água + 2 Cristais de Prismarinho', '5.000', 'Chove por 10 minutos (os baldes voltam vazios)'),
         ('Céu Limpo', 'Orbe de Mana', '2 Girassóis + 2 Pó de Pedra Luminosa', '5.000', 'Para a chuva e, se for noite, pula para a manhã'),
         ('Tempestade', 'Orbe de Mana', '2 Para-raios + 2 Pólvoras', '8.000', 'Tempestade com raios por 5 minutos'),
         ('Lua Roxa', 'Olho do Ender', '2 Fragmentos de Ametista + 2 Essências de Mana', '15.000', 'Chama a Lua Roxa agora (se for noite) ou na próxima noite'),
         ('Eclipse Solar', 'Fragmento Lunar', '2 Girassóis + 2 Obsidianas', '15.000', 'Chama o Eclipse Solar agora (se for dia) ou no próximo meio-dia'),
         ('Transmutação', 'Diamante', '2 Essências de Mana + 2 Esmeraldas', '6.000', '2 Diamantes Instáveis'),
         ('Bênção', 'Maçã Dourada', 'Essência de Mana + Pó de Blaze + Pena + Açúcar', '8.000', 'Força II, Velocidade II, Regeneração e Resistência por 5 min para todos a até 12 blocos'),
         ('Conhecimento', 'Livro', '2 Fragmentos Lunares + 2 Orbes de Mana', '20.000', '<b>+1 ponto de habilidade</b> para quem começou o ritual'),
         ('Estrela Despertada', 'Estrela de Mana', 'Fragmento Lunar + um Bloco Mágico + Essência do Void + Estrela do Nether', '25.000', 'Estrela de Mana Despertada (o bloco tem 30% de chance de sumir; senão fica no pedestal)'),
         ('Armadura Elemental', 'Peça de Armadura Elemental', 'O Bloco Mágico do elemento (para o Void: <b>Essência do Void</b>, o Bloco de Void não serve) + Cristal Instável + 2 Essências de Mana', '8.000', 'A peça ganha o elemento do bloco (o bloco tem 30% de chance de ser gasto; senão fica no pedestal)'),
         ('Bússola de Estruturas', 'Bússola', '4 Essências de Mana + 4 Teias (usa os 8 pedestais, incluindo as diagonais)', '8.000', 'Bússola Encantada: direito abre uma lista com busca de <b>todas as estruturas</b> (vanilla e de mods); escolha e ela aponta para a mais perto'),
         ('Bússola de Biomas', 'Bússola', '4 Essências de Mana + 4 Folhas quaisquer (8 pedestais)', '8.000', 'Bússola Encantada: lista com busca de <b>todos os biomas</b>; escolha e ela aponta para o mais perto'),
         ('Invocação do Golem', 'Um Bloco Mágico (não é gasto)', '2 Orbes de Mana + 2 Diamantes Instáveis', '20.000', 'Cria o <b>Invocador</b> do golem daquele elemento: coloque onde quiser para lutar com ele')],
         head=('Ritual', 'Catalisador (no altar)', 'Pedestais', 'Energia', 'Efeito'))]),
    ('magicblocks:nature_quarry', 'Uma máquina movida a <b>energia de natureza</b> (pelos cabos, guarda 40.000) que minera uma área de <b>9x9</b> embaixo dela, ou o <b>retângulo formado pelos Marcadores de Área</b> (até <b>64x64</b>), camada por camada, até o fundo do mundo: um bloco a cada 0,2s, 250 de energia por bloco, como uma picareta de diamante. Pula líquidos, blocos inquebráveis e blocos com inventário (baús, spawners...). Os itens vão para um <b>baú encostado</b> em qualquer lado; sem baú, ela guarda até 27 pilhas e pausa. Só trabalha com <b>sinal de redstone</b> (alavanca, tocha de redstone, botão... encostado). A <b>área que vai ser minerada aparece sempre</b>: uma caixa 9x9 do Minerador até a camada atual, com a camada sendo minerada destacada (verde = minerando, laranja = parado sem sinal ou sem energia, cinza = terminou). Não mina dentro da arena de um golem vivo.',
     [crafting('nature_quarry'), '<div class="prints"><figure><img src="img/prints/minerador.jpg" alt="Minerador ligado na redstone: a área aparece no chão" loading="lazy"><figcaption>Minerador ligado na redstone: a área aparece no chão</figcaption></figure></div>', table([('Direito', 'Mostra o estado, a camada e a energia; entrega os itens guardados'), ('Sinal de redstone', 'Liga (sem sinal fica parado)'), ('Shift + direito (mão vazia)', 'Recalcula a área pelos marcadores e recomeça do topo')], head=('Ação', 'Efeito'))]),
    ('magicblocks:quarry_marker', 'Uma tocha com cristal verde que <b>marca a área do Minerador da Natureza</b>. Coloque nos <b>cantos</b> da área (até 64 blocos do Minerador e na mesma altura, até 2 acima ou abaixo): o Minerador usa o <b>retângulo formado pelos marcadores</b>, até 64x64 (com um só marcador, o retângulo entre ele e o Minerador). A área é escolhida quando ele começa a minerar e aparece sempre no mundo; os marcadores não são minerados. Se passar de 64x64, ele avisa e usa a área padrão 9x9. A área começa na altura do Minerador e desce. Só o que fica <b>dentro</b> das tochas é minerado: a linha dos marcadores fica de pé.',
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
    ('magicblocks:nature_shield', 'Protege uma <b>área quadrada</b> de 25x25 (12 blocos para cada lado), de <b>12 blocos abaixo até 20 acima</b> do escudo. A borda aparece no chão como uma faixa de luz, acompanhando o terreno, igual aos anéis de fogo do golem. Escudos com áreas que se encostam ou se cruzam <b>se fundem</b>: aparece só o contorno de fora e os monstros são empurrados para fora do conjunto inteiro. Clique no bloco com um <b>corante</b> para mudar a cor do emblema e da área. O escudo <b>destrói projéteis</b> que não são de jogadores (flechas de esqueleto, bolas de fogo, disparos dos espíritos...) e <b>empurra os monstros</b> para fora. Não afeta chefes. 150 de energia por projétil e 20 por empurrão.',
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
    ('magicblocks:ancestral_sapling', 'A <b>Árvore Ancestral</b> é uma árvore gigante (~30 blocos) de folhas vermelhas, rara em <b>qualquer floresta</b>. Na base dela fica a <b>Raiz Ancestral</b> (tronco com runas douradas): clique para ganhar <b>1 Muda Ancestral</b> (uma por jogador em cada árvore). A muda cresce uma árvore do tamanho de um carvalho, mas <b>Maçãs Douradas</b> brotam embaixo das folhas e amadurecem em 4 estágios (madura, clique para colher ou quebre); as folhas <b>não soltam mudas</b>. Num <b>vaso</b> perto do Nature Charger ou do Nature Infuser, cada muda soma <b>+0,5x de natureza</b> (até 4 = +2x). A madeira tem todas as peças: tronco, madeira, descascados, tábuas, escada, laje, cerca, portão, porta, alçapão, botão, placa de pressão, placa e placa pendurada.',
     [note('Raiz Ancestral, na base da árvore gigante das florestas.')]),
    ('magicblocks:mastery_codex', 'A Mesa de Maestria <b>de bolso</b>. Segurando e clicando <b>usar</b>, abre a tela de maestria de qualquer lugar para <b>ligar/desligar as habilidades</b> de cada Bloco Mágico e os <b>Efeitos</b> (tipo shader) dos Blocos Verdadeiros e do Void. As melhorias (rituais) continuam só na mesa. Feito com a Mesa de Maestria no meio, 7 Altares de Ritual em volta e uma Barra de Manilium embaixo.',
     [crafting('mastery_codex')]),
    ('magicblocks:mastery_table', 'A <b>Árvore de Habilidades de cada Bloco Mágico</b>, estilo RPG. Clique na mesa <b>segurando um Bloco Mágico</b>: abre a árvore daquele bloco. <b>Usar o bloco sobe o nível dele</b> (cada mana gasta com ele na mão = 3 de XP da árvore, cada criatura morta = 10) e <b>cada nível dá 1 ponto</b> da árvore. Cada nó custa <b>pontos</b> (1; finais dos ramos 2; Maestria Suprema 3) <b>e níveis de XP</b> e só abre depois dos anteriores (linhas douradas = desbloqueado, ciano piscando = pode comprar). Sem bloco na mão, a mesa abre a tela de <b>ações</b> para ligar/desligar o que você não quer usar (ex.: o Shift + Bater do Bloco de Fogo) e os Efeitos dos Verdadeiros e do Void.',
     [crafting('mastery_table'),
      '<h4>A árvore</h4><pre class="ring">                 Despertar (1)\n        /             |             \\\nDano I (2)       Alcance I (2)      Economia I (2)\n | \\ Vampirismo (5) | \\ Agilidade (5) | \\ Fonte de Mana (5)\nDano II (4)      Alcance II (4)     Economia II (4)\nDano III (8)     Alcance III (8)    Economia III (8)\nGolpe Crítico (12) Recarga Rápida (12) Conjuração Livre (12)\n        \\             |             /\n            Maestria Suprema (20)</pre>',
      table([('Despertar', '1', 'Abre os 3 ramos'),
             ('Dano I / II / III', '2 / 4 / 8', '+15% de dano por nível em tudo que você causa segurando o bloco'),
             ('Vampirismo', '5', 'Cura 10% do dano causado com o bloco'),
             ('Golpe Crítico', '12', '20% de chance de 1,75x de dano'),
             ('Alcance I / II / III', '2 / 4 / 8', '+15% de alcance / raio por nível (jatos, raios, feixes, explosões...)'),
             ('Agilidade', '5', 'Velocidade I segurando o bloco'),
             ('Recarga Rápida', '12', 'Recargas 33% mais rápidas segurando o bloco'),
             ('Economia I / II / III', '2 / 4 / 8', '-20% de mana gasta por nível (a parte quebrada vira chance)'),
             ('Fonte de Mana', '5', '+1 de mana a cada 10s segurando o bloco'),
             ('Conjuração Livre', '12', '15% de chance de uma habilidade não gastar mana'),
             ('Maestria Suprema', '20', '+10% de dano e +10% de alcance; precisa dos 3 finais')], head=('Nó', 'Níveis de XP', 'Efeito')),
      '<p class="tip">O Blackstone Dourado só tem o ramo da Economia, o Spawner só Alcance e Economia, e o Bloco de Baú não tem árvore (só as ações). Cada bloco tem a sua árvore. Quem já tinha melhorias do ritual antigo continua com elas na árvore. O <b>Códice de Maestria</b> liga/desliga as ações de qualquer lugar.</p>']),
    ('magicblocks:pedestal', 'Expõe um item: clique com o item para colocar e com a mão vazia para pegar. Espadas ficam cravadas. É a peça dos <b>rituais</b>: 4 em volta do Altar de Rituais (veja a montagem com fotos no altar). Com folhas (ou o Bloco de Folha) em cima, fortalece o Nature Infuser. <b>Funis</b> colocam itens no pedestal vazio (1 por vez) e recolhem por baixo só as <b>sobras dos rituais</b> (baldes vazios...), nunca os ingredientes.',
     [crafting('pedestal')]),
    ('magicblocks:arcane_pedestal', 'A melhoria do pedestal, mais alto e com cristal: <b>funciona igual ao Pedestal</b> (guarda um item e conta nos rituais do Altar e no Nature Infuser) e solta partículas encantadas. Dá para misturar pedestais comuns e arcanos no mesmo ritual.',
     [crafting('arcane_pedestal')]),
    ('magicblocks:mana_controller', 'O <b>Armazenamento de Mana</b> guarda milhares de itens numa rede (no estilo do AE2 e do Refined Storage), movida a <b>energia de natureza</b>.',
     [table([('Controlador de Mana', 'O coração da rede. Recebe a energia do <b>Nature Charger</b> pelos Cabos de Natureza ou pelos Cabos de Rede e gasta 1 por tick + 1 por Leitor. Clique nele: abre a <b>telinha</b> com tudo o que está guardado (busca, quantidade de cada item, uso e energia). Clique com um <b>corante</b>: pinta a rede inteira dessa cor'),
             ('Controlador com Mesa', 'Feito no <b>Altar de Rituais</b> (o controlador no altar + 2 mesas de trabalho e 2 Essências de Mana). A tela ganha uma <b>grade 3x3 de criação</b> que usa os itens da rede: com o <b>JEI</b>, o "+" de uma receita puxa os itens da rede direto para a grade (com Shift, várias de uma vez). Depois de criar, a grade se enche de novo sozinha'),
             ('Leitor de Mana', 'Guarda até <b>4 Orbes de Condensação</b>; a frente mostra quantos estão encaixados. Quebrado, os orbes caem com tudo dentro'),
             ('Orbes de Condensação', 'Guardam uma <b>quantidade de itens</b> (não espaços), de quantos tipos quiser: <b>1k</b>, <b>4k</b>, <b>16k</b> e <b>64k</b> itens. Cada tamanho junta 4 do anterior'),
             ('Cabo de Rede', 'Liga o Controlador, os Leitores e outros cabos, e também leva a energia de natureza')], head=('Peça', 'Como funciona')),
      '<p class="tip">Na tela: clique esquerdo pega uma pilha (com um item na mão, guarda), direito pega metade (com um item, guarda 1), Shift + clique manda para o inventário e Shift + clique no inventário guarda na rede. Sem energia a rede desliga, mas nada se perde.</p>']),
    ('magicblocks:manilium_spawner', 'Um spawner melhorado: cria as criaturas <b>mesmo com luz</b>, mas só enquanto recebe <b>sinal de redstone</b>. Clique nele com um ovo gerador para escolher a criatura. Quebra com qualquer picareta e guarda a criatura escolhida. <b>Melhorias</b>: faça a melhoria no Nature Infuser (Pedra Lisa + o item) e clique no spawner com a <b>Chave de Spawner</b> (15% de chance ao quebrar um spawner; ela não é gasta). Abre uma tela com 4 espaços: coloque a melhoria para instalar e tire para remover. O spawner guarda as melhorias ao quebrar. <b>Açúcar</b> = Velocidade (até 10, no máximo 3x mais rápido); <b>Sinalizador</b> = Carregador de Chunk (até 1: mantém o chunk carregado e funciona sem jogador perto); <b>Cabeça de criatura</b> = Quantidade (até 5: +2 criaturas por vez); <b>Areia das Almas</b> = Dormente (até 1: as criaturas nascem <b>sem IA e sem som</b>).',
     [infuser('magicblocks:lifeless_spawner', 'magicblocks:manilium_ingot', 'magicblocks:manilium_spawner'),
      infuser('minecraft:smooth_stone', 'minecraft:sugar', 'magicblocks:spawner_upgrade_speed'),
      infuser('minecraft:smooth_stone', 'minecraft:beacon', 'magicblocks:spawner_upgrade_chunk'),
      infuser('minecraft:smooth_stone', 'minecraft:zombie_head', 'magicblocks:spawner_upgrade_count'),
      infuser('minecraft:smooth_stone', 'minecraft:soul_sand', 'magicblocks:spawner_upgrade_dormant')]),
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
         ('Shift + direito', 'Esqueleto campeão com cópia da sua armadura e da arma mais à esquerda da hotbar. Sabe usar <b>qualquer arco ou besta</b> (até de outros mods) e <b>Blocos Mágicos</b> (lança a magia do elemento de longe); com o <b>Bloco de Folha</b> ele não luta e fica <b>curando você</b>', '3')]),
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
      '<p class="tip">Blocos corrompidos ficam intangíveis por 15 segundos e depois voltam ao normal.</p>',
      '<p><b>Buraco Negro Solar</b>: o Bloco de Void + o <b>Coração da Luz</b> no <b>Nature Infuser</b> vira o buraco negro da arena da Guardiã da Luz: o mesmo poder, mas com o disco dourado e laranja, raios de luz, e as explosões e projéteis <b>põem fogo</b> nos atingidos.</p>']),
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
         ('Shift + segurar direito', '<b>Kamehameha</b>: carrega uma esfera de energia 3D nas mãos por 4 segundos (barra de carga acima da fome) e, ao soltar, dispara um feixe 3D brilhante que segue a mira. Disparar custa de 1 (carga fraca) a 4 de mana (carga cheia), e o feixe gasta mais 1 por segundo. Quanto mais carga, mais largo, longo e forte (até 10 de dano a cada meio segundo); cada acerto cura 1 coração', '1 a cada 3s')]),
      '<h4>Bloco de Redstone Instável</h4><p>No <b>Infusor da Natureza</b>, um Bloco de Redstone com um <b>Bloco de TNT ativo</b> vira o <b>Bloco de Redstone Instável</b> (nome em vermelho). Ele faz tudo o que o normal faz, mas os lasers <b>quebram blocos</b>: a faísca quebra o bloco que acerta e o Kamehameha abre um túnel por onde passa (com o que cair). Nunca quebra bedrock, blocos duros como obsidiana ou mais, nem baús/fornalhas, e respeita proteções de terreno.</p>'
      '<p><b>No Cajado Ancestral</b>, o laser do céu vira o <b>Laser Instável</b>: demora <b>5 segundos a mais</b> para carregar, gasta <b>15 de mana a mais</b> e cai com a grossura de toda a área do ataque (12 blocos de raio), <b>vaporizando tudo</b> que puder ser quebrado, de cima até bem abaixo do chão, com 18 de dano e fogo. Na carga o chão treme e solta faíscas; quem estiver por perto (até 160 blocos) vê o <b>céu escurecer</b> puxando para o vermelho, a luz pulsar e, no fim, uma <b>coroa de raios</b> em volta do laser. Ao carregar, o jogador ergue o cajado com as duas mãos (tremendo cada vez mais) e, ao soltar, desce o cajado num golpe apontando para o alvo.</p>']),
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
      '<p class="tip">A arena <b>não pode ser quebrada</b> enquanto o golem estiver vivo: nem na mão, nem por explosões, nem pela cratera da nuclear do Bloco de TNT, pela corrupção do Void ou pelo Minerador da Natureza. Na aba criativa há os <b>Invocadores</b> (um pedestal de cada golem) para colocar onde quiser. Todos também dão um <b>Esmagar</b> quando você está colado (disco vermelho em volta dele). Cada golem tem 175 corações, armadura, e deixa 75 de experiência, Essência de Mana, diamantes e itens do elemento (Coração do Mar, Maçã Dourada Encantada, sucata de Netherita...).</p>']),
    ('magicblocks:corrupted_fire_block', 'Os Blocos de Fogo, Folha, Blackstone Dourado, Spawner, Água, Gelo e TNT têm uma <b>versão corrompida</b> (escurecida e avermelhada), achada em baús de estruturas que combinam com ele. Funciona como o bloco normal, mas é <b>mais fraca</b> (quem segura causa 40% menos dano e se cura 40% menos) e aguenta só <b>2 usos</b>: cada habilidade usada gasta 1. Não pode ser consertada, encantada (nada de Remendo) nem colocada na Espada de Manilium.',
     [table([
         ('Bloco de Fogo Corrompido', 'Fortaleza do Nether', '30%'),
         ('Bloco de Folha Corrompido', 'Templo da Selva / Mansão da Floresta', '35% / 30%'),
         ('Bloco de Blackstone Dourado Corrompido', 'Bastião (tesouro / outros baús)', '50% / 15%'),
         ('Bloco de Spawner Corrompido', 'Masmorra', '25%'),
         ('Bloco de Água Corrompido', 'Ruínas Submersas (grande / pequena)', '30% / 15%'),
         ('Bloco de Gelo Corrompido', 'Iglu', '50%'),
         ('Bloco de TNT Corrompido', 'Pirâmide do Deserto', '30%')], head=('Bloco', 'Onde achar', 'Chance por baú'))]),
    ('magicblocks:sun_block', 'Um <b>pequeno sol</b> que flutua sobre a mão. Na mão (ou num <b>pedestal</b>) ilumina em volta e faz as <b>plantações crescerem 20% mais rápido</b> num raio de 8 blocos. <b>De dia</b> tudo fica uns <b>15% mais forte</b>.',
     [table([('Bater', 'Dispara um <b>laser</b> de 96 blocos que <b>atravessa</b> todas as criaturas na linha (14 de dano e fogo)', '1'),
             ('Shift + bater', '<b>Explosão solar</b> em volta (9 blocos): queima, cega e empurra os monstros', '3'),
             ('Segurar o direito', '<b>Feixe de luz contínuo</b> de 64 blocos que atravessa tudo e <b>esquenta</b>: fica mais grosso e mais forte quanto mais tempo você segura', '2 a cada 2s'),
             ('Shift + segurar o direito', 'Carrega <b>3 segundos</b> uma <b>bola de sol</b> sobre a cabeça; ao soltar ela voa <b>3x mais rápido</b> que a do Bloco de Fogo e explode num raio <b>5 blocos maior</b>, sem fogo no chão (e sem acertar você)', '4')]),
      note('<b>Altar de Rituais</b>: o <b>Coração da Luz</b> (o núcleo do sol, troféu da Guardiã do Sol) no altar, <b>4 Blocos de Fogo Verdadeiros</b> e <b>4 Orbes de Mana</b> (pedestais também nas diagonais).')]),
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
    ('magicblocks:elemental_chestplate', 'A <b>Armadura de Mago melhorada</b>: o mesmo modelo (chapéu, manto, calças e sapatos), com as cores do elemento. Receita: a peça de mago no meio com <b>Diamantes Elementais</b> em volta (chapéu 3, manto 7, calças 6, sapatos 2). Defesa de diamante, durabilidade quase de netherita, 2,5 de resistência e <b>conta como peça de mago</b> para a volta da mana. O <b>elemento</b> vem do <b>Altar de Rituais</b>: a peça no altar e, nos 4 pedestais, o <b>Bloco Mágico</b> do elemento, 1 Cristal Instável e 2 Essências de Mana (8.000 de energia). O bloco tem <b>30% de chance de ser gasto</b> (senão fica no pedestal). Dá para trocar de elemento depois. <b>Cada peça</b> vestida dá o efeito no nível 1; com as <b>4 peças</b> do mesmo elemento, nível 2.',
     ['<div class="pieces">%s</div>' % ''.join(slot('magicblocks:elemental_' + p) for p in ['helmet', 'chestplate', 'leggings', 'boots']),
      crafting('elemental_chestplate'),
      table([('Fogo', 'Bloco de Fogo', 'Resistência ao Fogo', 'Quem te bate pega fogo'),
             ('Água', 'Bloco de Água', 'Poder do Conduto', '+ Graça do Golfinho'),
             ('Gelo', 'Bloco de Gelo', 'Anda sobre a água; não congela nem fica lento', 'Anda sobre a lava também (vira obsidiana por um tempo)'),
             ('Trovão', 'Bloco de Trovão', 'Velocidade I', 'Velocidade II'),
             ('Redstone', 'Bloco de Redstone', 'Pressa I', 'Pressa II'),
             ('Folha', 'Bloco de Folha', 'Regeneração I', 'Regeneração II'),
             ('Sculk', 'Bloco de Sculk', 'Imune à Escuridão e Resistência I', 'Resistência II'),
             ('Void', 'Bloco de Void', 'Projéteis não acertam', 'O voo instável do Bloco de Void'),
             ('Dourado', 'Blackstone Dourado', 'Piglins não atacam e Sorte I', 'Sorte II'),
             ('TNT', 'Bloco de TNT', '-50% de dano de explosão', 'Imune a explosões'),
             ('Slime', 'Bloco de Slime', 'Super Pulo I', 'Super Pulo II e sem dano de queda'),
             ('Spawner', 'Bloco de Spawner', 'Força I', 'Força II'),
             ('Baú', 'Bloco de Baú', 'Visão Noturna', 'Herói da Vila')],
            head=('Elemento', 'Bloco no ritual', 'Cada peça', '4 peças')),
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
      '<h4>Rolar para desviar (tecla R)</h4><p>Com qualquer item (ou mão vazia), aperte <b>R</b> no chão para dar uma cambalhota na direção em que está andando (para frente se estiver parado). Durante a rolagem você fica <b>invulnerável por 0,4s</b> e desvia de qualquer ataque, inclusive dos golens. Recarga de <b>2 segundos</b>: um ícone ao lado direito da hotbar mostra quando dá para rolar de novo (apagado enquanto recarrega, pisca quando fica pronto). Gasta um pouco de fome. Não funciona na água, voando ou montado.</p>',
      '<h4>Câmera de ombro (TAB)</h4><p>Na terceira pessoa de costas (F5), aperte <b>TAB</b>: a câmera chega mais perto e vai para o ombro direito, e a <b>mira aparece no meio da tela</b>. O personagem vira para o ponto exato da mira, então golpes, magias e flechas vão onde você está mirando. TAB de novo desliga. A tecla pode ser trocada nos controles.</p>'])])

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
    ('minecraft:iron_sword', 'Nas <b>planícies</b> (e planícies de girassol) às vezes aparece um <b>Acampamento</b>: uma clareira de terra batida com uma <b>fogueira acesa</b>, troncos de banco, duas barracas de lã, um poste com lanterna, baú de suprimentos, barril, bancada e feno. É raro (no mínimo uns 640 blocos um do outro, e só em chão plano). Na fogueira fica o <b>Mestre Andarilho</b>, um viajante de capuz verde que não morre e não sai dali.',
     [table([('Conversar', 'Clique nele: ele oferece ensinar a <b>Trava de Mira</b> em troca de um <b>Bloco Verdadeiro</b>'),
             ('A troca', 'Clique nele <b>segurando um Bloco Verdadeiro</b> (qualquer um): ele fica com o bloco e você aprende a técnica para sempre (vale depois de morrer)'),
             ('Trava de Mira (tecla Z)', 'Olhe para uma criatura (até 32 blocos) e aperte <b>Z</b>: a câmera gira até ela e <b>fica presa</b>, com colchetes vermelhos na mira, o nome e a vida do alvo, e um anel vermelho girando em cima dele. Solta com Z de novo, quando o alvo morre ou passa de 40 blocos')],
            head=('', 'Como funciona')),
      '<p class="tip">A tecla Z pode ser trocada em Opções &gt; Controles &gt; Magic Blocks (Trava de Mira).</p>']),
    ('magicblocks:werewolf_spawn_egg', 'À noite, em qualquer bioma da Superfície (ao ar livre), às vezes aparece um <b>Lobisomem</b> (nas <b>noites de lua cheia</b> eles aparecem bem mais): preto com franjas cinza, olhos vermelhos, garras enormes. Anda curvado em pé e <b>corre de quatro</b>. Todo golpe <b>marca a área em vermelho no chão</b> antes de acertar. Solta <b>Pele de Lobo</b> e às vezes <b>Garras</b>.',
     [table([('Garrada', 'Disco vermelho na frente dele: ergue o braço e rasga'),
             ('Investida', 'Faixa vermelha até você: agacha, dispara de quatro e fere quem estiver no caminho'),
             ('Batida no chão', 'Disco grande em você: pula e esmaga com os dois punhos (empurra e deixa lento)')], head=('Ataque', 'Como funciona'))]),
    ('magicblocks:alpha_werewolf_spawn_egg', 'O <b>Lobisomem Alfa</b> (chefe, 420 de vida) vive no <b>Covil</b> ou, nas <b>savanas</b>, numa <b>arena ao ar livre</b> (um círculo de terra pisoteada com pedras em pé, crânios e um ninho de feno no meio). Ele nunca vai longe dela e, se ficar <b>3 minutos sem alvo</b> longe do centro, volta para lá num salto de sombra. O Covil é um buraco pequeno com pedregulho musgoso e ossos no chão das <b>taigas de pinheiros e abetos gigantes</b>, difícil de achar. Um túnel desce até uma caverna escura com ossos, teias, um ninho de feno e um baú. Ele é maior, mais bombado e tem crina prateada; faz os mesmos golpes, mais fortes e rápidos, e na metade da vida <b>uiva</b> (fica mais forte e rápido e deixa você lento). Solta peles, garras e o amuleto: o <b>Amuleto Alfa</b> só em <b>10%</b> das vezes; nas outras, o <b>Amuleto Quebrado</b> (também transforma, mas gasta <b>3 de mana</b> por período, não tem árvore e não embute em peitoral; conserte na bancada com uma <b>Pedra de Mana</b>).',
     [table([('Amuleto Alfa', '<b>Vinculado</b> a quem o veste primeiro: só funciona com essa pessoa e <b>não se perde ao morrer</b>. No colar do Curios, <b>sozinho no slot do peitoral</b> (4 de armadura) ou embutido num peitoral (Nature Infuser); aparece pendurado no peito. Na bancada, o amuleto (ou o peitoral com ele) + <b>qualquer corante</b> muda a <b>cor dos olhos</b> do lobisomem (e da pedra do colar). Com a mão vazia, segure <b>Shift + direito por 2s</b> para virar lobisomem (e de novo para voltar): o corpo se contorce, cresce e termina uivando'),
             ('Transformado', '<b>-50% de dano recebido</b>, <b>+25% de dano</b>, Velocidade I, <b>visão noturna</b>, sobe 1 bloco sem pular, <b>2,4 blocos de altura</b> (agachado passa por buracos de 2), corre de quatro, segura os itens nas garras e tem <b>+1 bloco de alcance</b>, bate com as <b>duas mãos</b> (os golpes alternam; na vez da esquerda vale a arma da segunda mão; mão vazia = garrada de 15) e tem esquiva própria no R. Gasta <b>1 de mana a cada 15s</b>'),
             ('Árvore do Amuleto', 'Clique na <b>Mesa de Maestria</b> com o amuleto na mão (a árvore só abre lá). Sangue Lupino abre 3 ramos: Fúria (Garras Afiadas, Sede de Sangue, Frenesi), Resistência (Pele Grossa, Regeneração Lunar, Pelagem de Ferro) e Caça (Faro: os monstros a 20 blocos brilham através das paredes; Salto do Predador, Fôlego). O <b>Bote</b> (depois das Garras Afiadas) libera a <b>investida</b>: segure o esquerdo com a mão vazia e solte (15 a 40 de dano). Ataques novos: <b>Esmagar</b> (depois do Bote: Shift + esquerdo com a mão vazia, salta bem alto e cai com os punhos, 14 de dano em 4 blocos; corpo a corpo, não gasta mana), <b>Dilacerar</b> (depois da Sede de Sangue: a 3ª garrada seguida sangra, +4 e Murchar II) e <b>Uivo</b> (depois do Faro: direito com a mão vazia, a única habilidade do lobisomem que gasta mana, Força II e Resistência por 20s e os monstros a 14 blocos ficam fracos, lentos e recuam; recarga 45s), que levam à forma <b>Alfa</b> (maior, crina prateada, +15% de dano, +10% de redução, Velocidade II). Usar transformado sobe o nível do amuleto e dá pontos; os nós custam pontos e níveis de XP. Com a forma Alfa, um botão na tela da árvore troca entre a forma <b>Alfa</b> e a <b>normal</b>'),
             ('Recargas na tela', 'Transformado (sobrevivência), ao lado do ícone da rolagem aparecem os ícones do <b>Bote</b>, <b>Esmagar</b> e <b>Uivo</b> com os segundos que faltam'),
             ('Aura de fúria', 'Com adagas em fúria nas mãos ou com o Uivo ativo, o lobisomem fica envolto numa aura de fúria')],
            head=('', 'Como funciona')),
      '<p class="tip">O Lobisomem Alfa agora luta com <b>duas adagas de ferro</b>.</p>']),
    ('magicblocks:iron_spear', 'As <b>Lanças</b> vêm nos mesmos materiais das adagas: <b>madeira</b>, <b>pedra</b>, <b>cobre</b>, <b>ferro</b>, <b>ouro</b>, <b>diamante</b> e <b>netherite</b> (esta na mesa de ferraria, a partir da de diamante). Batem um pouco mais forte e mais devagar que a espada e <b>alcançam 1,5 bloco mais longe</b>. <b>Segurando o direito</b> você recolhe a lança (até 1s) e, ao soltar, dá uma <b>Estocada</b>: avança e fura tudo numa linha de 5 blocos à frente, com até <b>150% do dano</b> (recarga de 2s). Receita: o material no canto de cima à direita e dois gravetos na diagonal.', []),
    ('magicblocks:iron_dagger', 'Existem adagas dos materiais das ferramentas vanilla: <b>madeira</b>, <b>pedra</b>, <b>cobre</b>, <b>ferro</b>, <b>ouro</b>, <b>diamante</b> e <b>netherite</b>. São rápidas e vão nas <b>duas mãos</b> (como as adagas do Leviatã), mas <b>não entram em fúria</b>.',
     [table([('Receita', 'Na bancada, o material na ponta e um graveto no cabo, na diagonal'),
             ('Netherite', 'Mesa de ferraria: adaga de diamante + lingote de netherite + molde de melhoria')], head=('', 'Como fazer'))]),
    ('magicblocks:goblin_spawn_egg', 'Nas <b>savanas</b> e <b>taigas</b> aparecem <b>Aldeias Goblin</b> (geradas como as vilas). Os <b>Goblins</b> têm 1,5 bloco de altura, uma <b>cabeça enorme</b>, olhões vermelhos, orelhas compridas, nariz comprido, presas e avental de couro, e andam em bando. Eles <b>abrem portas</b>, <b>não caem em armadilhas de alçapão</b> e quebram blocos simples no caminho (terra, madeira, tábuas e o que é feito delas, folhas). Podem usar <b>armadura</b> (menos capacete), não ferem os aliados e brigam com os outros <b>monstros</b> (que também atacam goblins, menos os creepers). Soltam moedas de madeira, às vezes uma <b>Orelha de Goblin</b> e uma Sopa de Mana.',
     [table([('Guerreiro', 'Espada; vai na frente e luta corpo a corpo'),
             ('Arqueiro', 'Arco, ou uma <b>zarabatana</b> com dardos de <b>veneno</b>; fica longe'),
             ('Mago', 'Fica longe e ataca (devagar) com um <b>Cajado Ancestral</b> com o bloco de <b>fogo</b>, <b>água</b>, <b>folha</b> ou <b>sculk</b>'),
             ('Ladino', 'Capuz preto e <b>duas adagas</b>: chega perto e <b>gira</b> como a Imperatriz Solar, cortando tudo em volta'),
             ('Ferreiro', 'Mora na <b>casa do ferreiro</b> (toda aldeia tem uma: bigorna, alto-forno, lava e chaminé) e vende armaduras e armas'),
             ('Xamã', 'Mora na <b>casa do xamã</b> (toda aldeia tem uma: telhado de azaleia, caldeirão, poções e ametista). Vende <b>orbes de mana condensadas</b> e os <b>Orbes de Condensação</b> do armazenamento; subindo de nível passa a vender orbes que guardam mais mana e compartimentos maiores (até o 64k e a Estrela de Mana)')], head=('Classe', 'Como luta')),
      '<p>A aldeia tem de <b>5 a 12 casinhas</b> (3 modelos, com <b>tapete no lugar da cama</b>; cada uma com 1 a 3 goblins), caminhos de terra, <b>Árvores de Mana</b> e <b>Árvores Ancestrais</b> (as da muda, que dão maçãs douradas) e <b>plantações de Cogumelo de Mana</b>: canteiros quadrados de grama. O cogumelo <b>brilha</b>, só fica na grama e com o tempo <b>se espalha</b> para um dos 8 lados. <b>3 cogumelos + tigela</b> = <b>Sopa de Mana</b>: devolve <b>6 de mana</b>, se toma rápido e empilha até 16.</p>',
      '<p><b>Bandos goblins</b>: nas savanas e taigas (com ou sem aldeia por perto), <b>de dia e de noite</b>, grupos de <b>3 a 5 goblins</b> aparecem de vez em quando a 24-40 blocos de você, como saqueadores, mas com mais frequência (sempre com um guerreiro, um arqueiro e um mago, e o resto sorteado). Não aparecem perto do Rei Goblin.</p>']),
    ('magicblocks:goblin_king_spawn_egg', 'Toda aldeia tem o <b>Salão do Rei</b>, a casa grande do meio, com trono de ouro e baús. Lá mora o <b>Rei Goblin</b> (chefe, 320 de vida): enorme e bombado, de coroa de ouro, ombreiras e capa, com uma <b>espada pesada</b>. Ele passeia pela aldeia. Cada golpe é <b>marcado em verde no chão</b> antes.',
     [table([('Corte', 'Disco na frente dele: ergue a espada e desce'),
             ('Giro', 'Anel em volta: gira com a espada'),
             ('Salto', 'Disco em você: pula e cai em cima'),
             ('Investida', 'Faixa até você: corre e atropela'),
             ('Combo', 'Três talhos seguidos andando para a frente; o último, de cima, é o mais forte'),
             ('Fenda', 'Faixa até você: crava a espada e uma rachadura corre pelo chão jogando para cima'),
             ('Grito de Guerra', 'Anel em volta (abaixo de 60% da vida): berra, empurra quem está perto e fica mais forte e mais rápido')], head=('Ataque', 'Como funciona')),
      '<p>Transformado em goblin ou com o respeito dos goblins, clique no Rei para abrir a tela de <b>desafio</b>: um duelo só com ele. Vencer o Rei (no desafio ou numa briga normal) dá o <b>respeito dos goblins</b>, e nenhum goblin continua brigando com você.</p>',
      '<p>A briga com o Rei é <b>só dele</b>: enquanto ele luta, os goblins saem de perto e não atacam quem está enfrentando o Rei. Ele não tem barra de vida.</p>',
      '<p class="tip">O Rei <b>não morre</b>: derrotado, ele volta para casa, <b>deita no tapete por 5 minutos</b> e levanta curado. Quando levanta, os goblins que morreram na aldeia <b>voltam</b> (saem do salão), inclusive o ferreiro e o xamã. Na primeira derrota sempre solta a <b>Espada Pesada Goblin</b> (depois, 15%): lenta, muito forte, empurra longe e <b>ocupa as duas mãos</b>: ao empunhar, o item da segunda mão vai para o inventário (sem espaço, a hotbar volta para o slot anterior e aparece "Eu preciso das duas mãos para usar isto"). As habilidades da Árvore da Espada só funcionam com ela <b>transformado em lobisomem</b>. Também espalha moedas de madeira.</p>']),
    ('magicblocks:ork_spawn_egg', 'Nas <b>florestas</b>, <b>planícies</b>, savanas e taigas, <b>de dia e de noite</b>, às vezes aparece um <b>Ork</b> (raro, nunca dois perto): um gigante verde de <b>5 blocos</b> e <b>330 de vida</b>, com presas, calça preta, cinto, botas com tachas e faixas nos pulsos. Ele <b>atravessa as copas quebrando as folhas</b>. Cada golpe é <b>marcado em vermelho</b> antes.',
     [table([('Rugido', 'Disco grande em volta: urra, <b>empurra para longe</b> e deixa lento'),
             ('Pisão', 'Bate o pé e solta uma <b>onda no chão</b> que se espalha: <b>pule</b> por cima dela'),
             ('Esmagada', 'Disco na frente: ergue os braços e esmaga'),
             ('Salto', 'Disco em você: pula e cai em cima')], head=('Ataque', 'Como funciona')),
      '<p>Também tem a <b>Investida</b> (faixa vermelha: dispara de cabeça baixa), a <b>Varrida</b> (leque na frente: gira o machado de lado) e o <b>Pedregulho</b> (disco em você: arranca um pedaço do chão, ergue sobre a cabeça e arremessa em arco).</p>',
      '<p class="tip">Metade deles carrega o <b>Machado do Ork</b>, que solta em <b>5%</b> das vezes: <b>40 de dano</b>, bate 2x mais devagar que um machado de pedra e <b>derruba a árvore inteira</b>. Todo Ork solta de <b>1 a 6 Ossos de Ork</b> (para o ferreiro goblin), couro e ferro.</p>']),
    ('magicblocks:goblin_crown', 'Depois de vencer o Rei, clicar nele abre a tela dele (verde e dourada) com a <b>missão dos Ossos de Ork</b>: ele quer <b>20 Ossos de Ork</b>, que podem ser entregues aos poucos (o botão Desafiar continua lá). Cumprida a missão: os <b>guerreiros</b> passam a lutar com a Espada de Osso de Ork, os <b>ladinos</b> com duas Adagas de Osso de Ork e o <b>ferreiro</b> com o Machado de Ork; você ganha a <b>Coroa do Príncipe Goblin</b> (inquebrável, +2 de armadura); e o <b>Construtor Goblin</b> levanta a casa dele perto do salão, bloco a bloco, com o <b>baú grande</b> que é o depósito da aldeia.',
     [table([('Lenhador', 'Machado na mão: acha árvores de verdade perto da aldeia, derruba tora por tora (de cima para baixo) e replanta a muda'),
             ('Patrulha', 'Faz a ronda em volta da aldeia e caça os monstros que chegam (menos creepers)'),
             ('Mineiro', 'Picareta: desce na <b>Mina</b> e tira pedra e minérios das paredes (carvão, ferro, cobre, ouro, redstone, lápis e, raramente, esmeralda e diamante). Precisa da Mina'),
             ('Colheita', 'Enxada: colhe o que está maduro no <b>Pomar</b>, replanta e apanha maçãs (às vezes uma dourada). Precisa do Pomar'),
             ('Descansar', 'Volta à vida normal, com a arma dele')], head=('Tarefa (com a coroa, clique no goblin)', 'O que faz')),
      '<p>O que os goblins juntam vai para o <b>baú grande do Construtor</b> quando a bolsa enche (16 itens). Morrendo, soltam o que estavam carregando.</p>',
      table([('Mina', '48 pedregulhos, 24 tábuas, 12 tochas, 8 trilhos', 'Buraco de 8x8 com 4 de fundo, borda de tábuas cercada, degraus, escoras, trilhos, tochas e um guindaste com lanterna'),
             ('Pomar', '4 mudas, 16 sementes de trigo, 6 cenouras, 6 batatas, 32 tábuas', '11x11 cercado com porteira: 4 árvores frutíferas floridas, trigo, cenoura, batata e beterraba, trilha em cruz com água no meio, espantalho')],
            head=('Construção', 'Materiais', 'Como é')),
      '<p>O <b>Construtor</b> vende as plantas: na tela dele aparecem os materiais (quanto você tem / quanto pede) e o botão <b>Encomendar</b>. Com a <b>Planta de Construção</b> na mão, a área da obra aparece onde você olha, <b>verde</b> se dá para construir ali e <b>vermelha</b> se não (com o motivo): tem que ser na aldeia, sem água e sem construções no caminho (só terra, pedra e plantas são limpas). Clique direito e o Construtor vai até lá e levanta a obra aos poucos. Cada aldeia tem uma de cada.</p>'
      '<p>As trilhas da aldeia que passam por água viram <b>pontes de tábuas</b> na altura da água.</p>']),
    ('magicblocks:ork_bone_sword', 'Depois de ganhar a <b>confiança do Rei Goblin</b> (vencendo ele), falar com o <b>ferreiro goblin</b> abre a <b>Forja do Ferreiro</b>: abas <b>Armas</b>, <b>Armaduras</b>, <b>Ferramentas</b> e <b>Magia</b>, a peça grande sobre a bigorna (setas ou rodinha do mouse para trocar), a fileira com todas as peças da aba e, à direita, os materiais com quantos você tem. <b>Forjar</b> gasta os materiais do inventário; <b>Trocas</b> abre a loja normal dele.',
     [table([('Adaga de Osso de Ork', '1 couro + 4 Ossos de Ork', '<b>35 de dano</b>. Uma em cada mão entra na <b>Fúria</b> como as adagas da besta, mas <b>sem o dash vermelho</b> no R e gastando <b>1 de mana a mais</b>'),
             ('Espada de Osso de Ork', '1 couro + 5 Ossos de Ork', '<b>45 de dano</b>'),
             ('Katana do Ronin', '3 Metal Solar + 2 Tecidos de Mago + 2 Barras do Vazio + 2 Cristais Abissais + 2 Garras de Leviatã', 'A lâmina dos deuses, a mesma do Ronin: <b>100 de dano</b> e <b>3 encaixes de pedra</b>. Só para quem passou por <b>todas as provações do Ronin</b>'),
             ('Peças de malha', 'Correntes', 'A cota de malha que só os goblins fazem'),
             ('Ferro', 'Lingotes e gravetos', 'Armas, armaduras e ferramentas de ferro, escudo, besta, tesoura e correntes'),
             ('Espelho da Alma Inativo', '8 Fragmentos de Espelho + 1 slime', '<b>Só sai daqui</b> (não tem mais receita na bancada)'),
             ('Bolsa Mágica Melhorada', '5 Tecidos de Mago + 1 Bolsa de Orbes + 2 linhas + 1 ouro', 'Guarda <b>5 orbes</b> (as da bolsa velha passam para a nova)')], head=('Peça', 'Materiais', 'O que é')),
      '<p class="tip">O ferreiro mora na casa do ferreiro de toda aldeia goblin.</p>']),
    ('minecraft:iron_sword', 'A <b>Árvore da Espada</b> vale para <b>qualquer espada</b> (vanilla, do mod ou de outros mods; adagas, luvas, lança e martelo não contam). Clique na <b>Mesa de Maestria</b> segurando uma espada (com a Espada de Manilium com bloco, <b>Shift</b> + clique abre a árvore do bloco). Os pontos vêm de <b>bater</b> e <b>derrotar</b> criaturas com espadas; cada nó custa pontos e níveis de XP. São <b>3 ramos de 4 nós</b> que se juntam no Mestre da Espada.',
     [table([('Fio Afiado', '+5% de dano com espadas (a raiz)'),
             ('Estocada Carregada', '<b>Ativa (carregada)</b>: segure o botão em que ela está equipada: a barra enche embaixo da mira e a lâmina solta faíscas quando está cheia. <b>Solte</b> e você dispara numa estocada que rasga o caminho (1,5x a 3x o dano da espada). Recarga de 3s'),
             ('Saque Rápido', 'A estocada carrega 35% mais rápido'),
             ('Estocada Perfurante', 'A estocada vai mais longe, <b>atravessa todos</b> no caminho, bate 25% mais forte e faz sangrar. Precisa da <b>1ª provação do Ronin</b>'),
             ('Estocada do Vento', 'No fim da estocada sai um <b>corte de vento</b> que segue em frente. Precisa de <b>todas as provações do Ronin</b>'),
             ('Pulo Duplo', 'Passiva: no ar, aperte pular de novo para um segundo pulo (uma vez até tocar o chão). Vale aprendido em qualquer das duas árvores'),
             ('Lâmina Afiada', '+10% de dano com espadas'),
             ('Golpe Crítico', '20% de chance de um golpe causar 1,6x o dano'),
             ('Corte Profundo', 'Os críticos fazem sangrar (Wither II por 3s)'),
             ('Redemoinho', '<b>Ativa (carregada)</b>: segure e solte para girar com a espada esticada, cortando tudo em volta várias vezes (mais carga = mais tempo girando). Recarga de 3,5s'),
             ('Guarda', '-10% de dano recebido segurando uma espada'),
             ('Vampirismo', 'Os golpes de espada curam 8% do dano'),
             ('Firmeza', '60% menos empurrão e mais 5% de redução de dano'),
             ('Contra-Ataque', '<b>Ativa (no clique)</b>: por 0,6s o próximo golpe corpo a corpo de frente é bloqueado e devolvido com 1,5x o dano. Recarga de 2,5s'),
             ('Mestre da Espada', 'Precisa dos 3 finais e de <b>todas as provações do Ronin</b>: +10% de dano e as habilidades recarregam 2x mais rápido'),
             ('Imbuir Mana', '<b>Técnica do Ronin (segurar)</b>: enquanto o botão fica apertado a mana corre pela lâmina (chamas azuis) e os golpes, inclusive a Estocada e o Redemoinho, batem <b>50% mais forte</b>. Gasta 1 de mana ao começar e mais 1 a cada 3s segurando'),
             ('Aparar', '<b>Técnica do Ronin (clique)</b>: como o aparar do Escudo Solar, mas em vez de devolver ele <b>anula</b>: por 1s o próximo golpe, magia ou projétil de frente não causa dano e quem atacou fica <b>atordoado 2s</b> (não consegue atacar nem se mover; estrelas girando sobre a cabeça). Recarga de 3s')], head=('Nó', 'O que faz')),
      '<h4>Habilidades nos botões do mouse</h4><p>Na tela da árvore, à direita, ficam os <b>dois botões do mouse</b> (o desenho do mouse com o botão aceso). Clique no espaço de um botão para trocar a habilidade ativa dele entre as que você já comprou e <b>Sem habilidade</b> (clique esquerdo avança, direito volta). A mesma habilidade não fica nos dois botões. A Estocada começa no botão esquerdo. As habilidades <b>carregadas</b> (Estocada, Redemoinho) disparam ao soltar; as de <b>clique</b> (Contra-Ataque, Aparar) na hora; a de <b>segurar</b> (Imbuir Mana) fica ligada enquanto o botão está apertado. Habilidades corpo a corpo <b>não gastam mana</b>, só o Imbuir. Em sobrevivência, as habilidades equipadas aparecem <b>ao lado do ícone da rolagem</b> com a recarga. Carregando no botão direito, a segunda mão não bate.</p>',
      '<p class="tip">Em terceira pessoa toda espada tem <b>animação de corte</b> cinematográfica, e cada habilidade tem a sua: a estocada (carga e avanço com o corpo inteiro), o Redemoinho (o corpo todo gira com a espada esticada) e o Aparar (lâmina de pé na frente do corpo).</p>']),
    ('magicblocks:iron_dagger', 'A <b>Árvore das Adagas</b> vale para <b>qualquer adaga</b> (de minério, de cristal instável, as da besta, a solar, a de osso de ork e adagas de outros mods). Clique na <b>Mesa de Maestria</b> segurando uma adaga. Os pontos vêm de <b>bater</b> e <b>derrotar</b> criaturas com adagas. São <b>3 ramos de 4 nós</b> que se juntam no Mestre das Lâminas.',
     [table([('Lâminas Ligeiras', '+5% de dano com adagas (a raiz)'),
             ('Giro das Lâminas', '<b>Ativa (carregada)</b>, com <b>uma adaga em cada mão</b>: segure para enrolar o corpo e solte para girar cortando tudo em volta. Recarga de 4s'),
             ('Giro Ligeiro', 'O giro carrega 35% mais rápido'),
             ('Ciclone', 'O giro dura mais, alcança mais longe, bate 15% mais forte e <b>puxa os inimigos</b>'),
             ('Dança das Lâminas', '<b>Ativa (carregada)</b>, uma adaga em cada mão: dispara de 4 a 8 blocos para a frente, <b>intocável</b>, cortando cada inimigo no caminho. Recarga de 4s'),
             ('Fúria da Besta', '<b>Ativa (carregada)</b>, uma das primeiras: com uma <b>adaga de fúria em cada mão</b> (da besta, Celestial, do Caos, Solar ou de Osso de Ork), segure o botão em que ela está equipada por <b>3s</b> e solte para entrar em fúria (Força, Regeneração, aura vermelha e o dash vermelho no R; gasta mana a cada 20s). O atalho antigo (Shift + direito 3s) também só funciona com ela comprada'),
             ('Lâminas Envenenadas', '25% de chance de envenenar (Veneno II por 3s)'),
             ('Apunhalar', '+50% de dano acertando <b>pelas costas</b>'),
             ('Execução', '+60% de dano em alvos com menos de 30% de vida'),
             ('Passo Sombrio', '<b>Ativa (no clique)</b>: aparece nas costas do inimigo na mira (até 14 blocos); o próximo golpe em 3s bate 50% mais forte. Recarga de 6s'),
             ('Pulo Duplo', 'Passiva: no ar, aperte pular de novo para um segundo pulo'),
             ('Esquiva', '10% de chance de desviar de um golpe corpo a corpo segurando uma adaga'),
             ('Passo Cortante', 'Passiva (depois da Esquiva): com uma adaga na mão, a esquiva (R) <b>para a frente</b> vira um passo rápido de 4,5 blocos que corta quem estiver no caminho; para os lados e para trás continua a rolagem'),
             ('Combo', '<b>Técnica do Pantan0 (clique)</b>: a outra habilidade equipada é usada <b>3 vezes seguidas</b>, com 1s entre elas (as carregadas saem cheias); depois 10s de recarga'),
             ('Embalo', 'Cada golpe com adaga dá Velocidade II por 2s'),
             ('Acrobata', 'Quedas contam 6 blocos a menos e tiram metade do dano'),
             ('Fantasma', 'Ao se esquivar, fica invisível por 2s e o próximo golpe bate 50% mais forte'),
             ('Mestre das Lâminas', 'Precisa dos 3 finais: +10% de dano e as habilidades recarregam 2x mais rápido')], head=('Nó', 'O que faz')),
      '<p>As habilidades ativas vão nos <b>botões do mouse</b> do mesmo jeito que na Árvore da Espada (o Giro começa no esquerdo).</p>',
      '<p class="tip">Em terceira pessoa as adagas têm <b>golpes rápidos</b> alternando as mãos (os cortes formam um X), o giro com os braços abertos, a Dança (corpo baixo com as adagas para trás e passadas rápidas) e o Passo Sombrio (as duas adagas cravam juntas de cima).</p>']),
    ('magicblocks:ronin_spawn_egg', 'Nos <b>bosques de cerejeira</b> fica o <b>Dojo do Ronin</b>: um salão japonês aberto sobre um tablado de madeira escura com tatame de bambu, pilares vermelhos, grade baixa em volta (a arena), telhado de telhas escuras em camadas e lanternas. No meio está o <b>Ronin</b>, um chefe maior que o jogador: chapéu de palha, máscara de samurai, ombreiras laqueadas, capa carmesim e a <b>Katana do Ronin</b>, que ele segura com as duas mãos. Durante o desafio os olhos dele brilham em vermelho. Ele <b>não tem barra de vida</b> e, fora de um desafio, <b>nada o machuca</b>. Fale com ele para abrir a tela da <b>provação</b>: os itens pedidos (dá para <b>entregar aos poucos</b>) e o botão <b>Desafiar</b>, que acende quando tudo foi entregue.',
     [table([('1ª provação', 'Não pede nada. <b>1000 de vida</b>: <b>Corte</b> (disco na frente), <b>Sequência</b> (três cortes avançando) e <b>Estocada</b> (faixa até você e dispara em linha reta). Vencer libera a <b>Estocada Perfurante</b>'),
             ('2ª provação', 'Pede <b>10 Orelhas de Goblin</b>. <b>1500 de vida</b> e os mesmos golpes, mas <b>metade deles com mana na espada</b>: marcados em <b>azul</b>, com chamas azuis na lâmina, e batem <b>50% mais forte</b>. Vencer: você escolhe entre dois ícones, <b>Imbuir Mana</b> ou <b>Aparar</b>'),
             ('Última provação', 'Pede <b>5 Ossos de Ork</b>, <b>2 Garras de Leviatã</b>, <b>1 Estrela do Vazio</b> e <b>5 Metal Solar</b>. <b>2000 de vida</b>, <b>todos os golpes com mana</b> e três novos: <b>Corte Relâmpago</b> (um X no chão em volta de você; ele atravessa as duas diagonais num piscar de olhos), <b>Lua Crescente</b> (gira com um anel marcado em volta e solta uma onda de corte pela faixa) e <b>Queda do Céu</b> (salta, paira sobre você com o disco marcado e cai com a katana). Vencer ensina a <b>outra técnica</b>, libera a Estocada do Vento e o Mestre da Espada, dá o <b>Chapéu de Palha do Ronin</b> e manda você atrás de um ferreiro'),
             ('Chapéu de Palha do Ronin', 'O troféu das provações: <b>inquebrável</b>, <b>+5% de dano com espadas</b> (não adagas); como capacete dá <b>+4 de armadura</b>; no slot de cabeça do Curios só o dano')], head=('', 'Como funciona')),
      table([('Teto de dano', 'Ele não recebe mais de <b>20 de dano por golpe</b>, nem refletido'),
             ('Projéteis e magias', 'Em qualquer fase, a espada imbuída de mana <b>devolve</b> para quem lançou'),
             ('Adagas', 'Não ferem o Ronin ("É sério? Você trouxe facas para uma briga de espada?")'),
             ('Escudo', 'Bloquear a <b>Estocada</b> com escudo <b>desativa o escudo</b>'),
             ('Intrometidos', 'Se outro jogador bater nele no meio de um duelo, ele <b>recupera toda a vida</b> e passa a ter <b>3x a vida e o dano</b>, gastando <b>4x</b> as armaduras e escudos'),
             ('Ritmo', 'Ele ataca com calma: pausas longas entre os golpes')], head=('Regra do dojo', '')),
      '<p class="tip">Só quem desafiou consegue machucar o Ronin. Se você morrer, sair de perto (40 blocos) ou mudar de dimensão, o desafio acaba e ele volta ao centro curado (os itens entregues não se perdem). Vencido, ele não morre: volta para o centro do dojo.</p>']),
    ('magicblocks:pantano_spawn_egg', 'No <b>Pântano Abissal</b> (Vazio) às vezes aparece a <b>Arena do Pantan0</b>: um tablado redondo sem paredes, com froglight no centro, anel de ametista com velas roxas, tijolos de lama com musgo, borda de pedra-negra e mangue, postes com lanternas de alma, estandartes roxos e cristais. <b>Nenhum monstro nasce nela nem perto</b>. No meio está o <b>Pantan0</b>, mestre das adagas, com duas <b>Adagas Abissais</b>. Ele <b>só conversa com quem lhe entrega uma sopa de cogumelos</b> (a tela de provação, como a do Ronin). Os golpes dele são sempre <b>avisados em roxo</b>.',
     [table([('1ª provação', '<b>1500 de vida</b>: <b>Investida</b> (faixa), <b>Giro</b> com as adagas (anel em volta) e <b>Salto</b> em direção a você (disco). Vencer ensina o <b>Giro das Lâminas</b>'),
             ('2ª provação', 'Ele invoca <b>4 Golens Fragmentados</b> e fica observando. Eles não soltam nada; se você se afastar da arena eles somem e a provação falha. Derrotar os 4 dá a <b>Sopa Abissal</b>'),
             ('3ª provação', '<b>2000 de vida</b>: <b>Combo</b> (três golpes seguidos, 1s entre eles), Investida, Giro, Salto e, aos <b>50% da vida</b>, a <b>Fúria</b>: volta ao centro, entra em fúria roxa e volta mais rápido e forte. Vencer ensina o <b>Combo</b> e dá <b>3 Barras Abissais</b>'),
             ('Regras', 'Só <b>adagas</b> o ferem ("Eu só acho que 2 é melhor do que um, não?"); no máximo <b>20 de dano por golpe</b>; projéteis e magias voltam; um intrometido no duelo o deixa com 3x a vida e o dano')], head=('', 'Como funciona')),
      table([('Sopa Abissal', 'Parece a sopa de cogumelos: <b>5 usos</b>, cada gole (o tempo da Sopa de Mana) recupera <b>3 corações e 3 de fome</b> e lembra as lutas de HG. Vazia vira o <b>Pote Abissal</b>: na bancada com um <b>cacto</b>, <b>qualquer cogumelo</b> ou <b>semente de cacau</b> volta a ter 5 usos'),
             ('Adaga Abissal', 'A adaga do Pantan0, em 3D: lâmina de obsidiana com o sulco de ametista brilhando, guarda em crescente e gema. <b>80 de dano</b>; uma em cada mão entra na <b>Fúria roxa</b>. Só sai com <b>3 Barras Abissais</b> na diagonal'),
             ('Barra Abissal', 'Da 3ª provação do Pantan0 ou do <b>Minério Abissal</b>: um só, raríssimo, por região de Pântano Abissal, escondido na pedra do Vazio (picareta de diamante)')], head=('Item', 'O que é')),
      '<p class="tip">Com <b>shaders</b> (Oculus/Iris) a borda cósmica do Manilium vira uma galáxia pintada e os olhos brilhantes das criaturas não aparecem mais através das paredes.</p>']),
    ('magicblocks:soul_mirror', 'O <b>Espelho da Alma</b> guarda as almas das criaturas que você derrota e deixa você <b>virar</b> elas. Primeiro peça o <b>Espelho da Alma Inativo</b> ao <b>ferreiro goblin</b> (na forja dele, depois de ganhar a confiança do Rei Goblin): 8 <b>Fragmentos de Espelho das Almas</b> + 1 <b>slime</b>. Depois desperte-o no <b>Altar de Rituais</b> (o inativo no altar + <b>Orbe de Mana</b>, <b>Estrela do Nether</b>, <b>Essência de Mana</b> e um <b>Bloco Verdadeiro</b>). Funciona só de estar no <b>inventário</b> (ou no Curios) e <b>não cai ao morrer</b>.',
     [table([('Almas', 'Com o espelho no inventário, toda criatura que você derrota <b>pela primeira vez</b> tem a alma absorvida (a alma voa até você)'),
             ('Virar (tecla \')', 'Abre a tela de formas: cada alma aparece em miniatura com o custo. Clique para virar a criatura (tamanho, modelo e características); <b>Forma humana</b> volta ao normal'),
             ('Custo de mana', 'Comuns (monstros e animais normais, goblins): <b>1 a cada 25s</b>. Mais fortes (mais de 40 de vida, como o golem de ferro): <b>2 a cada 25s</b>. Chefes até 500 de vida: <b>3 a cada 20s</b>. Mais fortes que isso: <b>4 a cada 15s</b>. Sem mana, volta a ser humano'),
             ('Características', 'Sendo monstro, <b>os monstros não te atacam</b> (a menos que você bata neles; os chefes atacam). Zumbis e esqueletos <b>pegam fogo no sol</b>. Abelhas, morcegos, ghasts, blazes, fantasmas e afins <b>voam</b>. Quem não queima fica imune a fogo; aquáticos respiram na água; aranhas <b>sobem paredes</b>; galinhas caem devagar; cavalos, lobos e coelhos correm mais; coelhos e slimes pulam mais'),
             ('Poderes', 'Segure o <b>botão esquerdo com a mão vazia</b>: creeper <b>explode</b> (segurando 1,5s), enderman <b>teleporta</b>, blaze, ghast, wither e dragão <b>atiram</b>, esqueleto atira flecha, golem de ferro <b>esmaga o chão</b>, bruxa joga poção, evocador chama presas, warden solta a <b>rajada sônica</b>, golem de neve joga bolas de neve')],
            head=('', 'Como funciona')),
      '<p class="tip">A <b>Árvore do Espelho</b> abre clicando na <b>Mesa de Maestria</b> com o espelho na mão. Os pontos vêm das almas novas e do tempo transformado: Elo da Alma (cura e fica invisível ao trocar), Alma Leve e Alma Serena (a mana dura mais), Instinto e Eco (poderes recarregam mais rápido e ficam mais fortes), Vitalidade e Forma Ágil (+2 corações, mais velocidade e voo) e o Mestre das Formas (toda forma gasta 1 de mana a menos).</p>']),
    ('magicblocks:wooden_coin', 'Os goblins <b>negociam</b> em <b>Moedas de Madeira</b> (eles soltam as moedas e também compram coisas de você). Mas só negociam com quem é goblin ou com quem eles <b>respeitam</b>. O Rei Goblin não negocia.',
     [table([('Como goblin', 'Transformado em goblin pelo <b>Espelho da Alma</b>: clique num goblin para abrir a loja dele'),
             ('Duelo', 'Transformado em goblin, <b>Shift + clique</b> num goblin desafia ele para um duelo (os outros não entram). Deixe ele quase sem vida (ele se rende, não morre) e você ganha o <b>respeito dos goblins</b>'),
             ('Respeito', 'Para sempre (mesmo morrendo): os goblins negociam com você sem a forma e <b>só o goblin em que você bater revida</b>'),
             ('Níveis', 'Como os aldeões, <b>todo goblin sobe de nível</b> (1 a 4) conforme você negocia com ele (barra de progresso na loja) e passa a vender coisas melhores')], head=('', 'Como funciona')),
      table([('Guerreiro', 'Espada de ferro, escudo', 'Peças de malha', 'Espada com Afiação II, capacete de ferro', 'Espada de diamante, escudo com Inquebrável III'),
             ('Arqueiro', 'Flechas, arco', 'Flechas de veneno, zarabatana', 'Besta, flechas espectrais', 'Arco com Força III, flechas de dano'),
             ('Mago', 'Sopa e Cogumelos de Mana', 'Essência de Mana, poção de cura', 'Frascos de experiência, regeneração', 'Força II, maçã dourada'),
             ('Ladino', 'Adaga de ferro', 'Adaga de ouro, invisibilidade', 'Pérolas do fim, velocidade', 'Adagas de esmeralda e de diamante'),
             ('Ferreiro', 'Botas e machado de ferro', 'Peitoral e calças de ferro, escudo', 'Peitoral com Proteção II, bigorna', 'Peitoral e picareta de diamante')],
            head=('Classe', 'Nível 1', 'Nível 2', 'Nível 3', 'Nível 4')),
      '<p class="tip">No nível 1 eles também <b>compram</b>: o guerreiro ferro e couro, o arqueiro linha e penas, o mago glowstone e lápis, o ladino pepitas de ouro e olhos de aranha, o ferreiro ferro e carvão, o xamã ossos.</p>']),
    ('magicblocks:goblin_ear', 'No <b>Acampamento</b>, junto do Mestre Andarilho, agora fica o <b>Caçador</b> (chapéu de couro e aljava). Clique nele com <b>Orelhas de Goblin</b> na mão: ele paga <b>2 a 4 Moedas de Prata</b> por orelha. Sem orelhas, ele abre a loja dele (flechas, flechas espectrais, arco com Força, besta com Recarga Rápida, luneta, cenouras douradas e maçã dourada), paga em prata.',
     ['<p class="tip">As orelhas só caem de goblins derrotados por você (45%, mais com Pilhagem).</p>']),
    ('magicblocks:werewolf_glove', 'A <b>Luva de Lobisomem</b> é uma arma rápida que se <b>veste na mão</b>: aparece no braço do jogador (primeira e terceira pessoa), sem precisar do Curios. Vai nas <b>duas mãos</b>: com uma em cada, os golpes alternam como as adagas.',
     ['<p class="tip">Receita na bancada: Garras de Lobisomem na coluna da esquerda e Pele de Lobo nas outras duas, com o meio da direita vazio.</p>']),
    ('magicblocks:chosen_flower', 'A <b>Flor do Escolhido</b> é raríssima e nasce em <b>qualquer floresta</b> (2 blocos de altura, brilha). Quem a pega primeiro é <b>escolhido</b>: ela fica vinculada a você.',
     [table([('Mana de longe', 'Plante-a com um <b>Poço de Mana</b> dentro do quadrado <b>5x5</b> em volta dela (a flor no meio): o poço enche a <b>sua</b> mana de <b>qualquer distância</b>, gastando <b>6x mais energia</b>'),
             ('Carrega a região', 'A flor mantém carregados os chunks em volta (o poço, o Nature Charger e os cabos continuam funcionando sem ninguém perto)'),
             ('O preço', 'Os <b>monstros vêm atrás dela</b> (até 20 blocos) e arrancam as pétalas (20 de vida; se ninguém encostar por 10s, ela se recupera). Se ela <b>morrer</b>, não solta nada e <b>você morre junto</b> (mesmo fora do jogo: morre ao entrar)')],
            head=('', 'Como funciona'))]),
    ('magicblocks:wolf_helmet', 'A <b>Armadura de Lobo</b> é feita de <b>Pele de Lobo</b> (mesmas receitas da armadura de couro). Protege como <b>ferro</b>, o capacete é uma <b>cabeça de lobo</b> com a mandíbula de cima sobre o rosto, e o peitoral, as calças e as botas têm pelagem, patas e garras.',
     [table([('Esquiva', 'Cada peça recarrega a <b>rolagem 3 ticks mais rápido</b> (12 ticks com as 4)'),
             ('Cor', 'Pinte como a armadura de couro: na bancada junto com corantes')], head=('', 'Como funciona'))]),
    ('minecraft:spawner', 'Uma masmorra <b>subterrânea e rara</b> (entre as camadas -30 e 20, em qualquer bioma da Superfície). No centro, um salão com o <b>baú final</b> e um spawner de zumbi ou esqueleto; dele saem 4 corredores com <b>armadilhas de flechas</b> (placas de pressão atravessando o corredor) até 4 salas, uma por elemento. Cada sala tem o seu <b>Guardião</b>: um Espírito Elemental com 40 corações e mais dano, que não sai da sala, e um baú do elemento.',
     [table([('Fogo (norte)', 'Tijolos do Nether, blocos de magma e poços de lava', 'Varas de Blaze, Creme de Magma'),
             ('Água (sul)', 'Prismarinho, lanternas do mar e uma piscina', 'Fragmentos de Prismarinho, às vezes Coração do Mar'),
             ('Gelo (leste)', 'Gelo compactado e azul, buracos de neve fofa', 'Gelo Azul, Gelo Compactado'),
             ('Trovão (oeste)', 'Cobre e para-raios', 'Barras de Cobre, Para-raios')], head=('Sala', 'Como é', 'Baú do elemento')),
      '<p class="tip">Os baús das salas podem ter o <b>Bloco Corrompido</b> do elemento e peças da <b>Armadura Elemental</b> já com o elemento. O baú final tem estilhaços, Diamantes Instáveis, Orbes, diamantes, livros encantados e às vezes um Bloco Corrompido, uma ferramenta instável ou um Peitoral Elemental. Cada Guardião solta 2 ou mais Estilhaços Instáveis e Essência de Mana.</p>']),
    ('magicblocks:lunar_fragment', 'Em uma noite rara (<b>1 em 10</b>, a partir do 4º dia) ou chamada pelo <b>Ritual da Lua Roxa</b>, a lua fica roxa, o céu e a neblina ficam roxos e ninguém consegue dormir. Vêm <b>5 ondas</b> de monstros, uma por minuto, em volta de cada jogador na Superfície: zumbis, esqueletos, bruxas, magos e Espíritos Elementais (brilhando), cada onda maior. Depois da última chega o <b>Arauto da Lua Roxa</b>: uma Sentinela Arcana com 150 corações. Todos os monstros das ondas têm <b>contorno roxo brilhante</b> (dá para ver através das paredes) e não somem sozinhos. Se a meia-noite chegar antes de você vencer, <b>a lua para no meio do céu</b> até todos os monstros roxos e o Arauto caírem (a barra mostra quantos faltam); depois o tempo volta a correr.',
     ['<div class="prints"><figure><img src="img/prints/lua_roxa.jpg" alt="A lua roxa no alto do céu" loading="lazy"><figcaption>A lua roxa no alto do céu</figcaption></figure><figure><img src="img/prints/lua_roxa_monstros.jpg" alt="A noite da Lua Roxa" loading="lazy"><figcaption>A noite da Lua Roxa</figcaption></figure></div>',
      '<p class="tip">Os monstros da Lua Roxa soltam <b>Fragmentos Lunares</b> (35%). O Arauto solta 4 a 6 fragmentos, Diamante Instável e dá 1 ponto de habilidade. A Lua Roxa acaba quando amanhece.</p>']),
    ('minecraft:enchanted_book', 'Aperte <b>K</b> para abrir os <b>Atributos</b>, no estilo de D&amp;D. A cada <b>nível de XP</b> que você <b>alcança pela primeira vez</b> ganha 1 ponto (cada atributo vai até <b>100</b>; gastar níveis encantando não tira pontos). Chefes dão pontos bônus (golem: 2; Sentinela Arcana e Arauto da Lua Roxa: 1) e o Ritual do Conhecimento dá 1. Cada atributo vai de <b>0 a 100</b> e os <b>primeiros pontos rendem mais</b>: com 10 pontos você já tem cerca de 19% do máximo, com 25 quase metade, com 50 três quartos (passe o mouse num atributo para ver o bônus <b>atual</b>). Redistribuir tudo custa 10 níveis de XP. Os pontos não se perdem ao morrer.',
     [table([('Força', '+6 de dano corpo a corpo'), ('Destreza', '+20% de velocidade e +25% de velocidade de ataque; a rolagem recarrega de 2s até 0,75s e fica até 0,9s invencível'),
             ('Constituição', '+10 corações e 40% de resistência a empurrão'),
             ('Inteligência', '+10 de mana máxima e +40% de dano das habilidades dos Blocos Mágicos'),
             ('Sabedoria', 'A mana volta 1,8x mais rápido e -35% de dano mágico/elemental recebido'),
             ('Carisma', '+3 de sorte e 20% de chance de uma habilidade não gastar mana')], head=('Atributo', 'Com 100 pontos')),
      '<div class="prints"><figure><img src="img/prints/atributos.jpg" alt="A tela de Atributos (tecla K)" loading="lazy"><figcaption>A tela de Atributos (tecla K)</figcaption></figure></div>']),
    ('magicblocks:eclipse_shard', 'Em um dia raro (<b>1 em 12</b>, ao meio-dia, a partir do 5º dia) ou chamado pelo <b>Ritual do Eclipse</b>, a lua cobre o sol: o céu escurece, o horizonte fica alaranjado e um <b>disco negro com coroa de fogo</b> toma o lugar do sol por <b>2 minutos</b>. Enquanto dura, <b>Sombras</b> surgem da fumaça em volta de cada jogador na Superfície (2 a 3 a cada 10s, até 8 perto de você).',
     [table([('Sombra', 'Espectro encapuzado de olhos laranja que flutua com uma cauda de fumaça. 12 corações, golpe de 5 que <b>cega por 2s</b>.'),
             ('Só morre perto de luz', 'Sem luz, os golpes <b>atravessam</b> a Sombra. Ela só toma dano com luz de bloco 7+ onde está, se alguém a até 6 blocos segura uma <b>tocha, lanterna ou a Lanterna de Mana</b> (na mão ou no cinto), ou com <b>fogo</b>.'),
             ('Fragmento do Eclipse', 'As Sombras soltam (40%, mais com Pilhagem). Faz a <b>Torre de Cristal</b>.'),
             ('Fim', 'Quando o eclipse acaba, as Sombras se desfazem na luz do sol.')], head=('', 'Como é')),
      '<div class="prints"><figure><img src="img/prints/eclipse_sol.jpg" alt="O sol coberto" loading="lazy"><figcaption>O sol coberto</figcaption></figure><figure><img src="img/prints/eclipse_sombras.jpg" alt="Sombras no eclipse" loading="lazy"><figcaption>Sombras no eclipse</figcaption></figure></div>']),
]

ARMAS.extend([
    ('magicblocks:leviathan_chestplate', 'Feita com as <b>Escamas de Leviatã</b>. Tem um <b>modelo 3D próprio</b>: o capacete é a cabeça do Leviatã (o seu rosto aparece pela boca), o peitoral tem o anel e asas de verdade saindo das costas, as ombreiras têm espinhos e as botas, garras. Cada peça tem <b>2 de armadura a mais que a de netherita</b> e 4 de resistência. <b>Pintura</b>: na Mesa de Ferraria, sem molde, a peça (de Leviatã ou da Besta Celestial) com um <b>corante</b> pinta as escamas cinzas e com um <b>minério</b> (ou gema/barra: diamante, esmeralda, redstone, lápis, ouro, cobre, ametista, quartzo...) pinta as partes roxas; na Celestial elas são uma <b>galáxia animada</b> na cor do minério.',
     ['<div class="pieces">%s</div>' % ''.join(slot('magicblocks:leviathan_' + p) for p in ['helmet', 'chestplate', 'leggings', 'boots']),
      crafting('leviathan_chestplate'),
      table([('Cada peça', 'Corta <b>15% do dano</b> recebido (as 4 juntas deixam só 40%: protege <b>2,5x mais</b>)'),
             ('4 peças', '<b>Nenhum dano do void</b>: nem o void normal nem o ar da dimensão do Vazio machucam'), ('Nadar', 'Cada peça nada <b>35% mais rápido</b> (as 4: 2,4x)')], head=('Vestindo', 'Efeito')),
      '<h4>Armadura Elemental de Leviatã</h4><p>No <b>Nature Infuser</b>, uma peça da <a href="#elemental-chestplate">Armadura Elemental</a> na entrada e uma <b>Escama de Leviatã</b> na alimentação. A peça mantém o <b>elemento e os encantamentos</b>, ganha +2 de armadura, +1,5 de resistência e conta como peça de Leviatã (os 15% por peça e a proteção do void com as 4).</p>',
      infuser('magicblocks:elemental_chestplate', 'magicblocks:leviathan_scale', 'magicblocks:elemental_chestplate')]),
    ('magicblocks:abyssal_chestplate', 'Armadura do Vazio feita na bancada com <b>Cristal Abissal</b> e <b>Fragmento do Vazio</b>. Tem os mesmos números da <b>netherita</b> (não queima na lava). Cada peça tira <b>25%</b> do dano do void e do ar do Vazio (dá para misturar com outras peças que resistem ao void); com <b>4 peças</b>, nenhum dano.',
     ['<div class="pieces">%s</div>' % ''.join(slot('magicblocks:abyssal_' + p) for p in ['helmet', 'chestplate', 'leggings', 'boots']),
      crafting('abyssal_helmet'), crafting('abyssal_chestplate'), crafting('abyssal_leggings'), crafting('abyssal_boots')]),
    ('magicblocks:beast_sword', 'Uma adaga de garra do Leviatã com <b>50 de dano</b>, feita com 2 Garras sobre 1 Escama. Na <b>segunda mão</b>, o botão direito bate exatamente como na principal (dano, encantamentos, crítico), e cada mão tem a <b>própria recarga</b>: dá para alternar direita e esquerda.',
     [crafting('beast_sword'),
      '<h4>Defesa</h4><p>Com duas armas "duas mãos" (uma em cada mão), <b>segure o botão direito</b> (sem shift; um clique rápido continua sendo o golpe da segunda mão): elas se cruzam e bloqueiam como escudo o que vem de frente. As adagas da besta só defendem durante a Fúria.</p><h4>Fúria da Besta</h4><p>Com uma adaga em cada mão (comum, Celestial ou Lâmina do Caos), segure <b>Shift + botão direito</b> por 3 segundos e solte. Enquanto carrega, as adagas se cruzam e um círculo de aura vermelha cresce nos pés.</p>',
      table([('Bônus', '+25% de dano, Regeneração I e +35% de velocidade'),
             ('Custo', '4 de mana ao ativar e mais 4 a cada 20s (renova sozinha enquanto houver mana e as duas adagas)'),
             ('Escudos', 'As adagas desativam escudos como um machado'),
             ('Dash (R)', 'No lugar da rolagem: um dash vermelho que corta quem estiver no caminho (12 de dano e fogo)')], head=('', 'Fúria da Besta'))]),
    ('magicblocks:manilium_beast_sword', 'A Espada da Besta com Manilium: <b>60 de dano</b> e lâmina roxa-escura com galáxia. Feita no <b>Nature Infuser</b> (mantém encantamentos e nome). Durante a Fúria da Besta a galáxia fica vermelha.',
     [infuser('magicblocks:beast_sword', 'magicblocks:manilium_ingot', 'magicblocks:manilium_beast_sword')]),
    ('magicblocks:chaos_blade', 'A lâmina negra-carmesim com galáxia: <b>65 de dano</b> e sobe com Estrelas igual à Espada de Manilium. Feita no <b>Altar de Rituais</b>: a Espada da Besta (comum ou Celestial) no altar e <b>4 Barras de Manilium + 4 Cristais Instáveis</b> nos pedestais. Como são 8 itens, o altar aceita também 4 pedestais nas <b>diagonais</b>, a 2 blocos dele.',
     ['<p class="tip">Funciona com a Fúria da Besta como as outras adagas.</p>',
      '<p class="tip"><b>Skin acorrentada</b>: no Nature Infuser, a Lâmina do Caos com uma <b>Corrente</b> vira a Lâmina do Caos Acorrentada (veios vermelhos incandescentes que viram galáxia vermelha na Fúria).</p>']),
    ('magicblocks:solar_chestplate', 'A armadura que a <b>Guardiã do Sol</b> veste, no estilo das estátuas antigas: elmo espartano com a abertura em T (o seu rosto aparece) e uma <b>crista de chifres em V</b>, asinhas brancas dos lados, ombreiras grandes em camadas com espinhos, peitoral em divisas com o <b>sol</b> no meio, saiote de placas e grevas pontudas. As placas são de aço escuro, com <b>detalhes brancos</b> e <b>pontas douradas</b>. Feita na <b>Mesa de Ferraria</b>: o <b>Molde de Melhoria do Sol</b>, uma peça da <a href="#abyssal-chestplate">Armadura Abissal</a> e uma <b>Barra de Metal Solar</b> (mantém os encantamentos).',
     ['<div class="pieces">%s</div>' % ''.join(slot('magicblocks:solar_' + p) for p in ['helmet', 'chestplate', 'leggings', 'boots']),
      crafting('solar_upgrade_smithing_template'),
      smithing3('magicblocks:solar_upgrade_smithing_template', 'magicblocks:abyssal_chestplate', 'magicblocks:sunsteel_ingot', 'magicblocks:solar_chestplate'),
      table([('Cada peça', 'A proteção da Armadura da Besta <b>+2</b> e corta <b>19% do dano</b>; quem bate em você <b>pega fogo</b>'),
             ('4 peças', '<b>Imune a fogo</b>, ao <b>void</b> e ao ar do Vazio; a esquiva (R) vira o <b>dash amarelo</b> da Guardiã, que corta quem estiver no caminho')], head=('Vestindo', 'Efeito')),
      '<p class="tip"><b>Pintura</b> (Mesa de Ferraria, sem molde): um <b>corante</b> tinge as placas de aço e um <b>minério</b> (ou gema/barra: diamante, esmeralda, redstone, lápis, ametista...) pinta as <b>pontas douradas</b>. A Barra de Metal Solar volta para o dourado.</p>']),
    ('magicblocks:solar_dagger', 'Adaga de <b>Metal Solar</b> com <b>60 de dano</b> que <b>bota fogo</b> em quem acerta. Como as adagas da Besta, é <b>duas mãos</b> (na segunda mão o botão direito golpeia) e, com uma em cada mão, <b>Shift + segurar o direito</b> por 3s entra na <b>Fúria</b>, só que <b>amarela</b>: aura, onda e dash amarelos.',
     [crafting('solar_dagger'),
      '<p class="tip">As partes douradas das adagas, da lança, do escudo e das espadas também pintam com minério na Mesa de Ferraria.</p>']),
    ('magicblocks:solar_spear', 'Lança de <b>Metal Solar</b>: <b>65 de dano</b>, alcance <b>1,5 bloco maior</b> e bota fogo. <b>Segure o botão direito</b> para carregar o <b>arremesso de luz</b> (o mesmo da Guardiã): um círculo amarelo mostra onde vai cair (cresce com a carga, até 48 blocos) e, ao soltar, a lança de luz explode em área com fogo (até 38 de dano; 3 de mana).',
     [crafting('solar_spear')]),
    ('magicblocks:solar_shield', 'Escudo redondo com o sol no meio. Defende como um escudo comum e, <b>enquanto defende</b>, <b>projéteis</b> (flechas, bolas de fogo...) e <b>magias</b> que vêm de frente <b>voltam para quem atirou</b>. <b>Defendendo, aperte o botão esquerdo para aparar</b>: no próximo <b>1 segundo</b> um golpe corpo a corpo volta inteiro no atacante (e bota fogo). Aparar gasta <b>1 de mana</b> e desativa o escudo por <b>3 segundos</b>.',
     [note('<b>Altar de Rituais</b>: um escudo comum no altar, <b>4 Barras de Metal Solar</b> nos pedestais normais e <b>4 Barras do Vazio</b> nas diagonais. Veja a aba <a href="rituais.html#solar-shield">Rituais</a>.')]),
    ('magicblocks:solar_sword', 'Espada de <b>Metal Solar</b> com <b>70 de dano</b> que bota fogo. Como a Espada de Manilium, guarda um <b>Bloco Mágico</b> (no Nature Infuser) e usa as habilidades dele.',
     [crafting('solar_sword'), infuser('magicblocks:solar_sword', 'magicblocks:fire_block', 'magicblocks:solar_sword')]),
    ('magicblocks:radiant_sword', 'A Espada de Metal Solar abençoada pelas mariposas: igual a ela (70 de dano, fogo, guarda um Bloco Mágico), mas cada golpe tem <b>20% de chance</b> de invocar uma <b>Mariposa Radiante</b> que voa até o alvo e morde (<b>2 corações</b> por mordida). No máximo <b>10 mariposas</b> por jogador; cada uma dura 30 segundos.',
     [note('<b>Altar de Rituais</b>: a Espada de Metal Solar no altar, <b>2 Almas Radiantes</b> e <b>2 Asas de Mariposa</b> nos pedestais. Mantém o bloco guardado, a pintura e os encantamentos.')]),
    ('magicblocks:molten_manilium_bucket', 'Com o <b>Tinkers\' Construct</b> instalado, o Manilium vira material de ferramentas, armaduras e escudo. Ele derrete na fornalha virando <b>Manilium Derretido</b>, um líquido com uma <b>galáxia animada</b>. Derrete a <b>950°</b>, então a fornalha com lava comum já funciona. Escamas (45 mb) e Garras (90 mb) de Leviatã também derretem no mesmo líquido, e o novo material <b>Leviatã</b> deixa as espadas do Tinkers "duas mãos" e com a Fúria da Besta. O líquido machuca como o void (sem fogo) e não queima itens. Com o <b>Silent Gear</b> instalado, Manilium e Barra do Vazio viram materiais com encantabilidade alta.',
     [table([('Ferramentas (Tinkers)', 'Nível netherita, Enderference e Experienced'),
             ('Armaduras (Tinkers)', 'Proteção Mágica'),
             ('Manilium (Silent Gear)', 'Stellar, Renew e Magnetic'),
             ('Barra do Vazio (Silent Gear)', 'Void Ward, Hard e Adamant'), ('Escama de Leviatã (Silent Gear)', 'Besta (espadas, adagas, facas e katanas ficam duas mãos e entram na Fúria) e Light'), ('Cristal Abissal (Silent Gear)', 'Rasgo do Vazio (Wither)'), ('Cristal Instável (Silent Gear)', 'Surto de Mana (chance de devolver mana a cada golpe)')], head=('Material', 'Traços')),
      '<p class="tip">Os itens do próprio Magic &amp; Blocks continuam iguais e encantáveis. Sem esses mods instalados nada disso aparece.</p>']),
])

VAZIO = [
    ('magicblocks:gray_grass', 'Uma dimensão de <b>ilhas flutuantes</b> cinzentas embaixo do mundo. Só se entra pelo <b>void do Overworld</b>: quem cair e passar da <b>camada -100</b> vai para lá (antes do dano do void normal, ninguém morre no caminho) (o void do Nether, do End e do próprio Vazio não leva). Ao chegar aparece o <b>Pedestal do Retorno</b>, inquebrável, com um portal que leva ao seu ponto de spawn. O céu é escuro e cheio de buracos negros, e lá é bem mais fácil achar Orbes de Mana.',
     [table([('Planícies do Vazio', 'Ilhas enormes e inteiras'), ('Abismos do Vazio', 'As mesmas planícies cortadas por ravinas até o fundo'),
             ('Ilhas do Vazio', 'Várias ilhas separadas'), ('Planícies de Luz', 'Douradas e iluminadas: árvores e arbustos dourados, Gira-Sóis, mariposas brilhantes, o raro Minério de Metal do Sol e o Templo Solar'), ('Pântano Abissal', 'Floresta de mangues com raízes sobre lama funda, lagos roxos com algas e vitórias-régias, manchas de sculk, carpete de musgo, ametistas, luzes perolizadas e líquen brilhante; Lesmas Estelares e, raramente, o Colosso Fraturado')], head=('Bioma', 'Como é')),
      '<p class="tip">No céu de todos os biomas do Vazio podem aparecer <b>Ruínas Flutuantes</b>: ilhotas de pedra com pilares quebrados, ligadas por correntes, com um baú de tesouros na do meio.</p>',
      '<h4>O ar do Vazio</h4>',
      table([('Sem proteção', '<b>25% da sua vida</b> a cada 20 segundos (ignora armadura)'),
             ('Cada peça que resiste ao void (Besta, Besta Celestial, Abissal, Metal Solar ou Elemental de Void; dá para misturar)', 'Tira <b>25%</b> desse dano e do dano do void normal'),
             ('4 peças (o Bloco de Void na mão vale 2)', 'Nenhum dano'),
             ('Camadas -20 a -50 (Abismo Verdadeiro)', 'Dano pesado, Fraqueza e Escuridão; nada protege. Só a Âncora Abissal te puxa de volta'),
             ('Abaixo da camada -50', 'O buraco negro vermelho gigante te engole: morte, como no void normal')], head=('Situação', 'Dano'))]),
    ('magicblocks:void_mana_ore', 'Os minérios das ilhas do Vazio.',
     [table([('Minério de Mana do Vazio', 'O mais comum', '1 a 2 Orbes de Mana (Fortuna aumenta)'),
             ('Minério de Vazio', 'Picareta de ferro', '1 Pepita do Vazio (com Fortuna, no máximo 2)'),
             ('Minério de Cristal Abissal', 'Picareta de diamante', 'Cristal Abissal'),
             ('Minério de Vazio Profundo', 'Raro e sempre sozinho, picareta de diamante', '1 Pepita do Vazio (com Fortuna, no máximo 2)')], head=('Minério', 'Como', 'Solta'))]),
    ('magicblocks:void_shard', 'Sai de <b>9 Pepitas do Vazio</b> (que caem dos Minérios de Vazio) e aparece no baú da Forja. 4 fragmentos viram 1 Essência do Void. Na <b>Fornalha Natural</b>, depois de <b>120 segundos</b>, vira uma <b>Barra do Vazio</b> (a fornalha comum não aceita; coloque com o mouse ou por funil).',
     [crafting('void_shard_from_nuggets'), crafting('void_essence_from_shards')]),
    ('magicblocks:void_bar', 'Feita na <b>Fornalha Natural</b> com um Fragmento do Vazio (120 segundos). Também cai do Leviatã. É material do Silent Gear.',
     [note('Fragmento do Vazio na Fornalha Natural (120s) ou drop do Leviatã.')]),
    ('magicblocks:void_star', 'No <b>Nature Infuser</b>: Estrela de Mana Despertada + Barra do Vazio. Depois da Despertada, cada Estrela do Vazio dá <b>+1</b> na armadura de Manilium (até <b>+15</b>) ou na espada (até <b>+150</b>). Jogada no buraco da <a href="#void-leviathan-spawn-egg">Toca do Abismo</a>, chama o Leviatã.',
     [infuser('magicblocks:awakened_mana_star', 'magicblocks:void_bar', 'magicblocks:void_star')]),
    ('magicblocks:abyss_rock', 'A "madeira" do Vazio: formações de pedra tortas espalhadas pelas ilhas, com um <b>Núcleo do Abismo</b> escondido na base. Enquanto o núcleo existir, a formação devolve <b>1 bloco a cada 30 segundos</b>. Quebrando o núcleo (picareta de ferro) ela para de crescer, e o núcleo faz a <b>Lanterna do Abismo</b>: um lampião com um mini buraco negro girando dentro (luz 15).',
     [crafting('abyss_lantern')]),
    ('magicblocks:abyssal_anchor', 'Se você cair no <b>Abismo Verdadeiro</b> (camadas -20 a -50 do Vazio), ela te puxa de volta ao último chão firme e se quebra.',
     [crafting('abyssal_anchor')]),
    ('magicblocks:void_jellyfish_spawn_egg', 'As criaturas do Vazio. As do Overworld não nascem lá.',
     [table([('Água-viva do Vazio', 'Passiva: flutua em pulsos e brilha', 'Gel do Vazio (comida: Queda Lenta por 30s)'),
             ('Mariposa Cinzenta', 'Passiva: voa até o bloco iluminado mais perto e fica rodopiando', 'Pó de Mariposa (poção estranha + pó = Visão Noturna)'),
             ('Sombra Errante', 'Agressiva: some e reaparece nas suas costas', '—'),
             ('Devorador', 'Agressivo: boca flutuante que cospe mini buracos negros', '15% de chance de Orbe de Mana')], head=('Criatura', 'Comportamento', 'Solta'))]),
    ('magicblocks:forge_bench', '<b>A Forja</b> é uma estrutura rara do Vazio (no mínimo uns 2500 blocos uma da outra): muralha redonda de pedra negra com contrafortes de Pedra do Abismo, telhado cônico, a fornalha grande com chaminé, bigornas, altos-fornos e um baú com loot. No centro fica a <b>Bancada da Forja</b> (3x1), que ainda vai ser usada para forjar uma super espada.',
     ['<p class="tip">Para gerar uma onde você está (operador): <code>/magicblocks structure forge</code>.</p>']),
    ('magicblocks:void_leviathan_spawn_egg', 'A <b>Toca do Abismo</b> é uma arena redonda do Vazio com um buraco muito fundo no meio. Jogue uma <b>Estrela do Vazio</b> no buraco: o <b>Leviatã do Vazio</b>, um dragão-serpente no estilo Rayquaza, sai em espiral e um pedestal com o <b>Cristal do Vazio</b> sobe no meio. Todos os ataques mostram antes onde vão acertar.',
     [table([('Fase 1', 'Barra de 5 pontos. Golpes não fazem nada: faça o <b>laser</b> dele acertar o cristal (o cristal devolve uma onda que tira 1 ponto). Com 3 pontos ele se enfurece e ataca 35% mais rápido. O laser vem a cada 4 ataques.'),
             ('Transição', 'Ele destrói o cristal e empurra todo mundo para a beira.'),
             ('Fase 2', '1500 de vida. Ele fica enrolado no meio da arena e o buraco é tapado.')], head=('', 'Como funciona')),
      table([('Meteoros', '1 e 2', 'Círculos vermelhos no chão'), ('Buraco negro', '1', 'Puxa a arena inteira e arranca pedras da borda'),
             ('Metralhadora', '1', 'Mini buracos negros saindo da cabeça'), ('Laser', '1', 'Carrega 5s; acertar o cristal é o objetivo'),
             ('Mergulho', '1 e 2', 'Sobe em cima de você e desce com uma onda de choque'), ('Bote', '1 e 2', 'Avança rápido e morde'),
             ('Rugido', '1 e 2', 'Empurra todo mundo e deixa lento'), ('Investida', '2', 'Corre na faixa vermelha, seguindo você até pouco antes'),
             ('Laser varrendo', '2', 'Sobe devagar de baixo para cima'), ('Lasers do céu', '2', 'Caem nos círculos roxos'),
             ('Nova', '2', 'Anéis de tiros para todos os lados')], head=('Ataque', 'Fase', 'Como é')),
      '<p class="tip">O corpo inteiro pode ser acertado (50% do dano; a cabeça leva 100%). <b>Magias</b>, projéteis e explosões dão <b>50% a mais</b>, e nenhum golpe passa de <b>100 de dano</b>. Se a arena ficar vazia por 1 minuto ele volta para o buraco. Comandos de operador: <code>/magicblocks structure den</code> gera uma Toca e <code>/magicblocks leviathan</code> chama o Leviatã na Toca mais perto.</p>']),
    ('magicblocks:leviathan_scale', 'O Leviatã solta <b>12 a 28 Escamas</b>, <b>2 a 8 Garras</b>, o <b>Coração do Leviatã</b> (um bloquinho rosa que pulsa e brilha), Cristais Abissais, sucata de netherita, 1 Orbe de Mana, Essência do Void e Barras do Vazio. As escamas fazem a <a href="armas-e-armaduras.html#leviathan-chestplate">Armadura de Leviatã</a> e as garras, a <a href="armas-e-armaduras.html#beast-sword">Espada da Besta</a>.',
     ['<div class="pieces">%s</div>' % ''.join(slot(i) for i in ['magicblocks:leviathan_scale', 'magicblocks:leviathan_claw', 'magicblocks:leviathan_heart']),
      '<p class="tip">Uma <b>Garra</b> no Nature Infuser com a Espada de Manilium deixa a espada <b>"duas mãos"</b>: na segunda mão, o botão direito bate como na principal.</p>']),
    ('magicblocks:fractured_colossus_spawn_egg', 'O <b>Colosso Fraturado</b> é um mini-chefe raro das Planícies e do Pântano Abissal: um golem de pedra abissal rachado, com cristais roxos brilhando nas fendas. <b>Todo ataque é avisado antes</b>.',
     [table([('Pancada', 'Ergue os braços e um <b>círculo vermelho</b> aparece no chão onde vai cair (1,5s). Quem estiver dentro leva 15 de dano e voa'),
             ('Lança de Cristal', 'Uma <b>linha vermelha</b> mostra o caminho (1,25s) e um feixe de cristal corta a linha (11 de dano)'),
             ('Erupção de Cristais', '<b>5 círculos roxos</b> aparecem em volta de você (1,5s) e espinhos de cristal sobem de cada um (10 de dano)'), ('Investida', 'Uma <b>faixa vermelha</b> no chão mostra o caminho (1,25s) e ele corre por ela atropelando quem estiver na frente (14 de dano)'), ('Fratura', 'Com 2/3 e 1/3 da vida ele se parte e solta <b>2 Fragmentos</b> (pequenos, só dão a pancada)')], head=('Ataque', 'Como é')),
      '<p>Solta o <b>Núcleo Fraturado</b>, 2 a 5 Cristais Abissais e 1 a 3 Essências do Void (nunca Barra do Vazio nem Orbe de Mana). O núcleo faz o <b>Martelo Fraturado</b>: a cada 1,5s o golpe faz um tremor que joga os monstros em volta para cima.</p>',
      crafting('fractured_hammer')]),
    ('magicblocks:star_slug_spawn_egg', 'A <b>Lesma Estelar</b> é passiva e bem lenta, com estrelinhas piscando dentro do corpo. Por onde passa deixa um <b>Rastro Estelar</b> brilhante que some sozinho depois de uns 15 segundos. Vive nas Planícies de Luz e no Pântano Abissal e solta <b>Gosma Estelar</b> (1 gosma = 2 Bolsas de Tinta Brilhante).', []),
    ('magicblocks:sunturn', 'O <b>Gira-Sol</b> nasce nas Planícies de Luz: a flor vira a cabeça para o jogador mais perto e dá <b>Visão Noturna</b> a quem estiver a até 6 blocos. Brilha e pode ser replantado em grama, terra ou Grama Luminosa.', []),
    ('magicblocks:golden_door', 'A <b>Madeira Dourada</b> das árvores das Planícies de Luz (brilha de leve): tábuas, escadas, laje, cerca, portão, porta, alçapão, botão, placa de pressão, madeira e as versões descascadas (machado no tronco).', []),
    ('magicblocks:solar_empress_spawn_egg', 'O <b>Templo Solar</b> aparece (raro) nas <b>Planícies de Luz</b>: uma plataforma redonda de quartzo com raios de ouro e 8 colunas. Acima do meio flutua o <b>Núcleo Solar</b>, um buraco negro amarelo cujo centro é um bloco de pedra luminosa. Ponha <b>Asas de Mariposa</b> nos pedestais das pontas e uma <b>Alma Radiante</b> no do meio: o templo se desfaz e vira uma <b>arena de 9 ilhas</b> sobre o void, o buraco negro reage e nasce a <b>Guardiã do Sol</b>: uma guerreira toda de <b>Armadura de Metal Solar</b>, com asas de luz e um sol inteiro atrás das costas.',
     ['<p>Ela tem <b>3 fases de 1500 de vida</b>, numa <b>ordem sorteada</b>. Cada fase é uma arma; na troca ela joga a arma anterior fora e pega a nova. Todo ataque é <b>avisado em amarelo</b> no chão antes (círculos e faixas com borda escura).</p>',
      table([('Golpes', 'De perto, uma adaga de cada vez (faixa amarela na frente dela)'),
             ('Giro', 'Um disco amarelo em volta dela; depois gira com as adagas perseguindo você entre as ilhas'),
             ('Raios do céu', 'Levanta a mão direita: <b>círculos amarelos</b> em você e em volta; depois caem raios de luz'),
             ('Dash entre ilhas', 'Uma <b>faixa amarela</b> mostra o caminho e ela corta até a sua ilha (nunca cai no void)'),
             ('Fúria (metade da vida)', 'Vai para o centro, carrega e solta uma onda; fica com a <b>aura amarela</b>, mais rápida e mais forte')],
            head=('Adagas Solares', 'Como é')),
      table([('Voo', 'Voa em volta da arena sempre olhando para você. A cada <b>3 ataques</b> desce ao centro para <b>descansar</b> (leva 50% a mais de dano)'),
             ('Investida', 'Faixa amarela e um círculo onde vai cair: ela sobe e desce em cima de você'),
             ('Lança arremessada', 'Ergue a lança; um <b>círculo amarelo grande</b> segue você e trava; a lança cai e explode em área com fogo'),
             ('Raios do céu', 'A mesma chuva de raios, espalhada pela arena (3 ondas)')], head=('Lança', 'Como é')),
      table([('Escudo', 'Levanta o escudo na frente do corpo e uma <b>cúpula dourada de hexágonos</b> aparece em volta dela (com um som de sino): <b>não bata!</b> Quem bate leva de volta o mesmo dano; projéteis são bloqueados (magias passam)'),
             ('Corte de luz', 'Faixa amarela comprida no chão; um corte de luz corre por ela'),
             ('Raios do céu', 'A mesma chuva de raios (3 ondas)')], head=('Espada e Escudo', 'Como é')),
      '<p>Golpes <b>físicos</b> (espada, machado, flecha, tridente) tiram no máximo <b>10</b>; <b>magias</b> (cajados, Blocos Mágicos...) tiram o dano normal. Os golpes dela <b>botam fogo</b>.</p>',
      '<p>Ao morrer ela é <b>sugada para o buraco negro</b> do Núcleo Solar, gira, encolhe e <b>explode</b>, soltando o <b>Coração da Luz</b>, 10 a 20 barras e 2 a 4 blocos de <b>ouro</b> e 3 a 5 <b>Minérios de Metal do Sol</b>. Quando ela nasce os pedestais somem; depois da luta eles voltam na ilha do meio e dá para chamá-la de novo.</p>',
      '<div class="pieces">%s</div>' % ''.join(slot(i) for i in ['magicblocks:moth_wing', 'magicblocks:radiant_soul', 'magicblocks:moth_wing', 'magicblocks:light_heart']),
      '<p class="tip">Para gerar um templo onde você está (operador): <code>/magicblocks structure solar</code>.</p>']),
    ('magicblocks:radiant_soul', 'A <b>Alma Radiante</b> cai das <b>Mariposas</b> (cinzenta e brilhante) com <b>1% de chance</b> quando um jogador as mata. Vai no pedestal do meio do Templo Solar.', []),
    ('magicblocks:sunsteel_ore', 'O <b>Minério de Metal do Sol</b> só aparece nas <b>Planícies de Luz</b>, dentro da pedra do vazio, e é bem raro (picareta de diamante). A Guardiã do Sol também solta. Na <b>fornalha</b> (ou no alto-forno) vira a <b>Barra de Metal Solar</b>.', []),
]


MAGICOS.extend([
    ('magicblocks:sculk_block', 'O <b>Bloco de Sculk Roxo</b>: no <b>Nature Infuser</b>, o Bloco de Sculk na entrada e uma <b>Vitória-régia</b> na alimentação. Funciona igual, mas tudo fica <b>roxo</b>: o bloco (que agora usa <b>óculos escuros</b>), o <b>Estrondo Sônico</b> e o <b>Warden aliado</b> (pele e luzes roxas, e o estrondo dele também).',
     [infuser('magicblocks:sculk_block', 'minecraft:lily_pad', 'magicblocks:sculk_block')]),
])

# ---- entradas 1.0.105 ----
ARMAS.extend([
    ('magicblocks:gem_bench', 'Joias encaixáveis: armas, cajados e a Espada de Manilium têm <b>2 encaixes</b>, cada peça de armadura <b>1</b> e a Manopla Solar <b>5</b>. Na <b>Bancada de Joias</b>, coloque o item no slot da esquerda e as joias nos encaixes da direita (tirar a joia devolve ela). As joias são feitas no <b>Nature Infuser</b>: um <b>Diamante</b> na entrada e o catalisador na alimentação.',
     [crafting('gem_bench'),
      table([('Rubi', 'Pó de Blaze', '+1 a 8% de dano e o alvo pega fogo'),
             ('Safira', 'Gelo Compactado', 'O alvo fica lento por 0,5 a 3s'),
             ('Topázio', 'Barra de Cobre', '4 a 15% de chance de um choque (+5 de dano)'),
             ('Ônix', 'Barra do Vazio', '-1 a 8% de dano recebido (até 40% somando tudo)'),
             ('Jade', 'Maçã Dourada', '+1 a 8 de vida máxima'),
             ('Ametista', 'Orbe de Mana', '+1 a 4 de mana máxima'),
             ('Pedra Solar', 'Barra de Metal Solar', '+2 a 10% de velocidade'),
             ('Opala', 'Membrana de Phantom', '-4 a 16% de recarga da esquiva')], head=('Joia', 'Catalisador', 'Efeito')),
      note('Cada joia <b>sorteia o valor</b> quando é pega (em passos de 0,5; quanto maior, mais rara). Na <b>bigorna</b>, duas joias iguais com o <b>mesmo valor</b> viram uma com <b>+0,5</b>.')]),
    ('magicblocks:solar_gauntlet', 'A <b>Manopla Solar</b>, de Metal Solar com o Coração da Luz, tem <b>5 encaixes</b> e aparece <b>vestida na mão</b> do jogador, com as joias nos nós dos dedos e a grande nas costas da mão, em primeira e terceira pessoa. Vai no slot de <b>mãos</b> do Curios, ou é só <b>segurar</b> (em qualquer mão) que ela se veste no braço. Os efeitos das joias dela <b>valem o tempo todo</b>; <b>sem o Curios instalado</b>, valem só de ela estar no <b>inventário</b>. Com <b>5 joias diferentes</b> vira o <b>Poder Infinito</b>: tudo vale 1,5x e as joias pulsam. Segurada, o soco com ela dá <b>4 de dano</b>; vestida no Curios (ou na segunda mão), o soco de mão vazia bate +6.',
     [crafting('solar_gauntlet')]),
    ('magicblocks:solar_wings', 'As <b>Asas Solares</b> são as asas de luz da Guardiã do Sol. Vão no slot do peito e <b>planam igual à elytra</b>, sem gastar durabilidade e <b>sem precisar de foguetes</b>: voando, aperte <b>R</b> para ganhar embalo (<b>1 de mana</b>). Só aparecem no jogador quando ele começa a voar: abrem, batem devagar (a onda corre da base até a ponta) e dobram um pouco a cada batida.',
     [note('<b>Altar de Rituais</b>: uma <b>Elytra</b> no altar, <b>2 Asas de Mariposa</b>, <b>2 Asas Brilhantes</b> e <b>2 Barras de Metal Solar</b> nos pedestais (use também os das diagonais). A Asa de Mariposa cai das Mariposas e a Asa Brilhante das Mariposas Brilhantes (3% cada).')]),
])

RECURSOS.extend([
    ('magicblocks:soul_pearl', 'Com o mod <b>Corpse</b>: use a <b>Pérola da Alma</b> para puxar o seu <b>corpo</b> (com tudo o que estava com você) do lugar da última morte até você, mesmo de outra dimensão ou do <b>fundo do Vazio</b>. Ela só é gasta se achar o corpo.',
     [crafting('soul_pearl')]),
])

CRIATURAS.extend([
    ('magicblocks:mimic_spawn_egg', 'O <b>Mímico</b> anda pela Superfície <b>disfarçado de qualquer criatura do mod</b> (pacífica ou não), passeando devagar como ela. Se você chegar a <b>4 blocos</b> ou ficar <b>olhando para ele</b>, o disfarce treme, incha e estoura num <b>monstro de espelho de 2,5 blocos</b>: corpo de vidro escuro, um espelho rachado no peito que se abre como uma <b>boca vertical cheia de dentes</b>, seis olhos acesos e braços com <b>lâminas de vidro</b>. Se apanhar disfarçado, se revela na hora (e o primeiro golpe pega pela metade).',
     [table([('Retalho', 'Um <b>disco prateado</b> na frente dele: cruza as lâminas no alto e corta em X'),
             ('Salto', 'Um disco prateado em você: agacha, pula e cai espalhando cacos'),
             ('Reflexo', 'Uma <b>faixa prateada</b> até você: desliza como um reflexo, corta e <b>cega</b>')], head=('Ataque', 'Como é')),
      '<p class="tip">80 de vida. Solta 1 a 3 <b>Fragmentos de Espelho das Almas</b>.</p>']),
])

VAZIO.extend([
    ('magicblocks:ember_heart', 'A <b>Forja Primordial</b> é uma dimensão de planícies. Para abrir: vá até <b>A Forja</b> do Vazio e jogue um <b>Coração da Luz</b> na fornalha de lava (o 3x3 de lava): a lava vira o <b>Portal da Forja</b>. Do outro lado você chega no chão, ao lado do portal de volta (ele te leva de volta para perto da fornalha). É uma <b>grande planície de Grama Vermelha</b>, sempre de dia, com o <b>céu azul</b> como o do Overworld (com nuvens), menos o sol: no lugar dele está um <b>sol gigante em colapso</b> (coroa, ondas de choque e rachaduras escuras).',
     [table([('Planícies Vermelhas', 'Grama Vermelha e raízes carmesim, com árvores de Madeira Densa espalhadas'),
             ('Bosque Denso', 'Muitas árvores de Madeira Densa juntas')], head=('Bioma', 'Como é')),
      '<p>Por baixo da grama fica a <b>Pedra da Forja</b>, dura como <b>obsidiana</b> (só sai com picareta de diamante). Ela é <b>rica em minérios</b> (veios de <b>qualquer minério</b>, de todos os mods instalados, e o <b>Minério de Coração de Brasa</b>), mas ainda tem bem mais pedra do que minério. O <b>Coração de Brasa</b> é brasa viva: queima <b>40 itens</b> numa fornalha.</p>']),
    ('magicblocks:dwarf_spawn_egg', 'Na Forja vivem os <b>Anões</b>: baixinhos, barbudos, de capacete de ferro e com um <b>machado de pedra</b>. São <b>neutros</b>, como os piglins zumbis: só brigam com quem bate neles, e aí os anões em volta entram junto. Os golpes são <b>marcados no chão</b> antes, como os dos chefes.',
     [table([('Machadada', 'Disco na frente dele: ergue o machado e desce'),
             ('Salto', 'Disco em você: agacha, pula e cai com o machado, jogando para cima')], head=('Ataque', 'Como funciona')),
      '<p class="tip">Os anões soltam <b>ferro</b> e <b>pão</b> (e às vezes o machado).</p>']),
    ('magicblocks:dense_log', 'As árvores da Forja são de <b>Madeira Densa</b>, uma madeira escura nova. O tronco é pesado: demora <b>o dobro</b> de um tronco normal para quebrar, mas cada um vira <b>8 tábuas</b>. Tem todas as variantes: tábuas, escadas, laje, cerca, portão, porta, alçapão, botão, placa de pressão, madeira e as versões descascadas pelo machado.',
     []),
    ('magicblocks:forgestone_bricks', 'A <b>Pedra da Forja</b> e o <b>Voidstone</b> (do Vazio) viram <b>tijolos</b>: 4 pedras em quadrado dão 4 tijolos. Com os tijolos dá para fazer <b>escadas</b>, <b>lajes</b> e <b>muros</b> (na bancada ou no cortador de pedra). Os de Pedra da Forja também são duros como obsidiana.',
     []),
    ('minecraft:glass', '<b>Armadura transparente</b>: qualquer peça de armadura + <b>Vidro</b> no <b>Nature Infuser</b> fica invisível no corpo (continua protegendo normalmente) e ganha <b>Transparente</b> no nome. Para voltar ao normal, coloque a peça com outro Vidro.',
     []),
])

# ---- entradas 1.0.149 - 1.0.155 ----
VAZIO.extend([
    ('magicblocks:mithril_ore', 'O <b>Mithril</b> é raro como o diamante e só aparece na <b>dimensão da Forja</b>, dentro da Pedra da Forja (abaixo da altura 48). Precisa de picareta de diamante. O minério solta <b>Mithril Bruto</b>, que na fornalha vira uma <b>Pepita de Mithril</b>; <b>9 pepitas</b> fazem uma <b>Barra de Mithril</b>. A Forja agora também tem <b>cavernas e cânions</b> como os do Overworld.',
     [crafting('mithril_ingot')]),
    ('magicblocks:forge_furnace', 'A <b>Fornalha de Forja</b> cozinha <b>1,5x mais rápido</b> que a Fornalha Natural e só queima <b>Coração de Brasa</b> (cada um vale <b>10 itens</b>). Cozinha tudo o que a fornalha comum cozinha e é a única que transforma a <b>Pedra da Forja</b> em <b>Pedra da Forja Refinada</b>.',
     [crafting('forge_furnace')]),
    ('magicblocks:refined_forgestone_bricks', 'A <b>Pedra da Forja Refinada</b> (Pedra da Forja cozida na Fornalha de Forja) e os <b>Tijolos de Pedra Refinada</b>, com texturas próprias. Os dois têm <b>escadas</b>, <b>lajes</b> e <b>muros</b>, e os tijolos têm a versão <b>cinzelada</b> com uma runa de brasa.',
     [crafting('refined_forgestone_bricks'), crafting('chiseled_refined_forgestone_bricks')]),
    ('magicblocks:forge_pedestal', 'O <b>Pedestal da Forja</b> funciona como os outros pedestais (inclusive na formação de 8) e é o único aceito nos <b>rituais de nível 2</b>: <b>12 Pedestais da Forja</b> em volta do altar, cada item no seu lugar (vale também a formação girada 90°).',
     [crafting('forge_pedestal'),
      '<pre class="ritual">S _ _ M _ _ S\n_ X _ _ _ X _\nM _ _ A _ _ M\n_ X _ _ _ X _\nS _ _ M _ _ S</pre>',
      note('<b>Fornalha de Herfestus</b>: a <b>Fornalha de Forja</b> no altar, <b>Barras de Metal Solar</b> nos cantos (S), <b>Barras de Mithril</b> no meio dos lados (M) e <b>Tijolos de Pedra da Forja</b> por dentro (X). Usa 20.000 de energia de natureza.')]),
    ('magicblocks:herfestus_furnace', 'A <b>Fornalha de Herfestus</b> tem <b>duas entradas</b> que cozinham ao mesmo tempo, <b>2x mais rápido</b> que a Fornalha Natural. Queima <b>Coração de Brasa</b> (10 itens) ou <b>energia de natureza</b> pelos cabos (7.200 por item, 6x o gasto da Fornalha Natural). Com <b>Minério de Ignus</b> numa entrada e <b>Barra de Mithril</b> na outra, faz a <b>Barra de Ignus</b>.',
     []),
    ('magicblocks:ignus_ingot', 'O <b>Herfestus</b> solta <b>2 a 4 Minérios de Ignus</b>. Na Fornalha de Herfestus, junto com uma Barra de Mithril, vira a <b>Barra de Ignus</b>, o metal de fogo dele.',
     []),
])

RECURSOS.extend([
    ('magicblocks:mana_thread', 'A <b>Linha de Mana</b> é uma linha azul, como a da aranha, infundida com mana (sai 2 por vez). Faz a <b>Bolsa de Orbes de Mana</b>, a Bolsa Melhorada do ferreiro goblin e o <b>Arco de Mana</b>.',
     [infuser('minecraft:string', 'magicblocks:mana_essence', 'magicblocks:mana_thread')]),
    ('magicblocks:limit_breaker', 'O <b>Quebra-Limites</b> só existe no <b>criativo</b>. No inventário ou no slot de amuleto do Curios, seus golpes <b>ignoram o limite de dano por golpe dos chefes</b> (Kraken, Ronin, Pantan0, Lobisomem Alfa, Guardiã do Sol e Leviatã).',
     []),
    ('magicblocks:shade_crystal', 'O <b>Cristal do Vazio</b> cai das Sombras Errantes e agora também de <b>qualquer mob morto na dimensão do Vazio</b> (10% de chance, mais com Saque).',
     []),
])

ARMAS.extend([
    ('magicblocks:mana_bow', 'O <b>Arco de Mana</b> (Cristais Instáveis e Linha de Mana) atira normal quando há flechas. <b>Sem flechas</b>, gasta <b>1 de mana</b> por tiro e atira uma <b>Flecha de Mana</b> azul (<b>1,5x o dano</b> de uma flecha comum). A animação de puxar mostra a flecha comum ou a de mana.',
     [crafting('mana_bow')]),
    ('magicblocks:ronin_katana', 'Hierarquia das armas e armaduras (do mais fraco ao mais forte): Instáveis, Lobo e Coroa Goblin; Ork, Adaga dos Viajantes, Mago e Elemental; Abissal e Martelo Fraturado; Manilium; Leviatã; Metal Solar e Besta Celestial; Lâmina do Caos; Katana do Ronin (100), Adagas do Pantan0 (80) e Martelo de Herfestus (90). Os tiers de cima ficam todos acima da netherita e cortam um pouco mais do dano (9% Abissal, 14% Manilium, 19% Leviatã e 26% com o conjunto de Metal Solar ou Besta Celestial), e os chefes causam <b>25% a mais</b> de dano.',
     []),
])

CRIATURAS.extend([
    ('magicblocks:eclipse_wyrm_spawn_egg', 'O <b>Wyrm do Eclipse</b> agora é um <b>monstro raro</b> do Vazio, não um chefe: aparece do nada voando (sem ninho), com uns <b>3 blocos de largura</b>. No ar dá <b>Rasantes</b> e <b>Chuva de Estrelas</b>; a cada 3 a 5 ataques <b>pousa</b> e dá 1 ou 2 <b>Investidas</b> ou <b>Cuspes de Laser</b>, e volta a voar. Todo golpe é marcado no chão.',
     []),
    ('magicblocks:primate_necklace', 'A <b>transformação em gorila</b> (Colar de Primata vestido; Shift + direito de mão vazia por 2s): o 3º soco seguido vira uma <b>Pancada</b> em área, o <b>R</b> dá uma cambalhota, e a árvore tem <b>Berro</b>, <b>Soco no Chão</b>, <b>Pedregulho Rolante</b> (um bloco gigante que sai rolando reto e atropela tudo no caminho) e <b>Investida</b>.',
     []),
])



# ---- entradas 1.0.156 - 1.0.157 ----
MAGICOS.extend([
    ('magicblocks:redstone_block', 'Os <b>Blocos de Redstone</b> (normal e Instável) podem ser <b>pintados</b> com qualquer tinta na bancada: o bloco na mão e no cajado e <b>todos os ataques</b> (faíscas, Corrente Carmesim, Kamehameha, Explosão Carmesim, o laser do céu e até a cor do céu) ficam na cor da tinta; tinta vermelha volta ao normal. No cajado, o <b>laser do céu do Redstone Instável</b> mira até <b>75 blocos</b>, desce como uma coluna gigante e cava do teto do mundo <b>até o fundo da bedrock</b>.',
     []),
])

ARMAS.extend([
    ('magicblocks:werewolf_glove', 'A <b>Árvore das Manoplas</b> (Mesa de Maestria com a Luva de Lobisomem ou a Manopla Solar): <b>Punho de Ferro</b> (+10%), <b>Soco Carregado</b> (avança e soca 2x a 4x) → <b>Mãos Pesadas</b> (atordoa e enfraquece), <b>Onda de Choque</b> (soco no chão, 5 blocos) → <b>Abalo</b> (8 blocos e lentidão), <b>Fúria do Lutador</b> (transformação: +30% de dano, velocidade e roubo de vida, gasta mana) → <b>Berserker</b>, e o <b>Campeão</b>. A Luva de Lobisomem não tem mais garras.',
     []),
    ('magicblocks:mana_bow', 'Novas habilidades da <b>Árvore do Arco</b> (no botão de bater, sem puxar): <b>Marca do Caçador</b> (o alvo aparece pelas paredes e leva +20% de dano), <b>Chuva de Flechas</b> (18 a 30 flechas caem numa área) e <b>Tiro Triplo</b> (a próxima flecha sai em leque). A <b>Flecha Perfurante</b> e o <b>Tiro Preciso</b> gastam 1 de mana. Mirando mais de 6s, a mira começa a balançar.',
     []),
    ('magicblocks:goblin_greatsword', 'Árvore da Espada: o <b>Aparar</b> agora se compra no meio da árvore; o Ronin ensina <b>Imbuir Mana</b> ou o <b>Corte Limpo</b> (uma barra com vermelho, amarelo e verde: solte no verde para um corte em área de 2x o dano). Entregando os <b>Ossos de Ork</b>, o <b>Rei Goblin</b> fica fortalecido para sempre (maior, 480 de vida, <b>Terremoto de Osso</b> com anéis para pular e <b>Chuva de Lâminas</b>); vencendo ele assim, ele ensina o <b>Arremesso da Espada</b> (a espada vai e volta cortando).',
     []),
    ('magicblocks:void_rifle', 'O <b>Rifle do Vazio</b> agora é como num jogo de tiro: <b>segure o direito para mirar</b> (zoom, a arma vai para o meio da tela e o tiro sai certeiro: 12 de dano, 48 blocos) e <b>atire com o esquerdo</b> (sem mirar: 9 de dano e o tiro abre). Cada tiro dá um coice na arma, e os <b>cristais podem ser pintados</b> com corante.',
     []),
])

CRIATURAS.extend([
    ('magicblocks:jonkey_spawn_egg', 'Gorila (Colar de Primata): a árvore agora abre só <b>clicando com o colar numa Mesa de Maestria</b>, tem ícones próprios e duas habilidades novas: <b>Rugido de Guerra</b> (Força II, Resistência e Velocidade por 1 minuto para você e os aliados) e <b>Agarrão</b> (agarra e arremessa). O <b>Berro</b> chega a 26 blocos, a carga tem uma <b>barra verde</b>, o colar aparece no peito e o item seguro aparece na mão do gorila.',
     []),
])

RECURSOS.extend([
    ('magicblocks:nature_harvester', 'O <b>Coletor de Colheita</b> guarda a colheita nos seus <b>5 slots</b> (direito no bloco abre; funis e baús encostados puxam). O <b>Tablet de Mana</b> abre a rede em <b>outra dimensão</b> se houver um <b>sinalizador aceso</b> a até 30 blocos. O <b>goblin xamã</b> sempre vende a <b>Orbe de Mana Condensada Instável</b>, que guarda mais mana a cada nível dele (10, 15, 20, 30); o resto das ofertas é sorteado, e cada Orbe de armazenamento acima da 1ª custa a anterior + 64 moedas.',
     []),
])


# ---- entradas 1.0.158 - 1.0.159 ----
ARMAS.extend([
    ('magicblocks:leather_gauntlet', 'A <b>Manopla de Couro</b> (couro em volta, lã em cima e linha no meio) veste na mão: <b>3 de dano</b>, durabilidade de pedra e <b>sem tempo de espera</b> para bater, em qualquer mão (na segunda mão, o botão direito soca). Com ela o jogador luta como um boxeador, com <b>animações próprias</b> em primeira e terceira pessoa: base de guarda, jab reto, corrida, Soco Carregado e Onda de Choque. A skill <b>Bloquear</b> da Árvore das Manoplas (só no botão direito) levanta a guarda depois de 1,5s segurando e bloqueia como um escudo.',
     [crafting('leather_gauntlet')]),
    ('magicblocks:enchanted_gauntlet', 'A <b>Manopla Encantada</b> (Cristal Instável, ferro e Cristal Instável; Essência de Mana dos lados da Manopla de Couro; Tecido de Mago embaixo) dá <b>5 de dano</b>, tem 400 de durabilidade, é muito encantável e <b>15%</b> dos socos soltam uma faísca arcana (+3 de dano mágico). As duas manoplas podem ser <b>reforçadas</b> na bancada com 4 lingotes de ferro ou ouro, diamantes ou netheritas em cruz em volta delas (mais dano e a durabilidade da ferramenta daquele metal). A Luva de Lobisomem agora tem as garras na palma e 10% de chance de deixar o alvo enjoado e sangrando.',
     [crafting('enchanted_gauntlet')]),
])


# ---- entradas 1.0.162 ----
ARMAS.extend([
    ('magicblocks:metal_gauntlet', 'A <b>Luva de Metal</b> só sai da forja do <b>ferreiro goblin</b> (aba Armas): 6 barras de ferro, 1 corrente e 6 ossos de ork. <b>15 de dano</b>, 900 de durabilidade, placas de ferro, anel de corrente e espetos de osso nos nós. Como todas as manoplas, bate sem tempo de espera em qualquer mão, e o soco da segunda mão tem o mesmo alcance da principal.',
     []),
    ('magicblocks:void_gauntlet', 'A <b>Manopla do Vazio</b> é feita com os materiais do Vazio (Fragmentos, Cristal Abissal, Barras e uma Pepita do Vazio). <b>15 de dano</b> e 1.800 de durabilidade: cada soco <b>puxa os inimigos</b> a 4 blocos do alvo para perto dele, e 20% abrem um <b>mini buraco negro</b> (+6 de dano mágico em volta).',
     [crafting('void_gauntlet')]),
])

# ---- entradas 1.0.166 ----
ARMAS.extend([
    ('magicblocks:iron_gauntlet', 'A <b>Manopla de Ferro</b>: a Manopla de Couro no meio e 4 lingotes de ferro em cruz. <b>7 de dano</b>, 250 de durabilidade, placas de ferro no braço.',
     [crafting('iron_gauntlet')]),
    ('magicblocks:golden_gauntlet', 'A <b>Manopla de Ouro</b>: a Manopla de Couro e 4 lingotes de ouro em cruz. <b>6 de dano</b> e muito encantável.',
     [crafting('golden_gauntlet')]),
    ('magicblocks:diamond_gauntlet', 'A <b>Manopla de Diamante</b>: a Manopla de Couro e 4 diamantes em cruz. <b>10 de dano</b>, com uma gema acesa nas costas da mão.',
     [crafting('diamond_gauntlet')]),
    ('magicblocks:netherite_gauntlet', 'A <b>Manopla de Netherita</b>: Melhoria de Netherita na mesa de ferraria sobre a de diamante. <b>13 de dano</b>, filetes de ouro escuro, não queima na lava.',
     [smithing3('minecraft:netherite_upgrade_smithing_template', 'magicblocks:diamond_gauntlet', 'minecraft:netherite_ingot', 'magicblocks:netherite_gauntlet')]),
    ('magicblocks:manilium_gauntlet', 'A <b>Manopla de Manilium</b>: <b>18 de dano</b> e a <b>galáxia</b> nas placas, como os outros itens de Manilium (no braço, em primeira e terceira pessoa). 20% dos socos <b>explodem em estrelas</b> (+6 de dano mágico em volta do alvo).',
     [smithing('magicblocks:netherite_gauntlet', 'magicblocks:manilium_gauntlet')]),
])


# ---- entradas 1.0.164 ----
ARMAS.extend([
    ('magicblocks:leather_gauntlet', 'Transformações das manoplas: segure <b>Shift + botão direito</b> com uma manopla na mão por 3s e solte. <b>Punhos Cerrados</b> imbui mana nas manoplas (+15% de dano, Velocidade I e Resistência I; 1 de mana a cada 20s) e a melhoria <b>Espírito de Luta</b> envolve o corpo inteiro em mana (+25% de dano, Velocidade II e Resistência II; 1 de mana a cada 10s). A <b>Fúria do Lutador</b> também virou transformação, e o <b>Soco Carregado</b> agora joga o jogador para a frente junto com a rajada.',
     [table([('Punhos Cerrados', '+15% de dano, Velocidade I, Resistência I, 1 de mana a cada 20s'),
             ('Espírito de Luta', '+25% de dano, Velocidade II, Resistência II, 1 de mana a cada 10s')], head=('Transformação', 'Efeito'))]),
])
CRIATURAS.extend([
    ('magicblocks:ember_boar_spawn_egg', 'O <b>Javali de Brasa</b> vive nas planícies e deltas da <b>Forja Primordial</b>, perto dos <b>vulcões gigantes</b> (cones de basalto e pedra-negra de até 42 blocos, com cratera de lava e rios de magma). Tem 90 de vida, pelo carvão com rachaduras de lava acesas e é imune a fogo. Todos os golpes são marcados no chão antes.',
     [table([('Pancada', 'De perto: cabeçada com as presas que joga para cima e queima'),
             ('Investida', 'Faixa no chão: abaixa a cabeça, raspa o chão e dispara em linha reta; se bater numa parede, fica tonto'),
             ('Pisada', 'Disco em volta: empina e bate no chão como o Golem de Fogo, soltando um anel de fogo (pule por cima)')],
            head=('Ataque', 'Como funciona'))]),
])
RECURSOS.extend([
    ('magicblocks:boar_tusk', 'A <b>Presa de Javali</b> cai do Javali de Brasa (50%, +10% por nível de Pilhagem). É uma peça da futura <b>Espada do Apocalipse</b>.',
     []),
])

PAGES = [
    ('recursos', 'Recursos', 'Materiais, essências e itens úteis.', RECURSOS),
    ('blocos', 'Blocos', 'Blocos que você coloca no mundo.', BLOCOS),
    ('blocos-magicos', 'Blocos Mágicos', 'Blocos que flutuam na mão e dão poderes elementais.', MAGICOS),
    ('armas-e-armaduras', 'Armas e Armaduras', 'Ferramentas Instáveis, o equipamento de Manilium e o Talismã dos Blocos.', ARMAS),
    ('o-vazio', 'O Vazio', 'A dimensão embaixo do mundo: ilhas, minérios, criaturas, A Forja e o Leviatã.', VAZIO),
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
                   for slug, title, _, _ in PAGES) + ('<a href="rituais.html"%s>Rituais</a>' % (' class="on"' if active == 'rituais' else '')) + ('<a href="infusor.html"%s>Infusor</a>' % (' class="on"' if active == 'infusor' else '')) + ('<a href="integracoes.html"%s>Integrações</a>' % (' class="on"' if active == 'integracoes' else '')) + ('<a href="balanceamento.html"%s>Balanceamento</a>' % (' class="on"' if active == 'balanceamento' else ''))
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
        ('Drops raros do mod', 'caem multiplicador vezes menos', 'Fragmentos Lunares e do Eclipse, Diamante Instável, Essência de Mana e do Void, Orbes de Mana, Estilhaços Instáveis e Barras de Manilium. Com x2 cai metade (a parte quebrada vira chance). O <b>loot dos chefes</b> (golens e Esmeralda Colossal) <b>não muda</b>.')])
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


# ===================================================================== rituais (aba propria)

# (id, nome, catalisador, itens nos 4 pedestais em cruz [N, S, L, O], itens nas 4 diagonais ou None, energia, resultado
#  (item ou None), efeito, observacao)
RITUAIS = [
    ('mana_orb', 'Orbe de Mana', 'magicblocks:elemental_diamond', ['magicblocks:mana_essence'] * 4, None, 4000,
     'magicblocks:mana_orb', 'Cria uma <b>Orbe de Mana</b>.', ''),
    ('transmutation', 'Transmutação', 'minecraft:diamond',
     ['magicblocks:mana_essence', 'magicblocks:mana_essence', 'minecraft:emerald', 'minecraft:emerald'], None, 6000,
     'magicblocks:elemental_diamond', 'Transforma o diamante em <b>2 Cristais Instáveis</b>.', ''),
    ('rain', 'Chuva', 'magicblocks:mana_orb',
     ['minecraft:water_bucket', 'minecraft:water_bucket', 'minecraft:prismarine_crystals', 'minecraft:prismarine_crystals'], None, 5000,
     None, 'Chove por <b>10 minutos</b>.', 'Os baldes voltam vazios para os pedestais.'),
    ('clear', 'Céu Limpo', 'magicblocks:mana_orb',
     ['minecraft:sunflower', 'minecraft:sunflower', 'minecraft:glowstone_dust', 'minecraft:glowstone_dust'], None, 5000,
     None, 'Para a chuva e, se for noite, <b>pula para a manhã</b>.', ''),
    ('storm', 'Tempestade', 'magicblocks:mana_orb',
     ['minecraft:lightning_rod', 'minecraft:lightning_rod', 'minecraft:gunpowder', 'minecraft:gunpowder'], None, 8000,
     None, 'Tempestade com raios por <b>5 minutos</b>.', ''),
    ('purple_moon', 'Lua Roxa', 'minecraft:ender_eye',
     ['minecraft:amethyst_shard', 'minecraft:amethyst_shard', 'magicblocks:mana_essence', 'magicblocks:mana_essence'], None, 15000,
     None, 'Chama a <b>Lua Roxa</b> agora (se for noite) ou na próxima noite.', ''),
    ('eclipse', 'Eclipse Solar', 'magicblocks:lunar_fragment',
     ['minecraft:sunflower', 'minecraft:sunflower', 'minecraft:obsidian', 'minecraft:obsidian'], None, 15000,
     None, 'Chama o <b>Eclipse Solar</b> agora (se for dia) ou no próximo meio-dia.', ''),
    ('blessing', 'Bênção', 'minecraft:golden_apple',
     ['magicblocks:mana_essence', 'minecraft:blaze_powder', 'minecraft:feather', 'minecraft:sugar'], None, 8000,
     None, 'Força II, Velocidade II, Regeneração e Resistência por <b>5 minutos</b> para todos a até 12 blocos.', ''),
    ('knowledge', 'Conhecimento', 'minecraft:book',
     ['magicblocks:lunar_fragment', 'magicblocks:lunar_fragment', 'magicblocks:mana_orb', 'magicblocks:mana_orb'], None, 20000,
     None, '<b>+1 ponto de habilidade</b> para quem começou o ritual.', ''),
    ('elemental_armor', 'Armadura Elemental', 'magicblocks:elemental_chestplate',
     ['magicblocks:fire_block', 'magicblocks:elemental_diamond', 'magicblocks:mana_essence', 'magicblocks:mana_essence'], None, 8000,
     'magicblocks:elemental_chestplate', 'A peça ganha o <b>elemento do bloco</b> (mantém os encantamentos).',
     'Use o Bloco Mágico do elemento que quiser (na imagem, Fogo). Para o <b>Void</b>, use a <b>Essência do Void</b>: o Bloco de Void não serve. '
     'O bloco tem 70% de chance de voltar para o pedestal.'),
    ('awakened_star', 'Estrela Despertada', 'magicblocks:mana_star',
     ['magicblocks:lunar_fragment', 'magicblocks:fire_block', 'magicblocks:void_essence', 'minecraft:nether_star'], None, 25000,
     'magicblocks:awakened_mana_star', 'Cria a <b>Estrela de Mana Despertada</b>.',
     'Qualquer Bloco Mágico serve (na imagem, Fogo); ele tem 70% de chance de voltar para o pedestal.'),
    ('golem', 'Invocação do Golem', 'magicblocks:fire_block',
     ['magicblocks:mana_orb', 'magicblocks:mana_orb', 'magicblocks:elemental_diamond', 'magicblocks:elemental_diamond'], None, 20000,
     'magicblocks:ruin_pedestal', 'Cria o <b>Invocador</b> do golem do elemento do bloco: coloque onde quiser para lutar com ele.',
     'O Bloco Mágico no altar <b>não é gasto</b>.'),
    ('chaos_blade', 'Lâmina do Caos', 'magicblocks:beast_sword', ['magicblocks:manilium_ingot'] * 4, ['magicblocks:elemental_diamond'] * 4, 30000,
     'magicblocks:chaos_blade', 'Transforma a Espada da Besta (comum ou Celestial) na <b>Lâmina do Caos</b> (mantém encantamentos).', ''),
    ('structure_compass', 'Bússola de Estruturas', 'minecraft:compass', ['magicblocks:mana_essence'] * 4, ['minecraft:cobweb'] * 4, 8000,
     'minecraft:compass', 'Cria a <b>Bússola Encantada de Estruturas</b> (caixa de ametista; com ela na mão a <b>distância até o alvo</b> aparece acima da hotbar): botão direito abre uma lista com busca de todas as estruturas '
     '(do jogo e de outros mods); escolha uma e ela aponta para a mais perto.', ''),
    ('biome_compass', 'Bússola de Biomas', 'minecraft:compass', ['magicblocks:mana_essence'] * 4, ['minecraft:oak_leaves'] * 4, 8000,
     'minecraft:compass', 'Cria a <b>Bússola Encantada de Biomas</b>: lista com busca de todos os biomas; escolha um e ela aponta para o mais perto.',
     'Qualquer folha serve (na imagem, Carvalho).'),
    ('mana_totem', 'Totem de Mana', 'minecraft:totem_of_undying', ['magicblocks:mana_orb', 'magicblocks:mana_orb', 'magicblocks:manilium_ingot', 'magicblocks:mana_star'],
     ['magicblocks:abyssal_crystal', 'magicblocks:abyssal_crystal', 'magicblocks:void_bar', 'magicblocks:void_bar'], 30000,
     'magicblocks:mana_totem', 'Cria o <b>Totem da Imortalidade de Mana</b>: salva da morte gastando 10 de mana (não se gasta) e vincula itens à alma no Infuser.', ''),
    ('solar_shield', 'Escudo Solar', 'minecraft:shield', ['magicblocks:sunsteel_ingot'] * 4, ['magicblocks:void_bar'] * 4, 30000,
     'magicblocks:solar_shield', 'Cria o <b>Escudo Solar</b> (aparar com o botão esquerdo defendendo).', ''),
    ('radiant_sword', 'Espada Radiante', 'magicblocks:solar_sword',
     ['magicblocks:radiant_soul', 'magicblocks:radiant_soul', 'magicblocks:moth_wing', 'magicblocks:moth_wing'], None, 25000,
     'magicblocks:radiant_sword', 'Transforma a Espada de Metal Solar na <b>Espada Radiante</b> (mantém bloco, pintura e encantamentos).', ''),
    ('sun_block', 'Bloco Solar', 'magicblocks:light_heart', ['magicblocks:fire_block'] * 4, ['magicblocks:mana_orb'] * 4, 40000,
     'magicblocks:sun_block', 'Cria o <b>Bloco Solar</b>.', 'Os 4 Blocos de Fogo precisam ser <b>Verdadeiros</b> (os que o golem de fogo devolve).'),
]

RIT_DIR = os.path.join(SITE, 'img', 'rituais')


def ritual_image(rid, catalyst, cross, diag):
    """A foto de cima do altar com o icone de cada item em cima do seu pedestal (e o catalisador no altar)."""
    base = Image.open(os.path.join(RIT_DIR, 'base8.png' if diag else 'base4.png')).convert('RGBA')
    c = 480
    spots = [(c, c - 322), (c, c + 322), (c + 322, c), (c - 322, c)]
    if diag:
        spots += [(c - 214, c - 214), (c + 214, c - 214), (c - 214, c + 214), (c + 214, c + 214)]
    items = list(cross) + list(diag or [])

    def put(item_id, x, y, size):
        ic = Image.open(os.path.join(SITE, icon(item_id))).convert('RGBA').resize((size, size), Image.NEAREST)
        sh = Image.new('RGBA', ic.size, (0, 0, 0, 0))
        sh.putalpha(ic.getchannel('A').point(lambda a: int(a * 0.55)))
        base.alpha_composite(sh, (x - size // 2 + 5, y - size // 2 + 6))
        base.alpha_composite(ic, (x - size // 2, y - size // 2))

    for item_id, (x, y) in zip(items, spots):
        put(item_id, x, y, 84)
    # catalisador no altar, com um brilho roxo em volta
    glow = Image.new('RGBA', base.size, (0, 0, 0, 0))
    gp = glow.load()
    for yy in range(c - 80, c + 80):
        for xx in range(c - 80, c + 80):
            d = ((xx - c) ** 2 + (yy - c) ** 2) ** 0.5
            if d < 80:
                gp[xx, yy] = (200, 120, 255, int(110 * (1 - d / 80.0)))
    base.alpha_composite(glow)
    put(catalyst, c, c, 104)
    out = os.path.join(RIT_DIR, rid + '.png')
    base.convert('RGB').save(out, optimize=True)
    return 'img/rituais/%s.png' % rid


def rituals_page():
    side = ''.join('<a href="#%s"><img src="%s" alt="">%s</a>' % (rid.replace('_', '-'), icon(cat), html.escape(nome))
                   for rid, nome, cat, *_ in RITUAIS)
    cards = ''
    for rid, nome, cat, cross, diag, energy, out, effect, obs in RITUAIS:
        img = ritual_image(rid, cat, cross, diag)
        counts = {}
        for it in list(cross) + list(diag or []):
            counts[it] = counts.get(it, 0) + 1
        peds = ''.join('<li>%s<span>%dx %s</span></li>' % (slot(it), n, html.escape(name(it))) for it, n in counts.items())
        res = ('<p class="rit-out">Resultado: %s <b>%s</b></p>' % (slot(out), html.escape(name(out)))) if out else ''
        cards += ('<article class="entry ritual" id="%s" data-name="%s"><div class="rit-img"><img src="%s" alt="%s visto de cima" loading="lazy"></div>'
                  '<div class="rit-info"><h3>%s</h3><p>%s</p>'
                  '<p class="rit-cat">No altar: %s <b>%s</b></p><p class="rit-lbl">Nos pedestais%s:</p><ul class="rit-list">%s</ul>'
                  '<p class="rit-energy">Energia de natureza: <b>%s</b></p>%s%s</div></article>') % (
            rid.replace('_', '-'), html.escape(nome.lower()), img, html.escape(nome), html.escape(nome), effect,
            slot(cat), html.escape(name(cat)), ' (os 8: em cruz e nas diagonais)' if diag else ' (os 4 em cruz)', peds,
            '{:,}'.format(energy).replace(',', '.'), res, ('<p class="tip">%s</p>' % obs) if obs else '')
    intro = ('<div class="callout"><b>Como montar:</b> coloque o <b>Altar de Rituais</b> e <b>4 Pedestais</b> a 3 blocos dele '
             '(norte, sul, leste e oeste), na mesma altura. Rituais de 8 itens usam também <b>4 pedestais nas diagonais</b>, a 2 blocos. '
             'Ligue o altar à energia de natureza pelos cabos, clique no altar com o <b>catalisador</b>, ponha os itens nos pedestais '
             '(qualquer ordem) e clique no altar de <b>mão vazia</b>. Um funil embaixo do altar recebe o resultado.</div>')
    body = ('<div class="layout"><aside class="side"><input id="busca" type="search" placeholder="Buscar..." aria-label="Buscar">'
            '<div class="side-list">%s</div></aside><main><h1>Rituais</h1><p class="sub">Todos os rituais do Altar, vistos de cima: '
            'cada item aparece em cima do pedestal onde vai.</p>%s%s</main></div>') % (side, intro, cards)
    return page('Rituais', body, 'rituais')


# ===================================================================== infusor (aba propria)

# (ancora, nome, entrada, catalisador (None = conversao simples, sem catalisador), resultado, segundos, texto, observacao)
INFUSOES = [
    ('cristal-instavel', 'Cristal Instável', 'minecraft:diamond', None, 'magicblocks:elemental_diamond', 10,
     'Conversão simples: só o diamante, sem catalisador. Gasta combustível vegetal.', ''),
    ('estrela-de-mana', 'Estrela de Mana', 'minecraft:nether_star', 'magicblocks:mana_orb', 'magicblocks:mana_star', 30, 'Cria a <b>Estrela de Mana</b>.', ''),
    ('estrela-do-vazio', 'Estrela do Vazio', 'magicblocks:awakened_mana_star', 'magicblocks:void_bar', 'magicblocks:void_star', 40,
     'A Estrela de Mana Despertada vira a <b>Estrela do Vazio</b>.', ''),
    ('reforco-armadura', 'Reforço da Armadura de Manilium', 'magicblocks:manilium_chestplate', 'magicblocks:mana_star', 'magicblocks:manilium_chestplate', 15,
     '<b>+1 de defesa</b> por estrela, até +5. Com a <b>Estrela Despertada</b> vai de +5 até +10, e com a <b>Estrela do Vazio</b> de +10 até +15.',
     'Vale para qualquer peça de Manilium e para a armadura da Besta Celestial.'),
    ('reforco-espada', 'Reforço da Espada', 'magicblocks:manilium_sword', 'magicblocks:mana_star', 'magicblocks:manilium_sword', 15,
     '<b>+1 de dano</b> por estrela, até +50. Com a <b>Estrela Despertada</b> vai até +120 e com a <b>Estrela do Vazio</b> até +150.',
     'Vale para a Espada de Manilium e a Lâmina do Caos.'),
    ('espada-com-bloco', 'Espada com Bloco Mágico', 'magicblocks:manilium_sword', 'magicblocks:fire_block', 'magicblocks:manilium_sword', 15,
     'A Espada de Manilium vazia recebe o <b>Bloco Mágico</b> na guarda e ganha os poderes dele.', 'Qualquer Bloco Mágico serve (na imagem, Fogo).'),
    ('espada-duas-maos', 'Espada Duas Mãos', 'magicblocks:manilium_sword', 'magicblocks:leviathan_claw', 'magicblocks:manilium_sword', 20,
     'A Espada de Manilium fica <b>duas mãos</b>: na segunda mão, o botão direito bate como na principal.', ''),
    ('espada-besta-celestial', 'Espada da Besta Celestial', 'magicblocks:beast_sword', 'magicblocks:manilium_ingot', 'magicblocks:manilium_beast_sword', 30,
     'A Espada da Besta vira a <b>Espada da Besta Celestial</b> (60 de dano, galáxia roxa). Mantém encantamentos e nome.', ''),
    ('lamina-do-caos-acorrentada', 'Lâmina do Caos Acorrentada', 'magicblocks:chaos_blade', 'minecraft:chain', 'magicblocks:chaos_blade', 20,
     'Skin da Lâmina do Caos no estilo das <b>Lâminas do Caos</b>: lâmina curva escura com <b>veios vermelhos incandescentes</b>, cabo enrolado e uma corrente pendurada. Na <b>Fúria</b> os veios viram uma <b>galáxia vermelha</b>. Mantém dano, encantamentos e nome.', ''),
    ('cajado-com-bloco', 'Cajado com Bloco Mágico', 'magicblocks:ancestral_staff', 'magicblocks:fire_block', 'magicblocks:ancestral_staff', 15,
     'O Cajado Ancestral vazio recebe o <b>Bloco Mágico</b> e ganha o poder dele.', 'Qualquer Bloco Mágico menos Baú e Slime (na imagem, Fogo).'),
    ('cajado-arcano', 'Cajado Arcano', 'magicblocks:ancestral_staff', 'magicblocks:mana_stone', 'magicblocks:arcane_staff', 30,
     'O Cajado Ancestral vira o <b>Cajado Arcano</b>: carrega mais rápido e pode devolver mana. Mantém o bloco e os encantamentos.', ''),
    ('armadura-elemental-leviata', 'Armadura Elemental de Leviatã', 'magicblocks:elemental_chestplate', 'magicblocks:leviathan_scale', 'magicblocks:elemental_chestplate', 25,
     'A peça Elemental ganha <b>+2 de armadura, +1,5 de resistência</b> e conta como peça de Leviatã. Mantém o elemento e os encantamentos.', ''),
    ('peitoral-conversor', 'Peitoral com Conversor de Almas', 'minecraft:iron_chestplate', 'magicblocks:soul_converter', 'minecraft:iron_chestplate', 15,
     'O <b>Conversor de Almas</b> fica embutido no peitoral.', 'Qualquer peitoral serve.'),
    ('molde-manilium', 'Molde de Melhoria de Manilium', 'minecraft:netherite_upgrade_smithing_template', 'magicblocks:mana_essence',
     'magicblocks:manilium_upgrade_smithing_template', 20, 'Cria o <b>Molde de Melhoria de Manilium</b>.', ''),
    ('molde-esmeralda-real', 'Molde de Esmeralda Real', 'minecraft:netherite_upgrade_smithing_template', 'magicblocks:emerald_heart',
     'magicblocks:royal_emerald_template', 30, 'Cria o <b>Molde de Esmeralda Real</b>.', ''),
    ('spawner-manilium', 'Spawner de Manilium', 'magicblocks:lifeless_spawner', 'magicblocks:manilium_ingot', 'magicblocks:manilium_spawner', 30,
     'O Spawner sem Vida vira o <b>Spawner de Manilium</b>.', ''),
    ('melhoria-velocidade', 'Melhoria de Velocidade (Spawner)', 'minecraft:smooth_stone', 'minecraft:sugar', 'magicblocks:spawner_upgrade_speed', 15,
     'Melhoria do Spawner de Manilium: <b>mais rápido</b>.', ''),
    ('melhoria-area', 'Melhoria de Área (Spawner)', 'minecraft:smooth_stone', 'minecraft:beacon', 'magicblocks:spawner_upgrade_chunk', 30,
     'Melhoria do Spawner de Manilium: <b>funciona sem jogador perto</b>.', ''),
    ('melhoria-quantidade', 'Melhoria de Quantidade (Spawner)', 'minecraft:smooth_stone', 'minecraft:zombie_head', 'magicblocks:spawner_upgrade_count', 20,
     'Melhoria do Spawner de Manilium: <b>mais criaturas</b> por vez.', 'Qualquer cabeça de criatura serve.'),
    ('melhoria-dormente', 'Melhoria Dormente (Spawner)', 'minecraft:smooth_stone', 'minecraft:soul_sand', 'magicblocks:spawner_upgrade_dormant', 20,
     'Melhoria do Spawner de Manilium: as criaturas nascem <b>sem IA e sem som</b>.', ''),
    ('fogo-vermelho', 'Bloco de Fogo Vermelho', 'magicblocks:fire_block', 'minecraft:redstone_block', 'magicblocks:fire_block', 15,
     'O Bloco de Fogo fica na <b>variante vermelha</b>: todos os ataques ficam vermelhos.', ''),
    ('tnt-ativa', 'Bloco de TNT Ativo', 'magicblocks:tnt_block', 'minecraft:tnt', 'magicblocks:tnt_block', 20,
     'O Bloco de TNT fica <b>ativo</b>: a TNT arremessada e a nuclear quebram blocos.', ''),
    ('redstone-instavel', 'Bloco de Redstone Instável', 'magicblocks:redstone_block', 'magicblocks:tnt_block', 'magicblocks:redstone_block', 30,
     'O Bloco de Redstone vira o <b>Instável</b>: os lasers quebram blocos.',
     'A alimentação é o <b>Bloco de TNT Ativo</b> (faça antes: Bloco de TNT + TNT comum). O Bloco de TNT normal não serve.'),
    ('bloco-de-gelo', 'Bloco de Gelo', 'magicblocks:water_block', 'minecraft:blue_ice', 'magicblocks:ice_block', 20,
     'O Bloco de Água vira o <b>Bloco de Gelo</b>.', ''),
    ('muda-de-mana', 'Muda de Mana', 'minecraft:oak_sapling', 'magicblocks:mana_essence', 'magicblocks:mana_sapling', 15,
     'Qualquer muda vira a <b>Muda de Mana</b>.', 'Qualquer muda serve (menos a própria Muda de Mana).'),
]

INF_DIR = os.path.join(SITE, 'img', 'infusor')


def infuser_image(key, inp, cat, out):
    """A tela do Nature Infuser (da textura do mod) com a seta cheia e os itens nos slots: entrada em cima, catalisador
    embaixo (na alimentacao) e o resultado a direita."""
    os.makedirs(INF_DIR, exist_ok=True)
    tex = Image.open(os.path.join(MOD, 'assets', 'magicblocks', 'textures', 'gui', 'nature_infuser.png')).convert('RGBA')
    gui = tex.crop((0, 0, 176, 78))
    border = tex.crop((0, 0, 176, 3)).transpose(Image.FLIP_TOP_BOTTOM)
    gui.alpha_composite(border, (0, 75))
    gui.alpha_composite(tex.crop((176, 0, 200, 11)), (76, 39))   # seta cheia
    s = 4
    img = gui.resize((176 * s, 78 * s), Image.NEAREST)

    def put(item_id, x, y):
        ic = Image.open(os.path.join(SITE, icon(item_id))).convert('RGBA').resize((16 * s, 16 * s), Image.NEAREST)
        img.alpha_composite(ic, (x * s, y * s))

    put(inp, 44, 20)
    if cat:
        put(cat, 44, 54)
    put(out, 116, 37)
    img.convert('RGB').save(os.path.join(INF_DIR, key + '.png'), optimize=True)
    return 'img/infusor/%s.png' % key


def infuser_page():
    side = ''.join('<a href="#%s"><img src="%s" alt="">%s</a>' % (k, icon(o), html.escape(n)) for k, n, _, _, o, *_ in INFUSOES)
    cards = ''
    for key, nome, inp, cat, out, secs, text, obs in INFUSOES:
        img = infuser_image(key, inp, cat, out)
        cards += ('<article class="entry ritual infusion" id="%s" data-name="%s"><div class="rit-img"><img src="%s" alt="%s no Nature Infuser" loading="lazy"></div>'
                  '<div class="rit-info"><h3>%s</h3><p>%s</p>'
                  '<p class="rit-cat">Entrada: %s <b>%s</b></p>%s<p class="rit-out">Resultado: %s <b>%s</b></p>'
                  '<p class="rit-energy">Tempo: <b>%d segundos</b></p>%s</div></article>') % (
            key, html.escape(nome.lower()), img, html.escape(nome), html.escape(nome), text, slot(inp), html.escape(name(inp)),
            ('<p class="rit-cat">Catalisador (embaixo): %s <b>%s</b></p>' % (slot(cat), html.escape(name(cat)))) if cat else '',
            slot(out), html.escape(name(out)), secs, ('<p class="tip">%s</p>' % obs) if obs else '')
    intro = ('<div class="callout"><b>Como usar:</b> ponha o item no slot de <b>cima</b> e o catalisador no slot de <b>baixo</b> '
             '(o da alimentação). O Nature Infuser precisa de <b>natureza em volta</b> (plantas, folhas e grama perto). '
             'Na infusão ele gasta 1 catalisador e a entrada e não queima combustível; a conversão simples (sem catalisador) '
             'usa combustível vegetal no slot de baixo. O resultado mantém encantamentos, dano e nome da entrada.</div>')
    body = ('<div class="layout"><aside class="side"><input id="busca" type="search" placeholder="Buscar..." aria-label="Buscar">'
            '<div class="side-list">%s</div></aside><main><h1>Nature Infuser</h1><p class="sub">Todas as receitas do Infusor, como '
            'aparecem na tela dele: entrada em cima, catalisador embaixo e o resultado à direita.</p>%s%s</main></div>') % (side, intro, cards)
    return page('Infusor', body, 'infusor')


# ===================================================================== integracoes (aba propria)

INTEGRACOES = [
    ('jei', 'JEI (Just Enough Items)', 'magicblocks:nature_workbench',
     'Todas as receitas especiais do Magic &amp; Blocks aparecem no JEI, além das receitas normais de bancada e fornalha.',
     [table([('Nature Infuser', 'Todas as conversões e infusões: entrada + catalisador &rarr; resultado, com o tempo. Clique na <b>seta</b> do Nature Infuser para abrir as receitas dele.'),
             ('Altar de Rituais', 'Os 15 rituais vistos de cima, como no jogo: o catalisador no altar, os itens em volta nos pedestais (em cruz e nas diagonais), o resultado e a energia. Rituais de clima e evento mostram o efeito.'),
             ('Receitas especiais', 'Aparência do Bloco de Folha e do Bloco de Baú, formato do Bloco de Slime, cor do Spawner e tirar o bloco da Espada de Manilium aparecem como receitas de bancada; a pintura das armaduras da Besta aparece na Mesa de Ferraria.'),
             ('Informações', 'Todo item do mod com descrição no livro-guia ganha uma página de informação no JEI (máquinas, mecânicas, criaturas...).'),
             ('Como abrir', 'Aperte <b>R</b> (receita) ou <b>U</b> (usos) em cima do Nature Infuser, do Altar, do Pedestal ou de qualquer item do mod.')],
            head=('Categoria', 'O que mostra'))]),
    ('tinkers', 'Tinkers\' Construct', 'magicblocks:molten_manilium_bucket',
     'Com o Tinkers\' Construct instalado, o Manilium, o Leviatã, o <b>Metal Solar</b> e o <b>Metal do Vazio</b> viram materiais de ferramentas, armaduras e escudos, e os metais derretem na fornalha.',
     [table([('Manilium', 'Barra, bloco', 'Durabilidade 1800, ataque 4,5, mineração 9, nível netherita', 'Enderference e Experienced; armaduras: Proteção Mágica'),
             ('Leviatã', 'Escama (1) e Garra (2)', 'Durabilidade 1500, ataque 5, mineração 7, nível netherita', 'Jagged e Lightweight; espadas, cutelos e adagas com Leviatã ficam <b>duas mãos</b> e entram na <b>Fúria da Besta</b>'),
             ('Metal Solar', 'Barra de Metal Solar (ou fundido)', 'Durabilidade 1700, ataque 5,5, mineração 9, nível netherita', 'Solar Powered e Fiery; armaduras: Proteção contra Fogo'),
             ('Metal do Vazio', '<b>Só fundido</b> (liga na fornalha)', 'Durabilidade 2200, ataque 5, mineração 8, nível netherita', 'Enderference e Dense; armaduras: Enderdodging')],
            head=('Material', 'Feito com', 'Ponta de ferramenta', 'Traços')),
      '<h4>Manilium Derretido</h4>',
      table([('Temperatura', '950° (a fornalha com lava comum já derrete)'),
             ('Barra / Bloco', '90 mb / 810 mb'),
             ('Escama / Garra de Leviatã', '45 mb / 90 mb'),
             ('O líquido', 'Galáxia animada; machuca como o void (sem fogo) e não queima itens')], head=('', 'Manilium Derretido')),
      '<h4>Metal Solar e Metal do Vazio</h4>',
      table([('Metal Solar Derretido', 'Barra de Metal Solar = 90 mb, Minério = 180 mb (1150°)', 'Funde de volta em Barra de Metal Solar'),
             ('Vazio Derretido', 'Barra do Vazio = 90 mb, Pepita = 10 mb (1000°)', 'Funde de volta em Barra do Vazio'),
             ('Cristal Abissal Derretido', 'Cristal Abissal = 100 mb (1000°)', 'Ingrediente da liga'),
             ('Metal do Vazio Derretido', '<b>Liga</b>: 90 mb de Vazio Derretido + 100 mb de Cristal Abissal Derretido = 90 mb (1300°)', 'Funda as peças direto nos moldes')],
            head=('Líquido', 'De onde vem', 'Uso')),
      '<p class="tip">Armaduras do Tinkers ou do Silent Gear feitas com Metal do Vazio, Barra do Vazio ou Metal Solar contam como peças de proteção contra o void (25% cada).</p>']),
    ('silentgear', 'Silent Gear', 'magicblocks:manilium_ingot',
     'Com o Silent Gear instalado, seis itens do mod viram materiais para peças de ferramentas, armas e armaduras.',
     [table([('Barra de Manilium', 'Stellar, Renew e Magnetic', 'Muito encantável, a mais rara'),
             ('Barra do Vazio (Metal do Vazio)', 'Void Ward, Hard e Adamant', 'A mais resistente (2600 de durabilidade); armaduras protegem do void'),
             ('Barra de Metal Solar', 'Fiery, Flame Ward, Brilliant e Lustrous', 'O maior dano (11) e incendeia; armaduras protegem do void'),
             ('Escama de Leviatã', '<b>Besta</b> e Light', 'Besta: espadas, adagas, facas, katanas e machetes ficam duas mãos e entram na Fúria da Besta'),
             ('Cristal Abissal', '<b>Rasgo do Vazio</b>', 'Os golpes aplicam Wither'),
             ('Cristal Instável', '<b>Surto de Mana</b> e Brittle', 'Cada golpe tem 5% por nível de devolver 1 de mana')],
            head=('Material', 'Traços', 'Destaque'))]),
    ('curios', 'Curios', 'magicblocks:soul_converter',
     'Com o Curios instalado, alguns itens podem ir nos slots extras de acessório (e continuam funcionando).',
     [table([('Conversor de Almas', 'Amuleto (necklace)', 'Paga a mana com XP quando ela acaba'),
             ('Talismã dos Blocos', 'Cinto (belt)', 'A roda de blocos continua funcionando'),
             ('Lanterna de Mana', 'Cinto (belt)', 'Continua iluminando'),
             ('Bolsa de Orbes', 'Cinto (belt)', 'A mana das orbes dentro dela continua sendo usada')], head=('Item', 'Slot', 'Efeito'))]),
]


def integrations_page():
    side = ''.join('<a href="#%s"><img src="%s" alt="">%s</a>' % (k, icon(ic), html.escape(n.replace('\\', ''))) for k, n, ic, _, _ in INTEGRACOES)
    cards = ''
    for key, nome, ic, intro, extras in INTEGRACOES:
        cards += ('<article class="entry" id="%s" data-name="%s"><div class="head"><span class="slot big"><img src="%s" alt=""></span>'
                  '<div><h3>%s</h3><p>%s</p></div></div>%s</article>') % (key, html.escape(nome.lower()), icon(ic), nome, intro, ''.join(extras))
    body = ('<div class="layout"><aside class="side"><input id="busca" type="search" placeholder="Buscar..." aria-label="Buscar">'
            '<div class="side-list">%s</div></aside><main><h1>Integrações</h1><p class="sub">Mods que conversam com o Magic &amp; Blocks. '
            'Todos são <b>opcionais</b>: sem eles nada disso aparece e o mod funciona normalmente.</p>%s</main></div>') % (side, cards)
    return page('Integrações', body, 'integracoes')


def home():
    cards = ''
    for slug, title, sub, entries in PAGES:
        icons = ''.join('<img src="%s" alt="">' % icon(i) for i, _, _ in entries[:5])
        cards += '<a class="topic" href="%s.html"><div class="icons">%s</div><h3>%s</h3><p>%s</p><span>%d páginas &rarr;</span></a>' % (
            slug, icons, title, sub, len(entries))
    body = ('<main class="home"><img class="logo" src="img/logo.png" alt="Magic & Blocks">'
            '<p class="lead">A wiki oficial do <b>Magic &amp; Blocks</b>: blocos mágicos que flutuam na mão, mana, o Nature Infuser, '
            'equipamento de Manilium, magos e muito mais para Minecraft 1.20.1 (Forge).</p>'
            '<div class="pills"><span>Minecraft 1.20.1</span><span>Forge 47</span><span><a href="integracoes.html">JEI, Tinkers, Silent Gear e Curios</a></span><span>PT-BR / EN</span></div>'
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
write('rituais.html', rituals_page())
write('infusor.html', infuser_page())
write('integracoes.html', integrations_page())

if MISSING_RECIPES:
    print('receitas que nao existem mais (puladas):', ', '.join(MISSING_RECIPES))
