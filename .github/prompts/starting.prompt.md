---
name: bootstrapProject
description: Bootstrap a new project by generating project.md and constitution governance files from scratch.
argument-hint: Describe your project's purpose, tech stack, and core principles (optional - will prompt if missing)
---
Help me bootstrap my project governance files from scratch. I'm at the starting point with no existing project.md or constitution.md.

## What I Need

1. **Generate `specs/project.md`** - Define:
   - Project name and description
   - Technology stack (languages, frameworks, tools)
   - Architecture patterns and conventions
   - Folder structure and file organization
   - Coding standards and naming conventions
   - Testing approach and requirements
   - Documentation standards

2. **Generate `specs/memory/constitution.md`** - Establish:
   - Core principles that govern this project
   - Development workflow rules
   - Quality gates and validation requirements
   - Agent collaboration guidelines (if using AI agents)
   - Decision-making frameworks
   - Non-negotiable constraints

## My Project Context

${Describe your project here, or leave blank and the agent will ask clarifying questions}

## Expected Output

- A complete, populated `specs/project.md` file (no placeholders)
- A complete, populated `specs/memory/constitution.md` file (no placeholders)
- Both files should be tailored to my specific project context
- Files should follow SpecKit governance standards if applicable

If I haven't provided enough context, ask me clarifying questions about:
- What is this project's primary purpose?
- What technology stack am I using or planning to use?
- What are the non-negotiable principles for this project?
- What quality standards must be maintained?
- Who/what will be working on this project (human developers, AI agents, both)?
