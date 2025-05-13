# Git Workflow Guide for Hackathon

Initial Setup:
```
git clone [repository-url]
cd [repository-name]
```
Branch Structure:
```
main: Production-ready code
dev: Integration branch for features
feature/[feature-name]: Individual feature branches
```

Commands:

Branch Management:
# Create and switch to dev branch
```
git checkout -b dev
git push -u origin dev
```
# Create feature branch from dev
```
git checkout dev
git pull
git checkout -b feature/your-feature-name
git push -u origin feature/your-feature-name
```

# Regular Workflow:
## Update your feature branch with latest dev changes
```
git checkout dev
git pull
git checkout feature/your-feature-name
git merge dev
```

## Make changes, then commit and push
```
git add .
git commit -m "Descriptive message"
git push
```

## Merge completed feature into dev
```
git checkout dev
git merge feature/your-feature-name
git push
```

## Deploy to production
```
git checkout main
git merge dev
git push
```


## Common Commands:
```
git status                     # Check status
git branch                     # List branches
git log --oneline --graph      # View commit history
git fetch --all                # Update remote tracking
```