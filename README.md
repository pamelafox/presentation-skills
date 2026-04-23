# 🎤 Presentation Skills

A collection of agent skills for working with presentations.

## Skills

### 📄 pdf-to-markdown

Converts PDF and other document formats (PowerPoint, Word, Excel) to Markdown using [Microsoft's markitdown](https://github.com/microsoft/markitdown) package.

**Use when:** converting a PDF/PPTX/DOCX to Markdown, extracting text from a document, or reading/parsing document content.

### 🔍 review-presentation

Reviews presentation slides for accuracy and consistency with the code samples in the repository.

**Use when:** you want feedback on your slides — checking for errors, inconsistencies, or areas that need clarification relative to the repo's code.

## Installation

Install all skills using the [`skills`](https://www.npmjs.com/package/skills) CLI:

```sh
npx skills add pamelafox/presentation-skills
```

Or install individual skills:

```sh
npx skills add pamelafox/presentation-skills/pdf-to-markdown
npx skills add pamelafox/presentation-skills/review-presentation
```
