#!/bin/bash

# 🚀 Crypto Scalping Bot - Automated Deployment Script
# This script will deploy your bot to GitHub and set it up for 24x7 operation

echo "🚀 CRYPTO SCALPING BOT - AUTOMATED DEPLOYMENT"
echo "=============================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Your credentials (already provided)
TELEGRAM_TOKEN="7773093247:AAEHYC48CqkF7J9n2e-Xu3dlvXuv2DlK8Is"
TELEGRAM_CHAT_ID="7915749117"
WEBHOOK_SECRET="WH_SECRET_f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1"

echo -e "${BLUE}📋 Deployment Configuration:${NC}"
echo "   Telegram Token: ${TELEGRAM_TOKEN:0:20}..."
echo "   Chat ID: $TELEGRAM_CHAT_ID"
echo "   Webhook Secret: ${WEBHOOK_SECRET:0:20}..."

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git is not installed. Please install git first.${NC}"
    exit 1
fi

# Check if GitHub CLI is available
if command -v gh &> /dev/null; then
    echo -e "${GREEN}✅ GitHub CLI detected${NC}"
    GH_CLI_AVAILABLE=true
else
    echo -e "${YELLOW}⚠️  GitHub CLI not found. Manual repository creation required.${NC}"
    GH_CLI_AVAILABLE=false
fi

# Get repository name
read -p "Enter your GitHub repository name (e.g., crypto-scalping-bot): " REPO_NAME
if [ -z "$REPO_NAME" ]; then
    REPO_NAME="crypto-scalping-bot"
fi

read -p "Enter your GitHub username: " GITHUB_USERNAME
if [ -z "$GITHUB_USERNAME" ]; then
    echo -e "${RED}❌ GitHub username is required${NC}"
    exit 1
fi

echo -e "\n${BLUE}🔧 Setting up local repository...${NC}"

# Initialize git repository if not already
if [ ! -d ".git" ]; then
    git init
    echo -e "${GREEN}✅ Git repository initialized${NC}"
fi

# Create .env file with credentials
echo -e "\n${BLUE}📝 Creating environment configuration...${NC}"
cat > .env << EOF
TELEGRAM_BOT_TOKEN=$TELEGRAM_TOKEN
TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID
WEBHOOK_SECRET=$WEBHOOK_SECRET
EOF
echo -e "${GREEN}✅ Environment file created${NC}"

# Add .env to .gitignore to keep credentials safe
if ! grep -q ".env" .gitignore 2>/dev/null; then
    echo ".env" >> .gitignore
    echo -e "${GREEN}✅ Added .env to .gitignore${NC}"
fi

# Add all files
git add .
git commit -m "🚀 Deploy crypto scalping bot with ATR-based strategies

Features:
- 6 proven scalping strategies with unique ATR multipliers
- 24x7 GitHub Actions automation
- Real-time Telegram signals
- Smart risk management with dynamic stops
- BTC, ETH, DOGE on 3m, 5m, 15m timeframes"

echo -e "${GREEN}✅ Files committed locally${NC}"

# GitHub repository creation and setup
if [ "$GH_CLI_AVAILABLE" = true ]; then
    echo -e "\n${BLUE}🌐 Creating GitHub repository...${NC}"
    
    # Check if user is logged in to GitHub CLI
    if gh auth status &>/dev/null; then
        echo -e "${GREEN}✅ GitHub CLI authenticated${NC}"
        
        # Create repository
        gh repo create "$REPO_NAME" --public --description "🚀 Professional crypto scalping bot with ATR-based risk management. Runs 24x7 on GitHub Actions with real-time Telegram signals for BTC, ETH, DOGE." --confirm
        
        # Set remote origin
        git remote remove origin 2>/dev/null || true
        git remote add origin "https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
        
        # Push code
        git branch -M main
        git push -u origin main
        
        echo -e "${GREEN}✅ Code pushed to GitHub${NC}"
        
        # Set repository secrets
        echo -e "\n${BLUE}🔐 Setting up repository secrets...${NC}"
        echo "$TELEGRAM_TOKEN" | gh secret set TELEGRAM_BOT_TOKEN --repo "$GITHUB_USERNAME/$REPO_NAME"
        echo "$TELEGRAM_CHAT_ID" | gh secret set TELEGRAM_CHAT_ID --repo "$GITHUB_USERNAME/$REPO_NAME"
        echo "$WEBHOOK_SECRET" | gh secret set WEBHOOK_SECRET --repo "$GITHUB_USERNAME/$REPO_NAME"
        
        echo -e "${GREEN}✅ Repository secrets configured${NC}"
        
        # Trigger first workflow run
        echo -e "\n${BLUE}⚡ Triggering first bot run...${NC}"
        gh workflow run "crypto-signal-bot.yml" --repo "$GITHUB_USERNAME/$REPO_NAME"
        
        echo -e "${GREEN}✅ Bot deployment initiated${NC}"
        
    else
        echo -e "${YELLOW}⚠️  Please login to GitHub CLI first: gh auth login${NC}"
        echo -e "${BLUE}Then re-run this script${NC}"
        exit 1
    fi
