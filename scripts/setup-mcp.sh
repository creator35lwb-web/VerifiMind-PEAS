#!/bin/bash
# VerifiMind PEAS MCP Server Setup Script
# One-click configuration for Claude Code, Claude Desktop, and Cursor
# https://github.com/creator35lwb-web/VerifiMind-PEAS

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║       VerifiMind™ PEAS - MCP Server Setup                    ║"
echo "║       Multi-Agent AI Validation System                       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# MCP Configuration
MCP_CONFIG='{
  "mcpServers": {
    "verifimind-genesis": {
      "url": "https://verifimind.ysenseai.org/mcp",
      "transport": "http-sse"
    }
  }
}'

# Detect OS
detect_os() {
    case "$(uname -s)" in
        Darwin*)    echo "macos" ;;
        Linux*)     echo "linux" ;;
        MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
        *)          echo "unknown" ;;
    esac
}

OS=$(detect_os)

echo -e "${GREEN}Detected OS: ${OS}${NC}"
echo ""

# Function to show configuration
show_config() {
    echo -e "${CYAN}MCP Server Configuration:${NC}"
    echo ""
    echo "$MCP_CONFIG"
    echo ""
}

# Function to setup Claude Desktop
setup_claude_desktop() {
    echo -e "${YELLOW}Setting up Claude Desktop...${NC}"
    
    if [ "$OS" = "macos" ]; then
        CONFIG_DIR="$HOME/Library/Application Support/Claude"
        CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
    elif [ "$OS" = "windows" ]; then
        CONFIG_DIR="$APPDATA/Claude"
        CONFIG_FILE="$CONFIG_DIR/claude_desktop_config.json"
    else
        echo -e "${RED}Claude Desktop setup not supported on Linux.${NC}"
        echo "Please manually add the configuration to your Claude Desktop settings."
        return
    fi
    
    # Create directory if it doesn't exist
    mkdir -p "$CONFIG_DIR"
    
    # Check if config file exists
    if [ -f "$CONFIG_FILE" ]; then
        echo -e "${YELLOW}Existing config found. Creating backup...${NC}"
        cp "$CONFIG_FILE" "$CONFIG_FILE.backup.$(date +%Y%m%d%H%M%S)"
        
        # Check if jq is available for merging
        if command -v jq &> /dev/null; then
            echo -e "${GREEN}Merging configuration...${NC}"
            jq -s '.[0] * .[1]' "$CONFIG_FILE" <(echo "$MCP_CONFIG") > "$CONFIG_FILE.tmp"
            mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
        else
            echo -e "${YELLOW}jq not found. Please manually merge the configuration.${NC}"
            echo "Add the following to $CONFIG_FILE:"
            show_config
            return
        fi
    else
        echo "$MCP_CONFIG" > "$CONFIG_FILE"
    fi
    
    echo -e "${GREEN}✓ Claude Desktop configured successfully!${NC}"
    echo "  Config file: $CONFIG_FILE"
    echo "  Restart Claude Desktop to apply changes."
}

# Function to show manual instructions
show_manual_instructions() {
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}Manual Setup Instructions${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    
    echo -e "${GREEN}1. Claude Code:${NC}"
    echo "   Open Settings > MCP Servers and add:"
    echo ""
    echo "$MCP_CONFIG"
    echo ""
    
    echo -e "${GREEN}2. Claude Desktop:${NC}"
    if [ "$OS" = "macos" ]; then
        echo "   Edit: ~/Library/Application Support/Claude/claude_desktop_config.json"
    elif [ "$OS" = "windows" ]; then
        echo "   Edit: %APPDATA%\\Claude\\claude_desktop_config.json"
    else
        echo "   Edit your Claude Desktop configuration file"
    fi
    echo ""
    
    echo -e "${GREEN}3. Cursor:${NC}"
    echo "   Open Settings (Cmd/Ctrl+Shift+P > 'Preferences: Open Settings (JSON)')"
    echo "   Add the following:"
    echo ""
    echo '{
  "mcp.servers": {
    "verifimind-genesis": {
      "url": "https://verifimind.ysenseai.org/mcp",
      "transport": "http-sse"
    }
  }
}'
    echo ""
}

# Function to verify server status
verify_server() {
    echo -e "${YELLOW}Verifying MCP Server status...${NC}"
    
    if command -v curl &> /dev/null; then
        RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://verifimind.ysenseai.org/health 2>/dev/null || echo "000")
        
        if [ "$RESPONSE" = "200" ]; then
            echo -e "${GREEN}✓ MCP Server is online and healthy!${NC}"
        else
            echo -e "${YELLOW}⚠ Server returned status: $RESPONSE${NC}"
            echo "  The server may be temporarily unavailable."
        fi
    else
        echo -e "${YELLOW}curl not found. Skipping server verification.${NC}"
    fi
}

# Main menu
echo "Select setup option:"
echo ""
echo "  1) Auto-configure Claude Desktop"
echo "  2) Show manual setup instructions"
echo "  3) Copy configuration to clipboard"
echo "  4) Verify server status"
echo "  5) Show available tools"
echo "  0) Exit"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        setup_claude_desktop
        ;;
    2)
        show_manual_instructions
        ;;
    3)
        if [ "$OS" = "macos" ]; then
            echo "$MCP_CONFIG" | pbcopy
            echo -e "${GREEN}✓ Configuration copied to clipboard!${NC}"
        elif [ "$OS" = "linux" ] && command -v xclip &> /dev/null; then
            echo "$MCP_CONFIG" | xclip -selection clipboard
            echo -e "${GREEN}✓ Configuration copied to clipboard!${NC}"
        else
            echo -e "${YELLOW}Clipboard not available. Here's the configuration:${NC}"
            show_config
        fi
        ;;
    4)
        verify_server
        ;;
    5)
        echo -e "${CYAN}Available MCP Tools:${NC}"
        echo ""
        echo -e "${GREEN}consult_agent_x${NC} - Innovation & Strategy Analysis (Gemini 2.0 Flash)"
        echo "  Analyze ideas for innovation potential and strategic value"
        echo ""
        echo -e "${GREEN}consult_agent_z${NC} - Ethics & Safety Review (Claude 3 Haiku)"
        echo "  Evaluate ethical implications and safety considerations"
        echo ""
        echo -e "${GREEN}consult_agent_cs${NC} - Security & Feasibility Validation (Claude 3 Haiku)"
        echo "  Assess technical feasibility and security aspects"
        echo ""
        echo -e "${GREEN}run_full_trinity${NC} - Complete X → Z → CS Validation"
        echo "  Run all three agents in sequence for comprehensive analysis"
        echo ""
        ;;
    0)
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid option. Showing manual instructions...${NC}"
        show_manual_instructions
        ;;
esac

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Resources:${NC}"
echo "  Website:    https://verifimind.ysenseai.org"
echo "  GitHub:     https://github.com/creator35lwb-web/VerifiMind-PEAS"
echo "  Docs:       https://github.com/creator35lwb-web/VerifiMind-PEAS/blob/main/MCP_SERVER_FEATURES.md"
echo "  White Paper: https://doi.org/10.5281/zenodo.17645665"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
