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
| 1 | **Eleanor** (60) | controlling mother / mother-in-law | silver-streaked chin-length bob, pearl necklace, **cream** cardigan · formal: **emerald** dress |
| 2 | **Richard** (64) | father / father-in-law / grandfather | bald, short grey beard, round tortoiseshell glasses, **brown tweed** blazer · formal: black tuxedo |
| 3 | **Chloe** (26) | entitled sister, bridezilla, golden child | long strawberry-blonde waves, **pastel pink** blouse · formal: blush satin gown |
| 4 | **Ethan** (32) | husband / fiancé / groom | short dark-brown hair, light stubble, **light-blue** oxford shirt · formal: **navy** wedding suit |
| 5 | **Marcus** (36) | cheating husband, brother-in-law, smooth villain | Black man, short fade, full trimmed beard, **charcoal** henley · formal: charcoal suit, no tie |
| 6 | **Priya** (28) | narrator #2: bride, daughter-in-law, tenant | South Asian, long straight black hair in a low ponytail, **lavender** blouse · formal: ivory wedding dress / gold-trim lehenga |
| 7 | **Rose** (78) | grandmother, will-maker | short white curls, gold-rimmed glasses, **floral** cardigan, pearl earrings |
| 8 | **Frank** (60) | landlord, greedy uncle | balding with comb-over, heavy build, **maroon** polo, gold chain |
| 9 | **Jade** (27) | affair partner, scheming bridesmaid | East Asian, sleek black bob with blunt bangs, **teal** satin top |
| 10 | **Tyler** (30) | entitled cousin / brother | slicked-back blond hair, smug grin, **white** quarter-zip · formal: loud **plaid** suit |
| 11 | **Sam** (30) | best friend / loyal ally | short auburn pixie cut, freckles, **denim** shirt, small gold hoops |
| 12 | **Linda** (57) | second mother / mother-in-law (wedding stories need two mums) | Black woman, short natural grey hair, gold earrings, **burgundy** blouse · formal: burgundy gown |

Coverage check — every top theme can be cast without duplicates:
- **Wedding:** Priya (bride), Ethan (groom), Eleanor + Linda (mothers), Chloe (sister), Tyler (cousin), Richard (father)
- **In-law:** Maya, Ethan, Eleanor, Marcus (brother-in-law)
- **Sibling:** Maya, Chloe, Tyler, Eleanor, Richard
- **Landlord:** Priya or Maya, Frank, Sam
- **Marriage:** Maya, Marcus, Jade, Sam
- **Career:** Maya, Vanessa, Daniel, Leo
- **Inheritance:** Rose, Daniel (lawyer), Chloe, Tyler, Maya

## 3. Flow production plan (Nano Banana Pro, free)

Per actor: **1 base + 6 views = 7 images** (formal-outfit actors: +2 → 9). Total ≈ 100 images.

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
| `{actor}_emote` | …same… Close-up head-and-shoulders, facing camera, [actor's signature emotion: smug / furious / shocked / tearful]. … |

**Step C — formal outfit (actors marked "formal" only), attach `{actor}_ref`:**
- `{actor}_formal_ref`: "The same [man/woman] from the reference image, exact same face and hair, now wearing [FORMAL OUTFIT]. Full-body, front view, plain light grey studio background…"
- `{actor}_formal_close`: close-up head-and-shoulders from `_formal_ref`.

### Actor descriptions to paste into [ACTOR DESCRIPTION]

1. **Eleanor:** Eleanor: a 60-year-old woman, silver-streaked chin-length straight bob, pale skin, thin lips, sharp disapproving eyes, pearl necklace, cream cable-knit cardigan over a white blouse, beige tailored trousers, low beige heels.
2. **Richard:** Richard: a 64-year-old man, completely bald, short grey beard, round tortoiseshell glasses, kind but tired eyes, brown tweed blazer, white shirt, dark brown trousers, brown brogues.
3. **Chloe:** Chloe: a 26-year-old woman, long wavy strawberry-blonde hair, fair skin, light freckles, glossy pink lips, pastel pink silk blouse, white high-waisted jeans, nude heels, small gold necklace.
4. **Ethan:** Ethan: a 32-year-old man, short neat dark-brown hair, light stubble, hazel eyes, athletic build, light-blue oxford shirt with sleeves rolled up, khaki chinos, white sneakers.
5. **Marcus:** Marcus: a 36-year-old Black man, short fade haircut, full neatly trimmed black beard, confident smile, tall, charcoal grey henley, dark jeans, black leather boots, black watch.
6. **Priya:** Priya: a 28-year-old South Asian woman, long straight black hair in a low ponytail, warm brown skin, dark brown eyes, small gold nose stud, lavender blouse, white trousers, tan flats.
7. **Rose:** Rose: a 78-year-old woman, short white curly hair, gold-rimmed glasses, gentle wrinkled face, floral print cardigan over a cream dress, pearl earrings, walking cane in one hand.
8. **Frank:** Frank: a 60-year-old man, balding with a thin comb-over, heavy build, ruddy cheeks, smug half-smile, maroon polo shirt, thin gold chain, grey slacks, brown loafers.
9. **Jade:** Jade: a 27-year-old East Asian woman, sleek black chin-length bob with blunt bangs, dark winged eyeliner, nude lips, teal satin camisole top, black tailored trousers, black heels.
10. **Tyler:** Tyler: a 30-year-old man, slicked-back blond hair, clean-shaven, smug grin, white quarter-zip pullover, navy chinos, brown loafers, expensive silver watch.
11. **Sam:** Sam: a 30-year-old woman, short auburn pixie cut, freckles, warm friendly smile, light denim shirt with rolled sleeves, black jeans, white sneakers, small gold hoop earrings.
12. **Linda:** Linda: a 57-year-old Black woman, short natural grey hair, elegant, gold drop earrings, burgundy silk blouse, black tailored trousers, black low heels.

Formal outfits:
- Eleanor: floor-length emerald green satin dress, pearl necklace
- Richard: classic black tuxedo, black bow tie
- Chloe: blush pink satin gown
- Ethan: navy wedding suit, white shirt, silver tie
- Marcus: charcoal suit, white shirt, no tie
- Priya: ivory wedding dress (and optionally a red-and-gold lehenga)
- Tyler: loud green-and-navy plaid suit
- Linda: burgundy floor-length gown

### Quality checks before saving
- Face matches `{actor}_ref` (compare side by side).
- **Crop the ✦ watermark** (bottom-right) out of every image — the video model copies it.
- File names exactly as above, one folder per actor. Keep originals; refs are the asset that makes every future story possible.

### Order of work
1. Bases for all 12 (Step A) — compare them side by side; if two look alike, change one's hair or colour before going further.
2. Views (Step B) for the 6 most-needed actors first: **Eleanor, Ethan, Chloe, Priya, Marcus, Richard**.
3. Formal outfits (Step C).
4. Remaining actors.
