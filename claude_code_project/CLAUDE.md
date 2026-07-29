# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository overview

This is not a buildable software project — it's a single self-contained HTML file with no package.json, build tool, bundler, test runner, dependency manager, or git repository. `task-board.html` has everything inline (`<style>` and `<script>` in the `<head>`/body, no external assets or CDN links) and can be opened directly in a browser.

`task-board.html` is a Korean-language ("학습 과제 관리 보드" — study task management board) task/study-planner app with:
- Add/filter/status/priority controls for tasks
- A month calendar view showing tasks by date
- Persistence via `localStorage` (key `task-board:v1`)

## Working with this repo

- There is nothing to install and nothing to build. To try a change, open `task-board.html` directly in a browser (or use a simple local server if `file://` restrictions get in the way).
- There is no test suite or linter configured. Verify changes manually in a browser.
- The file follows a consistent internal pattern: an IIFE at the bottom of the `<script>` block holds all state and DOM references at the top, small mutation functions (e.g. `addTask`, `updateStatus`, `updatePriority`), and a `render()` function that re-syncs the DOM from state (calling `renderList`, `renderSummary`, `renderCalendar`, `renderDateFilterIndicator`). When editing behavior, follow this same "mutate state, then call render" flow rather than mutating the DOM directly in event handlers.
- UI text is in Korean (`lang="ko"`); keep new user-facing strings consistent with the existing language unless asked otherwise.
- Since there's no git repo here, don't assume commit/branch workflows are available — confirm with the user before suggesting `git init` or similar.
