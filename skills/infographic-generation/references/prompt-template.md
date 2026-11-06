---
created: "2026-11-04T23:22:13Z"
updated: "2026-11-04T23:22:13Z"
---

# Image-generation prompt: template, defaults and style descriptors

Build one prompt per cluster. Fill each angle-bracket slot and keep every other word as written.

```text
Create a professional infographic. <objective> Visual style: <style descriptor>. Aspect ratio: <aspect ratio>. Communicate the following ideas accurately:
SLIDE CONTENT:
<slide text of every slide in the cluster, in slide order>
PRESENTER NOTES:
<presenter notes of those slides, in the same order>
Render all text exactly as given. Use icons and visual hierarchy. Do not add unspecified statistics or facts.
```

Slots:

- objective: the user's objective text, placed right after the core objective sentence; leave the slot empty when the user gave none.
- style descriptor: the descriptor of the chosen style key below.
- aspect ratio: one of 1:1, 4:3, 3:4, 9:16, 16:9; default 16:9.
- slide content and presenter notes: for a single description, the whole description goes under SLIDE CONTENT and the notes slot reads none.

## Style descriptors

| Key | Descriptor |
|---|---|
| lean_clean (default) | Lean, clean, on white background. Focus more on visual elements than text. No cluttered text. Use simple icons to represent complex ideas. |
| minimalist | Flat design, limited color palette, clean lines |
| isometric | Isometric illustration, precise, tech-focused |
| modern | Clear layout, simple icons, sans-serif fonts, business-friendly |
| editorial | Bold shapes, high-impact, magazine-style |
| geometric | Sharp shapes, balanced composition, abstract |
| corporate | Neutral colors, polished, boardroom-ready |
| flat_ui | Soft gradients, friendly shapes, SaaS/app style |
| sketch | Pencil sketch, hand-drawn lines, brainstorming aesthetic |
| cyberpunk | Neon lights, high contrast, dark, futuristic |
