"""1차 판정: 사전어 규칙(정규식)으로 제목·초록·주제어를 판정한다. 판정 기준표(codebook.md)의 항목을 따른다.
규칙은 수정할 때마다 판 번호를 올리고, 정독 판정과의 일치도는 audit/agreement.py로 다시 계산한다."""
import re

RULES_VERSION = "1.0"

ORGANISMS = (r"pine ?cones?|sunflowers?|lotus|cact(us|i)|termites?|mounds?|stomat(a|al|e)|leaf|leaves|"
             r"plants?|flowers?|petals?|mimosa|gazania|venus fly ?trap|strelitzia|bird[- ]of[- ]paradise|"
             r"skin of|human skin|skins? of animals|polar bears?|penguins?|camels?|elephants?|beetles?|"
             r"stenocara|namib|ants?\b|silver ants?|butterfl(y|ies)|morpho|moths?|bees?|honey ?bees?|honeycomb|"
             r"spiders?|snails?|shells?|mollus[ck]s?|turtles?|tortoises?|fish|scales?|sharks?|whales?|"
             r"cephalopods?|squids?|octopus|chromatophores?|iris|eyes?|feathers?|birds?|bats?|corals?|sponges?|"
             r"diatoms?|algae|moss(es)?|lichens?|fungi|mycelium|trees?|bark|roots?|seeds?|cones?|"
             r"oxalis|maple|bamboo|grass(es)?|desert plants?|succulents?|bromeliads?|nepenthes|aldrovanda|"
             r"armadillos?|pangolins?|hedgehogs?|porcupines?|zebras?|giraffes?|ostrich|kingfishers?|"
             r"organisms?|species|animals?")
GENERIC_NATURE = r"\b(nature|natural)\b"
MECHANISM = (r"hygroscopic|hygromorph|bilayer|turgor|osmotic|guard cells?|swelling|anisotrop|"
             r"microstructur|nanostructur|superhydrophob|evaporative cooling|countercurrent|vasodilat|"
             r"vasoconstrict|thermoregulat|heliotrop|phototrop|nyctinast|thigmonast|nastic|"
             r"stack effect|convection in (the )?mounds?|cellulose fibril|lignin")
TRANSFER = (r"ISO ?18458|abstraction|abstracted|abstract (the|its) (principle|function)|"
            r"top[- ]down|bottom[- ]up|problem[- ]driven|solution[- ]driven|problem[- ]based|"
            r"biotriz|design spiral|asknature|biomimicry taxonomy|transfer(red)? (of )?(the )?(biological )?"
            r"(principles?|strategies|mechanisms?|functions?)|(translat|transfer)\w* .{0,40}(into|to) (architect|build|design|facade|façade)|"
            r"biomimetic (design )?(process|methodology|framework|approach)|bio-?inspired design (process|methodology|framework)")
FORM = r"\b(form|shape|morpholog\w*|geometr\w*|pattern\w*|aesthetic\w*|silhouette|ornament\w*|voronoi|fractal)\b"
MATERIAL = (r"\bmaterials?\b|composite|coating|paint|film|membrane|textile|bilayer|hygroscopic|"
            r"4d[- ]print|3d[- ]print|wood|timber|polymer|hydrogel|shape memory|smart material")
PROCESS = (r"\b(control|controller|controlled|actuat\w*|kinetic|responsive|adaptive|adaptation|"
           r"movement|motion|open(s|ing)? and clos|respond\w*|react\w*|tracking|sensor\w*|algorithm|"
           r"behaviou?r|self-regulat\w*|feedback|rule-based|swarm)\b")
ECOSYSTEM = r"\b(ecosystem\w*|symbio\w*|circular|regenerative|nutrient|metabolism|ecological services)\b"

E_FIELD = (r"field (test|measurement|monitoring|study|experiment)|in[- ]situ|on[- ]site|monitored|"
           r"real building|existing building.{0,30}measur|full[- ]scale|post[- ]occupancy")
E_PROTO = (r"prototype|mock-?up|physical model|scale model|experiment(al|s)?\b|laboratory|lab test|"
           r"test(ed)? (in|under|on)|fabricat\w*|demonstrator|pavilion|wind tunnel|climate chamber|"
           r"heliodon|measured|sample(s)? (were|was)")
E_SIM = (r"simulat\w*|energyplus|energy plus|design ?builder|trnsys|radiance|daysim|ladybug|honeybee|"
         r"grasshopper|climate studio|ies ?ve|openstudio|cfd|computational fluid|finite element|fea\b|"
         r"numerical|parametric (study|analysis|model)|optimi[sz]\w*|genetic algorithm|galapagos|octopus|"
         r"annual (energy|daylight)|daylight autonomy|sda\b|udi\b|useful daylight")
E_DESIGN = (r"design (proposal|concept|scheme|framework)|propos(e|ed|es) a (new |novel )?(design|concept|facade|façade|system)|"
            r"conceptual|case stud(y|ies)|schematic")
