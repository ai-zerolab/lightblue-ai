# lightblue-ai

[![Release](https://img.shields.io/github/v/release/ai-zerolab/lightblue-ai)](https://img.shields.io/github/v/release/ai-zerolab/lightblue-ai)
[![Build status](https://img.shields.io/github/actions/workflow/status/ai-zerolab/lightblue-ai/main.yml?branch=main)](https://github.com/ai-zerolab/lightblue-ai/actions/workflows/main.yml?query=branch%3Amain)
[![codecov](https://codecov.io/gh/ai-zerolab/lightblue-ai/branch/main/graph/badge.svg)](https://codecov.io/gh/ai-zerolab/lightblue-ai)
[![Commit activity](https://img.shields.io/github/commit-activity/m/ai-zerolab/lightblue-ai)](https://img.shields.io/github/commit-activity/m/ai-zerolab/lightblue-ai)
[![License](https://img.shields.io/github/license/ai-zerolab/lightblue-ai)](https://img.shields.io/github/license/ai-zerolab/lightblue-ai)

> Inspired by Deep Blue – Harnessing computational power to transcend human design.
>
> [The Bitter Lesson](http://www.incompleteideas.net/IncIdeas/BitterLesson.html)
>
> [The Bitter Lesson: Rethinking How We Build AI Systems](https://ankitmaloo.com/bitter-lesson/)

Light Blue is an agent designed for generating HTML.

- **Github repository**: <https://github.com/ai-zerolab/lightblue-ai/>

## Pre-requisites

### Mac

Mac users will have to install poppler for pdf to image conversion

Installing using Brew:

```bash
brew install poppler
```

### Linux

Most distros ship with pdftoppm and pdftocairo. If they are not installed, refer to your package manager to install poppler-utils. e.g. `apt-get install poppler-utils`

## Usage

### CLI

Directly prompt:

```bash
uvx lightblue-ai submit <prompt>
```

Use prompt file:

```bash
uvx lightblue-ai submit prompt.md # Or just uvx lightblue-ai submit, prompt.md is the default prompt file
```

### Programmatic

See [agent.py](./lightblue_ai/agent.py) and [Examples](./examples/README.md)

## Configuration

- `system_prompt.md` to Override [system prompt](./lightblue_ai/prompts/templates/system_prompt.md)
- `mcp.json` to configure [MCP](./mcp.example.json)
- `.env` for [setting environment variables](./.env.example)

Once you provided the api-key of the tools, tools will automatically be loaded.
