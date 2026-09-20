#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate a long bilingual PowerPoint on twelve Li Bai poems."""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import nsmap
from lxml import etree
import copy

# Colors — ink-wash / Tang aesthetic (avoid purple / cream / terracotta AI defaults)
INK = RgbColor(0x1A, 0x1F, 0x2E)
INK_SOFT = RgbColor(0x2C, 0x35, 0x48)
JADE = RgbColor(0x1E, 0x5A, 0x5A)
JADE_LIGHT = RgbColor(0x2A, 0x7A, 0x72)
GOLD = RgbColor(0xA6, 0x7C, 0x52)
PAPER = RgbColor(0xF7, 0xF3, 0xEB)
PAPER_DARK = RgbColor(0xE8, 0xE0, 0xD0)
WHITE = RgbColor(0xFF, 0xFF, 0xFF)
MUTED = RgbColor(0x5A, 0x62, 0x72)

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def set_run_font(run, name="Microsoft YaHei", size=18, bold=False, color=INK, italic=False):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    # Also set East Asian font via XML for Chinese rendering
    rPr = run._r.get_or_add_rPr()
    # clear existing latin/ea
    for child in list(rPr):
        if child.tag.endswith("}latin") or child.tag.endswith("}ea") or child.tag.endswith("}cs"):
            rPr.remove(child)
    latin = etree.SubElement(rPr, "{http://schemas.openxmlformats.org/drawingml/2006/main}latin")
    latin.set("typeface", name)
    ea = etree.SubElement(rPr, "{http://schemas.openxmlformats.org/drawingml/2006/main}ea")
    ea.set("typeface", name)


