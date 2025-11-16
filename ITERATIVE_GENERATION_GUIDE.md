# VerifiMind Iterative Code Generation Guide

## 🎯 What is Iterative Generation?

**Iterative Generation** implements the true "RefleXion" concept - your code doesn't just get generated once, it gets **continuously improved** through self-reflection and iteration until it meets quality standards.

### The RefleXion Pattern

```
┌─────────────────────────────────────────────────────────────┐
│  Iteration 1: Generate v1.0 → Reflect → Find 15 issues     │
│  Iteration 2: Generate v1.1 → Reflect → Find 8 issues      │
│  Iteration 3: Generate v1.2 → Reflect → Find 2 issues ✓    │
└─────────────────────────────────────────────────────────────┘
```

Each iteration:
1. **Generates** code based on spec
2. **Reflects** on quality, security, compliance, performance
3. **Identifies** specific improvements needed
4. **Applies** improvements to spec for next iteration
5. **Repeats** until quality threshold met

---

## 🚀 Quick Start

### Run the Demo

```bash
# Run the iterative generation demo
python demo_iterative_generation.py
```

This will:
- Generate a kids meditation app
- Run through multiple iterations
- Save each version separately
- Show improvement metrics
- Create comparison reports

### Basic Usage

```python
from src.generation.iterative_generator import IterativeCodeGenerationEngine
from src.generation.core_generator import AppSpecification
from src.llm.llm_provider import LLMProvider

# Initialize
llm = LLMProvider(config)
generator = IterativeCodeGenerationEngine(
    config=config,
    llm_provider=llm,
    max_iterations=3,        # Maximum 3 iterations
    quality_threshold=85     # Target 85/100 quality
)

# Generate with iterations
generated_app, history = await generator.generate_with_iterations(
    spec=your_app_spec,
    output_dir="output"
)

# Check improvement
print(f"Initial: {history.initial_score}/100")
print(f"Final: {history.final_score}/100")
print(f"Improvement: +{history.improvement_percentage}%")
```

---

## 📊 What Gets Analyzed

### The Reflection Agent analyzes 5 dimensions:

#### 1. **Code Quality** (30% weight)
- Code structure and organization
- Error handling completeness
- Code duplication (DRY principle)
- Debug statements in production code
- Hardcoded values
- Documentation quality

#### 2. **Security** (30% weight)
- SQL injection vulnerabilities
- XSS (Cross-Site Scripting) risks
- Missing authentication/authorization
- Password handling without hashing
- CORS misconfigurations
- Sensitive data exposure

