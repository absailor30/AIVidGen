# Flow prompt pack — full reference set for every actor

Tool: Flow → **Nano Banana Pro**, **Portrait 9:16**, 2 outputs per prompt, keep
the one closest to the base ref. Everything is photorealistic, plain light grey
studio background, one person per image.

How it works:
1. **Step A — base ref** (text only, no image attached). This is the source of
   truth for the face. Generate 4, keep the best → `{actor}_ref`.
2. **Steps B–E — every other view**, made **from the base ref** (attach
   `{actor}_ref` every time; never chain off a previous output — drift adds up).
3. Crop the **✦ watermark** (bottom-right) out of every image before use.
4. One folder per actor; file names exactly as listed.

Existing actors (Maya, Vanessa, Daniel, Leo) already have a base ref and a
close-up — do only the views they're missing (marked ★ below).

---

## Step A — base ref (text only)

Paste the template with the actor's description from the cast list below:

```
Full-body character reference photo, front view, standing straight in a neutral relaxed pose, arms at sides, whole body visible from head to shoes. Plain light grey studio background, soft even studio lighting. [ACTOR DESCRIPTION]. Photorealistic, sharp focus, natural skin texture, consistent proportions. No text, no logos, no other people.
```

## Step B — core views (attach `{actor}_ref`)

Use "woman/her" or "man/his" as fits. Every prompt starts with the same
identity line:

> The [woman/man] from the reference image, exact same face, hair, skin tone, body and outfit.

and ends with:

> Plain light grey studio background, soft even studio lighting. Photorealistic, sharp focus, natural skin texture. No text, no other people.

