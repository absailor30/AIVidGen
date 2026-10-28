"""Recipe Clause part 1 — clips with refs (close-up, full body, expression)."""
V = ("<Subject 1> is the woman shown in <Picture 1> (face close-up) and <Picture 2> (full body), "
     "preserving her identity, face, sleek platinum blonde hair, red lipstick, black blazer dress and red nails. "
     "<Picture 3> shows only her {e} facial expression; ignore the clothing in <Picture 3>.")
OFFICE = "a small restaurant back office with a wooden desk and warm lamp light"
KITCHEN = "a busy professional restaurant kitchen with stainless steel counters and soft steam"

def p(expr, summary, place, state, shot, sound):
    return f"""subject_definitions:
{V.format(e=expr)}
summary:
[reference generation] {summary}
retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - face, hair, makeup, nails and outfit.
detailed_description:
The target video is a vertical cinematic shot in {place}. From the very first frame exactly one person is in the scene, and from the very first frame {state} No readable text anywhere.
[Shot 1] {shot}
overall_soundscape: {sound} No one speaks, no dialogue, no voices.
non_diegetic_music: none."""

CLIPS = [
 {"name": "clip02_vanessa_apron", "refs": ["vanessa_office_close", "vanessa_office_ref", "vanessa_smug"],
  "prompt": p("smug", "A woman looks down with contempt at a folded white apron on her desk.", OFFICE,
   "her expression is cold contempt: one eyebrow slightly raised, lips pressed in a faint sneer. She looks down at the desk, never into the lens.",
   "Close-up, head, shoulders and hands. <Subject 1> sits behind the desk looking down at a neatly folded white apron in front of her. Her red-nailed fingers hover just above it without touching, then slowly withdraw. Slow camera push-in.",
   "quiet office, faint lamp hum.")},
 {"name": "clip10_vanessa_tablet", "refs": ["vanessa_office_close", "vanessa_office_ref", "vanessa_angry"],
  "prompt": p("angry", "A furious woman, lost for words, jabs at her tablet.", OFFICE,
   "she is angry and flustered: jaw clenched, eyes narrowed. She looks to the right of the camera at someone off-screen, never into the lens. The tablet screen faces away from the camera.",
   "Close-up, chest up. <Subject 1> opens her mouth as if to reply, closes it again without a word, looks down and stabs at a tablet on the desk with one finger, hard, twice. Static camera.",
   "quiet office, two sharp taps on glass.")},
 {"name": "clip12_vanessa_door", "refs": ["vanessa_office_close", "vanessa_office_ref", "vanessa_angry"],
  "prompt": p("angry", "A woman glares in silent fury at a doorway someone just walked out of.", OFFICE,
   "she is seething: jaw clenched hard, nostrils flared, eyes fixed and cold. She stares to the left of the camera at an open doorway, never into the lens.",
   "Tight close-up, head and shoulders, face fills the frame. <Subject 1> sits rigid behind the desk staring at the doorway. Her jaw tightens, she swallows hard, and her fingers curl into a fist on the desk. Slow camera push-in.",
   "quiet office, a door creaking as it slowly swings.")},
 {"name": "clip24_vanessa_drains", "refs": ["vanessa_office_close", "vanessa_office_ref", "vanessa_shock"],
  "prompt": p("shocked", "A woman's confidence collapses as someone walks away from her.", KITCHEN,
   "her face is pale and unsettled: lips slightly parted, eyes widening, any smile gone. She looks to the right of the camera, following someone walking away off-screen, never into the lens.",
   "Close-up, chest up. <Subject 1> stands still in the kitchen, her eyes tracking someone leaving. She swallows, her shoulders drop slightly, and she grips the edge of the steel counter. Static camera.",
   "kitchen hum, distant clatter, footsteps fading away.")},
 {"name": "clip26_vanessa_freeze", "refs": ["vanessa_office_close", "vanessa_office_ref", "vanessa_shock"],
  "prompt": p("shocked", "A woman freezes in shock at news she has just heard.", KITCHEN,
   "she is frozen in shock: eyes wide, mouth slightly open, colour drained from her face. She stares to the left of the camera at someone off-screen holding a phone, never into the lens.",
   "Tight close-up, face fills the frame. <Subject 1> stands completely still, not blinking, then slowly raises one hand to her collarbone. Very slow camera push-in.",
   "kitchen hum suddenly quiet, a single phone buzz.")},
]

