# Agent Instructions (Claude Code)

When the user asks to edit raw footage or direct a video (Instagram Reels, TikTok, YouTube Shorts, podcast, or talking head):
1. Read and follow `SKILL.md` in this directory as the master entrypoint.
2. Probe footage and generate an autonomous editing plan using `scripts/director.py`.
3. Follow the **MANDATORY PREVIEW-FIRST WORKFLOW**: Always generate keyframe stills or a proxy video (`scripts/preview.py`) before final rendering.
4. Detailed module references:
   - Core Workflow: `references/01-core-workflow.md`
   - Footage Understanding: `references/02-footage-understanding.md`
   - Semantic Transcription: `references/03-transcription-semantics.md`
   - Creative Direction: `references/04-creative-direction.md`
   - Safe Zones & Typography: `references/05-typography-safezones.md`
   - Infographics & B-Roll: `references/06-motion-graphics-infographics.md` & `references/07-broll-visual-generation.md`
   - 82+ Effects Reference: `references/08-effects-catalog-65.md`
   - Sound Design & Zero SFX: `references/09-sound-design.md`
   - Preview Approval Gate: `references/10-preview-first-workflow.md`
   - Cross-Platform & Debugging: `references/11-cross-platform-troubleshooting.md`
5. Style presets are stored in `presets/style-1.json` through `presets/style-13.json`.