def add_textbox(slide, left, top, width, height, text, *, size=18, bold=False,
                color=INK, align=PP_ALIGN.LEFT, font="Microsoft YaHei", italic=False,
                valign=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = None
    try:
        box.text_frame.paragraphs[0].alignment = align
    except Exception:
        pass
    # Set vertical anchor
    bodyPr = tf._txBody.bodyPr
    if valign == MSO_ANCHOR.MIDDLE:
        bodyPr.set("anchor", "ctr")
    elif valign == MSO_ANCHOR.BOTTOM:
        bodyPr.set("anchor", "b")
    else:
        bodyPr.set("anchor", "t")

    lines = text.split("\n") if text else [""]
    for i, line in enumerate(lines):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.alignment = align
        run = p.add_run()
        run.text = line
        set_run_font(run, name=font, size=size, bold=bold, color=color, italic=italic)
        p.space_after = Pt(4)
    return box


def add_rect(slide, left, top, width, height, fill):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill
    shape.line.fill.background()
    return shape


def add_accent_bar(slide, left, top, width, height=Inches(0.08), color=JADE):
    return add_rect(slide, left, top, width, height, color)


def blank_slide(prs):
    blank = prs.slide_layouts[6]  # blank
    return prs.slides.add_slide(blank)


def paint_bg(slide, color=PAPER):
    add_rect(slide, 0, 0, SLIDE_W, SLIDE_H, color)


def footer(slide, page, total, title="李白诗作精讲 · Li Bai Poetry"):
    add_textbox(
        slide, Inches(0.5), Inches(7.1), Inches(10), Inches(0.3),
        f"{title}  |  {page}/{total}",
        size=10, color=MUTED, align=PP_ALIGN.LEFT
    )


# ---------------------------------------------------------------------------
# Poem data
# ---------------------------------------------------------------------------

POEMS = [
    {
        "no": 1,
        "title_zh": "峨眉山月歌",
        "title_en": "Song of the Moon over Mount Emei",
        "form": "七言绝句 / Seven-character quatrain",
        "period": "开元十三年（约725年） · 出蜀东下游历之初",
        "chinese": (
            "峨眉山月半轮秋，影入平羌江水流。\n"
            "夜发清溪向三峡，思君不见下渝州。"
        ),
        "english": (
            "Half a wheel of autumn moon hangs over Mount Emei;\n"
            "Its reflection drifts with the Pingqiang River’s flow.\n"
            "At night I leave Clear Stream, bound for the Three Gorges;\n"
            "Missing you, unseen, I sail down toward Yuzhou."
        ),
        "background": (
            "此诗作于李白青年出蜀、顺江东下途中。开元十三年左右，二十五岁左右的李白"
            "告别家乡蜀地，自峨眉一带启程，经清溪、渝州，指向三峡。诗中地名连贯："
            "峨眉山—平羌江—清溪—三峡—渝州，勾勒出一段真实的水路行程，是其早期"
            "山水羁旅诗的代表。"
        ),
        "background_en": (
            "Written around 725, when young Li Bai left Shu (Sichuan) and traveled east "
            "by river. Place names form a continuous itinerary: Mount Emei, the Pingqiang "
            "River, Clear Stream, the Three Gorges, and Yuzhou—an early landmark of his "
            "travel poetry."
        ),
        "meaning": (
            "以秋月为情感枢纽：月照故乡，影随江水，人却渐行渐远。“思君不见”一句，"
            "既可解为思念友人，亦可解为对峨眉山月（故乡象征）的依恋。短短四句，"
            "空间不断下移，乡情却愈加浓厚，体现李白早期“景中含情、地名入诗”的清丽风格。"
        ),
        "meaning_en": (
            "The autumn moon anchors homesickness: light stays on the homeland while the "
            "poet drifts away. “Missing you, unseen” may address a friend or the moon itself "
            "as a symbol of home. Brief lines move steadily downstream as longing deepens."
        ),
        "keywords": "乡情 · 秋月 · 蜀江 · 羁旅",
    },
    {
        "no": 2,
        "title_zh": "渡荆门送别",
        "title_en": "Crossing Jingmen: A Farewell",
        "form": "五言律诗 / Five-character regulated verse",
        "period": "开元十四年（约726年） · 出蜀途经荆门",
        "chinese": (
            "渡远荆门外，来从楚国游。\n"
            "山随平野尽，江入大荒流。\n"
            "月下飞天镜，云生结海楼。\n"
            "仍怜故乡水，万里送行舟。"
        ),
        "english": (
            "Crossing far beyond Jingmen Gate,\n"
            "I come to roam the land of Chu.\n"
            "Mountains yield to open plain;\n"
            "The river pours into the vast wilds.\n"
            "Beneath the moon, a flying sky-mirror;\n"
            "Clouds rise and build mirage towers.\n"
            "Still I love my homeland’s waters—\n"
            "They escort my boat for a thousand miles."
        ),
        "background": (
            "李白出蜀后继续东行，渡过荆门进入楚地。荆门山位于今湖北宜都附近，"
            "是长江出蜀入楚的地理标志。此诗既是告别故乡山水，也是面向广阔世界的"
            "自我宣言。颔联“山随平野尽，江入大荒流”历来被推为写江汉开阔气势的名句。"
        ),
        "background_en": (
            "After leaving Shu, Li Bai crossed Jingmen into Chu (Hubei). Jingmen marks the "
            "Yangtze’s exit from the Sichuan basin. The couplet on mountains ending in plains "
            "and the river entering the wilderness is among his most celebrated landscape lines."
        ),
        "meaning": (
            "前半写空间豁然开朗：山尽原出，江入大荒，象征诗人视野与人生境界的拓展；"
            "后半以月、云的奇幻景象烘托壮游兴致，收束却又回落到“故乡水万里送行舟”，"
            "豪迈中不失温柔。全诗在“远游”与“乡恋”之间取得精妙平衡。"
        ),
        "meaning_en": (
            "The first half opens space—plains and wilderness—as a figure for expanding "
            "vision. Moon and clouds heighten the thrill of travel; the close returns to "
            "homeland waters escorting the boat, balancing grandeur with affection."
        ),
        "keywords": "壮游 · 江汉 · 乡恋 · 境界",
    },
    {
        "no": 3,
        "title_zh": "长干行",
        "title_en": "Ballad of Changgan (The Merchant’s Wife)",
        "form": "乐府歌行 / Yuefu narrative song",
        "period": "约开元末至天宝初 · 寓居金陵一带时作",
        "chinese": (
            "妾发初覆额，折花门前剧。\n"
            "郎骑竹马来，绕床弄青梅。\n"
            "同居长干里，两小无嫌猜。\n"
            "十四为君妇，羞颜未尝开。\n"
            "十五始展眉，愿同尘与灰。\n"
            "十六君远行，瞿塘滟滪堆。\n"
            "五月不可触，猿声天上哀。\n"
            "门前迟行迹，一一生绿苔。\n"
            "苔深不能扫，落叶秋风早。\n"
            "八月蝴蝶黄，双飞西园草。\n"
            "感此伤妾心，坐愁红颜老。\n"
            "早晚下三巴，预将书报家。\n"
            "相迎不道远，直至长风沙。"
        ),
        "english": (
            "When my hair first covered my forehead,\n"
            "I picked flowers and played by the gate.\n"
            "You came riding a bamboo horse,\n"
            "Circling the well, tossing green plums.\n"
            "We lived together in Changgan Lane—\n"
            "Two children, without doubt or shame.\n"
            "At fourteen I became your wife,\n"
            "Too shy to ever lift my face.\n"
            "At fifteen I began to smile,\n"
            "Willing to share dust and ash with you.\n"
            "At sixteen you journeyed far,\n"
            "Through Qutang’s perilous Yanyu Rock.\n"
            "In the fifth month one dare not touch it;\n"
            "Gibbons cry sorrow from the skies.\n"
            "Footprints before our gate grow late,\n"
            "Each one sprouting green moss.\n"
            "Moss too deep to sweep away;\n"
            "Fallen leaves, autumn wind comes early.\n"
            "In the eighth month yellow butterflies\n"
            "Fly in pairs over the western garden grass.\n"
            "Seeing this wounds my heart;\n"
            "I sit grieving as youth fades.\n"
            "Whenever you leave the Three Ba region,\n"
            "Send a letter home first.\n"
            "I will meet you, not counting the distance—\n"
            "Even as far as Changfengsha."
        ),
        "background": (
            "《长干行》属乐府旧题，长干里为金陵（今南京）商贾聚居之地。李白以商妇口吻，"
            "叙述青梅竹马、婚后离别与苦候归期。唐代商业繁荣，丈夫远行长江上下游经商"
            "是常见现实；诗中瞿塘、滟滪堆等险滩，既写行程之危，也写妇人心中的恐惧。"
        ),
        "background_en": (
            "A yuefu-style narrative in the voice of a merchant’s wife from Changgan Lane "
            "(Jinling/Nanjing). Childhood love, early marriage, and anxious waiting for a "
            "husband trading along the Yangtze reflect Tang commercial life and river dangers."
        ),
        "meaning": (
            "以年龄为时间轴（覆额—十四—十五—十六），细腻刻画女子从嬉戏到深情、"
            "再到相思煎熬的情感成长。“青梅竹马”“两小无嫌猜”成为汉语中纯洁初恋的"
            "经典意象；末句“直至长风沙”以千里迎夫收束，写出坚贞与深情。全诗叙事与"
            "抒情交融，是李白乐府叙事诗的杰作。"
        ),
        "meaning_en": (
            "Age markers structure the wife’s emotional growth—from play to devotion to "
            "anxious waiting. “Green plums and bamboo horses” became proverbial for innocent "
            "first love; the vow to meet him even at Changfengsha crowns steadfast affection."
        ),
        "keywords": "青梅竹马 · 商妇 · 相思 · 乐府",
    },
    {
        "no": 4,
        "title_zh": "金陵酒肆留别",
        "title_en": "Parting at a Jinling Tavern",
        "form": "七言古诗（短歌） / Short seven-character song",
        "period": "约开元十四年前后 · 金陵送别友人",
        "chinese": (
            "风吹柳花满店香，吴姬压酒唤客尝。\n"
            "金陵子弟来相送，欲行不行各尽觞。\n"
            "请君试问东流水，别意与之谁短长？"
        ),
        "english": (
            "Wind blows willow catkins—fragrance fills the shop;\n"
            "Wu girls press fresh wine and call guests to taste.\n"
            "Young men of Jinling come to see me off;\n"
            "Ready to leave yet lingering, we drain every cup.\n"
            "I ask you—ask the eastward-flowing river:\n"
            "Whose parting sorrow is longer, yours or its waters?"
        ),
        "background": (
            "李白在金陵（南京）与当地友人宴别。江南春日、柳花飘香、酒肆吴姬，"
            "构成明丽的送别场景。与一般凄苦离歌不同，此诗以豪爽畅饮写别情，"
            "末句以东流水作比，将抽象的“别意”化为可感的江水长度，构思精巧而气势开朗。"
        ),
        "background_en": (
            "A farewell banquet in Jinling. Spring willow fragrance and Wu tavern girls "
            "set a bright scene. Unlike mournful parting poems, this one drinks boldly and "
            "compares parting sorrow to the endless eastward river."
        ),
        "meaning": (
            "前四句写饯别的声色与人情：风、花、酒、人，一片热闹；结句陡然一问，"
            "把酒席上的依依不舍推向哲理高度。流水无穷，别意亦无穷——以问作结，"
            "余味不尽，体现李白送别诗“豪中有深情”的独特气质。"
        ),
        "meaning_en": (
            "Sensory bustle fills the first lines; the final question lifts farewell into "
            "philosophy. Endless water, endless parting—closing with a question leaves the "
            "emotion open, typical of Li Bai’s bold yet deeply felt leave-takings."
        ),
        "keywords": "送别 · 酒肆 · 流水 · 豪情",
    },
    {
        "no": 5,
        "title_zh": "长相思",
        "title_en": "Everlasting Longing (Changxiangsi)",
        "form": "乐府歌行 / Yuefu song",
        "period": "约天宝初年 · 长安时期或此后不久",
        "chinese": (
            "长相思，在长安。\n"
            "络纬秋啼金井阑，微霜凄凄簟色寒。\n"
            "孤灯不明思欲绝，卷帷望月空长叹。\n"
            "美人如花隔云端。\n"
            "上有青冥之长天，下有渌水之波澜。\n"
            "天长路远魂飞苦，梦魂不到关山难。\n"
            "长相思，摧心肝。"
        ),
        "english": (
            "Everlasting longing—far away in Chang’an.\n"
            "Autumn crickets cry by the golden well railing;\n"
            "Thin frost chills the bamboo mat.\n"
            "A lone lamp dims; longing nearly breaks me.\n"
            "I roll up the curtain, gaze at the moon, and sigh in vain.\n"
            "The beauty, flower-like, is barred beyond the clouds.\n"
            "Above: the long blue vault of heaven;\n"
            "Below: clear waters rolling in waves.\n"
            "Heaven is long, the road far—the soul flies in torment;\n"
            "Even in dreams it cannot cross the hard mountain passes.\n"
            "Everlasting longing—it crushes the heart."
        ),
        "background": (
            "李白《长相思》有多首，此为最著名的一篇。传统上或解为男女相思，"
            "或解为政治失意下对君主与理想的向往——“美人”常作比兴，"
            "象征贤君或政治理想。诗写于长安相关语境中，秋夜孤灯、关山难越，"
            "与诗人供奉翰林前后复杂心境相呼应。"
        ),
        "background_en": (
            "The most famous of Li Bai’s Changxiangsi poems. Read as romantic longing or, "
            "allegorically, as yearning for a ruler/ideal (“beauty” as bi-xing symbol). "
            "Autumn night, lone lamp, and impassable passes echo his Chang’an-period unease."
        ),
        "meaning": (
            "开篇点题“在长安”，以秋虫、微霜、孤灯、望月层层渲染凄清；“美人如花隔云端”"
            "将思念对象推至可望而不可即的高度。天长路远、梦魂难到，把空间阻隔与"
            "心理绝望写到极致；首尾“长相思”回环，形成强烈的情感节奏。既是相思曲，"
            "也是政治失意的心灵独白。"
        ),
        "meaning_en": (
            "Autumn insects, frost, a lone lamp, and moonlight build desolation; the "
            "cloud-barred beauty is forever out of reach. Distance defeats even dreams. "
            "The refrain “everlasting longing” frames a song of desire—and of thwarted ambition."
        ),
        "keywords": "相思 · 长安 · 比兴 · 孤夜",
    },
    {
        "no": 6,
        "title_zh": "行路难（其一）",
        "title_en": "Hard Is the Road (I)",
        "form": "乐府歌行 / Yuefu song",
        "period": "天宝三载（744年）前后 · 赐金放还后",
        "chinese": (
            "金樽清酒斗十千，玉盘珍羞直万钱。\n"
            "停杯投箸不能食，拔剑四顾心茫然。\n"
            "欲渡黄河冰塞川，将登太行雪满山。\n"
            "闲来垂钓碧溪上，忽复乘舟梦日边。\n"
            "行路难，行路难，多歧路，今安在？\n"
            "长风破浪会有时，直挂云帆济沧海。"
        ),
        "english": (
            "A golden cup of clear wine, ten thousand a measure;\n"
            "A jade plate of rare delicacies, worth a myriad cash.\n"
            "I set down the cup, throw aside the chopsticks—cannot eat;\n"
            "I draw my sword, look four ways—my heart is lost.\n"
            "I would cross the Yellow River—ice chokes the stream;\n"
            "I would climb the Taihang—snow seals the mountains.\n"
            "At leisure I fish on a jade-green creek;\n"
            "Suddenly again I dream of a boat beside the sun.\n"
            "Hard is the road, hard is the road!\n"
            "Many forked paths—where am I now?\n"
            "There will be a time to ride the wind and cleave the waves;\n"
            "I’ll hoist my cloudlike sail and cross the blue sea."
        ),
        "background": (
            "天宝初，李白供奉翰林，不久因遭谗毁被“赐金放还”，政治理想受挫。"
            "《行路难》三首抒写此时愤懑与自我激励。本篇为第一首，最广为传诵。"
            "“垂钓碧溪”“乘舟梦日”分别用姜尚、伊尹典故，暗示贤才终遇明主的希望。"
        ),
        "background_en": (
            "Around 744, after dismissal from the Hanlin Academy with a “gift of gold,” "
            "Li Bai wrote three Hard Is the Road poems. This first piece is the most famous. "
            "Allusions to Jiang Ziya fishing and Yi Yin dreaming of the sun hint at future favor."
        ),
        "meaning": (
            "先写盛宴难以下咽、拔剑茫然，极言内心失路；黄河冰塞、太行雪满，"
            "象征仕途梗阻。中间转入典故，自我宽慰；结尾“长风破浪会有时”陡然振起，"
            "将悲愤化为对未来的坚定信念。这首诗成为中国文学中“逆境不屈”的经典表达。"
        ),
        "meaning_en": (
            "A feast uneaten and a drawn sword show bewilderment; ice and snow figure "
            "blocked careers. Historical allusions offer hope; the famous close—“ride the "
            "wind and cleave the waves”—turns anguish into defiant faith."
        ),
        "keywords": "失路 · 信念 · 长风破浪 · 政治挫折",
    },
    {
        "no": 7,
        "title_zh": "蜀道难",
        "title_en": "The Road to Shu Is Hard",
        "form": "乐府歌行（杂言） / Irregular yuefu song",
        "period": "约开元末至天宝初 · 送友人入蜀或有所讽喻",
        "chinese": (
            "噫吁嚱，危乎高哉！\n"
            "蜀道之难，难于上青天！\n"
            "蚕丛及鱼凫，开国何茫然！\n"
            "尔来四万八千岁，不与秦塞通人烟。\n"
            "西当太白有鸟道，可以横绝峨眉巅。\n"
            "地崩山摧壮士死，然后天梯石栈相钩连。\n"
            "……\n"
            "连峰去天不盈尺，枯松倒挂倚绝壁。\n"
            "飞湍瀑流争喧豗，砯崖转石万壑雷。\n"
            "其险也如此，嗟尔远道之人胡为乎来哉！\n"
            "……\n"
            "蜀道之难，难于上青天，侧身西望长咨嗟！"
        ),
        "english": (
            "Yi! Xu! Xi! How perilous, how high!\n"
            "The road to Shu is harder than climbing the blue sky!\n"
            "Cancong and Yufu—how remote their founding!\n"
            "Forty-eight thousand years since then,\n"
            "No traffic passed between Qin and Shu.\n"
            "West of Taibai only a bird-path\n"
            "Could cross to Emei’s peak.\n"
            "Earth split, mountains fell, heroes died—\n"
            "Then sky-ladders and stone galleries linked the way.\n"
            "…\n"
            "Linked peaks leave less than a foot to heaven;\n"
            "Withered pines hang upside-down from cliffs.\n"
            "Flying torrents and cataracts roar in rivalry;\n"
            "Boulders crash—thunder in ten thousand gullies.\n"
            "Such is the danger—why, traveler from afar, have you come?\n"
            "…\n"
            "The road to Shu is harder than climbing the blue sky;\n"
            "I turn west and heave a long sigh!"
        ),
        "note_zh": "全文较长，PPT中另附完整原文页；此处为结构精选。",
        "full_chinese": (
            "噫吁嚱，危乎高哉！蜀道之难，难于上青天！\n"
            "蚕丛及鱼凫，开国何茫然！尔来四万八千岁，不与秦塞通人烟。\n"
            "西当太白有鸟道，可以横绝峨眉巅。地崩山摧壮士死，然后天梯石栈相钩连。\n"
            "上有六龙回日之高标，下有冲波逆折之回川。黄鹤之飞尚不得过，猿猱欲度愁攀援。\n"
            "青泥何盘盘，百步九折萦岩峦。扪参历井仰胁息，以手抚膺坐长叹。\n"
            "问君西游何时还？畏途巉岩不可攀。但见悲鸟号古木，雄飞雌从绕林间。\n"
            "又闻子规啼夜月，愁空山。蜀道之难，难于上青天，使人听此凋朱颜！\n"
            "连峰去天不盈尺，枯松倒挂倚绝壁。飞湍瀑流争喧豗，砯崖转石万壑雷。\n"
            "其险也如此，嗟尔远道之人胡为乎来哉！\n"
            "剑阁峥嵘而崔嵬，一夫当关，万夫莫开。所守或匪亲，化为狼与豺。\n"
            "朝避猛虎，夕避长蛇，磨牙吮血，杀人如麻。锦城虽云乐，不如早还家。\n"
            "蜀道之难，难于上青天，侧身西望长咨嗟！"
        ),
        "full_english": (
            "Yi! Xu! Xi! How perilous, how high! The road to Shu is harder than climbing the blue sky!\n"
            "Cancong and Yufu—how remote their founding! For forty-eight thousand years, Qin and Shu shared no traffic.\n"
            "West of Taibai only a bird-path could cross to Emei’s peak. Earth split, mountains fell, heroes died—then sky-ladders and stone galleries linked the way.\n"
            "Above: a peak so high the six dragons of the sun turn back; below: swirling rivers that reverse their course. Even yellow cranes cannot fly over; gibbons fret at the climb.\n"
            "How winding is Qingni Pass—a hundred steps, nine bends around the ridges. Touching the stars, one gasps; hand on breast, one sits and sighs.\n"
            "Friend, when will you return from the west? The dread road’s cliffs cannot be scaled. Only mournful birds cry in ancient trees; male and female wheel through the woods.\n"
            "Again the cuckoo weeps under the night moon, grieving in empty mountains. The road to Shu is harder than the sky—hearing this, one’s rosy cheeks fade!\n"
            "Peaks leave less than a foot to heaven; withered pines hang from cliffs. Torrents roar; boulders thunder in ten thousand gullies.\n"
            "Such danger—why, traveler, have you come so far?\n"
            "Jianmen Tower looms steep: one man holds the pass, ten thousand cannot open it. If the guard be not loyal, he turns wolf and jackal.\n"
            "By day flee tigers, by night long snakes—they grind teeth, suck blood, kill like hemp. Though Brocade City is said to be joyous, better return home early.\n"
            "The road to Shu is harder than climbing the blue sky; I turn west and heave a long sigh!"
        ),
        "background": (
            "《蜀道难》为李白代表作，贺知章读后叹为“谪仙人”。诗用乐府旧题，"
            "极写秦蜀栈道之险。关于主旨，历代有多种说法：送友人入蜀告诫、"
            "讽喻蜀地形胜易生割据、或纯以山川雄奇骋才。无论何解，其艺术成就"
            "在于将地理险阻写成震撼人心的音乐化长篇。"
        ),
        "background_en": (
            "A signature masterpiece; He Zhizhang called Li Bai a “banished immortal” after "
            "reading it. Readings vary: warning a friend entering Shu, political allegory about "
            "strategic terrain, or pure landscape virtuosity. Its power lies in turning geography "
            "into thunderous, musical verse."
        ),
        "meaning": (
            "以“难于上青天”为主旋律三次反复，穿插神话、历史、鸟兽、山水与政治隐忧，"
            "句式长短错落，情绪大起大落。它不仅写蜀道，更写人生之路的艰危，以及"
            "诗人面对绝境时的惊叹、忧虑与豪迈才情。是盛唐浪漫主义诗歌的高峰之一。"
        ),
        "meaning_en": (
            "The refrain “harder than the blue sky” returns three times, mixing myth, history, "
            "beasts, landscape, and political unease. Irregular lines surge and crash. Beyond "
            "Shu’s roads, it figures life’s perils—and Li Bai’s awe, alarm, and genius."
        ),
        "keywords": "奇险 · 乐府 · 反复咏叹 · 谪仙",
    },
    {
        "no": 8,
        "title_zh": "将进酒",
        "title_en": "Bring in the Wine",
        "form": "乐府歌行 / Yuefu song",
        "period": "约天宝年间 · 与友人岑勋、元丹丘宴饮时",
        "chinese": (
            "君不见黄河之水天上来，奔流到海不复回。\n"
            "君不见高堂明镜悲白发，朝如青丝暮成雪。\n"
            "人生得意须尽欢，莫使金樽空对月。\n"
            "天生我材必有用，千金散尽还复来。\n"
            "烹羊宰牛且为乐，会须一饮三百杯。\n"
            "岑夫子，丹丘生，将进酒，杯莫停。\n"
            "与君歌一曲，请君为我倾耳听。\n"
            "钟鼓馔玉不足贵，但愿长醉不复醒。\n"
            "古来圣贤皆寂寞，惟有饮者留其名。\n"
            "陈王昔时宴平乐，斗酒十千恣欢谑。\n"
            "主人何为言少钱，径须沽取对君酌。\n"
            "五花马，千金裘，呼儿将出换美酒，与尔同销万古愁。"
        ),
        "english": (
            "Have you not seen the Yellow River’s waters come from Heaven,\n"
            "Rushing to the sea, never to return?\n"
            "Have you not seen, in bright mirrors of high halls, grieving over white hair—\n"
            "At dawn like black silk, by evening turned to snow?\n"
            "When life is glad, we must drain our joy;\n"
            "Never let the golden cup face the moon in vain.\n"
            "Heaven made me—my talent must be of use;\n"
            "A thousand gold pieces spent will come again.\n"
            "Cook the lamb, butcher the ox—let us make merry;\n"
            "We must drink three hundred cups at one sitting.\n"
            "Master Cen, Danqiu my friend—bring in the wine, don’t set the cups down!\n"
            "I sing you a song; lend me your ear.\n"
            "Bells, drums, and jade delicacies are not worth treasure;\n"
            "I only wish to stay forever drunk and never wake.\n"
            "Sages of old have all been lonely;\n"
            "Only the drinkers left their names.\n"
            "Prince Chen once feasted at Pingle,\n"
            "Ten thousand a dipper, wild in joy and jest.\n"
            "Host, why speak of little money?\n"
            "Just buy wine and drink with you.\n"
            "Piebaald horse, fur coat worth a thousand gold—\n"
            "Call the boy to take them out and trade for fine wine,\n"
            "And with you I’ll melt ten thousand ages of sorrow."
        ),
        "background": (
            "约作于李白离开长安后与友人欢宴之时。表面劝酒狂欢，实则糅合时光易逝、"
            "怀才不遇与及时行乐的复杂情感。诗中点名岑夫子（岑勋）、丹丘生（元丹丘），"
            "是真实友朋宴席上的放歌。其豪放基调与深层忧愁并存，最能代表李白的人格与诗风。"
        ),
        "background_en": (
            "Likely from a banquet with friends Cen Xun and Yuan Danqiu after leaving Chang’an. "
            "On the surface a drinking song; underneath, time’s flight, unused talent, and carpe "
            "diem. Bold joy and deep sorrow together define Li Bai’s persona."
        ),
        "meaning": (
            "开篇两个“君不见”以黄河与白发写出时间的不可逆；随即转向纵酒豪饮，"
            "“天生我材必有用”是自信的宣言，也是对命运的反拨。后半以古来圣贤寂寞、"
            "饮者留名自解，最终愿以名马狐裘换酒，同销万古愁。狂欢是外壳，"
            "愁与傲是内核——这正是此诗千古动人的原因。"
        ),
        "meaning_en": (
            "Twin “Have you not seen” openings fix irreversible time; then comes defiant "
            "drinking—“Heaven made my talent; it must be of use.” Lonely sages versus "
            "famed drinkers, and trading horse and fur for wine, melt “ten thousand ages of "
            "sorrow.” Revelry is the shell; pride and grief are the core."
        ),
        "keywords": "纵酒 · 自信 · 时光 · 万古愁",
    },
    {
        "no": 9,
        "title_zh": "清平调（三首）",
        "title_en": "Qingping Tunes (Three Lyrics)",
        "form": "七言绝句组诗 / Three seven-character quatrains",
        "period": "天宝二年左右（约743年） · 供奉翰林、沉香亭赏牡丹时",
        "chinese": (
            "其一\n"
            "云想衣裳花想容，春风拂槛露华浓。\n"
            "若非群玉山头见，会向瑶台月下逢。\n"
            "\n"
            "其二\n"
            "一枝红艳露凝香，云雨巫山枉断肠。\n"
            "借问汉宫谁得似，可怜飞燕倚新妆。\n"
            "\n"
            "其三\n"
            "名花倾国两相欢，长得君王带笑看。\n"
            "解释春风无限恨，沉香亭北倚阑干。"
        ),
        "english": (
            "I\n"
            "Clouds call to mind her robes, flowers her face;\n"
            "Spring wind brushes the rail—dew’s glow is rich.\n"
            "If not glimpsed on Group Jade Mountain’s peak,\n"
            "She must be met on Jasper Terrace beneath the moon.\n"
            "\n"
            "II\n"
            "One spray of red beauty, dew-thick with fragrance;\n"
            "Wu Mountain’s cloud-and-rain romance grieves in vain.\n"
            "Ask—who in the Han palace could compare?\n"
            "Poor Flying Swallow leans on her new makeup.\n"
            "\n"
            "III\n"
            "Famous flower and peerless beauty delight each other;\n"
            "Always they win the sovereign’s smiling gaze.\n"
            "To dissolve spring wind’s endless regret,\n"
            "North of Aloes Pavilion she leans on the railing."
        ),
        "background": (
            "据记载，唐玄宗与杨贵妃在兴庆宫沉香亭赏牡丹，命李白作新词，"
            "李白醉中成《清平调》三首，由李龟年演唱。诗以花喻人，咏牡丹兼咏贵妃，"
            "辞采华美，是李白宫廷应制之作的巅峰。后人或谓其二以赵飞燕作比有讽意，"
            "亦有人认为纯属颂美。无论何种解读，三诗皆体现李白才思敏捷与意象之清丽。"
        ),
        "background_en": (
            "At Aloes Pavilion in Xingqing Palace, Xuanzong and Yang Guifei viewed peonies; "
            "Li Bai, reportedly tipsy, wrote three Qingping lyrics for Li Guinian to sing. "
            "Flower and beauty mirror each other. Later readers debate praise versus veiled "
            "irony (Zhao Feiyan); the craft remains exquisite court poetry."
        ),
        "meaning": (
            "第一首以云、花、仙山写贵妃之绝世风姿；第二首以红艳凝香压倒巫山云雨、"
            "汉宫飞燕，极尽推崇；第三首点明“名花倾国”同承君恩，收于沉香亭北倚阑之景。"
            "花与人、仙与凡、颂与美交织，形成盛唐宫廷美学的诗意瞬间。"
        ),
        "meaning_en": (
            "I: clouds, flowers, and immortal mountains sketch peerless grace. II: peony "
            "fragrance outshines mythic romance and Han beauty Zhao Feiyan. III: flower and "
            "“ruinous beauty” share the emperor’s smile at Aloes Pavilion—a crystal of High Tang "
            "court aesthetics."
        ),
        "keywords": "牡丹 · 贵妃 · 宫廷 · 花人合一",
    },
    {
        "no": 10,
        "title_zh": "梦游天姥吟留别",
        "title_en": "Dream Journey to Tianmu: A Farewell Song",
        "form": "杂言歌行 / Irregular song-poem",
        "period": "天宝四载（745年） · 将离东鲁南下吴越时",
        "chinese": (
            "海客谈瀛洲，烟涛微茫信难求；\n"
            "越人语天姥，云霞明灭或可睹。\n"
            "天姥连天向天横，势拔五岳掩赤城。\n"
            "……\n"
            "霓为衣兮风为马，云之君兮纷纷而来下。\n"
            "虎鼓瑟兮鸾回车，仙之人兮列如麻。\n"
            "忽魂悸以魄动，恍惊起而长嗟。\n"
            "惟觉时之枕席，失向来之烟霞。\n"
            "世间行乐亦如此，古来万事东流水。\n"
            "……\n"
            "安能摧眉折腰事权贵，使我不得开心颜！"
        ),
        "note_zh": "全文较长，PPT中另附完整原文页；此处为结构精选。",
        "full_chinese": (
            "海客谈瀛洲，烟涛微茫信难求；越人语天姥，云霞明灭或可睹。\n"
            "天姥连天向天横，势拔五岳掩赤城。天台四万八千丈，对此欲倒东南倾。\n"
            "我欲因之梦吴越，一夜飞度镜湖月。湖月照我影，送我至剡溪。\n"
            "谢公宿处今尚在，渌水荡漾清猿啼。脚著谢公屐，身登青云梯。\n"
            "半壁见海日，空中闻天鸡。千岩万转路不定，迷花倚石忽已暝。\n"
            "熊咆龙吟殷岩泉，栗深林兮惊层巅。云青青兮欲雨，水澹澹兮生烟。\n"
            "列缺霹雳，丘峦崩摧。洞天石扉，訇然中开。\n"
            "青冥浩荡不见底，日月照耀金银台。霓为衣兮风为马，云之君兮纷纷而来下。\n"
            "虎鼓瑟兮鸾回车，仙之人兮列如麻。忽魂悸以魄动，恍惊起而长嗟。\n"
            "惟觉时之枕席，失向来之烟霞。世间行乐亦如此，古来万事东流水。\n"
            "别君去兮何时还？且放白鹿青崖间，须行即骑访名山。\n"
            "安能摧眉折腰事权贵，使我不得开心颜！"
        ),
        "full_english": (
            "Seafarers speak of Yingzhou—misty waves, hard to seek; Yue folk tell of Tianmu—clouds that may be glimpsed.\n"
            "Tianmu stretches across the sky, towering over the Five Peaks, eclipsing Red Wall. Tiantai’s forty-eight thousand zhang would topple southeast before it.\n"
            "I would dream my way to Wu-Yue—one night I fly across Mirror Lake’s moon. The lake moon lights my shadow to Shan Stream.\n"
            "Xie’s lodging still remains; clear water ripples, gibbons cry. In Xie’s clogs I climb the cloud ladder.\n"
            "Halfway up I see the sea sun; in midair I hear the heavenly cock. A thousand cliffs, ten thousand turns—lost among flowers, evening falls.\n"
            "Bears roar, dragons chant through rocky springs; deep woods tremble, layered peaks startle. Clouds darken toward rain; waters grow mist.\n"
            "Lightning splits; hills collapse. Stone doors of the grotto-heaven boom open.\n"
            "Blue void without bottom; sun and moon light gold-and-silver terraces. Rainbows for robes, wind for horses—Cloud Lords descend in throngs.\n"
            "Tigers drum zithers, phoenixes turn carriages; immortals stand thick as hemp. Suddenly the soul shudders—I start awake with a long sigh.\n"
            "Only pillow and mat remain; the mists are gone. Worldly joys are like this; since old times all things flow east.\n"
            "When shall I return after leaving you? I’ll free a white deer on green cliffs, and when I go, ride it to famous mountains.\n"
            "How can I bow and scrape to the powerful, and not keep an open, joyful face!"
        ),
        "english": (
            "Seafarers speak of Yingzhou—misty waves, hard to seek;\n"
            "Yue folk tell of Tianmu—clouds that may be glimpsed.\n"
            "Tianmu stretches across the sky,\n"
            "Towering over the Five Peaks, eclipsing Red Wall.\n"
            "…\n"
            "Rainbows for robes, wind for horses—\n"
            "Cloud Lords descend in throngs.\n"
            "Tigers drum zithers, phoenixes turn carriages;\n"
            "Immortals stand thick as hemp.\n"
            "Suddenly the soul shudders—I start awake with a long sigh.\n"
            "Only pillow and mat remain; the mists are gone.\n"
            "Worldly joys are like this; since old times all things flow east.\n"
            "…\n"
            "How can I bow and scrape to the powerful,\n"
            "And not keep an open, joyful face!"
        ),
        "background": (
            "李白被赐金放还后，在东鲁一带盘桓，天宝四载准备南下吴越，"
            "以此诗向友人告别。全篇以梦游天姥山为核心，将山水、游仙与政治态度熔于一炉。"
            "末句“安能摧眉折腰事权贵”是诗人傲岸人格的最强宣言，也是理解其离开长安后心境的钥匙。"
        ),
        "background_en": (
            "After leaving court, while preparing to leave eastern Lu for Wu-Yue (745), "
            "Li Bai wrote this farewell. A dream journey to Mount Tianmu fuses landscape, "
            "immortal fantasy, and politics. The final refusal to bow to the powerful is his "
            "clearest statement of independence."
        ),
        "meaning": (
            "诗分三段：向往天姥—梦入仙境—梦醒抒怀。仙境越绚烂，梦醒越虚空，"
            "从而引出“世间行乐亦如此”的觉悟；最终以访名山、拒权贵收束，完成从幻境到"
            "人格抉择的升华。浪漫想象服务于现实态度，是李白“诗与人合一”的典范。"
        ),
        "meaning_en": (
            "Three movements: longing for Tianmu, dream paradise, waking reflection. The "
            "brighter the immortal scene, the emptier the waking—hence “worldly joys are like "
            "this.” Visiting mountains and rejecting power complete the arc from fantasy to "
            "moral choice."
        ),
        "keywords": "梦游 · 游仙 · 傲骨 · 留别",
    },
    {
        "no": 11,
        "title_zh": "早发白帝城",
        "title_en": "Departing Baidi City at Dawn",
        "form": "七言绝句 / Seven-character quatrain",
        "period": "乾元二年（759年） · 流放夜郎途中遇赦东归",
        "chinese": (
            "朝辞白帝彩云间，千里江陵一日还。\n"
            "两岸猿声啼不住，轻舟已过万重山。"
        ),
        "english": (
            "At dawn I leave Baidi among colored clouds;\n"
            "A thousand li to Jiangling—back in a single day.\n"
            "From both banks, gibbons cry without pause;\n"
            "My light boat has already passed ten thousand folded mountains."
        ),
        "background": (
            "安史之乱后，李白因永王李璘事件获罪，被流放夜郎。行至白帝城（今重庆奉节）"
            "附近时遇大赦，遂放舟东下江陵。历经死地而重生，心情无比畅快，"
            "于是写下这首千古传诵的七绝。诗中的“快”，既是船行之快，更是心情之快。"
        ),
        "background_en": (
            "After the An Lushan Rebellion, Li Bai was exiled to Yelang for involvement with "
            "Prince Yong. Near Baidi City he received a pardon and raced downriver toward "
            "Jiangling. Speed of boat and of relieved spirit fuse in this famous quatrain."
        ),
        "meaning": (
            "首句写白帝之高、晨云之丽；次句以“千里”“一日”的时空压缩写江流迅疾；"
            "三四句以猿声未绝、轻舟已过的对比，把听觉的绵延与空间的飞跃叠合。"
            "全诗明快跳脱，是绝境逢生后的精神解放之歌，也是李白晚年诗风明朗一面的代表。"
        ),
        "meaning_en": (
            "Height and colored dawn; then “a thousand li in one day” compresses space-time. "
            "Gibbons still cry as the boat has already cleared countless ranges—lingering sound "
            "against flashing distance. A song of release after near-ruin."
        ),
        "keywords": "遇赦 · 轻舟 · 迅疾 · 欢畅",
    },
    {
        "no": 12,
        "title_zh": "庐山谣寄卢侍御虚舟",
        "title_en": "Ballad of Mount Lu, Sent to Censor Lu Xuzhou",
        "form": "杂言歌行 / Irregular song-poem",
        "period": "上元元年（760年）左右 · 晚年游庐山时",
        "chinese": (
            "我本楚狂人，凤歌笑孔丘。\n"
            "手持绿玉杖，朝别黄鹤楼。\n"
            "五岳寻仙不辞远，一生好入名山游。\n"
            "庐山秀出南斗旁，屏风九叠云锦张。\n"
            "……\n"
            "早服还丹无世情，琴心三叠道初成。\n"
            "遥见仙人彩云里，手把芙蓉朝玉京。\n"
            "先期汗漫九垓上，愿接卢敖游太清。"
        ),
        "note_zh": "全文较长，PPT中另附完整原文页；此处为结构精选。",
        "full_chinese": (
            "我本楚狂人，凤歌笑孔丘。手持绿玉杖，朝别黄鹤楼。\n"
            "五岳寻仙不辞远，一生好入名山游。庐山秀出南斗旁，屏风九叠云锦张。\n"
            "影落明湖青黛光，金阙前开二峰长，银河倒挂三石梁。\n"
            "香炉瀑布遥相望，回崖沓嶂凌苍苍。翠影红霞映朝日，鸟飞不到吴天长。\n"
            "登高壮观天地间，大江茫茫去不还。黄云万里动风色，白波九道流雪山。\n"
            "好为庐山谣，兴因庐山发。闲窥石镜清我心，谢公行处苍苔没。\n"
            "早服还丹无世情，琴心三叠道初成。遥见仙人彩云里，手把芙蓉朝玉京。\n"
            "先期汗漫九垓上，愿接卢敖游太清。"
        ),
        "full_english": (
            "I am the Madman of Chu, singing of the phoenix, laughing at Confucius. Green jade staff in hand, at dawn I leave Yellow Crane Tower.\n"
            "I seek immortals among the Five Peaks, never minding distance; all my life I love roaming famous mountains. Mount Lu rises fine beside the Southern Dipper; nine-fold screen cliffs unfurl like brocade clouds.\n"
            "Shadows fall on the bright lake in blue-black light; golden towers open before twin long peaks; the Milky Way hangs inverted on Three Stone Bridges.\n"
            "Incense Burner Falls face each other afar; circling cliffs and layered ridges pierce the gray-blue. Green shadows and red mist mirror the morning sun; birds cannot reach the long Wu sky.\n"
            "Climbing high, I survey heaven and earth: the Great River rolls away and does not return. Yellow clouds for ten thousand li stir the wind’s color; white waves in nine channels flow like snowy mountains.\n"
            "Gladly I make a ballad of Lu; inspiration rises from Lu. Idly I peer into the Stone Mirror and clear my heart; where Xie once walked, green moss has buried the path.\n"
            "Early I take the returned elixir, free of worldly feeling; with triple-layered qin-heart, the Way begins to form. Far off I see immortals in colored clouds, lotus in hand, toward the Jade Capital.\n"
            "I have an appointment with the Boundless above the Nine Regions; I wish to meet Lu Ao and roam the Great Purity."
        ),
        "english": (
            "I am the Madman of Chu,\n"
            "Singing of the phoenix, laughing at Confucius.\n"
            "Green jade staff in hand,\n"
            "At dawn I leave Yellow Crane Tower.\n"
            "I seek immortals among the Five Peaks, never minding distance;\n"
            "All my life I love roaming famous mountains.\n"
            "Mount Lu rises fine beside the Southern Dipper;\n"
            "Nine-fold screen cliffs unfurl like brocade clouds.\n"
            "…\n"
            "Early I take the returned elixir, free of worldly feeling;\n"
            "With triple-layered qin-heart, the Way begins to form.\n"
            "Far off I see immortals in colored clouds,\n"
            "Lotus in hand, toward the Jade Capital.\n"
            "I have an appointment with the Boundless above the Nine Regions;\n"
            "I wish to meet Lu Ao and roam the Great Purity."
        ),
        "background": (
            "李白晚年遇赦后继续漫游，上元前后登庐山，将此谣寄给侍御史卢虚舟。"
            "诗中自称“楚狂人”，用陆通凤歌笑孔子的典故，表明疏离礼法、追求自由与求仙的态度。"
            "庐山的屏风叠、香炉瀑布、石镜等实景与游仙想象交织，是晚年精神世界的集中呈现。"
        ),
        "background_en": (
            "In late life, after pardon, Li Bai climbed Mount Lu and sent this ballad to Censor "
            "Lu Xuzhou. Calling himself the “Madman of Chu,” he invokes the phoenix-song that "
            "mocked Confucius—freedom and immortality over ritual. Real Lu scenery blends with "
            "Daoist vision."
        ),
        "meaning": (
            "开篇即以狂者自居，奠定傲视权贵与礼教的基调；中间以浓墨重彩铺写庐山壮观，"
            "“登高壮观天地间”一节气象万千；结尾转入服丹求仙、愿接卢敖游太清，"
            "把对友人的寄赠升为同游仙境的邀约。山水之美、人格之狂、仙道之思三者合一，"
            "是李白晚年的精神自画像。"
        ),
        "meaning_en": (
            "The madman persona rejects rigid orthodoxy; the middle paints Lu’s grandeur—“survey "
            "heaven and earth”—in sweeping strokes; the close invites Lu Xuzhou into a Daoist "
            "ascent. Landscape, defiance, and immortality form Li Bai’s late self-portrait."
        ),
        "keywords": "庐山 · 楚狂 · 求仙 · 晚年",
    },
]


def cover_slide(prs, total):
    slide = blank_slide(prs)
    paint_bg(slide, INK)
    add_rect(slide, 0, 0, Inches(0.35), SLIDE_H, JADE)
    add_rect(slide, Inches(12.98), 0, Inches(0.35), SLIDE_H, GOLD)
    add_textbox(
        slide, Inches(1.2), Inches(1.6), Inches(10.5), Inches(0.5),
        "盛唐浪漫 · 诗仙李白",
        size=18, color=GOLD, align=PP_ALIGN.LEFT, bold=True
    )
    add_textbox(
        slide, Inches(1.2), Inches(2.2), Inches(11), Inches(1.2),
        "李白十二名篇精讲",
        size=44, color=WHITE, align=PP_ALIGN.LEFT, bold=True
    )
    add_textbox(
        slide, Inches(1.2), Inches(3.4), Inches(11), Inches(0.6),
        "Twelve Masterpieces of Li Bai — Chinese & English, Context & Meaning",
        size=18, color=PAPER_DARK, align=PP_ALIGN.LEFT, italic=True
    )
    add_accent_bar(slide, Inches(1.2), Inches(4.2), Inches(2.5), Inches(0.06), JADE_LIGHT)
    add_textbox(
        slide, Inches(1.2), Inches(4.5), Inches(10), Inches(1.2),
        "含：峨眉山月歌 · 渡荆门送别 · 长干行 · 金陵酒肆留别\n"
        "长相思 · 行路难 · 蜀道难 · 将进酒 · 清平调\n"
        "梦游天姥吟留别 · 早发白帝城 · 庐山谣寄卢侍御虚舟",
        size=14, color=PAPER, align=PP_ALIGN.LEFT
    )
    add_textbox(
        slide, Inches(1.2), Inches(6.5), Inches(10), Inches(0.4),
        "中英对照 · 创作背景 · 诗文意义 · 长版演示文稿",
        size=12, color=MUTED, align=PP_ALIGN.LEFT
    )


def toc_slides(prs, total, start_page):
    """Two TOC slides."""
    half = (len(POEMS) + 1) // 2
    for part, poems in enumerate([POEMS[:half], POEMS[half:]]):
        slide = blank_slide(prs)
        paint_bg(slide, PAPER)
        add_rect(slide, 0, 0, SLIDE_W, Inches(0.9), INK)
        add_textbox(
            slide, Inches(0.6), Inches(0.25), Inches(12), Inches(0.5),
            f"目录 Contents（{part + 1}/2）",
            size=24, color=WHITE, bold=True
        )
        y = 1.2
        for p in poems:
            add_textbox(
                slide, Inches(0.8), Inches(y), Inches(11.5), Inches(0.45),
                f"{p['no']:02d}  {p['title_zh']}    {p['title_en']}",
                size=16, color=INK
            )
            add_textbox(
                slide, Inches(1.2), Inches(y + 0.32), Inches(11), Inches(0.3),
                f"{p['form']}  ·  {p['period']}",
                size=11, color=MUTED
            )
            y += 0.85
        footer(slide, start_page + part, total)


def intro_slide(prs, page, total):
    slide = blank_slide(prs)
    paint_bg(slide, PAPER)
    add_rect(slide, 0, 0, SLIDE_W, Inches(0.9), INK)
    add_textbox(
        slide, Inches(0.6), Inches(0.25), Inches(12), Inches(0.5),
        "诗人简介 · About Li Bai",
        size=24, color=WHITE, bold=True
    )
    add_textbox(
        slide, Inches(0.7), Inches(1.2), Inches(12), Inches(5.5),
        "李白（701—762），字太白，号青莲居士，盛唐浪漫主义诗歌的巅峰代表，后人尊为“诗仙”。\n"
        "早年出蜀漫游，天宝初供奉翰林，不久赐金放还；安史乱中因永王事流放夜郎，中途遇赦。\n"
        "其诗想象瑰奇、情感奔放、语言清雄，尤擅乐府歌行与绝句。\n\n"
        "Li Bai (701–762), courtesy name Taibai, the “Poet Immortal,” stands at the summit of\n"
        "High Tang romantic poetry. He left Shu young, briefly served at court, then wandered;\n"
        "after exile and pardon late in life, his verse remained bold in vision and music.\n\n"
        "本演示文稿按大致创作时间，精讲十二首名篇：每篇含原文、英译、创作背景与诗文意义。\n"
        "This deck presents twelve masterpieces in roughly chronological order, each with\n"
        "Chinese text, English translation, historical context, and interpretive meaning.",
        size=15, color=INK_SOFT
    )
    footer(slide, page, total)


def section_divider(prs, poem, page, total):
    slide = blank_slide(prs)
    paint_bg(slide, INK)
    add_rect(slide, 0, 0, Inches(0.3), SLIDE_H, JADE)
    add_textbox(
        slide, Inches(1.2), Inches(2.0), Inches(10), Inches(0.4),
        f"第 {poem['no']} 篇  /  Poem {poem['no']}",
        size=16, color=GOLD, bold=True
    )
    add_textbox(
        slide, Inches(1.2), Inches(2.6), Inches(11), Inches(0.9),
        f"《{poem['title_zh']}》",
        size=40, color=WHITE, bold=True
    )
    add_textbox(
        slide, Inches(1.2), Inches(3.6), Inches(11), Inches(0.5),
        poem["title_en"],
        size=20, color=PAPER_DARK, italic=True
    )
    add_accent_bar(slide, Inches(1.2), Inches(4.3), Inches(2.2), Inches(0.06), JADE_LIGHT)
    add_textbox(
        slide, Inches(1.2), Inches(4.6), Inches(11), Inches(0.8),
        f"{poem['form']}\n{poem['period']}\n关键词 Keywords：{poem['keywords']}",
        size=14, color=PAPER
    )
    footer(slide, page, total, title=poem["title_zh"])


def content_header(slide, title):
    add_rect(slide, 0, 0, SLIDE_W, Inches(0.75), INK)
    add_textbox(
        slide, Inches(0.5), Inches(0.18), Inches(12.3), Inches(0.45),
        title, size=20, color=WHITE, bold=True
    )


def chinese_slide(prs, poem, page, total, text=None, subtitle="原文 Original Chinese"):
    slide = blank_slide(prs)
    paint_bg(slide, PAPER)
    content_header(slide, f"《{poem['title_zh']}》 · {subtitle}")
    body = text if text is not None else poem["chinese"]
    # Choose size based on length
    lines = body.count("\n") + 1
    size = 18 if lines <= 10 else (15 if lines <= 16 else 13)
    add_textbox(
        slide, Inches(0.7), Inches(1.1), Inches(12), Inches(5.6),
        body, size=size, color=INK, align=PP_ALIGN.LEFT
    )
    footer(slide, page, total, title=poem["title_zh"])


def english_slide(prs, poem, page, total, text=None, subtitle="英译 English Translation"):
    slide = blank_slide(prs)
    paint_bg(slide, PAPER)
    content_header(slide, f"{poem['title_en']} · {subtitle}")
    body = text if text is not None else poem["english"]
    lines = body.count("\n") + 1
    size = 16 if lines <= 12 else (13 if lines <= 20 else 12)
    add_textbox(
        slide, Inches(0.7), Inches(1.1), Inches(12), Inches(5.6),
        body, size=size, color=INK_SOFT, align=PP_ALIGN.LEFT, italic=False
    )
    footer(slide, page, total, title=poem["title_zh"])


def bilingual_compact(prs, poem, page, total):
    """Side-by-side for short poems."""
    slide = blank_slide(prs)
    paint_bg(slide, PAPER)
    content_header(slide, f"《{poem['title_zh']}》 · 中英对照 Bilingual")
    add_rect(slide, Inches(0.5), Inches(1.0), Inches(5.9), Inches(5.5), PAPER_DARK)
    add_rect(slide, Inches(6.9), Inches(1.0), Inches(5.9), Inches(5.5), RgbColor(0xEE, 0xF4, 0xF3))
    add_textbox(
        slide, Inches(0.7), Inches(1.15), Inches(5.5), Inches(0.35),
        "中文", size=12, color=JADE, bold=True
    )
    add_textbox(
        slide, Inches(7.1), Inches(1.15), Inches(5.5), Inches(0.35),
        "English", size=12, color=JADE, bold=True
    )
    zh_size = 14 if poem["chinese"].count("\n") > 8 else 16
    en_size = 12 if poem["english"].count("\n") > 10 else 13
    add_textbox(
        slide, Inches(0.7), Inches(1.55), Inches(5.5), Inches(4.8),
        poem["chinese"], size=zh_size, color=INK
    )
    add_textbox(
        slide, Inches(7.1), Inches(1.55), Inches(5.5), Inches(4.8),
        poem["english"], size=en_size, color=INK_SOFT
    )
    footer(slide, page, total, title=poem["title_zh"])


def bg_meaning_slide(prs, poem, page, total, kind="background"):
    slide = blank_slide(prs)
    paint_bg(slide, PAPER)
    if kind == "background":
        title = f"《{poem['title_zh']}》 · 创作背景 Context"
        zh = poem["background"]
        en = poem["background_en"]
    else:
        title = f"《{poem['title_zh']}》 · 诗文意义 Meaning"
        zh = poem["meaning"]
        en = poem["meaning_en"]
    content_header(slide, title)
    add_accent_bar(slide, Inches(0.6), Inches(1.0), Inches(1.5), Inches(0.05), JADE)
    add_textbox(
        slide, Inches(0.6), Inches(1.2), Inches(12.1), Inches(2.6),
        zh, size=15, color=INK
    )
    add_textbox(
        slide, Inches(0.6), Inches(4.0), Inches(12.1), Inches(2.6),
        en, size=13, color=INK_SOFT, italic=True
    )
    footer(slide, page, total, title=poem["title_zh"])


def timeline_slide(prs, page, total):
    slide = blank_slide(prs)
    paint_bg(slide, PAPER)
    content_header(slide, "创作年表略图 · Approximate Timeline")
    items = [
        ("约725", "峨眉山月歌", "出蜀之初"),
        ("约726", "渡荆门送别 / 金陵酒肆留别", "东游楚吴"),
        ("开天之际", "长干行 / 蜀道难", "漫游与乐府高峰"),
        ("约743", "清平调", "翰林供奉"),
        ("约744", "行路难 / 长相思", "赐金放还前后"),
        ("745", "梦游天姥吟留别", "离鲁南下"),
        ("759", "早发白帝城", "遇赦东归"),
        ("约760", "庐山谣", "晚年庐山"),
    ]
    y = 1.1
    for year, titles, note in items:
        add_rect(slide, Inches(0.6), Inches(y), Inches(1.8), Inches(0.55), JADE)
        add_textbox(
            slide, Inches(0.65), Inches(y + 0.08), Inches(1.7), Inches(0.4),
            year, size=12, color=WHITE, bold=True, align=PP_ALIGN.CENTER
        )
        add_textbox(
            slide, Inches(2.6), Inches(y + 0.02), Inches(7), Inches(0.3),
            titles, size=14, color=INK, bold=True
        )
        add_textbox(
            slide, Inches(2.6), Inches(y + 0.28), Inches(7), Inches(0.25),
            note, size=11, color=MUTED
        )
        y += 0.7
    footer(slide, page, total)


def themes_slide(prs, page, total):
    slide = blank_slide(prs)
    paint_bg(slide, PAPER)
    content_header(slide, "主题脉络 · Thematic Threads")
    themes = [
        ("乡恋与壮游", "Homeland & Roaming", "峨眉山月歌、渡荆门送别"),
        ("儿女深情", "Love & Longing", "长干行、长相思"),
        ("送别豪情", "Farewell & Wine", "金陵酒肆留别、将进酒"),
        ("失路与傲骨", "Setback & Pride", "行路难、梦游天姥"),
        ("奇境长歌", "Visionary Songs", "蜀道难、庐山谣、清平调"),
        ("绝境重生", "Release After Peril", "早发白帝城"),
    ]
    cols = 3
    for i, (zh, en, poems) in enumerate(themes):
        col = i % cols
        row = i // cols
        left = Inches(0.5 + col * 4.2)
        top = Inches(1.2 + row * 2.6)
        add_rect(slide, left, top, Inches(4.0), Inches(2.3), PAPER_DARK)
        add_accent_bar(slide, left, top, Inches(4.0), Inches(0.08), JADE)
        add_textbox(
            slide, left + Inches(0.2), top + Inches(0.3), Inches(3.6), Inches(0.4),
            zh, size=18, color=INK, bold=True
        )
        add_textbox(
            slide, left + Inches(0.2), top + Inches(0.75), Inches(3.6), Inches(0.35),
            en, size=12, color=JADE, italic=True
        )
        add_textbox(
            slide, left + Inches(0.2), top + Inches(1.25), Inches(3.6), Inches(0.8),
            poems, size=13, color=INK_SOFT
        )
    footer(slide, page, total)


def closing_slide(prs, page, total):
    slide = blank_slide(prs)
    paint_bg(slide, INK)
    add_rect(slide, 0, 0, Inches(0.35), SLIDE_H, GOLD)
    add_textbox(
        slide, Inches(1.2), Inches(2.2), Inches(11), Inches(0.6),
        "长风破浪会有时，直挂云帆济沧海。",
        size=28, color=WHITE, bold=True
    )
    add_textbox(
        slide, Inches(1.2), Inches(3.1), Inches(11), Inches(0.5),
        "There will be a time to ride the wind and cleave the waves.",
        size=16, color=PAPER_DARK, italic=True
    )
    add_accent_bar(slide, Inches(1.2), Inches(3.9), Inches(2.2), Inches(0.06), JADE_LIGHT)
    add_textbox(
        slide, Inches(1.2), Inches(4.3), Inches(11), Inches(1.2),
        "十二名篇，贯穿出蜀、供奉、放还、流放与遇赦的一生轨迹。\n"
        "读其诗，可见盛唐之气象，亦可见一位诗人的骄傲、深情与自由。\n\n"
        "— 李白诗作精讲 · 完 —",
        size=14, color=PAPER
    )
    footer(slide, page, total)


def reading_tips_slide(prs, page, total):
    slide = blank_slide(prs)
    paint_bg(slide, PAPER)
    content_header(slide, "阅读提示 · How to Read These Poems")
    tips = (
        "1. 先诵中文，感受声韵与节奏；再读英译，对照意象如何转换。\n"
        "   Recite the Chinese first for sound and cadence; then read the English for imagery.\n\n"
        "2. 注意乐府歌行的“杂言”与绝句的凝练：前者如交响乐，后者如水墨一笔。\n"
        "   Yuefu songs sprawl musically; quatrains distill a single stroke.\n\n"
        "3. 背景帮助理解，但诗意大于史实——允许象征与多义并存。\n"
        "   Context helps, yet meaning exceeds biography; allegory and ambiguity are allowed.\n\n"
        "4. 李白的“豪”常与“愁”共生：纵酒、游仙、傲视权贵，皆是对困境的回应。\n"
        "   His boldness coexists with sorrow—wine, immortals, and defiance answer adversity."
    )
    add_textbox(
        slide, Inches(0.7), Inches(1.2), Inches(12), Inches(5.5),
        tips, size=15, color=INK
    )
    footer(slide, page, total)


def build():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H

    # Estimate total pages for footer
    # cover + toc×2 + intro + tips + timeline + themes + closing
    # per poem: divider + chinese + english [+ full zh/en if long] + bilingual(short) + bg + meaning
    # We'll fill footers in a second pass by rebuilding with known total — simpler: compute first.

    # Compute total
    total = 1 + 2 + 1 + 1  # cover, toc×2, intro, tips
    for p in POEMS:
        total += 1  # divider
        if p.get("full_chinese"):
            total += 4  # excerpt zh, excerpt en, full zh, full en
        else:
            total += 3  # zh, en, bilingual
        total += 2  # background, meaning
    total += 3  # timeline, themes, closing

    page = 0

    def next_page():
        nonlocal page
        page += 1
        return page

    cover_slide(prs, total)
    next_page()

    toc_slides(prs, total, start_page=2)
    next_page()
    next_page()

    intro_slide(prs, next_page(), total)
    reading_tips_slide(prs, next_page(), total)

    for poem in POEMS:
        section_divider(prs, poem, next_page(), total)
        if poem.get("full_chinese"):
            chinese_slide(prs, poem, next_page(), total, poem["chinese"], "原文节选 Excerpt")
            english_slide(prs, poem, next_page(), total, poem["english"], "英译节选 Excerpt")
            chinese_slide(prs, poem, next_page(), total, poem["full_chinese"], "全文原文 Full Chinese")
            english_slide(prs, poem, next_page(), total, poem["full_english"], "全文英译 Full English")
        else:
            chinese_slide(prs, poem, next_page(), total)
            english_slide(prs, poem, next_page(), total)
            bilingual_compact(prs, poem, next_page(), total)
        bg_meaning_slide(prs, poem, next_page(), total, "background")
        bg_meaning_slide(prs, poem, next_page(), total, "meaning")

    timeline_slide(prs, next_page(), total)
    themes_slide(prs, next_page(), total)
    closing_slide(prs, next_page(), total)

    assert page == total, f"page count mismatch: {page} vs {total}"

    out = "/workspace/李白十二名篇精讲_中英对照.pptx"
    prs.save(out)
    print(f"Saved: {out}")
    print(f"Total slides: {total}")
    return out, total


if __name__ == "__main__":
    build()
