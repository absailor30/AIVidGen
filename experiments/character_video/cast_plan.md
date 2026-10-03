# Twisty! StoryVault — recurring cast plan

## 1. What the data says (short lane, YouTube)

Median views at day 3 per theme (from `story_state` + `story_metrics`, Oct 3 2026):

| Theme | Stories | Median day-3 views | Best video | Median % watched |
|---|---|---|---|---|
| Wedding & Family Entitlement | 37 | **304** | 976 | 60% |
| In-Law Conflicts | 21 | **301** | 1,255 | 66% |
| Sibling Rivalry & Favoritism | 22 | 202 | 723 | 73% |
| Landlord / Tenant Dispute | 15 | 198 | 553 | 64% |
| Marriage & Infidelity | 36 | 175 | 776 | 65% |
| Career Sabotage / Workplace | 29 | 164 | 778 | 72% |
| Family Inheritance | 28 | 120 | 1,152 | 63% |
| Friendship Betrayal & Glow-Up | 18 | 105 | 921 | 51% |
| Business Partnership Betrayal | 16 | 39 | 304 | 59% |

Long lane is too small to read (2–8 videos per theme, single-digit views).

**Takeaways**
- **Family is the channel.** Wedding, in-law, sibling and inheritance stories are 4 of the top 7, and most of the top-30 videos.
- The same roles keep coming back: **narrator (bride / daughter-in-law / sister)**, **controlling mother / mother-in-law**, **complicit husband / fiancé**, **entitled sister**, **entitled cousin**, **father**, **grandmother**, **landlord**, **affair partner**, **boss / rival coworker**.
- Business Partnership Betrayal is the clear loser — no cast needed for it.

## 2. The idea: a repertory cast

Not one character per story — a fixed company of **16 "actors"** who play different roles across stories (like a TV troupe). The narration gives them a new name each story; the faces stay. Each actor has a **casual** and a **formal** outfit, so the same face works for a kitchen argument and a wedding.

Design rules (so MiniMax never mixes them up): every actor differs in **age, hair colour/shape and signature outfit colour**. No two share a colour. All fictional adults.

### Existing (keep)
| Actor | Plays | Look |
|---|---|---|
| **Maya** (34) | narrator / heroine | curly shoulder-length black hair, mustard denim jacket |
| **Vanessa** (32) | villain: rival, entitled sister, mistress | sleek platinum hair, red lipstick, black leather |
| **Daniel** (55) | boss, father, lawyer, judge | silver hair + beard, navy three-piece suit |
| **Leo** (24) | ally, brother, assistant, IT guy | messy ginger hair, glasses, green hoodie |

### New (12)
| # | Actor | Plays | Signature look |
|---|---|---|---|
| 1 | **Eleanor** (58) | controlling mother / mother-in-law | white, glamorous silver-blonde blowout bob, pearls, **cream** fitted sheath dress, nude block-heel pumps · formal: **emerald** gown |
| 2 | **Richard** (62) | father / father-in-law | white, distinguished, salt-and-pepper hair, trimmed grey beard, **brown tweed** blazer · formal: black tuxedo |
| 3 | **Chloe** (26) | entitled sister, bridezilla, golden child | white, long strawberry-blonde waves, **pastel pink** mini dress, strappy pink stiletto sandals · formal: blush satin gown |
| 4 | **Ethan** (32) | husband / fiancé / groom | Latino, handsome, short dark wavy hair, light stubble, **light-blue** shirt + navy blazer · formal: **navy** wedding suit |
| 5 | **Marcus** (36) | cheating husband, brother-in-law, smooth villain | Black, handsome, short fade, trimmed beard, **charcoal** suit, open collar · formal: charcoal tux |
| 6 | **Priya** (28) | narrator #2: bride, daughter-in-law, tenant | South Asian, long glossy black hair, **lavender** wrap dress, gold strappy block heels · formal: ivory wedding dress / red-and-gold lehenga |
| 7 | **Rose** (76) | grandmother, will-maker | white, elegant short white hair, gold-rimmed glasses, **floral** silk blouse, low kitten heels |
| 8 | **Frank** (58) | landlord, greedy uncle | white, heavy build, slicked grey hair, smug, **maroon** shirt, gold chain (deliberately unappealing — the role needs it) |
| 9 | **Jade** (27) | affair partner, scheming bridesmaid | East Asian, sleek black bob with bangs, **teal** satin slip dress, black pointed stilettos |
| 10 | **Tyler** (30) | entitled cousin / brother | East Asian, handsome, styled undercut, smug grin, **white** knit polo + camel trousers · formal: loud **plaid** suit |
| 11 | **Sam** (29) | best friend / loyal ally | Latina, wavy caramel-highlighted hair, **coral** wrap top, white jeans, tan wedge sandals |
| 12 | **Linda** (55) | second mother / mother-in-law | Black, elegant, short natural grey hair, gold earrings, **burgundy** pencil dress, burgundy slingback heels · formal: burgundy gown |

