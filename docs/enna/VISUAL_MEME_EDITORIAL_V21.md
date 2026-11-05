# Enna Visual 2.1 — Meme-first editorial standard
**Status:** production code and licensed-photo previews; social publishing remains an explicit, separate operation.

## Why Visual 2.0 felt flat

It paired a visually pleasant Wikimedia photograph with a relatable but mostly declarative slogan. That's a poster, not automatically a meme. RMIT Vietnam's 2026 research on local meme culture describes parody, exaggeration, fictional chat remixes and dramatic twists: https://www.rmit.edu.vn/news/all-news/2026/mar/can-memes-reveal-how-a-generation-feels-about-gender

Do not transplant other creators' photographs, punchlines, celebrity likenesses, meme templates or viral quotes. Study rhetorical mechanics, produce original workplace humor using licensed photos.

## New production brief (3 original meme formats per batch)

1. **Reaction image:** the actual picture provides the answer to a ridiculous office setup; keep text short and never describe an action not visible. In the actual `Cat on laptop yawning.jpg` preview, the cat's **back is shown while it sits on the laptop**; yawning is **not visible**. We corrected the story to: **"SẾP: SAO CHƯA GỬI FILE?" → "DẠ FILE ĐANG BỊ GIỮ LÀM CON TIN Ạ."**
2. **Ironic contrast:** two concrete events within the same workday. Example: **"08:59 — CÀ PHÊ CÒN NÓNG" → "10:30 — CÀ PHÊ XIN NGHỈ VIỆC TRƯỚC TÔI."**
3. **Fictional chat:** original dialogue bubbles visibly labeled `ĐOẠN CHAT GIẢ LẬP`. Example: **"08:30: Nay em làm ba việc" → "08:35: 9h họp về ba việc" → "ỦA RỒI BA VIỆC NÀY LÀM TRONG GIỜ HỌP HẢ SẾP?"**. Never pretend it's an employee's real chat screenshot.

## Quality gates

- The setup must be concrete; a second beat must change expectation. Photo must add the joke, not merely decorate the text.
- Reject corporate motivational filler, generic sharing requests, self-promotional slogans, identifiable people/brands, links, harassment and screenshots of real private chat.
- Reject copy claiming any action explicitly marked as **not visible** after source review (e.g. yawning for the cat-back photo).
- The Groq writer can propose 3 variants in one API call; a deterministic gate keeps only variants meeting the source's selected comic device and physical typography limits. Failure reverts to manually written scenarios.
- Pass/fail is **structural**, not a prediction of laughter, Gen Z preference or algorithmic reach. No fabricated performance numbers. Images stay `DRAFT_REQUIRES_HUMAN_REVIEW`.
- Review 3 originals in a contact sheet at phone thumbnail size; reject if the image changes neither the meaning nor the punchline. Separate visually interesting from genuinely amusing.
- After human review, use one or two photos in existing upcoming schedule slots, preserve UUID/time, measure real impressions, shares, saves and comments after actual verified publication. Never schedule a duplicate or claim a pending post is public.

## Technical paths
- `scripts/enna_visual_source_bank.json`: 8 original fictional setups, chosen visual mechanism, image-truth restrictions.
- `scripts/enna_visual_factory.py`: rotate one chat, one reaction and one contrast; photoreal backgrounds, no AI faces.
- `growth/visual_comedy_gate.py`: minimum contrast/specificity and rejected unobserved actions.
- `growth/visual_humor_editor.py`: Groq candidates + safety/structural filter; no spending outside existing credentials.
- `.github/workflows/enna-visual-factory.yml`: push CI produces drafts, scheduled workflows can register **review-only** media in Supabase; no social posts.


## Production-path quality incident, 06 November 2026

An authenticated Groq smoke test produced three captions that passed the initial *mechanical* checks but failed human visual review. Notable failures were broken cat dialogue, nonsensical coffee anthropomorphism, and generic scheduling copy using the English word "team". All three were marked `rejected` in Supabase media library; **none was published**.

Lessons now encoded as hard regression fixtures:
- `growth/visual_comedy_gate.py` requires each punchline to preserve an explicit source-specific twist anchor, not merely mention coffee, office, or meetings.
- Broken quotation marks, certain generic AI filler and claims about unseen photo actions are rejected.
- `tests/test_enna_visual_comedy.py` includes the *actual failed outputs*, so a refactor cannot silently weaken these controls.
- A structurally acceptable copy is still not proof of human humor or Gen Z social engagement. Where the model fails, the curated human baseline is kept.

Three useful contrasts: **the cat actually blocks the keyboard** → file is "held hostage"; **a morning coffee** → the drink "resigns" before the employee; **three planned tasks** → the 09:00 meeting consumes the time needed to complete them. These are fictional jokes, not real incidents.

Publishing remains human-review-only; Metricool schedule is unaffected by this engineering QA.


## Additional live test and stricter default

A second official-credentials smoke test confirmed the model could produce more than one candidate, but one accepted coffee variant still said "ngừng ngơi" and contained several explanatory sentences. That image was marked `rejected` in Supabase. This demonstrates why keyword-level humor checks alone cannot establish creative quality.

The factory now **always renders the human-curated, photo-verified story**. Optional Groq variants are saved as **unapproved, private review suggestions** in rights evidence, never automatically replacing the visible meme or being scheduled. This remains true if they pass keyword and structure tests. Multiple sentences, awkward English `vs/team` and known stilted language are rejected before review. Future use of an AI option requires separate human editorial approval.

Latest proof is the GitHub Actions draft artifact; no Threads, Facebook or Instagram posts are caused by these smoke tests.
