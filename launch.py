"""
VerifiMind™ One-Click Launcher
Interactive menu system for launching VerifiMind applications
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass


class VerifiMindLauncher:
    """One-click launcher for VerifiMind system"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_python = self._find_python()

    def _find_python(self):
        """Find Python executable (venv or system)"""
        # Check for virtual environment
        venv_paths = [
            self.project_root / "venv" / "Scripts" / "python.exe",
            self.project_root / ".venv" / "Scripts" / "python.exe",
            self.project_root / "env" / "Scripts" / "python.exe",
        ]

        for venv_path in venv_paths:
            if venv_path.exists():
                return str(venv_path)

        # Use system Python
        return sys.executable

    def clear_screen(self):
        """Clear console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_banner(self):
        """Print VerifiMind banner"""
        banner = """
        ==================================================================

                 VerifiMind - AI Application Generator
                      One-Click Launch System

                 Transform Ideas into Production Apps

        ==================================================================
        """
        print(banner)

    def print_menu(self):
        """Print main menu"""
        menu = """
        ------------------------------------------------------------------
                              MAIN MENU
        ------------------------------------------------------------------

          [1] Generate New Application
              -> Run complete app generation (demo)

          [2] Test Enhanced Agents
              -> Test LLM integration, compliance, security

          [3] Quick Demo (No Emoji)
              -> Run meditation app demo

          [4] Check System Status
              -> Verify dependencies and configuration

          [5] Setup & Installation
              -> Install dependencies and configure

          [6] View Documentation
              -> Open project documentation

          [7] Advanced Options
              -> Developer tools and utilities

          [0] Exit

        ------------------------------------------------------------------
        """
        print(menu)

    def run_command(self, command, description):
        """Run a command with output"""
        print(f"\n[RUNNING] {description}")
        print(f"[COMMAND] {command}\n")
        print("=" * 70)

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=str(self.project_root),
                text=True,
                capture_output=False
            )

            print("=" * 70)
            if result.returncode == 0:
                print(f"\n[SUCCESS] {description} completed successfully!")
            else:
                print(f"\n[ERROR] {description} failed with code {result.returncode}")

            return result.returncode == 0
        except Exception as e:
            print(f"\n[ERROR] Failed to run command: {e}")
            return False

    def option_1_generate_app(self):
        """Option 1: Generate new application"""
        self.clear_screen()
        self.print_banner()
        print("\n[OPTION 1] Generate New Application with Attribution\n")

        print("This will guide you through creating YOUR OWN custom app.")
        print("Features:")
        print("  - Describe your app idea in plain English")
        print("  - Get blockchain-verified proof of creation")
        print("  - Receive attribution certificate with QR code")
        print("  - Protect your copyright permanently\n")

        input("Press Enter to continue...")

        self.run_command(
            f'"{self.venv_python}" interactive_generation_with_attribution.py',
            "Interactive Application Generation with Attribution"
        )

        print("\n\nCheck ./output/ directory for your generated app")
        print("Your attribution certificate is included!")
        input("\nPress Enter to return to main menu...")

    def option_2_test_agents(self):
        """Option 2: Test enhanced agents"""
        self.clear_screen()
        self.print_banner()
        print("\n[OPTION 2] Test Enhanced Agents\n")

        print("This will test all three enhanced agents:")
        print("  - X Intelligent Agent (Business Analysis)")
        print("  - Z Guardian Agent (12 Compliance Frameworks)")
        print("  - CS Security Agent (100+ Threat Patterns)\n")

        input("Press Enter to continue...")

        self.run_command(
            f'"{self.venv_python}" test_enhanced_agents.py',
            "Enhanced Agent Testing"
        )

        input("\nPress Enter to return to main menu...")

    def option_3_quick_demo(self):
        """Option 3: Quick demo"""
        self.clear_screen()
        self.print_banner()
        print("\n[OPTION 3] Quick Demo\n")

        print("This runs a quick demonstration of the system.")
        print("Generates: KidsCalmMind meditation app\n")

        input("Press Enter to continue...")

        self.run_command(
            f'"{self.venv_python}" demo_generation_no_emoji.py',
            "Quick Demo"
        )

        input("\nPress Enter to return to main menu...")

    def option_4_system_status(self):
        """Option 4: Check system status"""
        self.clear_screen()
        self.print_banner()
        print("\n[OPTION 4] System Status Check\n")

        print("Checking system configuration...\n")
        print("=" * 70)

        # Check Python version
        print(f"\n[1/5] Python Version")
        print(f"      Location: {self.venv_python}")
        version = subprocess.run(
            f'"{self.venv_python}" --version',
            shell=True,
            capture_output=True,
            text=True
        )
        print(f"      Version: {version.stdout.strip()}")

        # Check dependencies
        print(f"\n[2/5] Dependencies")
        deps = ['openai', 'anthropic', 'aiohttp']
        for dep in deps:
            result = subprocess.run(
                f'"{self.venv_python}" -c "import {dep}; print({dep}.__version__)"',
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print(f"      ✓ {dep}: {result.stdout.strip()}")
            else:
                print(f"      ✗ {dep}: Not installed")

        # Check API keys
        print(f"\n[3/5] API Keys")
        openai_key = os.getenv('OPENAI_API_KEY')
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        print(f"      OpenAI: {'✓ Configured' if openai_key else '✗ Not set (will use mock)'}")
        print(f"      Anthropic: {'✓ Configured' if anthropic_key else '✗ Not set (will use mock)'}")

        # Check project structure
        print(f"\n[4/5] Project Structure")
        critical_files = [
            'src/agents/x_intelligent_agent.py',
            'src/agents/z_guardian_agent.py',
            'src/agents/cs_security_agent.py',
            'src/generation/core_generator.py',
            'src/generation/frontend_generator.py',
            'src/llm/llm_provider.py'
        ]
        for file in critical_files:
            path = self.project_root / file
            if path.exists():
                print(f"      ✓ {file}")
            else:
                print(f"      ✗ {file} (MISSING)")

        # Check output directory
        print(f"\n[5/5] Output Directory")
        output_dir = self.project_root / "output"
        if output_dir.exists():
            apps = list(output_dir.iterdir())
            print(f"      ✓ Output directory exists")
            print(f"      Generated apps: {len(apps)}")
        else:
            print(f"      ✗ Output directory not found")

        print("\n" + "=" * 70)
        print("\n[STATUS] System check complete!")

        input("\nPress Enter to return to main menu...")

    def option_5_setup(self):
        """Option 5: Setup and installation"""
        self.clear_screen()
        self.print_banner()
        print("\n[OPTION 5] Setup & Installation\n")

        print("This will install all required dependencies.\n")

        choice = input("Continue with installation? (y/n): ").strip().lower()
        if choice != 'y':
            return

        print("\n[STEP 1] Installing Python dependencies...")
        self.run_command(
            f'"{self.venv_python}" -m pip install --upgrade pip',
            "Upgrade pip"
        )

        print("\n[STEP 2] Installing required packages...")
        self.run_command(
            f'"{self.venv_python}" -m pip install openai anthropic aiohttp',
            "Install dependencies"
        )

        print("\n[STEP 3] Creating output directory...")
        output_dir = self.project_root / "output"
        output_dir.mkdir(exist_ok=True)
        print("[SUCCESS] Output directory created")

        print("\n[STEP 4] API Key Setup (Optional)")
        print("\nTo use real LLM APIs, set these environment variables:")
        print("  set OPENAI_API_KEY=sk-...")
        print("  set ANTHROPIC_API_KEY=sk-ant-...")
        print("\nNote: System will use intelligent mock responses if keys not set.")

        print("\n[COMPLETE] Setup finished!")
        input("\nPress Enter to return to main menu...")

    def option_6_documentation(self):
        """Option 6: View documentation"""
        self.clear_screen()
        self.print_banner()
        print("\n[OPTION 6] Documentation\n")

        docs = {
            '1': ('README.md', 'Project Overview'),
            '2': ('COMPLETE_VISION.md', 'Complete Vision & Roadmap'),
            '3': ('AGENT_ENHANCEMENTS.md', 'Agent Enhancement Details'),
            '4': ('FRONTEND_GENERATOR_SPEC.xml', 'Frontend Generator Spec'),
            '5': ('DEMO_RUN_SUCCESS.md', 'Demo Success Report'),
            '6': ('ENHANCEMENT_SUMMARY.md', 'Enhancement Summary'),
        }

        print("Available Documentation:\n")
        for key, (file, desc) in docs.items():
            print(f"  [{key}] {desc}")
            print(f"      ({file})")
        print(f"\n  [0] Return to main menu")

        choice = input("\nSelect document to open: ").strip()

        if choice in docs:
            file_path = self.project_root / docs[choice][0]
            if file_path.exists():
                if sys.platform == 'win32':
                    os.startfile(file_path)
                else:
                    subprocess.run(['xdg-open', str(file_path)])
                print(f"\n[SUCCESS] Opening {docs[choice][0]}...")
            else:
                print(f"\n[ERROR] File not found: {docs[choice][0]}")

        input("\nPress Enter to return to main menu...")

    def option_7_advanced(self):
        """Option 7: Advanced options"""
        self.clear_screen()
        self.print_banner()
        print("\n[OPTION 7] Advanced Options\n")

        menu = """
        ------------------------------------------------------------------
                           ADVANCED OPTIONS
        ------------------------------------------------------------------

          [1] Run Specific Agent Test
          [2] View Generated Apps
          [3] Verify Attribution / Certificate
          [4] View Blockchain Statistics
          [5] Clean Output Directory
          [6] Open Project in Explorer
          [7] Show API Keys Status
          [8] Run Python Shell

          [0] Back to Main Menu

        ------------------------------------------------------------------
        """
        print(menu)

        choice = input("Select option: ").strip()

        if choice == '1':
            self.advanced_test_specific_agent()
        elif choice == '2':
            self.advanced_view_apps()
        elif choice == '3':
            self.advanced_verify_attribution()
        elif choice == '4':
            self.advanced_blockchain_stats()
        elif choice == '5':
            self.advanced_clean_output()
        elif choice == '6':
            self.advanced_open_explorer()
        elif choice == '7':
            self.advanced_show_api_keys()
        elif choice == '8':
            self.advanced_python_shell()

    def advanced_test_specific_agent(self):
        """Test specific agent"""
        print("\n[ADVANCED] Test Specific Agent\n")
        print("  [1] X Intelligent Agent")
        print("  [2] Z Guardian Agent")
        print("  [3] CS Security Agent")

        choice = input("\nSelect agent: ").strip()

        test_scripts = {
            '1': 'try:\\n    from src.agents.x_intelligent_agent import XIntelligentAgent\\n    print("✓ X Agent imported successfully")\\nexcept Exception as e:\\n    print(f"✗ X Agent error: {e}")',
            '2': 'try:\\n    from src.agents.z_guardian_agent import ZGuardianAgent\\n    print("✓ Z Agent imported successfully")\\nexcept Exception as e:\\n    print(f"✗ Z Agent error: {e}")',
            '3': 'try:\\n    from src.agents.cs_security_agent import CSSecurityAgent\\n    print("✓ CS Agent imported successfully")\\nexcept Exception as e:\\n    print(f"✗ CS Agent error: {e}")'
        }

        if choice in test_scripts:
            # Escape for Windows command line
            test_code = test_scripts[choice].replace('\\n', '\n')

            # Write to temp file instead of inline command
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(test_code)
                temp_file = f.name

            try:
                self.run_command(
                    f'"{self.venv_python}" "{temp_file}"',
                    f"Agent Import Test"
                )
            finally:
                import os
                try:
                    os.unlink(temp_file)
                except:
                    pass

        input("\nPress Enter to continue...")

    def advanced_view_apps(self):
        """View generated apps"""
        print("\n[ADVANCED] View Generated Apps\n")

        output_dir = self.project_root / "output"
        if output_dir.exists():
            apps = [d for d in output_dir.iterdir() if d.is_dir()]
            if apps:
                print(f"Found {len(apps)} generated app(s):\n")
                for i, app in enumerate(apps, 1):
                    print(f"  [{i}] {app.name}")
                    readme = app / "README.md"
                    if readme.exists():
                        print(f"      ✓ Has README")
                    db_schema = app / "database" / "schema.sql"
                    if db_schema.exists():
                        print(f"      ✓ Has database schema")
            else:
                print("No apps generated yet.")
        else:
            print("Output directory does not exist.")

        input("\nPress Enter to continue...")

    def advanced_clean_output(self):
        """Clean output directory"""
        print("\n[ADVANCED] Clean Output Directory\n")

        output_dir = self.project_root / "output"
        if output_dir.exists():
            apps = [d for d in output_dir.iterdir() if d.is_dir()]
            if apps:
                print(f"This will delete {len(apps)} generated app(s):")
                for app in apps:
                    print(f"  - {app.name}")

                choice = input("\nAre you sure? (y/n): ").strip().lower()
                if choice == 'y':
                    import shutil
                    for app in apps:
                        shutil.rmtree(app)
                    print("\n[SUCCESS] Output directory cleaned!")
                else:
                    print("\n[CANCELLED] Operation cancelled.")
            else:
                print("Output directory is already empty.")
        else:
            print("Output directory does not exist.")

        input("\nPress Enter to continue...")

    def advanced_open_explorer(self):
        """Open project in Windows Explorer"""
        print("\n[ADVANCED] Opening project directory...\n")

        if sys.platform == 'win32':
            os.startfile(self.project_root)
        else:
            subprocess.run(['xdg-open', str(self.project_root)])

        print("[SUCCESS] Explorer opened!")
        input("\nPress Enter to continue...")

    def advanced_show_api_keys(self):
        """Show API keys status"""
        print("\n[ADVANCED] API Keys Status\n")

        openai_key = os.getenv('OPENAI_API_KEY')
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')

        print("OpenAI API Key:")
        if openai_key:
            print(f"  ✓ Set (ends with ...{openai_key[-4:]})")
        else:
            print("  ✗ Not set")
            print("  To set: set OPENAI_API_KEY=sk-...")

        print("\nAnthropic API Key:")
        if anthropic_key:
            print(f"  ✓ Set (ends with ...{anthropic_key[-4:]})")
        else:
            print("  ✗ Not set")
            print("  To set: set ANTHROPIC_API_KEY=sk-ant-...")

        print("\nNote: System will use intelligent mock responses if keys not set.")

        input("\nPress Enter to continue...")

    def advanced_python_shell(self):
        """Open Python shell"""
        print("\n[ADVANCED] Python Interactive Shell\n")
        print("Launching Python shell in project context...")
        print("Type 'exit()' to return to launcher.\n")

        input("Press Enter to continue...")

        subprocess.run(
            f'"{self.venv_python}"',
            shell=True,
            cwd=str(self.project_root)
        )

    def advanced_verify_attribution(self):
        """Verify attribution or certificate"""
        print("\n[ADVANCED] Verify Attribution / Certificate\n")
        print("What would you like to verify?")
        print("  [1] Verify App Attribution")
        print("  [2] Verify Certificate File")
        print("  [3] View Creator Portfolio")

        choice = input("\nSelect option: ").strip()

        if choice == '1':
            app_id = input("Enter App ID: ").strip()
            if app_id:
                self.run_command(
                    f'"{self.venv_python}" verify_attribution.py app {app_id}',
                    "Verify App Attribution"
                )
        elif choice == '2':
            cert_path = input("Enter Certificate Path: ").strip()
            if cert_path:
                self.run_command(
                    f'"{self.venv_python}" verify_attribution.py cert "{cert_path}"',
                    "Verify Certificate"
                )
        elif choice == '3':
            email = input("Enter Creator Email: ").strip()
            if email:
                self.run_command(
                    f'"{self.venv_python}" verify_attribution.py creator --email {email}',
                    "View Creator Portfolio"
                )

        input("\nPress Enter to continue...")

    def advanced_blockchain_stats(self):
        """Show blockchain statistics"""
        print("\n[ADVANCED] Blockchain Statistics\n")

        self.run_command(
            f'"{self.venv_python}" verify_attribution.py stats',
            "Blockchain Statistics"
        )

        input("\nPress Enter to continue...")

    def run(self):
        """Main launcher loop"""
        while True:
            self.clear_screen()
            self.print_banner()
            self.print_menu()

            choice = input("Select option: ").strip()

            if choice == '0':
                print("\nExiting VerifiMind Launcher...")
                print("Thank you for using VerifiMind™!\n")
                break
            elif choice == '1':
                self.option_1_generate_app()
            elif choice == '2':
                self.option_2_test_agents()
            elif choice == '3':
                self.option_3_quick_demo()
            elif choice == '4':
                self.option_4_system_status()
            elif choice == '5':
                self.option_5_setup()
            elif choice == '6':
                self.option_6_documentation()
            elif choice == '7':
                self.option_7_advanced()
            else:
                print("\n[ERROR] Invalid option. Please try again.")
                input("Press Enter to continue...")


if __name__ == "__main__":
    launcher = VerifiMindLauncher()
    try:
        launcher.run()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Launcher interrupted by user.")
        print("Goodbye!\n")
    except Exception as e:
        print(f"\n[ERROR] Launcher error: {e}")
        input("Press Enter to exit...")
