# VerifiMind-PEAS Documentation Best Practices

**A Comprehensive Guide to LLM-Optimized Documentation and Context Management**

**Version**: 1.0  
**Last Updated**: December 11, 2025  
**Author**: Manus AI (CTO - T)

---

## Table of Contents

1. [Introduction: The Missing Piece](#introduction-the-missing-piece)
2. [The Core Problem: Documentation for Humans vs. LLMs](#the-core-problem-documentation-for-humans-vs-llms)
3. [The Solution: Three-Layer Documentation Architecture](#the-solution-three-layer-documentation-architecture)
4. [Layer 1: Genesis Master Prompt (Project Memory)](#layer-1-genesis-master-prompt-project-memory)
5. [Layer 2: Module Documentation (Deep Context)](#layer-2-module-documentation-deep-context)
6. [Layer 3: Session Notes (Iteration History)](#layer-3-session-notes-iteration-history)
7. [The Complete Workflow: Daily and Multi-Model](#the-complete-workflow-daily-and-multi-model)
8. [Platform-Specific Best Practices](#platform-specific-best-practices)
9. [Templates and Resources](#templates-and-resources)
10. [Conclusion: Building with Wisdom and Memory](#conclusion-building-with-wisdom-and-memory)

---

## Introduction: The Missing Piece

**Welcome to the VerifiMind-PEAS Documentation Best Practices Guide!**

This guide addresses a critical gap in modern AI development: **how to manage documentation and context across multiple LLM sessions and platforms**.

**Who is this guide for?**
- Knowledge creators building complex projects with AI
- Researchers developing new concepts with multiple LLMs
- Founders validating business ideas across different AI platforms
- Anyone working with AI over extended periods (days, weeks, months)

**What you'll learn**:
- A systematic framework for LLM-optimized documentation
- How to create and maintain a Genesis Master Prompt
- How to structure documentation for multi-model workflows
- Platform-specific best practices for Claude, GPT-4, Gemini, Perplexity, and Manus AI

**This is a core component of the VerifiMind-PEAS methodology.**

---

## The Core Problem: Documentation for Humans vs. LLMs

### **The Challenge**

Most documentation is written for humans, but LLMs need a different structure to be effective.

| **Human-Optimized Documentation** | **LLM-Optimized Documentation** |
|---------------------------------|-------------------------------|
| Long-form prose                 | Structured data (Markdown, YAML) |
| Visual formatting (bold, colors) | Explicit context (no assumptions) |
| Hierarchical structure (chapters) | Modular chunks (self-contained files) |
| Assumes reader has context      | Clear relationships (links) |
| Optimized for linear reading    | Version-aware (iteration history) |

### **The Multi-Model Dilemma**

Your workflow uses multiple LLMs (X, Z, CS agents) on different platforms. Each session starts with **zero context**. This forces you to manually re-explain everything, leading to inconsistency and wasted time.

**What's Needed**: A platform-agnostic documentation system that preserves context across all sessions.

---

## The Solution: Three-Layer Documentation Architecture

We propose a three-layer architecture for LLM-optimized documentation:

```
Layer 1: Genesis Master Prompt (Project Memory)
         ↓
Layer 2: Module Documentation (Deep Context)
         ↓
Layer 3: Session Notes (Iteration History)
```

This structure ensures that you have a **single source of truth** (Genesis Master Prompt), **deep-dive context** (Module Documentation), and a **complete audit trail** (Session Notes).

---

## Layer 1: Genesis Master Prompt (Project Memory)

### **Purpose**

The **Genesis Master Prompt** is your **project memory** - a single, living document that contains the complete, up-to-date context of your project.

### **Structure**

See `templates/genesis_master_prompt_template.md` for a copy-paste ready template.

### **Best Practices**

1. **Update after every session**: Keep it current.
2. **Version it**: `genesis_master_prompt_v1.1.md`
3. **Keep it concise**: 5,000-10,000 words max.
4. **Link to detailed docs**: Don't duplicate everything.
5. **Store in Git**: For version control and backup.

### **How to Use with LLMs**

**Start every session by pasting the Genesis Master Prompt** into the conversation. This gives the LLM immediate, complete context.

---

## Layer 2: Module Documentation (Deep Context)

### **Purpose**

**Module Documentation** provides **deep-dive context** for specific features, concepts, or components.

### **Structure**

Organize your documentation into a clear folder structure:

```
/docs
├── /core_methodology
├── /guides
├── /case_studies
└── /white_paper
```

### **Best Practices**

1. **One concept per file**: Modular and self-contained.
2. **Use Markdown**: LLM-friendly and human-readable.
3. **Include metadata**: Author, date, version.
4. **Link between files**: Create a knowledge graph.
5. **Store in Git**: For version control and collaboration.

### **How to Use with LLMs**

When you need deep context on a specific topic, paste the content of the relevant file into the conversation.

---

## Layer 3: Session Notes (Iteration History)

### **Purpose**

**Session Notes** capture your **iteration history** - what you discussed, decided, and learned in each LLM session.

### **Structure**

See `templates/session_notes_template.md` for a copy-paste ready template.

### **Best Practices**

1. **Create after every session**: Capture while fresh.
2. **Name with date and topic**: `2025-12-11_oil_palm_validation.md`
3. **Link to Genesis Master Prompt version**: Track which version you used.
4. **Store in Git**: For a complete audit trail.
5. **Update Genesis Master Prompt**: Incorporate key insights.

### **How to Use with LLMs**

When you want to reference a previous session, paste the content of the session notes into the conversation.

---

## The Complete Workflow: Daily and Multi-Model

### **Daily Workflow**

1. **Morning**: `git pull`, open Genesis Master Prompt, start LLM session by pasting it.
2. **During Work**: Reference Module Documentation as needed, take notes.
3. **Evening**: Create Session Notes, update Genesis Master Prompt, `git commit`, `git push`.

### **Multi-Model Workflow**

1. **X Agent (Innovation)**: Start with Genesis Master Prompt, save findings to Session Notes.
2. **Z Agent (Ethics)**: Start with Genesis Master Prompt + X Agent findings, save assessment to Session Notes.
3. **CS Agent (Security)**: Start with Genesis Master Prompt + X & Z findings, save assessment to Session Notes.
4. **Orchestrator (Synthesis)**: Start with Genesis Master Prompt + all findings, make decision, update Genesis Master Prompt.

---

## Platform-Specific Best Practices

| **Platform** | **Strengths** | **Best Practices** |
|--------------|---------------|--------------------|
| **Claude** | Long context (200K), Projects feature | Use Projects for persistent context, upload all docs |
| **GPT-4** | Fast, structured output, Custom GPTs | Create Custom GPT with Genesis Master Prompt in instructions |
| **Gemini** | 2M token context, multi-modal | Paste entire Genesis Master Prompt at start |
| **Perplexity** | Real-time web search, citations | Use for X Agent research, paste Genesis Master Prompt for context |
| **Manus AI** | Session persistence, GitHub integration, tools | Use for Orchestrator role, leverage session history |

---

## Templates and Resources

- `templates/genesis_master_prompt_template.md`
- `templates/session_notes_template.md`
- `templates/module_documentation_template.md`

---

## Conclusion: Building with Wisdom and Memory

This documentation framework is the **missing piece** of the VerifiMind-PEAS methodology. It solves the critical problem of context persistence in multi-model AI workflows.

By adopting this framework, you will:
- ✅ **Save time** by eliminating manual context re-entry
- ✅ **Improve quality** by ensuring consistent context
- ✅ **Enhance collaboration** with a single source of truth
- ✅ **Create a complete audit trail** of your project's evolution

**This is how you build with wisdom and memory.**