**Maya** keeps her white sneakers in the existing refs (the "normal girl" contrast to Vanessa). If you want her in heels too, make a `maya_formal` set (tan nude heels) rather than replacing her refs — the finished story depends on them.

### Style rules
- **Women:** attractive, glamorous, polished; heels in almost every look (stilettos, block heels, strappy sandals, slingbacks, wedges, kitten heels for the oldest), manicured almond nails, and a matching pedicure whenever toes show. Exceptions only when a scene calls for it (gym, bed, hospital).
- **Men:** handsome, well-groomed, professional (blazers, suits, tailored shirts) unless the role needs otherwise (Frank, Leo).
- **Everyone is clearly an adult** (youngest 24). Keep descriptions adult — no "girlish", "petite teen" or school wear.
- **Platform-safe wardrobe:** dresses, skirts and heels are fine; no lingerie, swimwear or see-through outfits. Shorts with sexualised framing get limited reach or age-restricted, and that hits a channel posting daily.
- **Feet and hands:** good-looking in shots where they matter to the story (heels walking away, nails tapping the desk). Don't add foot-focused shots for their own sake — on Shorts that pulls in an off-target audience and can get flagged.

Coverage check — every top theme can be cast without duplicates:
- **Wedding:** Priya (bride), Ethan (groom), Eleanor + Linda (mothers), Chloe (sister), Tyler (cousin), Richard (father)
- **In-law:** Maya, Ethan, Eleanor, Marcus (brother-in-law)
- **Sibling:** Maya, Chloe, Tyler, Eleanor, Richard
- **Landlord:** Priya or Maya, Frank, Sam
- **Marriage:** Maya, Marcus, Jade, Sam
- **Career:** Maya, Vanessa, Daniel, Leo
- **Inheritance:** Rose, Daniel (lawyer), Chloe, Tyler, Maya

## 3. Flow production plan (Nano Banana Pro, free)

Per actor: **1 base + 6 views (+ shoes and hands for women) = 7–9 images** (formal-outfit actors: +2 → 9). Total ≈ 100 images.

**Step A — base full-body (text only, no reference).** Portrait 9:16. Template:
```
Full-body character reference photo, front view, neutral relaxed standing pose, arms at sides. Plain light grey studio background, soft even lighting. [ACTOR DESCRIPTION]. Photorealistic, sharp focus, natural skin texture, consistent proportions. No text, no logos.
```
Generate 4, pick the best, save as `{actor}_ref`. Every other image is made **from this one** (attach it each time).