#### 3. **Compliance** (20% weight)
- GDPR requirements (data export, deletion, consent)
- COPPA compliance (for children's apps)
- Privacy policy implementation
- Audit logging
- Data retention policies

#### 4. **Performance** (20% weight)
- Database query optimization
- Missing indexes on foreign keys
- SELECT * queries
- Pagination missing
- N+1 query problems
- Caching opportunities

#### 5. **Best Practices**
- README quality
- Environment variable examples
- API documentation
- Deployment readiness
- Framework conventions

---

## 🔄 How Iteration Works

### Example: Kids Meditation App

**Iteration 1 (v1.0):**
```
Generated initial code
Issues found:
  🚨 CRITICAL: Password handling without hashing
  ⚠️  HIGH: Missing COPPA compliance features
  ⚠️  HIGH: No parental consent workflow
  📋 MEDIUM: Missing indexes on foreign keys

Overall Score: 62/100
Decision: ITERATE ✓
```

**Iteration 2 (v1.1):**
```
Applied improvements:
  ✅ Added bcrypt password hashing
  ✅ Implemented age verification
  ✅ Added parental consent workflow
  ✅ Added indexes on child_id, parent_id

Issues found:
  📋 MEDIUM: Missing audit logging
  📋 MEDIUM: No rate limiting on auth endpoints

Overall Score: 78/100
Decision: ITERATE ✓
```

**Iteration 3 (v1.2):**
```
Applied improvements:
  ✅ Added audit logging for sensitive operations
  ✅ Implemented rate limiting
  ✅ Enhanced error handling

Issues found:
  🟢 LOW: README could be more comprehensive

Overall Score: 92/100
Decision: COMPLETE ✅
```

---

## 📁 Output Structure

After running iterative generation:

```
output/
└── KidsCalmMind/
    ├── versions/
    │   ├── v1.0/                           # Initial version
    │   │   ├── src/
    │   │   ├── database/
    │   │   ├── docs/
    │   │   ├── README.md
    │   │   └── REFLECTION_REPORT_v1.0.json
    │   ├── v1.1/                           # Improved version
    │   │   ├── src/
    │   │   ├── database/
    │   │   ├── docs/
    │   │   ├── README.md
    │   │   └── REFLECTION_REPORT_v1.1.json
    │   └── v1.2/                           # Final version
    │       ├── src/
    │       ├── database/
    │       ├── docs/
    │       ├── README.md
    │       └── REFLECTION_REPORT_v1.2.json
    ├── verifimind_history.json             # Complete history (JSON)
    └── ITERATION_HISTORY.md                # Readable comparison report
```

---

## 📄 Understanding the Reports

### Reflection Report (JSON)

Each version has a `REFLECTION_REPORT_vX.X.json`:

```json
{
  "iteration": 2,
  "version": "v1.1",
  "scores": {
    "overall": 78.5,
    "quality": 85.0,
    "security": 90.0,
    "compliance": 70.0,
    "performance": 75.0
  },
  "issue_counts": {
    "security": 0,
    "quality": 3,
    "compliance": 2,
    "performance": 1
  },
  "critical_issues": 0,
  "improvement_suggestions": [
    "Add audit logging for sensitive operations",
    "Implement rate limiting on authentication endpoints",
    ...
  ],
  "should_iterate": true
}
```

### Iteration History (Markdown)

`ITERATION_HISTORY.md` provides a human-readable comparison:

```markdown
# VerifiMind Iteration History - KidsCalmMind

## Summary
- Total Iterations: 3
- Duration: 45.2s
- Quality Improvement: 62.0 → 92.0 (+48.4%)

## Version History

### v1.0 (Iteration 1)
**Scores**: Overall: 62.0/100
**Issues**: Total: 15, Critical: 2

### v1.1 (Iteration 2)
**Scores**: Overall: 78.5/100
**Issues**: Total: 6, Critical: 0
**Improvements Applied**:
- Added bcrypt password hashing
- Implemented COPPA compliance features

### v1.2 (Iteration 3)
**Scores**: Overall: 92.0/100
**Issues**: Total: 1, Critical: 0
...
```

### History JSON

`verifimind_history.json` contains complete structured data:

```json
{
  "app_id": "app-20250101-123456",
  "app_name": "KidsCalmMind",
  "total_iterations": 3,
  "metrics": {
    "initial_score": 62.0,
    "final_score": 92.0,
    "improvement_percentage": 48.4
  },
  "versions": [...]
}
```

---

## ⚙️ Configuration Options

### Max Iterations

```python
generator = IterativeCodeGenerationEngine(
    config=config,
    llm_provider=llm,
    max_iterations=5,  # Will iterate up to 5 times
    quality_threshold=90
)
```

**Recommended**: 3-5 iterations
- **1 iteration**: Single pass (no improvement)
- **2-3 iterations**: Usually enough for most apps
- **4-5 iterations**: For complex/critical applications

### Quality Threshold

```python
generator = IterativeCodeGenerationEngine(
    config=config,
    llm_provider=llm,
    max_iterations=3,
    quality_threshold=85  # Stop when score >= 85
)
```

**Recommended thresholds**:
- **70-79**: Acceptable for MVPs/prototypes
- **80-89**: Good for production apps
- **90-95**: High quality for critical apps
- **95+**: Very difficult to achieve

---

## 🎯 Decision Logic

The system decides whether to iterate based on:

### Automatic Iteration Triggers

```python
if critical_security_issues > 0:
    ITERATE = True  # Always fix critical security

elif overall_score < quality_threshold:
    ITERATE = True  # Below quality target

elif high_compliance_gaps > 0:
    ITERATE = True  # Must fix compliance

else:
    ITERATE = False  # Quality met!
```

### Stopping Conditions

Iteration stops when:
1. Quality threshold is met
2. No critical issues remain
3. Max iterations reached
4. No more improvements available

---

## 💡 Best Practices

### 1. **Set Realistic Thresholds**

```python
# For quick MVP
quality_threshold=75

# For production app
quality_threshold=85

# For critical/regulated app
quality_threshold=90
```

### 2. **Review Each Version**

Don't just look at the final version - review the iteration history to understand what improved:

```bash
# Compare v1.0 vs v1.2
diff output/YourApp/versions/v1.0/src/server.js \
     output/YourApp/versions/v1.2/src/server.js
```

### 3. **Use Reflection Reports**

Read the `REFLECTION_REPORT_*.json` files to understand:
- What issues were found
- Why certain improvements were made
- What trade-offs exist

### 4. **Track Metrics Over Time**

```python
# Load history
history = version_tracker.load_history('output/YourApp/verifimind_history.json')

# Analyze improvement
for version in history['versions']:
    print(f"{version['version']}: {version['overall_score']}/100")
```

---

## 🔬 Advanced Usage

### Custom Improvement Logic

You can customize how improvements are applied:

```python
class CustomIterativeGenerator(IterativeCodeGenerationEngine):
    async def _apply_improvements_to_spec(self, spec, report):
        # Your custom logic here
        spec = await super()._apply_improvements_to_spec(spec, report)

        # Add custom improvements
        if 'my_specific_issue' in report.issues:
            spec.custom_features.append('my_fix')

        return spec
```

### Programmatic Access to History

```python
# Get version history
history = generator.get_version_history(app_id)

# Access specific metrics
print(f"Total iterations: {history.total_iterations}")
print(f"Improvement: {history.improvement_percentage}%")

# Access all versions
for version in history.versions:
    print(f"{version.version}: {version.overall_score}/100")
```

---

## 📈 Metrics Explained

### Overall Score Calculation

```
Overall Score = (
    Quality Score     × 30% +
    Security Score    × 30% +
    Compliance Score  × 20% +
    Performance Score × 20%
)
```

### Issue Severity

- **Critical**: Security vulnerabilities, legal compliance violations
- **High**: Missing important features, security gaps
- **Medium**: Performance issues, quality concerns
- **Low**: Best practice violations, documentation gaps

### Improvement Percentage

```
Improvement % = ((Final Score - Initial Score) / Initial Score) × 100
```

Example:
- Initial: 60/100
- Final: 90/100
- Improvement: +50%

---

## 🚨 Troubleshooting

### "Max iterations reached but quality still low"

**Solution**: Either:
1. Increase `max_iterations`
2. Lower `quality_threshold`
3. Review the reflection reports to see what's failing

### "Same issues appearing in multiple iterations"

**Cause**: The improvement application logic may not be fixing the issue

**Solution**:
- Check the reflection report to see exact issue
- Manually fix the issue in the spec
- Report as a bug if it's a system limitation

### "Too many iterations for simple app"

**Solution**: Increase the `quality_threshold` or set stricter stopping conditions

---

## 🎓 Learning from Iterations

### What Iteration Teaches You

By reviewing the iteration history, you learn:

1. **Common Mistakes**: What issues appear in v1.0
2. **Best Practices**: What fixes are applied automatically
3. **Quality Standards**: What constitutes "production-ready"
4. **Security Patterns**: How vulnerabilities are detected and fixed

### Use as Training Data

The iteration history can be used to:
- Train your team on code quality
- Create coding standards documentation
- Build automated linting rules
- Improve future generations

---

## 🔮 Future Enhancements

Planned features:
- [ ] User-provided custom quality checks
- [ ] Integration with external linters (ESLint, Pylint)
- [ ] A/B testing between iterations
- [ ] Machine learning from iteration patterns
- [ ] Automated performance benchmarking
- [ ] Visual diff viewer for iterations

---

## 📞 Support

Questions about iterative generation?
- Read `ITERATION_HISTORY.md` in your output
- Check `REFLECTION_REPORT_*.json` for details
- Review this guide
- Submit issues on GitHub

---

**Remember**: Iteration is not failure - it's continuous improvement!

The goal isn't to generate perfect code on the first try. The goal is to **systematically improve** until quality standards are met. That's the power of RefleXion.

---

*Generated by VerifiMind™ Iterative Code Generation Engine*
