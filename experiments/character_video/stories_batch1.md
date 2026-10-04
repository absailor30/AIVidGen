# Stories batch 1 — top 3 themes, existing cast only

Cast available: **Maya, Vanessa, Daniel, Leo** (refs from "The Stolen Pitch").
Everyone wears their signature outfit in every shot (the refs lock it):
Maya — mustard denim jacket; Vanessa — black leather, red heels; Daniel — navy
three-piece suit; Leo — green hoodie, glasses.

The four don't look related, so every story is a **blended family**:
Daniel is the stepdad, Vanessa the stepsister, Leo the half-brother (on Daniel's
side). The narration says "stepdad / stepsister" once, early, and viewers accept
it.

Length: ~175–180 words each → 60–75s at the current edge-tts rate (+20%).

Shot types (from `docs/proposals/hybrid-character-lane.md`):
**A** = MiniMax character clip (≤5s, close/medium, two refs per actor) ·
**B** = set still with slow motion · **C** = freeze-frame from an A clip ·
**D** = prop still.

## New library items to make once in Flow (no people)

| Kind | Item | Used in |
|---|---|---|
| Set | `living_room` — warm family living room, sofa, framed photos, evening lamps | 1, 2 |
| Set | `dining_room` — family dinner table set for a celebration, candles | 1, 3 |
| Set | `kitchen` — bright home kitchen, island counter | 2 |
| Set | `bakery` — small cosy bakery kitchen, flour, trays of pastries, morning light | 3 |
| Set | `tv_kitchen` — TV cooking-show studio kitchen with studio lights | 3 |
| Prop | `bank_letter` — bank statement on a table, numbers blurred | 1 |
| Prop | `phone_post` — phone screen showing a social post of a cake, text unreadable | 3 |
| Prop | `house_keys` — house keys and a folded document on a counter | 2 |
| Prop | `deed` — property deed with a signature, text blurred | 2 |
| Prop | `ring_box` — open engagement ring box | 1 |

---

## Story 1 — Wedding & Family Entitlement
### "The Wedding Fund Wasn't Hers"

**Narration (177 words)**

> My mom started a wedding fund for me when I was born. After she passed, my stepdad Daniel kept it safe. Or so I thought.
>
> At Sunday dinner, my stepsister Vanessa held up her hand. A diamond ring. "We're getting married in June," she squealed.
>
> Daniel raised his glass. "And the wedding is paid for. Maya's fund. She's not even dating anyone."
>
> Vanessa smiled at me like she'd already won.
>
> I didn't argue. I just finished my dinner.
>
> Because my brother Leo had sent me a photo that morning. Mom's bank letter. The fund was never Daniel's to give. It was in my name. Only my signature could touch it.
>
> Two weeks later, Vanessa's venue called her. The deposit had bounced.
>
> She stormed into the living room in her heels. "Dad, fix this!"
>
> Daniel turned to me. "Maya. Sign the transfer."
>
> I handed him a folder instead. Mom's will. One line, highlighted: "For Maya. No one else."
>
> He went quiet. Vanessa didn't.
>
> But for the first time, nobody in that room could pretend the money was theirs.

**Shot list**

| # | Narration | Type | Shot |
|---|---|---|---|
| 1 | My mom started a wedding fund… Or so I thought. | B | `living_room`, slow push toward framed family photos |
| 2 | At Sunday dinner… "We're getting married in June." | A | Vanessa, chest up, `dining_room` style ref, holding up her hand to show a ring, delighted smug smile. Nobody looks at the camera. 4s |
| 3 | Daniel raised his glass… "She's not even dating anyone." | A | Daniel, medium, seated at the table, raising a wine glass, proud and dismissive. 4s |
| 4 | Vanessa smiled at me like she'd already won. | C | freeze-frame from #2, slow zoom on her smile |
| 5 | I didn't argue. I just finished my dinner. | A | Maya, close-up at the dinner table, calm, cutting her food, faint knowing look. 4s |
| 6 | Because my brother Leo had sent me a photo… | A | Leo, chest up, `living_room`, holding up his phone screen toward someone, serious, glasses. Phone shows only blurred shapes. 4s |
| 7 | Mom's bank letter… Only my signature could touch it. | D | `bank_letter`, slow pan |
| 8 | Two weeks later, Vanessa's venue called her. The deposit had bounced. | D | `ring_box`, slow push-in |
| 9 | She stormed into the living room… "Dad, fix this!" | A | Vanessa, medium, `living_room`, angry, gesturing, red heels visible. 4s |
| 10 | Daniel turned to me… I handed him a folder… Mom's will… | A | Daniel and Maya two-shot, chest up: Maya hands him a folder, he opens it, his face falls. 5s |
| 11 | He went quiet. Vanessa didn't. But for the first time… | C | freeze-frame from #10 on Daniel, slow zoom |

**Type A: 6 parts (~25 min of L40 with SageAttention).**

---

## Story 2 — In-Law Conflicts (no older woman in the cast yet, so father-in-law + sister-in-law)
### "Whose House Is It?"

**Narration (179 words)**

> When my husband's father lost his apartment, I said he could stay with us. Two weeks, tops.
>
> Daniel arrived with four suitcases. And his daughter, Vanessa.
>
> By the end of the first month, Vanessa had moved into my bedroom. "You two can take the guest room," she said. "It's only fair."
>
> Daniel started telling the neighbours it was his son's house. My husband just shrugged. "Keep the peace, Maya."
>
> My brother-in-law Leo was the only one who looked embarrassed. He'd seen what I had in my drawer.
>
> One morning, I set breakfast on the counter. Next to the coffee, I placed a set of keys and a folded paper.
>
> Daniel picked it up. A copy of the deed. Bought three years before I got married. One name on it. Mine.
>
> Under it, a lease. Rent, due on the first. Or a moving date, Friday.
>
> Vanessa laughed. Then she read the number. Then she stopped laughing.
>
> They were gone by Thursday.
>
> Leo helped them carry the suitcases. On his way out, he turned around and gave me a thumbs up.