# ---- batch 2: single-person clips without a set image ----
DINING = "an elegant modern restaurant dining room in the morning, warm wood tables with white linen, brass pendant lights"
TERRACE = "a restaurant rooftop terrace at night with string lights, an iron railing and city lights beyond"
APARTMENT = "a small cosy apartment kitchen at night with a single warm pendant light and glass jars on a wooden counter"
DARK_OFFICE = "a small restaurant back office at night, lit only by one dim desk lamp"
LOOK = {
 "aria": ("woman", "her", "sleek dark brown low ponytail, light olive skin, crisp white shirt with rolled sleeves, black trousers and nude nails"),
 "aria_home": ("woman", "her", "sleek dark brown hair worn loose, light olive skin, oversized grey knit sweater and black jeans"),
 "vanessa": ("woman", "her", "sleek platinum blonde hair, red lipstick, black blazer dress and red nails"),
 "maya": ("woman", "her", "curly shoulder-length black hair, warm brown skin, mustard yellow blazer over a white camisole and dark jeans"),
 "daniel": ("man", "his", "short silver hair, trimmed silver beard, navy three-piece suit and burgundy tie"),
}
def q(look, expr, summary, place, state, shot, sound):
    g, pos, desc = LOOK[look]
    sub = f"<Subject 1> is the {g} shown in <Picture 1> (face close-up) and <Picture 2> (full body), preserving {pos} identity, face, {desc}."
    if expr:
        sub += f" <Picture 3> shows only {pos} {expr} facial expression; ignore the clothing in <Picture 3>."
    return f"""subject_definitions:
{sub}
summary:
[reference generation] {summary}
retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - face, hair and outfit.
detailed_description:
The target video is a vertical cinematic shot in {place}. From the very first frame exactly one person is in the scene, and from the very first frame {state} No readable text anywhere.
[Shot 1] {shot}
overall_soundscape: {sound} No one speaks, no dialogue, no voices.
non_diegetic_music: none."""