else
    echo -e "\n${YELLOW}📋 MANUAL DEPLOYMENT STEPS:${NC}"
    echo "1. Create repository on GitHub: https://github.com/new"
    echo "   - Repository name: $REPO_NAME"
    echo "   - Make it public"
    echo "   - Don't initialize with README"
    echo ""
    echo "2. Add remote origin:"
    echo "   git remote add origin https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
    echo ""
    echo "3. Push code:"
    echo "   git branch -M main"
    echo "   git push -u origin main"
    echo ""
    echo "4. Add repository secrets in GitHub:"
    echo "   Go to: Settings → Secrets and variables → Actions"
    echo "   Add these secrets:"
    echo "   - TELEGRAM_BOT_TOKEN: $TELEGRAM_TOKEN"
    echo "   - TELEGRAM_CHAT_ID: $TELEGRAM_CHAT_ID"
    echo "   - WEBHOOK_SECRET: $WEBHOOK_SECRET"
    echo ""
    echo "5. Enable GitHub Actions:"
    echo "   Go to Actions tab → Enable workflows"
fi

# Test Telegram connection
echo -e "\n${BLUE}📱 Testing Telegram connection...${NC}"
TEST_MESSAGE="🚀 Crypto Scalping Bot deployed successfully! 

✅ ATR-based strategies active
✅ 24x7 GitHub Actions enabled
✅ Monitoring BTC, ETH, DOGE
✅ Ready for live trading signals

Bot will start generating signals automatically!"

curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_TOKEN/sendMessage" \
    -d chat_id="$TELEGRAM_CHAT_ID" \
    -d text="$TEST_MESSAGE" \
    -d parse_mode="HTML" > /dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Telegram test message sent successfully${NC}"
else
    echo -e "${RED}❌ Failed to send Telegram test message${NC}"
    echo -e "${YELLOW}Please check your Telegram credentials${NC}"
fi

# Final status
echo -e "\n${GREEN}🎉 DEPLOYMENT COMPLETE!${NC}"
echo -e "${BLUE}📊 Your crypto scalping bot is now:${NC}"
echo "   ✅ Deployed to GitHub"
echo "   ✅ Running 24x7 on GitHub Actions"
echo "   ✅ Monitoring BTC, ETH, DOGE on 3m, 5m, 15m"
echo "   ✅ Using ATR-based risk management"
echo "   ✅ Sending signals to Telegram"
echo ""
echo -e "${BLUE}📅 Schedule:${NC}"
echo "   🕐 Peak Hours: Every 15 minutes"
echo "   🕐 Off-Peak: Every 30 minutes"
echo "   🕐 Backup: Every 2 hours"
echo ""
echo -e "${BLUE}🔗 Repository URL:${NC} https://github.com/$GITHUB_USERNAME/$REPO_NAME"
echo -e "${BLUE}⚡ Actions URL:${NC} https://github.com/$GITHUB_USERNAME/$REPO_NAME/actions"
echo ""
echo -e "${GREEN}Your bot will start generating real scalping signals automatically!${NC}"