QUANT = r"\d+(\.\d+)?\s?(%|percent|kwh|kw\b|w/m|°c|℃|k\b|lux|lx\b|db\b)|by (up to |about |approximately )?\d+(\.\d+)?\s?(%|times)"
BASE_EQUIV = (r"(conventional|traditional|standard|typical|commercial|existing) (venetian|blinds?|louvers?|louvres?|"
              r"shading|kinetic|dynamic|automated|motori[sz]ed|adaptive)|(rule-based|cut-?off|slat[- ]angle|"
              r"thermostat|schedule[d]?|reactive) control|compared (with|to) .{0,60}(automated|dynamic|kinetic|"
              r"motori[sz]ed|controlled|adaptive) (shading|blinds?|louvers?|facade|façade|system)|non-biomimetic|"
              r"non-bio-?inspired|electrochromic")
BASE_STATIC = (r"(static|fixed|stationary|horizontal|vertical) (shading|louvers?|louvres?|fins?|blinds?|overhangs?|"
               r"shades?|screens?)|overhangs?|brise[- ]soleil|venetian blinds?|roller (shades?|blinds?)")
BASE_REF = (r"base ?case|baseline|reference (case|building|model|scenario)|without (any )?(shading|the (facade|façade|"
            r"system|skin|device))|unshaded|no[- ]shading|bare (glass|façade|facade)|existing (facade|façade|"
            r"envelope|condition)|before (the )?(retrofit|intervention)|conventional (facade|façade|glazing|"
            r"envelope|building|wall|curtain wall)|compared (with|to)|in comparison|relative to|than (the )?"
            r"(base|reference|conventional|existing|original)")
SUST = (r"sustainab\w*|eco-?friendly|environmentally[- ]friendly|green (building|architecture|design)|"
        r"ecological(ly)? (design|architecture|friendly)|low[- ]carbon|net[- ]zero|carbon[- ]neutral")
LCA = (r"life[- ]cycle (assessment|analysis|cost\w*|impact)|\blca\b|embodied (energy|carbon)|cradle[- ]to|"
       r"environmental impact assessment|global warming potential|\bgwp\b|life[- ]cycle cost|payback|"
       r"cost[- ]benefit|economic (analysis|feasibility|evaluation)")
OPER = r"energy (consumption|use|saving\w*|demand|performance|efficien\w*)|cooling (load|demand|energy)|heating (load|demand|energy)|\beui\b"
BIO_AFF = (r"biolog|botan|zoolog|plant (science|biology|biomechanics)|life sciences?|ecolog|evolution|"
           r"biosciences?|biomechanics group|botanic garden|natural history|entomolog|marine science|forest science")


def has(pat, t):
    return re.search(pat, t, re.I) is not None


def code(rec):
    """rec: dict(title, abstract, keywords(list), affiliations(list of str))"""
    t = " ".join([rec.get("title") or "", rec.get("abstract") or "", " ".join(rec.get("keywords") or [])])
    out = {}
    out["B1"] = int(has(ORGANISMS, t) and not re.fullmatch(r"\s*", t))
    # B2: 0 이름만, 1 기능, 2 기제
    if not out["B1"]:
        out["B2"] = 0
    elif has(MECHANISM, t):
        out["B2"] = 2
    elif has(r"(function|strateg\w*|adapt\w*|mechanism|principle|regulat\w*|respond|response) (of|in|from|used by|found in|inspired by) (the )?(" + ORGANISMS + ")", t) \
            or has(r"(" + ORGANISMS + r")\W+(\w+\W+){0,6}(regulat\w*|adapt\w*|respond\w*|control\w*|cool\w*|shad\w*|open\w*|clos\w*|track\w*)", t):
        out["B2"] = 1
    else:
        out["B2"] = 0
    out["T1"] = int(has(TRANSFER, t))
    lv = []
    if has(ECOSYSTEM, t):
        lv.append("ecosystem")
    if has(PROCESS, t):
        lv.append("process")
    if has(MATERIAL, t):
        lv.append("material")
    if has(FORM, t):
        lv.append("form")
    out["L_all"] = lv
    out["L"] = lv[0] if lv else "unclear"
    if has(E_FIELD, t):
        e = 4
    elif has(E_PROTO, t):
        e = 3
    elif has(E_SIM, t):
        e = 2
    elif has(E_DESIGN, t):
        e = 1
    else:
        e = 0
    out["E"] = e
    out["Q"] = int(has(QUANT, t))
    if has(BASE_EQUIV, t):
        r = 3
    elif has(BASE_STATIC, t):
        r = 2
    elif has(BASE_REF, t):
        r = 1
    else:
        r = 0
    out["R"] = r
    out["S1"] = int(has(SUST, t))
    out["S2"] = (2 if has(LCA, t) else (1 if has(OPER, t) else 0)) if out["S1"] else 0
    aff = " ".join(rec.get("affiliations") or [])
    out["P"] = int(has(BIO_AFF, aff)) if aff.strip() else None
    return out