A = ["aria_close", "aria_ref"]; VN = ["vanessa_office_close", "vanessa_office_ref"]
M = ["maya_v2_close", "maya_v2_ref"]; D = ["daniel_close", "daniel_ref"]
CLIPS2 = [
 {"name": "clip01_aria_apron", "refs": A + ["aria_cold"], "prompt": q("aria", "cold, calm",
  "A calm woman folds a white apron and slides it across a steel counter.", KITCHEN,
  "her face is calm, cold and unreadable. She looks down at her hands, never into the lens.",
  "Medium close-up, chest up with hands visible. <Subject 1> folds a white apron into a neat square on a steel counter, smooths it once and slides it forward away from her. Slow camera push-in toward her face.",
  "quiet kitchen hum, soft fabric rustle.")},
 {"name": "clip04_vanessa_beaming", "refs": VN + ["vanessa_smile"], "prompt": q("vanessa", "smiling",
  "A glamorous woman steps forward beaming to take the spotlight.", DINING,
  "she is beaming with a proud, triumphant smile, chin lifted. She looks to the left of the camera at a crowd off-screen, never into the lens.",
  "Medium shot, waist up. <Subject 1> takes two confident steps forward toward the off-screen crowd, smoothing her blazer dress, then stops and raises her chin. Slow camera push-in.",
  "light applause, heels clicking on a wooden floor.")},
 {"name": "clip05_aria_clap", "refs": A + ["aria_unbothered"], "prompt": q("aria", "calm, unreadable",
  "A woman claps politely, her face giving nothing away.", DINING,
  "her face is calm and unreadable, a polite neutral expression. She looks to the left of the camera at someone off-screen, never into the lens.",
  "Close-up, chest up. <Subject 1> claps slowly and politely three times, her expression not changing at all, her eyes steady. Static camera.",
  "light applause around her.")},
 {"name": "clip08_aria_unties", "refs": A + ["aria_cold"], "prompt": q("aria", "cold, calm",
  "A woman calmly unties her apron and lays it on her boss's desk.", OFFICE,
  "she is calm, composed and cold. She looks across the desk to the right of the camera at someone off-screen, never into the lens.",
  "Medium shot, waist up. <Subject 1> stands in front of the desk, unhurriedly unties a white apron from her waist, folds it once and sets it neatly on the desk. Static camera.",
  "quiet office, fabric rustle.")},
 {"name": "clip11_aria_door", "refs": A + ["aria_unbothered"], "prompt": q("aria", "calm",
  "A woman opens a door wider and walks out without looking back.", OFFICE,
  "she is calm and unbothered. She never looks into the lens.",
  "Medium shot. <Subject 1> pulls the office door wide open, pauses for a beat, then walks out through it without looking back. Static camera.",
  "door creak, footsteps on a hard floor.")},
 {"name": "clip13_aria_fridge", "refs": A, "prompt": q("aria", "",
  "A woman pins a laminated sheet to a steel fridge door.", KITCHEN,
  "she is calm and deliberate. She looks at the fridge, never into the lens. The sheet is blank white with no readable text.",
  "Medium shot, waist up. <Subject 1> presses a blank laminated sheet onto a stainless steel fridge door with a magnet and smooths it flat with her palm, then steps back to look at it. Static camera.",
  "kitchen hum, a soft magnet click.")},
 {"name": "clip16_maya_plates", "refs": M + ["maya_angry"], "prompt": q("maya", "frustrated",
  "A frustrated restaurant manager pushes into the kitchen carrying returned plates.", KITCHEN,
  "she is frustrated and stressed, brow furrowed. She looks to the right of the camera at someone off-screen, never into the lens.",
  "Medium shot, waist up. <Subject 1> pushes through swinging kitchen doors carrying two plates of food, stops and holds them up. Static camera.",
  "busy kitchen, swing doors flapping, sizzling pans.")},
 {"name": "clip17_vanessa_storms", "refs": VN + ["vanessa_angry"], "prompt": q("vanessa", "angry",
  "A furious woman storms into a busy kitchen holding a phone.", KITCHEN,
  "she is furious, jaw clenched, eyes blazing. She looks to the left of the camera at someone off-screen, never into the lens. The phone screen faces away from the camera.",
  "Medium shot, waist up. <Subject 1> storms into the kitchen with a phone in her hand and stops abruptly, glaring. Static camera.",
  "busy kitchen, sharp heel steps.")},
 {"name": "clip18_vanessa_fridge", "refs": VN + ["vanessa_angry"], "prompt": q("vanessa", "angry",
  "A furious woman glances at a fridge and realises she has been outplayed.", KITCHEN,
  "she is angry and humiliated: jaw clenched, lips pressed tight. Her eyes flick to the right of the camera toward a fridge off-screen, never into the lens.",
  "Close-up, head and shoulders. <Subject 1> glances sideways at something off-screen, holds the look, and her jaw tightens; she swallows hard. Static camera.",
  "kitchen hum.")},
 {"name": "clip21_daniel_window", "refs": D + ["daniel_sad"], "prompt": q("daniel", "troubled",
  "A troubled older man looks through a lit window at night.", TERRACE,
  "he is troubled and quietly sad. He looks to the left of the camera through a lit window off-screen, never into the lens.",
  "Close-up, head and shoulders, at night under string lights. <Subject 1> stares through the window for a long moment, then lowers his eyes and exhales. Static camera.",
  "night city ambience, faint music from inside.")},
 {"name": "clip22_daniel_leaves", "refs": D + ["daniel_sad"], "prompt": q("daniel", "troubled",
  "An older man stands and walks away avoiding someone's eyes.", TERRACE,
  "he is uneasy and avoids eye contact. He never looks into the lens.",
  "Medium shot at night. <Subject 1> rises from a terrace chair, buttons his jacket, avoids looking at anyone and walks away along the terrace. Static camera.",
  "night city ambience, footsteps on wood.")},
 {"name": "clip25_maya_phone", "refs": M + ["maya_shock"], "prompt": q("maya", "shocked",
  "A woman reads a message on her phone and her eyes widen.", KITCHEN,
  "she is startled, eyes wide, lips parted. She looks down at a phone in her hand, never into the lens. The phone screen faces away from the camera.",
  "Close-up, head and shoulders. <Subject 1> looks down at her phone as it buzzes, reads it, and slowly raises her eyes in disbelief. Static camera.",
  "kitchen hum, a single phone buzz.")},
 {"name": "clip27_aria_walks", "refs": A + ["aria_unbothered"], "prompt": q("aria", "calm",
  "A woman walks out of a kitchen without looking back.", KITCHEN,
  "she is calm and unbothered. She never looks into the lens.",
  "Wide shot, full body. <Subject 1> walks steadily away from the camera toward swinging kitchen doors and pushes through them without looking back. Static camera.",
  "kitchen hum, footsteps, swing doors.")},
 {"name": "clip28_aria_jar", "refs": ["aria_home_close", "aria_home_ref", "aria_unbothered"], "prompt": q("aria_home", "quietly confident",
  "A woman lifts the lid off a jar at home and smiles faintly.", APARTMENT,
  "she is quietly confident with a faint knowing smile. She looks down at the counter, never into the lens.",
  "Close-up, head, shoulders and hands. <Subject 1> lifts the lid off a glass jar on the counter; a wisp of steam rises; a faint smile crosses her face. Slow camera push-in.",
  "quiet night, a glass lid clink.")},
 {"name": "clip29_vanessa_dark", "refs": VN + ["vanessa_shock"], "prompt": q("vanessa", "stunned",
  "A woman sits alone in a dark office staring at a folded apron.", DARK_OFFICE,
  "she is stunned and uneasy, the confidence gone from her face. She stares down at the desk, never into the lens.",
  "Medium close-up, chest up. <Subject 1> sits alone at the desk in near darkness, staring at a neatly folded white apron in front of her, not moving. Very slow camera push-in.",
  "silence, a distant clock ticking.")},
]

