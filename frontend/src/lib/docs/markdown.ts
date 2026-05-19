/**
 * Client-side Markdown rendering pipeline.
 *
 * Uses `marked` for parsing, `marked-alert` for GitHub-style callouts
 * (> [!NOTE] / [!TIP] / [!WARNING] / [!IMPORTANT] / [!CAUTION]),
 * `marked-gfm-heading-id` for slugged heading anchors, Shiki for
 * VS Code-grade syntax highlighting (dual light/dark theme via CSS
 * variables so theme switches are instant), and DOMPurify for safe
 * HTML injection.
 *
 * Mermaid code fences become a `<div class="mermaid-placeholder"
 * data-source="...">` which `lib/docs/mermaid.ts` upgrades after mount.
 */

import { Marked } from 'marked';
import markedAlert from 'marked-alert';
import { gfmHeadingId } from 'marked-gfm-heading-id';
import DOMPurify from 'dompurify';
import { createHighlighter, type Highlighter } from 'shiki';

export interface Heading {
	id: string;
	text: string;
	level: number;
}

export interface RenderedDoc {
	html: string;
	headings: Heading[];
	hasMermaid: boolean;
}

const SHIKI_LANGS = [
	'bash',
	'sh',
	'shell',
	'console',
	'python',
	'py',
	'javascript',
	'js',
	'typescript',
	'ts',
	'tsx',
	'jsx',
	'json',
	'yaml',
	'yml',
	'toml',
	'ini',
	'dockerfile',
	'docker',
	'html',
	'css',
	'svelte',
	'sql',
	'diff',
	'markdown',
	'md',
	'text',
	'plaintext',
];

let _highlighterPromise: Promise<Highlighter> | null = null;

function getHighlighter(): Promise<Highlighter> {
	if (!_highlighterPromise) {
		_highlighterPromise = createHighlighter({
			themes: ['github-light', 'github-dark'],
			langs: SHIKI_LANGS,
		});
	}
	return _highlighterPromise;
}

function escapeHtml(s: string): string {
	return s
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;')
		.replace(/'/g, '&#39;');
}

function escapeAttr(s: string): string {
	return s.replace(/&/g, '&amp;').replace(/"/g, '&quot;');
}

function langOrFallback(lang: string, highlighter: Highlighter): string {
	const loaded = new Set<string>(highlighter.getLoadedLanguages());
	if (loaded.has(lang)) return lang;
	return 'text';
}

/**
 * Render markdown to sanitized HTML. Extracts headings (for the TOC rail)
 * and flags whether the document contains mermaid blocks.
 */
export async function renderMarkdown(raw: string): Promise<RenderedDoc> {
	const highlighter = await getHighlighter();

	const marked = new Marked({
		gfm: true,
		breaks: false,
	});

	marked.use(markedAlert());
	marked.use(gfmHeadingId());

	marked.use({
		renderer: {
			code({ text, lang }: { text: string; lang?: string }) {
				const language = (lang || '').toLowerCase().trim();
				if (language === 'mermaid') {
					return `<div class="mermaid-placeholder" data-source="${escapeAttr(text)}"></div>`;
				}
				const effective = langOrFallback(language || 'text', highlighter);
				const displayLang = language || 'text';
				const highlighted = highlighter.codeToHtml(text, {
					lang: effective,
					themes: { light: 'github-light', dark: 'github-dark' },
					defaultColor: false,
				});
				return `<figure class="code-block" data-lang="${escapeAttr(displayLang)}">
<figcaption class="code-block__header">
<span class="code-block__lang">${escapeHtml(displayLang)}</span>
<button type="button" class="code-block__copy" data-copy="${escapeAttr(text)}" aria-label="Copy code">Copy</button>
</figcaption>
${highlighted}
</figure>`;
			},
		},
	});

	const dirty = await marked.parse(raw, { async: true });
	const clean = DOMPurify.sanitize(dirty, {
		ADD_TAGS: ['figure', 'figcaption'],
		ADD_ATTR: ['data-lang', 'data-source', 'data-copy', 'data-theme', 'style', 'tabindex'],
	});

	const headings: Heading[] = [];
	let hasMermaid = false;
	if (typeof window !== 'undefined') {
		const tmpl = document.createElement('template');
		tmpl.innerHTML = clean;
		const root = tmpl.content;
		root.querySelectorAll('h1, h2, h3, h4').forEach((el) => {
			const id = el.getAttribute('id');
			if (!id) return;
			headings.push({
				id,
				text: (el.textContent ?? '').trim(),
				level: Number(el.tagName.slice(1)),
			});
		});
		hasMermaid = root.querySelectorAll('.mermaid-placeholder').length > 0;
	}

	return { html: clean, headings, hasMermaid };
}
