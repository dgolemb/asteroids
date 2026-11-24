# Asteroids - training project

## What this project is

A simple Asteroids-style game project. Its purpose is to teach programming fundamentals and an AI-native workflow.

## Stack and tools

Python 3.13
Pygames 2.6.1
uv 0.13.8
pygbag 0.9.3

Docker base images:
python:3.13-slim
nginx:1.30-alpine

Browser runtime:
CPython 3.12
pygame-ce 2.5.7

Infra:
Terraform 1.15.6

## Commands

uv venv
source .venv/bin/activate
python -m unittest

## Code conventions

Variable names in snake_case style
Class names in PascalCase style

## Constraints (guardrails)

Do not commit directly to main.
Do not search for or install additional dependencies unless I explicitly ask you to.
Do not comment code unless I ask you to.
Do not use emoji.
Do not write documentation unless you are directly asked to.
Do not add Co-Authored-By information to commits.

## Rules

When you are not sure, ask questions instead of guessing.
After every approved and completed Edit, commit to the current branch with a short (1-2 sentence) description of the changes made.
After every commit, verify that the contents of README.md still match the actual state. If not, update the README.