**Shot list**

| # | Narration | Type | Shot |
|---|---|---|---|
| 1 | When my husband's father lost his apartment… Two weeks, tops. | B | `living_room`, slow push-in |
| 2 | Daniel arrived with four suitcases. And his daughter, Vanessa. | A | Daniel and Vanessa two-shot, medium, at the front door of a home, suitcases beside them, Vanessa smug, Daniel entitled. Nobody looks at the camera. 4s |
| 3 | Vanessa had moved into my bedroom. "You two can take the guest room…" | A | Vanessa, chest up, lounging in a bright bedroom, arms crossed, condescending smile. 4s |
| 4 | Daniel started telling the neighbours… "Keep the peace, Maya." | C | freeze-frame from #2 on Daniel, slow zoom |
| 5 | My brother-in-law Leo was the only one who looked embarrassed… | A | Leo, close-up, `living_room`, awkward, glancing sideways, adjusting his glasses. 4s |
| 6 | One morning, I set breakfast on the counter… keys and a folded paper. | A | Maya, medium, `kitchen` style ref, calmly placing keys and a folded paper beside a coffee mug, composed. 4s |
| 7 | A copy of the deed… One name on it. Mine. | D | `deed`, slow pan |
| 8 | Under it, a lease. Rent, due on the first. Or a moving date, Friday. | D | `house_keys`, slow push-in |
| 9 | Vanessa laughed. Then she read the number. Then she stopped laughing. | A | Vanessa, close-up, `kitchen`, reading a paper, smirk fading into shock. 4s |
| 10 | They were gone by Thursday. | B | `living_room`, empty, slow pull-back |
| 11 | Leo helped them carry the suitcases… gave me a thumbs up. | A | Leo, medium, at a front door holding a suitcase, turns back and gives a small thumbs up with a grin. 4s |

**Type A: 6 parts (~25 min).**

---

## Story 3 — Sibling Rivalry & Favoritism
### "The Cake She Couldn't Bake"

**Narration (178 words)**

> I've baked every morning since I was nineteen. My little bakery isn't famous, but my honey-lavender cake is.
>
> My stepsister Vanessa has never baked anything in her life.
>
> So imagine my face when her post went viral. My cake. My photo. Her caption: "My secret family recipe."
>
> A TV cooking show called her the next day. They wanted her to bake it live.
>
> I called my stepdad. Daniel sighed. "Let her have this one, Maya. She needs it more than you."
>
> He always said that.
>
> My brother Leo didn't. He asked one question: "Does she know the secret?"
>
> She didn't. Nobody does. I've never written it down.
>
> On the show, the host smiled. "So, Vanessa, what makes it special?"
>
> Vanessa froze. The cake came out flat. Grey. Live, in front of everyone.
>
> The host's producer called me that night. Leo had sent them my baking videos. Four years of them, every morning, the same cake.
>
> Next week, I'm baking it on that show myself.
>
> Daniel called to say he was proud of me.
>
> First time in thirty years.

**Shot list**

| # | Narration | Type | Shot |
|---|---|---|---|
| 1 | I've baked every morning… my honey-lavender cake is. | A | Maya, medium, `bakery` style ref, dusting a cake with icing sugar, content, morning light. Nobody looks at the camera. 4s |
| 2 | My stepsister Vanessa has never baked anything in her life. | A | Vanessa, chest up, lounging on a sofa scrolling her phone, bored, red nails. 4s |
| 3 | So imagine my face when her post went viral… "My secret family recipe." | D | `phone_post`, slow push-in |
| 4 | A TV cooking show called her… bake it live. | C | freeze-frame from #2, slow zoom |
| 5 | I called my stepdad… "She needs it more than you." He always said that. | A | Daniel, chest up, `living_room`, on the phone, tired, dismissive shrug. 4s |
| 6 | My brother Leo didn't… "Does she know the secret?" | A | Leo, close-up, `bakery`, leaning on the counter, eyebrows raised, half smile. 4s |
| 7 | She didn't. Nobody does. I've never written it down. | C | freeze-frame from #1 on Maya |
| 8 | On the show, the host smiled… Vanessa froze. The cake came out flat. | A | Vanessa, medium, `tv_kitchen` style ref, in front of a collapsed grey cake under studio lights, frozen in horror. 5s |
| 9 | The producer called me… Four years of them… | B | `bakery`, slow pan across trays of cakes |
| 10 | Next week, I'm baking it on that show myself. | A | Maya, medium, `tv_kitchen`, confident smile, holding a perfect cake. 4s |
| 11 | Daniel called to say he was proud of me. First time in thirty years. | B | `living_room` at dusk, slow pull-back |

**Type A: 6 parts (~25 min).**

---

## Producing the batch

- **18 type-A parts** in one pod session: ~75–80 min of L40 + ~20 min startup ≈ **$1.40 for all three stories**.
- Every type-A prompt uses the template that worked (`prompts/`), two refs per actor, the set as a **style reference**, "From the very first frame…", "Nobody looks at the camera", no readable text.
- Make the sets and props in Flow first (10 images, free), and crop the ✦ watermark.
- Captions and the AI-content label as before.
