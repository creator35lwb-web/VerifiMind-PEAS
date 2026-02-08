# VerifiMind PEAS MCP Server - Demo Video Script

**Duration**: 3-5 minutes  
**Style**: Screen recording with voiceover  
**Audience**: AI builders, developers, entrepreneurs  
**Language**: English (with Chinese subtitles optional)

---

## 🎬 VIDEO STRUCTURE

### INTRO (0:00 - 0:30)

**[SCREEN: VerifiMind logo + tagline]**

**VOICEOVER:**
> "Have you ever had a brilliant idea, asked AI about it, and got an enthusiastic 'Yes, this is amazing!' response? But then you wondered... is AI just telling me what I want to hear?"

**[SCREEN: Show AI chat with overly positive response]**

> "This is the AI hallucination problem. And today, I'm going to show you how VerifiMind PEAS solves it with multi-model validation."

**[SCREEN: Transition to VerifiMind PEAS logo]**

---

### SECTION 1: The Problem (0:30 - 1:00)

**[SCREEN: Split screen showing same question to different AIs]**

**VOICEOVER:**
> "When you ask one AI about your idea, you get one perspective. That AI might be optimistic, pessimistic, or simply hallucinating."

**[SCREEN: Show conflicting AI responses]**

> "What if instead, you could have THREE different AI agents, each with a different specialty, analyze your idea from different angles?"

**[SCREEN: Show RefleXion Trinity diagram - X, Z, CS]**

> "That's exactly what VerifiMind PEAS does. We call it the RefleXion Trinity."

---

### SECTION 2: The Solution - RefleXion Trinity (1:00 - 1:45)

**[SCREEN: Animated diagram of three agents]**

**VOICEOVER:**
> "Meet the three agents:"

**[SCREEN: X Intelligent Agent card]**
> "X Intelligent - powered by Gemini - analyzes innovation potential and market opportunity. Think of X as your strategic advisor."

**[SCREEN: Z Guardian Agent card]**
> "Z Guardian - powered by Claude - reviews ethics and safety. Z is your moral compass, ensuring your idea doesn't harm society."

**[SCREEN: CS Security Agent card]**
> "CS Security - also Claude - validates technical feasibility and security. CS is your technical auditor."

**[SCREEN: Show arrows connecting all three]**
> "Together, they provide a 360-degree validation of your concept."

---

### SECTION 3: Live Demo - MCP Server (1:45 - 3:30)