# ---- batch 3: clips using set images, Leo's chef look, and two-person shots ----
LOOK["leo"] = ("man", "his", "messy short ginger hair, freckles, round black glasses, white chef whites and white apron")
def r(look, n_refs_before, expr, summary, place_ref, state, shot, sound, extra_subject=None, people=1):
    g, pos, desc = LOOK[look]
    a, b = n_refs_before + 1, n_refs_before + 2
    subs = [f"<Subject 1> is the {place_ref} from <Picture 1>, preserving its layout, lighting and colours.",
            f"<Subject 2> is the {g} shown in <Picture {a}> (face close-up) and <Picture {b}> (full body), preserving {pos} identity, face, {desc}."]
    ret = ["<Subject 1> (appears in [Shot 1]): fully_preserved - layout and lighting.",
           "<Subject 2> (appears in [Shot 1]): fully_preserved - face, hair and outfit."]
    nxt = b + 1
    if expr:
        subs[1] += f" <Picture {nxt}> shows only {pos} {expr} facial expression; ignore the clothing in <Picture {nxt}>."
        nxt += 1
    if extra_subject:
        g2, pos2, desc2 = LOOK[extra_subject]
        subs.append(f"<Subject 3> is the {g2} shown in <Picture {nxt}> (full body), preserving {pos2} identity, face, {desc2}.")
        ret.append("<Subject 3> (appears in [Shot 1]): fully_preserved - face, hair and outfit.")
    n = {1: "exactly one person is", 2: "exactly two people are"}[people]
    return f"""subject_definitions:
{chr(10).join(subs)}
summary:
[reference generation] {summary}
retention_analysis:
{chr(10).join(ret)}
detailed_description:
The target video is a vertical cinematic shot in <Subject 1>. From the very first frame {n} in the scene, and from the very first frame {state} No readable text anywhere.
[Shot 1] {shot}
overall_soundscape: {sound} No one speaks, no dialogue, no voices.
non_diegetic_music: none."""

