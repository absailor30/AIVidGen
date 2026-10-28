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
