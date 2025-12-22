# Simon Willison: HTML Tools Pattern

**Source**: https://simonwillison.net/2025/Dec/10/html-tools/  
**Date**: December 10, 2025  
**Author**: Simon Willison

## Key Points

### What are HTML Tools?

- **Definition**: HTML applications combining HTML, JavaScript, and CSS in a single file
- **Scale**: Simon has built **over 150 of these in the past two years**
- **Method**: Almost all written by LLMs (Claude, ChatGPT, Gemini)

### Core Characteristics

1. **Single file**: Inline JavaScript and CSS in one HTML file
2. **No React**: Avoids build steps, easier to copy/paste
3. **CDN dependencies**: Load libraries from cdnjs or jsdelivr
4. **Keep them small**: A few hundred lines of code

### Development Process

1. **Prototype with Artifacts/Canvas**: Start in ChatGPT, Claude, or Gemini
2. **Switch to coding agents**: Use Claude Code or Codex CLI for complex projects
3. **Host on GitHub Pages**: Self-host for reliability and control

### Why This Matters

- **LLMs can generate complete tools** in minutes
- **No build step** = easier distribution and maintenance
- **Self-hosted** = not dependent on LLM platforms
- **Rapid iteration** = rewrite from scratch takes just minutes

## Relevance to VerifiMind-PEAS

**Potential Threat**:
- If LLMs can generate complete tools instantly, do users need validation methodologies?
- "Vibe coding" (rapid prototyping with LLMs) might replace systematic validation

**Counter-Argument**:
- Simon's tools are **small, single-purpose utilities** (few hundred lines)
- VerifiMind-PEAS targets **complex, multi-stakeholder applications** (thousands of lines)
- HTML tools are for **personal productivity**, not enterprise validation
- No mention of **ethical validation, security assessment, or multi-model orchestration**

**Assessment**: **Low threat**. Different problem space (personal tools vs. enterprise validation).