| # | File | Middle of the prompt | Why the video model needs it |
|---|---|---|---|
| 1 | `{actor}_close` ★ | Close-up head-and-shoulders portrait, facing the camera directly, neutral expression. | main identity ref (always paired with `_ref`) |
| 2 | `{actor}_34L` ★ | Close-up head-and-shoulders, head turned three-quarters to [her/his] left, eyes slightly off camera. | faces turned in conversation shots |
| 3 | `{actor}_34R` ★ | Close-up head-and-shoulders, head turned three-quarters to [her/his] right, eyes slightly off camera. | the other side of two-shots |
| 4 | `{actor}_profile` ★ | Close-up side profile, head turned fully to [her/his] right. | over-the-shoulder and side shots |
| 5 | `{actor}_medium` ★ | Medium shot from the waist up, standing, facing the camera, arms relaxed. | the framing most story shots use |
| 6 | `{actor}_full34` ★ | Full body, head to shoes, standing at a three-quarter angle, turned to [her/his] left. | walking / entering shots |
| 7 | `{actor}_fullside` ★ | Full body, head to shoes, side view, standing, facing right. | walking past camera |
| 8 | `{actor}_back` ★ | Full body, head to shoes, seen from behind, back to the camera, walking away. | exits (like Vanessa's corridor walk) |
| 9 | `{actor}_seated` ★ | Medium shot, sitting on a simple grey chair at a plain table, hands resting on the table, facing the camera. | dinners, meetings, offices |

## Step C — expressions (attach `{actor}_ref`)

Same identity line and ending. Middle:

> Close-up head-and-shoulders, facing the camera, **[EXPRESSION]**.

| File | [EXPRESSION] |
|---|---|
| `{actor}_smile` ★ | a warm genuine smile |
| `{actor}_angry` ★ | angry, frowning, jaw clenched |
| `{actor}_shock` ★ | shocked, eyes wide, mouth slightly open |
| `{actor}_sad` ★ | sad, eyes glossy with tears, lips pressed together |
| `{actor}_smug` ★ | smug, one eyebrow raised, faint smirk |

These aren't uploaded to every generation — use the one that matches the
shot's emotion **as a third ref** when that emotion is the point of the shot
(e.g. `vanessa_shock` for her frozen close-up).

## Step D — hands and shoes (women; attach `{actor}_ref`)

| File | Middle of the prompt |
|---|---|
| `{actor}_hands` ★ | Close-up of her hands resting together, showing the exact same manicure, nail shape and rings. |
| `{actor}_shoes` ★ | Close-up of her feet in the exact same heels, standing on a light grey floor, showing the exact same shoes [and pedicure]. Product-photo style. |

Used only for story beats about hands or feet (nails tapping, heels walking away).

## Step E — formal outfit (actors with a formal look; attach `{actor}_ref`)

| File | Prompt |
|---|---|
| `{actor}_formal_ref` | The [woman/man] from the reference image, exact same face, hair, skin tone and body, now wearing **[FORMAL OUTFIT]**. Full body, head to shoes, front view, neutral relaxed pose. *(ending)* |
| `{actor}_formal_close` | *(attach `_formal_ref`)* Close-up head-and-shoulders, facing the camera, neutral expression. *(identity line + ending)* |
| `{actor}_formal_medium` | *(attach `_formal_ref`)* Medium shot from the waist up, facing the camera. *(identity line + ending)* |

In a formal story, pair `_formal_close` + `_formal_ref` instead of the casual
pair.

## Step F — story-theme looks (attach `{actor}_ref`)

Extra outfits so each actor looks right for the setting their stories use.
Same three images per look as Step E, same prompts with **[LOOK OUTFIT]** in
place of the formal outfit: `{actor}_{look}_ref` (attach `{actor}_ref`), then
`{actor}_{look}_close` and `{actor}_{look}_medium` (attach `{actor}_{look}_ref`).

| Actor | Look | Themes | [LOOK OUTFIT] |
|---|---|---|---|
| Maya | `v2` new everyday look (replaces the sneakers look for new stories) | all | fitted mustard yellow blazer over a white silk camisole, slim high-waisted dark jeans, tan strappy block-heel sandals showing a nude-pink pedicure, nude-pink almond nails, small gold hoops |
| Maya | `office` | Career | tailored mustard blazer, cream silk blouse, black pencil skirt, nude pointed-toe pumps |
| Maya | `home` | In-law, Sibling, Marriage | soft cream knit sweater, light blue jeans, tan heeled mules |
| Maya | `dinner` | Wedding, Sibling, Marriage | fitted mustard satin midi dress, gold strappy stiletto sandals, gold hoops |
| Vanessa | `office` | Career | sleek black blazer dress, red pointed-toe stiletto pumps |
| Vanessa | `dinner` | Wedding, Sibling, Marriage | red bodycon cocktail dress, red stiletto sandals showing a red pedicure |
| Daniel | `home` | In-law, Sibling, Inheritance | navy cable-knit sweater over a white collared shirt, grey trousers, brown loafers |
| Eleanor | `home` | In-law, Wedding planning | cream silk blouse, camel tailored trousers, pearls, nude kitten-heel slingbacks |
| Richard | `home` | In-law, Sibling, Inheritance | grey wool cardigan over a light blue shirt, dark trousers, brown loafers |
| Chloe | `party` | Wedding, Sibling | sparkly silver sequin mini dress, silver strappy stiletto sandals |
| Chloe | `home` | Sibling, In-law | baby-pink satin shirt and wide-leg trousers, pink heeled mules |
| Ethan | `office` | Career, Marriage | fitted charcoal suit, white shirt, navy tie, black oxfords |
| Ethan | `home` | Marriage, In-law | fitted navy henley, dark jeans, white sneakers |
| Marcus | `home` | Marriage, In-law | fitted black t-shirt, dark jeans, black leather boots |
| Priya | `office` | Career, Landlord | fitted ivory blazer, lavender silk blouse, grey pencil skirt, nude pumps |
| Priya | `home` | In-law, Landlord | lavender embroidered kurta top, white slim trousers, gold heeled sandals |
| Jade | `office` | Career, Marriage | fitted white shirt dress with a thin black belt, black pointed stilettos |
| Tyler | `office` | Sibling, Inheritance, Career | sharp light-grey slim suit, white shirt, no tie, white leather sneakers |
| Sam | `office` | Career, Friendship | coral blazer over a white top, slim black trousers, tan block-heel pumps |
| Sam | `dinner` | Wedding, Marriage | fitted coral satin slip dress, nude strappy stiletto sandals |
| Linda | `home` | In-law, Wedding | elegant burgundy knit twin set, black tailored trousers, burgundy kitten-heel slingbacks |

21 looks × 3 = **63 more images**. Maya's `v2` is made first: change the
outfit **from her existing ref**, never with a new text-only base, or her face
changes. The old sneakers look stays for "The Stolen Pitch" and batch 1.

The live checklist with copy-ready prompts for every image (366 total) is the
Cast Reference Tracker artifact: https://claude.ai/artifact/FmoDcows7SWiVm7HJwoXxH

---

## Cast list

### Existing — do the ★ views only (base refs exist)

| Actor | Description (for prompts that need it) | Formal |
|---|---|---|
| **Maya** (34) | a 34-year-old woman with warm brown skin, curly shoulder-length black hair, mustard yellow denim jacket, white t-shirt, dark blue jeans, white sneakers | optional `maya_formal`: elegant black wrap dress, tan nude heels, rose-gold nails |
| **Vanessa** (32) | a 32-year-old woman, sleek straight platinum blonde hair past her shoulders, high cheekbones, grey eyes, red lipstick, fitted black leather biker jacket, black leather pants, glossy red stiletto heels, red nails, silver hoops | red satin gown, red stiletto heels |
| **Daniel** (55) | a 55-year-old man, short neatly combed silver hair, short trimmed silver beard, navy three-piece suit, white shirt, burgundy tie, brown shoes, silver watch | black tuxedo, black bow tie |
| **Leo** (24) | a 24-year-old man, messy ginger hair, freckles, round black glasses, bright green hoodie, lanyard with blank ID badge, grey cargo pants, white high-tops | navy suit, no tie, glasses |

### New — all steps

| # | Actor | [ACTOR DESCRIPTION] | [FORMAL OUTFIT] |
|---|---|---|---|
| 1 | **Eleanor** | Eleanor: a glamorous 58-year-old white woman, silver-blonde blowout bob, striking cheekbones, sharp disapproving eyes, perfect makeup, pearl necklace, fitted cream sheath dress, nude manicured nails, nude block-heel pumps. | floor-length emerald green satin gown, pearl necklace, gold strappy heels |
| 2 | **Richard** | Richard: a distinguished, handsome 62-year-old white man, salt-and-pepper hair neatly combed back, trimmed grey beard, warm eyes, brown tweed blazer, crisp white shirt, dark trousers, polished brown brogues. | classic black tuxedo, black bow tie |
| 3 | **Chloe** | Chloe: a gorgeous 26-year-old white woman, long glossy strawberry-blonde waves, flawless skin, glossy pink lips, pastel pink fitted mini dress, almond nails painted baby pink, strappy pink stiletto sandals showing a matching pink pedicure. | blush pink satin gown, crystal stiletto sandals |
| 4 | **Ethan** | Ethan: a handsome 32-year-old Latino man, short dark wavy hair, light stubble, warm brown eyes, athletic build, light-blue shirt under a slim navy blazer, grey trousers, brown leather loafers. | navy wedding suit, white shirt, silver tie, black oxfords |
| 5 | **Marcus** | Marcus: a handsome 36-year-old Black man, short fade haircut, neatly trimmed beard, confident charming smile, tall and fit, tailored charcoal suit with an open-collar white shirt, black leather shoes, black watch. | black tuxedo, black bow tie |
| 6 | **Priya** | Priya: a beautiful 28-year-old South Asian woman, long glossy straight black hair, warm brown skin, dark expressive eyes, small gold nose stud, lavender wrap dress, almond nails painted soft rose, gold strappy block-heel sandals showing a matching rose pedicure. | ivory wedding dress, ivory satin heels *(optional 2nd: red-and-gold lehenga, gold heels)* |
| 7 | **Rose** | Rose: an elegant 76-year-old white woman, short styled white hair, gold-rimmed glasses, kind face, floral silk blouse, cream skirt, pearl earrings, pale pink nails, low cream kitten heels. | lilac chiffon dress, pearl necklace, low silver heels |
| 8 | **Frank** | Frank: a 58-year-old white man, heavy build, slicked-back grey hair, ruddy cheeks, smug half-smile, maroon short-sleeve shirt, thin gold chain, grey slacks, brown loafers. | — |
| 9 | **Jade** | Jade: a stunning 27-year-old East Asian woman, sleek black chin-length bob with blunt bangs, winged eyeliner, deep red lips, teal satin midi slip dress, almond nails painted deep wine, black pointed-toe stiletto pumps. | black satin bridesmaid gown, black stilettos |
| 10 | **Tyler** | Tyler: a handsome 30-year-old East Asian man, styled black undercut, clean-shaven, smug grin, white knit polo shirt, camel tailored trousers, white leather sneakers, expensive silver watch. | loud green-and-navy plaid suit, white shirt |
| 11 | **Sam** | Sam: a pretty 29-year-old Latina woman, long wavy dark hair with caramel highlights, warm friendly smile, coral wrap top, white jeans, almond nails painted coral, tan wedge sandals showing a matching coral pedicure, small gold hoop earrings. | coral satin bridesmaid dress, nude strappy heels |
| 12 | **Linda** | Linda: an elegant, beautiful 55-year-old Black woman, short natural grey hair, gold drop earrings, burgundy fitted pencil dress, burgundy manicured nails, burgundy slingback heels. | burgundy floor-length gown, gold slingback heels |

Signature expression worth an extra take: Eleanor `smug`, Chloe `smug`,
Vanessa `shock`, Frank `smug`, Priya `sad`, Maya `smile`, Ethan `shock`,
Marcus `smug`, Rose `smile`.

---

## Totals and order

| Set | Per actor | Count |
|---|---|---|
| Base ref (A) | 1 | 12 |
| Core views (B) | 9 | 12 × 9 + 4 × 8 (existing have `_close`) = 140 |
| Expressions (C) | 5 | 16 × 5 = 80 |
| Hands + shoes (D) | 2 (women) | 10 × 2 = 20 |
| Formal (E) | 3 | 15 × 3 = 45 |
| **Total** | | **≈ 297 images** (free in Flow, ~2 outputs each to pick from) |

Do it in this order so the next stories are never blocked:
1. **Existing four, core views (B)** — the batch-1 stories need them now.
2. **New actors, base refs (A)** — all 12, then line them up side by side and
   change anyone who looks like someone else **before** making their views.
3. **Core views (B)** for Eleanor, Ethan, Chloe, Priya, Marcus, Richard.
4. **Expressions (C)**, then **formal (E)** for the wedding cast.
5. Everyone else; **hands/shoes (D)** last.

## Before saving each image

- Face matches `{actor}_ref` side by side (eyes, nose, jaw, hairline).
- Outfit and colours unchanged (except in Step E).
- One person only, plain background, no text.
- ✦ watermark cropped out.