**[SCREEN: Browser showing https://verifimind.ysenseai.org/health]**

**VOICEOVER:**
> "Our MCP Server is now live at verifimind.ysenseai.org. Let me show you how it works."

**[SCREEN: Show health endpoint response]**
> "The server is healthy and running version 0.2.0."

---

**[SCREEN: Open Claude Desktop or MCP client]**

**VOICEOVER:**
> "To use VerifiMind, you connect your AI assistant via the Model Context Protocol - or MCP."

**[SCREEN: Show MCP configuration]**
```json
{
  "mcpServers": {
    "verifimind-genesis": {
      "url": "https://verifimind.ysenseai.org/mcp"
    }
  }
}
```

> "Once connected, your AI gains access to four powerful tools."

---

**[SCREEN: Show tool list]**

**VOICEOVER:**
> "consult_agent_x for innovation analysis..."
> "consult_agent_z for ethics review..."
> "consult_agent_cs for security validation..."
> "And run_full_trinity for the complete three-agent validation."

---

**[SCREEN: Type a concept into the AI chat]**

**VOICEOVER:**
> "Let's validate a real concept. I'll ask: 'Validate my idea for a meditation app for busy professionals.'"

**[SCREEN: Show AI calling the tools]**

> "Watch as the AI calls each agent..."

**[SCREEN: Show X Agent response]**
> "X Intelligent gives an innovation score of 78 out of 100, highlighting the market opportunity in the wellness space."

**[SCREEN: Show Z Agent response]**
> "Z Guardian raises ethical concerns about positioning meditation as a 'productivity tool' and recommends framing it as 'well-being practice' instead."

**[SCREEN: Show CS Agent response]**
> "CS Security confirms technical feasibility but recommends privacy-first design for sensitive meditation data."

**[SCREEN: Show synthesized result]**

> "The final verdict? PROCEED WITH CAUTION. The idea is viable, but needs refinement based on the ethical and security feedback."

---

### SECTION 4: Why This Matters (3:30 - 4:00)

**[SCREEN: Before/After comparison]**

**VOICEOVER:**
> "Before VerifiMind: You ask one AI, get one biased answer."
> "After VerifiMind: You get multi-perspective validation with transparent reasoning."

**[SCREEN: Cost breakdown]**

> "And the best part? Each validation costs only about $0.003 - that's less than half a cent. X Agent uses Gemini's free tier, so innovation analysis is completely free."

---

### SECTION 5: Call to Action (4:00 - 4:30)

**[SCREEN: GitHub repository]**

**VOICEOVER:**
> "VerifiMind PEAS is completely open source. You can find everything on GitHub."

**[SCREEN: Show links]**
- GitHub: github.com/creator35lwb-web/VerifiMind-PEAS
- Live Server: verifimind.ysenseai.org
- 57 validation reports in the archive

> "We've already validated 57 real concepts, from DeFi protocols to meditation apps."

**[SCREEN: Community invitation]**

> "I'm looking for users and contributors to help build this ecosystem. Try it out, give feedback, and let's make AI validation more reliable together."

---

### OUTRO (4:30 - 5:00)

**[SCREEN: VerifiMind logo with tagline]**

**VOICEOVER:**
> "VerifiMind PEAS - Proof of Ethical AI Synthesis. Because your ideas deserve more than one perspective."

**[SCREEN: End card with links]**
- 🔗 verifimind.ysenseai.org
- 📂 github.com/creator35lwb-web/VerifiMind-PEAS
- 💬 Join the discussion

> "Thanks for watching. Now go validate your ideas!"

**[FADE OUT]**

---

## 📝 PRODUCTION NOTES

### Screen Recordings Needed

1. **Health endpoint** - https://verifimind.ysenseai.org/health
2. **MCP config** - https://verifimind.ysenseai.org/.well-known/mcp-config
3. **Claude Desktop** - MCP configuration screen
4. **Live validation** - Running a concept through the tools
5. **GitHub repo** - Main page and validation archive

### Graphics Needed

1. **VerifiMind logo** - Main branding
2. **RefleXion Trinity diagram** - X, Z, CS agents
3. **Agent cards** - Individual agent descriptions
4. **Cost breakdown** - Visual comparison
5. **Before/After** - Single AI vs Trinity validation

### Voiceover Tips

- **Tone**: Conversational, enthusiastic but not hype-y
- **Pace**: Moderate, allow time for visuals to register
- **Emphasis**: Highlight "multi-model", "three agents", "transparent reasoning"

### Music

- **Style**: Upbeat tech/innovation background
- **Volume**: Low, under voiceover
- **Suggestion**: Royalty-free from Epidemic Sound or Artlist

---

## 🎯 KEY MESSAGES TO CONVEY

1. **Problem**: AI hallucination and single-perspective bias
2. **Solution**: Multi-model, multi-agent validation
3. **How**: RefleXion Trinity (X, Z, CS agents)
4. **Proof**: 57 real validation reports
5. **Access**: Free MCP Server at verifimind.ysenseai.org
6. **Cost**: ~$0.003 per validation (X Agent is FREE)
7. **Action**: Try it, give feedback, contribute

---

## 📊 DEMO CONCEPT SUGGESTIONS

For the live demo, choose one of these relatable concepts:

| Concept | Why It Works |
|---------|--------------|
| Meditation app | Relatable, has ethical angles |
| AI writing assistant | Meta (AI validating AI) |
| Decentralized voting | Technical + ethical complexity |
| Health tracking app | Privacy concerns obvious |
| Educational platform | Social impact clear |

**Recommended**: Meditation app (used in the script) - relatable and shows all three agent perspectives clearly.

---

## ⏱️ TIMING BREAKDOWN

| Section | Duration | Cumulative |
|---------|----------|------------|
| Intro | 0:30 | 0:30 |
| The Problem | 0:30 | 1:00 |
| RefleXion Trinity | 0:45 | 1:45 |
| Live Demo | 1:45 | 3:30 |
| Why This Matters | 0:30 | 4:00 |
| Call to Action | 0:30 | 4:30 |
| Outro | 0:30 | 5:00 |

**Total**: ~5 minutes (can trim to 3 minutes for social media)

---

## 🎥 SHORT VERSION (60 seconds - for social media)

**[0:00-0:10]** Hook: "Is AI just telling you what you want to hear?"

**[0:10-0:25]** Problem + Solution: "VerifiMind uses THREE AI agents to validate your ideas from different angles."

**[0:25-0:45]** Quick demo: Show the three agents analyzing a concept

**[0:45-0:55]** Result: "Multi-perspective validation for less than a cent."

**[0:55-0:60]** CTA: "Try it free at verifimind.ysenseai.org"

---

**Script Version**: 1.0  
**Author**: Manus AI  
**Date**: December 23, 2025
