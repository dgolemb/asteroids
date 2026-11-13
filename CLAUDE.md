# Asteroids - projekt szkoleniowy

## What this project is

Projekt prostej gry w stylu Asteroids. Ma za zadanie nauke podstaw programowania oraz AI native workflow.

## Stack and tools

Python 3.13
Pygames 2.6.1
uv 0.13.8
pygbag 0.9.3

Obrazy bazowe Docker:
python:3.13-slim
nginx:1.30-alpine

Runtime w przeglądarce:
CPython 3.12
pygame-ce 2.5.7

Infra:
Terraform 1.15.6

## Commands

uv venv
source .venv/bin/activate

## Code conventions

Nazwy zmiennych w stylu snake_case
Nazwy klas w stylu PascalCase

## Constraints (guardrails)

Nie commituj prosto do main.
Nie szukaj ani nie instaluj dodatkowych zaleznosci jesli wyraznie o to nie poprosze.
Nie komentuj kodu jeśli o to nie poproszę.
Nie uzywaj emoji.

## Rules

Korzystaj z venv.
Gdy nie jesteś pewien, zadawaj pytania zamiast zgadywać.
Po kazdym zatwierdzonym i wykonanym Edit, commituj do aktualnego brancha z krótkim (1-2 zdania) opisem wprowadzonych zmian.