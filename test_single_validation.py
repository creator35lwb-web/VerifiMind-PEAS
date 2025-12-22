#!/usr/bin/env python3
"""Quick test of single validation with report generation."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from run_60_validations import TrinityReportRunner

async def main():
    output_dir = Path("test_single_report")
    runner = TrinityReportRunner(output_dir)
    
    concept_name = "AI-Powered Fraud Detection for Banking"
    concept_desc = "Real-time fraud detection system using machine learning to identify suspicious transactions and prevent financial crimes. Target: Banks and financial institutions."
    
    result = await runner.validate_concept(1, concept_name, concept_desc)
    
    if result["success"]:
        print("\n✅ SUCCESS!")
        print(f"Score: {result['score']:.1f}/10")
        print(f"Verdict: {result['verdict']}")
        print(f"Duration: {result['duration']:.2f}s")
        print(f"Cost: ${result['cost']:.6f}")
        print(f"\nReport saved to: {output_dir}")
        return 0
    else:
        print(f"\n❌ FAILED: {result['error']}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
