# Build frontend locally
Write-Host "Building React frontend..." -ForegroundColor Cyan

cd frontend

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
npm install --legacy-peer-deps

# Build
Write-Host "Building production bundle..." -ForegroundColor Yellow
npm run build

Write-Host "Build complete! Output in frontend/build/" -ForegroundColor Green

cd ..