**Step B — views (attach `{actor}_ref`).**
| File | Prompt |
|---|---|
| `{actor}_close` | The [man/woman] from the reference image, exact same face, hair and outfit. Close-up head-and-shoulders portrait, facing camera directly, neutral expression. Plain light grey studio background, soft even lighting. Photorealistic, sharp focus, natural skin texture. |
| `{actor}_34` | …same… Close-up head-and-shoulders, head turned three-quarters to the left, eyes slightly off camera. … |
| `{actor}_profile` | …same… Close-up side profile, head turned fully to the right. … |
| `{actor}_medium` | …same… Medium shot from the waist up, standing, facing camera, arms relaxed. … |
| `{actor}_back` | …same… Full body seen from behind, walking away, back to camera. … |
| `{actor}_shoes` | (women) …same… Close-up of her feet and shoes, standing on a light grey floor, showing the exact same heels [and pedicure]. Product-photo style. |
| `{actor}_hands` | …same… Close-up of her hands resting together, showing the exact same manicure and rings. |
| `{actor}_emote` | …same… Close-up head-and-shoulders, facing camera, [actor's signature emotion: smug / furious / shocked / tearful]. … |

**Step C — formal outfit (actors marked "formal" only), attach `{actor}_ref`:**
- `{actor}_formal_ref`: "The same [man/woman] from the reference image, exact same face and hair, now wearing [FORMAL OUTFIT]. Full-body, front view, plain light grey studio background…"
- `{actor}_formal_close`: close-up head-and-shoulders from `_formal_ref`.

### Actor descriptions to paste into [ACTOR DESCRIPTION]

1. **Eleanor:** Eleanor: a glamorous 58-year-old white woman, silver-blonde blowout bob, striking cheekbones, sharp disapproving eyes, perfect makeup, pearl necklace, fitted cream sheath dress, nude manicured nails, nude block-heel pumps.
2. **Richard:** Richard: a distinguished, handsome 62-year-old white man, salt-and-pepper hair neatly combed back, trimmed grey beard, warm eyes, brown tweed blazer, crisp white shirt, dark trousers, polished brown brogues.
3. **Chloe:** Chloe: a gorgeous 26-year-old white woman, long glossy strawberry-blonde waves, flawless skin, glossy pink lips, pastel pink fitted mini dress, almond nails painted baby pink, strappy pink stiletto sandals showing a matching pink pedicure.
4. **Ethan:** Ethan: a handsome 32-year-old Latino man, short dark wavy hair, light stubble, warm brown eyes, athletic build, light-blue shirt under a slim navy blazer, grey trousers, brown leather loafers.
5. **Marcus:** Marcus: a handsome 36-year-old Black man, short fade haircut, neatly trimmed beard, confident charming smile, tall and fit, tailored charcoal suit with an open-collar white shirt, black leather shoes, black watch.
6. **Priya:** Priya: a beautiful 28-year-old South Asian woman, long glossy straight black hair, warm brown skin, dark expressive eyes, small gold nose stud, lavender wrap dress, almond nails painted soft rose, gold strappy block-heel sandals showing a matching rose pedicure.
7. **Rose:** Rose: an elegant 76-year-old white woman, short styled white hair, gold-rimmed glasses, kind face, floral silk blouse, cream skirt, pearl earrings, pale pink nails, low cream kitten heels.
8. **Frank:** Frank: a 58-year-old white man, heavy build, slicked-back grey hair, ruddy cheeks, smug half-smile, maroon short-sleeve shirt, thin gold chain, grey slacks, brown loafers.
9. **Jade:** Jade: a stunning 27-year-old East Asian woman, sleek black chin-length bob with blunt bangs, winged eyeliner, deep red lips, teal satin midi slip dress, almond nails painted deep wine, black pointed-toe stiletto pumps.
10. **Tyler:** Tyler: a handsome 30-year-old East Asian man, styled black undercut, clean-shaven, smug grin, white knit polo shirt, camel tailored trousers, white leather sneakers, expensive silver watch.
11. **Sam:** Sam: a pretty 29-year-old Latina woman, long wavy dark hair with caramel highlights, warm friendly smile, coral wrap top, white jeans, almond nails painted coral, tan wedge sandals showing a matching coral pedicure, small gold hoop earrings.
12. **Linda:** Linda: an elegant, beautiful 55-year-old Black woman, short natural grey hair, gold drop earrings, burgundy fitted pencil dress, burgundy manicured nails, burgundy slingback heels.

Formal outfits:
- Eleanor: floor-length emerald green satin gown, pearl necklace, gold strappy heels
- Richard: classic black tuxedo, black bow tie
- Chloe: blush pink satin gown, crystal stiletto sandals
- Ethan: navy wedding suit, white shirt, silver tie, black oxfords
- Marcus: charcoal suit, white shirt, no tie
- Priya: ivory wedding dress with ivory satin heels (and optionally a red-and-gold lehenga with gold heels)
- Tyler: loud green-and-navy plaid suit
- Linda: burgundy floor-length gown, gold slingback heels

### Quality checks before saving
- Face matches `{actor}_ref` (compare side by side).
- **Crop the ✦ watermark** (bottom-right) out of every image — the video model copies it.
- File names exactly as above, one folder per actor. Keep originals; refs are the asset that makes every future story possible.

### Order of work
1. Bases for all 12 (Step A) — compare them side by side; if two look alike, change one's hair or colour before going further.
2. Views (Step B) for the 6 most-needed actors first: **Eleanor, Ethan, Chloe, Priya, Marcus, Richard**.
3. Formal outfits (Step C).
4. Remaining actors.
