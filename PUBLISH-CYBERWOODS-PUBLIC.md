# Publish Cyberwoods Public Only

## Stage only public skill files

```bash
git add .gitignore
git add skills/cyberwoods-public/SKILL.md
git add skills/cyberwoods-public/agents/openai.yaml
git add skills/cyberwoods-public/references/threat-model.md
git add skills/cyberwoods-public/references/adoption-checklist.md
```

## Commit message template

```txt
feat(skill): add cyberwoods-public sanitized security review workflow
```

## Optional verify command

```bash
git diff --cached --name-only
```