S = "/workspace/sets/"
LC = ["leo_chef_close", "leo_chef_ref"]
CLIPS3 = [
 {"name": "clip03_daniel_toast", "refs": [S+"set_dining"] + D + ["daniel_smile"], "prompt": r("daniel", 1, "proud, smiling",
  "A proud older man raises a champagne glass to his staff.", "elegant restaurant dining room",
  "he is beaming with pride. He looks to the left of the camera at a crowd off-screen, never into the lens.",
  "Medium shot, waist up. <Subject 2> raises a glass of champagne high toward the off-screen crowd, smiling warmly, then nods. Slow camera push-in.",
  "murmuring staff, a glass clink.")},
 {"name": "clip06_leo_glance", "refs": [S+"set_dining"] + LC, "prompt": r("leo", 1, "",
  "A young chef glances sideways with a worried look.", "elegant restaurant dining room",
  "he looks worried and uneasy. He glances to the right of the camera at someone off-screen, never into the lens.",
  "Close-up, head and shoulders. <Subject 2> stands among clapping staff, stops clapping and glances sideways with a worried frown. Static camera.",
  "applause fading.")},
 {"name": "clip07_vanessa_tablet", "refs": [S+"set_office"] + VN + ["vanessa_smug"], "prompt": r("vanessa", 1, "smug",
  "A smug woman reads payroll on a tablet behind a desk.", "small restaurant back office",
  "she is smug and self-satisfied, a faint smirk. She looks down at a tablet, then up to the right of the camera at someone off-screen, never into the lens. The tablet screen faces away from the camera.",
  "Medium shot, waist up. <Subject 2> sits behind the desk swiping a tablet, pauses, then looks up across the desk with a satisfied smirk. Static camera.",
  "quiet office, tablet taps.")},
 {"name": "clip14_leo_grin", "refs": [S+"set_kitchen"] + LC + ["leo_smug"], "prompt": r("leo", 1, "knowing, grinning",
  "A young chef slowly breaks into a knowing grin.", "professional restaurant kitchen",
  "he has a knowing look. He looks to the left of the camera at someone off-screen, never into the lens.",
  "Close-up, head and shoulders. <Subject 2> listens, then slowly breaks into a wide knowing grin and nods once. Static camera.",
  "kitchen hum.")},
 {"name": "clip15_leo_taste", "refs": [S+"set_kitchen"] + LC, "prompt": r("leo", 1, "",
  "A chef tastes a sauce and winces.", "professional restaurant kitchen",
  "he is focused. He looks down at a spoon, never into the lens.",
  "Close-up, head and shoulders. <Subject 2> lifts a spoon of sauce from a pot to his mouth, tastes it, and winces in disgust. Static camera.",
  "sizzling pans, busy kitchen.")},
 {"name": "clip19_kitchen_freeze", "refs": [S+"set_kitchen"] + VN + ["vanessa_angry", "leo_chef_ref"], "prompt": r("vanessa", 1, "humiliated, angry",
  "A kitchen falls silent as a furious woman is humiliated in front of her staff.", "professional restaurant kitchen",
  "<Subject 2> stands in the foreground, flushed and furious, and <Subject 3> stands behind her at a counter. Neither looks into the lens.",
  "Medium shot. <Subject 2> in the foreground stares to the left of the camera, her face reddening; behind her <Subject 3> freezes and a metal spoon slips from his hand and clatters onto the counter. Static camera.",
  "sudden silence, a spoon clattering.", extra_subject="leo", people=2)},
 {"name": "clip20_terrace_talk", "refs": [S+"set_terrace"] + D + ["aria_ref"], "prompt": r("daniel", 1, "",
  "An older man and a younger woman talk quietly at a terrace railing at night.", "rooftop terrace at night",
  "<Subject 2> and <Subject 3> stand side by side at the railing, both serious. Neither looks into the lens.",
  "Medium shot at night. <Subject 2> and <Subject 3> stand at the railing with city lights behind; he turns to her and speaks quietly while she keeps looking out at the city, unmoved. Static camera.",
  "night city ambience, faint music from inside.", extra_subject="aria", people=2)},
 {"name": "clip23_vanessa_laurent", "refs": [S+"set_kitchen"] + VN + ["vanessa_smile"], "prompt": r("vanessa", 1, "proud, smiling",
  "A woman proudly presents a celebrity chef to her kitchen staff.", "professional restaurant kitchen",
  "she is smiling proudly. A man in a designer black chef's jacket stands beside her with his back to the camera. She never looks into the lens.",
  "Medium shot, waist up. <Subject 2> gestures proudly toward the man in the black chef's jacket beside her, looking to the left of the camera at staff off-screen. Static camera.",
  "staff murmuring.")},
]
