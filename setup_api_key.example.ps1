# Example: Set OpenAI API Key for LLM Recommendations
# Copy this file and rename to setup_api_key.ps1, then add your real key

# STEP 1: Get your API key from https://platform.openai.com/api-keys

# STEP 2: Set the environment variable (replace with your actual key)
$env:OPENAI_API_KEY="sk-proj-your-actual-key-here-DO-NOT-COMMIT-THIS"

# STEP 3: Verify it's set
Write-Host "OpenAI API Key set: $($env:OPENAI_API_KEY.Substring(0,10))..." -ForegroundColor Green

# STEP 4: Run this in the same PowerShell window before starting the server
# Then run: python api_server.py

# NOTE: This only sets the key for the current PowerShell session
# For persistent storage, add to your PowerShell profile or use .env file

Write-Host "`n✅ Ready to start API server with LLM support!" -ForegroundColor Green
Write-Host "Run: python api_server.py" -ForegroundColor Yellow
